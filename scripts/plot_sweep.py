#!/usr/bin/env python3
"""Plot the simulation sweep: recovered frequency against the model, per ring.

    scripts/plot_sweep.py build/sweep.csv docs/sweep.png

Writes <out> (eight overlays) and <out stem>_error (relative error of every live measurement,
so the quantisation gets its own axis). Timed-out codes are drawn at zero with a cross.
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RING_NAMES = {
    0: "0: 21-stage min drive",
    1: "1: copy of slot 0",
    2: "2: copy of slot 0",
    3: "3: copy of slot 0",
    4: "4: 21-stage high drive",
    5: "5: 11-stage min drive",
    6: "6: tap-select trim",
    7: "7: analog macro (model)",
}


def load(path):
    rows = {r: [] for r in range(8)}
    with open(path) as f:
        for row in csv.DictReader(f):
            rows[int(row["ring"])].append({
                "code": int(row["code"]),
                "tap": int(row["tap"]),
                "count": int(row["count"]),
                "timeout": int(row["timeout_error"]),
                "f_model": float(row["f_model_hz"]),
                "f_meas": float(row["f_meas_hz"]),
            })
    return rows


def main(csv_path, out_path):
    rows = load(csv_path)
    out = Path(out_path)

    fig, axes = plt.subplots(2, 4, figsize=(16, 7.5), sharex=True)
    for ring, ax in enumerate(axes.flat):
        r = rows[ring]
        codes = [m["code"] for m in r]
        ax.plot(codes, [m["f_model"] / 1e6 for m in r], "-", color="0.6", lw=3, label="model")
        live = [m for m in r if not m["timeout"]]
        dead = [m for m in r if m["timeout"]]
        ax.plot([m["code"] for m in live], [m["f_meas"] / 1e6 for m in live], ".", ms=3,
                color="C0", label="recovered")
        if dead:
            ax.plot([m["code"] for m in dead], [0] * len(dead), "x", ms=4, color="C3",
                    label="timeout")
        ax.set_title(RING_NAMES[ring], fontsize=10)
        ax.set_ylabel("MHz")
        ax.grid(True, alpha=0.3)
        if ring >= 4:
            ax.set_xlabel("trim code")
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("Ring oscillator meter, simulation sweep: recovered vs. model")
    fig.tight_layout()
    fig.savefig(out, dpi=110)

    fig, axes = plt.subplots(2, 4, figsize=(16, 7.5), sharex=True)
    for ring, ax in enumerate(axes.flat):
        live = [m for m in rows[ring] if not m["timeout"] and m["f_model"] > 0]
        codes = [m["code"] for m in live]
        err = [100.0 * (m["f_meas"] - m["f_model"]) / m["f_model"] for m in live]
        bound = [100.0 / m["count"] for m in live]      # +/-1 count, as a percentage
        ax.fill_between(codes, [-b for b in bound], bound, color="0.85", label="±1 count")
        ax.plot(codes, err, ".", ms=3, color="C0", label="error")
        ax.axhline(0, color="0.5", lw=0.8)
        ax.set_title(RING_NAMES[ring], fontsize=10)
        ax.set_ylabel("error, %")
        ax.grid(True, alpha=0.3)
        if ring >= 4:
            ax.set_xlabel("trim code")
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Relative error of the recovered frequency, with the ±1-count bound")
    fig.tight_layout()
    err_path = out.with_name(out.stem + "_error" + out.suffix)
    fig.savefig(err_path, dpi=110)
    print(f"wrote {out} and {err_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
