# Audio Data Flow: WAV → GPU Training/Inference (FP32 기준)

## 1. Host (CPU) Side

| 단계 | 데이터 타입 / 포맷 | 주요 연산 / 처리 | 비고 |
|------|-------------------|------------------|------|
| **파일 디코드** | WAV (PCM16/24/32) → **int16** 버퍼 | 파일 I/O, libsndfile/sox/torchaudio | WAV → raw PCM |
| **정규화** | **int16 → float32** | 스케일링 (÷32768.0) | 값 범위 [-1,1] |
| **전처리 (옵션)** | **float32** | DC 제거(HPF), 리샘플(FIR/IIR), 채널합 | 통계/계수 누적은 float64 사용 가능 |
| **Loudness/SNR 증강** | **float32 (in/out)**, 통계 **float64** | RMS, LUFS, SNR 계산, 노이즈 믹스 | 안정성 위해 통계는 float64 |
| **특징 추출 (옵션)** | 입력 **float32** → STFT **complex64** → magnitude/log **float32** | FFT, Mel matmul | CPU: FFTW/MKL/soxr |
| **마스킹** | 마스크: **bool/uint8/float32** / 대상: **float32** | elementwise 곱, convolution masking | Spectrogram mask, FIR mask |
| **배치 구성** | **float32** (또는 float16 준비) | pinned memory, prefetch | `pin_memory=True` |
| **GPU 전송** | Host float32/16 → Device float32/16 | DMA (PCIe/NVLink) | `non_blocking=True` |

---

## 2. GPU Side

| 컴포넌트 | dtype/포맷 | 주요 연산 (커널) | 비고 |
|----------|------------|------------------|------|
| **입력 텐서** | **float32** (기본) / **float16, bfloat16** | 텐서 이동, cast | 추론/학습 모두 AMP 가능 |
| **CNN/Conv 블록** | half/bfloat16 (계산), **FP32 accumulate** | cuDNN Conv (Winograd/FFT) | Tensor Core 사용 |
| **GEMM/FC 레이어** | half/bfloat16, 가중치도 half | cuBLAS / CUTLASS GEMM | accumulate FP32 |
| **정규화/활성** | 내부 통계 **float32** | BN/LayerNorm | Mixed precision에서도 통계는 FP32 |
| **어텐션 (있다면)** | QKV half/bf16, softmax **float32** | GEMM, softmax | mask: bool/uint8 → float(-inf) |
| **손실 계산** | **float32** | CE/CTC/MSE, STFT Loss 등 | 안전을 위해 FP32 고정 |
| **옵티마이저 상태** | **float32** | AdamW, 모멘트 1/2차 | 파라미터는 half, 상태는 FP32 |
| **체크포인트** | 혼합 (weight FP16, state FP32) | serialize | 대형 모델 효율화 |

---

## 3. Data Flow Summary

### Training
```
CPU: wav → int16 → float32 normalize
   → 전처리(float32, 통계 float64)
   → (옵션) STFT complex64 → mag/log float32
   → masking(bool/float32)
   → pinned buffer float32/16
GPU: half/bfloat16 텐서 (accum FP32)
   → Conv/GEMM/Attention
   → Loss FP32 → backward (grad FP16/32)
   → Optimizer state FP32
```

### Inference (Streaming)
```
CPU: wav → float32 → frame split/overlap
   → (옵션) STFT/Mel float32
GPU: half/bfloat16 input
   → 모델 추론
   → (디코더/ISTFT 등) FP32
CPU: overlap-add → 출력 조립
```

---

## 4. 추천 기본값
- **CPU 전처리**: float32, 통계계산 float64
- **STFT/Mel**: FFT complex64 → magnitude/log float32
- **마스크**: bool/uint8(이진) 또는 float32(소프트)
- **GPU 학습**: AMP (half/bfloat16 compute, FP32 accumulate/손실/통계, 옵티마 상태 FP32)
- **추론**: 가능하면 FP16/BF16, INT8은 PTQ/QAT 후 적용
