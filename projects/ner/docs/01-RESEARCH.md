# 01 - 调研文档

## 序列标注概述

序列标注 (Sequence Labeling) 是 NLP 中的基础任务，目标是为输入序列中的每个 token 分配一个标签。

### 应用场景

| 任务 | 输入 | 输出 | 应用 |
|------|------|------|------|
| NER | 文本 | 实体标签 | 信息抽取 |
| POS Tagging | 文本 | 词性标签 | 句法分析 |
| Chunking | 文本 | 短语标签 | 语义分析 |
| Slot Filling | 语音/文本 | 槽位标签 | 对话系统 |

### 标注方案

#### BIO 标注
```
B-XXX: 实体开始 (Begin)
I-XXX: 实体内部 (Inside)
O:     非实体 (Outside)

优点: 简单直观
缺点: 无法区分相邻同类实体
```

#### BIOES 标注
```
B-XXX: 实体开始 (Begin)
I-XXX: 实体内部 (Inside)
O:     非实体 (Outside)
E-XXX: 实体结束 (End)
S-XXX: 单独实体 (Single)

优点: 信息更丰富
缺点: 标签数量更多
```

## CRF 算法调研

### 概率图模型

CRF 是一种判别式概率图模型，用于建模条件概率 P(Y|X)。

#### 与生成式模型的对比

| 特性 | 生成式 (HMM) | 判别式 (CRF) |
|------|-------------|-------------|
| 建模目标 | P(X, Y) | P(Y\|X) |
| 需要建模 P(X) | 是 | 否 |
| 特征工程 | 受限于生成过程 | 灵活 |
| 典型应用 | 语音识别 | NER, POS |

### 线性链 CRF

线性链 CRF 是最常见的 CRF 变体，适用于序列标注任务。

#### 定义

给定观测序列 X = (x_1, ..., x_n) 和标签序列 Y = (y_1, ..., y_n):

```
P(Y|X) = exp(Σ_i Σ_k λ_k f_k(y_{i-1}, y_i, X, i)) / Z(X)

其中:
- f_k: 特征函数
- λ_k: 特征权重
- Z(X): 配分函数
```

#### 特征函数

在深度学习时代，特征函数被神经网络替代:

```
传统 CRF: 手工设计特征函数
深度学习 CRF: 神经网络自动学习特征
```

### 前向算法

计算配分函数 Z(x) 的动态规划算法:

```
初始化:
  α_0(j) = start_transitions[j] + emission[0][j]

递推:
  α_i(j) = log Σ_k exp(α_{i-1}(k) + transition[k][j] + emission[i][j])

终止:
  Z(x) = log Σ_j exp(α_n(j) + end_transitions[j])
```

### 维特比算法

找到最优标签序列的动态规划算法:

```
初始化:
  δ_0(j) = start_transitions[j] + emission[0][j]
  ψ_0(j) = 0

递推:
  δ_i(j) = max_k (δ_{i-1}(k) + transition[k][j] + emission[i][j])
  ψ_i(j) = argmax_k (δ_{i-1}(k) + transition[k][j])

回溯:
  y_n = argmax_j δ_n(j) + end_transitions[j]
  y_i = ψ_{i+1}(y_{i+1})
```

## BiLSTM-CRF 调研

### 历史背景

| 年份 | 方法 | 贡献 |
|------|------|------|
| 2001 | MEMM | 最大熵马尔可夫模型 |
| 2001 | CRF | 条件随机场 |
| 2015 | LSTM-CRF | Huang et al. |
| 2016 | BiLSTM-CRF | Lample et al. |

### 为什么 BiLSTM + CRF?

#### LSTM 的优势
- 捕获长距离依赖
- 自动学习特征
- 处理变长序列

#### CRF 的优势
- 建模标签间依赖
- 保证输出合法性
- 全局最优解

#### 组合优势
```
BiLSTM: 学习高质量的上下文表示
CRF:    保证输出序列的合法性
=       更准确的序列标注
```

### 与其他方法的对比

| 方法 | 优点 | 缺点 |
|------|------|------|
| CNN-CRF | 速度快 | 上下文受限 |
| BiLSTM-CRF | 上下文建模好 | 训练较慢 |
| Transformer-CRF | 并行计算 | 参数量大 |

## NER 数据集调研

### 常用数据集

| 数据集 | 语言 | 实体类型 | 规模 |
|--------|------|---------|------|
| CoNLL-2003 | 英 | PER, LOC, ORG, MISC | 22K 句 |
| OntoNotes 5.0 | 中/英 | 18 类 | 1.7M 词 |
| MSRA NER | 中 | PER, LOC, ORG | 46K 句 |
| People Daily | 中 | PER, LOC, ORG | 20K 句 |

### 评估指标

```
精确率 (Precision) = TP / (TP + FP)
召回率 (Recall)    = TP / (TP + FN)
F1 分数            = 2 * P * R / (P + R)

TP: 正确识别的实体
FP: 错误识别的实体
FN: 漏掉的实体
```

实体级别的评估: 只有当实体的边界和类型都正确时，才算正确。
