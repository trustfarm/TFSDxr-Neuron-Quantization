
---

## 📄 README_zh.md (ZH)

```markdown
# UE8M0-Neuron-Quant (v0.1.4a)

[KO](README.md) | [EN](README_en.md) | [ZH](README_zh.md)

**UE8M0** 是一种以 *差分* 和 *事件* 为核心的低功耗量化/编码方案。  
通过结合 `2^E` 移位缩放与 FP8 尾数，实现了 **无需乘法器(仅移位)** 的宽动态范围。

---

## 🧭 快速链接
**文档:** [ZH](docs/algorithm_full_zh.md)  
**图表 (SVG):**  
- 概览: `docs/diagrams/ue8m0_overview_auto_zh.dot`  
- 同步(垂直): `docs/diagrams/ue8m0_sync_auto_vertical_zh.dot`  

> Windows 转换: 使用 `docs/diagrams/dot2svg.bat` 将 `.dot → .svg`

---

**UE4T** 是一种轻量级编码方案，将 **UE8M0 的理念** 扩展为 **4位格式**。  
- 2^E 缩放 (移位) + ΣΔ 事件 + 4位令牌映射  
- 小变化：ΣΔ ±1，大变化：MAX/MIN，中等变化：NORM_ESC+payload  
- 硬件优化，无需乘法器  

👉 [UE4T v0.3 详细文档](docs/ue4t_format_v.0.3.md)

---

## ✨ 什么是 UE8M0?
- **差分**: 从输入 `x` 中去除基线 `b`(EMA) → `d = x - b`  
- **事件驱动**: 小变化 → ΣΔ ±1 脉冲，大变化 → **MAX/MIN** 事件  
- **移位缩放**: `E` 表示 2 的幂次缩放 → 无需硬件乘法器  
- **FP8 尾数**: 提供精度 (E4M3/E5M2)

---

## ⚙️ 可调参数 (推荐范围)
| 名称 | 含义 | 范围 |
|---|---|---|
| `beta` | EMA 系数 | 0.01 ~ 0.2 |
| `lambda0` | 小变化阈值 | 根据传感器灵敏度 |
| `lambda_hi` | 大变化阈值 | 噪声的 5–20× |
| `T_silence` | ΣΔ 静默时间 | 5–50 ms |
| `T_emit` | ΣΔ 最小间隔 | 1–10 ms |
| `T_refractory` | MAX/MIN 不应期 | 10–100 ms |
| `T_scale_dwell` | 缩放停留时间 | 50–500 ms |
| `near_upper/lower` | FP8 边界接近 | 上/下 10% |

> 安静输入 → 提高 `T_silence`  
> 宽动态范围 → 采用 E5M2  
> 高灵敏度需求 → 采用 E4M3

---

## 🔁 编码器–解码器同步
- 编码器与解码器共享 **EMA(b) 与 E 更新** → 即使丢失 token 也能逐步恢复同步。  
- 异常恢复技巧: 若 q 聚集在边界 → 应用 **SCALE 推断**(启发式)。

---

## 🛠️ 图表生成
```powershell
# 安装 graphviz (dot 在 PATH 中)
# 转换单个文件
docs\diagrams\dot2svg.bat docs\diagrams\ue8m0_overview_auto_zh.dot

# 递归转换
docs\diagrams\dot2svg.bat docs\diagrams

