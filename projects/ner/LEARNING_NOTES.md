# NER 序列标注 - 学习笔记

## 学习目标

1. 理解序列标注问题的本质
2. 掌握 CRF 算法的原理和实现
3. 学会 BiLSTM-CRF 架构
4. 实现完整的 NER 系统

## 关键知识点

### 1. 序列标注是什么?

序列标注是 NLP 中的基础任务，为输入序列中的每个 token 分配一个标签。

**核心挑战**:
- 标签之间有依赖关系 (B-PER 后面应该是 I-PER)
- 需要上下文信息 (同一个词在不同上下文可能是不同实体)
- 变长序列处理

**应用场景**:
- 命名实体识别 (NER)
- 词性标注 (POS Tagging)
- 语义角色标注 (SRL)

### 2. CRF 的核心思想

CRF (Conditional Random Field) 是一种判别式概率图模型。

**核心公式**:
```
P(y|x) = exp(Score(x, y)) / Z(x)

Score(x, y) = Σ emission_score + Σ transition_score
```

**关键理解**:
- 发射分数: 当前位置的特征对标签的偏好
- 转移分数: 相邻标签之间的兼容性
- 配分函数: 归一化常数，确保概率和为 1

**为什么需要 CRF?**

纯 LSTM 独立预测每个位置的标签，不考虑标签间的依赖关系。CRF 通过转移矩阵建模标签之间的依赖，保证输出序列的合法性。

### 3. 维特比算法

维特比算法是求解最优路径的动态规划算法。

**核心思想**:
- 维护到达每个位置每个标签的最优分数
- 从后向前回溯得到最优路径

**复杂度**:
- 时间: O(T * n^2)
- 空间: O(T * n)

**实现要点**:
- 使用向量化计算加速
- 使用 log-sum-exp 避免数值溢出

### 4. BiLSTM-CRF 架构

**架构组件**:

```
Input → Embedding → BiLSTM → Linear → CRF → Output
```

**各组件作用**:
- Embedding: 将离散 token 映射为连续向量
- BiLSTM: 捕获上下文信息 (前向 + 后向)
- Linear: 将隐状态映射为发射分数
- CRF: 建模标签转移关系

**为什么 BiLSTM + CRF?**
- BiLSTM 学习高质量的上下文表示
- CRF 保证输出序列的合法性
- 两者结合比单独使用效果更好

### 5. BIO 标注方案

```
B-XXX: 实体 XXX 的开始 (Begin)
I-XXX: 实体 XXX 的内部 (Inside)
O:     非实体 (Outside)
```

**标注规则**:
- 实体的第一个 token 用 B-
- 实体的后续 token 用 I-
- 非实体 token 用 O
- 相邻同类实体用 B- 分隔

**示例**:
```
John lives in New York
B-PER O O B-LOC I-LOC
```

## 实现心得

### CRF 实现

**最重要的技巧**:
1. 使用 log-sum-exp 避免数值溢出
2. 使用掩码处理变长序列
3. 转移矩阵使用 column-major 方式

**调试经验**:
- 检查损失是否为正数
- 检查最优路径分数是否 <= 配分函数
- 检查梯度是否正常

### BiLSTM 实现

**关键点**:
1. 使用 pack_padded_sequence 处理变长序列
2. Dropout 放在嵌入层和 LSTM 输出后
3. 多层 LSTM 才使用层间 Dropout

### 数据处理

**CoNLL 格式**:
- 每行一个 token + 标签
- 空行分隔句子
- 支持多种分隔符

**词表构建**:
- 特殊标记: PAD (0), UNK (1)
- 最小频率过滤
- 统计词频

## 常见问题

### Q1: 为什么需要 CRF?

**A**: LSTM 独立预测每个位置的标签，不考虑标签间的依赖关系。例如，I-PER 不应该跟在 B-LOC 后面。CRF 通过转移矩阵学习标签之间的合法转移规则。

### Q2: CRF 的训练目标是什么?

**A**: 最大化正确标签序列的对数似然:

```
L = log P(y*|x) = Score(x, y*) - log Z(x)
```

### Q3: 维特比算法和前向算法的区别?

**A**:
- 前向算法: 计算配分函数 Z(x)，用于训练
- 维特比算法: 找到最优路径 y*，用于预测

### Q4: 如何处理变长序列?

**A**:
1. 填充到固定长度
2. 使用掩码标记有效位置
3. 使用 pack_padded_sequence 加速计算

### Q5: 如何评估 NER 系统?

**A**: 使用实体级别的评估:
- 精确率 (Precision): 预测为实体的结果中，正确比例
- 召回率 (Recall): 真实实体中，被正确识别的比例
- F1 分数: 精确率和召回率的调和平均

## 学习资源

### 论文

1. **Conditional Random Fields**: Lafferty et al., 2001
2. **BiLSTM-CRF for NER**: Lample et al., 2016
3. **BERT for NER**: Devlin et al., 2019

### 教程

1. Stanford CS224N: NLP with Deep Learning
2. CMU CS11-747: Neural Nets for NLP
3. Hugging Face NER Tutorial

### 代码

1. PyTorch CRF 实现
2. Hugging Face Transformers
3. AllenNLP

## 下一步学习

### 短期目标

1. 在 CoNLL-2003 数据集上训练
2. 实现字符级特征
3. 尝试不同的超参数

### 中期目标

1. 实现 BERT-CRF 模型
2. 支持中文 NER
3. 实现多任务学习

### 长期目标

1. 研究最新的 NER 方法
2. 应用到实际项目
3. 探索小样本 NER

## 总结

通过这个项目，我学习了:

1. **序列标注**: 理解了序列标注问题的本质和挑战
2. **CRF 算法**: 掌握了 CRF 的原理和实现
3. **BiLSTM-CRF**: 学会了如何结合深度学习和概率图模型
4. **NER 系统**: 实现了完整的命名实体识别系统

关键收获:
- CRF 通过转移矩阵建模标签之间的依赖关系
- 维特比算法高效求解最优路径
- BiLSTM-CRF 是序列标注的经典架构
- 实体级别的评估更能反映实际效果
