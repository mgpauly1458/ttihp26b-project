#!/usr/bin/env python3
"""The current DAC on its own: linearity over corners and under mismatch.

    ./run.sh python3 verify/dac.py [--mc 200] [--stat 100] [--jobs N]

What is tested
  csro_dac (the 255 binary-weighted unit fingers plus the two always-on
  ones), sinking from an ideal voltage held at the drain node. The drain is
  held at 0.6 V, the middle of the range the real diode node spans, so this
  measures the array itself: how well 2^k fingers deliver 2^k unit currents.
  The compression that comes from the drain sagging is the bias block's
  business (bias.py) and shows up here only as the two extra rows at 0.46
  and 0.85 V.

  One .dc analysis sweeps all 256 codes: eight B-sources turn the swept
  variable into the code bits (common.code_bits).

Three questions, three runs
  1. Corners: I(code) at all 45 PVT points (5 process corners x 3
     temperatures x 3 supplies). Reports the unit current, the full-scale
     current, the always-on current at code 0, and the endpoint-fit DNL and
     INL in LSB. The instrument needs monotonic; INL is informational (the
     tile measures frequency, not current, and the code-to-frequency map
     is calibrated on the bench anyway).
  2. Mismatch Monte Carlo: `mos_tt_mismatch`, N samples, each finger with
     its own random Vt and mobility offset (the PDK's agauss on
     delvto/factuo, scaled by 1/sqrt(WL)). The worst DNL in the run is the
     number that says whether the binary weighting can ever produce a
     non-monotonic step, and where (it is always at a major transition).
  3. Process Monte Carlo: `mos_tt_stat`, every device moved together by the
     PDK's global distributions. Reports the spread of the unit current,
     which is the spread of the whole frequency scale from die to die.
"""
import argparse
import os

import common as C

VD = 0.6            # drain voltage the array is measured into
VD_EXTRA = [0.46, 0.85]   # the diode node at code 255 and code 1 (typical)


def deck(models, vdd, vd):
    return f"""* csro_dac: I(code) into Vd={vd}
{models}{C.blocks()}Vdd VPWR 0 {vdd}
Vd vbp 0 {vd}
{C.code_bits(vdd)}Xdac {C.CODE_PORTS} vbp VPWR 0 csro_dac
.control
dc Vsw 0 255 1
let iout = -i(Vd)
wrdata iout.txt iout
.endc
.end
"""


def analyse(rundir):
    """I(code) -> metrics. Endpoint fit: unit = (I255 - I0) / 255."""
    rows = C.read_wrdata(os.path.join(rundir, "iout.txt"))
    if len(rows) != 256:
        return None
    I = [r[1] for r in rows]
    unit = (I[255] - I[0]) / 255
    dnl = [(I[k] - I[k - 1]) / unit - 1 for k in range(1, 256)]
    inl = [(I[k] - I[0] - k * unit) / unit for k in range(256)]
    worst_dnl_k = max(range(255), key=lambda i: abs(dnl[i])) + 1
    return dict(I=I, i0=I[0], unit=unit, ifs=I[255], ilsb=I[1] - I[0],
                dnl_max=max(dnl), dnl_min=min(dnl), worst_dnl_code=worst_dnl_k,
                inl_max=max(abs(x) for x in inl), monotonic=all(d > -1 for d in dnl))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc", type=int, default=200, help="mismatch samples")
    ap.add_argument("--stat", type=int, default=100, help="process samples")
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()

    # ---- 1. corners -------------------------------------------------------
    decks = {}
    for c, t, v in C.PVT:
        decks[C.pvt_name(c, t, v)] = deck(C.corner(c, t), v, VD)
    for vd in VD_EXTRA:
        decks[f"tt_27C_1.20V_vd{vd}"] = deck(C.corner(), 1.2, vd)
    res = C.run_decks(decks, a.jobs, tag="dac")
    rows = []
    curves = {}
    for name, (log, d) in res.items():
        m = analyse(d)
        if m is None:
            print("FAILED:", name, log[-300:])
            continue
        curves[name] = m["I"]
        rows.append([name, m["i0"] * 1e6, m["ilsb"] * 1e6, m["unit"] * 1e6, m["ifs"] * 1e6,
                     m["dnl_min"], m["dnl_max"], m["worst_dnl_code"], m["inl_max"], "yes" if m["monotonic"] else "NO"])
    hdr = ["PVT", "I(0) uA", "I(1)-I(0) uA", "unit uA", "I(255) uA", "DNL min", "DNL max", "at code", "|INL| max", "monotonic"]
    fmt = [None, "%.2f", "%.2f", "%.3f", "%.0f", "%.3f", "%.3f", "%d", "%.2f", None]
    C.write_csv(os.path.join(C.OUT, "dac_corners.csv"), hdr, rows)
    byname = {r[0]: r for r in rows}

    md = ["## DAC: current against code\n",
          f"Drain held at {VD} V. Endpoint fit; DNL/INL in units of the fitted LSB.\n",
          "**Signoff corners** (the three LibreLane times the tile at):\n",
          C.table(hdr, [byname[C.pvt_name(*p)] for p in C.SIGNOFF if C.pvt_name(*p) in byname], fmt)]
    pvt_rows = [r for r in rows if not r[0].endswith("V") or "vd" not in r[0]]
    pvt_rows = [r for r in rows if "_vd" not in r[0]]
    md.append(f"\n**All {len(pvt_rows)} PVT points**, extremes:\n")
    ext = []
    for col, label, f in [(3, "unit current uA", "%.3f"), (4, "full scale uA", "%.0f"), (1, "code-0 current uA", "%.2f"),
                          (5, "DNL min", "%.3f"), (6, "DNL max", "%.3f"), (8, "|INL| max", "%.2f")]:
        lo = min(pvt_rows, key=lambda r: r[col]); hi = max(pvt_rows, key=lambda r: r[col])
        ext.append([label, f % lo[col], lo[0], f % hi[col], hi[0]])
    md.append(C.table(["", "min", "at", "max", "at"], ext))
    nonmono = [r[0] for r in pvt_rows if r[9] != "yes"]
    md.append(f"\nMonotonic at {len(pvt_rows) - len(nonmono)} of {len(pvt_rows)} PVT points"
              + (f"; NOT at: {', '.join(nonmono)}" if nonmono else "") + ".\n")
    md.append("\n**Drain voltage sensitivity** (typical): the units are in triode, so the current follows the drain.\n")
    md.append(C.table(hdr, [byname["tt_27C_1.20V"]] + [byname[f"tt_27C_1.20V_vd{vd}"] for vd in VD_EXTRA], fmt))

    # ---- 2. mismatch Monte Carlo -----------------------------------------
    if a.mc:
        decks = {f"mm{s}": deck(C.mc("mismatch", 1000 + s), 1.2, VD) for s in range(a.mc)}
        res = C.run_decks(decks, a.jobs, tag="dac_mm")
        ms = [analyse(d) for _, (log, d) in sorted(res.items())]
        ms = [m for m in ms if m]
        dnl_min = [m["dnl_min"] for m in ms]
        worst = min(ms, key=lambda m: m["dnl_min"])
        codes = [m["worst_dnl_code"] for m in ms]
        from collections import Counter
        top = Counter(codes).most_common(3)
        mu, sd, lo, hi = C.stats([m["unit"] for m in ms])
        md.append(f"\n## DAC: mismatch Monte Carlo, {len(ms)} samples (mos_tt_mismatch, 27 C, 1.2 V)\n")
        md.append(C.table(["", "value"], [
            ["samples monotonic", f"{sum(m['monotonic'] for m in ms)} / {len(ms)}"],
            ["worst DNL (most negative step)", f"{worst['dnl_min']:.3f} LSB at code {worst['worst_dnl_code']}"],
            ["DNL min, mean over samples", f"{sum(dnl_min)/len(dnl_min):.3f} LSB"],
            ["|INL| max, worst sample", f"{max(m['inl_max'] for m in ms):.2f} LSB"],
            ["worst-DNL codes (count)", ", ".join(f"{c} ({n})" for c, n in top)],
            ["unit current sigma/mean", f"{100*sd/mu:.2f} %"],
        ]))
        C.write_csv(os.path.join(C.OUT, "dac_mm.csv"),
                    ["sample", "unit_A", "ifs_A", "dnl_min", "dnl_max", "worst_code", "inl_max", "monotonic"],
                    [[k, m["unit"], m["ifs"], m["dnl_min"], m["dnl_max"], m["worst_dnl_code"], m["inl_max"], m["monotonic"]]
                     for k, m in enumerate(ms)])

    # ---- 3. process Monte Carlo -----------------------------------------
    if a.stat:
        decks = {f"st{s}": deck(C.mc("stat", 2000 + s), 1.2, VD) for s in range(a.stat)}
        res = C.run_decks(decks, a.jobs, tag="dac_stat")
        ms = [m for m in (analyse(d) for _, (log, d) in sorted(res.items())) if m]
        mu, sd, lo, hi = C.stats([m["unit"] for m in ms])
        mu0, sd0, lo0, hi0 = C.stats([m["i0"] for m in ms])
        md.append(f"\n## DAC: process Monte Carlo, {len(ms)} samples (mos_tt_stat, 27 C, 1.2 V)\n")
        md.append(C.table(["", "mean", "sigma", "sigma/mean", "min", "max"], [
            ["unit current uA", f"{mu*1e6:.3f}", f"{sd*1e6:.3f}", f"{100*sd/mu:.1f} %", f"{lo*1e6:.3f}", f"{hi*1e6:.3f}"],
            ["code-0 current uA", f"{mu0*1e6:.2f}", f"{sd0*1e6:.2f}", f"{100*sd0/mu0:.1f} %", f"{lo0*1e6:.2f}", f"{hi0*1e6:.2f}"],
        ]))
        md.append(f"\nMonotonic in {sum(m['monotonic'] for m in ms)} / {len(ms)} samples "
                  f"(global variation moves every finger together, so it cannot break the weighting).\n")
        C.write_csv(os.path.join(C.OUT, "dac_stat.csv"), ["sample", "unit_A", "i0_A", "ifs_A"],
                    [[k, m["unit"], m["i0"], m["ifs"]] for k, m in enumerate(ms)])

    # ---- figure --------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        for c in C.CORNERS:
            n = C.pvt_name(c, 27, 1.2)
            if n in curves:
                ax[0].plot(range(256), [i * 1e6 for i in curves[n]], label=c[4:])
        for t, v, ls in [(125, 1.08, "--"), (-40, 1.32, ":")]:
            n = C.pvt_name("mos_tt", t, v)
            if n in curves:
                ax[0].plot(range(256), [i * 1e6 for i in curves[n]], "k" + ls, label=f"tt {t} C {v} V")
        ax[0].set_xlabel("code"); ax[0].set_ylabel("I_dac / uA (drain at 0.6 V)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
        ax[0].set_title("DAC current vs code, corners")
        if a.mc:
            ax[1].hist(dnl_min, bins=30, color="C0")
            ax[1].axvline(-1, color="r", ls="--", label="non-monotonic below -1")
            ax[1].set_xlabel("worst DNL per sample / LSB"); ax[1].set_ylabel("samples"); ax[1].legend(fontsize=8)
            ax[1].set_title(f"mismatch Monte Carlo, {len(dnl_min)} samples")
        fig.tight_layout()
        fig.savefig(os.path.join(C.DOCS, "verify_dac.png"), dpi=110)
    except ImportError:
        pass

    C.write_md("dac", "".join(md))


if __name__ == "__main__":
    main()
