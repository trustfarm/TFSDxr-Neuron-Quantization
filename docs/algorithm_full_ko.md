# UE8M0‑Neuron‑Quant 알고리즘 (v0.1.3)

본 문서는 일반 독자와 엔지니어 모두가 이해하기 쉽도록 **직관적 서술(예시/흐름)**과 **기술적 보강(수식/근거)**을 함께 제공합니다.

---
## 1) 서론: 왜 차분/이벤트인가
이 알고리즘은 인간 신경계의 관찰에서 출발합니다. 사람은 **절대값**보다 **상대적 변화(차분)**와 **이벤트(극값/포화)**에 민감합니다.  
- **손가락 미세 터치**: 표면을 살짝 문지르면 아주 작은 요철도 “변화”로 느낍니다.  
- **파리 접촉 감지**: 힘은 작아도, “닿는 순간의 변화”가 감각을 일으킵니다.

UE8M0‑Neuron‑Quant는 이 원리를 디지털로 옮겨, **저전력 이벤트 기반 인코딩**을 구현합니다.

---
## 2) 용어와 토큰 (먼저 정의)
- **b**: 기준값(baseline). 지수이동평균(EMA)로 천천히 입력을 추종.  
- **d = x − b**: 차분. 변화 자체를 나타내는 신호.  
- **E**: UE8M0 스케일 지수. 2^E 배율(시프트)로 동적 범위 확장.  
- **r**: ΣΔ 누산기(잔여 오차/미세 변화 축적).

### 토큰
- **NORM(q)**: 일반 양자화 값(주로 FP8 q).  
- **MAX / MIN**: 큰 양/음 변화 이벤트.  
- **SCALE(±1)**: 스케일 지수 E를 한 스텝 조정.  
- **SILENT**: 발화 없음(유지).

---
## 3) 핵심 개념 정리
### 3.1 UINT8 vs FP8 vs UE8M0
- **UINT8**: 0~255 정수, 곱셈/스케일은 구현체에 의존.  
- **FP8**: 두 포맷이 일반적입니다.  
  - **E4M3**: 정밀도↑, 범위↓ → 미세 변화에 유리.  
  - **E5M2**: 범위↑, 정밀도↓ → 큰 범위를 안정적으로 커버.  
- **UE8M0(2^E)**: 배율이 2의 거듭제곱 → **곱셈기가 아닌 시프트**로 구현(전력/면적/지연에 유리).  
  FP8 원소의 **가수(정밀도)**와 UE8M0의 **배율(범위)**이 역할을 분담합니다.

### 3.2 오차 피드백(error‑feedback)
양자화 후 `residual = d − d̂`를 r에 누적하여 **체계적 편향을 제거**합니다.  
이는 ΣΔ/디더링과 같은 원리로, 미세 변화가 시간에 걸쳐 **±1 펄스**로 방출됩니다.

### 3.3 시간 파라미터의 의미
- **T_silence**: 디바운스. 지속된 작은 변화만 펄스 허용.  
- **T_emit**: 펄스 최소 간격. 과도한 발화 방지/전력 절감.  
- **T_refractory**: MAX/MIN 후 불응기. 이벤트 폭주 방지, 안정성 확보.  
- **T_scale_dwell**: 스케일 변경 최소 체류. E 튐 방지.

### 3.4 EMA로 b를 갱신하는 이유
EMA는 **저주파 추세**만 통과시킵니다. b가 느리게 움직이니 d가 **순수한 변화(고주파)**를 담아 효율적입니다.

---
## 4) 인코더 (의사코드, 가독성 개선)

```pseudo
# 파라미터(예): lambda0, lambda_hi, beta, T_silence, T_emit, T_refractory, T_scale_dwell
state:
  b, E, r
  t_last_emit, t_last_scale, t_event_quiet, t_silence

for each sample x at time now with step Δt:
  d = x - b

  # 1) 큰 이벤트 이후 불응기
  if now < t_event_quiet:
    b = (1 - beta)*b + beta*x
    continue

  # 2) 작은 변화(ΣΔ 경로)
  if |d| < lambda0 * 2^E:
    r += d * Δt
    t_silence += Δt
    if t_silence ≥ T_silence and (now - t_last_emit) ≥ T_emit and |r| ≥ 0.5 * 2^E:
       emit NORM(sign(r))      # ±1 펄스
       r -= sign(r) * 2^E
       t_last_emit = now
       t_silence = 0
    b = (1 - beta)*b + beta*x
    continue

  # 3) 큰 변화 이벤트
  if |d| > lambda_hi * 2^E:
    emit (MAX if d>0 else MIN)
    t_event_quiet = now + T_refractory
    b = (1 - beta)*b + beta*x
    continue

  # 4) 보통 변화(정규 양자화)
  u = d / 2^E
  q = FP8_quant(u)             # (E4M3 or E5M2)
  emit NORM(q)

  # 5) 오차 피드백
  d_hat = deFP8(q) * 2^E
  r += (d - d_hat)

  # 6) 스케일 적응
  if (near_upper(q) or near_lower(q)) and (now - t_last_scale) ≥ T_scale_dwell:
     E += +1 or -1
     emit SCALE(±1)
     t_last_scale = now

  # 7) 기준 갱신
  b = (1 - beta)*b + beta*x
  t_silence = 0
```

> **near 정의 예시**: `near_upper(q) ⇔ q ≥ 0.9·FP8_MAX`, `near_lower(q) ⇔ q ≤ 0.9·FP8_MIN`

---
## 5) 디코더 개요
- `SCALE(±1)` 토큰으로 E 동기화.  
- `NORM(q)`는 `deFP8(q) * 2^E`로 복원.  
- `MAX/MIN`은 임계 이벤트로 처리.  
- b 갱신은 인코더와 동일한 EMA 규칙 사용 → **상태 동기성**으로 토큰 절약.

---
## 6) 구현·활용 팁
- 시프트/비교 중심의 **Multiplier‑Free** RTL로 전력·면적 절감.  
- 파라미터 선택 가이드(예):  
  - 민감한 센서: E4M3 + 작은 lambda0, 짧은 T_silence  
  - 넓은 범위: E5M2 + 큰 lambda_hi, 긴 T_refractory  
- 적용 분야: 이벤트 카메라/접촉 센서, IoT, 임베디드 음성/진동 인코딩 등.

---
## 7) 다이어그램
- `diagrams/ue8m0_overview_auto.svg` (개요/시간/오차피드백/스케일 흐름)  
- `diagrams/ue8mue8m0_sync_auto_vertical.svg` (인코더‑디코더 동기/토큰 스트림)

> 모든 다이어그램은 **소스 덤프**(JSON 레이아웃 & DOT)와 함께 제공합니다.
