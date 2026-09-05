"""Plot the inverter VTC and switching waveforms from the ngspice wrdata output."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# wrdata writes interleaved x/y column pairs, one pair per saved vector.
vtc = np.loadtxt("out/inverter_vtc.data")
vin, vout, _, gain = vtc[:, 0], vtc[:, 1], vtc[:, 2], vtc[:, 3]
tr = np.loadtxt("out/inverter_tran.data")
t, va, vy = tr[:, 0] * 1e9, tr[:, 1], tr[:, 3]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

ax1.plot(vin, vout, lw=2, color="#2a6fb5", label="V(Y)")
ax1.axvline(0.6183, ls="--", lw=1, color="#b5482a", label="trip = 618 mV")
ax1.plot(vin, -gain / 20, lw=1, color="#7a7a7a", alpha=0.7, label="|gain| / 20")
ax1.set_xlabel("V(A)  [V]"); ax1.set_ylabel("V(Y)  [V]")
ax1.set_title("Voltage transfer characteristic, VDD = 1.2 V")
ax1.grid(alpha=0.3); ax1.legend(fontsize=8); ax1.set_xlim(0, 1.2)

ax2.plot(t, va, lw=1.6, color="#7a7a7a", label="V(A) in")
ax2.plot(t, vy, lw=2, color="#2a6fb5", label="V(Y) out")
ax2.set_xlabel("time  [ns]"); ax2.set_ylabel("V")
ax2.set_title("Switching into 10 fF: $t_{PHL}$ = 38.5 ps, $t_{PLH}$ = 36.9 ps")
ax2.grid(alpha=0.3); ax2.legend(fontsize=8)

fig.tight_layout()
fig.savefig("../docs/inverter_sim.png", dpi=130)
print("wrote docs/inverter_sim.png")
