#!/usr/bin/env python3
"""Bias chain: vbp, vbn and per-stage starve currents against code over PVT; mismatch Monte Carlo; noise at the bias nodes.

    ./run.sh python3 verify/bias.py [--mc 200] [--jobs N]

Writes out/verify/bias.md, bias_corners.csv, bias_mm.csv, bias_noise.csv and docs/verify_bias.png.

DUT: csro_dac into diode PMOS MPD (24 x 2/0.5), mirror MPM (1/0.5) into diode NMOS MND (0.5/0.5), as the top sheet,
plus NSTAGE replicas of each stage's starve device with drains at VMID. One .dc covers all 256 codes.
- Corners: compression (vbp falls, the triode units follow) and the PVT movement of the bias points.
- Mismatch MC: spread of the eleven stage currents (single 1 um and 0.5 um fingers, the dominant mismatch);
  changes duty cycle, second-order frequency. Also the MPD/MPM mirror ratio.
- Noise: .noise at vbp and vbn over 1 kHz-1 GHz, 1 Hz-1 GHz and 1 kHz-1 MHz, as a fraction of one LSB step
  of the node. ngspice needs `ac 1` on Vdd for .noise; onoise_total is V rms.
"""
import argparse
import os

import common as C

NSTAGE = 11
VMID = 0.6
CODES_REPORT = [0, 1, 16, 128, 255]
CODES_NOISE = [1, 16, 128, 255]


def bias_devices(mm=False):
    """MPD, MPM, MND as on the top sheet; 0 V sources in series read their currents."""
    mmk = " mm_ok=1" if mm else ""
    return f"""Vmpd VPWR vpd 0
XMPD vbp vbp vpd VPWR sg13_lv_pmos w=48u l=0.5u ng=24{mmk}
Vmpm VPWR vpm 0
XMPM vbn vbp vpm VPWR sg13_lv_pmos w=1u l=0.5u ng=1{mmk}
XMND vbn vbn 0 0 sg13_lv_nmos w=0.5u l=0.5u ng=1{mmk}
"""


def replicas(mm=False):
    mmk = " mm_ok=1" if mm else ""
    lines = []
    for i in range(NSTAGE):
        lines.append(f"XSP{i} sp{i} vbp VPWR VPWR sg13_lv_pmos w=1u l=0.5u ng=1{mmk}")
        lines.append(f"VSP{i} sp{i} 0 {VMID}")
        lines.append(f"XSN{i} sn{i} vbn 0 0 sg13_lv_nmos w=0.5u l=0.5u ng=1{mmk}")
        lines.append(f"VSN{i} sn{i} 0 {VMID}")
    return "\n".join(lines) + "\n"


def deck_dc(models, vdd, mm=False):
    cols = " ".join([f"i(VSP{i})" for i in range(NSTAGE)] + [f"i(VSN{i})" for i in range(NSTAGE)])
    return f"""* bias chain: vbp, vbn, I_dac, stage currents vs code
{models}{C.blocks()}Vdd VPWR 0 {vdd}
{C.code_bits(vdd)}Xdac {C.CODE_PORTS} vbp VPWR 0 csro_dac
{bias_devices(mm)}{replicas(mm)}.control
dc Vsw 0 255 1
wrdata bias.txt v(vbp) v(vbn) i(Vmpd) i(Vmpm) {cols}
.endc
.end
"""


def deck_noise(vdd, code):
    return f"""* bias chain noise at code {code}
{C.corner()}{C.blocks()}Vdd VPWR 0 {vdd} ac 1
{C.code_dc(vdd, code)}Xdac {C.CODE_PORTS} vbp VPWR 0 csro_dac
{bias_devices()}{replicas()}.control
op
echo "vbp_op=$&v(vbp) vbn_op=$&v(vbn)"
noise v(vbn) Vdd dec 10 1 1G
setplot noise2
let vbn_tot_1 = onoise_total
echo "vbn_1Hz=$&vbn_tot_1"
setplot noise1
wrdata vbn_spec.txt onoise_spectrum
noise v(vbn) Vdd dec 10 1k 1G
setplot noise4
let vbn_tot_1k = onoise_total
echo "vbn_1kHz=$&vbn_tot_1k"
noise v(vbp) Vdd dec 10 1 1G
setplot noise6
let vbp_tot_1 = onoise_total
echo "vbp_1Hz=$&vbp_tot_1"
noise v(vbp) Vdd dec 10 1k 1G
setplot noise8
let vbp_tot_1k = onoise_total
echo "vbp_1kHz=$&vbp_tot_1k"
noise v(vbn) Vdd dec 10 1k 1Meg
setplot noise10
let vbn_lf = onoise_total
echo "vbn_lf=$&vbn_lf"
noise v(vbp) Vdd dec 10 1k 1Meg
setplot noise12
let vbp_lf = onoise_total
echo "vbp_lf=$&vbp_lf"
.endc
.end
"""


def analyse(rundir):
    rows = C.read_wrdata(os.path.join(rundir, "bias.txt"))
    if len(rows) != 256:
        return None
    # wrdata writes x y pairs per column: [sw, vbp, sw, vbn, sw, impd, ...]
    def col(j):
        return [r[2 * j + 1] for r in rows]
    vbp, vbn = col(0), col(1)
    idac = col(2)                        # current through MPD = the DAC's current
    impm = col(3)
    isp = [[col(4 + i)[k] for i in range(NSTAGE)] for k in range(256)]
    isn = [[-col(4 + NSTAGE + i)[k] for i in range(NSTAGE)] for k in range(256)]   # VSN sources the current
    return dict(vbp=vbp, vbn=vbn, idac=idac, impm=impm, isp=isp, isn=isn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()
    md = []

    # ---- 1. corners ---------------------------------------------------------
    decks = {C.pvt_name(c, t, v): deck_dc(C.corner(c, t), v) for c, t, v in C.PVT}
    res = C.run_decks(decks, a.jobs, tag="bias")
    data = {}
    rows = []
    for name, (log, d) in res.items():
        m = analyse(d)
        if not m:
            print("FAILED", name, log[-300:]); continue
        data[name] = m
        for k in CODES_REPORT:
            isp = sum(m["isp"][k]) / NSTAGE
            isn = sum(m["isn"][k]) / NSTAGE
            rows.append([name, k, m["vbp"][k], m["vbn"][k], m["idac"][k] * 1e6, isp * 1e6, isn * 1e6,
                         m["idac"][k] / isp if isp else None])
    hdr = ["PVT", "code", "vbp V", "vbn V", "I_dac uA", "I_stage(p) uA", "I_stage(n) uA", "I_dac/I_stage"]
    fmt = [None, "%d", "%.3f", "%.3f", "%.1f", "%.2f", "%.2f", "%.1f"]
    C.write_csv(os.path.join(C.OUT, "bias_corners.csv"), hdr, rows)
    md.append("## Bias chain: operating points against code\n")
    md.append("Stage starve devices measured with their drains at 0.6 V. The nominal mirror ratio is 48:1 (24 x 2 um diode, 1 um stage device).\n\n")
    md.append("**Signoff corners:**\n")
    sig = [r for p in C.SIGNOFF for r in rows if r[0] == C.pvt_name(*p)]
    md.append(C.table(hdr, sig, fmt))
    md.append("\n**All 45 PVT points**, per-stage PMOS current extremes (this is what sets the ring's delay):\n")
    ext = []
    for k in CODES_REPORT:
        rk = [r for r in rows if r[1] == k]
        lo = min(rk, key=lambda r: r[5]); hi = max(rk, key=lambda r: r[5])
        ext.append([k, lo[5], lo[0], hi[5], hi[0], hi[5] / lo[5]])
    md.append(C.table(["code", "min I_stage(p) uA", "at", "max I_stage(p) uA", "at", "max/min"],
                      ext, ["%d", "%.2f", None, "%.2f", None, "%.1f"]))
    ratios = [r[7] for r in rows if r[1] >= 1 and r[7]]
    md.append(f"\nI_dac / I_stage(p) over every PVT point and code >= 1: {min(ratios):.1f} .. {max(ratios):.1f} "
              f"(nominal 48; the deviation is the diode and the stage device sitting at different drain voltages).\n")

    # ---- 2. mismatch Monte Carlo ------------------------------------------
    if a.mc:
        decks = {f"mm{s}": deck_dc(C.mc("mismatch", 3000 + s), 1.2, mm=True) for s in range(a.mc)}
        res = C.run_decks(decks, a.jobs, tag="bias_mm")
        ms = [m for m in (analyse(d) for _, (log, d) in sorted(res.items())) if m]
        md.append(f"\n## Bias chain: mismatch Monte Carlo, {len(ms)} samples (mos_tt_mismatch, 27 C, 1.2 V)\n")
        mm_rows = []
        csv_rows = []
        for k in [1, 16, 255]:
            spread_p, spread_n, worst_p, ratio = [], [], [], []
            for m in ms:
                mu, sd, lo, hi = C.stats(m["isp"][k]); spread_p.append(100 * sd / mu); worst_p.append(100 * (hi - lo) / mu)
                mu, sd, lo, hi = C.stats(m["isn"][k]); spread_n.append(100 * sd / mu)
                ratio.append(m["impm"][k] / m["idac"][k] * 48)
            idac = [m["idac"][k] for m in ms]
            mu_i, sd_i, _, _ = C.stats(idac)
            mu_r, sd_r, _, _ = C.stats(ratio)
            mm_rows.append([k, sum(spread_p) / len(spread_p), max(spread_p), max(worst_p), sum(spread_n) / len(spread_n),
                            100 * sd_r / mu_r, 100 * sd_i / mu_i])
            csv_rows += [[k, s, spread_p[s], spread_n[s], ratio[s], idac[s]] for s in range(len(ms))]
        md.append(C.table(["code", "stage PMOS current sigma/mean %, mean", "worst sample", "worst max-min %",
                           "stage NMOS sigma/mean %", "MPM/MPD ratio sigma %", "I_dac sigma %"],
                          mm_rows, ["%d", "%.1f", "%.1f", "%.1f", "%.1f", "%.1f", "%.2f"]))
        md.append("\nEach row: across the eleven stages within one sample (mean and worst over samples), then the mirror ratio and the DAC current across samples.\n")
        C.write_csv(os.path.join(C.OUT, "bias_mm.csv"), ["code", "sample", "isp_sigma_pct", "isn_sigma_pct", "mirror_ratio_x48", "idac_A"], csv_rows)

    # ---- 3. noise ------------------------------------------------------------
    decks = {f"noise_code{k}": deck_noise(1.2, k) for k in CODES_NOISE}
    res = C.run_decks(decks, a.jobs, tag="bias_noise")
    ref = data.get(C.pvt_name("mos_tt", 27, 1.2))
    nrows = []
    spectra = {}
    for k in CODES_NOISE:
        log, d = res[f"noise_code{k}"]
        vbn1, vbn1k = C.meas(log, "vbn_1Hz"), C.meas(log, "vbn_1kHz")
        vbp1, vbp1k = C.meas(log, "vbp_1Hz"), C.meas(log, "vbp_1kHz")
        vbnlf, vbplf = C.meas(log, "vbn_lf"), C.meas(log, "vbp_lf")
        if vbn1k is None:
            print("noise failed at code", k, log[-500:]); continue
        # one LSB step of the same node, from the DC sweep
        d_vbn = abs(ref["vbn"][k + 1] - ref["vbn"][k]) if ref and k < 255 else abs(ref["vbn"][k] - ref["vbn"][k - 1])
        d_vbp = abs(ref["vbp"][k + 1] - ref["vbp"][k]) if ref and k < 255 else abs(ref["vbp"][k] - ref["vbp"][k - 1])
        nrows.append([k, vbn1k * 1e6, vbn1 * 1e6, vbnlf * 1e6, d_vbn * 1e3, 100 * vbn1k / d_vbn, 100 * vbnlf / d_vbn,
                      vbp1k * 1e6, vbp1 * 1e6, vbplf * 1e6, d_vbp * 1e3, 100 * vbp1k / d_vbp, 100 * vbplf / d_vbp])
        try:
            spectra[k] = C.read_wrdata(os.path.join(d, "vbn_spec.txt"))
        except FileNotFoundError:
            pass
    hdr = ["code", "vbn noise uVrms 1k-1G", "1-1G", "1k-1M", "vbn LSB step mV", "noise/LSB % (1k-1G)", "noise/LSB % (1k-1M)",
           "vbp noise uVrms 1k-1G", "1-1G", "1k-1M", "vbp LSB step mV", "noise/LSB % (1k-1G)", "noise/LSB % (1k-1M)"]
    md.append("\n## Bias chain: noise at the bias nodes (typical, 27 C, 1.2 V)\n")
    md.append(C.table(hdr, nrows, ["%d", "%.1f", "%.1f", "%.1f", "%.2f", "%.1f", "%.2f", "%.1f", "%.1f", "%.1f", "%.2f", "%.1f", "%.2f"]))
    md.append("\nIntegrated output noise (rms) of the bias nodes with the code held, from ngspice `.noise` (PSP thermal + flicker; ngspice reports onoise_total as the rms voltage). "
              "\"LSB step\" is how far the node moves for one code step at that code; noise/LSB is the rms noise as a "
              "percentage of that step. The 1 kHz-1 GHz figure is everything the node carries; most of it is white noise "
              "above 1 MHz, which the ring turns into period jitter that a reciprocal count averages (ring.py measures "
              "that directly). The 1 kHz-1 MHz figure is the slow part that behaves like a code error within one "
              "measurement, and is the one to compare with a code step.\n")
    C.write_csv(os.path.join(C.OUT, "bias_noise.csv"), hdr, nrows)

    # ---- figure -----------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        for c in C.CORNERS:
            n = C.pvt_name(c, 27, 1.2)
            if n in data:
                ax[0].plot(range(256), data[n]["vbp"], label=f"vbp {c[4:]}")
                ax[0].plot(range(256), data[n]["vbn"], "--", label=f"vbn {c[4:]}")
                ax[1].plot(range(256), [sum(x) / NSTAGE * 1e6 for x in data[n]["isp"]], label=c[4:])
        ax[0].set_xlabel("code"); ax[0].set_ylabel("V"); ax[0].legend(fontsize=7, ncol=2); ax[0].grid(alpha=.3)
        ax[0].set_title("bias nodes vs code, process corners")
        for t, v, ls in [(125, 1.08, "--"), (-40, 1.32, ":")]:
            n = C.pvt_name("mos_tt", t, v)
            if n in data:
                ax[1].plot(range(256), [sum(x) / NSTAGE * 1e6 for x in data[n]["isp"]], "k" + ls, label=f"tt {t} C {v} V")
        ax[1].set_xlabel("code"); ax[1].set_ylabel("per-stage PMOS current / uA"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
        ax[1].set_title("stage current vs code")
        for k, sp in spectra.items():
            ax[2].loglog([r[0] for r in sp], [r[1] for r in sp], label=f"code {k}")
        ax[2].set_xlabel("Hz"); ax[2].set_ylabel("vbn noise / V/sqrt(Hz)"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3, which="both")
        ax[2].set_title("vbn noise density")
        fig.tight_layout()
        fig.savefig(os.path.join(C.DOCS, "verify_bias.png"), dpi=110)
    except ImportError:
        pass

    C.write_md("bias", "".join(md))


if __name__ == "__main__":
    main()
