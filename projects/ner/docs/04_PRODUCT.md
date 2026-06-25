# 04 - 产品文档

## 产品概述

NER 序列标注系统是一个完整的命名实体识别解决方案，提供从规则方法到深度学习的多种技术方案。

## 功能特性

### 1. 多种 NER 方法

| 方法 | 适用场景 | 速度 | 准确度 |
|------|---------|------|--------|
| 正则匹配 | 格式化实体 | 最快 | 高(限) |
| 词典匹配 | 已知实体 | 快 | 高(限) |
| HMM | 小数据集 | 快 | 中 |
| CRF | 中等数据 | 中 | 较高 |
| BiLSTM | 大数据集 | 较慢 | 较高 |
| BiLSTM-CRF | 大数据集 | 较慢 | 最高 |

### 2. 标注方案

支持 BIO 和 BIOES 两种标注方案，可相互转换。

### 3. 评估指标

提供完整的评估体系:
- Accuracy: token 级别准确率
- Precision: 实体级别精确率
- Recall: 实体级别召回率
- F1: 精确率和召回率的调和平均

### 4. 实体类型

默认支持三种实体类型:
- PER (人名): John, 张三, Barack Obama
- LOC (地名): New York, 北京, Paris
- ORG (机构名): Google, 清华大学, United Nations

## 使用示例

### 基于规则的 NER

```python
from src.rules import RegexNER, DictNER

# 正则匹配 - 识别电话号码
regex_ner = RegexNER()
entities = regex_ner.recognize("请拨打 13812345678 联系我")
print(entities)
# [('PHONE', '13812345678', 4, 15)]

# 词典匹配 - 识别地名和机构名
dict_ner = DictNER()
dict_ner.add_entity("北京", "LOC")
dict_ner.add_entity("清华大学", "ORG")
dict_ner.add_entity("北京大学", "ORG")
entities = dict_ner.recognize("我去了北京市清华大学")
print(entities)
# [('LOC', '北京', 3, 5), ('ORG', '清华大学', 5, 9)]
```

### HMM NER

```python
from src.hmm import HMM
from src.dataset import create_sample_data

# 训练
sentences, tags = create_sample_data()
hmm = HMM(smooth=1e-6)
hmm.fit(sentences, tags)

# 预测
predicted = hmm.predict(["John", "works", "at", "Google"])
print(predicted)
# ['B-PER', 'O', 'O', 'B-ORG']
```

### BiLSTM-CRF NER

```python
import torch
from src.model import BiLSTM_CRF
from src.dataset import Vocabulary, TagVocabulary, create_sample_data
from src.trainer import Trainer
from torch.utils.data import DataLoader

# 准备数据
sentences, tags = create_sample_data()
vocab = Vocabulary()
vocab.build(sentences)
tag_vocab = TagVocabulary()
tag_vocab.build(tags)

# 创建数据集
dataset = NERDataset(sentences, tags, vocab, tag_vocab, max_len=10)
loader = DataLoader(dataset, batch_size=4, shuffle=True)

# 创建模型
model = BiLSTM_CRF(
    vocab_size=len(vocab),
    num_tags=len(tag_vocab),
    embedding_dim=64,
    hidden_dim=128
)

# 训练
trainer = Trainer(model, tag_vocab=tag_vocab, learning_rate=0.005)
# ... 训练过程
```

### 标注方案转换

```python
from src.schemes import bio_to_bioes, bioes_to_bio

# BIO -> BIOES
bio_tags = ['B-PER', 'I-PER', 'O', 'B-LOC', 'I-LOC']
bioes_tags = bio_to_bioes(bio_tags)
print(bioes_tags)
# ['B-PER', 'E-PER', 'O', 'B-LOC', 'E-LOC']

# BIOES -> BIO
bio_tags_back = bioes_to_bio(bioes_tags)
print(bio_tags_back)
# ['B-PER', 'I-PER', 'O', 'B-LOC', 'I-LOC']
```

## 性能指标

### CoNLL-2003 数据集基准

| 模型 | F1 |
|------|-----|
| BiLSTM | 88.17 |
| BiLSTM-CRF | 90.10 |
| BERT-CRF | 93.50 |

### 模型大小

| 配置 | 参数量 | 训练速度 |
|------|--------|---------|
| emb=64, hidden=128 | ~200K | 100 sent/s |
| emb=128, hidden=256 | ~800K | 50 sent/s |
| emb=256, hidden=512 | ~3.2M | 20 sent/s |
