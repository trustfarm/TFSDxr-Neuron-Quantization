**免责声明**：本文件的韩文 (KO) 版本为原始版本。  
如在翻译中出现问题或歧义，请参考韩文版本。

---

# UE4T 神经元单元内存层次结构

[KO](Neuron_Cell_Memory.md) | [EN](Neuron_Cell_Memory_en.md) | [ZH](Neuron_Cell_Memory_zh.md)


本文档说明了基于 UE4T 的神经元单元内部的 **存储层次结构**。  
在 FPGA 原型中使用 BRAM/分布式 RAM，而在 ASIC 实现中，结合 **动态锁存寄存器文件 (RF)** 与 **GC-eDRAM** 更为有利。

---

## 🔑 存储层次结构

### 1. 单元级 (cell local)
- **动态锁存寄存器文件**
  - 存储项目: `b` (EMA), `E` (尺度), `r` (ΣΔ 累加器), 状态标志
  - 容量: 每单元约 32–64bit
  - 实现: 基于脉冲锁存的动态寄存器文件
- **自刷新**
  - 每个 UE4T token 周期自然覆盖 → 最大程度减少强制刷新需求

### 2. Tile 级 (256 单元共享)
- **GC-eDRAM 宏单元**
  - 用途: 权重、连接索引、token FIFO
  - 容量: 约 1–8 KB
- **感应放大器 + 预充电**
  - 节能低摆幅感应放大器
  - 可支持奇偶校验/ECC
- **刷新 FSM**
  - 根据温度/电压补偿保持时间
  - 执行逐行周期刷新
  - 可与 SILENT 时间段联动

### 3. 主机连接
- **主机 CPU + 外部存储**
  - 在训练时负责反向传播和权重更新
  - 与 GC-eDRAM 双向连接

---

## 📐 图示

![Neuron Cell Memory Hierarchy](diagrams/neuron_cell_memory.svg)

---

## 📌 总结
- **单元本地**: 动态锁存寄存器文件 (面积小、漏电低、访问快)  
- **Tile 共享**: GC-eDRAM (高密度、低功耗、需刷新 FSM)  
- **刷新**: 基于 Token 周期 + FSM 的**认知刷新**  
- **FPGA**: 使用 BRAM/LUTRAM 验证功能，ASIC 转为 GC-eDRAM + 锁存器实现
