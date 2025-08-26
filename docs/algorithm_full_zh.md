# UE8M0‑Neuron‑Quant 算法 (v0.1.3)

本文面向普通读者与工程师，同时提供**直观说明（示例/流程）**与**技术依据（公式/设计考量）**。

---
## 1) 引言：为何关注“差分/事件”
人类对**相对变化（差分）**与**事件（极值/饱和）**更敏感：
- **指尖细触**：轻擦表面会感觉到非常细微的凹凸变化；
- **苍蝇落在皮肤上**：微弱触觉因“瞬时变化”而被明显感知。

UE8M0‑Neuron‑Quant 将该原理映射到数字逻辑，实现**低功耗、事件驱动编码**。

---
## 2) 术语与令牌（先定义）
- **b**：基线，采用 EMA 更新；  
- **d = x − b**：差分；  
- **E**：UE8M0 的 2^E 量级（对数尺度）；  
- **r**：ΣΔ 累加器（残差/微小变化累积）。

**令牌**
- **NORM(q)**：常规量化值（FP8 q）  
- **MAX / MIN**：大正/大负事件  
- **SCALE(±1)**：尺度步进（E 增减 1）  
- **SILENT**：无发放

---
## 3) 核心概念
### 3.1 UINT8 vs FP8 vs UE8M0
- **UINT8**：0–255 固定范围；
- **FP8**：常见两种格式  
  - **E4M3** 精度高、范围窄；  
  - **E5M2** 范围宽、精度低；
- **UE8M0 (2^E)**：按 2 的幂缩放 → **移位实现、无需乘法器**。FP8 负责精度，UE8M0 负责动态范围。

### 3.2 误差反馈
量化后累加 `residual = d − d̂` 到 r，避免长期偏置；等价于**抖动/ΣΔ 误差反馈**，随时间释放 ±1 脉冲。

### 3.3 时间参数
- **T_silence**：去抖；仅持续微小变化才允许发放；  
- **T_emit**：脉冲最小间隔，限制发放频率，降低功耗；  
- **T_refractory**：MAX/MIN 事件后不应期，防止事件风暴；  
- **T_scale_dwell**：尺度驻留时间，避免 E 抖动。

### 3.4 为何用 EMA 更新 b
EMA 是**低通**，b 跟踪慢变化趋势，d 捕捉快速变化。

---
## 4) 编码器（可读伪代码）
```pseudo
state:
  b, E, r
  t_last_emit, t_last_scale, t_event_quiet, t_silence
...
# 与英文版相同逻辑，见上
```
> 例如：`near_upper(q) ⇔ q ≥ 0.9·FP8_MAX`，`near_lower(q) ⇔ q ≤ 0.9·FP8_MIN`

---
## 5) 解码器概要
通过 `SCALE(±1)` 共享 E 的更新；将 `NORM(q)` 复原为 `deFP8(q) * 2^E`；MAX/MIN 为阈值事件；b 也按相同 EMA 规则更新以保持**状态同步**。

---
## 6) 实现提示
- 基于移位/比较的 RTL（无乘法器）可节能省面积；  
- 参数建议：  
  - 高灵敏传感 → E4M3、较小 lambda0、较短 T_silence；  
  - 宽动态范围 → E5M2、较大 lambda_hi、较长 T_refractory；  
- 应用：事件相机/触觉、IoT、嵌入式音频/振动编码等。

---
## 7) 图示
- `diagrams/ue8m0_overview_auto_zh.svg` 
  [ue8m0_overview](diagrams/ue8m0_overview_auto_zh.svg) 
- `diagrams/ue8m0_sync_auto_vertical_zh.svg`
  [ue8m0_sync_auto](diagrams/ue8mue8m0_sync_auto_vertical_zh.svg)
