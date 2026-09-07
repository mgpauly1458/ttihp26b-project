"""Plot ideal vs. post-layout (kpex-extracted) inverter waveforms, side by side
with the ideal-only plot from plot.py."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

vtc = np.loadtxt("out/inverter_vtc.data")
vin, vout = vtc[:, 0], vtc[:, 1]
tr = np.loadtxt("out/inverter_tran.data")
t, va, vy = tr[:, 0] * 1e9, tr[:, 1], tr[:, 3]

vtc_p = np.loadtxt("out/inverter_vtc_pex.data")
vin_p, vout_p = vtc_p[:, 0], vtc_p[:, 1]
tr_p = np.loadtxt("out/inverter_tran_pex.data")
t_p, va_p, vy_p = tr_p[:, 0] * 1e9, tr_p[:, 1], tr_p[:, 3]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

ax1.plot(vin, vout, lw=2, color="#2a6fb5", label="ideal")
ax1.plot(vin_p, vout_p, lw=2, ls="--", color="#b5482a", label="post-layout (kpex)")
ax1.set_xlabel("V(A)  [V]"); ax1.set_ylabel("V(Y)  [V]")
ax1.set_title("VTC: ideal vs. post-layout")
ax1.grid(alpha=0.3); ax1.legend(fontsize=8); ax1.set_xlim(0, 1.2)

ax2.plot(t, vy, lw=2, color="#2a6fb5", label="ideal V(Y)")
ax2.plot(t_p, vy_p, lw=2, ls="--", color="#b5482a", label="post-layout V(Y)")
ax2.plot(t, va, lw=1.2, color="#7a7a7a", alpha=0.7, label="V(A) in")
ax2.set_xlabel("time  [ns]"); ax2.set_ylabel("V")
ax2.set_title("Switching into 10 fF: ideal vs. extracted parasitics")
ax2.grid(alpha=0.3); ax2.legend(fontsize=8)

fig.tight_layout()
fig.savefig("../docs/inverter_sim_post.png", dpi=130)
print("wrote docs/inverter_sim_post.png")
