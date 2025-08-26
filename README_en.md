
---

## 📄 README_en.md (EN)

```markdown
# UE8M0-Neuron-Quant (v0.1.4a)

[KO](README.md) | [EN](README_en.md) | [ZH](README_zh.md)

**UE8M0** is a low-power quantization/encoding scheme focused on *differentials* and *events*.  
By combining a `2^E` shift-only scale with FP8 mantissa, it covers a wide dynamic range **without multipliers** (only shifts).

---

## 🧭 Quick links
**Docs:** [EN](docs/algorithm_full_en.md)  
**Diagrams (SVG):**  
- Overview: `docs/diagrams/ue8m0_overview_auto_en.dot`  
- Sync (vertical): `docs/diagrams/ue8m0_sync_auto_vertical_en.dot`  

> Windows conversion: use `docs/diagrams/dot2svg.bat` to convert `.dot → .svg`

---

## ✨ What’s UE8M0?
- **Differential**: remove baseline `b` (EMA) from input `x` → `d = x - b`  
- **Event-based**: small changes → ΣΔ ±1 pulse, large changes → **MAX/MIN** events  
- **Shift-only scale**: `E` represents power-of-two scaling → no hardware multipliers needed  
- **FP8 mantissa**: provides precision (E4M3/E5M2)

---

## ⚙️ Tunable parameters (recommended ranges)
| Name | Meaning | Typical |
|---|---|---|
| `beta` | EMA coefficient | 0.01 ~ 0.2 |
| `lambda0` | small change threshold | sensor-dependent |
| `lambda_hi` | large change threshold | 5–20× noise level |
| `T_silence` | ΣΔ silence duration | 5–50 ms |
| `T_emit` | ΣΔ minimum interval | 1–10 ms |
| `T_refractory` | MAX/MIN refractory | 10–100 ms |
| `T_scale_dwell` | scale dwell time | 50–500 ms |
| `near_upper/lower` | FP8 boundary proximity | top/bottom 10% |

> If input is quiet → increase `T_silence`.  
> If wide dynamic range → use E5M2.  
> If fine sensitivity → use E4M3.

---

## 🔁 Encoder–Decoder Sync
- Encoder & decoder share **EMA(b) and E updates** → sync recovers gradually even with token loss.  
- Recovery tip: if q clusters near FP8 boundary → apply heuristic **SCALE inference**.

---

## 🛠️ Build diagrams
```powershell
# Install graphviz (dot in PATH)
# Convert single file
docs\diagrams\dot2svg.bat docs\diagrams\ue8m0_overview_auto_en.dot

# Convert recursively
docs\diagrams\dot2svg.bat docs\diagrams
