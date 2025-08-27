# encdec_appendix_plots.py
# Usage:
#   pip install matplotlib numpy
#   python encdec_appendix_plots.py
import numpy as np
import matplotlib.pyplot as plt

# --- Appendix B: K Sensitivity ---
def simulate_emissions(K, seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1.0, 400)  # 1s window
    d = 0.15*np.sin(2*np.pi*4*t) + 0.05*rng.standard_normal(t.shape)
    lambda0 = 0.25
    E = 0
    thresh = lambda0*(2**E)*K
    T_emit = 0.02
    emitted = 0
    r = 0.0
    last_emit_t = -1e9
    for i, ti in enumerate(t):
        r += d[i]
        if (ti - last_emit_t) >= T_emit and abs(r) >= thresh:
            emitted += 1
            r -= np.sign(r)*thresh
            last_emit_t = ti
    return emitted

Ks = np.linspace(0.5, 3.0, 11)
counts = np.array([simulate_emissions(K) for K in Ks])

plt.figure(figsize=(7,4), dpi=130)
plt.plot(Ks, counts, marker='o')
plt.title("K Sensitivity: Emission count vs K (1s window)")
plt.xlabel("K (threshold multiplier)")
plt.ylabel("ΣΔ emission count")
plt.tight_layout()
plt.savefig("appendix_B_K_sensitivity.svg", format="svg")
plt.close()

# --- Appendix C: BASE_TICK resync timeline ---
t = np.linspace(0,1.0,201)
x = 20 + 0.5*np.sin(2*np.pi*1.2*t)     # ground truth
xhat = x.copy()
xhat[(t>=0.35)&(t<0.6)] += 0.25        # drift (token drop)
xhat[t>=0.6] = x[t>=0.6]               # resync at BASE_TICK

plt.figure(figsize=(9,4.2), dpi=130)
plt.plot(t, x, label="x (truth)")
plt.plot(t, xhat, linestyle='--', label="x̂ (decoder)")
for tt, lbl in [(0.35,"drop start"), (0.6,"BASE_TICK")]:
    plt.axvline(tt, linestyle=':', alpha=0.7)
    ymin = min(x.min(), xhat.min())
    plt.text(tt+0.005, ymin+0.05, lbl, rotation=90, va="bottom", fontsize=9)
plt.title("BASE_TICK resync example (conceptual)")
plt.xlabel("time (s)")
plt.ylabel("value")
plt.legend()
plt.tight_layout()
plt.savefig("appendix_C_BASE_TICK_resync.svg", format="svg")
plt.close()

print("generated: appendix_B_K_sensitivity.svg, appendix_C_BASE_TICK_resync.svg")
