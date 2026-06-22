# 05 - 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.7+
- pytest (测试)

### 1.2 安装依赖

```bash
pip install pytest
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
│   ├── vocabulary.py
│   ├── ngram.py
│   └── language_model.py
└── tests/
    ├── test_vocabulary.py
    ├── test_ngram.py
    └── test_language_model.py
```

## 2. 快速开始

### 2.1 运行示例

```python
from src.language_model import LanguageModel

# 准备语料
corpus = [
    "the cat sat on the mat",
    "the dog sat on the rug",
    "the cat ate the fish",
    "the dog chased the cat",
    "a cat and a dog played together",
    "the fish swam in the pond",
]

# 创建并训练模型
lm = LanguageModel(n=2, smoothing="add_k", k=1.0)
lm.train(corpus)

# 计算概率
log_prob = lm.probability("the cat sat on the mat")
print(f"对数概率: {log_prob:.4f}")

# 生成文本
text = lm.generate(seed="the", max_length=10, temperature=0.8)
print(f"生成文本: {text}")

# 计算困惑度
ppl = lm.perplexity(["the cat sat on the mat"])
print(f"困惑度: {ppl:.2f}")

# 全面评估
results = lm.evaluate(["the cat sat on the mat"])
print(f"评估结果: {results}")
```

### 2.2 运行测试

```bash
cd projects/language-model
python -m pytest tests/ -v
```

## 3. 开发流程

### 3.1 核心循环

```
语料 → N-gram 统计 → 概率模型 → 文本生成
```

### 3.2 实现步骤

1. **词汇表模块** (`vocabulary.py`)
   - 分词函数
   - 词汇表构建
   - 编码/解码

2. **N-gram 模型** (`ngram.py`)
   - 训练（N-gram 统计）
   - 概率计算
   - 困惑度评估
   - 文本生成

3. **语言模型** (`language_model.py`)
   - 整合词汇表和 N-gram
   - 统一接口
   - 全面评估

4. **测试** (`tests/`)
   - 单元测试
   - 集成测试

## 4. 使用指南

### 4.1 基本使用

```python
from src.language_model import LanguageModel

# 创建模型
lm = LanguageModel(n=3, smoothing="add_k", k=1.0)

# 训练
lm.train(corpus_texts)

# 使用
text = lm.generate(seed="hello", max_length=20)
ppl = lm.perplexity(test_texts)
```

### 4.2 参数调优

| 参数 | 建议值 | 说明 |
|------|--------|------|
| n | 2-3 | N-gram 阶数 |
| k | 0.1-1.0 | Add-k 平滑参数 |
| temperature | 0.5-1.5 | 生成温度 |

### 4.3 不同 N 值的效果

```python
# Unigram: 词独立，生成随机
lm1 = LanguageModel(n=1)

# Bigram: 考虑前一个词，生成较连贯
lm2 = LanguageModel(n=2)

# Trigram: 考虑前两个词，生成更连贯
lm3 = LanguageModel(n=3)
```

### 4.4 温度控制

```python
# 低温度 (0.1-0.5): 更确定性，选择高概率词
text = lm.generate(seed="the", temperature=0.2)

# 标准温度 (1.0): 标准采样
text = lm.generate(seed="the", temperature=1.0)

# 高温度 (1.5-2.0): 更随机，探索更多可能
text = lm.generate(seed="the", temperature=1.5)
```

## 5. API 参考

### 5.1 LanguageModel

```python
class LanguageModel:
    def __init__(self, n=3, smoothing="add_k", k=1.0, min_freq=1)
    def train(self, texts: List[str]) -> "LanguageModel"
    def probability(self, text: str) -> float
    def perplexity(self, texts: List[str]) -> float
    def generate(self, seed=None, max_length=50, temperature=1.0) -> str
    def generate_greedy(self, seed=None, max_length=50) -> str
    def top_words(self, n=10) -> List[Tuple[str, int]]
    def top_ngrams(self, n=10) -> List[Tuple[str, int]]
    def evaluate(self, test_texts: List[str]) -> Dict[str, float]
```

### 5.2 NGramModel

```python
class NGramModel:
    def __init__(self, n=3, smoothing="add_k", k=1.0)
    def train(self, corpus: List[List[str]]) -> "NGramModel"
    def probability(self, ngram: Tuple[str, ...]) -> float
    def sentence_probability(self, sentence: List[str]) -> float
    def perplexity(self, corpus: List[List[str]]) -> float
    def generate(self, max_length=50, temperature=1.0, seed=None) -> List[str]
    def generate_greedy(self, max_length=50, seed=None) -> List[str]
    def get_ngram_count(self, ngram: Tuple[str, ...]) -> int
    def get_context_count(self, context: Tuple[str, ...]) -> int
    def get_vocab(self) -> Set[str]
    def top_ngrams(self, n=10) -> List[Tuple[Tuple[str, ...], int]]
```

### 5.3 Vocabulary

```python
class Vocabulary:
    def __init__(self, min_freq=1)
    def build(self, corpus: List[List[str]]) -> "Vocabulary"
    def encode(self, tokens: List[str]) -> List[int]
    def decode(self, ids: List[int]) -> List[str]
    def get_id(self, token: str) -> int
    def get_token(self, idx: int) -> str
    def get_freq(self, token: str) -> int
    @staticmethod
    def tokenize(text: str) -> List[str]
    @property
    def size(self) -> int
```

## 6. 性能考虑

### 6.1 时间复杂度

| 操作 | 复杂度 |
|------|--------|
| 训练 | O(S * L) |
| 概率计算 | O(1) |
| 生成 | O(M * V) |
| 困惑度 | O(S * L) |

### 6.2 空间复杂度

- N-gram 计数：O(min(S * L, V^N))
- 词汇表：O(V)

### 6.3 优化建议

- 对于大语料，考虑使用更高效的数据结构
- 对于高阶 N-gram，考虑使用剪枝策略
- 对于生成任务，考虑使用 Beam Search

## 7. 扩展方向

### 7.1 更多平滑方法

- Good-Turing 平滑
- Kneser-Ney 平滑
- 回退 (Backoff) 方法

### 7.2 语言模型增强

- 字符级 N-gram
- 混合语言模型
- 神经网络语言模型

### 7.3 应用扩展

- 文本分类
- 拼写纠错
- 信息检索

## 8. 常见问题

### 8.1 困惑度很高怎么办?

- 增加训练数据
- 调整 N 值（通常 2-3 效果最好）
- 调整平滑参数 k
- 检查数据质量

### 8.2 生成的文本不连贯?

- 增加 N 值
- 降低温度
- 使用贪婪生成
- 增加训练数据

### 8.3 内存不够用?

- 减小 N 值
- 使用更高效的数据结构
- 考虑使用语言模型工具包（如 KenLM）
