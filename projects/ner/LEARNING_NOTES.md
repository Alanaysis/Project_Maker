# NER 序列标注 - 学习笔记

## 学习目标

1. 理解序列标注问题的本质和标注方案 (BIO / BIOES)
2. 掌握基于规则的 NER 方法 (正则匹配、词典匹配)
3. 掌握统计模型 NER (HMM、CRF)
4. 掌握深度学习 NER (BiLSTM、BiLSTM-CRF)
5. 实现完整的评估体系 (Accuracy、Precision、Recall、F1)

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

### 2. 标注方案

#### BIO 标注

```
B-XXX: 实体 XXX 的开始 (Begin)
I-XXX: 实体 XXX 的内部 (Inside)
O:     非实体 (Outside)

示例:
  John lives in New York
  B-PER O O B-LOC I-LOC
```

#### BIOES 标注

```
B-XXX: 多 token 实体的开始 (Begin)
I-XXX: 多 token 实体的内部 (Inside)
O:     非实体 (Outside)
E-XXX: 多 token 实体的结束 (End)
S-XXX: 单 token 实体 (Single)

示例:
  John lives in New    York     and Paris
  S-PER O  O  B-LOC E-LOC     O S-LOC
```

BIOES 比 BIO 提供更丰富的边界信息，通常效果更好。

### 3. 基于规则的 NER

#### 正则匹配

适用场景: 格式化实体 (日期、电话、邮箱等)

```
优点: 无需训练数据、精确度高、可解释性强
缺点: 召回率低、需要人工编写规则
```

#### 词典匹配

适用场景: 已知实体集合 (人名库、地名库)

```
优点: 速度快、精确度高、易于维护
缺点: 召回率受词典覆盖限制、无法识别未登录实体
```

使用 Trie 树实现高效的词典匹配。

### 4. HMM 的核心思想

HMM (Hidden Markov Model) 是生成式概率图模型。

**三个核心参数**:
```
- 初始概率 pi: P(y_1)
- 转移概率 A: P(y_t | y_{t-1})
- 发射概率 B: P(x_t | y_t)
```

**训练方法**: 极大似然估计 (MLE) + Laplace 平滑

**解码方法**: 维特比算法

**与 CRF 的区别**:
- HMM 是生成式模型，CRF 是判别式模型
- HMM 需要建模 P(X)，CRF 直接建模 P(Y|X)
- HMM 特征工程受限，CRF 可以使用任意特征

### 5. CRF 的核心思想

CRF (Conditional Random Field) 是一种判别式概率图模型。

**核心公式**:
```
P(y|x) = exp(Score(x, y)) / Z(x)

Score(x, y) = sum(emission_score) + sum(transition_score)
```

**关键理解**:
- 发射分数: 当前位置的特征对标签的偏好
- 转移分数: 相邻标签之间的兼容性
- 配分函数: 归一化常数，确保概率和为 1

**为什么需要 CRF?**

纯 LSTM 独立预测每个位置的标签，不考虑标签间的依赖关系。CRF 通过转移矩阵建模标签之间的依赖，保证输出序列的合法性。

### 6. 维特比算法

维特比算法是求解最优路径的动态规划算法。

**核心思想**:
- 维护到达每个位置每个标签的最优分数
- 从后向前回溯得到最优路径

**复杂度**:
- 时间: O(T * n^2)
- 空间: O(T * n)

### 7. BiLSTM-CRF 架构

```
Input -> Embedding -> BiLSTM -> Linear -> CRF -> Output
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

### 8. 评估指标

```
准确率 (Accuracy) = 正确预测的 token 数 / 总 token 数
精确率 (Precision) = TP / (TP + FP)
召回率 (Recall)    = TP / (TP + FN)
F1 分数            = 2 * P * R / (P + R)
```

实体级别的评估: 只有当实体的边界和类型都正确时，才算正确。

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

### HMM 实现

**关键点**:
1. 使用 Laplace 平滑避免零概率
2. 使用 log 概率避免下溢
3. 维特比算法使用向量化加速

### 词典匹配实现

**Trie 树的优势**:
1. 前缀共享，节省空间
2. 匹配时间与词典大小无关
3. 支持正向和逆向匹配

### BiLSTM 实现

**关键点**:
1. 使用 pack_padded_sequence 处理变长序列
2. Dropout 放在嵌入层和 LSTM 输出后
3. 多层 LSTM 才使用层间 Dropout

## 常见问题

### Q1: BIO 和 BIOES 哪个更好?

**A**: BIOES 通常效果更好，因为:
- 明确标记实体结束位置
- 区分单 token 实体和多 token 实体
- 提供更丰富的边界信息

但 BIOES 标签数量更多 (4n+1 vs 2n+1)，在小数据集上可能过拟合。

### Q2: 什么时候用规则方法，什么时候用模型方法?

**A**:
- 规则方法: 格式化实体 (日期、电话)、已知实体集合
- 模型方法: 需要上下文理解的实体 (人名、机构名)
- 混合方法: 规则方法处理明确实体，模型方法处理复杂实体

### Q3: HMM 和 CRF 怎么选?

**A**:
- HMM: 小数据集、需要快速训练、特征简单
- CRF: 中等数据集、需要丰富特征、追求更好效果

### Q4: BiLSTM 和 BiLSTM-CRF 怎么选?

**A**:
- BiLSTM: 训练速度快、实现简单
- BiLSTM-CRF: 效果更好、保证输出合法性

在实际应用中，BiLSTM-CRF 几乎总是更好的选择。

### Q5: 如何处理变长序列?

**A**:
1. 填充到固定长度
2. 使用掩码标记有效位置
3. 使用 pack_padded_sequence 加速计算

## 学习资源

### 论文

1. **Conditional Random Fields**: Lafferty et al., 2001
2. **BiLSTM-CRF for NER**: Lample et al., 2016
3. **BERT for NER**: Devlin et al., 2019

### 教程

1. Stanford CS224N: NLP with Deep Learning
2. CMU CS11-747: Neural Nets for NLP
3. Hugging Face NER Tutorial

## 总结

通过这个项目，我学习了:

1. **标注方案**: 理解了 BIO 和 BIOES 的区别和适用场景
2. **规则方法**: 掌握了正则匹配和词典匹配的实现
3. **统计模型**: 掌握了 HMM 和 CRF 的原理和实现
4. **深度学习**: 学会了 BiLSTM 和 BiLSTM-CRF 架构
5. **评估体系**: 实现了完整的 Accuracy/P/R/F1 评估

关键收获:
- 规则方法适合格式化实体和已知实体
- HMM 适合小数据集，CRF 适合中等数据集
- BiLSTM-CRF 是序列标注的经典架构
- 实体级别的评估更能反映实际效果
