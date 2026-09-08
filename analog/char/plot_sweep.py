#!/usr/bin/env python3
"""Plot the sweep CSV: f(code) with the line through the origin and the code-8 point (compression visible), and supply current.

    ./run.sh python3 char/plot_sweep.py out/sweep.csv ../docs/analog_ring_sweep.png
"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, dst = sys.argv[1], sys.argv[2]
rows = [r for r in csv.DictReader(open(src))]
code = [int(r["code"]) for r in rows]
f = [float(r["f_hz"]) / 1e6 for r in rows]
idd = [float(r["idd_a"]) * 1e6 for r in rows]

fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2))
a.plot(code, f, "o-", label="ngspice, typical corner, 27 °C")
if 8 in code:
    k = f[code.index(8)] / 8
    a.plot([0, 255], [0, 255 * k], "--", color="gray", label="linear from code 8")
a.set_xlabel("code")
a.set_ylabel("clk_out frequency / MHz")
a.set_title("tt_analog_ring: frequency vs. DAC code")
a.grid(True, alpha=0.3)
a.legend()
b.plot(code, idd, "s-", color="C3")
b.set_xlabel("code")
b.set_ylabel("supply current / µA")
b.set_title("supply current (DAC + bias + ring)")
b.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(dst, dpi=130)
print("wrote", dst)
