
# UE8M0 Front-side Shared Cache — Policy (64 MB physical → Logical KV/Tensor)

## 목표
- 64 MB **단일 물리 캐시**를 **논리 2 파티션(KV/Tensor)** 으로 운용
- 기본 분할: **32 MB / 32 MB**
- **히트율·미스패널티·대역 점유율**을 기반으로 **MB 단위 가변 재할당**(동적 파티셔닝)

## 물리 구성(요약)
- 뱅크: 16 banks × 4 MB/bank (=64 MB)
- 라인/블록: 128 B(기본), 정책별 가상 블록 크기 지원(KV=64–128 B, Tensor=256–512 B 스트림버퍼)
- 연관도: 16‑way (way‑mask로 파티션)
- 태그: policy bit(K/T), pin/lock bit, age/RRPV, reuse‑hint
- 포트: 2R1W, bank‑interleave
- 압축: UE‑헤더 + FP8 pack (KV hotset), Tensor는 무압축 우선(스트림)

## Front‑End (Classifier/Arbiter)
- 분류키: op‑type(Decode/KV vs GEMM/Conv), stride/size, reuse‑hint, stream‑ID
- 결정: (a) KV‑bucket, (b) Tensor‑bucket, (c) Bypass (재사용 낮음)

## KV‑policy
- 대체: **SRRIP + pin**(토큰 윈도 고정), 2‑queue(LRU‑hot/FIFO‑cold) 혼합 가능
- 프리패치: head‑of‑sequence(+1 token), warp‑공유 재사용 인지
- 쓰기: write‑back, write‑allocate

## Tensor‑policy
- 대체: **streaming‑friendly (NMR/Bypass‑prefer)** — 1회성 타일은 미적재
- 프리패치: 2‑갈래(odd/even bank) + block‑K 경계 인지(≥2 타일 선행)
- 쓰기: no‑write‑allocate (중간산물은 SPM 재순환)

## 동적 파티셔닝(논리 MB 가변)
- 상태: `Hk, Ht`(히트율), `MPk, MPt`(miss penalty), `BQk, BQt`(DRAM 큐 점유)
- 목표: 총 성능 최대화 & KV‑latency 최소화
- 조정 주기: 10–50 ms 윈도우, 히스테리시스(±4 MB step, min 16 MB, max 48 MB)

### Pseudo‑code
```
S_k = w1*Hk - w2*MPk - w3*BQk
S_t = w1*Ht - w2*MPt - w3*BQt
Δ = S_k - S_t
if Δ > θ and KV_MB < 48: KV_MB += 4; T_MB -= 4
elif Δ < -θ and T_MB < 48: T_MB += 4; KV_MB -= 4
apply_waymask(KV_MB, T_MB)   # MB→ways 매핑 LUT
```
- 안정화: 조정 후 2주기 쿨다운, QoS: KV 우선순위 cap

## QoS / MSHR
- MSHR 풀: KV/Tensor 분리, 상한 설정(폭주 방지)
- Arbiter: latency‑sensitive(KV) 우선, Tensor 대역폭 슬라이싱

## 측정/텔레메트리
- 히트율, 평균 miss‑penalty, DRAM 큐점유, bank‑conflict, prefetch accuracy
- 런타임이 DVFS/f‑target 및 파티션 비율 동조
