# 이미지 데이터 플로우 (최종 보강판)

## 1. 색공간 변환 (RGB ↔ YUV)

딥러닝 학습/추론에서는 **RGB float 텐서**가 표준이지만,  
실제 저장/전송은 **YUV420**이 주류입니다.  

- **변환 원리**: [RGB ↔ YUV 변환 공식](https://en.wikipedia.org/wiki/Y%e2%80%b2UV)  
  - Y (휘도), U/V (색차)로 분리  
  - YUV420은 U/V 채널을 2:1 subsampling → 데이터량 약 50% 절약  
- **실무 파이프라인**:  
  - 입력: 카메라 스트림(H.264/H.265, YUV420)  
  - 디코딩: HW decoder (NVDEC, V4L2 등) → **RGB tensor**  
  - 모델 입력: RGB float32 → GPU half/bfloat16  

👉 **저장/전송**: YUV420 / **학습·추론**: RGB float (표준)  

---

## 2. 단일 이미지 vs 영상(Frames)

### 단일 이미지 (Image-level)
- **분류**: CNN, ViT (ResNet, EfficientNet, Swin, DeiT 등)
- **검출**: YOLO, FasterRCNN, RetinaNet
- **세그멘테이션**: U-Net, DeepLab, Mask-RCNN

### 연속 프레임 (Video-level)
- **3D-CNN**: 공간+시간 동시에 convolution (C3D, I3D)  
- **CNN+RNN/Transformer**: Frame embedding → LSTM/Transformer  
- **Optical Flow 보강**: 프레임간 변화량을 채널로 추가  
- **Frame 관계 표현**: [Video Processing – Frame 관계](https://en.wikipedia.org/wiki/Video_processing#Frame_rate_and_time_base)  

---

## 3. 최신 트렌드
- **Video Transformer (ViViT, TimeSformer, Video-Swin)**  
- **Hybrid**: CNN (공간) + Transformer (시간)  
- **Self-supervised Video Learning**: 프레임 순서 섞기, Masked Frame Prediction  
- **효율화**: keyframe만 처리하고 중간 프레임은 Optical Flow 기반 보간  

---

## 4. 표준 공개 이미지 데이터셋
| 데이터셋 | 용도 | 규모 | 특징 |
|----------|------|------|------|
| **MNIST** | 숫자 분류 | 60k train, 10k test | 28×28 grayscale, classic |
| **CIFAR-10/100** | 분류 | 60k | 32×32 RGB, 소규모 벤치마크 |
| **ImageNet-1k** | 분류 (대규모) | 1.2M train, 50k val | 1000 classes, RGB |
| **COCO** | 객체 검출/세그멘테이션 | 330k 이미지, 80 클래스 | bbox + segmentation label |
| **Pascal VOC** | 검출/세그멘테이션 | 20 클래스 | 2007/2012 버전 유명 |
| **Cityscapes** | 자율주행 세그멘테이션 | 5k high-quality 라벨 | 도시 장면, pixel-level mask |
| **OpenImages** | 대규모 detection | 9M 이미지 | 600+ 클래스, Google 공개 |
| **CelebA** | 얼굴 속성 분류 | 200k 얼굴 | attribute/landmark 라벨 |
| **LSUN** | 장면 인식 | 수백만 이미지 | 특정 scene (bedroom, church) |
| **Places365** | 장면 분류 | 1.8M | 365 scene classes |

---

## 5. 데이터 플로우 요약

### 학습
```
CPU: jpg/png → uint8
   → float32 normalize (0~1 or -1~1)
   → resize/crop
   → augmentation (flip, jitter, mosaic…)
   → batch tensor float32
GPU: half/bf16 텐서 (accum FP32)
   → Conv/GEMM/Attention
   → Loss FP32 → backward
```

### 추론
```
CPU: jpg/png → uint8 → float32 normalize
   → resize/center crop
GPU: half/bf16 텐서
   → 모델 추론
   → (검출) NMS, (세그) mask decode
CPU: 결과 후처리 (bbox rescale, mask resize)
```

---

## ✅ 최종 결론
- **저장/전송 포맷**: YUV420 (압축 효율)  
- **학습/추론 입력**: RGB float tensor (pretrained 호환성 때문)  
- **단일 이미지**: 분류/검출/세그멘테이션  
- **영상**: 3D-CNN, CNN+RNN, Video Transformer (Temporal learning)  
- **대표 데이터셋**: MNIST, CIFAR, ImageNet, COCO, VOC, Cityscapes, OpenImages, CelebA 등  
