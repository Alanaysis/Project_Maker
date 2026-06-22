# 文本分类 (Text Classification)

从零实现文本分类系统，深入理解文本表示和分类算法的核心原理。

## 学习目标

- **理解文本表示**：掌握如何将文本转换为数值特征向量
- **掌握 TF-IDF**：理解词频-逆文档频率的计算原理和应用
- **学会朴素贝叶斯分类**：理解贝叶斯定理和朴素假设在文本分类中的应用

## 核心循环

```
文本 → 特征提取 → 分类器 → 类别
```

1. **文本**：原始文本数据
2. **特征提取**：使用 TF-IDF 将文本转换为数值特征向量
3. **分类器**：使用朴素贝叶斯算法进行分类
4. **类别**：输出预测的类别标签

## 项目结构

```
text-classification/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── tfidf.py                # TF-IDF 向量化器
│   ├── naive_bayes.py          # 朴素贝叶斯分类器
│   └── text_classifier.py      # 文本分类管道
└── tests/
    ├── __init__.py
    ├── test_tfidf.py           # TF-IDF 测试
    ├── test_naive_bayes.py     # 朴素贝叶斯测试
    └── test_text_classifier.py # 文本分类器测试
```

## 快速开始

### 基本使用

```python
from src import TextClassifier

# 训练数据
texts = [
    "I love this movie, it is great",
    "This movie is excellent and wonderful",
    "I hate this movie, it is terrible",
    "This movie is awful and boring",
]
labels = ["positive", "positive", "negative", "negative"]

# 创建分类器
classifier = TextClassifier()

# 训练
classifier.fit(texts, labels)

# 预测
predictions = classifier.predict([
    "This movie is great and wonderful",
    "This movie is terrible and awful",
])
print(f"预测结果: {predictions}")

# 预测概率
probabilities = classifier.predict_proba(["This movie is great"])
print(f"预测概率: {probabilities}")

# 准确率
accuracy = classifier.score(texts, labels)
print(f"训练准确率: {accuracy:.2%}")

# 获取顶级特征
top_features = classifier.get_top_features(n=5)
print(f"每个类的顶级特征: {top_features}")
```

### 使用 TF-IDF 向量化器

```python
from src import TFIDFVectorizer

# 文档集合
documents = [
    "the cat sat on the mat",
    "the dog sat on the log",
    "cats and dogs are friends",
]

# 创建向量化器
vectorizer = TFIDFVectorizer(
    max_features=100,  # 最大特征数
    min_df=1,          # 最小文档频率
    max_df=1.0,        # 最大文档频率
    norm="l2",         # L2 归一化
    use_idf=True,      # 使用 IDF
    smooth_idf=True,   # 平滑 IDF
)

# 拟合并转换
tfidf_matrix = vectorizer.fit_transform(documents)

# 获取特征名称
feature_names = vectorizer.get_feature_names()
print(f"特征名称: {feature_names}")

# 查看 TF-IDF 矩阵
for i, doc_vector in enumerate(tfidf_matrix):
    print(f"文档 {i}: {doc_vector}")
```

### 使用朴素贝叶斯分类器

```python
from src import NaiveBayesClassifier

# 训练数据
X_train = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
    [1, 0, 0],
]
y_train = ["a", "b", "c", "a"]

# 创建分类器
clf = NaiveBayesClassifier(
    alpha=1.0,           # 拉普拉斯平滑
    model_type="multinomial"  # 多项式模型
)

# 训练
clf.fit(X_train, y_train)

# 预测
predictions = clf.predict([[1, 0, 0]])
print(f"预测结果: {predictions}")

# 预测概率
probabilities = clf.predict_proba([[1, 0, 0]])
print(f"预测概率: {probabilities}")

# 准确率
accuracy = clf.score(X_train, y_train)
print(f"训练准确率: {accuracy:.2%}")
```

## 核心算法

### 1. TF-IDF (Term Frequency-Inverse Document Frequency)

TF-IDF 是一种统计方法，用于评估一个词对一个文档集或一个语料库中的其中一份文档的重要程度。

**公式**：

```
TF(t, d) = 词t在文档d中出现的次数 / 文档d的总词数
IDF(t) = log(文档总数 / 包含词t的文档数)
TF-IDF(t, d) = TF(t, d) × IDF(t)
```

**核心思想**：
- **TF (词频)**：一个词在文档中出现的频率越高，它对文档越重要
- **IDF (逆文档频率)**：一个词在越少的文档中出现，它对区分文档越重要
- **TF-IDF**：综合考虑词频和文档频率，既考虑词的重要性，又考虑词的区分能力

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

### 2. 朴素贝叶斯 (Naive Bayes)

朴素贝叶斯是一种基于贝叶斯定理的分类器，假设特征之间条件独立。

**贝叶斯定理**：

```
P(y|X) = P(X|y) × P(y) / P(X)
```

**朴素假设**：

```
P(X|y) = P(x₁|y) × P(x₂|y) × ... × P(xₙ|y)
```

**优点**：
- 训练和预测速度快
- 适合高维数据
- 对小样本效果好
- 不容易过拟合

**缺点**：
- 特征独立性假设往往不成立
- 对特征相关性敏感

**拉普拉斯平滑**：

```python
# 无平滑
P(x|y) = count(x, y) / count(y)

# 拉普拉斯平滑 (α = 1)
P(x|y) = (count(x, y) + α) / (count(y) + α × n_features)
```

### 3. 文本分类管道

```python
# 训练流程
def fit(texts, labels):
    # 1. 文本向量化
    X = vectorizer.fit_transform(texts)

    # 2. 训练分类器
    classifier.fit(X, labels)

# 预测流程
def predict(texts):
    # 1. 文本向量化
    X = vectorizer.transform(texts)

    # 2. 预测类别
    return classifier.predict(X)
```

## 关键概念

### 文本表示

将文本转换为数值特征向量的方法：

1. **词袋模型 (Bag of Words)**：忽略词序，只关注词频
2. **TF-IDF**：考虑词频和文档频率
3. **词嵌入 (Word Embeddings)**：将词映射到低维稠密向量空间
4. **预训练语言模型**：使用大规模预训练模型提取特征

### 特征工程

1. **N-gram 特征**：考虑连续 N 个词的组合
2. **词性标注特征**：使用词性信息作为特征
3. **命名实体特征**：识别文本中的实体

### 评估指标

1. **准确率 (Accuracy)**：正确预测数 / 总样本数
2. **精确率 (Precision)**：TP / (TP + FP)
3. **召回率 (Recall)**：TP / (TP + FN)
4. **F1 分数**：2 × (Precision × Recall) / (Precision + Recall)

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行 TF-IDF 测试
pytest tests/test_tfidf.py -v

# 运行朴素贝叶斯测试
pytest tests/test_naive_bayes.py -v

# 运行文本分类器测试
pytest tests/test_text_classifier.py -v

# 运行测试并显示覆盖率
pytest tests/ -v --tb=short
```

## 参考资料

- [Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval.](https://nlp.stanford.edu/IR-book/)
- [Jurafsky, D., & Martin, J. H. (2023). Speech and Language Processing.](https://web.stanford.edu/~jurafsky/slp3/)
- [scikit-learn TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [scikit-learn Naive Bayes](https://scikit-learn.org/stable/modules/naive_bayes.html)

## License

This project is for educational purposes.

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
