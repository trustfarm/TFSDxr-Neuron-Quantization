# PROTOCOL — TFSD16_V0_3b

## Frame Types (2 bits)
- `00` KF: next 16 bits = FP16 word (S1|E5|M10)
- `01` Patch: `pc(2b)=count−1` followed by `pc` patches
- `10` Reserved (SE6 in older drafts) — not used in V0_3b (SE change => KF)
- `11` ZeroRun: align to nibble, `0xF`(4b), `runlen`(4b ∈ [1..15])

## Patch Structure
Per patch:
- **Position**: `shift2(2b)` relative step; if absolute, `pos3(3b)`
  - `00` keep pos
  - `01` pos −= 1
  - `10` pos += 1
  - `11` read `pos3` absolute (0..7), then `pos = pos3`
  - `msb = 9 − pos`
- **Payload (M5+1)**: `M5(5b)` then `B1(1b)`
  - Write `[msb..msb−4]` from `M5`
  - If `msb−5 >= 0`, write `[msb−5]` according to `B1`
- Other mantissa bits remain as before.

## ZeroRun
- After type bits, pad to nibble: `(4 − (bits % 4)) % 4` zeros.
- Then `0xF` marker(4b), then `runlen`(4b). Decoder checks marker.

## Robust End-of-Stream
- If remaining bits are insufficient for a full field, treat as **padding** and fill remainder with the last reconstructed sample.

## License
Apache License 2.0 © 2025 TrustFarm  
SPDX-License-Identifier: Apache-2.0
