# UE4T: 4-bit Event/Differential Quantization (v0.1)

UE4T는 UE8M0의 철학(**차분·이벤트·2^E 스케일·EMA(b)**)을 유지하면서, **토큰을 4비트(니블)**로 표현하는 포맷입니다.
목표는 **乘法 없이(shift)**, **작은 LUT**와 **ΣΔ 누산**으로 미세 변화를 효율적으로 전달하는 것입니다.

---

## 1) 토큰 맵 (4-bit 코드 공간)

| Code | Token      | 의미/설명 |
|:---:|:-----------|:----------|
| 0x0 | SILENT     | 무토큰 구간 알림(타임아웃), RLE와 조합 가능 |
| 0x1 | SD+        | ΣΔ +1 펄스(미세 상승) |
| 0x2 | SD-        | ΣΔ -1 펄스(미세 하강) |
| 0x3 | SCALE+     | E ← E+1 (2배 스케일) |
| 0x4 | SCALE-     | E ← E-1 (1/2 스케일) |
| 0x5 | MAX        | 상한 이벤트(포화/상경계) |
| 0x6 | MIN        | 하한 이벤트(포화/하경계) |
| 0x7 | BASE_TICK  | b(EMA) 동기 힌트(옵션) |
| 0x8 | NORM_ESC   | 다음 니블이 NORM 페이로드 |
| 0x9 | RLE_ESC    | 다음 니블이 SILENT run-length |
| 0xA | RESET      | 상태 재동기(옵션) |
| 0xB | KEEPALIVE  | 상태 유지 하트비트(옵션) |
| 0xC~0xF | RSV/CRC | 예약/주기적 CRC4 등(옵션) |

### NORM 페이로드(1니블) 포맷
`p[3]` = 부호(0=+, 1=−), `p[2:0]` = 가수 인덱스 m∈{0..7}

값: `Δ ≈ sign * (1 + m/8) * 2^E`  
(간단한 LUT: `1.000, 1.125, 1.250, …, 1.875`)

---

## 2) 상태 및 파라미터

- 상태: `b`(EMA 기준), `E`(스케일 지수), `r`(ΣΔ 누산기), `t_last_emit`(ΣΔ 최소 간격), `t_refrac_end`(불응기 종료)
- 파라미터(권장 예시):  
  `beta∈[0.02,0.1]`, `lambda0`, `lambda_hi=5~20×lambda0`,  
  `T_emit=2~10ms`, `T_silence=20~100ms`, `T_refrac=20~80ms`, `T_scale_dwell=100~500ms`

---

## 3) 인코더 개요(의사코드)

```text
for each (x, now):
  d = x - b

  # 불응기
  if now < t_refrac_end: continue

  # 작은 변화: |d| < lambda0·2^E  → ΣΔ 누산
  if |d| < lambda0 * 2^E:
     r += d * Δt
     if (now - t_last_emit ≥ T_emit) and (|r| ≥ (lambda0·2^E)*K):
        emit(SD+ or SD-); r -= sign(r)*(lambda0·2^E)*K; t_last_emit=now
     goto update

  # 큰 변화: |d| > lambda_hi·2^E → MAX/MIN
  if |d| > lambda_hi * 2^E:
     emit(MAX or MIN); t_refrac_end = now + T_refrac; goto update

  # 중간 변화: NORM
  (sign, m) = quantize_NORM(d / 2^E)  # 1+m/8 근사
  emit(NORM_ESC); emit(payload(sign,m))

update:
  # 선택: 스케일 적응 (체류조건 & near)
  maybe_emit(SCALE±)
  # b 업데이트
  b = (1-beta)*b + beta*x
  # 무토큰 타임아웃
  if now - t_last_token ≥ T_silence: emit(SILENT) or emit(RLE_ESC,len)
