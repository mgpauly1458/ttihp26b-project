"""Splice a kpex-extracted parasitic netlist into an ideal testbench netlist,
so the *same* testbench (same stimulus, same .control block) can be re-run
post-layout without touching xschem.

    python3 layout/build_sim_post.py \
        --tb out/inverter_tb.sim.spice --pex out/tt_analog_inverter_pex.spice \
        --core inverter --pex-cell tt_analog_inverter --suffix pex \
        --out out/inverter_tb_pex.sim.spice

What it does, mechanically:

  1. Deletes the ideal device-level `.subckt <core> ... .ends` block that
     xschem netlisted inline (the two-transistor `inverter`).
  2. In its place, `.include`s the kpex netlist and wraps it in a same-named,
     same-port-order `<core>_<suffix>` subckt, so the rest of the testbench
     (which instantiates `<core>` by name) does not need to change at all --
     only the instantiation line's target cell name is rewritten.
  3. Renames every `write`/`wrdata` output file in the .control block with the
     suffix, so a pre- and post-layout run never overwrite each other's data.

The macro's ports and the schematic core's ports name the same four signals
differently (VPWR/VGND vs. VDD/VSS) and kpex does not promise to preserve
declaration order, so the wrapper is built by reading the extracted
`.SUBCKT` line's actual port order and translating names into it, rather than
assuming position N means the same thing in both netlists.
"""

import argparse
import os
import re

# Only the supply names differ between the ideal schematic core and the
# macro's extracted ports; A and Y are spelled the same on both sides.
NAME_MAP = {"VDD": "VPWR", "VSS": "VGND"}


def wrapper_subckt(core, suffix, pex_cell, core_ports, pex_ports):
    inv_map = {v: k for k, v in NAME_MAP.items()}
    call_ports = []
    for p in pex_ports:
        wrapper_name = p if p in core_ports else inv_map.get(p, p)
        call_ports.append(wrapper_name)
    return (
        f".subckt {core}_{suffix} {' '.join(core_ports)}\n"
        f"X1 {' '.join(call_ports)} {pex_cell}\n"
        f".ends\n"
    )


def ngspice_safe(pex_text):
    """kpex writes tap/well-tie resistors as `Rname n1 n2 <ohms> <model> P=<um>`
    -- its own serialization, borrowed from a tool that resolves <model> against
    a resistor .model card. ngspice has no such card for ntap1/ptap1 (the PDK's
    ngspice deck only has them as *device* subckts, R and Rspec params, not as
    two-terminal R models), so ngspice reads <model> as a 4th node and dies on
    an unknown-parameter error. The resistance value kpex already computed is
    still right; only the trailing model+perimeter is unusable here, so drop
    it and keep a plain two-terminal resistor.
    """
    pex_text = re.sub(
        r"^(R\S+\s+\S+\s+\S+\s+[\d.eE+-]+)\s+\S+\s+P=\S+\s*$",
        r"\1",
        pex_text,
        flags=re.MULTILINE,
    )
    # kpex writes transistors as native `M` elements referencing the model by
    # name (`Mname d g s b sg13_lv_pmos ...`). This PDK's ngspice deck has no
    # raw .model card for sg13_lv_pmos/sg13_lv_nmos -- it packages every
    # device, including diffusion-area/perimeter parameters, as a subckt
    # (see sg13g2_moslv_mod.lib), the same one the ideal schematic reaches
    # with an `X` instance. So an `M` line here needs to become an `X` line;
    # everything kpex already put on it (L/W/AS/AD/PS/PD/rfmode) is exactly
    # what that subckt accepts.
    pex_text = re.sub(r"^M(\S)", r"X\1", pex_text, flags=re.MULTILINE)
    return pex_text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tb", required=True, help="ideal *_tb.sim.spice from xschem")
    ap.add_argument("--pex", required=True, help="kpex --out_spice output")
    ap.add_argument("--core", required=True, help="ideal device subckt name, e.g. inverter")
    ap.add_argument("--pex-cell", required=True, help="kpex top subckt name, e.g. tt_analog_inverter")
    ap.add_argument("--suffix", default="pex")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tb = open(args.tb).read()
    pex = open(args.pex).read()

    # kpex's own artefact stays untouched on disk; the sanitized copy is
    # build scratch, written next to it with a distinct name.
    pex_ng_path = re.sub(r"\.spice$", "_ngspice.spice", args.pex)
    with open(pex_ng_path, "w") as fh:
        fh.write(ngspice_safe(pex))

    core_hdr = re.search(rf"\.subckt\s+{re.escape(args.core)}\s+(.+)", tb, re.IGNORECASE)
    pex_hdr = re.search(rf"\.subckt\s+{re.escape(args.pex_cell)}\s+(.+)", pex, re.IGNORECASE)
    if not core_hdr:
        raise SystemExit(f"no '.subckt {args.core} ...' found in {args.tb}")
    if not pex_hdr:
        raise SystemExit(f"no '.subckt {args.pex_cell} ...' found in {args.pex}")
    core_ports = core_hdr.group(1).split()
    pex_ports = pex_hdr.group(1).split()

    # 1. Drop the ideal device-level definition of <core>.
    tb = re.sub(
        rf"\.subckt\s+{re.escape(args.core)}\b.*?\.ends\b[^\n]*\n",
        "",
        tb,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # 2. Point every instantiation of <core> at <core>_<suffix> instead. Match
    # an "x..." line ending in the bare core name (xschem always trails the
    # subckt name last on its instance lines).
    tb, n = re.subn(
        rf"^(x\S+\s+.*\s){re.escape(args.core)}\s*$",
        rf"\g<1>{args.core}_{args.suffix}",
        tb,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if n == 0:
        raise SystemExit(f"no instantiation of '{args.core}' found to redirect in {args.tb}")

    # 3. Suffix every .control-block output file so pre/post runs don't clobber.
    tb = re.sub(
        r"^((?:write|wrdata)[ \t]+)(\S+?)(\.\w+)([ \t].*)?$",
        lambda m: f"{m.group(1)}{m.group(2)}_{args.suffix}{m.group(3)}{m.group(4) or ''}",
        tb,
        flags=re.MULTILINE,
    )

    # ngspice runs with cwd=out/ (see the Makefile's sim-post recipe), and the
    # .sim.spice file lives there too, so .include wants the pex file's
    # basename, not its (repo-root-relative) build path.
    header = (
        f"* --- post-layout: {args.core} devices replaced by kpex extraction of "
        f"{args.pex_cell} ---\n"
        f".include {os.path.basename(pex_ng_path)}\n"
        + wrapper_subckt(args.core, args.suffix, args.pex_cell, core_ports, pex_ports)
        + "\n"
    )

    with open(args.out, "w") as fh:
        fh.write(header + tb)
    print(f"wrote {args.out}  ({args.core} -> {args.core}_{args.suffix} -> {args.pex_cell})")


if __name__ == "__main__":
    main()
