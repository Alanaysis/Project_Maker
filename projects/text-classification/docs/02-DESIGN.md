# 02 - 设计文档：文本分类系统

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    文本分类系统架构                           │
├─────────────────────────────────────────────────────────────┤
│  应用层 (Applications)                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 情感分析     │ │ 新闻分类     │ │ 垃圾邮件检测 │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  分类器层 (Classifiers)                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 朴素贝叶斯   │ │ 逻辑回归     │ │ SVM          │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ TextCNN      │ │ LSTM         │ │ BiLSTM+Attn  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  特征提取层 (Feature Extraction)                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 词袋模型     │ │ TF-IDF       │ │ N-gram       │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  评估层 (Evaluation)                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 准确率       │ │ 精确率/召回率│ │ 混淆矩阵     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 特征提取模块 (src/bow.py, src/tfidf.py, src/ngram.py)

#### 类设计

```python
class Vectorizer:
    """特征提取器基类"""

    def fit(documents: List[str]) -> Self
        """学习词汇表"""

    def transform(documents: List[str]) -> List[List[float]]
        """转换文档为特征向量"""

    def fit_transform(documents: List[str]) -> List[List[float]]
        """拟合并转换"""

    def get_feature_names() -> List[str]
        """获取特征名称"""
```

#### BagOfWordsVectorizer

```
输入: ["the cat sat", "the dog ran"]
      ↓
分词: [["the", "cat", "sat"], ["the", "dog", "ran"]]
      ↓
构建词汇表: {the: 0, cat: 1, sat: 2, dog: 3, ran: 4}
      ↓
计数: [[2, 1, 1, 0, 0], [2, 0, 0, 1, 1]]
```

#### TFIDFVectorizer

```
输入文档
    ↓
计算TF (词频)
    ↓
计算IDF (逆文档频率)
    ↓
TF × IDF = TF-IDF权重
    ↓
归一化 (L1/L2)
```

#### NGramVectorizer

```
输入: "the cat sat"
      ↓
生成N-gram:
  - Unigram: ["the", "cat", "sat"]
  - Bigram: ["the cat", "cat sat"]
  - Combined: ["the", "cat", "sat", "the cat", "cat sat"]
      ↓
构建词汇表并计数
```

### 2.2 传统分类器模块

#### NaiveBayesClassifier

```
训练阶段:
    输入: (X, y)
        ↓
    计算先验概率 P(y)
        ↓
    计算条件概率 P(x|y)
        ↓
    存储模型参数

预测阶段:
    输入: x
        ↓
    计算后验概率 P(y|x) ∝ P(x|y) × P(y)
        ↓
    返回 argmax P(y|x)
```

#### LogisticRegressionClassifier

```
训练阶段 (梯度下降):
    初始化权重 w = 0
        ↓
    循环:
        计算预测值 ŷ = sigmoid(Xw + b)
        计算梯度 ∇L = X^T(ŷ - y) + λw
        更新权重 w = w - α∇L
        ↓
    直到收敛

预测阶段:
    输入: x
        ↓
    计算概率 p = sigmoid(w^T x + b)
        ↓
    返回类别 (p > 0.5 → 正类)
```

#### SVMClassifier

```
训练阶段 (Pegasos算法):
    初始化权重 w = 0
        ↓
    循环:
        随机选择样本 (xᵢ, yᵢ)
        计算学习率 η = 1/(λt)
        ↓
        如果 yᵢ(w^T xᵢ) < 1:
            w = (1 - ηλ)w + ηCyᵢxᵢ
        否则:
            w = (1 - ηλ)w
        ↓
    直到收敛

预测阶段:
    输入: x
        ↓
    计算决策值 score = w^T x + b
        ↓
    返回类别 (score > 0 → 正类)
```

### 2.3 深度学习模块 (src/deep_learning.py)

#### TextCNN

```
架构:
    输入序列 [w1, w2, ..., wn]
        ↓
    嵌入层: [e1, e2, ..., en]
        ↓
    并行卷积 (不同卷积核大小):
        ├── Conv(k=2): [h1, h2, ..., h_{n-1}]
        ├── Conv(k=3): [h1, h2, ..., h_{n-2}]
        └── Conv(k=4): [h1, h2, ..., h_{n-3}]
        ↓
    最大池化:
        ├── MaxPool(k=2): h_max1
        ├── MaxPool(k=3): h_max2
        └── MaxPool(k=4): h_max3
        ↓
    拼接: [h_max1, h_max2, h_max3]
        ↓
    全连接层 + Softmax
        ↓
    输出类别概率
```

#### LSTM

```
单元结构:
    输入: xₜ, hₜ₋₁, cₜ₋₁
        ↓
    遗忘门: fₜ = σ(Wf · [hₜ₋₁, xₜ])
    输入门: iₜ = σ(Wi · [hₜ₋₁, xₜ])
    候选值: c̃ₜ = tanh(Wc · [hₜ₋₁, xₜ])
    输出门: oₜ = σ(Wo · [hₜ₋₁, xₜ])
        ↓
    细胞状态: cₜ = fₜ * cₜ₋₁ + iₜ * c̃ₜ
    隐藏状态: hₜ = oₜ * tanh(cₜ)
        ↓
    输出: hₜ, cₜ
```

#### BiLSTM + Attention

```
架构:
    输入序列 [w1, w2, ..., wn]
        ↓
    嵌入层: [e1, e2, ..., en]
        ↓
    双向LSTM:
        ├── 前向LSTM: [h1→, h2→, ..., hn→]
        └── 后向LSTM: [h1←, h2←, ..., hn←]
        ↓
    拼接: [h1, h2, ..., hn] where hᵢ = [hᵢ→; hᵢ←]
        ↓
    注意力机制:
        eᵢ = v^T tanh(W hᵢ)
        αᵢ = softmax(eᵢ)
        context = Σ αᵢ hᵢ
        ↓
    全连接层 + Softmax
        ↓
    输出类别概率
```

### 2.4 评估模块 (src/evaluation.py)

```
评估流程:
    输入: (y_true, y_pred)
        ↓
    计算混淆矩阵
        ↓
    计算基础指标:
        ├── 准确率 (Accuracy)
        ├── 精确率 (Precision)
        ├── 召回率 (Recall)
        └── F1分数
        ↓
    生成分类报告
```

### 2.5 应用模块 (src/applications.py)

```
应用管道:
    ┌─────────────────────────────────────────┐
    │  SentimentAnalyzer                      │
    │  ├── TFIDFVectorizer                    │
    │  └── NaiveBayes/LogReg/SVM             │
    └─────────────────────────────────────────┘
    ┌─────────────────────────────────────────┐
    │  NewsClassifier                         │
    │  ├── TFIDFVectorizer (bigrams)          │
    │  └── LogisticRegression/SVM             │
    └─────────────────────────────────────────┘
    ┌─────────────────────────────────────────┐
    │  SpamDetector                           │
    │  ├── TFIDFVectorizer                    │
    │  └── NaiveBayes/LogReg/SVM             │
    └─────────────────────────────────────────┘
```

## 3. 接口设计

### 3.1 统一接口

所有分类器遵循统一接口：

```python
class Classifier:
    def fit(X, y) -> Self
    def predict(X) -> List[str]
    def predict_proba(X) -> List[Dict[str, float]]
    def score(X, y) -> float
    def get_params() -> Dict
```

### 3.2 管道接口

```python
class TextClassifier:
    """高级文本分类管道"""

    def fit(texts, labels) -> Self
    def predict(texts) -> List[str]
    def predict_proba(texts) -> List[Dict[str, float]]
    def score(texts, labels) -> float
    def get_top_features(n) -> Dict[str, List[Tuple[str, float]]]
```

## 4. 数据流设计

### 4.1 训练流程

```
原始文本 → 分词 → 特征提取 → 训练分类器 → 保存模型
```

### 4.2 预测流程

```
原始文本 → 分词 → 特征提取 → 分类器预测 → 输出类别
```

### 4.3 评估流程

```
测试数据 → 预测 → 计算指标 → 生成报告
```

## 5. 错误处理

### 5.1 输入验证

- 文本列表和标签列表长度必须一致
- 特征矩阵维度必须匹配
- 分类器必须先训练再预测

### 5.2 异常类型

- `RuntimeError`: 分类器未训练
- `ValueError`: 参数无效或维度不匹配

## 6. 性能优化

### 6.1 计算优化

- 使用NumPy进行向量化计算
- 批量处理减少循环

### 6.2 内存优化

- 特征选择减少维度
- 模型压缩减少存储

## 7. 扩展性设计

### 7.1 新增分类器

```python
class NewClassifier:
    def fit(X, y): ...
    def predict(X): ...
    def predict_proba(X): ...
    def score(X, y): ...
```

### 7.2 新增特征提取器

```python
class NewVectorizer:
    def fit(documents): ...
    def transform(documents): ...
    def fit_transform(documents): ...
```

### 7.3 新增应用

```python
class NewApplication:
    def __init__(classifier_type): ...
    def fit(texts, labels): ...
    def predict(texts): ...
    def evaluate(texts, labels): ...
```
