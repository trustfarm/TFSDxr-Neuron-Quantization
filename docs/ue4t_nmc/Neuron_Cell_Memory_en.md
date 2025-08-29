**Disclaimer**: The Korean (KO) version of this document is the original reference. In case of any translation issues or ambiguities, please refer to the Korean version.

---

# UE4T Neuron Cell Memory Hierarchy

This document describes the **memory hierarchy inside a UE4T-based neuron cell**.  
In FPGA prototypes, BRAM/distributed RAM is utilized, but in ASIC implementations, it is advantageous to combine **dynamic latch-based RF** and **GC-eDRAM**.

---

## 🔑 Memory Hierarchy

### 1. Per-Cell (cell local)
- **Dynamic Latch Register File**
  - Stored items: `b` (EMA), `E` (scale), `r` (ΣΔ accumulator), state flags
  - Size: about 32–64bit/cell
  - Implementation: pulsed latch based dynamic latch RF
- **Self-Refresh**
  - Natural overwrite occurs every UE4T token cycle → minimizes need for forced refresh

### 2. Per-Tile (shared by 256 cells)
- **GC-eDRAM Macro**
  - Purpose: weights, connection index, token FIFO
  - Size: 1–8 KB level
- **SenseAmp + Precharge**
  - Energy-saving low-swing sense amplifier
  - Parity/ECC possible
- **Refresh FSM**
  - Retention time compensation depending on temperature/voltage
  - Performs row-wise periodic refresh
  - Can be linked with SILENT intervals

### 3. Host connection
- **Host CPU + External Memory**
  - Handles backpropagation and weight update during training
  - Bi-directional connection with GC-eDRAM

---

## 📐 Diagram

![Neuron Cell Memory Hierarchy](diagrams/neuron_cell_memory.svg)

---

## 📌 Summary
- **Cell-local**: Dynamic latch RF (low area, low leakage, fast access)  
- **Tile-shared**: GC-eDRAM (high density, low power, needs refresh FSM)  
- **Refresh**: Token cycle + FSM based **cognitive refresh**  
- **FPGA**: Function verified with BRAM/LUTRAM, ASIC replaced with GC-eDRAM + latch based
