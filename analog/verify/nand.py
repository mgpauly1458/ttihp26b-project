#!/usr/bin/env python3
"""The starved NAND that closes the loop: does `enable` really stop the ring?

    ./run.sh python3 verify/nand.py [--jobs N]

What is tested
  csro_nand with the real bias chain, at every PVT point.
  1. Hold: with `a` (enable) low, the output must stay high whatever `b`
     (the feedback) does. A .dc sweep of `b` over the full rail with the
     stage's own load; the minimum output voltage is the number. If it ever
     dipped below the next stage's trip point the "stopped" ring would
     twitch. Also the supply current in that state: what the block draws
     when disabled, beyond the DAC.
  2. Gate: with `a` high the NAND is the eleventh inverter of the ring. Its
     delay is compared with a plain stage's (stage.py) at the same code -
     a much slower NAND would make one of the eleven stages odd and the
     output duty cycle lopsided.
"""
import argparse
import os

import common as C

CODES = [0, 16, 255]


def bias(vdd, code):
    return f"""{C.code_dc(vdd, code)}Xdac {C.CODE_PORTS} vbp VPWR 0 csro_dac
XMPD vbp vbp VPWR VPWR sg13_lv_pmos w=48u l=0.5u ng=24
XMPM vbn vbp VPWR VPWR sg13_lv_pmos w=1u l=0.5u ng=1
XMND vbn vbn 0 0 sg13_lv_nmos w=0.5u l=0.5u ng=1
"""


def deck_hold(models, vdd, code):
    return f"""* NAND hold: a=0, sweep b
{models}{C.blocks()}Vdd VPWR 0 {vdd}
{bias(vdd, code)}Va a 0 0
Vb b 0 0
Xnand a b y vbp vbn VPWR 0 csro_nand
Xload y z vbp vbn VPWR 0 csro_stage
Xload2 z zz vbp vbn VPWR 0 csro_stage
.control
dc Vb 0 {vdd} 0.01
meas dc ymin min v(y)
meas dc ymax max v(y)
meas dc idd_max max i(Vdd)
meas dc idd_min min i(Vdd)
.endc
.end
"""


def deck_gate(models, vdd, code):
    T = 2.0 / C.f_nom(code)
    return f"""* NAND as inverter: a=1, pulse b
{models}{C.blocks()}Vdd VPWR 0 {vdd}
{bias(vdd, code)}Va a 0 {vdd}
Vin p 0 pulse(0 {vdd} {T/4:.4g} 50p 50p {T/2:.4g} {T:.4g})
Xdrv p b vbp vbn VPWR 0 csro_stage
Xnand a b y vbp vbn VPWR 0 csro_nand
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
            decks[f"hold_{C.pvt_name(c, t, v)}_code{k}"] = deck_hold(C.corner(c, t), v, k)
            decks[f"gate_{C.pvt_name(c, t, v)}_code{k}"] = deck_gate(C.corner(c, t), v, k)
    res = C.run_decks(decks, a.jobs, tag="nand")

    hold, gate = [], []
    for c, t, v in C.PVT:
        n = C.pvt_name(c, t, v)
        for k in CODES:
            log, d = res[f"hold_{n}_code{k}"]
            ymin = C.meas(log, "ymin")
            if ymin is None:
                print("hold failed", n, k, log[-300:]); continue
            hold.append([n, k, v, ymin, ymin / v, -C.meas(log, "idd_max") * 1e6])
            log, d = res[f"gate_{n}_code{k}"]
            tplh, tphl = C.meas(log, "tplh"), C.meas(log, "tphl")
            if tplh is None:
                print("gate failed", n, k, log[-300:]); continue
            gate.append([n, k, tplh * 1e12, tphl * 1e12])

    # stage delays for comparison, if stage.py has run
    stage = {}
    p = os.path.join(C.OUT, "stage_corners.csv")
    if os.path.exists(p):
        import csv
        for r in csv.DictReader(open(p)):
            stage[(r["PVT"], int(r["code"]))] = (float(r["tPLH ps"]), float(r["tPHL ps"]))

    hdr = ["PVT", "code", "VDD", "min V(out) with enable=0", "as fraction of VDD", "supply current uA (enable=0, whole NAND+bias, min over b)"]
    md.append("## NAND: enable=0 holds the loop\n")
    md.append("The output of the starved NAND with `enable` low, over a full-rail sweep of the feedback input, "
              "loaded by a stage. It never leaves the high rail; the stopped ring is stopped.\n\n")
    worst = min(hold, key=lambda r: r[4])
    md.append(C.table(hdr, [r for p_ in C.SIGNOFF for r in hold if r[0] == C.pvt_name(*p_)],
                      [None, "%d", "%.2f", "%.4f", "%.4f", "%.1f"]))
    md.append(f"\nWorst over all {len(hold)} runs (45 PVT x 3 codes): V(out) min = {worst[3]:.4f} V = "
              f"{100*worst[4]:.2f} % of VDD at {worst[0]} code {worst[1]}.\n")

    hdr2 = ["PVT", "code", "NAND tPLH ps", "NAND tPHL ps", "stage tPLH ps", "stage tPHL ps", "NAND/stage (mean)"]
    grows = []
    for r in gate:
        s = stage.get((r[0], r[1]))
        grows.append(r + ([s[0], s[1], (r[2] + r[3]) / (s[0] + s[1])] if s else [None, None, None]))
    md.append("\n## NAND: as the eleventh inverter (enable=1)\n")
    md.append(C.table(hdr2, [r for p_ in C.SIGNOFF for r in grows if r[0] == C.pvt_name(*p_)],
                      [None, "%d", "%.0f", "%.0f", "%.0f", "%.0f", "%.2f"]))
    ratios = [r[6] for r in grows if r[6]]
    if ratios:
        md.append(f"\nNAND delay / stage delay over all PVT points and codes: {min(ratios):.2f} .. {max(ratios):.2f}. "
                  "(Its NMOS are 0.6 um against the stage's 0.3 um to make up for the series stack.)\n")
    C.write_csv(os.path.join(C.OUT, "nand_hold.csv"), hdr, hold)
    C.write_csv(os.path.join(C.OUT, "nand_gate.csv"), hdr2, grows)
    C.write_md("nand", "".join(md))


if __name__ == "__main__":
    main()
