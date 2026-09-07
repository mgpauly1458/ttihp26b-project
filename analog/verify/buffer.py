#!/usr/bin/env python3
"""The output buffer: full swing and clean edges into the tile's load.

    ./run.sh python3 verify/buffer.py [--jobs N]

What is tested
  csro_inv (0.5 / 0.3 um) followed by the 2 / 1 um inverter, as the top
  sheet has them after stage 10, driving clk_out into the two loads that
  bracket what the tile presents: 15 fF (a short wire and one gate) and
  108 fF (the Liberty's max_capacitance, what the flow is allowed to hang
  on the pin). The input is a 332 MHz square wave with 100 ps edges - the
  fastest code, the hardest case for the buffer.

Questions
  * Does the output reach both rails at the fastest code and heaviest
    load, at every PVT point? A clock that does not swing fully would be
    counted wrong by the divider's first flop.
  * Rise and fall times (20-80 %) and delay against load: these are the
    numbers the Liberty file carries at the typical corner; here they are
    seen at every corner.
"""
import argparse
import os

import common as C

LOADS = [0.015e-12, 0.108e-12]
F_IN = 332e6


def deck(models, vdd, cload):
    T = 1 / F_IN
    return f"""* output buffer into {cload*1e15:.0f} fF
{models}{C.blocks()}Vdd VPWR 0 {vdd}
Vin s10 0 pulse(0 {vdd} 0.2n 100p 100p {T/2 - 100e-12:.4g} {T:.4g})
XB1 s10 b1 VPWR 0 csro_inv
XMBP2 clk_out b1 VPWR VPWR sg13_lv_pmos w=2u l=0.13u ng=1
XMBN2 clk_out b1 0 0 sg13_lv_nmos w=1u l=0.13u ng=1
Cload clk_out 0 {cload}
.control
tran 2p {6*T:.4g}
let t4 = {4*T:.4g}
meas tran vmax max v(clk_out) from=$&t4
meas tran vmin min v(clk_out) from=$&t4
meas tran tr2 when v(clk_out)={0.2*vdd} rise=4
meas tran tr8 when v(clk_out)={0.8*vdd} rise=4
meas tran tf8 when v(clk_out)={0.8*vdd} fall=4
meas tran tf2 when v(clk_out)={0.2*vdd} fall=4
let trise = tr8 - tr2
let tfall = tf2 - tf8
echo "trise=$&trise tfall=$&tfall"
meas tran tin_r when v(s10)={vdd/2} rise=4
meas tran tout_r when v(clk_out)={vdd/2} rise=4
let tpd = tout_r - tin_r
echo "tpd=$&tpd"
.endc
.end
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()

    decks = {}
    for c, t, v in C.PVT:
        for cl in LOADS:
            decks[f"{C.pvt_name(c, t, v)}_{cl*1e15:.0f}fF"] = deck(C.corner(c, t), v, cl)
    res = C.run_decks(decks, a.jobs, tag="buffer")
    rows = []
    for c, t, v in C.PVT:
        for cl in LOADS:
            n = C.pvt_name(c, t, v)
            log, d = res[f"{n}_{cl*1e15:.0f}fF"]
            vmax, vmin = C.meas(log, "vmax"), C.meas(log, "vmin")
            if vmax is None:
                print("failed", n, cl, log[-300:]); continue
            rows.append([n, cl * 1e15, v, vmax, vmin, vmax / v, vmin / v,
                         C.meas(log, "trise") * 1e12, C.meas(log, "tfall") * 1e12, C.meas(log, "tpd") * 1e12])
    hdr = ["PVT", "load fF", "VDD", "V high", "V low", "high/VDD", "low/VDD", "rise 20-80 ps", "fall 20-80 ps", "delay ps"]
    fmt = [None, "%.0f", "%.2f", "%.3f", "%.4f", "%.3f", "%.4f", "%.0f", "%.0f", "%.0f"]
    C.write_csv(os.path.join(C.OUT, "buffer_corners.csv"), hdr, rows)
    md = ["## Output buffer: swing and edges at 332 MHz\n",
          "**Signoff corners**, both loads:\n",
          C.table(hdr, [r for p in C.SIGNOFF for r in rows if r[0] == C.pvt_name(*p)], fmt)]
    heavy = [r for r in rows if r[1] > 100]
    wh = min(heavy, key=lambda r: r[5]); wl = max(heavy, key=lambda r: r[6])
    sr = max(heavy, key=lambda r: r[7]); sf = max(heavy, key=lambda r: r[8])
    md.append(f"\n**All 45 PVT points into 108 fF**: lowest high level {wh[3]:.3f} V ({100*wh[5]:.1f} % of VDD) at {wh[0]}; "
              f"highest low level {wl[4]:.4f} V at {wl[0]}; slowest rise {sr[7]:.0f} ps at {sr[0]}, slowest fall {sf[8]:.0f} ps at {sf[0]}.\n")
    C.write_md("buffer", "".join(md))


if __name__ == "__main__":
    main()
