**Disclaimer** : 본 문서는 한국어(KO) 버전이 원본이며, 번역 과정에서 발생할 수 있는 문제나 모호한 부분은 한국어 버전을 참조하시기 바랍니다.

---


# UE4T Neuron Cell Memory Hierarchy (v0.1)

본 문서는 UE4T 기반 뉴런셀 내부의 **메모리 계층 구조**를 설명합니다.  
FPGA 프로토타입에서는 BRAM/분산RAM을 활용하지만, ASIC 구현에서는 **동적 래치 기반 RF**와 **GC-eDRAM**을 조합하는 방식이 유리합니다.

---

## DRAM-like 메모리 조사자료

More Detailed Study of DRAM-like Memory in SoC is 

[UE4T 뉴런 셀 내 DRAM-like 메모리 스터디 (v0.2)](UE4T_Neuron_DRAMlike_Study_v0.2.md)

---
## 🔑 메모리 계층 구조

### 1. Per-Cell (셀 로컬)
- **Dynamic Latch Register File**
  - 저장 항목: `b` (EMA), `E` (스케일), `r` (ΣΔ 누산기), 상태 플래그
  - 크기: 약 32–64bit/셀
  - 구현: Pulsed Latch 기반 동적 래치 RF
- **Self-Refresh**
  - UE4T 토큰 주기마다 자연스러운 overwrite 발생 → 별도 강제 리프레시 최소화

### 2. Per-Tile (256 Cell 공유)
- **GC-eDRAM Macro**
  - 용도: 가중치(Weight), 연결 인덱스(Index), 토큰 FIFO
  - 크기: 1–8 KB 수준
- **SenseAmp + Precharge**
  - 에너지 절약형 저스윙 센스앰프
  - Parity/ECC 추가 가능
- **Refresh FSM**
  - 온도/전압 의존 유지시간 보정
  - Row-wise 주기적 리프레시 수행
  - SILENT 구간과 연동 가능

### 3. Host 연결
- **Host CPU + External Memory**
  - Training 시 Backpropagation, Weight Update 담당
  - GC-eDRAM과 양방향 연결

---

## 📐 다이어그램

![Neuron Cell Memory Hierarchy](diagrams/neuron_cell_memory.svg)

---

## 📌 Summary
- **Cell-local**: Dynamic Latch RF (저면적, 저누설, 빠른 접근)
- **Tile-shared**: GC-eDRAM (고밀도, 저전력, Refresh FSM 필요)
- **Refresh**: Token 주기 + FSM 기반 **인지형 리프레시**
- **FPGA**: BRAM/LUTRAM으로 기능 검증, ASIC에서는 GC-eDRAM + 래치 기반으로 치환
