# LLM 학습 데이터 플로우

## 1. 데이터 소스 (Raw Corpus)
- **웹 크롤링**: CommonCrawl, Wikipedia, 뉴스, 블로그, Q&A  
- **라이선스/퍼블릭 데이터셋**: Books, ArXiv, StackExchange, Github  
- **도메인 특화 데이터**: 의료, 법률, 코드 등  
- **필터링**: 저작권, 개인정보, 노이즈 제거  

출력: **Raw Text (UTF-8, JSONL 등)**

---

## 2. CPU/데이터센터 전처리 (Preprocessing)

| 단계 | 데이터 타입 | 주요 연산 | 설명 |
|------|-------------|----------|------|
| **수집** | 문자열 (UTF-8) | 크롤러, API | 원시 텍스트 확보 |
| **클린징** | 문자열 | regex, heuristic 필터 | 광고/HTML/스팸 제거 |
| **토큰화** | 문자열 → 정수 ID | BPE, SentencePiece | Subword 단위 분할 |
| **샘플링/셔플** | int sequence | reservoir sampling, shuffle | 데이터 분포 균형 |
| **시퀀스화** | int tensor (N×L) | padding, chunking | 고정 길이 블록(L=1k~32k) |
| **마스크 생성** | bool/uint8 mask | causal mask | autoregressive 제약 |
| **배치화** | int tensor (B×L) | pinned memory | GPU 전송 준비 |

출력: **Token ID tensor (int32/uint16)**

---

## 3. GPU 학습 (Training)

| 컴포넌트 | 데이터 타입 | 주요 연산 | 설명 |
|----------|-------------|----------|------|
| **임베딩 레이어** | int32 idx → float16 vector | embedding lookup | 토큰→벡터 |
| **트랜스포머 블록** | float16/bfloat16, FP32 accum | GEMM, matmul, softmax | Multi-Head Attention + FFN |
| **LayerNorm** | float32 (통계) | reduction | 안정성 위해 FP32 |
| **Loss** | float32 | cross entropy | FP16/32 혼합 |
| **역전파** | grad FP16/32 | GEMM backward | optimizer update |
| **옵티마이저 상태** | FP32 | AdamW (moments) | 파라미터는 half, 상태는 FP32 |

출력: **학습된 모델 파라미터 (수십억~수천억 float16/32)**

---

## 4. 추론 (Inference)

| 단계 | 데이터 타입 | 주요 연산 | 설명 |
|------|-------------|----------|------|
| **입력 텍스트** | 문자열 | 토크나이저 | Subword 분할 |
| **토큰 ID** | int32 → float16 | embedding | GPU 전송 |
| **트랜스포머 forward** | half/bf16, accum FP32 | GEMM, KV-cache, softmax | 반복 디코딩 |
| **샘플링/디코딩** | float32 logits | top-k, nucleus | 토큰 선택 |
| **출력 텍스트** | int seq → 문자열 | detokenizer | 사용자 응답 |

---

## 5. 대규모 LLM 학습 특징
- **데이터 크기**: 수십억~수조 토큰
- **시퀀스 길이**: 1k → 4k → 32k 이상 (context extension)
- **분산 학습**:  
  - **데이터 병렬(Data Parallel)**: 다른 GPU에 서로 다른 batch  
  - **모델 병렬(Model Parallel)**: 레이어 분할 (tensor/pipeline parallel)  
  - **ZeRO, FSDP**: Optimizer state/gradient 분산 저장
- **정밀도**: AMP (FP16/bfloat16 compute, FP32 accumulate)  
- **효율화**: 체크포인팅, KV-cache, FlashAttention

---

## 6. 전체 플로우 요약

### 학습
```
[Raw Text Corpus]
   ↓ (크롤링/수집)
[Clean/Filter]
   ↓
[Tokenization → int IDs]
   ↓ (chunking, padding, mask)
[Batch Tensor (B×L, int32)]
   ↓ (GPU 전송, half/bf16)
[Transformer Training Loop]
   ↓ (FP16 compute, FP32 accum, AdamW FP32 state)
[Trained Model Checkpoint]
```

### 추론
```
[Input Text] → [Tokenization] → [Embedding] 
   → [Transformer w/ KV-cache] → [Logits]
   → [Sampling/Decoding] → [Output Text]
```

---

## ✅ 최종 결론
- **CPU/데이터센터**: 텍스트 정제, 토큰화, 시퀀스 구성 (int32)  
- **GPU 학습**: FP16/bf16 텐서 연산(GEMM/Attention), FP32 누적  
- **추론**: 동일 파이프라인이지만 KV-cache, 샘플링 전략 포함  
- **핵심 datatype 흐름**: 문자열 → int32 (토큰) → float16/bf16 (embedding & compute) → FP32(accum/loss/optimizer)  
