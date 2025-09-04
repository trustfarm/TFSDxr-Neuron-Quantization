# TFSDxr (TimeFeedBack SigmaDelta for eXtensibleReality) Progress. 250904_v0.1

**Disclaimer**: The Korean (KO) version is the original. If anything in translation feels off or ambiguous, please refer to the KO version.

---
[KO](README.md) | [EN](README_en.md) | [ZH](README_zh.md)
---

We extend the human-perception primitives of **difference (SigmaDelta)**, **residual**, and **time** to explore an encoding method that resembles **neurons**. We also apply this to AI hardware and software to study **AI ESG**.

## Philosophy

Entering the era of Artificial Intelligence (AI), the benefits of AI should reach everyone. But AI pushed by **unbounded energy use** that harms the planet and **relentless competition** isn’t really beneficial from a global **ESG (Environment, Social, Governance)** point of view. So we focus on **more efficient AI algorithms** and **AI infrastructure**. We already know a lot of fundamentals. From analog days to early digital, the basic principles and technologies are out there—and the core algorithms used in AI should be **re‑invented for efficiency** on top of those foundations.

This started from a small idea: *How can we minimize the massive energy consumption for training and inference in AI?*

Our philosophy is to build **codecs**—the foundation of information engineering—and use them to develop efficient hardware and algorithms. Also, this shouldn’t be monopolized by certain people, countries, or companies; we approach it as **“FairUSE.”**

So yes, the research can be open to everyone, but we may still put **human gating** via licenses and patents where it makes sense.

We’re still early; it may not be super efficient yet. But like life and humanity evolved toward higher efficiency, this project will also keep evolving.

“NOMAD_AI”

“HUMAN_AI”

## Goals of the codec

1. **Low‑Cost, Low‑Power, High‑Efficiency**: Can we deliver data efficiently at low cost?
2. **Scalability**: Like Sun Wukong’s Ruyi Staff—“Grow, Ruyi Staff!”
3. **Genetic DNA Compression**: Earth’s life is built from AGTC—what’s the secret?
4. **How to implement?**

## While developing the codec algorithms…

1. There are many efficient methods in industry already. The catch is aligning fundamentals with **current AI algorithms and infra**. TFSD blends the most conventional principles with the latest open tech and theory, adapting them to build new paths.
2. We combine academic theory with hands‑on industry experience to craft realistic **trade‑offs** and **optimistic** techniques. Cost perspective is always in scope—but **innovation first**. Based on innovation, we squeeze practical **cost optimization** with real‑world know‑how.
3. We apply technology from a **TCO (Total Cost Optimization)** perspective.
   - The base codec we’re building now might be inefficient, but we’ll squeeze efficiency from other HW angles to cover it.
   - We actively adopt brand‑new, cost‑effective tech or IP.
   - If we end up building a chip (SoC), we’ll decide with realistic trade‑offs.

## Introducing TFSDxr

1. With neuron‑style **kappa/emit** packing, we tested and verified using **8‑bit floating‑point / integer (IntegerMask)**.
   - This is **v0.1**, tested on **16 generated patterns**.
   - We tested adaptive, floating‑point‑based (Adaptive Floating Point) **difference delta / residual**:
     - For **FP8**, both float version and integer‑parameter version got **roughly near (RMSE 5%)**.
     - Because the **compute cost** of floating‑point theory vs. practical integer implementation diverges a lot in SW/HW, we validate algorithms in float, then re‑implement in **integers and bit ops** for deployment.
     - We had already confirmed baseline feasibility when releasing **TFSD8 (8‑bit)** / **TFSD4 (uedt4)**; with **TFSD16/32** we found more things to consider, so we’ll incorporate delta feedback and publish upgraded versions.
2. We aim for **variable‑length packets**, with a codec that can efficiently deliver data even over **1‑wire** links.
   - Using **difference delta / residual** to reflect real‑time data needs many parameters.
   - Since parameters adapt to various waveforms, it’s a bit like sending data to people with different “personalities”—the reaction can differ.

   During TFSD8 evaluation, we observed the following *“human‑personality‑like”* parameter sets:
   ---
   **Examples of parameter sets comparable to “human personalities”**

   - **Hypervigilant**: alpha≈0.2, theta_lsb≈0.75, T_silence=1, T_emit=1  
     Pros: reacts to tiny changes immediately; agile to abrupt change  
     Cons: events may be frequent in flat regions (small α → weaker normalization)

   - **Balanced**: alpha≈0.7, theta_lsb≈1.0, T_silence=2, T_emit=2  
     Pros/Cons balanced; works well for most data

   - **Stoic**: alpha≈1.2, theta_lsb≈1.25, T_silence=3, T_emit=3  
     Pros: minimizes overreaction in flat regions (strong normalization)  
     Cons: may be late to catch micro‑events

   While applying the algorithm, we found—especially in TFSD16 evaluation—that the **way delta was computed** made control hard. We decided to **re‑verify** and disclose a more organized **algorithm feasibility** instead of releasing raw details.

## About TFSD16

1. Based on TFSD8’s **Kappa/Emit**, we compared TFSD16’s baseline with **FP16**.
   - We tried using **DPCM (Delta Pulse Code Modulation)** as the kernel when transmitting 16‑bit.
   - The outcome wasn’t what we intended, and even sweeping many parameters didn’t satisfy us.
   - We suspect an **implementation issue**.
   - With **64QAM** in tests, we got meaningless RMSE and waveform distortion.
   - Sending only the top bits of Exp/Mantissa delta to catch up did not reduce **BPS (Bits Per Sample)**.
   - We concluded: packing float‑based delta/residual into bit‑based form **as we did** wasn’t aligned with the algorithm’s intent.
2. Back to basics:
   1) We simplified the encoder/decoder so it can eventually be **hardware‑optimized**, and first centered on **mantissa packing**.  
   2) Since floating‑point values end up as **bit operations**, we searched for delta from the **bits perspective**. Not fully optimal yet, but we found clues for packing delta/residual from the **bitmask** side.

## Lesson Learned ::

1. **Wrong way to compute delta/residual error.**  
   If you compute  
   `Delta = FP_enc(t) − FP_enc(t−1)`  
   on the encoder side of the raw input, we confirmed that **as bits increase**, errors keep surfacing even if the decoder “catches up.” The right approach is  
   `Delta = FP_enc(t) − FP_dec(t−1)`—the decoder is what ultimately interprets the final data.

2. **Closed‑loop encoder.**  
   Like video encoders (e.g., MPEG‑4/HEVC), which are complex (and include a decoder inside) to achieve compression while decoders are simpler, TFSD16 should also compute **Delta** and **SUM(Residual)** **based on the decoder’s** `FP_dec(t−1)` and transmit adaptively.

3. **Understanding floating‑point bitmask.**  
   Helpful links:
   - Arbitrary half‑precision converter: <https://flop.evanau.dev/half-precision-converter>
   - IEEE‑754 floating‑point converter: <https://www.h-schmidt.net/FloatConverter/IEEE754.html>

   For **FP16**:

   | sign | Exponent(5) | mantissa |
   |------|-------------|----------|
   | 1bit |     5bit    |  10bit   |

From public audio datasets, we used samples from [Keith Ito’s “The LJ Speech Dataset”](https://keithito.com/LJ-Speech-Dataset/) for experiments.

### Let’s look at a table from the test data

\\[LJ002-003mix.wav, data byte offset 332440~332519, 4 bytes FP32 align]

```
t, decimal, sign, expbits, mantissa, dexp, dmantisa    , delta[(t)-(t-1)]
 83114, -0.039307, 1, 01011, 0000000100 , ----- , --------1-- , -0.000031 [0,00000, 0000000010]
 83115, -0.039337, 1, 01011, 0000000111 , ----- , ---------1-1 , -0.000031 [0,00000, 0000000011]
 83116, -0.039368, 1, 01011, 0000001010 , ----- , --------1-- , -0.000031 [0,00000, 0000000011]
 83117, -0.039398, 1, 01011, 0000001101 , ----- , ---------1-1 , -0.000031 [0,00000, 0000000011]
 83118, -0.039398, 1, 01011, 0000001101 , ----- , ---------- ,  0.000000 [0,00000, 0000000000]
 83119, -0.039429, 1, 01011, 0000010000 , ----- , --------1-- , -0.000031 [0,00000, 0000000011]
```

As you can see, the **bitmask changes**. If we can **pack** and **transmit** those changes efficiently, we can improve.

Bitmask‑based operations also make the decoder logic very simple. If later implemented in **C**, it’s light on system resources and **ASIC‑friendly**.

Currently, when the sign changes we resend a **KF (KeyFrame)** including the exponent; and we evaluate mantissa with **M5W1** (among 10‑bit mantissa, packing the upper 5 bits or the lower 5 bits).

### Python Integer‑Mask‑based Reference Source code V0.3b

- [README_TFSD16_V0_3b.md](tfsd16_v0_3b_intcodec/README_TFSD16_V0_3b.md)

## TODO and Ideas for Improvements ::

1. Implement delta with **E5/E8 expansion** excluding the sign.  
   - Reason: complexity expected when the leading sign flips.  
   - If we renormalize from **[-1.0, +1.0]** to **[0, 2.0]**, computing/packing **exponent bitmask distance** in integers gets easier.
2. Implement in **C**.  
   - When packing the bitstream, we can remove unnecessary **padding bits** due to bit alignment.  
   - (In current Python code, non‑byte alignment may cause alignment errors.)
3. Apply **Kappa / Emit** and re‑verify/improve the **DPCM kernel**.
4. When using the TFSD codec as quantization specialized for **Audio/Video**, compose with existing **pre/post‑processing filters**.

  ⇒ See: [references/audio_datapath.md](../references/audio_datapath.md)

## License
Apache License 2.0 © 2025 TrustFarm  
SPDX‑License‑Identifier: Apache‑2.0
