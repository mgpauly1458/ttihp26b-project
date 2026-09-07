#!/usr/bin/env python3
"""Post-layout: where the parasitics are, block by block, and what they do.

    ./run.sh python3 verify/pex.py [--pex out/pex/tt_analog_ring.pex.spice] [--jobs N]

Two halves.

  1. Attribution. kpex extracts the flat macro; this sorts its capacitors by
     the net they hang on and the block that net belongs to (DAC and code
     buses, bias nodes, ring stages, output buffer), so each block's wiring
     load is a number next to the device capacitance it adds to. This is
     the "per-block extraction" a flat layout allows: the nets are labelled,
     the blocks are groups of nets.

  2. The same circuit twice. The whole macro is simulated pre-layout
     (spice/tt_analog_ring.spice) and post-layout (the kpex netlist) at the
     typical corner, codes 0, 16, 128, 255, and the block-level quantities
     are read off the internal nodes of the running ring: each stage's
     delay (s_k to s_k+1), the NAND's (s10 to s0), the buffer's (s10 to
     clk_out) and clk_out's edge times, the ripple the ring induces on vbp
     and vbn, and the RC settling of a code bus driven through 500 ohm. The
     ring frequency itself comes from ring.py's runs (pre: ring_corners.csv,
     post: ring_post_corners.csv) when they exist. docs/analog_ring_sim_post.png
     puts pre and post side by side.

kpex 2.5D extracts capacitance only; the metal resistances (the DAC's
0.3 um Metal1 bars carry tens of uA, sub-millivolt drops) are not in the
post-layout netlist and are argued, not simulated, in analog_layout_notes.md.
"""
import argparse
import csv
import os
import re

import common as C

CODES = [0, 16, 128, 255]
NODES = [f"s{k}" for k in range(11)] + ["b1", "clk_out", "vbp", "vbn"]
GROUPS = [("DAC and code buses", lambda n: n.startswith("code[")),
          ("bias nodes", lambda n: n in ("vbp", "vbn")),
          ("ring: stage outputs", lambda n: re.fullmatch(r"s\d+", n) is not None),
          ("ring: enable", lambda n: n == "enable"),
          ("ring: starved rails (unlabelled)", lambda n: n.startswith("n_")),
          ("output buffer", lambda n: n in ("b1", "clk_out"))]
GATE_CAP_FF = {"code[0]": 9.6, "code[1]": 19.4, "code[2]": 39.5, "code[3]": 79, "code[4]": 159,
               "code[5]": 320, "code[6]": 643, "code[7]": 1295, "enable": 2.2}   # Liberty, pre-layout


def value(s):
    m = re.fullmatch(r"([-\d.eE+]+)([a-zA-Z]*)", s)
    mult = {"a": 1e-18, "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "": 1}[m.group(2)[:1].lower() if m.group(2) else ""]
    return float(m.group(1)) * mult


def attribution(pex):
    caps = []
    for line in open(pex):
        if line.startswith("C"):
            t = line.split()
            caps.append((t[1], t[2], value(t[3])))
    per_net = {}
    for a, b, v in caps:
        for n, other in ((a, b), (b, a)):
            d = per_net.setdefault(n, {"total": 0, "supply": 0, "signal": 0, "partners": {}})
            d["total"] += v
            if other in ("VGND", "VPWR"):
                d["supply"] += v
            else:
                d["signal"] += v
            d["partners"][other] = d["partners"].get(other, 0) + v
    return caps, per_net


def deck(netlist, code, fscale):
    T = 1 / (C.f_nom(code) * fscale)
    t_en, tstop, step = 2 * T, 40 * T, T / 300
    probes = " ".join(f"v(xdut.{n})" if n != "clk_out" else "v(clk_out)" for n in NODES)
    return f"""* pre/post-layout in-situ block metrics, code {code}
{C.corner()}.include {netlist}
Vdd VPWR 0 1.2
{C.code_dc(1.2, code)}Ven enable 0 pulse(0 1.2 {t_en:.4g} 0.1n)
Xdut {C.CODE_PORTS} enable clk_out VPWR 0 tt_analog_ring
Cload clk_out 0 15f
.control
tran {step:.4g} {tstop:.4g}
let t0 = {tstop - 3 * T:.4g}
wrdata nodes.txt {probes}
.endc
.end
"""


def deck_bus(netlist, bit):
    """the code bus driven 0 -> 1.2 V through 500 ohm, ring disabled"""
    codes = "\n".join(f"Vc{k} code[{k}] 0 0" for k in range(8) if k != bit)
    return f"""* code[{bit}] bus RC settling through a 500 ohm driver
{C.corner()}.include {netlist}
Vdd VPWR 0 1.2
{codes}
Vdrv drv 0 pulse(0 1.2 1n 0.05n)
Rdrv drv code[{bit}] 500
Ven enable 0 0
Xdut {C.CODE_PORTS} enable clk_out VPWR 0 tt_analog_ring
Cload clk_out 0 15f
.control
tran 5p 40n
meas tran t10 when v(code[{bit}])=0.12 rise=1
meas tran t90 when v(code[{bit}])=1.08 rise=1
let trc = t90 - t10
echo "trc=$&trc"
.endc
.end
"""


def crossings(t, v, vth=0.6):
    out = []
    for i in range(1, len(t)):
        if (v[i - 1] < vth <= v[i]) or (v[i - 1] > vth >= v[i]):
            out.append((t[i - 1] + (vth - v[i - 1]) * (t[i] - t[i - 1]) / (v[i] - v[i - 1]), v[i] > v[i - 1]))
    return out


def analyse_nodes(rundir, T):
    rows = C.read_wrdata(os.path.join(rundir, "nodes.txt"))
    t = [r[0] for r in rows]
    tail = [i for i, tt in enumerate(t) if tt > t[-1] - 3 * T]
    sig = {n: [r[2 * j + 1] for r in rows] for j, n in enumerate(NODES)}
    xs = {n: [c for c in crossings(t, sig[n]) if c[0] > t[-1] - 3 * T] for n in NODES}

    def delay(a, b):
        """mean time from a crossing of a to the next opposite-direction crossing of b"""
        ds = []
        for ta, ra in xs[a]:
            nxt = [tb for tb, rb in xs[b] if tb > ta and rb != ra]
            if nxt:
                ds.append(nxt[0] - ta)
        ds = [d for d in ds if d < T]                # drop the wrap-around at the window edge
        return sum(ds) / len(ds) if ds else None

    def delay_same(a, b):
        ds = []
        for ta, ra in xs[a]:
            nxt = [tb for tb, rb in xs[b] if tb > ta and rb == ra]
            if nxt:
                ds.append(nxt[0] - ta)
        ds = [d for d in ds if d < T]
        return sum(ds) / len(ds) if ds else None

    stages = [delay(f"s{k}", f"s{k+1}") for k in range(10)]        # s0->s1 ... s9->s10
    nand = delay("s10", "s0")
    buf = delay_same("s10", "clk_out")                              # two inversions
    rise = [c for c in xs["clk_out"] if c[1]]
    period = (rise[-1][0] - rise[0][0]) / (len(rise) - 1) if len(rise) > 1 else None
    rip = {n: max(sig[n][i] for i in tail) - min(sig[n][i] for i in tail) for n in ("vbp", "vbn")}
    return dict(stages=stages, nand=nand, buf=buf, period=period, rip=rip)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pex", default=os.path.join(C.ROOT, "out", "pex", "tt_analog_ring.pex.spice"))
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()
    pex = os.path.abspath(a.pex)
    pre = C.DUT_NETLIST
    md = []

    # ---- 1. attribution ----------------------------------------------------------
    caps, per_net = attribution(pex)
    total = sum(v for _, _, v in caps)
    md.append("## Post-layout: where the parasitic capacitance is\n")
    md.append(f"kpex 2.5D on the flat macro: {len(caps)} capacitors, {total*1e15:.0f} fF in total "
              "(each counted once; the per-net column counts a coupling cap on both of its nets).\n\n")
    grows = []
    for gname, pred in GROUPS:
        nets = [n for n in per_net if pred(n)]
        tot = sum(per_net[n]["total"] for n in nets)
        sup = sum(per_net[n]["supply"] for n in nets)
        grows.append([gname, len(nets), tot * 1e15, sup * 1e15, (tot - sup) * 1e15])
    md.append(C.table(["block (group of nets)", "nets", "parasitic fF", "to VPWR/VGND/substrate fF", "to other signals fF"],
                      grows, [None, "%d", "%.1f", "%.1f", "%.1f"]))
    md.append("\n**Per net**, the ones that matter:\n")
    nrows = []
    order = [f"code[{k}]" for k in range(8)] + ["vbp", "vbn", "enable"] + [f"s{k}" for k in range(11)] + ["b1", "clk_out"]
    for n in order:
        if n not in per_net:
            continue
        d = per_net[n]
        top = sorted(d["partners"].items(), key=lambda kv: -kv[1])[:3]
        gate = GATE_CAP_FF.get(n)
        nrows.append([n, d["total"] * 1e15, d["supply"] * 1e15, d["signal"] * 1e15,
                      ", ".join(f"{p} {v*1e15:.1f}" for p, v in top),
                      gate, 100 * d["total"] * 1e15 / gate if gate else None])
    md.append(C.table(["net", "parasitic fF", "to supplies", "to signals", "largest partners (fF)", "device cap on the net fF (Liberty, pre-layout)", "wire / device %"],
                      nrows, [None, "%.2f", "%.2f", "%.2f", None, "%.1f", "%.0f"]))
    md.append("\nThe stage outputs s1..s10 carry about 1.7 fF of wiring each: the output strap, its Metal1 jog across "
              "the row gap, and its coupling to the neighbouring straps and to the vbp/vbn/enable lines it runs under. "
              "A stage's own input is a 0.5 um and a 0.3 um gate at L = 0.13 um, about 1 fF, plus its drains; the "
              "wiring is therefore comparable to the device load, which is why the post-layout ring is slower (below). "
              "The code buses add 8 to 210 fF to gate loads of 10 to 1300 fF, i.e. 16 to 90 %, largest in fraction on "
              "the small bits whose few fingers still need a full-length bus.\n")

    # ---- 2. the same circuit twice -------------------------------------------------
    decks = {}
    for code in CODES:
        decks[f"pre_code{code}"] = deck(pre, code, 1.0)
        decks[f"post_code{code}"] = deck(pex, code, 0.5)
    for bit in (0, 7):
        decks[f"bus_pre_bit{bit}"] = deck_bus(pre, bit)
        decks[f"bus_post_bit{bit}"] = deck_bus(pex, bit)
    res = C.run_decks(decks, a.jobs, tag="pex")
    m = {}
    for which, fs in (("pre", 1.0), ("post", 0.5)):
        for code in CODES:
            log, d = res[f"{which}_code{code}"]
            try:
                m[(which, code)] = analyse_nodes(d, 1 / (C.f_nom(code) * fs))
            except (FileNotFoundError, ZeroDivisionError):
                print("FAILED", which, code, log[-300:])
    md.append("\n## Post-layout: the same circuit twice (typical, 27 C, 1.2 V)\n")
    rows = []
    for code in CODES:
        pr, po = m.get(("pre", code)), m.get(("post", code))
        if not pr or not po:
            continue
        sp = [x for x in pr["stages"] if x]; so = [x for x in po["stages"] if x]
        rows.append([code, 1 / pr["period"] / 1e6, 1 / po["period"] / 1e6, 100 * (1 / po["period"]) / (1 / pr["period"]) - 100,
                     sum(sp) / len(sp) * 1e12, sum(so) / len(so) * 1e12,
                     pr["nand"] * 1e12 if pr["nand"] else None, po["nand"] * 1e12 if po["nand"] else None,
                     pr["buf"] * 1e12 if pr["buf"] else None, po["buf"] * 1e12 if po["buf"] else None,
                     pr["rip"]["vbp"] * 1e3, po["rip"]["vbp"] * 1e3, pr["rip"]["vbn"] * 1e3, po["rip"]["vbn"] * 1e3])
    md.append(C.table(["code", "f pre MHz", "f post MHz", "change %", "stage delay pre ps", "post ps", "NAND pre ps", "post ps",
                       "buffer s10->clk_out pre ps", "post ps", "vbp ripple pre mV", "post mV", "vbn ripple pre mV", "post mV"],
                      rows, ["%d", "%.2f", "%.2f", "%.0f", "%.0f", "%.0f", "%.0f", "%.0f", "%.0f", "%.0f", "%.2f", "%.2f", "%.2f", "%.2f"]))
    brows = []
    for bit in (0, 7):
        brows.append([bit, C.meas(res[f"bus_pre_bit{bit}"][0], "trc") * 1e12, C.meas(res[f"bus_post_bit{bit}"][0], "trc") * 1e12])
    md.append("\n**Code bus settling** (10-90 %, driven 0 -> 1.2 V through 500 ohm, ring disabled):\n")
    md.append(C.table(["code bit", "pre-layout ps", "post-layout ps"], brows, ["%d", "%.0f", "%.0f"]))
    md.append("\nStage delay is the mean over the ten stages of the time from a crossing of s_k to the next crossing of "
              "s_k+1, read off the running ring over its last three periods; the NAND is s10 to s0, the buffer s10 to "
              "clk_out. The bias ripple is the peak-to-peak movement of vbp and vbn while the ring runs, which the "
              "layout's coupling of the stage straps to the bias lines increases. Code bus settling is what the tile's "
              "driver sees; the code is a DC control, so nanoseconds do not matter.\n")
    C.write_csv(os.path.join(C.OUT, "pex_blocks.csv"),
                ["code", "f_pre", "f_post", "stage_pre", "stage_post", "nand_pre", "nand_post", "buf_pre", "buf_post",
                 "vbp_rip_pre", "vbp_rip_post", "vbn_rip_pre", "vbn_rip_post"],
                [[r[0], r[1], r[2], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]] for r in rows])

    # ---- 3. frequency against code pre vs post, from ring.py's runs when present -----
    def load(name):
        p = os.path.join(C.OUT, name)
        if not os.path.exists(p):
            return {}
        out = {}
        for r in csv.DictReader(open(p)):
            out[(r["PVT"], int(r["code"]))] = float(r["f_hz"])
        return out
    fpre, fpost = load("ring_corners.csv"), load("ring_post_corners.csv")
    if fpre and fpost:
        md.append("\n**Frequency against code, pre and post layout, signoff corners** (from `ring.py` and `ring.py --netlist <pex>`):\n")
        frows = []
        for sp in C.SIGNOFF:
            n = C.pvt_name(*sp)
            for k in sorted({kk for (nn, kk) in fpost if nn == n}):
                if (n, k) in fpre:
                    frows.append([n, k, fpre[(n, k)] / 1e6, fpost[(n, k)] / 1e6, 100 * fpost[(n, k)] / fpre[(n, k)]])
        md.append(C.table(["PVT", "code", "f pre MHz", "f post MHz", "post/pre %"], frows, [None, "%d", "%.2f", "%.2f", "%.0f"]))

    # ---- figure ---------------------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
        # (a) f vs code
        if fpre and fpost:
            for sp, col in zip(C.SIGNOFF, ["#2a6fb5", "#b5482a", "#3a9a3a"]):
                n = C.pvt_name(*sp)
                ks = sorted(k for (nn, k) in fpost if nn == n and (n, k) in fpre)
                ax[0].plot(ks, [fpre[(n, k)] / 1e6 for k in ks], "o-", color=col, label=f"{n} pre")
                ax[0].plot(ks, [fpost[(n, k)] / 1e6 for k in ks], "s--", color=col, label=f"{n} post-layout")
        else:
            ax[0].plot(CODES, [r[1] for r in rows], "o-", label="pre-layout")
            ax[0].plot(CODES, [r[2] for r in rows], "s--", label="post-layout (kpex)")
        ax[0].set_xlabel("code"); ax[0].set_ylabel("f / MHz"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=7)
        ax[0].set_title("frequency vs code: ideal vs. extracted parasitics")
        # (b) stage delays at code 255 and 16
        import numpy as np
        for code, off, col in ((16, -0.2, "#2a6fb5"), (255, 0.2, "#b5482a")):
            pr, po = m.get(("pre", code)), m.get(("post", code))
            if pr and po:
                labels = [f"s{k}>s{k+1}" for k in range(10)] + ["NAND", "buffer"]
                vp = [(x or 0) * 1e12 for x in pr["stages"]] + [(pr["nand"] or 0) * 1e12, (pr["buf"] or 0) * 1e12]
                vo = [(x or 0) * 1e12 for x in po["stages"]] + [(po["nand"] or 0) * 1e12, (po["buf"] or 0) * 1e12]
                x = np.arange(len(labels))
                ax[1].bar(x + off - 0.1, vp, 0.2, color=col, alpha=.5, label=f"code {code} pre")
                ax[1].bar(x + off + 0.1, vo, 0.2, color=col, label=f"code {code} post")
                ax[1].set_xticks(x); ax[1].set_xticklabels(labels, rotation=60, fontsize=7)
        ax[1].set_yscale("log"); ax[1].set_ylabel("delay / ps"); ax[1].grid(alpha=.3, which="both"); ax[1].legend(fontsize=7)
        ax[1].set_title("per-stage delay in the running ring")
        # (c) bias ripple
        for n, col in (("vbp", "#2a6fb5"), ("vbn", "#b5482a")):
            ax[2].plot(CODES, [m[("pre", c)]["rip"][n] * 1e3 for c in CODES if ("pre", c) in m], "o-", color=col, label=f"{n} pre")
            ax[2].plot(CODES, [m[("post", c)]["rip"][n] * 1e3 for c in CODES if ("post", c) in m], "s--", color=col, label=f"{n} post")
        ax[2].set_xlabel("code"); ax[2].set_ylabel("bias ripple / mV p-p"); ax[2].grid(alpha=.3); ax[2].legend(fontsize=7)
        ax[2].set_title("ring-induced ripple on the bias nodes")
        fig.tight_layout()
        fig.savefig(os.path.join(C.DOCS, "analog_ring_sim_post.png"), dpi=120)
    except ImportError:
        pass

    C.write_md("pex", "".join(md))


if __name__ == "__main__":
    main()
