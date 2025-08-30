
# Cache‑Centric System Integration

캐시를 중심에 두고, **Host/External Memory/SPM/Tiles/Codec**과의 연결을 정리합니다.

- **Host DMA/Queue** → Cache Front‑End: infeed/outfeed, 제어 메시지(QoS, 파티션 힌트)
- **External Memory (DDR/HBM)** ↔ Shared Cache: 미스/프리패치 라인, 압축/패킹
- **SPM** ↔ Shared Cache: 타일단위 burst, ping‑pong 버퍼
- **Tiles** ↔ SPM: compute 스트림 (block‑K), 결과는 PostOps/Decoder 경유
- **Codec(Scale/Calib)** ↔ SPM: 동적 스케일 보정, 포맷 변환

운영 포인트:
1. **KV 지연 민감** → 캐시 우선순위 상향, 파티션 확대
2. **Tensor 대역폭 민감** → 프리패치·스트림버퍼·bypass 튜닝
3. **DVFS 연동**: B_eff 추정치가 상승하면 f‑target 상승(메모리 지붕선 상향), 반대면 하향
