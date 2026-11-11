# gpt2-numpy

GPT-2 small(124M)의 순전파를 NumPy 행렬 연산만으로 구현하고, Hugging Face와 logits를 비교한 뒤 토크나이저, 어텐션, 샘플링, 구성요소 제거, 파인튜닝 손실을 실험한 코드입니다. 실험 결과와 해석은 블로그 글에 정리했습니다.

- 블로그: [NumPy로 GPT-2 구현하며 LLM 동작 원리 이해하기](https://grace0409.github.io/posts/numpy-gpt2-from-scratch/)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Grace0409/grace0409.github.io/blob/main/gpt2-numpy/gpt2_numpy.ipynb)

## 구성

| 경로 | 내용 |
|---|---|
| `src/gpt2.py` | GPT-2 순전파(NumPy), 부품을 하나씩 끄는 `Ablation` 옵션 |
| `src/bpe.py` | GPT-2 BPE 토크나이저와 BPE 학습 |
| `src/sampling.py` | greedy, temperature, top-k, top-p |
| `src/figs.py` | 그림 6개를 그리는 함수 |
| `experiments/e1_tokenizer.py` | 한국어/영어 토큰 수 비교, BPE를 tiktoken과 대조 |
| `experiments/e2_verify_hf.py` | Hugging Face와 logits 비교(float32, float64) |
| `experiments/e3_attention.py` | 임베딩 분석과 어텐션 맵 |
| `experiments/e4_sampling.py` | 샘플링 전략 비교 |
| `experiments/e5_ablation.py` | 학습된 GPT-2에서 부품 끄기, √d_k 난수 실험 |
| `experiments/e6_train_ablation.py` | 부품을 뺀 소형 GPT를 처음부터 학습(PyTorch) |
| `experiments/e7_losses.py` | 사전학습, SFT, RLHF(PPO), DPO 손실과 파인튜닝(PyTorch) |
| `experiments/make_figures.py` | 저장된 결과로 그림 6개 생성 |
| `gpt2_figures.ipynb` | 저장된 결과로 그림 6개만 다시 그리는 Colab 노트북(1분 안팎) |
| `results/` | 글에 쓴 실험 결과(JSON) |
| `figures/` | 글에 쓴 그림 |

## 실행

Colab에서는 위의 Open In Colab 배지를 눌러 노트북을 위에서부터 실행하면 됩니다.

그림만 다시 그리려면 [gpt2_figures.ipynb](https://colab.research.google.com/github/Grace0409/grace0409.github.io/blob/main/gpt2-numpy/gpt2_figures.ipynb)를 열어 실행하면 됩니다.

로컬에서는 다음 순서로 실행합니다.

```bash
pip install -r requirements.txt
python experiments/download_data.py
python experiments/e1_tokenizer.py
python experiments/e2_verify_hf.py
python experiments/e3_attention.py
python experiments/e4_sampling.py
python experiments/e5_ablation.py
python experiments/e6_train_ablation.py --summary-only
python experiments/e7_losses.py
python experiments/make_figures.py
```

## 알아 둘 점

- GPT-2 순전파는 NumPy만 씁니다. 기울기가 필요한 `e6`, `e7`의 학습 부분만 PyTorch를 씁니다.
- `e6`의 전체 실험은 학습 36회(시드 3개)이고, CPU 12코어에서 16시간 가까이 걸렸습니다. 그래서 `results/e6_runs/`에 저장된 결과를 넣어 두었고, `--summary-only`는 이 결과를 읽어 요약합니다. 학습 코드가 도는지 보려면 `--quick`(4가지, 300스텝)을 실행하면 됩니다. 저장된 결과를 지우고 36회를 처음부터 다시 돌리려면 GPU 환경에서 `python experiments/e6_train_ablation.py --rerun`을 실행합니다.
- 가중치와 데이터는 `download_data.py`가 `weights/`에 내려받고, `model.safetensors`는 공개된 해시와 대조합니다.
- 그림의 글꼴은 NanumGothic입니다. Colab에서는 `fonts-nanum`을 설치합니다.
