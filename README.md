# UE8M0-Neuron-Quant (v0.1.4a)

[KO](README.md) | [EN](README_en.md) | [ZH](README_zh.md)

**UE8M0**는 *변화(차분)*·*이벤트* 중심의 저전력 양자화/부호화 스킴입니다.  
`2^E` 스케일(쉬프트) + FP8 가수 조합으로 **곱셈 없이(shift만)** 넓은 동적 범위를 다룹니다.

---

## 🧭 Quick links
**Docs:** [KO](docs/algorithm_full_ko.md) · [EN](docs/algorithm_full_en.md) · [ZH](docs/algorithm_full_zh.md)  
**Diagrams (SVG):**  
- Overview: KO/EN/ZH DOT → `docs/diagrams/ue8m0_overview_auto*.dot`  
- Sync (vertical): KO/EN/ZH DOT → `docs/diagrams/ue8m0_sync_auto_vertical*.dot`  

> Windows 변환: `docs/diagrams/dot2svg.bat` 로 `.dot → .svg`

---

**UE4T**는 **UE8M0 철학**을 **4비트** 포맷으로 확장한 경량 부호화 방식입니다.  
- 2^E 스케일 (shift) + ΣΔ 이벤트 + 4bit 토큰 맵  
- 작은 변화: ΣΔ ±1, 큰 변화: MAX/MIN, 중간: NORM_ESC+payload  
- 곱셈기 없는 하드웨어 구현 최적화  

👉 [UE4T v0.3 상세 문서](docs/ue4t_format_v.0.3.md)

---

## ✨ What’s UE8M0?
- **Differential**: 입력 `x`에서 기준 `b`(EMA) 제거 → `d = x - b`  
- **Event-based**: 작은 변화는 ΣΔ ±1 pulse, 큰 변화는 **MAX/MIN** 이벤트  
- **Shift-only scale**: UE8M0의 `E`는 2의 거듭제곱 스케일 → 하드웨어乘法기 불필요  
- **FP8 mantissa**: 정밀도 담당(E4M3/E5M2)

---

## ⚙️ Tunable parameters (recommended ranges)
| Name | Meaning | Typical |
|---|---|---|
| `beta` | EMA 계수 | 0.01 ~ 0.2 |
| `lambda0` | 작은 변화 임계 | 센서 민감도에 맞춤 |
| `lambda_hi` | 큰 변화 임계 | 잡음대비 5~20× |
| `T_silence` | ΣΔ 발화 최소 지속 | 5~50 ms |
| `T_emit` | ΣΔ 최소 간격 | 1~10 ms |
| `T_refractory` | MAX/MIN 불응기 | 10~100 ms |
| `T_scale_dwell` | 스케일 체류 | 50~500 ms |
| `near_upper/lower` | FP8 경계 근접 판단 | 상위/하위 10% 등 |

> 장치가 조용하면 `T_silence↑`, 동적 범위가 넓으면 `E5M2`, 미세 감도가 필요하면 `E4M3` 권장.

---

## 🔁 Encoder–Decoder Sync
- 동일한 **EMA(b)·E 갱신**을 공유 → 토큰 유실에도 천천히 동기화 회복
- 예외 상황(토큰 드롭) 복구 팁: q가 경계에 몰리면 **SCALE 추정**(휴리스틱) 적용

---

## 🛠️ Build diagrams
```powershell
# Install graphviz first (dot in PATH)
# Convert single file
docs\diagrams\dot2svg.bat docs\diagrams\ue8m0_overview_auto_en.dot

# Convert recursively
docs\diagrams\dot2svg.bat docs\diagrams
