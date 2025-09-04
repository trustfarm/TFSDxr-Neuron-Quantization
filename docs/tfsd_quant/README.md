# TFSDxr (TimeFeedBack SigmaDelta for eXtensibleReality) Progress. 250904_v0.1

**Disclaimer** : 본 문서는 한국어(KO) 버전이 원본이며, 번역 과정에서 발생할 수 있는 문제나 모호한 부분은 한국어 버전을 참조하시기 바랍니다.

---
[KO](README.md) | [EN](README_en.md) | [ZH](README_zh.md)

---


**차변 (SigmaDelta)** , **잔차 (Residual)** , **시간 (Time)** 의 인간인지의 기본개념을 확장하여, 사람의 신경세포(Neuron)에 닮은 부호화방식을 연구하고 있습니다.
또한, 이를 AI Hardware , Software 에 적용하여 AI ESG 를 연구하고 있습니다.

## 철학 (Philosophy)

인공지능 (AI) 시대를 맞이하여, AI 의 혜택은 모두가 받을수있어야 합니다.
하지만, 지구의 환경을 해치는 무한 에너지 소모와, 무한 경쟁으로 인한 AI 발전이 지구전체의 ESG (Environment, Social, Governance) 관점에서 유익하지는 않습니다.
그래서 우리는 좀 더 효율적인 AI 알고리즘과 AI infra개발에 집중해야 합니다.
우리는 이미 수많은 기본기술과 원리를 알고있습니다.
아날로그 시대부터, 디지털 초반까지 우리의 저변에 이미 스며들어있는 기본적인 원리와, 기본 기술을 기반으로 인공지능에 사용되는 기본알고리즘들은 더 효율적으로 혁신이 되어야 합니다.

AI 에서, 학습, 추론을 위해서 사용되는 엄청난 에너지소비를 어떻게 최소화할수있을까? 하는 idea 에서 출발하였습니다.

정보공학의 기본이 되는 CODEC 과 이를 활용한 효율적 하드웨어, 알고리즘을 만들어야 한다는 철학을 가지고 있습니다.
또한, 이는 특정 사람이나, 특정 나라, 기업이 독점이 아니라, "FairUSE" 으로 접근되어야 합니다.

그러기에, 이런 연구는 누구에게나 공개되어서 쓸수있겠지만, License 와 특허를 통해서, 사람의 Gating 이 필요할수도 있습니다.

현재는 연구의 초반기라서, 아직은 덜 효율적일수있지만,
인류와 자연계의 모든 생명체는 최고의 효율을 지향하면서 진화해 왔기에, 본프로젝트도 계속 진화가 될것이라 생각합니다.

"NOMAD_AI"

"HUMAN_AI"

## CODEC 의 지향점.

1. **LOW-COST, LOW-POWER, HIGH Efficiency** : 저비용, 효율적으로 데이터를 전달할수있을까?
2. **Scalability** : 손오공 여의봉 처럼 무한 확장 가능할까? "커져라 여의봉~"
3. **Genetic DNA Compression** : 인간의 DNA (AGTC) 의 묶음으로 지구상의 생명체는 존재하는데, 그것의 비밀은? 
4. **How to implement?** : 어떻게 구현하지?

## CODEC 의 알고리즘을 개발하면서...

1. 이미 산업계에는 수많은 효율적인 방법이 존재합니다. 단지, 그것의 기본원리를 현재의 AI 알고리즘과, AI Infra 에 정합하기 어렵기 때문이지요.
TFSD 는 가장 Conventional 한 원리 부터, 최신의 공개된 기술, 이론을 융합하고, 차용(Adaptation) 하여, 새로운 방안을 개발합니다.

2. 학계의 이론적 배경과, 산업계의 실무적 경험을 융합하여, 현실적인 trade-off, optimistic 기법을 개발합니다.
   우리의 연구에는 항상 Cost 관점이 들어가 있습니다.
   하지만, Cost 우선은 아니고, Innovation 우선입니다. 
   Innovation 을 기반으로 하여, 현실적인 Cost Optimization 를 위해서 산업계의 경험으로 쥐어짜서 성공하는 방식을 택합니다.

3. TCO (Total Cost Optimization) 관점에서 기술을 적용합니다.
   - 지금 개발하는 가장 기본이 되는 CODEC이 비효율적일수 있겠지만, 다른 HW 관점에서 그 비효율을 커버할 효율을 쥐어짜냅니다.
   - 전혀 새로운 Cost Effective 한 기술이나 IP를 적극채택합니다.
   - 실제 칩(SoC)을 구현하게 된다면, 현실적인 Trade-off 를 따져서, 결정합니다.

## TFSDxr 을 소개하며.

1. kappa / emit 기반의 Neuron 알고리즘 기반 packing 방식으로, 8Bit 실수(FloatingPoint)/정수(IntegerMask) 기반으로 알고리즘을 테스트및 검증하였습니다.
   - 이는 v0.1 로서 16개의 생성된 테스트패턴 기반으로 테스트를 하였습니다.
   - Adaptive 하게 실수기반(Adaptive Floating Point 기반  차변 Delta / 잔차 residual) 를 테스트 하였고,
      - FP8 (8bit) 의 경우에는 실수버전 / 정수파라메터버전 이 어느정도 (RMSE 5%) 부근에 근접하였습니다.
      - 이론적 연산 (Float) 과 이를 현실화 한 정수(Integer) version 은 향후, System SW 및 HW 로 구현시, 연산 Cost 차이가 많이나기 때문에, 알고리즘의 검증은 실수 기반으로 하지만, 이의 현실적 적용은 정수 및 bits 연산으로 재구현합니다.
      - 이미, TFSD8 (8bits) / TFSD4 (uedt4) 을 공개할 시점에 기본적 Feasibility는 확인하였으나, TFSD16,32 를 구현하면서 발견한 고려점을 기반으로 , 이자체도 Delta Feedback 하여 Upgrade 후 공개예정입니다.

2. 기본적으로 **Variable Length packet**을 지향하고, **1-wire 통신**에도 데이터를 효율적으로 전달하기 위한 Codec 성격을 가지고 있습니다.
   - 차변 Delta / 잔차 Residual 을 이용한 실시간 데이터의 반영을 위해서 다양한 Parameter 값들이 필요하고, 
   - 다양한 파형에 맞게 Adaptive하게 parameter 를 세팅하는 구조이다 보니, 
  마치 다양한 성격을 가진 사람들에게 데이터를 보내도, 반응이 달라질수있는 오묘함이 존재합니다.

   - TFSD8 을 Evaluation 하면서 발견된 특징으로 예시되는 내용들을 서술하면 다음과 같습니다.
        
        ---
        ***“사람 성격” 과 비교되는 파라미터셋 예시***

        - 예민형(Hypervigilant): alpha≈0.2, theta_lsb≈0.75, T_silence=1, T_emit=1

                장점: 작은 변화도 즉시 감지, 급작 변화 민첩
                단점: 평탄구간에 이벤트가 잦아질 수 있음(α가 작아 정규화 덜함)

        - 균형형(Balanced): alpha≈0.7, theta_lsb≈1.0, T_silence=2, T_emit=2

                장/단점 균형, 대부분의 일반 데이터에 무난
        
        - 무던형(Stoic): alpha≈1.2, theta_lsb≈1.25, T_silence=3, T_emit=3

                장점: 평탄구간 과민반응 최소화(정규화 강함)
                단점: 미세 이벤트 감지가 늦을 수 있음
    
    - 구체적인 내용을 공개하기에는 알고리즘을 적용함에 있어서, 델타를 구하는데 방식의 문제로 인해서, 통제가 쉽지 않은 문제가 TFSD16 을 Evaluation 하면서, 발견되었습니다.
    이부분을 다시 검증하고, 좀 더 정리된 algorithm feasibility를 공개하는것으로 결정했습니다.

## TFSD16 에 대한 내용.

1. TFSD8 Kappa , Emit 방식을 기반으로, TFSD16 Baseline 값을 FP16 을 기준으로 비교하면서,

   - 16bits 전송시 Encoding Codec 의 Kernel 로, DPCM (Delta Pulse Code Modulation)  적용하여 테스트를 하였습니다.
   - 결과적으로 전혀 의도되지 않는 결과들이 발생하였고, 여러 파라메터를 Sweep 하여 테스트를 해보아도, 만족할 만한 내용들이 나오지 않았습니다.
   - 알고리즘 구현상에 문제가 있을수도 있다고 판단됩니다.
   - 64QAM 을 적용하여 테스트 하였으나, 의미가 없는 RMSE 와 파형의 왜곡 등이 발생하였습니다.
   - Exp Delta / Mantissa Delta 의 각각의 상위비트만 보내서 catch up 하게 하였으나,
     데이터 BPS (Bits Per Sample) 이 절감되지 않았습니다. 
   -  알고리즘 구현에서 Floating Point 기반의 Delta / Residual 을 Bit 기반의 packing 이 알고리즘의 의도와 맞지 않기 때문으로 판단했습니다.

2. 기본개념으로 돌아가서, 
   1. Encoder / Decoder 를 결국은 Hardware 최적화될수있도록 Simple 하게 알고리즘이 정리를 하였고, 우선은 Mantissa 의 packing 에 집중하여 알고리즘을 단순화 하였고,
   2. Floating Point 기반의 값들이 결국 Bit operation 되어야 하니, Bits 의 관점에서 Delta 를 찾는 방법을 시도하였고, 완전히 최적화는 되지 않았지만, Delta/Residual 을 bits 관점에서 packing 할 단서를 찾게 되었습니다.
   
## Lesson Learned :: 
    
1. Delta 와 Residual 의 오차의 잘못된 계산방식.

    단순히 차변 Delta / 잔차 (Residual) 을 계산함에, 원래의 입력 데이터를 처리하는   Encoder 기반에서 `Delta = FP_enc(t) - FP_enc(t-1)` 가 Bits가 늘어날수록 디코더가 Catch Up 해도, 계속 에러가 발생하는것을 확인했습니다.
    Decoder 가 최종 데이터를 해석하는것이므로, `Delta = FP_enc(t) - FP_dec(t-1)`  이것이 맞는방법이었습니다.

2. Closed Loop 방식 Encoder 구현.
    
    동영상압축 Codec 의 Encoder (예, MPEG4, HEVC codec) 의 경우, 효율적 압축율을 위해서 Encoding 은 매우 복잡도가 높고, Decoder 기능을 같이 가지고 있고,
    Decoding 은 상대적으로 쉽게 하는 비대칭 방식입니다.
    마찬가지로, TFSD16 도 잔차를 구하고, Decoder 가 catch up 이 용이하기 위해서는 Encoder 는 Decoder 의 `FP_dec(t-1)`  값에 근거해서 `Delta` 와 `SUM(Residual)` 을 구해야 하고,  Adaptive 하게 전송해야 합니다.
    
3. Floating Point Bitmask 이해.

    먼저 Floating Point 를 이해하기 쉽게 해놓은 사이트를 소개합니다.
  
   - [Arbitrary-float-converter](https://flop.evanau.dev/half-precision-converter)
   - [IEEE-754 Floating Point Converter](https://www.h-schmidt.net/FloatConverter/IEEE754.html)

    FP16 의 경우, 
   
   |sign|Exponent(5)|mantissa|
   |----|----------|-----------|
   |1bit|    5bit  |   10bit|
   

공개된 Audio 데이터 셋중, 

[Keith Ito's "The LJ Speech Dataset"](https://keithito.com/LJ-Speech-Dataset/) 

의 일부 Sample 을 실험용 데이터 셋으로 사용하였습니다.


###  테스트 데이터를 기반으로 데이터를 표로 보겠습니다.

\[LJ002-003mix.wav, 데이터 byte offset 332440\~332519 , 4bytes fp32 align]

```
t, decimal, sign, expbits, mantissa, dexp, dmantisa    , delta[(t)-(t-1)]
 83114, -0.039307, 1, 01011, 0000000100 , ----- , --------1-- , -0.000031 [0,00000, 0000000010]
 83115, -0.039337, 1, 01011, 0000000111 , ----- , ---------1-1 , -0.000031 [0,00000, 0000000011]
 83116, -0.039368, 1, 01011, 0000001010 , ----- , --------1-- , -0.000031 [0,00000, 0000000011]
 83117, -0.039398, 1, 01011, 0000001101 , ----- , ---------1-1 , -0.000031 [0,00000, 0000000011]
 83118, -0.039398, 1, 01011, 0000001101 , ----- , ---------- ,  0.000000 [0,00000, 0000000000]
 83119, -0.039429, 1, 01011, 0000010000 , ----- , --------1-- , -0.000031 [0,00000, 0000000011]
```

위와 같이 bitmask 가 바뀌므로, 이를 효율적으로 패킹(packing)해서 전송할수있으면 개선될수있다는것을 확인했습니다.

물론, Bitmask 기반의 operation 이 실제 decoder 로직도 매우 간단해지고, 향후, ASIC 친화적으로 알고리즘을 구현하기 쉽고, **C**언어로 구현했을시, 시스템 리소스도 소모 되지 않는 장점이 있습니다.

현재는, 부호가 변화할때, exponent 를 포함해서 KF (KeyFrame)을 다시 보내고, Mantissa 부분을 M5W1 (10bits mantissa 중, 상위5Bit 또는 하위5Bit를 packing) 하여 보내는것으로 Evaluation 하였습니다.

### Python Integer-Mask-based Reference Source code V0.3b

 - [README_TFSD16_V0_3b.md](tfsd16_v0_3b_intcodec/README_TFSD16_V0_3b.md)

## TODO and Idea for Improvements ::

1. Floating Point 의 sign (부호) 를 제외하고, E5 또는 E8 로 확장하여 Delta 구현.
    - 이유는 앞의 부호가 바뀔때, 처리복잡도 예상.
    - 정규화를 기존 [-1.0, +1.0] 에서 [0 , 2.0] 으로 하였을때, Exponent 의 Bitmask distance를 integer 기반으로 계산및 Packing 하기가 용이할것으로 예상됨.
2. C 언어로 구현하여, 
   - Bitstream packing 하여 보낼때, bits alignment 고려로인한 불필요한 padding bits 제거 가능. 
   - (현재, python 코드 특성상, 바이트단위로 되지 않을경우, alignment 에러 발생)
3. Kappa / Emit 방식을 적용하고, DPCM kernel 을 다시 검증 및 개선.
4. TFSD 코덱을 Audio / Video 데이터처리 특화 Quantization 으로 사용할경우, 기존 Pre/Post Processing Filter 복합구현.

  => 참고 : [references 디렉토리에, AI 연산시 audio_datapath.md][../references/audio_datapath.md]


## License
Apache License 2.0 © 2025 TrustFarm  
SPDX-License-Identifier: Apache-2.0
