# 05 - 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.7+
- NumPy (神经语言模型)
- pytest (测试)

### 1.2 安装依赖

```bash
pip install pytest numpy
```

### 1.3 项目结构

```
language-model/
├── README.md
├── LEARNING_NOTES.md
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── src/
│   ├── __init__.py
│   ├── vocabulary.py       # 词汇表
│   ├── ngram.py            # N-gram 模型
│   ├── language_model.py   # 语言模型接口
│   ├── smoothing.py        # 平滑技术
│   ├── neural_lm.py        # 神经语言模型
│   ├── evaluation.py       # 评估指标
│   └── applications.py     # 应用
└── tests/
    ├── test_vocabulary.py
    ├── test_ngram.py
    ├── test_language_model.py
    ├── test_smoothing.py
    ├── test_neural_lm.py
    ├── test_evaluation.py
    └── test_applications.py
```

## 2. 快速开始

### 2.1 N-gram 语言模型

```python
from src.language_model import LanguageModel

corpus = [
    "the cat sat on the mat",
    "the dog sat on the rug",
    "the cat ate the fish",
    "the dog chased the cat",
]

lm = LanguageModel(n=2, smoothing="add_k", k=1.0)
lm.train(corpus)

# 计算概率
log_prob = lm.probability("the cat sat on the mat")

# 生成文本
text = lm.generate(seed="the", max_length=10, temperature=0.8)

# 困惑度
ppl = lm.perplexity(["the cat sat on the mat"])
```

### 2.2 平滑技术

```python
from src.smoothing import LaplaceSmoothing, GoodTuringSmoothing, KneserNeySmoothing

# 拉普拉斯平滑
laplace = LaplaceSmoothing(k=1.0)
prob = laplace.probability(ngram_count=2, context_count=10, vocab_size=100)

# Good-Turing 平滑
gt = GoodTuringSmoothing(k_threshold=5)
gt.fit(ngram_counts)
prob = gt.probability(ngram_count=1, context_count=10, vocab_size=100)

# Kneser-Ney 平滑
kn = KneserNeySmoothing(discount=0.75)
kn.fit(ngram_counts, context_counts, vocab)
prob = kn.probability(("the", "cat"))
```

### 2.3 神经语言模型

```python
from src.neural_lm import FeedforwardNeuralLM, LSTMLanguageModel
import numpy as np

# FFNN 语言模型
ffnn = FeedforwardNeuralLM(vocab_size=100, embedding_dim=32, hidden_dim=64)
contexts = np.array([[0, 1], [2, 3]])
targets = np.array([5, 6])
loss = ffnn.train_step(contexts, targets)

# LSTM 语言模型
lstm = LSTMLanguageModel(vocab_size=100, embedding_dim=32, hidden_dim=64)
loss, h, c = lstm.train_step([0, 1, 2], [1, 2, 3])
```

### 2.4 评估指标

```python
from src.evaluation import EvaluationMetrics
import math

# 困惑度
ppl = EvaluationMetrics.perplexity([math.log(0.5), math.log(0.3)])

# 交叉熵
ce = EvaluationMetrics.cross_entropy([math.log(0.5)], base=2.0)

# BLEU
bleu = EvaluationMetrics.bleu_score(
    ["the", "cat", "sat"],
    [["the", "cat", "sat"]])

# 词错误率
wer = EvaluationMetrics.word_error_rate(
    ["hello", "there"], ["hello", "world"])
```

### 2.5 拼写纠错

```python
from src.applications import SpellingCorrector

corrector = SpellingCorrector(lm)
corrected = corrector.correct_text("the cat st on the mat")
suggestions = corrector.suggest("cat", n=5)
```

### 2.6 输入法

```python
from src.applications import InputMethod

ime = InputMethod(lm)
candidates = ime.complete_prefix("ca", context="the", n=5)
next_words = ime.predict_next_words("the cat", n=5)
```

### 2.7 运行测试

```bash
cd projects/language-model
python3 -m pytest tests/ -v
```

## 3. 开发流程

### 3.1 实现步骤

1. **词汇表模块** (`vocabulary.py`)
   - 分词函数、词汇表构建、编码/解码

2. **N-gram 模型** (`ngram.py`)
   - 训练（N-gram 统计）、概率计算、困惑度评估、文本生成

3. **语言模型** (`language_model.py`)
   - 整合词汇表和 N-gram，统一接口，全面评估

4. **平滑技术** (`smoothing.py`)
   - 拉普拉斯平滑、Good-Turing 平滑、Kneser-Ney 平滑

5. **神经语言模型** (`neural_lm.py`)
   - 前馈神经网络 LM、RNN LM、LSTM LM

6. **评估指标** (`evaluation.py`)
   - 困惑度、交叉熵、BPC、WER、BLEU

7. **应用** (`applications.py`)
   - 文本生成器、拼写纠错器、输入法

## 4. API 参考

### 4.1 LanguageModel

```python
class LanguageModel:
    def __init__(self, n=3, smoothing="add_k", k=1.0, min_freq=1)
    def train(self, texts: List[str]) -> "LanguageModel"
    def probability(self, text: str) -> float
    def perplexity(self, texts: List[str]) -> float
    def generate(self, seed=None, max_length=50, temperature=1.0) -> str
    def generate_greedy(self, seed=None, max_length=50) -> str
    def evaluate(self, test_texts: List[str]) -> Dict[str, float]
```

### 4.2 Smoothing

```python
class LaplaceSmoothing:
    def __init__(self, k: float = 1.0)
    def probability(self, ngram_count, context_count, vocab_size) -> float

class GoodTuringSmoothing:
    def __init__(self, k_threshold: int = 5)
    def fit(self, ngram_counts: Dict) -> None
    def probability(self, ngram_count, context_count, vocab_size) -> float

class KneserNeySmoothing:
    def __init__(self, discount: float = 0.75)
    def fit(self, ngram_counts, context_counts, vocab) -> None
    def probability(self, ngram: Tuple) -> float
```

### 4.3 NeuralLM

```python
class FeedforwardNeuralLM:
    def __init__(self, vocab_size, embedding_dim=32, hidden_dim=64, context_size=2, learning_rate=0.01)
    def train_step(self, context_ids, target_ids) -> float
    def predict_proba(self, context_ids) -> np.ndarray
    def perplexity(self, test_contexts, test_targets) -> float

class LSTMLanguageModel:
    def __init__(self, vocab_size, embedding_dim=32, hidden_dim=64, learning_rate=0.001)
    def train_step(self, word_ids, target_ids, h_prev=None, c_prev=None) -> Tuple[float, ndarray, ndarray]
    def predict_proba(self, word_ids, h_prev=None, c_prev=None) -> Tuple[ndarray, ndarray, ndarray]
    def perplexity(self, test_sequences) -> float
```

### 4.4 EvaluationMetrics

```python
class EvaluationMetrics:
    @staticmethod perplexity(log_probs: List[float]) -> float
    @staticmethod cross_entropy(log_probs: List[float], base=2.0) -> float
    @staticmethod bits_per_character(log_probs: List[float]) -> float
    @staticmethod word_error_rate(predicted: List[str], reference: List[str]) -> float
    @staticmethod bleu_score(predicted: List[str], references: List[List[str]], max_n=4) -> float
    @staticmethod compare_models(results: Dict[str, Dict[str, float]]) -> Dict[str, str]
```

### 4.5 Applications

```python
class TextGenerator:
    def __init__(self, lm)
    def generate(self, seed=None, max_length=50, temperature=1.0) -> str
    def generate_diverse(self, seed=None, num_samples=5, ...) -> List[str]

class SpellingCorrector:
    def __init__(self, lm, vocab=None)
    def correct_word(self, word, context=None) -> str
    def correct_text(self, text) -> str
    def suggest(self, word, n=5) -> List[str]

class InputMethod:
    def __init__(self, lm, vocab=None)
    def complete_prefix(self, prefix, context=None, n=10) -> List[Tuple[str, float]]
    def predict_next_words(self, context, n=10) -> List[Tuple[str, float]]
```

## 5. 参数调优

| 参数 | 建议值 | 说明 |
|------|--------|------|
| n | 2-3 | N-gram 阶数 |
| k | 0.1-1.0 | Add-k 平滑参数 |
| discount | 0.5-0.9 | Kneser-Ney 折扣 |
| temperature | 0.5-1.5 | 生成温度 |
| embedding_dim | 32-128 | 词嵌入维度 |
| hidden_dim | 64-256 | 隐藏层维度 |
| learning_rate | 0.001-0.01 | 学习率 |

## 6. 扩展方向

- 字符级 N-gram 和语言模型
- 混合语言模型 (Interpolation)
- Beam Search 生成
- 更大规模语料训练
- Transformer 语言模型
