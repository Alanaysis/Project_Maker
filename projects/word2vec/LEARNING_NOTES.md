# Word2Vec 学习笔记

## 1. 词向量基础

### 1.1 什么是词向量

词向量（Word Embedding）是将词语映射到低维稠密向量空间的技术。相比传统的 one-hot 编码，词向量能够：
- 捕获语义信息
- 降低维度
- 使词语之间可以计算相似度

### 1.2 词向量的核心思想

**分布式假设**：一个词的含义由它的上下文决定（You shall know a word by the company it keeps）。

相似上下文的词语具有相似的词向量。

## 2. Word2Vec 模型

### 2.1 两种架构

**CBOW (Continuous Bag of Words)**
- 输入：上下文词
- 输出：中心词
- 适合：频繁词，训练速度快

**Skip-gram**
- 输入：中心词
- 输出：上下文词
- 适合：稀有词，语义准确度高

### 2.2 Skip-gram 详解

给定中心词 $w_t$，预测其上下文窗口内的词 $w_{t+j}$：

$$P(w_{t+j} | w_t) = \frac{\exp(v'_{w_j} \cdot v_{w_t})}{\sum_{w \in V} \exp(v'_w \cdot v_{w_t})}$$

其中：
- $v_w$：词 $w$ 的输入向量
- $v'_w$：词 $w$ 的输出向量

### 2.3 训练目标

最大化对数似然：

$$J = \sum_{t=1}^{T} \sum_{-c \leq j \leq c, j \neq 0} \log P(w_{t+j} | w_t)$$

## 3. 负采样优化

### 3.1 为什么需要负采样

原始 Softmax 需要遍历整个词汇表，计算量 $O(|V|)$ 太大。

### 3.2 负采样原理

将多分类问题转化为二分类问题：
- 正样本：真实的 (中心词, 上下文词) 对
- 负样本：随机采样的 (中心词, 随机词) 对

目标函数：

$$\log \sigma(v'_o \cdot v_w) + \sum_{i=1}^{k} \mathbb{E}_{w_i \sim P_n(w)} [\log \sigma(-v'_{w_i} \cdot v_w)]$$

### 3.3 噪声分布

使用词频的 3/4 次方作为采样概率：

$$P_n(w) = \frac{f(w)^{3/4}}{\sum_{w'} f(w')^{3/4}}$$

## 4. 实现细节

### 4.1 词汇表构建

1. 统计词频
2. 过滤低频词
3. 构建词到索引的映射

### 4.2 训练数据生成

1. 滑动窗口遍历语料
2. 生成 (中心词, 上下文词) 对
3. 对每个正样本生成 k 个负样本

### 4.3 参数更新

使用随机梯度下降（SGD）更新参数：

$$\theta = \theta - \eta \cdot \nabla_\theta J$$

## 5. 评估方法

### 5.1 内在评估

- **词相似度**：计算词对相似度与人工评分的相关性
- **类比任务**：man:king = woman:?

### 5.2 外在评估

- 下游任务性能提升

## 6. 常见问题

### 6.1 训练不收敛

- 学习率过大/过小
- 负样本数量不合适
- 语料量不足

### 6.2 向量质量差

- 语料预处理不充分
- 窗口大小不合适
- 训练轮数不足

## 7. 参考资源

- Mikolov et al., 2013, "Efficient Estimation of Word Representations in Vector Space"
- Mikolov et al., 2013, "Distributed Representations of Words and Phrases and their Compositionality"
- TensorFlow Word2Vec Tutorial
