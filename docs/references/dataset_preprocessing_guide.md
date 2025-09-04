# 공개 음성 데이터셋 전처리 가이드라인

## 1. 대표 데이터셋의 배포 포맷
| 데이터셋 | 배포 형식 | 샘플레이트 | 채널 | 비고 |
|----------|-----------|-------------|------|------|
| **LJ Speech** | WAV (16-bit PCM) | 22,050 Hz | mono | TTS 표준 벤치마크 |
| **LibriSpeech** | WAV (16-bit PCM) | 16,000 Hz | mono | ASR 벤치마크 |
| **VCTK** | WAV (16-bit PCM) | 48,000 Hz | mono | 멀티스피커 TTS/ASR |
| **TED-LIUM** | WAV (16-bit PCM) | 16,000 Hz | mono | 강연 음성, ASR |
| **Common Voice** | 다양한 형식 (주로 WAV/MP3) | 48k 또는 16k | mono | 크라우드소싱, 변동성 큼 |

---

## 2. CPU에서 필요한 전처리 여부
| 단계 | 공개 데이터셋에서 필요성 | 설명 |
|------|------------------------|------|
| **디코딩** | ✅ 필요 | WAV → PCM16 → float32 |
| **정규화** | ✅ 필요 | int16 → float32 [-1,1], 혹은 이미 float32일 경우 생략 |
| **리샘플링** | ⚠️ 경우에 따라 | 모델이 요구하는 SR과 다르면 필수 (ex: LibriSpeech 16k → TTS 22.05k) |
| **채널 처리** | ⚠️ 경우에 따라 | 대부분 mono 제공 → stereo 데이터셋은 모노 변환 |
| **DC 제거/필터링** | ❌ 보통 불필요 | 공개 데이터셋은 이미 정제됨, 단 특수 도메인(노이즈 음성)은 예외 |
| **Loudness 표준화** | ❌ 연구 목적이면 불필요 | 다만 TTS 음질 평가시 LUFS 맞추는 경우 있음 |
| **증강(Augmentation)** | ✅ 학습 시 필요 | 노이즈 믹스, 타임마스크, 주파수마스크 등 (SpecAugment 계열) |
| **세그먼트화** | ✅ 필요 | 길이가 들쭉날쭉하므로 crop/pad/mask는 CPU에서 처리 |
| **패딩/마스크 생성** | ✅ 필요 | GPU 배치 학습용, attention mask 등 |

---

## 3. GPU로 넘기기 전에 최종 데이터 타입
- **waveform 기반 모델 (raw audio input)**  
  - CPU: float32 waveform 준비 (길이 crop/pad)  
  - GPU: float16/bfloat16로 변환 후 학습 (AMP), 누적·손실은 FP32  
- **spectrogram 기반 모델 (Mel/STFT input)**  
  - CPU: float32 spectrogram 계산  
  - GPU: float16/bfloat16 텐서로 전송  

---

## 4. 학습 vs 추론에서의 차이
| 구분 | 학습 | 추론 |
|------|------|------|
| **증강** | 필요 (SpecAugment, Noise mix) | 불필요 |
| **세그먼트화** | random crop (일반화 ↑) | center crop 또는 전체 시퀀스 |
| **정규화** | 항상 필요 | 항상 필요 |
| **리샘플링** | SR mismatch 시 필요 | SR mismatch 시 필요 |

---

## 5. 왜 이런 정리가 필요한가?
- 공식 튜토리얼은 **“tensorflow/keras example: load_dataset → map(preprocess) → train()”** 수준에 그치기 때문에,  
  - 어떤 경우 전처리를 생략해도 되는지  
  - 어떤 경우 반드시 CPU 단계에서 해줘야 하는지  
  명확하지 않음.
- 실제로는 연구자·학생들이 “그냥 torchaudio.load로 float32 뽑고 GPU에 올려 학습” 하지만, SR mismatch, padding 정책, 증강 여부가 결과 품질에 큰 영향을 미침.

---

# ✅ 최종 요약
- **공개 데이터셋 대부분은 clean WAV(PCM16) 상태 → decode+normalize만 하면 된다.**  
- **리샘플링, crop/pad, augmentation, mask 생성은 CPU 단계에서 여전히 중요하다.**  
- **추론 시에는 decode+normalize(+resample)만으로 충분하다.**
