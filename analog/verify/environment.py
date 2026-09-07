#!/usr/bin/env python3
"""The macro in a hostile tile: supply noise, ground bounce, crosstalk.

    ./run.sh python3 verify/environment.py [--netlist FILE] [--tag env] [--jobs N]

The block shares one supply and one substrate with ~4500 standard cells, a
50 MHz reference clock, seven other ring oscillators and Tiny Tapeout's
project multiplexer, and its inputs arrive over the tile's own routing next
to all of that. None of it is in the PDK models, so this test builds it as
sources around the whole macro and measures what it does to the frequency
the counter would read. Worst-case by intent: the amplitudes are at or
beyond what a 1.2 V digital tile plausibly produces, so the answers are
bounds. Every run is 300 periods at typical process, 27 C, 1.2 V; the
`quiet` run of each code is the reference.

Cases
  supply ripple   VPWR with a 50 MHz square ripple (1 ns edges) of 10, 30
                  and 100 mV peak-to-peak: the reference clock's own
                  switching current through the PDN's impedance.
  supply noise    VPWR with 10 mV rms broadband random noise (trnoise,
                  100 ps): the digital logic's aggregate activity.
  supply step     VPWR drops 50 mV at mid-run and stays: another block
                  turning on. Frequency before and after, and how fast the
                  ring follows (it has no loop filter; it follows at once).
  ground bounce   VGND with a 30 mV peak-to-peak 50 MHz square: return
                  current of the neighbours through the shared substrate
                  and ground rails.
  code crosstalk  a 50 MHz full-swing aggressor coupled through 20 fF onto
                  code[0] (the lightest input, 9.6 fF of gate) and code[7]
                  (1.3 pF), the code line driven through 500 ohm as the
                  tile's buffer would. How far the gate moves and what the
                  frequency does.
  enable          the same aggressor onto `enable`: with the ring stopped
                  (does it stay stopped? clk_out level) and running (period
                  disturbance). Also a slow 5 ns enable edge: clean start?
  output          the aggressor coupled through 30 fF onto clk_out with its
                  15 fF load: extra edges at the divider's threshold would
                  be counted as ring cycles.

What the tile's multiplexer cannot do
  Tiny Tapeout's mux passes the pins; the design's register file latches a
  code only on a 4-clock write strobe and refuses writes while a measurement
  is running, so a glitch on the pins cannot change the code mid-measurement
  (that is the digital design's job and its testbenches). What reaches the
  macro is the register's output through the tile's buffers, which is what
  the crosstalk cases model.
"""
import argparse
import os

import common as C

CODES = [16, 255]
N_RUN = 300
VDD = 1.2
CLOAD = "15f"


def deck(netlist, code, case, params, n_run=N_RUN):
    T = 1 / C.f_nom(code)
    tstop, step = n_run * T, T / 150
    t_settle = 20 * T
    vpwr, vgnd = "VPWR", "0"
    src = [f"Vdd VPWR 0 dc {VDD}"]
    extra = []
    if case == "ripple":
        a = params["mvpp"] * 1e-3
        src = [f"Vdd VPWR vn dc {VDD}", f"Vn vn 0 pulse({-a/2:.4g} {a/2:.4g} 0 1n 1n 9n 20n)"]
    elif case == "noise":
        a = params["mvrms"] * 1e-3
        src = [f"Vdd VPWR vn dc {VDD}", f"Vn vn 0 dc 0 trnoise({a:.4g} 100p 0 0)"]
    elif case == "step":
        ts = tstop / 2
        src = [f"Vdd VPWR vn dc {VDD}", f"Vn vn 0 pwl(0 0 {ts:.4g} 0 {ts + 1e-9:.4g} -0.05)"]
    elif case == "bounce":
        a = params["mvpp"] * 1e-3
        vgnd = "gb"
        extra.append(f"Vgb gb 0 pulse({-a/2:.4g} {a/2:.4g} 0 1n 1n 9n 20n)")
    codes = []
    for k in range(8):
        lvl = VDD if (code >> k) & 1 else 0
        if case == "xcode" and k == params["bit"]:
            codes.append(f"Vc{k} c{k}s 0 {lvl}\nRd{k} c{k}s code[{k}] 500\nCx{k} ag code[{k}] 20f")
        else:
            codes.append(f"Vc{k} code[{k}] 0 {lvl}")
    if case == "xenable_stopped":
        en = "Ven ens 0 0\nRden ens enable 500\nCxe ag enable 20f"
    elif case == "xenable_running":
        en = f"Ven ens 0 {VDD}\nRden ens enable 500\nCxe ag enable 20f"
    elif case == "slow_enable":
        en = f"Ven enable 0 pulse(0 {VDD} {2*T:.4g} 5n)"
    else:
        en = f"Ven enable 0 {VDD}"
    if case.startswith("x"):
        extra.append("Vag ag 0 pulse(0 1.2 0 0.2n 0.2n 9.8n 20n)")
    if case == "xout":
        extra.append("Cxo ag clk_out 30f")
    return f"""* environment: {case} {params} code {code}
{C.corner()}.include {netlist}
{chr(10).join(src)}
{chr(10).join(codes)}
{en}
Xdut {C.CODE_PORTS} enable clk_out {vpwr} {vgnd} tt_analog_ring
Cload clk_out 0 {CLOAD}
{chr(10).join(extra)}
.control
tran {step:.4g} {tstop:.4g}
let ts = {t_settle:.4g}
meas tran vmin_out min v(clk_out) from=$&ts
meas tran vmax_out max v(clk_out) from=$&ts
{"meas tran vg_min min v(code[%d]) from=$&ts" % params["bit"] if case == "xcode" else ""}
{"meas tran vg_max max v(code[%d]) from=$&ts" % params["bit"] if case == "xcode" else ""}
{"meas tran ven_max max v(enable) from=$&ts" if case.startswith("xenable") else ""}
{"meas tran ven_min min v(enable) from=$&ts" if case.startswith("xenable") else ""}
wrdata clk.txt v(clk_out)
.endc
.end
"""


def edges(path, vth=0.6):
    rows = C.read_wrdata(path)
    t = [r[0] for r in rows]
    v = [r[1] for r in rows]
    out = []
    for i in range(1, len(t)):
        if v[i - 1] < vth <= v[i]:
            out.append(t[i - 1] + (vth - v[i - 1]) * (t[i] - t[i - 1]) / (v[i] - v[i - 1]))
    return out


def periods(path, code, t0=None, t1=None):
    T = 1 / C.f_nom(code)
    ed = [e for e in edges(path) if e > (t0 if t0 is not None else 20 * T)]
    if t1 is not None:
        ed = [e for e in ed if e < t1]
    per = [b - a for a, b in zip(ed, ed[1:])]
    return ed, per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist", default=C.DUT_NETLIST)
    ap.add_argument("--tag", default="env")
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()
    nl = os.path.abspath(a.netlist)

    cases = [("quiet", {}), ("ripple", {"mvpp": 10}), ("ripple", {"mvpp": 30}), ("ripple", {"mvpp": 100}),
             ("noise", {"mvrms": 10}), ("step", {}), ("bounce", {"mvpp": 30}),
             ("xcode", {"bit": 0}), ("xcode", {"bit": 7}), ("xenable_running", {}), ("xout", {})]
    decks = {}
    for code in CODES:
        for case, p in cases:
            name = f"{case}_{'_'.join(f'{k}{v}' for k, v in p.items())}_code{code}".replace("__", "_")
            decks[name] = deck(nl, code, case, p)
    decks["xenable_stopped_code255"] = deck(nl, 255, "xenable_stopped", {}, n_run=60)
    decks["slow_enable_code16"] = deck(nl, 16, "slow_enable", {}, n_run=60)
    decks["slow_enable_code255"] = deck(nl, 255, "slow_enable", {}, n_run=60)
    res = C.run_decks(decks, a.jobs, tag=a.tag)

    rows = []
    ref = {}
    for name, (log, d) in res.items():
        p = os.path.join(d, "clk.txt")
        if not os.path.exists(p):
            print("FAILED", name, log[-300:]); continue
        code = int(name.rsplit("code", 1)[1])
        if name.startswith("xenable_stopped"):
            ed = edges(p)
            rows.append([name, code, None, None, None, None, C.meas(log, "vmin_out"), len(ed),
                         f"enable peak {C.meas(log, 'ven_max'):.3f} V"])
            continue
        if name.startswith("slow_enable"):
            T = 1 / C.f_nom(code)
            ed, per = periods(p, code, t0=2 * T)
            mu, sd, lo, hi = C.stats(per[5:])
            first = ed[0] - 2 * T if ed else None
            rows.append([name, code, 1 / mu if mu else None, None, None, None, C.meas(log, "vmin_out"), len(ed),
                         f"first edge {first*1e9:.1f} ns after enable starts rising; shortest early period {min(per[:5])*1e9:.3f} ns"
                         if ed and per else "no edges"])
            continue
        if name.startswith("step"):
            T = N_RUN / C.f_nom(code) / 2
            _, pa = periods(p, code, t1=T)
            _, pb = periods(p, code, t0=T + 5e-9)
            fa, fb = 1 / (sum(pa) / len(pa)), 1 / (sum(pb) / len(pb))
            ed_all, per_all = periods(p, code)
            # settling: first period after the step within 0.1 % of the final mean
            k = next((i for i, (e, pp) in enumerate(zip(ed_all, per_all)) if e > T and abs(pp - 1 / fb) < 1e-3 / fb), None)
            rows.append([name, code, fa, None, None, None, C.meas(log, "vmin_out"), len(ed_all),
                         f"before {fa/1e6:.3f} MHz, after -50 mV {fb/1e6:.3f} MHz ({1e6*(fb-fa)/fa:.0f} ppm); "
                         f"settled within {(ed_all[k]-T)*1e9:.1f} ns" if k is not None else f"before {fa/1e6:.3f}, after {fb/1e6:.3f} MHz"])
            continue
        ed, per = periods(p, code)
        mu, sd, lo, hi = C.stats(per)
        blocks = [sum(per[i:i + 50]) / 50 for i in range(0, len(per) - 49, 50)]
        _, bsd, _, _ = C.stats(blocks)
        note = ""
        if name.startswith("xcode"):
            note = f"gate moves {C.meas(log, 'vg_min'):.3f}..{C.meas(log, 'vg_max'):.3f} V"
        if name.startswith("xenable_running"):
            note = f"enable dips to {C.meas(log, 'ven_min'):.3f} V"
        if name.startswith("xout"):
            note = f"{len(per)} periods in the window; shortest {lo*1e9:.3f} ns (a glitch would be a period << T)"
        rows.append([name, code, 1 / mu, sd, bsd, hi - lo, C.meas(log, "vmin_out"), len(ed), note])
        if name.startswith("quiet"):
            ref[code] = 1 / mu

    hdr = ["case", "code", "f MHz", "shift ppm vs quiet", "period jitter ps rms", "50-period mean jitter ps",
           "max-min period ps", "clk_out min V", "edges", "note"]
    out = []
    for r in sorted(rows, key=lambda r: (r[1], r[0])):
        f = r[2]
        shift = 1e6 * (f - ref[r[1]]) / ref[r[1]] if f and r[1] in ref else None
        out.append([r[0], r[1], f / 1e6 if f else None, shift, r[3] * 1e12 if r[3] else None, r[4] * 1e12 if r[4] else None,
                    r[5] * 1e12 if r[5] else None, r[6], r[7], r[8]])
    fmt = [None, "%d", "%.3f", "%.0f", "%.2f", "%.2f", "%.1f", "%.3f", "%d", None]
    which = "post-layout" if "pex" in os.path.basename(nl) else "pre-layout"
    md = [f"## Environment: supply, ground and crosstalk ({which} netlist, typical, 27 C, 1.2 V)\n",
          C.table(hdr, out, fmt),
          "\nShift is the mean frequency over the run against the quiet run at the same code; the counter reads that "
          "mean. Period jitter is what the ring does cycle to cycle; the 50-period mean jitter is closer to what a "
          "reciprocal count over hundreds of periods scatters by. 50 MHz ripple and bounce are square waves with 1 ns "
          "edges; the crosstalk aggressor is a full-swing 50 MHz square with 200 ps edges through 20 fF (30 fF onto clk_out), "
          "the victim driven through 500 ohm.\n"]
    C.write_csv(os.path.join(C.OUT, f"{a.tag}.csv"), hdr, out)
    C.write_md(a.tag, "".join(md))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        for code in CODES:
            amps = [0, 10, 30, 100]
            sh, jt = [], []
            for amp in amps:
                key = "quiet_code%d" % code if amp == 0 else f"ripple_mvpp{amp}_code{code}"
                r = next((x for x in out if x[0] == key), None)
                sh.append(r[3] if r and r[3] is not None else 0); jt.append(r[4] if r else 0)
            ax[0].plot(amps, sh, "o-", label=f"code {code}: shift ppm")
            ax[1].plot(amps, jt, "s--", label=f"code {code}: period jitter ps")
        ax[0].set_xlabel("50 MHz supply ripple / mV p-p"); ax[0].set_ylabel("mean frequency shift / ppm"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=8)
        ax[0].set_title(f"supply ripple: what the counter sees ({which})")
        ax[1].set_xlabel("50 MHz supply ripple / mV p-p"); ax[1].set_ylabel("period jitter / ps rms"); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8)
        ax[1].set_title("supply ripple: cycle-to-cycle jitter")
        fig.tight_layout()
        fig.savefig(os.path.join(C.DOCS, f"verify_{a.tag}.png"), dpi=110)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
