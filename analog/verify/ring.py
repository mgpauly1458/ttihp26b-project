#!/usr/bin/env python3
"""The whole macro: frequency against code over corners, Monte Carlo, noise.

    ./run.sh python3 verify/ring.py [--mc 64] [--stat 32] [--codes ...] [--jobs N]
                                    [--skip-corners] [--skip-mc] [--skip-noise]

What is tested
  spice/tt_analog_ring.spice, the finger-by-finger netlist the layout
  generator wrote and LVS matched against the GDS: the DAC, the bias chain,
  the NAND, the ten stages and the output buffer, driving 15 fF. Every run
  starts with `enable` low (ring held, clk_out high), releases it after two
  nominal periods, and measures over the last 16 of 40 nominal periods, so
  every code is simulated for the same number of cycles at the same points
  per cycle. Start-up time (release to first edge) comes for free.

Four questions
  1. Corners: f(code) and supply current at all 45 PVT points, the ring
     stopped with enable=0 (clk_out level and current), start-up time, and
     supply pushing (df/dVDD). The fast/slow ratio over PVT is the range the
     bench will see; monotonicity in code must hold at every point.
  2. Mismatch Monte Carlo (mos_tt_mismatch, every finger its own offset):
     f at codes 0, 15, 16, 127, 128, 255 per sample. The two major-carry
     steps are where a binary DAC can go non-monotonic; the test counts
     samples where f(16) <= f(15) or f(128) <= f(127), and reports the
     spread of the end points.
  3. Process Monte Carlo (mos_tt_stat, all devices together): spread of
     f(0), f(16), f(255) from die to die.
  4. Noise, transient: ngspice has no device noise in transient, so the
     bias node's own current noise is measured by `.noise` (with the node
     impedance from an `ac` at the same operating point) and injected back
     as a `trnoise` current source of that density while the ring runs for
     600 periods. Period jitter and the jitter of 50-period means are read
     off the edge times. A run without the source gives the simulator's
     numerical floor, which is reported beside it. The stage's own thermal
     jitter is estimated separately in stage.py.
"""
import argparse
import csv
import math
import os

import common as C

CODES_CORNER = [0, 1, 2, 4, 8, 16, 32, 64, 128, 255]
CODES_MM = [0, 15, 16, 127, 128, 255]
CODES_STAT = [0, 16, 255]
CODES_NOISE = [16, 128]
CLOAD = "15f"
N_HOLD, N_RUN, N_MEAS = 2, 40, 16       # nominal periods: hold, total, measured (the last ones)
KMAX = 12                               # rising edges looked for in the window


def dut_exposed(mismatch=False):
    """The macro's netlist with vbp and vbn added to the port list, so a
    top-level source can touch the bias node (for the noise injection)."""
    src = C.dut(mismatch).split()[1]
    dst = os.path.join(C.OUT, os.path.basename(src).replace(".spice", ".exposed.spice"))
    if not os.path.exists(dst):
        with open(src) as fh, open(dst, "w") as out:
            for line in fh:
                if line.startswith(".subckt tt_analog_ring"):
                    line = line.rstrip("\n") + " vbp vbn\n"
                out.write(line)
    return f".include {dst}\n"


def deck(models, vdd, code, mismatch=False, expose=False, noise_ina=None, noise_nt=None, n_run=N_RUN, n_meas=N_MEAS, step_div=150):
    T = 1 / C.f_nom(code)
    t_en, tstop, tmeas, step = N_HOLD * T, n_run * T, (n_run - n_meas) * T, T / step_div
    ports = f"{C.CODE_PORTS} enable clk_out VPWR 0" + (" vbp vbn" if expose else "")
    inc = dut_exposed(mismatch) if expose else C.dut(mismatch)
    noise = f"Inz 0 vbp trnoise({noise_ina:.4g} {noise_nt:.4g} 0 0)\n" if noise_ina else ""
    edges = "\n".join(f"meas tran t{k} when v(clk_out)={vdd}/2 rise={k} from=$&tm" for k in range(1, KMAX + 1))
    return f"""* tt_analog_ring, code {code}
{models}{inc}Vdd VPWR 0 {vdd}
{C.code_dc(vdd, code)}Ven enable 0 pulse(0 {vdd} {t_en:.4g} 0.1n)
Xdut {ports} tt_analog_ring
Cload clk_out 0 {CLOAD}
{noise}.control
op
let idd_dis = -i(Vdd)
echo "idd_dis=$&idd_dis vbp=$&v(xdut.vbp) vbn=$&v(xdut.vbn) clk_dis=$&v(clk_out)"
tran {step:.4g} {tstop:.4g}
let tm = {tmeas:.4g}
let ten = {t_en:.4g}
meas tran vhold_min min v(clk_out) from=0 to=$&ten
meas tran tfirst when v(clk_out)={vdd}/2 fall=1
{edges}
meas tran idd_run avg i(Vdd) from=$&tm
meas tran vmax max v(clk_out) from=$&tm
meas tran vmin min v(clk_out) from=$&tm
{"wrdata clk.txt v(clk_out)" if noise_nt is not None else ""}
.endc
.end
"""


def frequency(log):
    ts = [C.meas(log, f"t{k}") for k in range(1, KMAX + 1)]
    ts = [t for t in ts if t is not None]
    if len(ts) < 2:
        return None, len(ts)
    return (len(ts) - 1) / (ts[-1] - ts[0]), len(ts)


def parse(log, code):
    f, n = frequency(log)
    tfirst = C.meas(log, "tfirst")
    t_en = N_HOLD / C.f_nom(code)
    return dict(f=f, nedges=n, idd=-(C.meas(log, "idd_run") or 0), idd_dis=C.meas(log, "idd_dis"),
                vbp=C.meas(log, "vbp"), vbn=C.meas(log, "vbn"), clk_dis=C.meas(log, "clk_dis"),
                vhold=C.meas(log, "vhold_min"), tstart=(tfirst - t_en) if tfirst else None,
                vmax=C.meas(log, "vmax"), vmin=C.meas(log, "vmin"))


def edges_from_wrdata(path, vth):
    rows = C.read_wrdata(path)
    t = [r[0] for r in rows]
    v = [r[1] for r in rows]
    out = []
    for i in range(1, len(t)):
        if v[i - 1] < vth <= v[i]:
            out.append(t[i - 1] + (vth - v[i - 1]) * (t[i] - t[i - 1]) / (v[i] - v[i - 1]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc", type=int, default=64)
    ap.add_argument("--stat", type=int, default=32)
    ap.add_argument("--codes", default=",".join(map(str, CODES_CORNER)))
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--skip-corners", action="store_true")
    ap.add_argument("--skip-mc", action="store_true")
    ap.add_argument("--skip-noise", action="store_true")
    a = ap.parse_args()
    codes = [int(c) for c in a.codes.split(",")]
    md = []

    # ---- 1. corners ---------------------------------------------------------------
    if not a.skip_corners:
        decks = {f"{C.pvt_name(c, t, v)}_code{k}": deck(C.corner(c, t), v, k) for c, t, v in C.PVT for k in codes}
        res = C.run_decks(decks, a.jobs, tag="ring")
        rows = []
        table = {}
        for c, t, v in C.PVT:
            n = C.pvt_name(c, t, v)
            for k in codes:
                log, d = res[f"{n}_code{k}"]
                m = parse(log, k)
                if m["f"] is None:
                    print("FAILED", n, k, log[-400:]); continue
                table[(n, k)] = m
                rows.append([n, c, t, v, k, m["f"], m["nedges"], m["idd"], m["idd_dis"], m["vbp"], m["vbn"],
                             m["clk_dis"], m["vhold"], m["tstart"], m["vmax"], m["vmin"]])
        hdr = ["PVT", "corner", "temp", "vdd", "code", "f_hz", "edges", "idd_run_A", "idd_dis_A", "vbp", "vbn",
               "clk_dis_V", "clk_hold_min_V", "tstart_s", "vmax", "vmin"]
        C.write_csv(os.path.join(C.OUT, "ring_corners.csv"), hdr, rows)

        # stage.py prediction at typical, if available
        pred = {}
        p = os.path.join(C.OUT, "stage_corners.csv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                pred[(r["PVT"], int(r["code"]))] = float(r["11-stage ring MHz"])

        md.append("## Whole block: frequency and current against code\n")
        md.append("The macro's own netlist (the LVS reference), clk_out into 15 fF, released from enable=0 and "
                  "measured over the last 16 of 40 nominal periods.\n\n**Signoff corners:**\n")
        sig = []
        for pvt in C.SIGNOFF:
            n = C.pvt_name(*pvt)
            for k in codes:
                m = table.get((n, k))
                if m:
                    sig.append([n, k, m["f"] / 1e6, m["idd"] * 1e6, m["idd_dis"] * 1e6, m["vbp"], m["vbn"],
                                m["tstart"] * 1e9 if m["tstart"] else None, pred.get((n, k))])
        md.append(C.table(["PVT", "code", "f MHz", "Idd running uA", "Idd disabled uA", "vbp V", "vbn V", "start-up ns", "stage.py predicts MHz"],
                          sig, [None, "%d", "%.2f", "%.1f", "%.1f", "%.3f", "%.3f", "%.1f", "%.1f"]))
        md.append("\n**All 45 PVT points**, frequency extremes per code, and monotonicity:\n")
        ext = []
        for k in codes:
            rk = [(n, m) for (n, kk), m in table.items() if kk == k]
            lo = min(rk, key=lambda x: x[1]["f"]); hi = max(rk, key=lambda x: x[1]["f"])
            ext.append([k, lo[1]["f"] / 1e6, lo[0], hi[1]["f"] / 1e6, hi[0], hi[1]["f"] / lo[1]["f"]])
        md.append(C.table(["code", "slowest MHz", "at", "fastest MHz", "at", "fast/slow"], ext, ["%d", "%.2f", None, "%.2f", None, "%.2f"]))
        nonmono = []
        for c, t, v in C.PVT:
            n = C.pvt_name(c, t, v)
            fs = [table[(n, k)]["f"] for k in codes if (n, k) in table]
            if any(b <= a_ for a_, b in zip(fs, fs[1:])):
                nonmono.append(n)
        md.append(f"\nf(code) monotonic over the codes simulated at {45 - len(nonmono)} of 45 PVT points"
                  + (f"; NOT at {', '.join(nonmono)}" if nonmono else "") + ".\n")
        # stopped ring, start-up, pushing
        held = [m for m in table.values()]
        clk_dis_min = min(m["clk_dis"] for m in held if m["clk_dis"] is not None)
        vhold_min = min(m["vhold"] for m in held if m["vhold"] is not None)
        tstart_max = max(((m["tstart"] or 0), n_k) for n_k, m in table.items())
        md.append(f"\n**Stopped** (enable=0, every PVT point and code): clk_out never below {clk_dis_min:.3f} V at the "
                  f"operating point, {vhold_min:.3f} V during the hold. Disabled supply current is the DAC's "
                  f"({min(m['idd_dis'] for m in held)*1e6:.1f} .. {max(m['idd_dis'] for m in held)*1e6:.0f} uA over "
                  f"codes and corners). **Start-up**: worst release-to-first-edge "
                  f"{tstart_max[0]*1e9:.0f} ns at {tstart_max[1][0]} code {tstart_max[1][1]}.\n")
        push = []
        for c in ["mos_tt"]:
            for k in [16, 128, 255]:
                lo = table.get((C.pvt_name(c, 27, 1.08), k)); mid = table.get((C.pvt_name(c, 27, 1.2), k)); hi = table.get((C.pvt_name(c, 27, 1.32), k))
                if lo and mid and hi:
                    push.append([k, lo["f"] / 1e6, mid["f"] / 1e6, hi["f"] / 1e6, 100 * (hi["f"] - lo["f"]) / mid["f"] / 0.24])
                tc = table.get((C.pvt_name(c, -40, 1.2), k)); th = table.get((C.pvt_name(c, 125, 1.2), k))
                if tc and th and mid:
                    push[-1] += [tc["f"] / 1e6, th["f"] / 1e6, 1e6 * (th["f"] - tc["f"]) / mid["f"] / 165]
        md.append("\n**Supply pushing and temperature coefficient** (typical process):\n")
        md.append(C.table(["code", "f @1.08 V", "f @1.20 V", "f @1.32 V", "%/V", "f @-40 C", "f @125 C", "ppm/C"],
                          push, ["%d", "%.1f", "%.1f", "%.1f", "%.1f", "%.1f", "%.1f", "%.0f"]))

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(11, 4))
            for cc in C.CORNERS:
                n = C.pvt_name(cc, 27, 1.2)
                ax[0].plot(codes, [table[(n, k)]["f"] / 1e6 for k in codes if (n, k) in table], "o-", label=cc[4:])
            for t, v, ls in [(125, 1.08, "--"), (-40, 1.32, ":")]:
                n = C.pvt_name("mos_tt", t, v)
                ax[0].plot(codes, [table[(n, k)]["f"] / 1e6 for k in codes if (n, k) in table], "k" + ls + "o", label=f"tt {t} C {v} V")
            ax[0].set_xlabel("code"); ax[0].set_ylabel("f / MHz"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=8)
            ax[0].set_title("frequency vs code, corners")
            for k in [0, 16, 255]:
                fs = sorted(table[(C.pvt_name(c, t, v), k)]["f"] / 1e6 for c, t, v in C.PVT if (C.pvt_name(c, t, v), k) in table)
                ax[1].plot(fs, [k] * len(fs), "|", ms=14, label=f"code {k}")
            ax[1].set_xscale("log"); ax[1].set_xlabel("f / MHz over the 45 PVT points"); ax[1].set_ylabel("code")
            ax[1].grid(alpha=.3, which="both"); ax[1].legend(fontsize=8); ax[1].set_title("PVT spread")
            fig.tight_layout(); fig.savefig(os.path.join(C.DOCS, "verify_ring_corners.png"), dpi=110)
        except ImportError:
            pass

    # ---- 2/3. Monte Carlo ---------------------------------------------------------------
    if not a.skip_mc:
        decks = {}
        for s in range(a.mc):
            for k in CODES_MM:
                decks[f"mm{s}_code{k}"] = deck(C.mc("mismatch", 5000 + s), 1.2, k, mismatch=True)
        for s in range(a.stat):
            for k in CODES_STAT:
                decks[f"st{s}_code{k}"] = deck(C.mc("stat", 6000 + s), 1.2, k)
        res = C.run_decks(decks, a.jobs, tag="ring_mc")
        mm = {}
        for s in range(a.mc):
            fs = {k: parse(res[f"mm{s}_code{k}"][0], k)["f"] for k in CODES_MM}
            if all(fs.values()):
                mm[s] = fs
        st = {}
        for s in range(a.stat):
            fs = {k: parse(res[f"st{s}_code{k}"][0], k)["f"] for k in CODES_STAT}
            if all(fs.values()):
                st[s] = fs
        C.write_csv(os.path.join(C.OUT, "ring_mm.csv"), ["sample"] + [f"f{k}" for k in CODES_MM],
                    [[s] + [fs[k] for k in CODES_MM] for s, fs in mm.items()])
        C.write_csv(os.path.join(C.OUT, "ring_stat.csv"), ["sample"] + [f"f{k}" for k in CODES_STAT],
                    [[s] + [fs[k] for k in CODES_STAT] for s, fs in st.items()])
        if mm:
            md.append(f"\n## Whole block: mismatch Monte Carlo, {len(mm)} samples (mos_tt_mismatch, 27 C, 1.2 V)\n")
            rows = []
            for k in CODES_MM:
                mu, sd, lo, hi = C.stats([fs[k] for fs in mm.values()])
                rows.append([k, mu / 1e6, sd / 1e6, 100 * sd / mu, lo / 1e6, hi / 1e6])
            md.append(C.table(["code", "mean MHz", "sigma MHz", "sigma %", "min", "max"], rows, ["%d", "%.2f", "%.3f", "%.2f", "%.2f", "%.2f"]))
            bad16 = sum(1 for fs in mm.values() if fs[16] <= fs[15])
            bad128 = sum(1 for fs in mm.values() if fs[128] <= fs[127])
            st16 = [fs[16] - fs[15] for fs in mm.values()]; st128 = [fs[128] - fs[127] for fs in mm.values()]
            md.append(f"\nMajor-carry steps: f(16) - f(15) = {min(st16)/1e6:.3f} .. {max(st16)/1e6:.3f} MHz, "
                      f"f(128) - f(127) = {min(st128)/1e6:.3f} .. {max(st128)/1e6:.3f} MHz. Non-monotonic samples: "
                      f"{bad16} at 15->16, {bad128} at 127->128, of {len(mm)}.\n")
        if st:
            md.append(f"\n## Whole block: process Monte Carlo, {len(st)} samples (mos_tt_stat, 27 C, 1.2 V)\n")
            rows = []
            for k in CODES_STAT:
                mu, sd, lo, hi = C.stats([fs[k] for fs in st.values()])
                rows.append([k, mu / 1e6, sd / 1e6, 100 * sd / mu, lo / 1e6, hi / 1e6])
            md.append(C.table(["code", "mean MHz", "sigma MHz", "sigma %", "min", "max"], rows, ["%d", "%.2f", "%.3f", "%.2f", "%.2f", "%.2f"]))
            r = [fs[255] / fs[0] for fs in st.values()]
            md.append(f"\nf(255)/f(0), the span of the scale, {min(r):.1f} .. {max(r):.1f} across samples.\n")

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 3, figsize=(15, 4))
            if mm:
                ax[0].hist([fs[255] / 1e6 for fs in mm.values()], bins=20, alpha=.7, label="mismatch")
            if st:
                ax[0].hist([fs[255] / 1e6 for fs in st.values()], bins=20, alpha=.7, label="process")
            ax[0].set_xlabel("f(255) / MHz"); ax[0].set_ylabel("samples"); ax[0].legend(); ax[0].set_title("code 255")
            if mm:
                ax[1].hist([(fs[16] - fs[15]) / 1e6 for fs in mm.values()], bins=20, alpha=.7, label="f(16)-f(15)")
                ax[1].hist([(fs[128] - fs[127]) / 1e6 for fs in mm.values()], bins=20, alpha=.7, label="f(128)-f(127)")
                ax[1].axvline(0, color="r", ls="--"); ax[1].set_xlabel("step / MHz"); ax[1].legend(); ax[1].set_title("major-carry steps, mismatch")
            if st:
                ax[2].hist([fs[0] / 1e6 for fs in st.values()], bins=20, alpha=.7, label="process")
            if mm:
                ax[2].hist([fs[0] / 1e6 for fs in mm.values()], bins=20, alpha=.7, label="mismatch")
            ax[2].set_xlabel("f(0) / MHz"); ax[2].legend(); ax[2].set_title("code 0")
            fig.tight_layout(); fig.savefig(os.path.join(C.DOCS, "verify_ring_mc.png"), dpi=110)
        except ImportError:
            pass

    # ---- 4. noise -------------------------------------------------------------------------
    if not a.skip_noise:
        # (a) the bias node's current noise density and impedance, ring held
        decks = {}
        for k in CODES_NOISE:
            decks[f"nz_code{k}"] = f"""* bias node noise + impedance at code {k}
{C.corner()}{dut_exposed()}Vdd VPWR 0 1.2
{C.code_dc(1.2, k)}Ven enable 0 0
Xdut {C.CODE_PORTS} enable clk_out VPWR 0 vbp vbn tt_analog_ring
Cload clk_out 0 {CLOAD}
Iac 0 vbp dc 0 ac 1
.control
op
ac dec 10 1k 10G
wrdata z.txt vm(vbp)
noise v(vbp) Iac dec 10 1k 10G
setplot noise1
wrdata sv.txt onoise_spectrum
.endc
.end
"""
        res = C.run_decks(decks, a.jobs, tag="ring_noise")
        inj = {}
        nrows = []
        for k in CODES_NOISE:
            log, d = res[f"nz_code{k}"]
            try:
                z = C.read_wrdata(os.path.join(d, "z.txt")); sv = C.read_wrdata(os.path.join(d, "sv.txt"))
            except FileNotFoundError:
                print("noise deck failed", k, log[-500:]); continue
            # current noise density S_i(f) = S_v(f) / |Z(f)|^2; take its level over 10 MHz - 1 GHz (white part)
            si = [(zz[0], (s[1] ** 2) / (zz[1] ** 2)) for zz, s in zip(z, sv)]
            white = [x[1] for x in si if 1e7 <= x[0] <= 1e9]
            si_white = sum(white) / len(white)
            zlow = z[0][1]
            inj[k] = (si_white ** 0.5, zlow, si)
            nrows.append([k, si_white ** 0.5 * 1e12, zlow / 1e3, sv[0][1] * 1e9, (si_white ** 0.5) * zlow * 1e9])
        md.append("\n## Whole block: noise on the bias node and the jitter it makes\n")
        md.append(C.table(["code", "vbp current noise pA/sqrt(Hz) (white, 10M-1G)", "vbp impedance kohm (1 kHz)", "vbp voltage noise nV/sqrt(Hz) at 1 kHz", "white-part voltage noise nV/sqrt(Hz)"],
                          nrows, ["%d", "%.2f", "%.1f", "%.1f", "%.1f"]))
        # (b) transient with and without the injected noise
        decks = {}
        for k in CODES_NOISE:
            if k not in inj:
                continue
            T = 1 / C.f_nom(k)
            nt = T / 50
            ina = inj[k][0] / (2 * nt) ** 0.5           # one-sided PSD S = 2 NA^2 NT
            n_run = 640
            decks[f"tj_code{k}_noise"] = deck(C.corner(), 1.2, k, expose=True, noise_ina=ina, noise_nt=nt, n_run=n_run, n_meas=600, step_div=600)
            decks[f"tj_code{k}_quiet"] = deck(C.corner(), 1.2, k, expose=True, noise_ina=None, noise_nt=nt, n_run=n_run, n_meas=600, step_div=600)
        res = C.run_decks(decks, a.jobs, tag="ring_jitter")
        jrows = []
        for k in CODES_NOISE:
            for kind in ["quiet", "noise"]:
                key = f"tj_code{k}_{kind}"
                if key not in res:
                    continue
                log, d = res[key]
                try:
                    ed = edges_from_wrdata(os.path.join(d, "clk.txt"), 0.6)
                except FileNotFoundError:
                    print("jitter deck failed", key, log[-500:]); continue
                ed = [t for t in ed if t > (N_HOLD + 20) / C.f_nom(k)]     # skip start-up
                per = [b - a_ for a_, b in zip(ed, ed[1:])]
                if len(per) < 100:
                    print("too few periods", key, len(per)); continue
                mu, sd, lo, hi = C.stats(per)
                blocks = [sum(per[i:i + 50]) / 50 for i in range(0, len(per) - 49, 50)]
                bmu, bsd, _, _ = C.stats(blocks)
                jrows.append([k, kind, len(per), mu * 1e9, sd * 1e12, 1e6 * sd / mu, bsd * 1e12 if bsd else None,
                              1e6 * bsd / mu if bsd else None])
        md.append("\n**Transient with the bias-node current noise injected** (typical, 27 C, 1.2 V; 600 periods; `quiet` = same run without the source, the numerical floor):\n")
        md.append(C.table(["code", "run", "periods", "mean period ns", "period jitter ps rms", "ppm", "jitter of 50-period means ps", "ppm"],
                          jrows, ["%d", None, "%d", "%.4f", "%.2f", "%.0f", "%.2f", "%.0f"]))
        md.append("\nThe injected source carries the white part of the current noise every device on vbp contributes "
                  "(DAC units, diode, always-on units), measured by `.noise` at the same operating point and divided "
                  "by the node's impedance from an `ac` analysis. Flicker noise below 10 MHz is not injected: the "
                  "bias node's own time constant already filters it into slow drift, which a reciprocal count "
                  "averages, and the stage's own thermal jitter is in stage.py.\n")
        C.write_csv(os.path.join(C.OUT, "ring_jitter.csv"), ["code", "run", "periods", "mean_period_s", "sigma_period_s", "ppm", "sigma_50mean_s", "ppm50"], jrows)

    C.write_md("ring", "".join(md))


if __name__ == "__main__":
    main()
