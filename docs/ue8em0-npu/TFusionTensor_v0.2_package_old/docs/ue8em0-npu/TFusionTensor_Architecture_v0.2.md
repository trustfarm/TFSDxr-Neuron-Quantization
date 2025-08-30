# TFusionTensor v0.2 — Architecture Overview (Student Edition)

> This document explains the **TFusionTensor** architecture at a practical, undergraduate‑friendly level.
> It focuses on *why* the design exists and *how* it works—without assuming prior TPU/GPU expertise.

## 1) Big Picture

Traditional CPUs rely on multi‑level caches (L1→L2→L3). That hierarchy helps hit rate,
but **accumulates latency**, which hurts massively parallel AI compute.
**TFusionTensor** is designed for AI accelerators where we prefer a **flat, single‑depth memory path**
augmented by a workload‑aware front‑side cache called **TFusionVcache**.

- Compute fabric: **shift‑based MAC**, 128×128 **tiles**, tensor‑friendly data paths.
- Dataflow: **Weight‑stationary** for conv, **Output‑stationary** for GEMM.
- Memory: External DRAM/HBM → **TFusionVcache** → Scratchpad (SPM) → Tiles.

For details on our hybrid cache:
**See TFusionVcache (Korean):** [`../TFusionVcache/TFusionVcache_v0.1.md`](../TFusionVcache/TFusionVcache_v0.1.md)  
**English companion:** [`../TFusionVcache/TFusionVcache_v0.1_en.md`](../TFusionVcache/TFusionVcache_v0.1_en.md)

## 2) Why TFusionTensor?

- **Latency matters** more than ever for large language models (LLMs) and long sequences.
- **Compute efficiency**: Our shift‑centric MAC pipeline reduces multiplier cost and power.
- **TCO focus**: With the right cache policy, we cut expensive DRAM/HBM trips.
  Think: not “buying water every time at a convenience store (DRAM)”, but **stocking 2‑liter bottles in your fridge (Cache)**.

## 3) Core Design

- **Tiles**: 128×128 PE tiles arranged in banks; systolic/blocked scheduling.
- **PE pipeline**: E‑adder → MantissaUnit (8×8 MUL/LUT) → Shifter → 24‑bit accumulator.
- **Format**: FP8 mantissa + `UE8M0`‑style exponent group header (e.g., 32 elems per group).  
  (*The legacy tag is kept for format clarity; “UE8M0” isn’t exposed as a product name.*)

### Dataflow Modes
- **Conv (weight‑stationary)**: reuse weights inside tiles, stream activations.
- **GEMM (output‑stationary)**: accumulate partial sums locally, stream inputs/weights.

## 4) Memory Path (Flat, 1‑Depth + TFusionVcache)

Instead of stacking many cache levels, we operate a **1‑depth path**:
**Host/DRAM → TFusionVcache → SPM → Tiles**.

- **TFusionVcache** (64 MB physical, logically split KV/Tensor with dynamic MB reallocation)
  maximizes cache hit and reduces fetch latency.
- **SPM** (on‑chip scratchpad) provides predictable, banked, ping‑pong buffering to tiles.

## 5) Diagrams

> Files are included under `./diagrams` and embedded as references below.

- **Algorithm view**: `diagrams/TFusionTensor_algorithm_v0_2.svg`
- **Dataflow view**:  `diagrams/TFusionTensor_dataflow_v0_2.svg`
- **Block Internals**: `diagrams/TFusionTensor_block_algo_v0_2.svg`
- **System Integration**: `diagrams/TFusionTensor_system_v0_2.svg`

## 6) TCO View (Why it’s cost‑effective)

- **Fewer DRAM/HBM transfers** ⇒ lower power and better system‑level cost.
- **Lower clock for same or better latency** ⇒ easier cooling, lower power delivery cost.
- **More perf per silicon area** ⇒ better ROI for training/inference clusters.

**Analogy:** Your **fridge** is the TFusionVcache. You don’t run to the store every time;
you stock what you repeatedly need and resize shelves (KV vs Tensor) depending on the week’s groceries.

## 7) What You Can Build

- A prototype NPU front‑end: classify memory requests as **KV** vs **Tensor**, apply separate replacement/prefetch rules.
- Implement a simple **dynamic partitioner** (e.g., 4 MB steps) that moves MBs between partitions
  based on hit rate and miss penalty.
- Connect a small **SPM** model to tile compute for controlled streaming.

## 8) Conclusion

**TFusionTensor v0.2** couples a shift‑centric compute fabric with a **single‑depth, policy‑smart cache** (TFusionVcache).
For AI students and engineers, this is a practical template to build efficient inference/training accelerators.
