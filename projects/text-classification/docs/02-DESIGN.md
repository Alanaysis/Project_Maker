# 02 - 设计文档：文本分类

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    TextClassifier                        │
│  ┌─────────────────┐      ┌──────────────────────┐     │
│  │  TFIDFVectorizer │      │ NaiveBayesClassifier │     │
│  │                  │      │                      │     │
│  │  文本 → 特征向量 │ ──→  │  特征向量 → 类别    │     │
│  └─────────────────┘      └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
text-classification/
├── src/
│   ├── __init__.py           # 包初始化
│   ├── tfidf.py              # TF-IDF 向量化器
│   ├── naive_bayes.py        # 朴素贝叶斯分类器
│   └── text_classifier.py    # 高层分类管道
└── tests/
    ├── __init__.py
    ├── test_tfidf.py         # TF-IDF 测试
    ├── test_naive_bayes.py   # 朴素贝叶斯测试
    └── test_text_classifier.py  # 文本分类器测试
```

## 2. TF-IDF 向量化器设计

### 2.1 类设计

```python
class TFIDFVectorizer:
    """TF-IDF 向量化器"""

    def __init__(self, max_features, min_df, max_df, norm, use_idf, smooth_idf, sublinear_tf):
        """初始化参数"""

    def fit(self, documents):
        """学习词汇表和 IDF 权重"""

    def transform(self, documents):
        """将文档转换为 TF-IDF 特征向量"""

    def fit_transform(self, documents):
        """拟合并转换文档"""

    def get_feature_names(self):
        """获取特征名称"""
```

### 2.2 核心算法

**TF 计算**：
```python
def _compute_tf(self, tokens):
    counter = Counter(tokens)
    total = len(tokens)
    tf = {term: count / total for term, count in counter.items()}
    if self.sublinear_tf:
        tf = {term: 1 + math.log(freq) for term, freq in tf.items()}
    return tf
```

**IDF 计算**：
```python
def _compute_idf(self, documents):
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

**归一化**：
```python
def _normalize(self, vector, norm):
    if norm == "l2":
        norm_value = math.sqrt(sum(x * x for x in vector))
        return [x / norm_value for x in vector]
    elif norm == "l1":
        norm_value = sum(abs(x) for x in vector)
        return [x / norm_value for x in vector]
    return vector
```

### 2.3 参数设计

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_features | int/None | None | 最大特征数 |
| min_df | float/int | 1 | 最小文档频率 |
| max_df | float/int | 1.0 | 最大文档频率 |
| norm | str/None | 'l2' | 归一化方式 |
| use_idf | bool | True | 是否使用 IDF |
| smooth_idf | bool | True | 是否平滑 IDF |
| sublinear_tf | bool | False | 是否使用次线性 TF |

## 3. 朴素贝叶斯分类器设计

### 3.1 类设计

```python
class NaiveBayesClassifier:
    """朴素贝叶斯分类器"""

    def __init__(self, alpha, model_type):
        """初始化参数"""

    def fit(self, X, y):
        """训练分类器"""

    def predict(self, X):
        """预测类别"""

    def predict_proba(self, X):
        """预测概率"""

    def score(self, X, y):
        """计算准确率"""
```

### 3.2 多项式朴素贝叶斯

**训练过程**：
```python
def _compute_multinomial_probs(self, X, y):
    # 统计每个类的特征计数
    feature_counts = defaultdict(lambda: [0.0] * n_features)
    class_counts = Counter()

    for features, label in zip(X, y):
        class_counts[label] += 1
        for j, value in enumerate(features):
            feature_counts[label][j] += value

    # 计算对数概率
    for cls in self.classes_:
        # 先验概率: P(y)
        self.class_log_prior_[cls] = math.log(class_counts[cls] / n_samples)

        # 条件概率: P(x|y)
        total_count = sum(feature_counts[cls]) + self.alpha * n_features
        self.feature_log_prob_[cls] = [
            math.log((feature_counts[cls][j] + self.alpha) / total_count)
            for j in range(n_features)
        ]
```

**预测过程**：
```python
def _predict_multinomial_single(self, x):
    best_class = None
    best_score = float("-inf")

    for cls in self.classes_:
        score = self.class_log_prior_[cls]
        for j, value in enumerate(x):
            if value != 0:
                score += value * self.feature_log_prob_[cls][j]

        if score > best_score:
            best_score = score
            best_class = cls

    return best_class
```

### 3.3 高斯朴素贝叶斯

**训练过程**：
```python
def _compute_gaussian_probs(self, X, y):
    # 按类别分组
    class_samples = defaultdict(list)
    for features, label in zip(X, y):
        class_samples[label].append(features)

    # 计算每个类的均值和方差
    for cls in self.classes_:
        samples = class_samples[cls]
        n_class = len(samples)

        # 均值
        mean = [sum(s[j] for s in samples) / n_class for j in range(n_features)]
        self.theta_[cls] = mean

        # 方差
        variance = [
            sum((s[j] - mean[j]) ** 2 for s in samples) / n_class
            for j in range(n_features)
        ]
        self.sigma_[cls] = variance
```

**预测过程**：
```python
def _predict_gaussian_single(self, x):
    best_class = None
    best_score = float("-inf")

    for cls in self.classes_:
        score = self.class_log_prior_[cls]
        for j, value in enumerate(x):
            mean = self.theta_[cls][j]
            variance = self.sigma_[cls][j]
            score -= 0.5 * math.log(2 * math.pi * variance)
            score -= 0.5 * ((value - mean) ** 2) / variance

        if score > best_score:
            best_score = score
            best_class = cls

    return best_class
```

### 3.4 拉普拉斯平滑

**问题**：如果某个特征在某个类别中从未出现，概率会为 0。

**解决方案**：添加平滑参数 α。

```python
# 无平滑
P(x|y) = count(x, y) / count(y)

# 拉普拉斯平滑 (α = 1)
P(x|y) = (count(x, y) + α) / (count(y) + α * n_features)
```

## 4. 文本分类器设计

### 4.1 类设计

```python
class TextClassifier:
    """文本分类管道"""

    def __init__(self, max_features, alpha, norm, use_idf, sublinear_tf):
        """初始化组件"""

    def fit(self, texts, labels):
        """训练分类器"""

    def predict(self, texts):
        """预测类别"""

    def predict_proba(self, texts):
        """预测概率"""

    def score(self, texts, labels):
        """计算准确率"""

    def get_top_features(self, n):
        """获取每个类的顶级特征"""
```

### 4.2 管道流程

```python
def fit(self, texts, labels):
    # 1. 文本向量化
    X = self.vectorizer.fit_transform(texts)

    # 2. 训练分类器
    self.classifier.fit(X, labels)

def predict(self, texts):
    # 1. 文本向量化
    X = self.vectorizer.transform(texts)

    # 2. 预测类别
    return self.classifier.predict(X)
```

## 5. 接口设计

### 5.1 一致性设计

所有组件遵循一致的接口模式：

```python
# 训练接口
component.fit(X, y)

# 预测接口
predictions = component.predict(X)

# 概率接口
probabilities = component.predict_proba(X)

# 评估接口
score = component.score(X, y)

# 参数接口
params = component.get_params()
```

### 5.2 错误处理

```python
# 未训练时调用预测
if not self.is_fitted:
    raise RuntimeError("Classifier has not been fitted. Call fit() first.")

# 参数不匹配
if len(texts) != len(labels):
    raise ValueError("texts and labels must have the same length")
```

### 5.3 链式调用

```python
# 支持链式调用
classifier = TextClassifier()
classifier.fit(texts, labels)  # 返回 self
```

## 6. 数据流设计

### 6.1 训练数据流

```
输入: texts = ["I love this", "I hate this"]
      labels = ["positive", "negative"]

1. TFIDFVectorizer.fit(texts)
   - 分词: [["i", "love", "this"], ["i", "hate", "this"]]
   - 构建词汇表: {"i": 0, "love": 1, "this": 2, "hate": 3}
   - 计算 IDF: {"i": 1.0, "love": 1.405, "this": 1.0, "hate": 1.405}

2. TFIDFVectorizer.transform(texts)
   - 计算 TF-IDF 矩阵:
     [[0.333 * 1.0, 0.333 * 1.405, 0.333 * 1.0, 0],
      [0.333 * 1.0, 0, 0.333 * 1.0, 0.333 * 1.405]]

3. NaiveBayesClassifier.fit(X, y)
   - 计算先验概率: P(positive) = 0.5, P(negative) = 0.5
   - 计算条件概率: P(x|positive), P(x|negative)
```

### 6.2 预测数据流

```
输入: text = "I love this"

1. TFIDFVectorizer.transform([text])
   - 分词: ["i", "love", "this"]
   - 计算 TF-IDF: [0.333 * 1.0, 0.333 * 1.405, 0.333 * 1.0, 0]

2. NaiveBayesClassifier.predict(X)
   - 计算 P(positive|X) ∝ P(X|positive) * P(positive)
   - 计算 P(negative|X) ∝ P(X|negative) * P(negative)
   - 返回 argmax

输出: "positive"
```

## 7. 性能考虑

### 7.1 时间复杂度

| 操作 | 复杂度 |
|------|--------|
| TF-IDF fit | O(D × V) |
| TF-IDF transform | O(D × V) |
| 朴素贝叶斯 fit | O(N × F) |
| 朴素贝叶斯 predict | O(C × F) |

其中：
- D = 文档数
- V = 词汇表大小
- N = 训练样本数
- F = 特征数
- C = 类别数

### 7.2 空间复杂度

| 组件 | 复杂度 |
|------|--------|
| 词汇表 | O(V) |
| IDF 权重 | O(V) |
| 类别概率 | O(C) |
| 特征概率 | O(C × V) |

### 7.3 优化策略

1. **稀疏矩阵**：对于高维稀疏特征，使用稀疏矩阵存储
2. **特征选择**：通过 max_features 限制特征数
3. **文档频率过滤**：通过 min_df 和 max_df 过滤低频/高频词
4. **对数空间计算**：使用对数概率避免数值下溢

## 8. 扩展性设计

### 8.1 支持新的向量化方法

```python
class Word2VecVectorizer:
    """词嵌入向量化器"""

    def fit(self, documents):
        # 训练 Word2Vec 模型
        pass

    def transform(self, documents):
        # 将文档转换为词嵌入向量
        pass
```

### 8.2 支持新的分类器

```python
class LogisticRegressionClassifier:
    """逻辑回归分类器"""

    def fit(self, X, y):
        # 训练逻辑回归模型
        pass

    def predict(self, X):
        # 预测类别
        pass
```

### 8.3 支持管道组合

```python
class TextClassifier:
    def __init__(self, vectorizer, classifier):
        self.vectorizer = vectorizer
        self.classifier = classifier
```

## 9. 测试策略

### 9.1 单元测试

- TF-IDF 向量化器测试
- 朴素贝叶斯分类器测试
- 文本分类器测试

### 9.2 集成测试

- 完整管道测试
- 端到端测试

### 9.3 边界测试

- 空输入
- 单个样本
- 极端值

## 10. 参考文献

1. Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval.
2. Jurafsky, D., & Martin, J. H. (2023). Speech and Language Processing.
3. scikit-learn 文档: https://scikit-learn.org/
