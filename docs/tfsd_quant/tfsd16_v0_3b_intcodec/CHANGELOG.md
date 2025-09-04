
# CHANGELOG (excerpt)

- V0_3b
  - Enforce closed-loop Δ: `Delta_t = FP_e(t) − FP_d(t−1)`
  - KF(t=0), SE-change => KF
  - Mantissa: **M5+1 absolute patch** per window, up to **W=2**
  - ZeroRun: type=11 nibble-aligned with `0xF` marker
  - Watchdogs: lower-6 not touched for 2205 => KF; lower-6 error accumulation ≥ 64 => KF
  - Optional RD-switch: per-sample `min(bits(KF), bits(M5+1))`

- Planned V0_4
  - Mantissa/Exponent **delta coding in FP6/FP8**, Golomb–Rice or similar entropy coding
  - Emit/Kappa redesign under the same Δ definition
