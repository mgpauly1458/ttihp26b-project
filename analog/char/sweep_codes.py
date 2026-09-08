#!/usr/bin/env python3
"""Frequency and supply current of the ring against DAC code, one ngspice process per code in parallel.

    ./run.sh python3 char/sweep_codes.py [--netlist FILE] [--codes 0,1,...] [--corner mos_tt] [--temp 27]
                                         [--vdd 1.2] [--tstop 3u] [--disabled] [--jobs N] [--out out/sweep.csv]

Writes the CSV (code, f_hz, idd_a, vbp_v, vbn_v, nrise, vout_avg) and prints it; decks and logs go to <out>.d/.
- Frequency from eight periods in the second half of the run (one period if only two edges); tstop must let the slowest code settle.
"""
import argparse
import csv
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(os.environ.get("PDK_ROOT", "/foss/pdks"),
                      os.environ.get("PDK", "ihp-sg13g2"),
                      "libs.tech/ngspice/models/cornerMOSlv.lib")
VDD = 1.2


def deck(netlist, code, corner, tstop, temp, vdd, enable):
    bits = "\n".join(f"Vc{k} code[{k}] 0 {vdd if (code >> k) & 1 else 0}" for k in range(8))
    ports = " ".join(f"code[{k}]" for k in range(8))
    return f"""* tt_analog_ring code sweep: code={code}
.lib {MODELS} {corner}
.option temp={temp}
.include {netlist}
Vdd VPWR 0 {vdd}
Ven enable 0 {vdd if enable else 0}
{bits}
Xdut {ports} enable clk_out VPWR 0 tt_analog_ring
Cload clk_out 0 15f
.control
op
let idd = -i(Vdd)
let vbp = v(xdut.vbp)
let vbn = v(xdut.vbn)
echo "OP idd=$&idd vbp=$&vbp vbn=$&vbn"
tran 20p {tstop}
let thalf = {tstop}/2
meas tran t1 when v(clk_out)={vdd}/2 rise=1 from=$&thalf
meas tran t2 when v(clk_out)={vdd}/2 rise=2 from=$&thalf
meas tran t9 when v(clk_out)={vdd}/2 rise=9 from=$&thalf
meas tran vout_avg avg v(clk_out) from=$&thalf
.endc
.end
"""


def run(args, code):
    # one directory per output file, so parallel sweeps never share decks
    d = os.path.splitext(os.path.abspath(args.out))[0] + ".d"
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"code{code}.spice")
    with open(path, "w") as fh:
        fh.write(deck(os.path.abspath(args.netlist), code, args.corner, args.tstop,
                      args.temp, args.vdd, not args.disabled))
    p = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, cwd=d)
    log = p.stdout + p.stderr
    with open(path.replace(".spice", ".log"), "w") as fh:
        fh.write(log)
    return code, log


def parse(log):
    def m(name):
        r = re.search(rf"^\s*{name}\s*=\s*([-\d.eE+]+)", log, re.M)
        return float(r.group(1)) if r else None
    op = re.search(r"OP idd=([-\d.eE+]+) vbp=([-\d.eE+]+) vbn=([-\d.eE+]+)", log)
    idd, vbp, vbn = (float(x) for x in op.groups()) if op else (None, None, None)
    t1, t2, t9 = m("t1"), m("t2"), m("t9")
    if t1 and t9:
        f, nrise = 8 / (t9 - t1), 9
    elif t1 and t2:
        f, nrise = 1 / (t2 - t1), 2
    else:
        f, nrise = 0.0, 0
    return f, idd, vbp, vbn, nrise, m("vout_avg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist", default=os.path.join(ROOT, "spice", "tt_analog_ring.spice"))
    ap.add_argument("--codes", default="0,1,2,3,4,6,8,12,16,24,32,48,64,96,128,160,192,224,255")
    ap.add_argument("--corner", default="mos_tt")
    ap.add_argument("--temp", type=float, default=27)
    ap.add_argument("--vdd", type=float, default=VDD)
    ap.add_argument("--tstop", default="3u")
    ap.add_argument("--disabled", action="store_true", help="enable=0: ring must be stopped")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "sweep.csv"))
    args = ap.parse_args()
    codes = [int(c) for c in args.codes.split(",")]
    with ThreadPoolExecutor(args.jobs) as ex:
        results = list(ex.map(lambda c: run(args, c), codes))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "f_hz", "idd_a", "vbp_v", "vbn_v", "nrise", "vout_avg"])
        print(f"{'code':>5} {'f_MHz':>9} {'Idd_uA':>8} {'vbp':>6} {'vbn':>6} {'edges':>5} {'vout':>5}")
        for code, log in results:
            f, idd, vbp, vbn, nrise, vavg = parse(log)
            w.writerow([code, f, idd, vbp, vbn, nrise, vavg])
            fmt = lambda v, s: (s % v) if v is not None else "   n/a"
            print(f"{code:>5} {fmt(f/1e6 if f else 0, '%9.3f')} {fmt(idd*1e6 if idd else 0, '%8.1f')} "
                  f"{fmt(vbp, '%6.3f')} {fmt(vbn, '%6.3f')} {nrise:>5} {fmt(vavg, '%5.2f')}")


if __name__ == "__main__":
    main()
