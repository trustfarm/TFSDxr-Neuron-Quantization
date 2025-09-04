# TFSD8-Neuron-Quant (v0.1.5)


**免责声明**：本文件的韩文 (KO) 版本为原始版本。  
如在翻译中出现问题或歧义，请参考韩文版本。

---


[KO](README.md) | [EN](README_en.md) | [ZH](README_zh.md)

---

**TFSD8** 是一种以 *差分* 和 *事件* 为核心的低功耗量化/编码方案。  
通过结合 `2^E` 移位缩放与 FP8 尾数，实现了 **无需乘法器(仅移位)** 的宽动态范围。

---

### 代号更新通知

本算法原先的名称 UE8M0
现正式更名为 **TFSD8** / **TFSD4(UE4T)** / **TFSD16**  , ***Time Feedback Sigma-Delta Quantization，时间反馈 ΣΔ 量化）***。

### 前言

> TFSD8 / TFSD16 并不仅仅是一个缩写。
在模拟计算机科学的早期阶段，研究先驱们提出了 ΣΔ (Sigma-Delta) 调制 与 残差反馈 (Residual Feedback) 的思想，
为紧凑而精确的数据表达奠定了基础。
> 
> 我 <ins>**们向这些前辈致以敬意**</ins>，并在此基础上引入了现代的概念：
基于时间的自适应门控 (Windowing & Refractory Control)。
由此诞生了一种适用于当代张量计算环境的新型量化方法。
> 
> 因此，我们将本算法命名为 TFSD8 / TFSD16 （Time Feedback Sigma-Delta Quantization）。
它融合了 过去模拟 ΣΔ 的智慧 + 当下时间自适应编码的思想 + 面向未来张量运算的扩展性。
> 
> 同时，字母 "T" 不仅代表 Time / Temporal / Tensor，
也象征着本项目的根基 TrustFarm。

--- 

### TFSD16xr Quantization Algorithm updated.

Refer Here --->  [**TFSD16xr Codec Progress**](docs/tfsd_quant/README_zh.md)

--- 

## TFSD8 Kappa/Emit Algorithm

![TFSD8_block_diagram](TFSD8_block_diagram.svg)

---

## 🧭 Algorithm Details Quick links

TFSD8 Details

**Docs:** [TFSD8 Details KO](docs/algorithm_full_ko.md) · [TFSD8 Details EN](docs/algorithm_full_en.md) · [TFSD8 Details ZH](docs/algorithm_full_zh.md)

**图表 (SVG):**  
- 概览: `docs/diagrams/ue8m0_overview_auto_zh.dot`  
- 同步(垂直): `docs/diagrams/ue8m0_sync_auto_vertical_zh.dot`  

> Windows 转换: 使用 `docs/diagrams/dot2svg.bat` 将 `.dot → .svg`

---

**TFSD4(UE4T)** 是一种轻量级编码方案，将 **TFSD8 的理念** 扩展为 **4位格式**。  
- 2^E 缩放 (移位) + ΣΔ 事件 + 4位令牌映射  
- 小变化：ΣΔ ±1，大变化：MAX/MIN，中等变化：NORM_ESC+payload  
- 硬件优化，无需乘法器  

- TFSD4 based NeuroMorphic Chip Architecture
👉 [TFSD4(UE4T) v0.3 详细文档](docs/ue4t_format_v.0.3_zh.md)

---

## 🔥 TFSD4(UE4T): 可训练神经形态SoC的关键

传统神经形态芯片（基于SNN）只表示 **脉冲事件(0/1)** 和 **发放时间**，  
因此在精确训练方面存在明显限制。  
ANN虽然可以训练，但功耗和资源消耗过高。

TFSD4(UE4T)同时突破这两个瓶颈。

### ✅ 差异化优势
- **用4位令牌表示脉冲强度**
  - `ΣΔ` → 累积微小变化  
  - `MAX/MIN` → 大幅事件  
  - `NORM_ESC + 4位负载` → **量化的脉冲强度**  
  - `SCALE (2^E)` → 扩展动态范围  
- **无需乘法器**（仅移位）即可实现接近FP8的缩放能力

### 🧠 可训练性
- 脉冲不仅是0/1事件，而是**类似浮点值**  
- 可支持 **梯度下降训练**（SNN无法做到）  
- 可扩展到 **大规模CNN / Transformer模型**

### 📊 对比表
| 类别 | 传统SNN | ANN | **TFSD4(UE4T)** |
|------|---------|-----|----------|
| 表达方式 | 脉冲=0/1, 时间 | FP32/INT8 | **脉冲+强度 (4bit+缩放)** |
| 训练 | STDP, 局部规则 | 梯度下降 | **可进行梯度下降** |
| 功耗 | 低 | 高 | **低 (移位+事件)** |
| 精度 | 低 | 高 | **高 (强度表达)** |
| 适用模型 | 简单模式 | 大多数 | **复杂CNN/Transformer** |

---

> **TFSD4(UE4T)是第一个可以量化脉冲强度的4位事件格式。**  
> 它使得神经形态芯片不仅能推理，还能实现真正的 **可训练NeuroSoC**。

---

## ✨ 什么是 TFSD4?
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

