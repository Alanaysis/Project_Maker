# 03 - 实现文档：文本分类

## 1. 实现概述

本文档详细描述了文本分类系统的实现细节，包括 TF-IDF 向量化器、朴素贝叶斯分类器和文本分类管道。

## 2. TF-IDF 向量化器实现

### 2.1 分词器实现

```python
def _tokenize(self, text: str) -> List[str]:
    """简单的分词器"""
    # 转换为小写
    text = text.lower()
    # 移除基本标点
    for char in ".,!?;:()[]{}\"'":
        text = text.replace(char, " ")
    # 按空格分割
    return text.split()
```

**设计决策**：
- 使用简单的小写转换和空格分割
- 移除基本标点符号
- 不使用复杂的 NLP 库，保持实现简单

### 2.2 TF 计算实现

```python
def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
    """计算单个文档的词频"""
    counter = Counter(tokens)
    total = len(tokens)

    if total == 0:
        return {}

    tf = {}
    for term, count in counter.items():
        frequency = count / total
        if self.sublinear_tf:
            frequency = 1 + math.log(frequency) if frequency > 0 else 0
        tf[term] = frequency

    return tf
```

**关键点**：
- 使用 Counter 统计词频
- 处理空文档的情况
- 支持次线性 TF 缩放（1 + log(tf)）

### 2.3 IDF 计算实现

```python
def _compute_idf(self, documents: List[List[str]]) -> Dict[str, float]:
    """计算所有词的逆文档频率"""
    n_documents = len(documents)
    df = Counter()  # 文档频率

    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1

    idf = {}
    for term, freq in df.items():
        if self.smooth_idf:
            idf[term] = math.log((1 + n_documents) / (1 + freq)) + 1
        else:
            idf[term] = math.log(n_documents / freq) + 1

    return idf
```

**关键点**：
- 使用集合去重，每个文档只计数一次
- 支持平滑 IDF（避免除零）
- IDF 公式：log(N / df) + 1

### 2.4 文档频率过滤实现

```python
def _apply_df_filter(self, df: Dict[str, int], n_documents: int) -> Set[str]:
    """根据文档频率阈值过滤词"""
    valid_terms = set()

    # 计算阈值
    if isinstance(self.min_df, float):
        min_threshold = self.min_df * n_documents
    else:
        min_threshold = self.min_df

    if isinstance(self.max_df, float):
        max_threshold = self.max_df * n_documents
    else:
        max_threshold = self.max_df

    for term, freq in df.items():
        if freq >= min_threshold and freq <= max_threshold:
            valid_terms.add(term)

    return valid_terms
```

**关键点**：
- 支持比例和绝对数两种阈值
- 过滤低频词（噪声）和高频词（停用词）

### 2.5 归一化实现

```python
# 在 transform 方法中
if self.norm == "l2":
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
elif self.norm == "l1":
    norm = sum(abs(x) for x in vector)
    if norm > 0:
        vector = [x / norm for x in vector]
```

**关键点**：
- L2 归一化：向量长度为 1
- L1 归一化：向量元素绝对值之和为 1
- 处理零向量的情况

### 2.6 完整 transform 流程

```python
def transform(self, documents: List[str]) -> List[List[float]]:
    """将文档转换为 TF-IDF 特征向量"""
    if not self.vocabulary_:
        raise RuntimeError("Vectorizer has not been fitted. Call fit() first.")

    n_features = len(self.vocabulary_)
    result = []

    for doc in documents:
        # 分词
        tokens = self._tokenize(doc)

        # 计算 TF
        tf = self._compute_tf(tokens)

        # 创建特征向量
        vector = [0.0] * n_features

        for term, tf_value in tf.items():
            if term in self.vocabulary_:
                idx = self.vocabulary_[term]
                if self.use_idf:
                    vector[idx] = tf_value * self.idf_[idx]
                else:
                    vector[idx] = tf_value

        # 归一化
        if self.norm == "l2":
            norm = math.sqrt(sum(x * x for x in vector))
            if norm > 0:
                vector = [x / norm for x in vector]
        elif self.norm == "l1":
            norm = sum(abs(x) for x in vector)
            if norm > 0:
                vector = [x / norm for x in vector]

        result.append(vector)

    return result
```

## 3. 朴素贝叶斯分类器实现

### 3.1 多项式朴素贝叶斯实现

**训练过程**：

```python
def _compute_multinomial_probs(self, X: List[List[float]], y: List[str]) -> None:
    """计算多项式朴素贝叶斯的特征概率"""
    n_samples = len(X)
    n_features = len(X[0]) if X else 0
    self.n_features_ = n_features

    # 统计每个类的特征计数
    feature_counts = defaultdict(lambda: [0.0] * n_features)
    class_counts = Counter()

    for i, (features, label) in enumerate(zip(X, y)):
        class_counts[label] += 1
        for j, value in enumerate(features):
            feature_counts[label][j] += value

    # 计算对数概率
    for cls in self.classes_:
        # 先验概率: P(y)
        self.class_log_prior_[cls] = math.log(
            class_counts[cls] / n_samples
        )

        # 条件概率: P(x|y) with Laplace smoothing
        total_count = sum(feature_counts[cls]) + self.alpha * n_features
        self.feature_log_prob_[cls] = [
            math.log((feature_counts[cls][j] + self.alpha) / total_count)
            for j in range(n_features)
        ]
```

**关键点**：
- 使用 defaultdict 统计特征计数
- 使用对数概率避免数值下溢
- 拉普拉斯平滑处理零计数

**预测过程**：

```python
def _predict_multinomial_single(self, x: List[float]) -> str:
    """预测单个样本的类别"""
    best_class = None
    best_score = float("-inf")

    for cls in self.classes_:
        # 从对数先验开始
        score = self.class_log_prior_[cls]

        # 添加特征的对数似然
        for j, value in enumerate(x):
            if value != 0:
                score += value * self.feature_log_prob_[cls][j]

        if score > best_score:
            best_score = score
            best_class = cls

    return best_class
```

**关键点**：
- 使用对数概率相加代替概率相乘
- 只计算非零特征，提高效率
- 返回得分最高的类别

### 3.2 高斯朴素贝叶斯实现

**训练过程**：

```python
def _compute_gaussian_probs(self, X: List[List[float]], y: List[str]) -> None:
    """计算高斯朴素贝叶斯的参数"""
    n_samples = len(X)
    n_features = len(X[0]) if X else 0
    self.n_features_ = n_features

    # 按类别分组
    class_samples = defaultdict(list)
    for features, label in zip(X, y):
        class_samples[label].append(features)

    # 计算每个类的均值和方差
    for cls in self.classes_:
        samples = class_samples[cls]
        n_class = len(samples)

        # 先验概率: P(y)
        self.class_log_prior_[cls] = math.log(n_class / n_samples)

        # 均值: theta = mean of each feature
        mean = [0.0] * n_features
        for j in range(n_features):
            mean[j] = sum(s[j] for s in samples) / n_class
        self.theta_[cls] = mean

        # 方差: sigma^2 = variance of each feature
        variance = [0.0] * n_features
        for j in range(n_features):
            variance[j] = (
                sum((s[j] - mean[j]) ** 2 for s in samples) / n_class
            )
            # 避免零方差
            variance[j] = max(variance[j], 1e-9)
        self.sigma_[cls] = variance
```

**关键点**：
- 按类别分组样本
- 计算每个特征的均值和方差
- 添加小的 epsilon 避免零方差

**预测过程**：

```python
def _predict_gaussian_single(self, x: List[float]) -> str:
    """预测单个样本的类别"""
    best_class = None
    best_score = float("-inf")

    for cls in self.classes_:
        # 从对数先验开始
        score = self.class_log_prior_[cls]

        # 添加特征的对数似然（高斯）
        for j, value in enumerate(x):
            mean = self.theta_[cls][j]
            variance = self.sigma_[cls][j]
            # 高斯 PDF 的对数
            score -= 0.5 * math.log(2 * math.pi * variance)
            score -= 0.5 * ((value - mean) ** 2) / variance

        if score > best_score:
            best_score = score
            best_class = cls

    return best_class
```

**关键点**：
- 使用高斯概率密度函数
- 在对数空间计算
- 处理方差为零的情况

### 3.3 概率预测实现

```python
def predict_proba(self, X: List[List[float]]) -> List[Dict[str, float]]:
    """预测概率"""
    if not self.classes_:
        raise RuntimeError("Classifier has not been fitted. Call fit() first.")

    probabilities = []
    for x in X:
        # 计算每个类的对数概率
        log_probs = {}
        for cls in self.classes_:
            if self.model_type == "multinomial":
                score = self.class_log_prior_[cls]
                for j, value in enumerate(x):
                    if value != 0:
                        score += value * self.feature_log_prob_[cls][j]
            else:
                score = self.class_log_prior_[cls]
                for j, value in enumerate(x):
                    mean = self.theta_[cls][j]
                    variance = self.sigma_[cls][j]
                    score -= 0.5 * math.log(2 * math.pi * variance)
                    score -= 0.5 * ((value - mean) ** 2) / variance
            log_probs[cls] = score

        # 使用 log-sum-exp 技巧转换为概率
        max_log_prob = max(log_probs.values())
        exp_probs = {
            cls: math.exp(lp - max_log_prob)
            for cls, lp in log_probs.items()
        }
        total = sum(exp_probs.values())
        probs = {cls: ep / total for cls, ep in exp_probs.items()}

        probabilities.append(probs)

    return probabilities
```

**关键点**：
- 使用 log-sum-exp 技巧避免数值溢出
- 确保概率之和为 1
- 返回每个类别的概率

## 4. 文本分类器实现

### 4.1 初始化实现

```python
class TextClassifier:
    def __init__(
        self,
        max_features: Optional[int] = None,
        alpha: float = 1.0,
        norm: Optional[str] = "l2",
        use_idf: bool = True,
        sublinear_tf: bool = False,
    ):
        self.max_features = max_features
        self.alpha = alpha
        self.norm = norm
        self.use_idf = use_idf
        self.sublinear_tf = sublinear_tf

        # 初始化组件
        self.vectorizer = TFIDFVectorizer(
            max_features=max_features,
            norm=norm,
            use_idf=use_idf,
            sublinear_tf=sublinear_tf,
        )
        self.classifier = NaiveBayesClassifier(alpha=alpha, model_type="multinomial")

        # 状态
        self.is_fitted = False
```

**关键点**：
- 组合 TFIDFVectorizer 和 NaiveBayesClassifier
- 参数传递给子组件
- 跟踪训练状态

### 4.2 训练实现

```python
def fit(self, texts: List[str], labels: List[str]) -> "TextClassifier":
    """训练文本分类器"""
    if len(texts) != len(labels):
        raise ValueError(
            f"texts and labels must have the same length, "
            f"got {len(texts)} and {len(labels)}"
        )

    # 拟合并转换文本为 TF-IDF 特征
    X = self.vectorizer.fit_transform(texts)

    # 训练朴素贝叶斯分类器
    self.classifier.fit(X, labels)
    self.is_fitted = True

    return self
```

**关键点**：
- 验证输入数据
- 组件协作：先向量化，再分类
- 返回 self 支持链式调用

### 4.3 预测实现

```python
def predict(self, texts: List[str]) -> List[str]:
    """预测类别"""
    if not self.is_fitted:
        raise RuntimeError("Classifier has not been fitted. Call fit() first.")

    # 转换文本为 TF-IDF 特征
    X = self.vectorizer.transform(texts)

    # 预测
    return self.classifier.predict(X)
```

**关键点**：
- 检查训练状态
- 复用向量化器的 transform 方法
- 委托给分类器预测

### 4.4 顶级特征实现

```python
def get_top_features(self, n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
    """获取每个类的顶级特征"""
    if not self.is_fitted:
        raise RuntimeError("Classifier has not been fitted. Call fit() first.")

    feature_names = self.vectorizer.get_feature_names()
    top_features = {}

    for cls in self.classifier.classes_:
        # 获取该类的对数概率
        log_probs = self.classifier.feature_log_prob_[cls]

        # 创建 (特征, 概率) 对
        feature_probs = [
            (feature_names[i], log_probs[i])
            for i in range(len(feature_names))
        ]

        # 按概率排序（降序）
        feature_probs.sort(key=lambda x: x[1], reverse=True)

        # 取前 n 个
        top_features[cls] = feature_probs[:n]

    return top_features
```

**关键点**：
- 结合词汇表和特征概率
- 按重要性排序
- 返回每个类的 top-n 特征

## 5. 错误处理实现

### 5.1 输入验证

```python
def fit(self, texts: List[str], labels: List[str]) -> "TextClassifier":
    if len(texts) != len(labels):
        raise ValueError(
            f"texts and labels must have the same length, "
            f"got {len(texts)} and {len(labels)}"
        )
```

### 5.2 状态检查

```python
def predict(self, texts: List[str]) -> List[str]:
    if not self.is_fitted:
        raise RuntimeError("Classifier has not been fitted. Call fit() first.")
```

### 5.3 参数验证

```python
def __init__(self, alpha: float = 1.0, model_type: str = "multinomial"):
    if model_type not in ["multinomial", "gaussian"]:
        raise ValueError(f"Unknown model_type: {model_type}")
```

## 6. 测试实现

### 6.1 单元测试策略

**TF-IDF 测试**：
- 测试基本 fit/transform 功能
- 测试 TF 计算
- 测试 IDF 计算
- 测试归一化
- 测试文档频率过滤
- 测试边界情况

**朴素贝叶斯测试**：
- 测试基本 fit/predict 功能
- 测试概率预测
- 测试准确率计算
- 测试拉普拉斯平滑
- 测试边界情况

**文本分类器测试**：
- 测试完整管道
- 测试错误处理
- 测试顶级特征提取
- 测试集成场景

### 6.2 测试数据设计

```python
# 简单二分类
texts = [
    "I love this movie, it is great",
    "This movie is excellent and wonderful",
    "I hate this movie, it is terrible",
    "This movie is awful and boring",
]
labels = ["positive", "positive", "negative", "negative"]

# 多分类
texts = [
    "I love programming in Python",
    "Python is a great language",
    "I enjoy cooking Italian food",
    "Italian cuisine is delicious",
    "The weather is sunny today",
    "Today is a beautiful day",
]
labels = ["tech", "tech", "food", "food", "weather", "weather"]
```

## 7. 性能优化

### 7.1 对数空间计算

使用对数概率避免数值下溢：

```python
# 不好的方式：概率相乘
prob = p1 * p2 * p3 * ...  # 可能下溢

# 好的方式：对数相加
log_prob = log_p1 + log_p2 + log_p3 + ...  # 稳定
```

### 7.2 log-sum-exp 技巧

计算 softmax 时避免溢出：

```python
# 不好的方式
exp_values = [math.exp(x) for x in values]  # 可能溢出
total = sum(exp_values)
probs = [x / total for x in exp_values]

# 好的方式
max_value = max(values)
exp_values = [math.exp(x - max_value) for x in values]  # 稳定
total = sum(exp_values)
probs = [x / total for x in exp_values]
```

### 7.3 稀疏特征优化

只计算非零特征：

```python
for j, value in enumerate(x):
    if value != 0:  # 跳过零特征
        score += value * self.feature_log_prob_[cls][j]
```

## 8. 代码质量

### 8.1 类型注解

```python
def fit(self, documents: List[str]) -> "TFIDFVectorizer":
    """Learn vocabulary and IDF weights."""
    ...
```

### 8.2 文档字符串

```python
class TFIDFVectorizer:
    """
    Convert a collection of raw documents to a matrix of TF-IDF features.

    Parameters
    ----------
    max_features : int or None
        Maximum number of features to keep.
    ...
    """
```

### 8.3 一致性接口

所有组件遵循相同的接口模式：
- fit() - 训练
- transform() / predict() - 预测
- fit_transform() - 训练并转换
- get_params() - 获取参数

## 9. 参考实现

### 9.1 scikit-learn TF-IDF

```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=10000,
    min_df=2,
    max_df=0.95,
    norm='l2',
    use_idf=True,
    smooth_idf=True,
    sublinear_tf=False
)
X = vectorizer.fit_transform(documents)
```

### 9.2 scikit-learn 朴素贝叶斯

```python
from sklearn.naive_bayes import MultinomialNB

clf = MultinomialNB(alpha=1.0)
clf.fit(X_train, y_train)
predictions = clf.predict(X_test)
```

## 10. 参考文献

1. scikit-learn TfidfVectorizer 源码
2. scikit-learn MultinomialNB 源码
3. Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval.
