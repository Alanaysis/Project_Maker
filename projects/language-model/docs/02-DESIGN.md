# 02 - 设计文档

## 1. 架构设计

### 1.1 整体架构

```
                    +----------------------+
                    |   LanguageModel      |
                    +----------------------+
                           |
            +--------------+--------------+
            |                             |
    +-------v-------+           +--------v--------+
    |  Vocabulary   |           |   NGramModel    |
    | (vocabulary.py)|           |   (ngram.py)    |
    +----------------+           +-----------------+
    | - tokenize()   |           | - train()       |
    | - build()      |           | - probability() |
    | - encode()     |           | - perplexity()  |
    | - decode()     |           | - generate()    |
    +----------------+           +-----------------+
```

### 1.2 数据流

```
原始文本列表
       │
       v
+------------------+
| Vocabulary       |
| .tokenize()      |  文本 → 词列表
| .build()         |  构建词汇表
+--------+---------+
         │
         v
+------------------+
| NGramModel       |
| .train()         |  统计 N-gram 计数
+--------+---------+
         │
         v
+------------------+
| 生成/评估        |
| .generate()      |  文本生成
| .perplexity()    |  困惑度评估
+------------------+
```

## 2. 模块设计

### 2.1 词汇表模块 (vocabulary.py)

**职责**：分词、词汇表管理、ID 映射

**接口**：
```python
class Vocabulary:
    def __init__(self, min_freq: int = 1)
    def build(self, corpus: List[List[str]]) -> "Vocabulary"
    def encode(self, tokens: List[str]) -> List[int]
    def decode(self, ids: List[int]) -> List[str]
    def get_id(self, token: str) -> int
    def get_token(self, idx: int) -> str
    def get_freq(self, token: str) -> int
    @staticmethod
    def tokenize(text: str) -> List[str]

    # 属性
    @property
    def size(self) -> int
    @property
    def pad_id(self) -> int
    @property
    def unk_id(self) -> int
    @property
    def bos_id(self) -> int
    @property
    def eos_id(self) -> int
```

**特殊标记**：
| 标记 | ID | 用途 |
|------|----|------|
| `<PAD>` | 0 | 填充 |
| `<UNK>` | 1 | 未知词 |
| `<BOS>` | 2 | 句子开始 |
| `<EOS>` | 3 | 句子结束 |

### 2.2 N-gram 模块 (ngram.py)

**职责**：N-gram 统计、概率计算、文本生成

**接口**：
```python
class NGramModel:
    def __init__(self, n: int = 3, smoothing: str = "add_k", k: float = 1.0)
    def train(self, corpus: List[List[str]]) -> "NGramModel"
    def probability(self, ngram: Tuple[str, ...]) -> float
    def sentence_probability(self, sentence: List[str]) -> float
    def perplexity(self, corpus: List[List[str]]) -> float
    def generate(self, max_length: int, temperature: float, seed: str) -> List[str]
    def generate_greedy(self, max_length: int, seed: str) -> List[str]
    def get_ngram_count(self, ngram: Tuple[str, ...]) -> int
    def get_context_count(self, context: Tuple[str, ...]) -> int
    def get_vocab(self) -> Set[str]
    def top_ngrams(self, n: int) -> List[Tuple[Tuple[str, ...], int]]
```

### 2.3 语言模型模块 (language_model.py)

**职责**：整合词汇表和 N-gram 模型，提供统一接口

**接口**：
```python
class LanguageModel:
    def __init__(self, n: int, smoothing: str, k: float, min_freq: int)
    def train(self, texts: List[str]) -> "LanguageModel"
    def probability(self, text: str) -> float
    def perplexity(self, texts: List[str]) -> float
    def generate(self, seed: str, max_length: int, temperature: float) -> str
    def generate_greedy(self, seed: str, max_length: int) -> str
    def top_words(self, n: int) -> List[Tuple[str, int]]
    def top_ngrams(self, n: int) -> List[Tuple[str, int]]
    def evaluate(self, test_texts: List[str]) -> Dict[str, float]
```

## 3. 数据结构设计

### 3.1 N-gram 计数存储

使用 `Counter` 存储 N-gram 计数：

```python
# N-gram 计数
_ngram_counts: Dict[Tuple[str, ...], int] = Counter()
# 示例: {("the", "cat"): 2, ("cat", "sat"): 1}

# 上下文计数（用于条件概率）
_context_counts: Dict[Tuple[str, ...], int] = Counter()
# 示例: {("the",): 5, ("cat",): 2}
```

**设计决策**：
- 使用元组作为键，支持变长 N-gram
- 使用 Counter，简化计数操作
- 同时存储上下文计数，加速概率计算

### 3.2 词汇表存储

```python
_token2id: Dict[str, int]  # 词 → ID
_id2token: Dict[int, str]  # ID → 词
_token_freq: Counter        # 词频
```

**设计决策**：
- 双向映射，支持快速查找
- 特殊标记占前 4 个 ID

### 3.3 输入输出格式

| 操作 | 输入 | 输出 |
|------|------|------|
| train | List[str] (原始文本) | self |
| probability | str (文本) | float (对数概率) |
| perplexity | List[str] (文本列表) | float (困惑度) |
| generate | seed: str | str (生成文本) |
| evaluate | List[str] (测试文本) | Dict[str, float] |

## 4. 算法设计

### 4.1 训练算法

```
输入: 语料库 corpus (词列表的列表)

1. 初始化计数表
2. 对每个句子:
   a. 添加 (N-1) 个 <BOS> 和 1 个 <EOS>
   b. 滑动窗口提取 N-gram
   c. 更新 _ngram_counts 和 _context_counts
3. 返回模型
```

### 4.2 概率计算算法

```
输入: N-gram (w1, ..., wN)
输出: 条件概率 P(wN | w1, ..., w_{N-1})

1. 提取 context = (w1, ..., w_{N-1})
2. 获取 ngram_count = _ngram_counts[ngram]
3. 获取 context_count = _context_counts[context]
4. 应用平滑:
   - add_k: (ngram_count + k) / (context_count + k * V)
   - none: ngram_count / context_count
5. 返回概率
```

### 4.3 文本生成算法

```
输入: 种子词 seed, 最大长度 max_length, 温度 temperature
输出: 生成的词列表

1. 初始化上下文: [<BOS>, ..., seed]
2. 重复直到达到 max_length 或生成 <EOS>:
   a. 获取当前上下文的下一个词概率分布
   b. 应用温度调整
   c. 采样下一个词
   d. 更新上下文
3. 返回生成的词列表
```

### 4.4 温度采样算法

```
输入: 概率分布 probs, 温度 temperature
输出: 采样结果

1. 转换到对数空间: log_p = log(p) / temperature
2. 转换回概率空间: p' = exp(log_p)
3. 归一化
4. 累积分布采样
```

## 5. 错误处理

### 5.1 输入验证

```python
# N 值验证
if n < 1:
    raise ValueError("n 必须为正整数")

# 温度验证
if temperature <= 0:
    raise ValueError("temperature 必须为正数")

# 训练状态检查
if not self._trained:
    raise RuntimeError("模型尚未训练，请先调用 train() 方法")
```

### 5.2 零概率处理

- 平滑技术避免零概率
- 对数空间计算避免下溢
- 困惑度返回 `float('inf')` 表示零概率

## 6. 性能设计

### 6.1 时间复杂度

| 操作 | 复杂度 |
|------|--------|
| 训练 | O(S * L)，S=句子数，L=平均长度 |
| 概率计算 | O(1) |
| 生成 | O(M * V)，M=最大长度，V=词汇表大小 |
| 困惑度 | O(S * L) |

### 6.2 空间复杂度

- N-gram 计数：O(min(S * L, V^N))
- 词汇表：O(V)

### 6.3 优化策略

- 使用字典存储稀疏计数（而非数组）
- 概率计算使用预存的上下文计数
- 生成时只遍历词汇表中出现过的词

## 7. 测试设计

### 7.1 单元测试

- 词汇表：构建、编码、解码、分词
- N-gram：训练、计数、概率、生成
- 语言模型：完整流程

### 7.2 集成测试

- 完整训练-评估-生成流程
- 不同 N 值和参数组合
- 模型质量验证
