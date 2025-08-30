
# Shared Cache — 운영 정책(Ops)

## 초기화
- 기본 파티션: **KV 32 MB / Tensor 32 MB**
- prefetcher: Tensor‑prefetch depth=2 tiles, KV head‑ahead=+1 token
- QoS: KV‑priority=high, Tensor bandwidth slice=80% max

## 주기적 튜닝(10–50 ms)
1. Telemetry 수집: 히트율(Hk,Ht), miss penalty(MPk,MPt), DRAM 큐(BQk,BQt)
2. 점수 S_k,S_t 계산, Δ=S_k−S_t
3. |Δ|>θ 이고 여유 있으면 **±4 MB** 재할당(최소 16 MB, 최대 48 MB)
4. 2‑윈도 쿨다운 + 안정성 체크(prefetch accuracy, bank conflict)

## 장애/안전
- 캐시 오류(ECC): 라인 drop + 리필
- 과열/전력: DVFS f‑target 하향, Tensor slice 축소
- 폭주: MSHR 상한, Bypass 확대
