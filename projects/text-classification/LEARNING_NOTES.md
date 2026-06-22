# 学习笔记：文本分类

## 1. 项目目标

从零实现文本分类系统，深入理解文本表示和分类算法的核心原理：
- 理解文本表示
- 掌握 TF-IDF
- 学会朴素贝叶斯分类

## 2. 核心概念

### 2.1 什么是文本分类？

文本分类是自然语言处理（NLP）中最基础和最重要的任务之一。它的目标是将文本文档自动分配到一个或多个预定义的类别中。

**核心流程**：
```
文本 → 特征提取 → 分类器 → 类别
```

**应用场景**：
- 情感分析：判断文本的情感倾向
- 垃圾邮件检测：识别垃圾邮件
- 新闻分类：将新闻分到不同类别
- 语言识别：识别文本的语言
- 主题分类：识别文本主题

### 2.2 文本表示方法

**词袋模型 (Bag of Words)**：
- 忽略词序，只关注词频
- 简单直观，但丢失词序信息

**TF-IDF (Term Frequency-Inverse Document Frequency)**：
- 综合考虑词频和文档频率
- 既考虑词的重要性，又考虑词的区分能力
- 是文本分类中最常用的特征提取方法

**词嵌入 (Word Embeddings)**：
- 将词映射到低维稠密向量空间
- 捕捉语义相似性
- 需要大量训练数据

**预训练语言模型**：
- 使用大规模预训练模型提取特征
- 强大的语义理解能力
- 计算资源需求大

### 2.3 TF-IDF 原理

**核心思想**：
- **TF (词频)**：一个词在文档中出现的频率越高，它对文档越重要
- **IDF (逆文档频率)**：一个词在越少的文档中出现，它对区分文档越重要
- **TF-IDF**：综合考虑词频和文档频率

**公式**：
```
TF(t, d) = 词t在文档d中出现的次数 / 文档d的总词数
IDF(t) = log(文档总数 / 包含词t的文档数)
TF-IDF(t, d) = TF(t, d) × IDF(t)
```

**示例**：
```python
文档1: "the cat sat on the mat"
文档2: "the dog sat on the log"

TF("the", 文档1) = 2/6 = 0.333
IDF("the") = log(2/2) = 0  # "the"出现在所有文档中
TF-IDF("the", 文档1) = 0.333 × 0 = 0

TF("cat", 文档1) = 1/6 = 0.167
IDF("cat") = log(2/1) = 0.693  # "cat"只出现在1个文档中
TF-IDF("cat", 文档1) = 0.167 × 0.693 = 0.116
```

**为什么 TF-IDF 有效？**
- 常见词（如 "the", "a", "is"）的 IDF 值低，权重被降低
- 罕见词（如专业术语）的 IDF 值高，权重被提升
- 综合考虑词的重要性和区分能力

### 2.4 朴素贝叶斯原理

**贝叶斯定理**：
```
P(y|X) = P(X|y) × P(y) / P(X)
```

其中：
- P(y|X) 是后验概率：给定特征 X，类别 y 的概率
- P(X|y) 是似然：给定类别 y，特征 X 的概率
- P(y) 是先验概率：类别 y 的概率
- P(X) 是证据：特征 X 的概率

**朴素假设**：
```
P(X|y) = P(x₁|y) × P(x₂|y) × ... × P(xₙ|y)
```

假设特征之间条件独立，给定类别后，每个特征的概率可以单独计算。

**为什么叫"朴素"？**
- 因为特征独立性假设在现实中往往不成立
- 但这个假设大大简化了计算
- 实践中，即使假设不成立，朴素贝叶斯仍然表现良好

**拉普拉斯平滑**：
```python
# 无平滑
P(x|y) = count(x, y) / count(y)

# 拉普拉斯平滑 (α = 1)
P(x|y) = (count(x, y) + α) / (count(y) + α × n_features)
```

平滑的目的是避免零概率问题：如果某个特征在某个类别中从未出现，概率会为 0，导致整个乘积为 0。

## 3. 实现细节

### 3.1 TF-IDF 向量化器

**分词器**：
```python
def _tokenize(self, text):
    # 转换为小写
    text = text.lower()
    # 移除基本标点
    for char in ".,!?;:()[]{}\"'":
        text = text.replace(char, " ")
    # 按空格分割
    return text.split()
```

**TF 计算**：
```python
def _compute_tf(self, tokens):
    counter = Counter(tokens)
    total = len(tokens)
    tf = {term: count / total for term, count in counter.items()}
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
        idf[term] = math.log((1 + n_documents) / (1 + freq)) + 1
    return idf
```

**归一化**：
```python
# L2 归一化
norm = math.sqrt(sum(x * x for x in vector))
vector = [x / norm for x in vector]

# L1 归一化
norm = sum(abs(x) for x in vector)
vector = [x / norm for x in vector]
```

### 3.2 朴素贝叶斯分类器

**多项式朴素贝叶斯**：
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

**预测**：
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

**概率预测**：
```python
def predict_proba(self, X):
    for x in X:
        # 计算每个类的对数概率
        log_probs = {}
        for cls in self.classes_:
            score = self.class_log_prior_[cls]
            for j, value in enumerate(x):
                if value != 0:
                    score += value * self.feature_log_prob_[cls][j]
            log_probs[cls] = score

        # 使用 log-sum-exp 技巧转换为概率
        max_log_prob = max(log_probs.values())
        exp_probs = {
            cls: math.exp(lp - max_log_prob)
            for cls, lp in log_probs.items()
        }
        total = sum(exp_probs.values())
        probs = {cls: ep / total for cls, ep in exp_probs.items()}
```

### 3.3 文本分类管道

**训练流程**：
```python
def fit(self, texts, labels):
    # 1. 文本向量化
    X = self.vectorizer.fit_transform(texts)

    # 2. 训练分类器
    self.classifier.fit(X, labels)
    self.is_fitted = True
```

**预测流程**：
```python
def predict(self, texts):
    # 1. 文本向量化
    X = self.vectorizer.transform(texts)

    # 2. 预测类别
    return self.classifier.predict(X)
```

## 4. 关键收获

### 4.1 TF-IDF 的力量

- **简单有效**：TF-IDF 是一种简单但有效的文本特征提取方法
- **考虑词的区分能力**：通过 IDF 降低常见词的权重，提升罕见词的权重
- **广泛使用**：在信息检索和文本分类中广泛应用

### 4.2 朴素贝叶斯的优势

- **训练速度快**：只需要统计频率，不需要迭代优化
- **预测速度快**：只需要计算概率乘积
- **适合高维数据**：对特征数量不敏感
- **对小样本效果好**：即使训练数据很少，也能有不错的效果

### 4.3 朴素假设的局限

- **特征独立性假设**：在现实中，特征往往是相关的
- **但在实践中有效**：即使假设不成立，朴素贝叶斯仍然表现良好
- **解释**：分类只需要知道哪个类别的概率最大，不需要精确的概率值

### 4.4 对数空间计算

**问题**：概率相乘可能导致数值下溢

**解决方案**：使用对数概率

```python
# 不好的方式
prob = p1 * p2 * p3 * ...  # 可能下溢

# 好的方式
log_prob = log_p1 + log_p2 + log_p3 + ...  # 稳定
```

**log-sum-exp 技巧**：
```python
# 计算 softmax 时避免溢出
max_value = max(values)
exp_values = [math.exp(x - max_value) for x in values]
total = sum(exp_values)
probs = [x / total for x in exp_values]
```

## 5. 实际应用

### 5.1 情感分析

```python
texts = [
    "This movie is absolutely wonderful and amazing",
    "I really enjoyed this film, it was fantastic",
    "This is the worst movie I have ever seen",
    "Terrible acting and a boring storyline",
]
labels = ["positive", "positive", "negative", "negative"]

classifier = TextClassifier()
classifier.fit(texts, labels)

# 预测
predictions = classifier.predict(["This film was amazing and I loved it"])
# 输出: ["positive"]
```

### 5.2 主题分类

```python
texts = [
    "The stock market crashed today",
    "Apple released a new iPhone",
    "The football team won the game",
]
labels = ["finance", "technology", "sports"]

classifier = TextClassifier()
classifier.fit(texts, labels)

# 预测
predictions = classifier.predict(["The Dow Jones index fell sharply"])
# 输出: ["finance"]
```

### 5.3 垃圾邮件检测

```python
texts = [
    "You have won a million dollars!",
    "Hey, are you coming to the party?",
]
labels = ["spam", "ham"]

classifier = TextClassifier()
classifier.fit(texts, labels)

# 预测
predictions = classifier.predict(["You have been selected to win a prize!"])
# 输出: ["spam"]
```

## 6. 超参数调优

### 6.1 TF-IDF 超参数

| 超参数 | 作用 | 建议值 |
|--------|------|--------|
| max_features | 最大特征数 | 10000-50000 |
| min_df | 最小文档频率 | 2-5 |
| max_df | 最大文档频率 | 0.9-0.95 |
| norm | 归一化方式 | 'l2' |
| use_idf | 是否使用 IDF | True |
| sublinear_tf | 是否使用次线性 TF | False |

### 6.2 朴素贝叶斯超参数

| 超参数 | 作用 | 建议值 |
|--------|------|--------|
| alpha | 平滑参数 | 0.1-1.0 |
| model_type | 模型类型 | 'multinomial' |

### 6.3 调优策略

- **max_features**：限制特征数量，减少过拟合
- **min_df**：过滤低频词，减少噪声
- **max_df**：过滤高频词，减少常见词的影响
- **alpha**：平滑参数，避免零概率

## 7. 与其他方法的对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| TF-IDF + 朴素贝叶斯 | 简单快速 | 忽略词序 | 小规模数据 |
| 词袋模型 + 逻辑回归 | 简单有效 | 忽略词序 | 中等规模数据 |
| 词嵌入 + SVM | 捕捉语义 | 需要大量数据 | 中大规模数据 |
| 预训练模型 | 强大语义理解 | 计算资源大 | 高精度要求 |

## 8. 数学基础

### 8.1 TF-IDF 公式

**TF (词频)**：
```
TF(t, d) = count(t, d) / |d|
```

**IDF (逆文档频率)**：
```
IDF(t) = log(N / df(t)) + 1
```

**TF-IDF**：
```
TF-IDF(t, d) = TF(t, d) × IDF(t)
```

### 8.2 贝叶斯定理

```
P(y|X) = P(X|y) × P(y) / P(X)
```

**朴素假设**：
```
P(X|y) = ∏ P(xᵢ|y)
```

**分类规则**：
```
ŷ = argmax_y P(y) × ∏ P(xᵢ|y)
```

### 8.3 拉普拉斯平滑

```
P(xᵢ|y) = (count(xᵢ, y) + α) / (count(y) + α × |V|)
```

其中 |V| 是词汇表大小。

## 9. 调试经验

### 9.1 常见问题

1. **准确率低**
   - 检查训练数据质量
   - 增加训练数据
   - 调整超参数

2. **过拟合**
   - 减少特征数量
   - 增加正则化
   - 使用交叉验证

3. **数值下溢**
   - 使用对数概率
   - 使用 log-sum-exp 技巧

### 9.2 调试技巧

- 打印词汇表和特征名称
- 检查 TF-IDF 矩阵
- 查看每个类的顶级特征
- 使用小数据集验证

## 10. 进一步学习

### 10.1 相关算法

- **逻辑回归**：线性模型，输出概率
- **支持向量机**：最大间隔分类
- **随机森林**：集成学习方法
- **深度学习**：神经网络方法

### 10.2 深入主题

- 词嵌入 (Word2Vec, GloVe)
- 预训练语言模型 (BERT, GPT)
- 注意力机制
- Transformer 架构

### 10.3 参考资料

- Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval.
- Jurafsky, D., & Martin, J. H. (2023). Speech and Language Processing.
- scikit-learn 文档: https://scikit-learn.org/
