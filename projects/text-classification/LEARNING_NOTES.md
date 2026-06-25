# 学习笔记：文本分类

## 1. 项目目标

从零实现文本分类系统，深入理解文本表示、传统分类器和深度学习模型的核心原理。

### 1.1 学习重点

1. **文本表示**：如何将文本转换为数值特征
2. **传统分类器**：朴素贝叶斯、逻辑回归、SVM的数学原理
3. **深度学习**：TextCNN、LSTM、BiLSTM+Attention的架构设计
4. **评估指标**：准确率、精确率、召回率、F1、混淆矩阵
5. **实际应用**：情感分析、新闻分类、垃圾邮件检测

## 2. 文本表示

### 2.1 词袋模型 (Bag of Words)

**核心思想**：忽略词序，只关注词频

```python
# 示例
文档: "the cat sat on the cat"
词汇表: {the: 0, cat: 1, sat: 2, on: 3}
向量: [2, 2, 1, 1]  # 词频统计
```

**关键实现**：
```python
def _tokenize(self, text):
    text = text.lower()
    for char in ".,!?;:()[]{}\"'":
        text = text.replace(char, " ")
    return text.split()

def transform(self, documents):
    for doc in documents:
        tokens = self._tokenize(doc)
        counter = Counter(tokens)
        vector = [counter.get(term, 0) for term in self.vocabulary_]
```

**学习要点**：
- Counter是高效的计数工具
- 分词是基础步骤
- 词汇表构建决定特征空间

### 2.2 TF-IDF

**核心思想**：综合考虑词频和文档频率

**公式**：
```
TF(t, d) = 词t在文档d中的出现次数 / 文档d的总词数
IDF(t) = log(文档总数 / 包含词t的文档数)
TF-IDF = TF × IDF
```

**关键实现**：
```python
def _compute_tf(self, tokens):
    counter = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counter.items()}

def _compute_idf(self, documents):
    n_documents = len(documents)
    df = Counter()
    for doc in documents:
        for term in set(doc):  # 每个文档只计一次
            df[term] += 1
    return {term: math.log(n_documents / freq) for term, freq in df.items()}
```

**学习要点**：
- IDF惩罚常见词（如"the"）
- 平滑处理避免零除
- 归一化消除文档长度影响

### 2.3 N-gram

**核心思想**：捕捉局部词序信息

```python
# Bigram示例
文本: "the cat sat"
Bigrams: ["the cat", "cat sat"]
```

**关键实现**：
```python
def _generate_ngrams(self, tokens):
    ngrams = []
    min_n, max_n = self.ngram_range
    for n in range(min_n, max_n + 1):
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i : i + n])
            ngrams.append(ngram)
    return ngrams
```

**学习要点**：
- N越大，捕捉的上下文越长
- 特征空间随N指数增长
- 实践中常用unigram+bigram

## 3. 传统分类器

### 3.1 朴素贝叶斯

**数学原理**：
```
P(y|X) = P(X|y) × P(y) / P(X)
       = P(x₁|y) × P(x₂|y) × ... × P(xₙ|y) × P(y) / P(X)
```

**关键实现**：
```python
def _predict_multinomial_single(self, x):
    best_class = None
    best_score = float("-inf")

    for cls in self.classes_:
        score = self.class_log_prior_[cls]  # log P(y)
        for j, value in enumerate(x):
            if value != 0:
                score += value * self.feature_log_prob_[cls][j]  # log P(x|y)

        if score > best_score:
            best_score = score
            best_class = cls

    return best_class
```

**学习要点**：
- 使用对数概率避免下溢
- 拉普拉斯平滑处理零概率
- "朴素"假设：特征条件独立

### 3.2 逻辑回归

**数学原理**：
```
P(y=1|x) = sigmoid(w^T x + b) = 1 / (1 + exp(-(w^T x + b)))

损失函数: L = -1/n Σ[y log(p) + (1-y) log(1-p)]

梯度更新: w = w - α ∇L
```

**关键实现**：
```python
def _sigmoid(self, x):
    x = max(-500, min(500, x))  # 防止溢出
    return 1.0 / (1.0 + math.exp(-x))

def _compute_gradient(self, X, y_binary, weights, bias):
    for i in range(n_samples):
        z = bias + sum(weights[j] * X[i][j] for j in range(n_features))
        pred = self._sigmoid(z)
        error = pred - y_binary[i]

        for j in range(n_features):
            dw[j] += error * X[i][j]
        db += error

    # 添加L2正则化
    for j in range(n_features):
        dw[j] = dw[j] / n_samples + self.regularization * weights[j]

    return dw, db
```

**学习要点**：
- sigmoid将任意实数映射到(0,1)
- 梯度下降是最优化方法
- 正则化防止过拟合

### 3.3 SVM

**数学原理**：
```
目标: 找到最大间隔超平面
min 1/2 ||w||^2 + C Σξᵢ
s.t. yᵢ(w^T xᵢ + b) >= 1 - ξᵢ

Hinge Loss: L = max(0, 1 - yᵢ(w^T xᵢ + b))
```

**关键实现**：
```python
def _fit_binary(self, X, y_binary):
    weights = [0.0] * n_features
    bias = 0.0

    for t in range(1, self.max_iter + 1):
        eta = 1.0 / (self.learning_rate * t)  # 学习率衰减
        i = (t - 1) % n_samples

        score = bias + sum(weights[j] * X[i][j] for j in range(n_features))

        if y_binary[i] * score < 1:  # Hinge loss
            for j in range(n_features):
                weights[j] = (1 - eta * self.learning_rate) * weights[j] + eta * self.C * y_binary[i] * X[i][j]
            bias += eta * self.C * y_binary[i]
        else:
            for j in range(n_features):
                weights[j] = (1 - eta * self.learning_rate) * weights[j]

    return weights, bias
```

**学习要点**：
- Pegasos是高效的线性SVM算法
- 学习率衰减保证收敛
- C参数控制正则化强度

## 4. 深度学习

### 4.1 TextCNN

**架构**：
```
输入 → 嵌入 → 多尺度卷积 → 最大池化 → 全连接 → 输出
```

**关键实现**：
```python
def _conv1d(self, x, filters):
    """1D卷积"""
    output = np.zeros((num_filters, out_len))
    for i in range(out_len):
        window = x[i : i + filter_size]
        for f in range(num_filters):
            output[f, i] = np.sum(window * filters[f])
    return output

def forward(self, x):
    embedded = self.embedding.forward(x)

    # 多尺度卷积
    pooled_outputs = []
    for size in self.filter_sizes:
        conv_out = self._conv1d(embedded, self.filters[size])
        pooled = np.max(conv_out, axis=1)  # 最大池化
        pooled_outputs.append(pooled)

    # 拼接 + 全连接
    features = np.concatenate(pooled_outputs)
    logits = np.dot(features, self.fc_weights) + self.fc_bias
    return logits
```

**学习要点**：
- 不同卷积核捕捉不同n-gram特征
- 最大池化提取最显著特征
- 并行计算效率高

### 4.2 LSTM

**门控机制**：
```
遗忘门: fₜ = σ(Wf · [hₜ₋₁, xₜ])
输入门: iₜ = σ(Wi · [hₜ₋₁, xₜ])
候选值: c̃ₜ = tanh(Wc · [hₜ₋₁, xₜ])
输出门: oₜ = σ(Wo · [hₜ₋₁, xₜ])

细胞状态: cₜ = fₜ * cₜ₋₁ + iₜ * c̃ₜ
隐藏状态: hₜ = oₜ * tanh(cₜ)
```

**关键实现**：
```python
def forward(self, x, h_prev, c_prev):
    combined = np.vstack([x.reshape(-1, 1), h_prev])

    fg = sigmoid(np.dot(self.Wf, combined) + self.bf)  # 遗忘门
    ig = sigmoid(np.dot(self.Wi, combined) + self.bi)  # 输入门
    c_candidate = tanh(np.dot(self.Wc, combined) + self.bc)  # 候选值
    og = sigmoid(np.dot(self.Wo, combined) + self.bo)  # 输出门

    c_new = fg * c_prev + ig * c_candidate
    h_new = og * tanh(c_new)

    return h_new, c_new
```

**学习要点**：
- 遗忘门：决定丢弃什么
- 输入门：决定添加什么
- 输出门：决定输出什么
- 细胞状态：长期记忆

### 4.3 BiLSTM + Attention

**注意力机制**：
```
eᵢ = v^T tanh(W hᵢ)  # 注意力分数
αᵢ = softmax(eᵢ)     # 注意力权重
context = Σ αᵢ hᵢ    # 上下文向量
```

**关键实现**：
```python
def _attention(self, hidden_states):
    # 计算注意力分数
    scores = np.dot(np.tanh(np.dot(hidden_states, self.W_attention)), self.v_attention)
    scores = scores.flatten()

    # Softmax归一化
    attention_weights = softmax(scores)

    # 加权求和
    context = np.dot(attention_weights, hidden_states)
    return context
```

**学习要点**：
- 双向LSTM捕捉前后文
- 注意力机制聚焦重要信息
- 可解释性：查看注意力权重

## 5. 评估指标

### 5.1 混淆矩阵

```
              预测为正    预测为负
实际为正        TP          FN
实际为负        FP          TN
```

### 5.2 指标计算

```python
accuracy = (TP + TN) / (TP + TN + FP + FN)
precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1 = 2 * precision * recall / (precision + recall)
```

### 5.3 多分类平均

- **Macro**: 各类别指标的算术平均
- **Micro**: 汇总所有类别后计算
- **Weighted**: 按类别样本数加权

## 6. 实际应用

### 6.1 情感分析

```python
# 管道：文本 → TF-IDF → 朴素贝叶斯 → 正面/负面
sentiment = SentimentAnalyzer(classifier_type="naive_bayes")
sentiment.fit(texts, labels)
predictions = sentiment.predict(["I love this!"])
```

### 6.2 新闻分类

```python
# 管道：文本 → TF-IDF → 逻辑回归 → 类别
news = NewsClassifier(classifier_type="logistic_regression")
news.fit(texts, labels)
predictions = news.predict(["The team won the game."])
```

### 6.3 垃圾邮件检测

```python
# 管道：文本 → TF-IDF → 朴素贝叶斯 → 垃圾/正常
spam = SpamDetector(classifier_type="naive_bayes")
spam.fit(texts, labels)
predictions = spam.detect(["Congratulations! You won!"])
```

## 7. 关键收获

### 7.1 文本表示

- 词袋模型简单但有效
- TF-IDF是最常用的特征
- N-gram捕捉局部词序

### 7.2 分类器选择

- 朴素贝叶斯：快速、适合基线
- 逻辑回归：输出概率、可解释
- SVM：高维有效、泛化好

### 7.3 深度学习

- TextCNN：并行高效、捕捉局部特征
- LSTM：捕捉长依赖、顺序计算
- BiLSTM+Attention：上下文+可解释

### 7.4 评估重要性

- 准确率可能有误导（类别不平衡）
- 精确率和召回率需要权衡
- F1分数是综合指标

## 8. 下一步学习

1. **预训练模型**：BERT、GPT等
2. **数据增强**：同义词替换、回译
3. **模型集成**：Bagging、Boosting
4. **迁移学习**：预训练+微调
5. **可解释性**：LIME、SHAP
