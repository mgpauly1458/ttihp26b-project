#!/usr/bin/env python3
"""One starved inverter stage: delay and slew over the 45 PVT points at codes 0/16/128/255; thermal noise to timing jitter.

    ./run.sh python3 verify/stage.py [--jobs N]

Writes out/verify/stage.md, stage_corners.csv, stage_noise.csv and docs/verify_stage.png.

DUT: csro_stage with the real bias chain at a fixed code, driven by and loading identical stages.
11 x (tPLH + tPHL) is the ring period ring.py should find.
- Noise: input DC at the trip point (from a .dc in the same run), .noise gives the output V rms;
  sigma_td = v_n / (dV/dt at the crossing, from the transient). Small-signal estimate, not transient noise
  (ngspice has none). Period jitter = sqrt(22) sigma_td; N periods average by sqrt(N).
- Slopes are taken from the 40/60 % crossing times because ngspice `deriv` is unsupported here.
- ngspice needs `ac 1` on the input source for .noise; onoise_total is V rms.
"""
import argparse
import os

import common as C

CODES = [0, 16, 128, 255]


def bias(vdd, code):
    return f"""{C.code_dc(vdd, code)}Xdac {C.CODE_PORTS} vbp VPWR 0 csro_dac
XMPD vbp vbp VPWR VPWR sg13_lv_pmos w=48u l=0.5u ng=24
XMPM vbn vbp VPWR VPWR sg13_lv_pmos w=1u l=0.5u ng=1
XMND vbn vbn 0 0 sg13_lv_nmos w=0.5u l=0.5u ng=1
"""


def deck_tran(models, vdd, code):
    T = 2.0 / C.f_nom(code)          # two nominal periods per pulse
    return f"""* stage delay at code {code}
{models}{C.blocks()}Vdd VPWR 0 {vdd}
{bias(vdd, code)}Vin a 0 pulse(0 {vdd} {T/4:.4g} 50p 50p {T/2:.4g} {T:.4g})
Xdrv a b vbp vbn VPWR 0 csro_stage
Xdut b y vbp vbn VPWR 0 csro_stage
Xload y z vbp vbn VPWR 0 csro_stage
Xload2 z zz vbp vbn VPWR 0 csro_stage
.control
tran {T/2000:.4g} {3*T:.4g}
let vh = {vdd}/2
meas tran tin_f when v(b)=vh fall=2
meas tran tout_r when v(y)=vh rise=2
meas tran tin_r when v(b)=vh rise=2
meas tran tout_f when v(y)=vh fall=2
let tplh = tout_r - tin_f
let tphl = tout_f - tin_r
echo "tplh=$&tplh tphl=$&tphl"
meas tran t40r when v(y)={0.4*vdd} rise=2
meas tran t60r when v(y)={0.6*vdd} rise=2
meas tran t60f when v(y)={0.6*vdd} fall=2
meas tran t40f when v(y)={0.4*vdd} fall=2
let sr_r = {0.2*vdd}/(t60r - t40r)
let sr_f = -{0.2*vdd}/(t40f - t60f)
echo "sr_r=$&sr_r sr_f=$&sr_f"
meas tran tr when v(y)={0.2*vdd} rise=2
meas tran tr8 when v(y)={0.8*vdd} rise=2
meas tran tf when v(y)={0.8*vdd} fall=2
meas tran tf2 when v(y)={0.2*vdd} fall=2
let trise = tr8 - tr
let tfall = tf2 - tf
echo "trise=$&trise tfall=$&tfall"
.endc
.end
"""


def deck_noise(vdd, code):
    return f"""* stage noise at its trip point, code {code}
{C.corner()}{C.blocks()}Vdd VPWR 0 {vdd}
{bias(vdd, code)}Vin b 0 dc {vdd/2} ac 1
Xdut b y vbp vbn VPWR 0 csro_stage
Xload y z vbp vbn VPWR 0 csro_stage
Xload2 z zz vbp vbn VPWR 0 csro_stage
.control
dc Vin 0 {vdd} 0.001
meas dc vtrip find v(b) when v(y)={vdd/2}
let vlo = vtrip - 0.005
let vhi = vtrip + 0.005
meas dc ylo find v(y) when v(b)=$&vlo
meas dc yhi find v(y) when v(b)=$&vhi
let gain = (yhi - ylo)/0.01
echo "vtrip=$&vtrip gain=$&gain"
alter Vin dc = $&vtrip
op
echo "vy_op=$&v(y)"
noise v(y) Vin dec 20 1k 100G
setplot noise2
let on_tot = onoise_total
let in_tot = inoise_total
echo "onoise_tot=$&on_tot inoise_tot=$&in_tot"
setplot noise1
wrdata onoise.txt onoise_spectrum
.endc
.end
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()
    md = []

    decks = {}
    for c, t, v in C.PVT:
        for k in CODES:
            decks[f"{C.pvt_name(c, t, v)}_code{k}"] = deck_tran(C.corner(c, t), v, k)
    res = C.run_decks(decks, a.jobs, tag="stage")
    rows = []
    for c, t, v in C.PVT:
        for k in CODES:
            log, d = res[f"{C.pvt_name(c, t, v)}_code{k}"]
            tplh, tphl = C.meas(log, "tplh"), C.meas(log, "tphl")
            if tplh is None or tphl is None:
                print("FAILED", c, t, v, k, log[-300:]); continue
            rows.append([C.pvt_name(c, t, v), k, tplh * 1e12, tphl * 1e12, (tplh + tphl) / 2 * 1e12,
                         C.meas(log, "trise") * 1e12, C.meas(log, "tfall") * 1e12,
                         C.meas(log, "sr_r") * 1e-9, -C.meas(log, "sr_f") * 1e-9,
                         1 / (11 * (tplh + tphl)) / 1e6])
    hdr = ["PVT", "code", "tPLH ps", "tPHL ps", "mean ps", "rise 20-80 ps", "fall 20-80 ps", "slope up V/ns", "slope down V/ns", "11-stage ring MHz"]
    fmt = [None, "%d", "%.0f", "%.0f", "%.0f", "%.0f", "%.0f", "%.2f", "%.2f", "%.1f"]
    C.write_csv(os.path.join(C.OUT, "stage_corners.csv"), hdr, rows)
    md.append("## Stage: delay against code and corner\n")
    md.append("A starved inverter driven by and loading identical stages, with the real bias chain at the code shown. "
              "The last column is 1 / (11 x (tPLH + tPHL)): the period an 11-stage ring of these would have.\n\n**Signoff corners:**\n")
    md.append(C.table(hdr, [r for p in C.SIGNOFF for r in rows if r[0] == C.pvt_name(*p)], fmt))
    md.append("\n**All 45 PVT points**, delay extremes:\n")
    ext = []
    for k in CODES:
        rk = [r for r in rows if r[1] == k]
        lo = min(rk, key=lambda r: r[4]); hi = max(rk, key=lambda r: r[4])
        ext.append([k, lo[4], lo[0], hi[4], hi[0], hi[4] / lo[4]])
    md.append(C.table(["code", "fastest mean delay ps", "at", "slowest mean delay ps", "at", "slow/fast"], ext,
                      ["%d", "%.0f", None, "%.0f", None, "%.2f"]))

    # ---- noise --------------------------------------------------------------------
    decks = {f"noise_code{k}": deck_noise(1.2, k) for k in CODES}
    res = C.run_decks(decks, a.jobs, tag="stage_noise")
    nrows = []
    spectra = {}
    typ = {r[1]: r for r in rows if r[0] == C.pvt_name("mos_tt", 27, 1.2)}
    for k in CODES:
        log, d = res[f"noise_code{k}"]
        on = C.meas(log, "onoise_tot")
        if on is None:
            print("noise failed at code", k, log[-600:]); continue
        vn = on                      # ngspice onoise_total is already the rms voltage (V), not V^2
        slope = (typ[k][7] + typ[k][8]) / 2 * 1e9 if k in typ else None      # V/s
        sig_td = vn / slope if slope else None
        period = 2 * 11 * typ[k][4] * 1e-12 if k in typ else None
        sig_T = sig_td * (22 ** 0.5) if sig_td else None
        nrows.append([k, C.meas(log, "vtrip"), C.meas(log, "gain"), vn * 1e3, slope * 1e-9 if slope else None,
                      sig_td * 1e12 if sig_td else None, sig_T * 1e12 if sig_T else None,
                      1e6 * sig_T / period if sig_T else None, 1e6 * sig_T / period / (200 ** 0.5) if sig_T else None])
        try:
            spectra[k] = C.read_wrdata(os.path.join(d, "onoise.txt"))
        except FileNotFoundError:
            pass
    hdr = ["code", "trip point V", "gain at trip", "output noise mVrms (1k-100G)", "slope V/ns",
           "sigma_td per transition ps", "sigma per period ps (x sqrt 22)", "ppm of period", "ppm over N=200 periods"]
    md.append("\n## Stage: thermal noise to timing jitter (typical, 27 C, 1.2 V)\n")
    md.append(C.table(hdr, nrows, ["%d", "%.3f", "%.1f", "%.2f", "%.2f", "%.1f", "%.1f", "%.0f", "%.0f"]))
    md.append("\nEstimate: output noise of the stage held at its trip point (ngspice `.noise`, the load being the next stage), "
              "divided by the output slope at the half-rail crossing from the transient. Twenty-two such transitions make a "
              "period, uncorrelated, so the period jitter is sqrt(22) larger; a measurement of N periods averages it by "
              "sqrt(N). This is the white-noise floor of the instrument; it excludes the bias chain (bias.py) and the supply.\n")
    C.write_csv(os.path.join(C.OUT, "stage_noise.csv"), hdr, nrows)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        for c in C.CORNERS:
            n = C.pvt_name(c, 27, 1.2)
            ax[0].plot([max(k, 0.5) for k in CODES], [r[4] for r in rows if r[0] == n], "o-", label=c[4:])
        for t, v, ls in [(125, 1.08, "--"), (-40, 1.32, ":")]:
            n = C.pvt_name("mos_tt", t, v)
            ax[0].plot([max(k, 0.5) for k in CODES], [r[4] for r in rows if r[0] == n], "k" + ls + "o", label=f"tt {t} C {v} V")
        ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("code (log; code 0 plotted at 0.5)")
        ax[0].set_ylabel("stage delay / ps"); ax[0].grid(alpha=.3, which="both"); ax[0].legend(fontsize=8)
        ax[0].set_title("stage delay vs code")
        for k, sp in spectra.items():
            ax[1].loglog([r[0] for r in sp], [r[1] for r in sp], label=f"code {k}")
        ax[1].set_xlabel("Hz"); ax[1].set_ylabel("output noise / V/sqrt(Hz)"); ax[1].grid(alpha=.3, which="both"); ax[1].legend(fontsize=8)
        ax[1].set_title("stage output noise at the trip point")
        fig.tight_layout()
        fig.savefig(os.path.join(C.DOCS, "verify_stage.png"), dpi=110)
    except ImportError:
        pass

    C.write_md("stage", "".join(md))


if __name__ == "__main__":
    main()
