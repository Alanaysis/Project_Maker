# 03 - 实现文档：文本分类系统

## 1. 实现概述

本文档详细描述了文本分类系统的实现细节，包括特征提取、传统分类器、深度学习模型、评估指标和实际应用。

### 1.1 技术栈

- **Python 3.8+**
- **NumPy**: 数值计算
- **collections.Counter**: 计数器
- **math**: 数学函数

### 1.2 模块结构

```
src/
├── __init__.py              # 包初始化
├── bow.py                   # 词袋模型
├── tfidf.py                 # TF-IDF向量化器
├── ngram.py                 # N-gram特征提取
├── naive_bayes.py           # 朴素贝叶斯分类器
├── logistic_regression.py   # 逻辑回归分类器
├── svm_classifier.py        # SVM分类器
├── deep_learning.py         # 深度学习模型
├── evaluation.py            # 评估指标
├── applications.py          # 实际应用
└── text_classifier.py       # 文本分类管道
```

## 2. 特征提取实现

### 2.1 BagOfWordsVectorizer (bow.py)

**核心实现**：

```python
class BagOfWordsVectorizer:
    def _tokenize(self, text: str) -> List[str]:
        """分词：小写化 + 去标点 + 空格分割"""
        text = text.lower()
        for char in ".,!?;:()[]{}\"'":
            text = text.replace(char, " ")
        return text.split()

    def fit(self, documents: List[str]) -> Self:
        """学习词汇表"""
        # 1. 分词
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        # 2. 计算文档频率
        df = Counter()
        for doc in tokenized_docs:
            for term in set(doc):
                df[term] += 1
        # 3. 过滤低频/高频词
        valid_terms = self._apply_df_filter(df, len(documents))
        # 4. 构建词汇表
        self.vocabulary_ = {term: idx for idx, term in enumerate(sorted(valid_terms))}

    def transform(self, documents: List[str]) -> List[List[int]]:
        """转换文档为词频向量"""
        result = []
        for doc in documents:
            tokens = self._tokenize(doc)
            counter = Counter(tokens)
            vector = [0] * len(self.vocabulary_)
            for term, count in counter.items():
                if term in self.vocabulary_:
                    vector[self.vocabulary_[term]] = count
            result.append(vector)
        return result
```

**关键点**：
- 使用Counter进行高效计数
- 支持binary模式（0/1）
- 支持min_df/max_df过滤

### 2.2 TFIDFVectorizer (tfidf.py)

**核心实现**：

```python
class TFIDFVectorizer:
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """计算词频"""
        counter = Counter(tokens)
        total = len(tokens)
        return {term: count / total for term, count in counter.items()}

    def _compute_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """计算逆文档频率"""
        n_documents = len(documents)
        df = Counter()
        for doc in documents:
            for term in set(doc):
                df[term] += 1

        idf = {}
        for term, freq in df.items():
            if self.smooth_idf:
                idf[term] = math.log((1 + n_documents) / (1 + freq)) + 1
            else:
                idf[term] = math.log(n_documents / freq) + 1
        return idf

    def transform(self, documents: List[str]) -> List[List[float]]:
        """计算TF-IDF向量"""
        result = []
        for doc in documents:
            tokens = self._tokenize(doc)
            tf = self._compute_tf(tokens)
            vector = [0.0] * len(self.vocabulary_)
            for term, tf_value in tf.items():
                if term in self.vocabulary_:
                    idx = self.vocabulary_[term]
                    vector[idx] = tf_value * self.idf_[idx]
            # L2归一化
            if self.norm == "l2":
                norm = math.sqrt(sum(x * x for x in vector))
                if norm > 0:
                    vector = [x / norm for x in vector]
            result.append(vector)
        return result
```

**关键点**：
- 支持平滑IDF（smooth_idf）
- 支持次线性TF（sublinear_tf）
- 支持L1/L2归一化

### 2.3 NGramVectorizer (ngram.py)

**核心实现**：

```python
class NGramVectorizer:
    def _generate_ngrams(self, tokens: List[str]) -> List[str]:
        """生成N-gram"""
        ngrams = []
        min_n, max_n = self.ngram_range
        for n in range(min_n, max_n + 1):
            for i in range(len(tokens) - n + 1):
                ngram = " ".join(tokens[i : i + n])
                ngrams.append(ngram)
        return ngrams

    def _generate_char_ngrams(self, text: str) -> List[str]:
        """生成字符N-gram"""
        text = text.lower()
        ngrams = []
        min_n, max_n = self.ngram_range
        for n in range(min_n, max_n + 1):
            for i in range(len(text) - n + 1):
                ngrams.append(text[i : i + n])
        return ngrams
```

**关键点**：
- 支持词级和字符级N-gram
- 可配置N的范围
- 自动处理边界情况

## 3. 传统分类器实现

### 3.1 NaiveBayesClassifier (naive_bayes.py)

**核心实现**：

```python
class NaiveBayesClassifier:
    def _compute_multinomial_probs(self, X, y):
        """计算多项式朴素贝叶斯概率"""
        # 计算每个类的特征计数
        feature_counts = defaultdict(lambda: [0.0] * n_features)
        class_counts = Counter()

        for features, label in zip(X, y):
            class_counts[label] += 1
            for j, value in enumerate(features):
                feature_counts[label][j] += value

        # 计算对数概率（带平滑）
        for cls in self.classes_:
            self.class_log_prior_[cls] = math.log(class_counts[cls] / n_samples)
            total_count = sum(feature_counts[cls]) + self.alpha * n_features
            self.feature_log_prob_[cls] = [
                math.log((feature_counts[cls][j] + self.alpha) / total_count)
                for j in range(n_features)
            ]

    def predict(self, X):
        """预测类别"""
        predictions = []
        for x in X:
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
            predictions.append(best_class)
        return predictions
```

**关键点**：
- 使用对数概率避免下溢
- 拉普拉斯平滑处理零概率
- 支持多项式和高斯变体

### 3.2 LogisticRegressionClassifier (logistic_regression.py)

**核心实现**：

```python
class LogisticRegressionClassifier:
    def _sigmoid(self, x):
        """Sigmoid激活函数"""
        x = max(-500, min(500, x))  # 防止溢出
        return 1.0 / (1.0 + math.exp(-x))

    def _compute_gradient(self, X, y_binary, weights, bias):
        """计算梯度"""
        n_samples = len(X)
        dw = [0.0] * len(weights)
        db = 0.0

        for i in range(n_samples):
            # 计算预测值
            z = bias + sum(weights[j] * X[i][j] for j in range(len(weights)))
            pred = self._sigmoid(z)
            error = pred - y_binary[i]

            # 累积梯度
            for j in range(len(weights)):
                dw[j] += error * X[i][j]
            db += error

        # 平均梯度 + L2正则化
        for j in range(len(weights)):
            dw[j] = dw[j] / n_samples + self.regularization * weights[j]
        db = db / n_samples

        return dw, db

    def _fit_binary(self, X, y_binary):
        """梯度下降训练"""
        weights = [0.0] * len(X[0])
        bias = 0.0

        for iteration in range(self.max_iter):
            dw, db = self._compute_gradient(X, y_binary, weights, bias)
            for j in range(len(weights)):
                weights[j] -= self.learning_rate * dw[j]
            bias -= self.learning_rate * db

            # 收敛检查
            if math.sqrt(sum(d * d for d in dw) + db * db) < self.tol:
                break

        return weights, bias
```

**关键点**：
- 使用梯度下降优化
- 支持L2正则化
- 多分类使用One-vs-Rest策略

### 3.3 SVMClassifier (svm_classifier.py)

**核心实现**：

```python
class SVMClassifier:
    def _fit_binary(self, X, y_binary):
        """Pegasos算法训练"""
        weights = [0.0] * len(X[0])
        bias = 0.0

        for t in range(1, self.max_iter + 1):
            eta = 1.0 / (self.learning_rate * t)  # 学习率衰减
            i = (t - 1) % len(X)  # 循环遍历样本

            # 计算决策值
            score = bias + sum(weights[j] * X[i][j] for j in range(len(weights)))

            # Hinge loss更新
            if y_binary[i] * score < 1:
                for j in range(len(weights)):
                    weights[j] = (1 - eta * self.learning_rate) * weights[j] + eta * self.C * y_binary[i] * X[i][j]
                bias += eta * self.C * y_binary[i]
            else:
                for j in range(len(weights)):
                    weights[j] = (1 - eta * self.learning_rate) * weights[j]

        return weights, bias
```

**关键点**：
- 使用Pegasos算法（高效线性SVM）
- 学习率随时间衰减
- 支持多分类（One-vs-Rest）

## 4. 深度学习实现

### 4.1 TextCNN (deep_learning.py)

**核心实现**：

```python
class TextCNN:
    def _conv1d(self, x, filters):
        """1D卷积"""
        seq_len = x.shape[0]
        num_filters, filter_size, _ = filters.shape
        out_len = seq_len - filter_size + 1

        output = np.zeros((num_filters, out_len))
        for i in range(out_len):
            window = x[i : i + filter_size]
            for f in range(num_filters):
                output[f, i] = np.sum(window * filters[f])
        return output

    def forward(self, x):
        """前向传播"""
        embedded = self.embedding.forward(x.reshape(1, -1))[0]

        # 多尺度卷积 + 最大池化
        pooled_outputs = []
        for size in self.filter_sizes:
            conv_out = self._conv1d(embedded, self.filters[size])
            pooled = np.max(conv_out, axis=1)
            pooled_outputs.append(pooled)

        # 拼接 + 全连接
        features = np.concatenate(pooled_outputs)
        logits = np.dot(features, self.fc_weights) + self.fc_bias
        return logits
```

### 4.2 LSTM (deep_learning.py)

**核心实现**：

```python
class LSTMCell:
    def forward(self, x, h_prev, c_prev):
        """单步前向传播"""
        combined = np.vstack([x.reshape(-1, 1), h_prev])

        # 门控计算
        fg = sigmoid(np.dot(self.Wf, combined) + self.bf)  # 遗忘门
        ig = sigmoid(np.dot(self.Wi, combined) + self.bi)  # 输入门
        c_candidate = tanh(np.dot(self.Wc, combined) + self.bc)  # 候选值
        og = sigmoid(np.dot(self.Wo, combined) + self.bo)  # 输出门

        # 状态更新
        c_new = fg * c_prev + ig * c_candidate
        h_new = og * tanh(c_new)

        return h_new, c_new
```

### 4.3 BiLSTM + Attention (deep_learning.py)

**核心实现**：

```python
class BiLSTMAttention:
    def _attention(self, hidden_states):
        """注意力机制"""
        # 计算注意力分数
        scores = np.dot(np.tanh(np.dot(hidden_states, self.W_attention)), self.v_attention)
        scores = scores.flatten()

        # Softmax归一化
        attention_weights = softmax(scores)

        # 加权求和
        context = np.dot(attention_weights, hidden_states)
        return context

    def forward(self, x):
        """前向传播"""
        # 前向LSTM
        forward_states = [...]
        # 后向LSTM
        backward_states = [...]

        # 拼接双向状态
        hidden_states = np.column_stack([forward_states, backward_states])

        # 注意力加权
        context = self._attention(hidden_states)

        # 分类
        logits = np.dot(self.W_out, context.reshape(-1, 1)) + self.b_out
        return logits.flatten()
```

## 5. 评估指标实现

### 5.1 基础指标 (evaluation.py)

```python
def accuracy(y_true, y_pred):
    """准确率"""
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)

def precision(y_true, y_pred, average="macro"):
    """精确率"""
    classes = sorted(set(y_true) | set(y_pred))
    if average == "micro":
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        return tp / len(y_true)
    # macro/weighted平均...

def recall(y_true, y_pred, average="macro"):
    """召回率"""
    # 类似precision实现...

def f1_score(y_true, y_pred, average="macro"):
    """F1分数"""
    p = precision(y_true, y_pred, average)
    r = recall(y_true, y_pred, average)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0
```

### 5.2 混淆矩阵

```python
def confusion_matrix(y_true, y_pred):
    """混淆矩阵"""
    classes = sorted(set(y_true) | set(y_pred))
    matrix = {cls: {c: 0 for c in classes} for cls in classes}
    for true, pred in zip(y_true, y_pred):
        matrix[true][pred] += 1
    return matrix
```

## 6. 应用实现

### 6.1 SentimentAnalyzer (applications.py)

```python
class SentimentAnalyzer:
    def __init__(self, classifier_type="naive_bayes", max_features=5000):
        self.vectorizer = TFIDFVectorizer(max_features=max_features, sublinear_tf=True)
        if classifier_type == "naive_bayes":
            self.classifier = NaiveBayesClassifier(alpha=1.0)
        elif classifier_type == "logistic_regression":
            self.classifier = LogisticRegressionClassifier(learning_rate=0.1)
        elif classifier_type == "svm":
            self.classifier = SVMClassifier(C=1.0)

    def fit(self, texts, labels):
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        return self

    def predict(self, texts):
        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)
```

## 7. 性能优化

### 7.1 计算优化

- 使用NumPy向量化操作
- 避免不必要的Python循环
- 使用对数空间计算避免数值溢出

### 7.2 内存优化

- 稀疏矩阵存储
- 增量学习支持
- 特征选择减少维度

## 8. 测试覆盖

### 8.1 测试文件

```
tests/
├── test_bow.py                # 词袋模型测试
├── test_tfidf.py              # TF-IDF测试
├── test_ngram.py              # N-gram测试
├── test_naive_bayes.py        # 朴素贝叶斯测试
├── test_logistic_regression.py # 逻辑回归测试
├── test_svm.py                # SVM测试
├── test_deep_learning.py      # 深度学习测试
├── test_evaluation.py         # 评估指标测试
├── test_applications.py       # 应用测试
└── test_text_classifier.py    # 管道测试
```

### 8.2 测试类型

- 单元测试：测试单个函数/类
- 集成测试：测试模块间交互
- 边界测试：测试边界条件
