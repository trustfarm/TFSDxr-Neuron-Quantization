"""
TFSD8 vs FP8 — Input-following & Error Visualization (N=1000)
- Scenarios: RandomNormal, Poisson, Sigmoid, Sine, Triangle, AbruptJump, AbruptJump_Interpolated
- Outputs:
  * For each scenario: overlay plot (Input vs TFSD8 vs FP8)
  * For each scenario: semilogy(|error|) plot (TFSD8 vs FP8)
  * Summary metrics DataFrame printed and saved as CSV: TFSD8_vs_FP8_metrics.csv

Notes
- FP8: simplified E4M3 / E5M2 emulation with a single static per-series scale.
- TFSD8: residual accumulation + time gating (+ simple adaptive controller).
- The “AbruptJump” uses 1e2 instead of ~1e100 to avoid trivial scale collapse in this toy demo.
"""

import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Any

np.random.seed(42)

# ===============================
# FP8 helpers (simplified emu)
# ===============================

def fp8_values(fmt: str = "E4M3") -> np.ndarray:
    """
    Return a list of representable FP8 values (finite only, no subnormals/NaN/Inf).
    - E4M3: 1 sign, 4 exponent, 3 mantissa, bias=7, exp in [1..14]
    - E5M2: 1 sign, 5 exponent, 2 mantissa, bias=15, exp in [1..30]
    """
    if fmt == "E4M3":
        e_bits, m_bits, bias, e_min, e_max = 4, 3, 7, 1, 14
    elif fmt == "E5M2":
        e_bits, m_bits, bias, e_min, e_max = 5, 2, 15, 1, 30
    else:
        raise ValueError("Unsupported FP8 format")

    values = [0.0]
    for s in (1.0, -1.0):
        for e in range(e_min, e_max + 1):
            base = 2.0 ** (e - bias)
            for m in range(0, 2**m_bits):
                frac = 1.0 + m / (2**m_bits)
                values.append(s * base * frac)
    return np.array(sorted(values))


def fp8_quant_dequant(x: np.ndarray, fmt: str, scale: float):
    """Quantize-dequantize via nearest representable FP8 value with a global scale."""
    vals = fp8_values(fmt)
    x_scaled = x / scale
    diffs = np.abs(x_scaled.reshape(-1,1) - vals.reshape(1,-1))
    idx = np.argmin(diffs, axis=1)
    y = vals[idx] * scale
    return y, vals


def fp8_max_abs(fmt: str) -> float:
    vals = fp8_values(fmt)
    return float(np.max(np.abs(vals)))


def estimate_scale_static(x: np.ndarray, fmt: str = "E4M3",
                          percentile: float = 99.5, headroom: float = 0.9) -> float:
    """
    Static per-series scale: map |x| percentile to FP8 max * headroom.
    """
    p = np.percentile(np.abs(x), percentile)
    vmax = fp8_max_abs(fmt)
    s = p / (vmax * headroom + 1e-12)
    if s <= 0:
        s = 1.0
    return float(s)


def lsb_at_one(fmt: str) -> float:
    """Approximate LSB step size around 1.0 in the *unscaled* FP8 domain."""
    vals = fp8_values(fmt)
    i = int((np.abs(vals - 1.0)).argmin())
    j = i + 1 if i + 1 < len(vals) else i
    step = abs(vals[j] - vals[i]) if j != i else 2**-7
    return float(step)


# ===============================
# TFSD8 emulation (toy)
# ===============================

def tfsd8_run(x: np.ndarray,
              fmt_act: str = "E4M3",
              theta_lsb: float = 1.0,       # theta in units of local LSB around 1.0
              T_silence: int = 2,
              T_emit: int = 2,
              T_refractory: int = 4,        # kept constant in this toy
              r_clip_x_theta: float = 3.0,
              adaptive: bool = True,
              event_target: float = 0.07,   # target event rate (7%)
              window: int = 50
              ) -> Dict[str, Any]:
    """
    Runs a simplified TFSD8 loop on a 1D series:
     - Baseline FP8 dequant (d_hat)
     - Residual accumulation with clip
     - Time gating (Debounce via stable sign count, Emit via theta & cooldown)
     - Simple adaptive controller every 'window' samples adjusting theta/T_silence/T_emit
    Returns y_tfsd, y_fp8, pulses, theta_series, and metrics.
    """
    # scale / quantization base
    scale = estimate_scale_static(x, fmt=fmt_act, percentile=99.5, headroom=0.9)
    lsb = lsb_at_one(fmt_act) * scale
    theta = theta_lsb * lsb
    r_clip = r_clip_x_theta * theta

    y_fp8, _ = fp8_quant_dequant(x, fmt_act, scale)  # baseline
    y_tfsd = np.zeros_like(x)
    pulses_arr = np.zeros_like(x)
    theta_series = np.zeros_like(x)

    cooldown = 0
    stable = 0
    last_sign = 0.0
    r = 0.0
    events = 0

    event_hist = []
    err_hist = []

    for t in range(len(x)):
        d_hat = y_fp8[t]
        # residual update & clip
        r = np.clip(r + (x[t] - d_hat), -r_clip, r_clip)

        sgn = np.sign(r)
        if sgn == last_sign and sgn != 0:
            stable += 1
        else:
            stable = 1 if sgn != 0 else 0
            last_sign = sgn

        can_emit = (cooldown == 0) and (stable >= T_silence) and (abs(r) >= theta)
        pulse = sgn if can_emit else 0.0
        if can_emit:
            r -= pulse * theta
            cooldown = T_emit
            events += 1
        else:
            cooldown = max(0, cooldown - 1)

        # reconstructed output at this step (toy)
        y_tfsd[t] = d_hat + pulse * theta
        pulses_arr[t] = pulse
        theta_series[t] = theta

        # logs for adaptation
        event_hist.append(1 if pulse != 0 else 0)
        err_hist.append(abs(x[t] - y_tfsd[t]))

        # simple adaptive controller
        if adaptive and (t+1) % window == 0:
            er = np.mean(event_hist[-window:])
            ebar = np.mean(err_hist[-window:]) + 1e-12
            # heuristic band control on event rate with error sanity
            if er < 0.6 * event_target and ebar > np.median(err_hist) * 1.05:
                theta *= 0.9
                T_silence = max(1, T_silence - 1)
                r_clip = max(r_clip, r_clip_x_theta * theta)
            elif er > 1.4 * event_target:
                theta *= 1.1
                T_emit = min(6, T_emit + 1)
                r_clip = max(2*theta, r_clip * 0.95)

    # metrics
    err_tfsd = np.abs(x - y_tfsd)
    err_fp8  = np.abs(x - y_fp8)

    def mape(y_true, y_pred, eps=1e-9):
        denom = np.maximum(np.abs(y_true), eps)
        return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)

    def rmse(y_true, y_pred):
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    metrics = {
        "MAPE_TFSD8(%)": mape(x, y_tfsd),
        "RMSE_TFSD8": rmse(x, y_tfsd),
        "MAPE_FP8(%)": mape(x, y_fp8),
        "RMSE_FP8": rmse(x, y_fp8),
        "EventRate_TFSD8(%)": 100.0 * events / len(x),
        "theta_final": float(theta),
        "scale": float(scale),
    }

    return {
        "y_fp8": y_fp8,
        "y_tfsd": y_tfsd,
        "pulses": pulses_arr,
        "theta_series": theta_series,
        "metrics": metrics,
    }


# ===============================
# Data generators (N=1000)
# ===============================

N = 1000
t_idx = np.arange(N)

def data_random_normal():
    return np.random.normal(0, 1.0, N)

def data_poisson():
    lam = 5.0 + 4.0 * np.sin(2*np.pi * t_idx / 200.0)
    lam = np.clip(lam, 0.1, None)
    return np.random.poisson(lam).astype(float)

def data_sigmoid():
    x = (t_idx - 500.0) / 100.0
    return 2.0 / (1.0 + np.exp(-x)) - 1.0  # ~[-1, 1]

def data_sine():
    return 1.5 * np.sin(2*np.pi * t_idx / 100.0)

def data_triangle():
    period = 200
    phase = t_idx % period
    up = (phase < period/2)
    tri = np.where(up, phase/(period/2), 2 - phase/(period/2))
    tri = tri * 2 - 1  # [-1, 1]
    return tri

def data_abrupt_jump(interpolate=False, steps=10):
    """
    Abrupt jump from ~0 to large value; for demo uses 1e2 (not 1e100) to avoid blow-ups.
    If interpolate=True, spread the jump across 'steps' points (micro-stepping).
    """
    x = np.zeros(N)
    x[:400] = 0.01
    x[400] = 1e2
    x[401:800] = 1e2
    x[800:] = 1.0
    if interpolate:
        for k in range(steps):
            idx = 400 - steps//2 + k
            if 0 <= idx < N:
                x[idx] = 0.01 + (k+1)/(steps) * (1e2 - 0.01)
    return x


# ===============================
# Run scenarios
# ===============================

scenarios = {
    "RandomNormal": data_random_normal(),
    "Poisson": data_poisson(),
    "Sigmoid": data_sigmoid(),
    "Sine": data_sine(),
    "Triangle": data_triangle(),
    "AbruptJump": data_abrupt_jump(interpolate=False),
    "AbruptJump_Interpolated": data_abrupt_jump(interpolate=True, steps=12),
}

results: Dict[str, Any] = {}
for name, x in scenarios.items():
    out = tfsd8_run(
        x, fmt_act="E4M3",
        theta_lsb=1.0, T_silence=2, T_emit=2, T_refractory=4,
        r_clip_x_theta=3.0, adaptive=True, event_target=0.07, window=50
    )
    results[name] = (x, out)

# ===============================
# Plotting helpers
# ===============================

def overlay_plot(name, x, y_tfsd, y_fp8):
    plt.figure(figsize=(10, 4))
    plt.plot(x, label="Input")
    plt.plot(y_tfsd, label="TFSD8")
    plt.plot(y_fp8, label="FP8")
    plt.title(f"{name}: Input vs TFSD8 vs FP8")
    plt.xlabel("t")
    plt.ylabel("value")
    plt.legend()
    plt.tight_layout()
    plt.show()

def error_plot(name, x, y_tfsd, y_fp8):
    e_t = np.abs(x - y_tfsd)
    e_f = np.abs(x - y_fp8)
    plt.figure(figsize=(10, 4))
    plt.semilogy(e_t, label="|error| TFSD8")
    plt.semilogy(e_f, label="|error| FP8")
    plt.title(f"{name}: Absolute Error (log scale)")
    plt.xlabel("t")
    plt.ylabel("|error| (log)")
    plt.legend()
    plt.tight_layout()
    plt.show()

# Generate all plots
for name, (x, out) in results.items():
    overlay_plot(name, x, out["y_tfsd"], out["y_fp8"])
    error_plot(name, x, out["y_tfsd"], out["y_fp8"])

# ===============================
# Summary table
# ===============================

rows = []
for name, (x, out) in results.items():
    m = out["metrics"]
    rows.append({
        "Scenario": name,
        "MAPE_TFSD8(%)": m["MAPE_TFSD8(%)"],
        "RMSE_TFSD8": m["RMSE_TFSD8"],
        "MAPE_FP8(%)": m["MAPE_FP8(%)"],
        "RMSE_FP8": m["RMSE_FP8"],
        "EventRate_TFSD8(%)": m["EventRate_TFSD8(%)"],
        "theta_final": m["theta_final"],
        "scale": m["scale"],
    })
df = pd.DataFrame(rows).round(6)
print("\n=== TFSD8 vs FP8 — Summary Metrics ===")
print(df.to_string(index=False))

# Save CSV
df.to_csv("TFSD8_vs_FP8_metrics.csv", index=False)
print("\nSaved: TFSD8_vs_FP8_metrics.csv")
