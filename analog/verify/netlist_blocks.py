#!/usr/bin/env python3
"""Netlist the four schematic sub-sheets as ngspice subcircuits.

    ./run.sh python3 verify/netlist_blocks.py   ->  out/blocks/blocks.spice

The block-level tests (dac.py, bias.py, stage.py, nand.py, buffer.py) work
on the xschem sheets in xschem/: csro_dac, csro_stage, csro_nand, csro_inv.
Those sheets are the drawing LVS proved equal to the layout (make lvs-sch),
so a test on a sheet is a test on the block as it was laid out, and each
block can be exercised on its own with ideal sources around it.

xschem writes a sheet's devices as a flat list (its `top_subckt` flag only
wraps the top sheet), so this script wraps each in `.subckt name <pins>`
with the pin order below and concatenates them. The PDK symbols emit
`mm_ok=1` on every device, which is what lets the `_mismatch` model
sections apply their per-device random offsets in the Monte Carlo runs.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHEETS = os.path.join(ROOT, "xschem")
OUT = os.path.join(ROOT, "out", "blocks")

# Pin order of each subcircuit, as the tests instantiate them.
PINS = {
    "csro_dac":   [f"code[{k}]" for k in range(8)] + ["vbp", "VPWR", "VGND"],
    "csro_stage": ["in", "out", "vbp", "vbn", "VPWR", "VGND"],
    "csro_nand":  ["a", "b", "out", "vbp", "vbn", "VPWR", "VGND"],
    "csro_inv":   ["in", "out", "VPWR", "VGND"],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    out = ["* Block subcircuits netlisted from analog/xschem/*.sch by verify/netlist_blocks.py",
           "* GENERATED - do not edit. Pin order as PINS in that script.", ""]
    for sheet, pins in PINS.items():
        cmd = ["xschem", "--rcfile", os.path.join(SHEETS, "xschemrc"), "-n", "-s", "-q", "--no_x",
               os.path.join(SHEETS, sheet + ".sch"), "-o", OUT]
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=SHEETS)
        path = os.path.join(OUT, sheet + ".spice")
        if not os.path.exists(path):
            sys.exit(f"xschem produced no {path}:\n{p.stdout}\n{p.stderr}")
        devices = [l for l in open(path).read().splitlines()
                   if l.strip() and not l.startswith("*") and not l.startswith(".end")]
        out.append(f".subckt {sheet} {' '.join(pins)}")
        out.extend(devices)
        out.append(f".ends {sheet}\n")
        print(f"{sheet}: {len(devices)} devices")
    with open(os.path.join(OUT, "blocks.spice"), "w") as fh:
        fh.write("\n".join(out))
    print("wrote", os.path.join(OUT, "blocks.spice"))


if __name__ == "__main__":
    main()
