
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(42)
N = 10000
x = (np.random.rand(N).astype(np.float32) * 2 - 1) * 1000.0  # uniform [-1000, 1000]
EPS = 1e-6

def fp8_e5m2_pack(values: np.ndarray):
    v = values.astype(np.float32)
    sign = (v < 0).astype(np.uint8)
    av = np.abs(v).astype(np.float32)
    is_zero = av == 0.0
    e = np.floor(np.log2(np.maximum(av, EPS))).astype(np.int32)
    e_biased = e + 15
    frac = av / np.power(2.0, e, dtype=np.float32)
    m = np.clip(frac - 1.0, 0.0, 1.0 - 1e-8)
    m_q = np.floor(m * 4 + 0.5)
    m_q = np.clip(m_q, 0, 3).astype(np.int32)
    e_biased = np.clip(e_biased, 0, 31).astype(np.int32)
    frac_q = 1.0 + (m_q.astype(np.float32) / 4.0)
    v_q = frac_q * np.power(2.0, (e_biased - 15).astype(np.float32))
    v_q[is_zero] = 0.0
    v_q *= np.where(sign == 1, -1.0, 1.0).astype(np.float32)
    return v_q

UE_BIAS = 7
UE_E_MIN = -7
UE_E_MAX = 8
UE_LEVELS = np.array([1.0 + (k + 0.5) / 8.0 for k in range(8)], dtype=np.float32)

def ue8m0_pack(values: np.ndarray):
    v = values.astype(np.float32)
    sign = np.sign(v).astype(np.float32)
    av = np.abs(v).astype(np.float32)
    out = np.zeros_like(av, dtype=np.float32)
    nonzero = av > 0.0
    av_nz = av[nonzero]
    e = np.floor(np.log2(np.maximum(av_nz, EPS))).astype(np.int32)
    e = np.clip(e, UE_E_MIN, UE_E_MAX)
    frac = av_nz / np.power(2.0, e, dtype=np.float32)
    idx = np.argmin(np.abs(frac.reshape(-1, 1) - UE_LEVELS.reshape(1, -1)), axis=1)
    frac_q = UE_LEVELS[idx].astype(np.float32)
    recon = frac_q * np.power(2.0, e.astype(np.float32))
    out[nonzero] = recon
    out *= np.where(sign < 0, -1.0, 1.0).astype(np.float32)
    return out

x_fp8 = fp8_e5m2_pack(x)
x_ue  = ue8m0_pack(x)

err_fp8 = (np.abs(x_fp8 - x) / np.maximum(np.abs(x), EPS)) * 100.0
err_ue  = (np.abs(x_ue  - x) / np.maximum(np.abs(x), EPS)) * 100.0

abs_x = np.abs(x)
min_v, max_v = abs_x.min(), abs_x.max()
bins = np.linspace(min_v, max_v, 4)
labels = ["Low |x|", "Mid |x|", "High |x|"]
bin_idx = np.digitize(abs_x, bins[1:-1], right=False)

import numpy as np
rows = []
stats = [("Min", np.min), ("Median", np.median), ("Max", np.max)]
for i, lab in enumerate(labels):
    mask = bin_idx == i
    fp8_stats = [float(func(err_fp8[mask])) for _, func in stats] if np.any(mask) else [np.nan]*3
    ue_stats  = [float(func(err_ue[mask]))  for _, func in stats] if np.any(mask) else [np.nan]*3
    for (slabel, _), fp8_v, ue_v in zip(stats, fp8_stats, ue_stats):
        rows.append({
            "Range": lab,
            "Statistic": slabel,
            "FP8_E5M2_Error_%": round(fp8_v, 6) if fp8_v==fp8_v else None,
            "UE8M0_Error_%": round(ue_v, 6) if ue_v==ue_v else None
        })
summary_df = pd.DataFrame(rows, columns=["Range","Statistic","FP8_E5M2_Error_%","UE8M0_Error_%"])

# Plot
import matplotlib.pyplot as plt
idx_sample = np.random.choice(len(x), size=2000, replace=False)
plt.figure(figsize=(7,5))
plt.scatter(abs_x[idx_sample], err_fp8[idx_sample], s=6, alpha=0.5, label="FP8 E5M2")
plt.scatter(abs_x[idx_sample], err_ue[idx_sample], s=6, alpha=0.5, label="UE8M0")
plt.xlabel("|x| (FP32 true magnitude)")
plt.ylabel("Percent error (%)")
plt.title("Quantization Error vs Magnitude (10,000 random FP32)")
plt.legend()
plot_path = "UE8M0_vs_FP8_ErrorPlot.png"
plt.savefig(plot_path, dpi=140, bbox_inches="tight")

summary_df.to_csv("UE8M0_vs_FP8_ErrorSummary.csv", index=False)
print("Saved:", plot_path, "and UE8M0_vs_FP8_ErrorSummary.csv")
