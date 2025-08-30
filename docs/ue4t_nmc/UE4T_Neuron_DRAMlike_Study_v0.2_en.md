# TFSD4(UE4T) Neuron DRAM-like Study v0.2

**Disclaimer**: The Korean (KO) version of this document is the original reference. In case of any translation issues or ambiguities, please refer to the Korean version.

---

[KO](UE4T_Neuron_DRAMlike_Study_v0.2.md) | [EN](UE4T_Neuron_DRAMlike_Study_v0.2_en.md) | [ZH](UE4T_Neuron_DRAMlike_Study_v0.2_zh.md)

---

## 1) Candidate technology option summary
| Option | Bitcell | Density | Speed/Energy | Retention/Refresh | Port/Scalability | Note |
|---|---|---|---|---|---|---|
| SRAM | 6T/8T/10T | Low | Very fast, no refresh | Not required | Multi-port easy | Area/leakage big, cost↑ |
| GC-eDRAM | 2T1C/3T1D/5T etc. | High | Fast, low energy | Refresh required (several ms–hundreds ms) | Multi-port by peripheral | Logic process compatible, high density, many cases exist |
| Dynamic latch/Pulsed latch RF | D-Latch based | Medium | Fast, low area/low leakage | Periodic rewrite required | Multi-port limited | Suitable for register file/small buffer |
| 1T1C eDRAM (MIM cap) | 1T1C | Highest | Fast, CIM application active | Refresh required | Sense amp/precharge required | Many 1T1C cases |
| eMRAM | STT-MRAM | Medium | Fast read/write energy↑ | No refresh | Simple port | Some foundry option, process availability dependent |

Reference: **Gain-Cell eDRAM (GC-eDRAM)** is 2T1C/3T type “gain cell” embedded DRAM compatible with logic process / high density / extended retention time.  
Latest papers show retention extended from several ms to hundreds s, operating at high speed even in FinFET nodes.

---

## 2) What to put “where” inside neuron cell (memory hierarchy)

Example of TFSD4(UE4T) neuron cell states:
- b (EMA base, 12–16b), E (scale, 5–6b), r (ΣΔ accumulator, 16–24b)
- Recent token FIFO (several entries × 4b), local statistics/counter (8–16b), sparse connection index

Proposed 2-level structure:
- **Cell-local (ultra-local) dynamic latch storage**
  - Target: b, E, r, small number of flags/timer (total several tens bits/cell)
  - Implementation: pulsed latch based register file (or simple latch array)
  - Advantage: with clock gating + pulse width control → low area/low leakage/high speed. Refresh by **rewrite (write-back)** simple. UE4T has dense token/timing → natural self-refresh period.
- **Tile-shared GC-eDRAM small array**
  - Target: weights/connection index/recent token FIFO, several hundred b–several kB
  - Implementation: 2T1C/3T1D GC-eDRAM macro + small sense amp/precharge
  - Advantage: compared with SRAM large area saving + sufficient bandwidth. UE4T is low precision (4b) and event type → many optimization possibilities for bitline swing/SA. If necessary, CIM lightweight also possible.

Summary: Cell-local state = dynamic latch, large capacity item = tile-shared GC-eDRAM. (SRAM only minimal use for global buffer/multi-port control)

---

## 3) Refresh/Reliability strategy (neuron-event linked “cognitive refresh”)

- Temperature/voltage dependent retention time: dynamic storage retention decreases when temperature↑, VDD↓ → variable refresh interval using on-chip temperature sensor/speed bin. (GC-eDRAM has many compensation techniques)  
- Event-based refresh: when no cell token occurs, periodically rewrite linked with SILENT timeout.  
- Local refresh FSM: small FSM per tile performs row-by-row/group refresh, pause-resume if overlap with access.  
- Weak ECC/parity: nibble parity or lightweight SEC protection for 4b token/state.  
- Sense amp optimization: single bitline/low swing SA etc. → DRAM energy↓ circuit adoption possible.

---

## 4) Timing/Power/Area rough estimate

- Dynamic latch RF: 32–128b/cell, ~30–40% area↓ compared with flipflop, leakage↓ (depends on process/design)  
- GC-eDRAM 2T1C: 2–4× density↑ compared with 6T SRAM. Retention time several ms–several tens ms common, with reinforced design several s–hundreds s reported. Need to reflect SA/precharge overhead.  
- CIM option: using 1T1C/2T1C based micro swing accumulate/bit-parallel → FoM improved in 4b operation. Suitable for UE4T 4b payload.

---

## 5) Connection with FPGA prototype

- FPGA: BRAM/URAM (large), distributed RAM/LUTRAM (very small) emulate function.  
- Dynamic latch/DRAM-like cannot reproduce actual leakage in FPGA, not recommended. → only model refresh logic with periodic rewrite to check function.  

---

## 6) Recommended microarchitecture sketch

**Per-Cell (dynamic latch block)**
- Latency sensitive states: b(EMA), E, r, flag → pulsed latch RF  
- Natural refresh (overwrite) occurs every “token tick” → minimal extra refresh

**Per-Tile (GC-eDRAM macro 1–8 KB level)**
- Weight/sparse index/token FIFO  
- Temperature dependent refresh interval + block level low power precharge/SA  
- Lightweight ECC/parity, Row priority refresh according to **token class (QoS)**

**Timing**
- TFSD4(UE4T) token frequency (e.g., several MHz etc.) >> refresh cycle → design accordingly  
- Insert bus hold/one cycle restore into read-modify-write path to increase reliability

---

## 7) Risk & mitigation

- Process availability: depends on foundry/node if eDRAM option exists → consider gain-cell (logic compatible) first, if not possible use small SRAM alternative.  
- PVT variation: retention variation → variable refresh based on on-chip sensor + field tuning register.  
- Test: include refresh stress pattern in BIST, data retention screen procedure required.

---

## Conclusion/Proposal

**Core states inside neuron cell = dynamic latch RF**, **large capacity per-tile = GC-eDRAM**:  
- Area/Power optimized + complementary with TFSD4(UE4T)’s event/low precision characteristic  
- Use TFSD4(UE4T) token timing for awareness-driven refresh to minimize extra overhead  
- In FPGA use BRAM/LUTRAM for functional verification → in ASIC replace with GC-eDRAM + pulsed latch

---

## Block Diagram

![**TFSD4(UE4T) Neuron Memory Architecture v0.2**](diagrams/neuron_mem_arch_v0.2.svg)

---

## References (Topics)

- [sites.utexas.edu] Gain-Cell eDRAM related research/lecture materials  
- [Nature] eDRAM/GC-eDRAM and embedded memory overview papers/reviews  
- [people.ece.umn.edu] Memory/Sense amplifier/DRAM circuit lecture/paper links  
- [eScholarship] Dynamic latch/Register file optimization research  
- [ResearchGate] GC-eDRAM/1T1C eDRAM/CIM case studies  
- [researchpublish.com] Register file/Pulsed latch design reports  
- [Wiley Online Library] eDRAM/embedded memory survey  
- [MDPI] Low-swing sense amplifier/DRAM energy saving techniques  
- [synopsys.com] eMRAM technology/Foundry IP information  
- [docs.amd.com] FPGA BRAM/URAM/Distributed RAM guides  
- [projectf.io] FPGA memory practice materials
