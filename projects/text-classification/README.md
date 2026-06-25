# 文本分类 (Text Classification)

从零实现文本分类系统，深入理解文本表示、传统分类器和深度学习模型的核心原理。

## 学习目标

- **理解文本表示**：掌握词袋模型、TF-IDF、N-gram等特征提取方法
- **掌握传统分类器**：理解朴素贝叶斯、逻辑回归、SVM的原理和实现
- **学习深度学习**：实现TextCNN、LSTM、BiLSTM+Attention模型
- **学会评估**：掌握准确率、精确率、召回率、F1、混淆矩阵等指标
- **实际应用**：实现情感分析、新闻分类、垃圾邮件检测

## 核心循环

```
文本 → 特征提取 → 分类器 → 评估 → 类别
```

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
│   ├── __init__.py              # 包初始化
│   ├── bow.py                   # 词袋模型
│   ├── tfidf.py                 # TF-IDF向量化器
│   ├── ngram.py                 # N-gram特征提取
│   ├── naive_bayes.py           # 朴素贝叶斯分类器
│   ├── logistic_regression.py   # 逻辑回归分类器
│   ├── svm_classifier.py        # SVM分类器
│   ├── deep_learning.py         # 深度学习模型
│   ├── evaluation.py            # 评估指标
│   ├── applications.py          # 实际应用
│   └── text_classifier.py       # 文本分类管道
└── tests/
    ├── test_bow.py
    ├── test_tfidf.py
    ├── test_ngram.py
    ├── test_naive_bayes.py
    ├── test_logistic_regression.py
    ├── test_svm.py
    ├── test_deep_learning.py
    ├── test_evaluation.py
    └── test_applications.py
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

# 评估
accuracy = classifier.score(texts, labels)
print(f"训练准确率: {accuracy:.2%}")
```

### 使用不同特征提取器

```python
from src import BagOfWordsVectorizer, TFIDFVectorizer, NGramVectorizer

# 词袋模型
bow = BagOfWordsVectorizer(binary=False)
X_bow = bow.fit_transform(documents)

# TF-IDF
tfidf = TFIDFVectorizer(max_features=5000, sublinear_tf=True)
X_tfidf = tfidf.fit_transform(documents)

# N-gram (unigram + bigram)
ngram = NGramVectorizer(ngram_range=(1, 2))
X_ngram = ngram.fit_transform(documents)
```

### 使用不同分类器

```python
from src import NaiveBayesClassifier, LogisticRegressionClassifier, SVMClassifier

# 朴素贝叶斯
nb = NaiveBayesClassifier(alpha=1.0, model_type="multinomial")
nb.fit(X_train, y_train)
predictions = nb.predict(X_test)

# 逻辑回归
lr = LogisticRegressionClassifier(learning_rate=0.1, max_iter=1000)
lr.fit(X_train, y_train)
predictions = lr.predict(X_test)

# SVM
svm = SVMClassifier(C=1.0, max_iter=1000)
svm.fit(X_train, y_train)
predictions = svm.predict(X_test)
```

### 使用深度学习模型

```python
from src import TextCNN, LSTMModel, BiLSTMAttention
import numpy as np

# TextCNN
cnn = TextCNN(vocab_size=10000, embedding_dim=128, num_classes=2)
x = np.array([1, 2, 3, 4, 5])  # 词索引序列
pred = cnn.predict(x)

# LSTM
lstm = LSTMModel(vocab_size=10000, embedding_dim=128, hidden_dim=128, num_classes=2)
pred = lstm.predict(x)

# BiLSTM + Attention
bilstm = BiLSTMAttention(vocab_size=10000, embedding_dim=128, hidden_dim=128, num_classes=2)
pred = bilstm.predict(x)
weights = bilstm.get_attention_weights(x)  # 获取注意力权重
```

### 使用评估指标

```python
from src import accuracy, precision, recall, f1_score, confusion_matrix, classification_report

y_true = ["positive", "negative", "positive", "negative"]
y_pred = ["positive", "positive", "negative", "negative"]

print(f"准确率: {accuracy(y_true, y_pred):.4f}")
print(f"精确率: {precision(y_true, y_pred):.4f}")
print(f"召回率: {recall(y_true, y_pred):.4f}")
print(f"F1分数: {f1_score(y_true, y_pred):.4f}")

print("\n分类报告:")
print(classification_report(y_true, y_pred))
```

### 使用实际应用

```python
from src import SentimentAnalyzer, NewsClassifier, SpamDetector

# 情感分析
sentiment = SentimentAnalyzer(classifier_type="naive_bayes")
sentiment.fit(train_texts, train_labels)
predictions = sentiment.predict(["I love this!"])
metrics = sentiment.evaluate(test_texts, test_labels)

# 新闻分类
news = NewsClassifier(classifier_type="logistic_regression")
news.fit(train_texts, train_labels)
predictions = news.predict(["The team won the game."])

# 垃圾邮件检测
spam = SpamDetector(classifier_type="svm")
spam.fit(train_texts, train_labels)
predictions = spam.detect(["Congratulations! You won!"])
```

## 核心算法

### 1. 特征提取

| 方法 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| 词袋模型 | 词频统计 | 简单高效 | 丢失词序 |
| TF-IDF | 词频×逆文档频率 | 考虑词的重要性 | 高维稀疏 |
| N-gram | 连续N个词 | 捕捉局部词序 | 特征空间大 |

### 2. 传统分类器

| 算法 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 朴素贝叶斯 | 贝叶斯定理+特征独立假设 | 快速、适合高维 | 独立假设不成立 |
| 逻辑回归 | sigmoid函数建模概率 | 输出概率、可解释 | 线性边界 |
| SVM | 最大间隔超平面 | 高维有效 | 大数据慢 |

### 3. 深度学习模型

| 模型 | 架构 | 优点 | 缺点 |
|------|------|------|------|
| TextCNN | 卷积+池化 | 并行高效 | 无法捕捉长依赖 |
| LSTM | 门控循环单元 | 捕捉长依赖 | 顺序计算慢 |
| BiLSTM+Attention | 双向LSTM+注意力 | 上下文+可解释 | 计算复杂 |

### 4. 评估指标

| 指标 | 公式 | 含义 |
|------|------|------|
| 准确率 | (TP+TN)/(TP+TN+FP+FN) | 整体正确率 |
| 精确率 | TP/(TP+FP) | 预测为正中真正为正 |
| 召回率 | TP/(TP+FN) | 真正为正中被预测 |
| F1分数 | 2*P*R/(P+R) | 精确率和召回率调和平均 |

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_bow.py -v
pytest tests/test_tfidf.py -v
pytest tests/test_ngram.py -v
pytest tests/test_naive_bayes.py -v
pytest tests/test_logistic_regression.py -v
pytest tests/test_svm.py -v
pytest tests/test_deep_learning.py -v
pytest tests/test_evaluation.py -v
pytest tests/test_applications.py -v

# 运行测试并显示覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing
```

## 参考资料

- [Manning, C. D., et al. (2008). Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/)
- [Jurafsky, D., & Martin, J. H. (2023). Speech and Language Processing](https://web.stanford.edu/~jurafsky/slp3/)
- [Kim, Y. (2014). Convolutional Neural Networks for Sentence Classification](https://arxiv.org/abs/1408.5882)
- [Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory](https://www.bioinf.jku.at/publications/older/2604.pdf)
- [Yang, Z., et al. (2016). Hierarchical Attention Networks](https://www.cs.cmu.edu/~diyiy/docs/naacl16.pdf)

## License

This project is for educational purposes.

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
