**Disclaimer**: The Korean (KO) version of this document is the original reference. In case of any translation issues or ambiguities, please refer to the Korean version.

---


# UE8M0 Encoder–Decoder Example (encdec_example_en.md)


[KO](encdec_example.md) | [EN](encdec_example_en.md) | [ZH](encdec_example_zh.md)


This document provides **sample parameter defaults** and a step-by-step example of  
**input time series → encoding (tokens) → decoding (reconstruction)** using more than 20 data points.

> Goal: small changes → **ΣΔ accumulated pulses**, large changes → **MAX/MIN events**,  
> quiet periods → **SILENT timeout**, medium changes → **NORM(q)**.

---

## 1) Parameters (default example)

| Parameter | Meaning | Value (example) |
|---|---|---|
| `beta` | EMA coefficient of baseline b | **0.05** |
| `lambda0` | small diff threshold | **0.25** |
| `lambda_hi` | large diff threshold | **3.0** |
| `T_emit` | ΣΔ minimum interval | **5 ms** |
| `T_silence` | SILENT event threshold | **30 ms** |
| `T_refractory` | refractory after MAX/MIN | **40 ms** |
| `T_scale_dwell` | scale dwell time | **200 ms** |
| `near_upper/lower` | FP8 boundary proximity | top/bottom **10%** |
| Initial | `b0=20.0`, `E0=0`, `r0=0` | — |

---

## 2) Input time series (sensor data, 10 ms sampling)

24 points (0–230 ms, sampled every 10 ms).  
**Phase A: small rise (ΣΔ) → Phase B: medium jump (NORM) → Phase C: large rise (MAX + refractory) → Phase D: quiet (SILENT) → Phase E: small fall (ΣΔ) → Phase F: large fall (MIN + refractory) → Phase G: small recovery (ΣΔ)**

(detailed sequence table omitted, same as KO version)

---

## 6) SVG sample plots

- 📈 [Input vs Reconstructed time series](diagrams/encdec_timeseries.svg)  
- 🪙 [Token timeline](diagrams/encdec_tokens.svg)

---

## 7) Usage of `encdec_plot.py`

```bash
cd docs/diagram
python encdec_plot.py
```

---

## ✅ Summary

- **ΣΔ accumulated pulses** efficiently convey small changes  
- **MAX/MIN** concisely represent large events  
- **SILENT** marks long quiet periods with a single token  
- **NORM** handles medium changes robustly  
- Entire workflow can be reproduced with **`encdec_plot.py` + SVG samples**
