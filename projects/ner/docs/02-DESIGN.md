# 02 - 设计文档

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    NER System                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Dataset  │  │   Model  │  │ Trainer  │             │
│  │          │  │          │  │          │             │
│  │ - Vocab  │  │ - Embed  │  │ - Train  │             │
│  │ - Data   │  │ - BiLSTM │  │ - Eval   │             │
│  │ - Loader │  │ - CRF    │  │ - Predict│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│       │             │             │                     │
│       └─────────────┴─────────────┘                     │
│                     │                                   │
│              ┌──────┴──────┐                            │
│              │  Evaluator  │                            │
│              │  - P/R/F1   │                            │
│              │  - Entities │                            │
│              └─────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. CRF 模块 (`crf.py`)

#### 类设计

```python
class CRF(nn.Module):
    """条件随机场层"""

    def __init__(self, num_tags, batch_first=True):
        self.transitions        # 转移矩阵 (num_tags, num_tags)
        self.start_transitions  # 起始转移 (num_tags,)
        self.end_transitions    # 结束转移 (num_tags,)

    def forward(self, emissions, tags, mask):
        """计算负对数似然损失"""

    def decode(self, emissions, mask):
        """维特比解码"""
```

#### 内部方法

```
_compute_score()         - 计算真实路径分数
_compute_log_partition() - 前向算法计算配分函数
_viterbi_decode()        - 维特比解码
```

#### 数据流

```
输入:
  emissions: (batch, seq_len, num_tags)  - 发射分数
  tags:      (batch, seq_len)            - 真实标签
  mask:      (batch, seq_len)            - 掩码

输出:
  loss: 标量 (训练模式)
  best_tags: List[List[int]] (解码模式)
```

### 2. BiLSTM-CRF 模块 (`model.py`)

#### 模型架构

```python
class BiLSTM_CRF(nn.Module):
    """BiLSTM-CRF 序列标注模型"""

    def __init__(self, vocab_size, num_tags, embedding_dim, hidden_dim, ...):
        self.embedding   # 词嵌入层
        self.lstm        # 双向 LSTM
        self.hidden2tag  # 线性映射
        self.crf         # CRF 层
```

#### 维度变化

```
输入: (batch, seq_len)
  ↓ embedding
(batch, seq_len, embedding_dim)
  ↓ BiLSTM
(batch, seq_len, hidden_dim * 2)
  ↓ Linear
(batch, seq_len, num_tags)  ← 发射分数
  ↓ CRF
(batch, seq_len)            ← 标签序列
```

### 3. 数据模块 (`dataset.py`)

#### 类设计

```python
class Vocabulary:
    """词表管理"""
    token2idx: Dict[str, int]
    idx2token: Dict[int, str]

class TagVocabulary:
    """标签表管理"""
    tag2idx: Dict[str, int]
    idx2tag: Dict[int, str]

class NERDataset(Dataset):
    """NER 数据集"""
    sentences: List[List[str]]
    tags: List[List[str]]
```

#### 数据格式

CoNLL 格式:
```
John B-PER
lives O
in O
New B-LOC
York I-LOC

(空行分隔句子)
```

### 4. 评估器模块 (`evaluator.py`)

#### 评估流程

```
标签序列 → 提取实体 → 比较 → 计算 P/R/F1
```

#### 实体提取

```python
def _extract_entities(tag_seq):
    """
    ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
    → [("PER", 0, 1), ("LOC", 3, 4)]
    """
```

### 5. 训练器模块 (`trainer.py`)

#### 训练流程

```
for epoch in epochs:
    for batch in train_loader:
        loss = model(batch)
        loss.backward()
        optimizer.step()

    val_results = evaluate(val_loader)
    if val_f1 > best_f1:
        save_best_model()
    elif patience exceeded:
        early_stop()
```

## 数据流设计

### 训练流程

```
原始文本
    ↓
[数据处理]
  - 构建词表
  - 转换为索引
  - 填充/截断
    ↓
[模型前向]
  - Embedding
  - BiLSTM
  - Linear → emissions
  - CRF → loss
    ↓
[反向传播]
  - 计算梯度
  - 更新参数
    ↓
[评估]
  - 解码预测
  - 计算 P/R/F1
```

### 预测流程

```
输入文本
    ↓
[预处理]
  - 分词
  - 转换为索引
  - 填充
    ↓
[模型推理]
  - Embedding
  - BiLSTM
  - Linear → emissions
  - CRF → best_tags
    ↓
[后处理]
  - 转换为标签
  - 提取实体
    ↓
输出结果
```

## 关键设计决策

### 1. CRF 的转移矩阵

选择 column-major 方式:
```python
transitions[i][j] = score(j → i)  # 从 j 转移到 i 的分数
```

原因: 便于矩阵运算，transitions[tags[i], tags[i-1]] 直接获取转移分数。

### 2. 批量处理

使用 batch_first=True:
```python
emissions: (batch, seq_len, num_tags)
tags:      (batch, seq_len)
```

原因: 与 PyTorch 默认一致，便于数据处理。

### 3. 掩码处理

使用 float 掩码而非 bool 掩码:
```python
mask = torch.tensor([1, 1, 1, 0, 0])  # 而非 [True, True, True, False, False]
```

原因: 可以直接用于乘法，mask * score。

### 4. 梯度裁剪

使用 max_norm=5.0:
```python
nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
```

原因: 防止梯度爆炸，稳定训练。

## 扩展设计

### 支持字符级嵌入

```python
class CharCNN(nn.Module):
    """字符级 CNN"""
    # 提取字符级特征
    # 与词级嵌入拼接
```

### 支持预训练模型

```python
class BertCRF(nn.Module):
    """BERT-CRF 模型"""
    # 使用 BERT 替换 BiLSTM
    # 保留 CRF 层
```

### 支持多任务学习

```python
class MultiTaskModel(nn.Module):
    """多任务模型"""
    # 共享 BiLSTM
    # 多个 CRF 头 (NER, POS, ...)
```
