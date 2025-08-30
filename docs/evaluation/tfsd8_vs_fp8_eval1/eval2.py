# TFSD8 Parameter Tuning per Scenario (16 patterns) for FP8 formats E4M3 and E5M2
# - Grid search initial parameters with adaptive TFSD8 controller enabled
# - Compare tuned TFSD8 vs FP8 baseline (same format + static scale)
# - Produce:
#   * Summary table of defaults vs best params + metrics
#   * Marker/timetable per best run (per scenario+format) with parameter timelines
#   * Heatmaps of ΔRMSE per scenario (tuned TFSD8 - FP8 baseline)
#   * Top/Bottom lists by ΔRMSE
#   * Excel workbook with conditional formatting & per-scenario sheets
#
# Plots follow tool rules: matplotlib only, no explicit colors, single chart per figure.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple
from caas_jupyter_tools import display_dataframe_to_user

np.random.seed(7)

# ---------- FP8 helpers ----------
def fp8_values(fmt: str = "E4M3"):
    if fmt == "E4M3":
        bias, e_min, e_max, m_bits = 7, 1, 14, 3
    elif fmt == "E5M2":
        bias, e_min, e_max, m_bits = 15, 1, 30, 2
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
    vals = fp8_values(fmt)
    x_scaled = x / scale
    diffs = np.abs(x_scaled.reshape(-1,1) - vals.reshape(1,-1))
    idx = np.argmin(diffs, axis=1)
    y = vals[idx] * scale
    return y

def fp8_max_abs(fmt: str):
    return float(np.max(np.abs(fp8_values(fmt))))

def estimate_scale_static(x: np.ndarray, fmt: str, percentile: float = 99.5, headroom: float = 0.9):
    p = np.percentile(np.abs(x), percentile)
    vmax = fp8_max_abs(fmt)
    s = p / (vmax * headroom + 1e-12)
    return float(s if s > 0 else 1.0)

def lsb_at_one(fmt: str) -> float:
    vals = fp8_values(fmt)
    i = int(np.argmin(np.abs(vals - 1.0)))
    j = i + 1 if i + 1 < len(vals) else i
    step = abs(vals[j] - vals[i]) if j != i else 2**-7
    return float(step)

# ---------- TFSD8 sim with timelines & markers ----------
def tfsd8_run_with_timeline(
    x: np.ndarray,
    fmt_act: str,
    theta_lsb: float = 1.0,
    T_silence_init: int = 2,
    T_emit_init: int = 2,
    T_refractory: int = 4,
    r_clip_x_theta: float = 3.0,
    adaptive: bool = True,
    event_target: float = 0.07,
    window: int = 50,
    err_increase_ratio: float = 1.10,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    N = len(x)
    scale = estimate_scale_static(x, fmt=fmt_act, percentile=99.5, headroom=0.9)
    lsb = lsb_at_one(fmt_act) * scale
    theta = theta_lsb * lsb
    r_clip = r_clip_x_theta * theta

    y_fp8 = fp8_quant_dequant(x, fmt_act, scale)
    y_tfsd = np.zeros_like(x)
    pulses = np.zeros_like(x)

    theta_t = np.zeros(N)
    Tsil_t = np.zeros(N, dtype=int)
    Temit_t = np.zeros(N, dtype=int)
    err_t = np.zeros(N)
    err_fp8_t = np.zeros(N)

    cooldown = 0
    stable = 0
    last_sign = 0.0
    r = 0.0

    T_silence = T_silence_init
    T_emit = T_emit_init

    err_increase_idx = []
    theta_change_idx = []
    Tsil_change_idx = []
    Temit_change_idx = []

    event_hist = []
    err_hist = []

    prev_theta = theta
    prev_Tsil = T_silence
    prev_Temit = T_emit

    for t in range(N):
        d_hat = y_fp8[t]
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
        else:
            cooldown = max(0, cooldown - 1)
        pulses[t] = pulse

        y_tfsd[t] = d_hat + pulse * theta

        e_t = abs(x[t] - y_tfsd[t])
        e_f = abs(x[t] - y_fp8[t])
        err_t[t] = e_t
        err_fp8_t[t] = e_f
        if t > 0 and e_t > err_t[t-1] * err_increase_ratio:
            err_increase_idx.append(t)

        event_hist.append(1 if pulse != 0 else 0)
        err_hist.append(e_t)
        if adaptive and (t+1) % window == 0:
            er = np.mean(event_hist[-window:])
            med = np.median(err_hist[-window:])
            ebar = np.mean(err_hist[-window:])
            changed = False
            if er < 0.6 * event_target and ebar > med * 1.05:
                theta *= 0.9
                T_silence = max(1, T_silence - 1)
                r_clip = max(r_clip, r_clip_x_theta * theta)
                changed = True
            elif er > 1.4 * event_target:
                theta *= 1.1
                T_emit = min(6, T_emit + 1)
                r_clip = max(2*theta, r_clip * 0.95)
                changed = True
            if changed:
                theta_change_idx.append(t) if theta != prev_theta else None
                Tsil_change_idx.append(t) if T_silence != prev_Tsil else None
                Temit_change_idx.append(t) if T_emit != prev_Temit else None
                prev_theta, prev_Tsil, prev_Temit = theta, T_silence, T_emit

        theta_t[t] = theta
        Tsil_t[t] = T_silence
        Temit_t[t] = T_emit

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
        "EventRate_TFSD8(%)": 100.0 * np.count_nonzero(pulses) / len(x),
        "theta_init": float(theta_t[0]), "theta_final": float(theta_t[-1]),
        "T_silence_init": int(Tsil_t[0]), "T_silence_final": int(Tsil_t[-1]),
        "T_emit_init": int(Temit_t[0]), "T_emit_final": int(Temit_t[-1]),
        "scale": float(scale),
        "theta_changes": theta_change_idx,
        "Tsilence_changes": Tsil_change_idx,
        "Temit_changes": Temit_change_idx,
        "err_increase_idx": err_increase_idx,
    }
    timelines = {
        "x": x, "y_fp8": y_fp8, "y_tfsd": y_tfsd,
        "theta_t": theta_t, "Tsil_t": Tsil_t, "Temit_t": Temit_t,
        "err_t": err_t, "err_fp8_t": err_fp8_t, "pulses": pulses
    }
    return metrics, timelines

# ---------- Data generators (16 patterns, 1ms step) ----------
N = 1000
ms = np.arange(N)  # time in ms

def d_random_normal(): return np.random.normal(0, 1.0, N)
def d_poisson():
    lam = 5.0 + 4.0 * np.sin(2*np.pi * ms / 200.0); lam = np.clip(lam, 0.1, None)
    return np.random.poisson(lam).astype(float)
def d_sigmoid(): return 2.0 / (1.0 + np.exp(-(ms-500.0)/100.0)) - 1.0
def d_sine(): return 1.5 * np.sin(2*np.pi * ms / 100.0)
def d_triangle():
    period=200; phase=ms%period; up=(phase<period/2)
    tri=np.where(up, phase/(period/2), 2 - phase/(period/2)); return tri*2-1
def d_abrupt(interpolate=False, steps=10):
    x=np.zeros(N); x[:400]=0.01; x[400]=1e2; x[401:800]=1e2; x[800:]=1.0
    if interpolate:
        for k in range(steps):
            p=400-steps//2+k
            if 0<=p<N: x[p]=0.01+(k+1)/steps*(1e2-0.01)
    return x
# extra 1..9
def d_ar1(rho=0.97, sigma=0.1):
    x=np.zeros(N)
    for t in range(1,N): x[t]=rho*x[t-1]+np.random.normal(0,sigma)
    return x
def d_pink_noise():
    w=np.random.normal(0,1,N); W=np.fft.rfft(w)
    f=np.fft.rfftfreq(N, d=1.0); f[0]=1.0; W=W/np.sqrt(f)
    x=np.fft.irfft(W, n=N); return x/np.std(x)
def d_piecewise_const_bursts():
    x=np.zeros(N); blocks=10; L=N//blocks
    levels=np.random.uniform(-1,1,blocks)
    for b in range(blocks): x[b*L:(b+1)*L]=levels[b]
    for _ in range(20):
        p=np.random.randint(0,N); w=np.random.randint(3,12); a=np.random.uniform(3,8)
        x[p:p+w]+=a
    return x
def d_exp_decay_growth():
    x=np.zeros(N)
    x[:400]=np.exp(-np.linspace(0,5,400))
    x[400:700]=np.linspace(0,2,300)
    x[700:]=2*np.exp(-np.linspace(0,5,300))
    return x
def d_multi_sine():
    return (0.8*np.sin(2*np.pi*ms/37.0)+0.5*np.sin(2*np.pi*ms/103.0)+0.3*np.sin(2*np.pi*ms/251.0))
def d_heavy_t(df=2.5): return np.random.standard_t(df, size=N)
def d_clipped_quantized():
    x= np.tanh(0.02*(ms-500)) + 0.1*np.random.normal(0,1,N)
    x=np.clip(x,-0.9,1.1); q=0.1; x=np.round(x/q)*q; return x
def d_sparse_pulses():
    x=np.zeros(N)
    for _ in range(30):
        p=np.random.randint(0,N); x[p]=np.random.uniform(5,20)
    return x
def d_logistic_map(r=3.9, x0=0.2):
    x=np.zeros(N); x[0]=x0
    for t in range(1,N): x[t]=r*x[t-1]*(1-x[t-1])
    return x*2-1

scenarios = {
    "RandomNormal": d_random_normal(),
    "Poisson": d_poisson(),
    "Sigmoid": d_sigmoid(),
    "Sine": d_sine(),
    "Triangle": d_triangle(),
    "AbruptJump": d_abrupt(False),
    "AbruptJump_Interpolated": d_abrupt(True, steps=12),
    "AR1_RandomWalk": d_ar1(),
    "PinkNoise_1overF": d_pink_noise(),
    "PiecewiseConst_Bursts": d_piecewise_const_bursts(),
    "ExpDecay_Growth": d_exp_decay_growth(),
    "MultiSine": d_multi_sine(),
    "HeavyT": d_heavy_t(),
    "Clipped_Quantized": d_clipped_quantized(),
    "SparsePulses": d_sparse_pulses(),
    "LogisticMap": d_logistic_map(),
}

# ---------- Grid search space ----------
DEFAULTS = dict(fmt_act="E4M3", theta_lsb=1.0, T_silence_init=2, T_emit_init=2,
                T_refractory=4, r_clip_x_theta=3.0, adaptive=True,
                event_target=0.07, window=50, err_increase_ratio=1.10)

GRID = {
    "theta_lsb": [0.5, 1.0, 1.5],
    "T_silence_init": [1, 2, 3],
    "T_emit_init": [1, 2, 3],
    "r_clip_x_theta": [2.0, 3.0, 4.0],
    "event_target": [0.05, 0.07, 0.10],
    # window can stay fixed 50 for stability in this pass
}

def grid_iter(grid: Dict[str, List]):
    import itertools
    keys = list(grid.keys())
    for combo in itertools.product(*[grid[k] for k in keys]):
        yield dict(zip(keys, combo))

# ---------- Tuning per scenario & format ----------
formats = ["E4M3", "E5M2"]
tuning_records = []
best_runs_timelines = {}  # (scenario, format) -> timelines
best_runs_metrics = {}    # (scenario, format) -> metrics

for fmt in formats:
    for scen, x in scenarios.items():
        best = None
        best_m = None
        best_tl = None
        # FP8 baseline for comparison (scale estimated inside run)
        # We'll reuse the FP8 inside the TFSD run with the chosen params, but baseline is fixed by format.
        for params in grid_iter(GRID):
            cfg = DEFAULTS.copy()
            cfg.update(params)
            cfg["fmt_act"] = fmt
            m, tl = tfsd8_run_with_timeline(x, **cfg)
            # objective: RMSE_TFSD8
            score = m["RMSE_TFSD8"]
            if (best is None) or (score < best["RMSE_TFSD8"]):
                best = dict(m)
                best.update({"fmt_act": fmt, **params})
                best_m = m
                best_tl = tl
        # Save best
        best_runs_metrics[(scen, fmt)] = best_m
        best_runs_timelines[(scen, fmt)] = best_tl
        tuning_records.append({
            "Scenario": scen, "FP8_Format": fmt,
            # defaults
            "DEF_theta_lsb": DEFAULTS["theta_lsb"],
            "DEF_T_silence_init": DEFAULTS["T_silence_init"],
            "DEF_T_emit_init": DEFAULTS["T_emit_init"],
            "DEF_r_clip_x_theta": DEFAULTS["r_clip_x_theta"],
            "DEF_event_target": DEFAULTS["event_target"],
            # tuned params
            "BEST_theta_lsb": best["theta_lsb"],
            "BEST_T_silence_init": best["T_silence_init"],
            "BEST_T_emit_init": best["T_emit_init"],
            "BEST_r_clip_x_theta": best["r_clip_x_theta"],
            "BEST_event_target": best["event_target"],
            # metrics
            "MAPE_TFSD8(%)": best_m["MAPE_TFSD8(%)"],
            "RMSE_TFSD8": best_m["RMSE_TFSD8"],
            "MAPE_FP8(%)": best_m["MAPE_FP8(%)"],
            "RMSE_FP8": best_m["RMSE_FP8"],
            "EventRate_TFSD8(%)": best_m["EventRate_TFSD8(%)"],
            "theta_init": best_m["theta_init"], "theta_final": best_m["theta_final"],
            "T_silence_init": best_m["T_silence_init"], "T_silence_final": best_m["T_silence_final"],
            "T_emit_init": best_m["T_emit_init"], "T_emit_final": best_m["T_emit_final"],
            "scale": best_m["scale"],
            "theta_changes_count": len(best_m["theta_changes"]),
            "Tsilence_changes_count": len(best_m["Tsilence_changes"]),
            "Temit_changes_count": len(best_m["Temit_changes"]),
            "err_increase_count": len(best_m["err_increase_idx"]),
        })

tuned_df = pd.DataFrame(tuning_records)
# deltas vs FP8
tuned_df["delta_MAPE"] = tuned_df["MAPE_TFSD8(%)"] - tuned_df["MAPE_FP8(%)"]
tuned_df["delta_RMSE"] = tuned_df["RMSE_TFSD8"] - tuned_df["RMSE_FP8"]

# Save and show summary
summary_csv = "/mnt/data/TFSD8_tuned_summary.csv"
tuned_df_rounded = tuned_df.round(6)
tuned_df_rounded.to_csv(summary_csv, index=False)
display_dataframe_to_user("TFSD8_Tuned_Summary", tuned_df_rounded)

# ---------- Timetables (per best run) ----------
# For each scenario+format, dump a flat timetable (time_ms, FP32 value & delta, outputs, errors, params)
timetables = []
for (scen, fmt), tl in best_runs_timelines.items():
    x = tl["x"]
    x_delta = np.diff(x, prepend=x[0])
    time_ms = np.arange(len(x))
    df_tt = pd.DataFrame({
        "Scenario": scen,
        "FP8_Format": fmt,
        "t": time_ms,
        "time_ms": time_ms,  # 1 ms step
        "FP32": x,
        "FP32_delta": x_delta,
        "y_FP8": tl["y_fp8"],
        "y_TFSD8": tl["y_tfsd"],
        "err_TFSD8": tl["err_t"],
        "err_FP8": tl["err_fp8_t"],
        "theta": tl["theta_t"],
        "T_silence": tl["Tsil_t"],
        "T_emit": tl["Temit_t"],
        "pulses": tl["pulses"],
    })
    timetables.append(df_tt)

timetable_df = pd.concat(timetables, ignore_index=True)
tt_csv = "/mnt/data/TFSD8_tuned_timetables.csv"
timetable_df.to_csv(tt_csv, index=False)
display_dataframe_to_user("TFSD8_Tuned_Timetables", timetable_df.head(200))

# ---------- Heatmaps of ΔRMSE per scenario for each format ----------
def heatmap_delta_rmse(df, fmt):
    sub = df[df["FP8_Format"]==fmt].copy()
    sub = sub[["Scenario", "delta_RMSE"]].set_index("Scenario").sort_index()
    plt.figure(figsize=(8, 6))
    plt.imshow(sub.values, aspect="auto")
    plt.yticks(range(len(sub.index)), sub.index)
    plt.xticks([0], ["ΔRMSE (TFSD8 - FP8)"])
    plt.title(f"ΔRMSE Heatmap per Scenario — {fmt}")
    plt.tight_layout()
    plt.show()

heatmap_delta_rmse(tuned_df, "E4M3")
heatmap_delta_rmse(tuned_df, "E5M2")

# ---------- Top/Bottom by ΔRMSE ----------
def top_bottom(df, fmt, k=5):
    sub = df[df["FP8_Format"]==fmt].sort_values("delta_RMSE")
    topk = sub.head(k).copy()
    botk = sub.tail(k).copy()
    return topk, botk

topE4, botE4 = top_bottom(tuned_df, "E4M3", k=5)
topE5, botE5 = top_bottom(tuned_df, "E5M2", k=5)

display_dataframe_to_user("Top5_E4M3_best(ΔRMSE asc)", topE4.round(6))
display_dataframe_to_user("Bottom5_E4M3_worst(ΔRMSE desc)", botE4.round(6))
display_dataframe_to_user("Top5_E5M2_best(ΔRMSE asc)", topE5.round(6))
display_dataframe_to_user("Bottom5_E5M2_worst(ΔRMSE desc)", botE5.round(6))

# ---------- Representative parameter timelines for a few cases ----------
def plot_param_timeline(scen, fmt):
    tl = best_runs_timelines[(scen, fmt)]
    plt.figure(figsize=(10, 3))
    plt.plot(tl["theta_t"]); plt.title(f"{scen} [{fmt}] — theta(t)"); plt.xlabel("t (ms)"); plt.ylabel("theta"); plt.tight_layout(); plt.show()
    plt.figure(figsize=(10, 3))
    plt.plot(tl["Tsil_t"]); plt.title(f"{scen} [{fmt}] — T_silence(t)"); plt.xlabel("t (ms)"); plt.ylabel("T_silence"); plt.tight_layout(); plt.show()
    plt.figure(figsize=(10, 3))
    plt.plot(tl["Temit_t"]); plt.title(f"{scen} [{fmt}] — T_emit(t)"); plt.xlabel("t (ms)"); plt.ylabel("T_emit"); plt.tight_layout(); plt.show()

# Plot a few: best/worst from E4M3
for scen in list(topE4["Scenario"].head(3)):
    plot_param_timeline(scen, "E4M3")
for scen in list(botE4["Scenario"].tail(3)):
    plot_param_timeline(scen, "E4M3")

# ---------- Excel Workbook with conditional formatting ----------
xlsx_path = "/mnt/data/TFSD8_tuning_results.xlsx"
with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
    tuned_df_rounded.to_excel(writer, sheet_name="TunedSummary", index=False)
    timetable_df.to_excel(writer, sheet_name="AllTimetables", index=False)
    # Per-scenario sheets (short names)
    for (scen, fmt), tl in best_runs_timelines.items():
        sheet = (scen[:22] + "_" + fmt)[:31]
        sub = timetable_df[(timetable_df["Scenario"]==scen) & (timetable_df["FP8_Format"]==fmt)]
        sub.to_excel(writer, sheet_name=sheet, index=False)
        ws = writer.sheets[sheet]
        nrows, ncols = sub.shape
        # color scales on error and deltas
        for col in ["err_TFSD8", "err_FP8", "FP32_delta", "theta"]:
            if col in sub.columns:
                c = sub.columns.get_loc(col)
                ws.conditional_format(1, c, nrows, c, {"type": "3_color_scale"})
    # Global formatting on summary
    ws = writer.sheets["TunedSummary"]
    nrows, ncols = tuned_df_rounded.shape
    for col in ["delta_RMSE", "delta_MAPE", "EventRate_TFSD8(%)"]:
        c = tuned_df_rounded.columns.get_loc(col)
        ws.conditional_format(1, c, nrows, c, {"type": "3_color_scale"})

# Save additional CSVs for convenience
topE4.to_csv("/mnt/data/Top5_E4M3.csv", index=False)
botE4.to_csv("/mnt/data/Bottom5_E4M3.csv", index=False)
topE5.to_csv("/mnt/data/Top5_E5M2.csv", index=False)
botE5.to_csv("/mnt/data/Bottom5_E5M2.csv", index=False)

(summary_csv, tt_csv, xlsx_path)
