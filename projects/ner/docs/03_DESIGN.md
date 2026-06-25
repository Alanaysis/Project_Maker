# 03 - 设计文档

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                       NER System                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │  Rule-based   │  │  Statistical  │  │  Deep Learning│  │
│  │               │  │               │  │               │  │
│  │ - RegexNER    │  │ - HMM         │  │ - BiLSTM      │  │
│  │ - DictNER     │  │ - CRF         │  │ - BiLSTM-CRF  │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │   Schemes     │  │    Dataset    │  │   Evaluator   │  │
│  │               │  │               │  │               │  │
│  │ - BIOEncoder  │  │ - Vocabulary  │  │ - Accuracy    │  │
│  │ - BIOESEncoder│  │ - TagVocab    │  │ - Precision   │  │
│  │               │  │ - NERDataset  │  │ - Recall / F1 │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. 标注方案模块 (`schemes.py`)

```python
class BIOEncoder:
    @staticmethod
    def encode(entities, seq_len) -> List[str]
    @staticmethod
    def decode(tags) -> List[Tuple[str, int, int]]
    @staticmethod
    def get_tag_set(entity_types) -> List[str]

class BIOESEncoder:
    @staticmethod
    def encode(entities, seq_len) -> List[str]
    @staticmethod
    def decode(tags) -> List[Tuple[str, int, int]]
    @staticmethod
    def get_tag_set(entity_types) -> List[str]

def bio_to_bioes(bio_tags) -> List[str]
def bioes_to_bio(bioes_tags) -> List[str]
```

### 2. 基于规则模块 (`rules/`)

#### RegexNER

```python
class RegexNER:
    def __init__(self, patterns=None)
    def add_pattern(entity_type, pattern)
    def recognize(text) -> List[Tuple[str, str, int, int]]
    def recognize_tokens(tokens) -> List[str]
    def get_supported_types() -> List[str]
```

#### DictNER

```python
class TrieNode:
    children: Dict[str, TrieNode]
    is_end: bool
    entity_type: Optional[str]

class DictNER:
    def add_entity(entity, entity_type)
    def add_entities(entities: Dict[str, str])
    def add_entity_list(entity_list, entity_type)
    def load_from_file(filepath, entity_type)
    def recognize(text, method="forward") -> List[Tuple]
    def recognize_tokens(tokens, method) -> List[str]
```

### 3. HMM 模块 (`hmm.py`)

```python
class HMM:
    def __init__(self, smooth=1e-6)
    def fit(sentences, tags)
    def predict(sentence) -> List[str]
    def predict_batch(sentences) -> List[List[str]]
    def get_transition_matrix() -> np.ndarray
    def get_emission_matrix() -> np.ndarray
    def get_initial_probs() -> np.ndarray
```

### 4. CRF 模块 (`standalone_crf.py`)

```python
class FeatureExtractor:
    def extract(sentence, position, tag) -> List[str]
    def build(sentences, tags)
    def get_indices(sentence, position, tag) -> List[int]

class StandaloneCRF:
    def __init__(self, learning_rate, max_iterations, regularization, tolerance)
    def fit(sentences, tags)
    def predict(sentence) -> List[str]
    def predict_batch(sentences) -> List[List[str]]
```

### 5. BiLSTM 模块 (`bilstm.py`)

```python
class BiLSTM(nn.Module):
    def __init__(self, vocab_size, num_tags, embedding_dim, hidden_dim, ...)
    def forward(tokens, mask) -> emissions
    def decode(tokens, mask) -> List[List[int]]

class BiLSTMWithSoftmax(nn.Module):
    def __init__(self, vocab_size, num_tags, ...)
    def forward(tokens, tags, mask) -> loss
    def decode(tokens, mask) -> List[List[int]]
```

### 6. CRF 层模块 (`crf.py`)

```python
class CRF(nn.Module):
    def __init__(self, num_tags, batch_first=True)
    def forward(emissions, tags, mask) -> loss
    def decode(emissions, mask) -> List[List[int]]
    # 内部方法
    def _compute_score(emissions, tags, mask)
    def _compute_log_partition(emissions, mask)
    def _viterbi_decode(emissions, mask)
```

### 7. BiLSTM-CRF 模块 (`model.py`)

```python
class BiLSTM_CRF(nn.Module):
    def __init__(self, vocab_size, num_tags, embedding_dim, hidden_dim, ...)
    def forward(tokens, tags, mask) -> loss
    def decode(tokens, mask) -> List[List[int]]
    def _get_emissions(tokens, mask) -> emissions
```

### 8. 评估器模块 (`evaluator.py`)

```python
class Evaluator:
    def evaluate(true_tags, pred_tags) -> Dict
    def evaluate_from_indices(true_indices, pred_indices, masks) -> Dict
    def print_results(results)
    # 内部方法
    def _compute_accuracy(true_tags, pred_tags) -> float
    def _extract_entities(tag_sequences) -> List[List[Tuple]]
    def _count_matches(true_entities, pred_entities, entity_type) -> Tuple
```

## 数据流设计

### 训练流程

```
原始文本
    |
[数据处理]
  - 构建词表
  - 转换为索引
  - 填充/截断
    |
[模型前向]
  - Embedding
  - BiLSTM
  - Linear -> emissions
  - CRF -> loss
    |
[反向传播]
  - 计算梯度
  - 梯度裁剪
  - 更新参数
    |
[评估]
  - 解码预测
  - 计算 Accuracy/P/R/F1
```

### 预测流程

```
输入文本
    |
[预处理]
  - 分词
  - 转换为索引
  - 填充
    |
[模型推理]
  - Embedding
  - BiLSTM
  - Linear -> emissions
  - CRF -> best_tags
    |
[后处理]
  - 转换为标签
  - 提取实体
    |
输出结果
```

## 关键设计决策

### 1. CRF 的转移矩阵

选择 column-major 方式:
```python
transitions[i][j] = score(j -> i)  # 从 j 转移到 i 的分数
```

原因: 便于矩阵运算，transitions[tags[i], tags[i-1]] 直接获取转移分数。

### 2. 批量处理

使用 batch_first=True:
```python
emissions: (batch, seq_len, num_tags)
tags:      (batch, seq_len)
```

### 3. 掩码处理

使用 float 掩码而非 bool 掩码:
```python
mask = torch.tensor([1, 1, 1, 0, 0])  # 可以直接用于乘法
```

### 4. 梯度裁剪

使用 max_norm=5.0:
```python
nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
```
