# 현장감 있는 공개 오디오 테스트셋 가이드

LJSpeech 같은 스튜디오 수준의 깨끗한 음성과 달리, **실제 환경(far-field, noisy, conversational)**을 반영한 공개 데이터셋 정리.

---

## 1. VOICES (Voices Obscured in Complex Environmental Settings)

**설명**: LibriSpeech의 깨끗한 음성을 실제 방의 다양한 노이즈 환경(리버브, 텔레비전, 라디오, 배경 잡음 등)과 결합하여 원거리 마이크로 수집한 대규모 데이터셋. 12대 마이크에서 120시간 이상 녹음됨 (Creative Commons BY 4.0)  
출처: [registry.opendata.aws](https://registry.opendata.aws/voices/) · [arxiv.org](https://arxiv.org/abs/1804.05053) · [sri.com](https://www.sri.com)

**용도**: 실환경(far‑field) ASR, 노이즈/리버브 강건성 평가, 원거리 음성 인식 등.  

**자세한 정보**: [VOICES 공식 설명 페이지 (SRI/Lab41)](https://voices18.github.io/)  
추가 참고: [arxiv.org](https://arxiv.org/abs/1804.05053) · [voices18.github.io](https://voices18.github.io/) · [registry.opendata.aws](https://registry.opendata.aws/voices/)

---

## 2. GigaSpeech

**설명**: 오디오북, 팟캐스트, 유튜브 기반 다양한 도메인의 발화를 포함. 최대 40,000시간의 음성.  
출처: [arxiv.org](https://arxiv.org/abs/2106.06909) · [openslr.org](http://openslr.org)

**용도**: 대규모 범용 ASR 학습.  

---

## 3. SPGISpeech / Earnings-22

**설명**: SPGISpeech는 실시간 기업 실적 발표 콜, Earnings-22는 수천 시간 규모의 실제 컨퍼런스콜 음성.  
출처: [huggingface.co](https://huggingface.co/blog/audio-datasets) · [github.com](https://github.com/Yuan-ManX/ai-audio-datasets)

**용도**: 금융/비즈니스 도메인 강건 ASR.  

---

## 4. AMI Meeting Corpus

**설명**: 회의실 환경에서 중앙·개별 마이크를 사용해 녹음된 다자간 회의 음성. 약 100시간 분량.  
출처: [huggingface.co](https://huggingface.co/datasets/ami)

**용도**: 멀티스피커 회의 음성 인식, diarization, 대화 모델링.  

---

## 5. Buckeye Corpus

**설명**: 자연스러운 인터뷰 기반 발화, 방언과 연속 음성 포함. 40명의 화자.  
출처: [buckeyecorpus.osu.edu](https://buckeyecorpus.osu.edu) · [en.wikipedia.org](https://en.wikipedia.org/wiki/Buckeye_Corpus)

**용도**: 자연 회화 음성, 방언 연구, 인터뷰 음성 인식.  

---

## 6. Common Voice (Mozilla)

**설명**: 전 세계 자원자들이 기여한 다양한 언어, 억양, 환경에서의 발화 데이터. 수천 시간 이상.  
출처: [commonvoice.mozilla.org](https://commonvoice.mozilla.org)

**용도**: 다언어 ASR, 발화자/환경 다양성 연구.  

---

## 7. VoxCeleb2

**설명**: 실제 방송, 인터뷰 등에서 추출된 수천 명 화자의 음성. 배경 잡음, 리버브, 다양한 억양 포함.  
출처: [www.robots.ox.ac.uk](https://www.robots.ox.ac.uk/~vgg/data/voxceleb/vox2.html)

**용도**: 스피커 인식, 실세계 noisy 환경 음성 인식.  

---

# ✅ 요약

| 데이터셋       | 특성 요약                           | 추천 용도                        |
|----------------|------------------------------------|----------------------------------|
| **VOICES**     | 실제 환경 노이즈+리버브             | 원거리 마이크 ASR, 강건성 연구   |
| **GigaSpeech** | 다양한 도메인, 대규모              | 범용 ASR                         |
| **SPGISpeech** | 금융 발표/컨퍼런스콜               | 도메인 특화 ASR                  |
| **AMI**        | 회의 대화, 멀티스피커              | 회의 인식, diarization           |
| **Buckeye**    | 자연 회화, 방언 포함                | 인터뷰/회화 인식                 |
| **CommonVoice**| 다언어, 다양한 억양/환경            | 다언어/다발화자 학습             |
| **VoxCeleb2**  | 방송·인터뷰 기반, 잡음 포함         | 스피커 인식, noisy 환경 음성     |
