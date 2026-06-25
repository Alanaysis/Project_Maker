# 05 - 开发文档：文本分类系统

## 1. 开发环境

### 1.1 依赖要求

```
Python >= 3.8
NumPy >= 1.19.0
pytest >= 6.0.0 (测试)
```

### 1.2 安装依赖

```bash
# 基础依赖
pip install numpy

# 测试依赖
pip install pytest pytest-cov
```

### 1.3 项目结构

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
    ├── __init__.py
    ├── test_bow.py
    ├── test_tfidf.py
    ├── test_ngram.py
    ├── test_naive_bayes.py
    ├── test_logistic_regression.py
    ├── test_svm.py
    ├── test_deep_learning.py
    ├── test_evaluation.py
    ├── test_applications.py
    └── test_text_classifier.py
```

## 2. 快速开始

### 2.1 基本使用

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
```

### 2.2 使用不同特征提取器

```python
from src import BagOfWordsVectorizer, TFIDFVectorizer, NGramVectorizer

# 词袋模型
bow = BagOfWordsVectorizer()
X_bow = bow.fit_transform(documents)

# TF-IDF
tfidf = TFIDFVectorizer()
X_tfidf = tfidf.fit_transform(documents)

# N-gram
ngram = NGramVectorizer(ngram_range=(1, 2))
X_ngram = ngram.fit_transform(documents)
```

### 2.3 使用不同分类器

```python
from src import NaiveBayesClassifier, LogisticRegressionClassifier, SVMClassifier

# 朴素贝叶斯
nb = NaiveBayesClassifier(alpha=1.0)
nb.fit(X_train, y_train)

# 逻辑回归
lr = LogisticRegressionClassifier(learning_rate=0.1, max_iter=1000)
lr.fit(X_train, y_train)

# SVM
svm = SVMClassifier(C=1.0, max_iter=1000)
svm.fit(X_train, y_train)
```

### 2.4 使用深度学习模型

```python
from src import TextCNN, LSTMModel, BiLSTMAttention
import numpy as np

# TextCNN
cnn = TextCNN(vocab_size=10000, embedding_dim=128, num_classes=2)
x = np.array([1, 2, 3, 4, 5])
pred = cnn.predict(x)

# LSTM
lstm = LSTMModel(vocab_size=10000, embedding_dim=128, hidden_dim=128, num_classes=2)
pred = lstm.predict(x)

# BiLSTM + Attention
bilstm = BiLSTMAttention(vocab_size=10000, embedding_dim=128, hidden_dim=128, num_classes=2)
pred = bilstm.predict(x)
weights = bilstm.get_attention_weights(x)  # 获取注意力权重
```

### 2.5 使用评估指标

```python
from src import accuracy, precision, recall, f1_score, confusion_matrix, classification_report

y_true = ["positive", "negative", "positive", "negative"]
y_pred = ["positive", "positive", "negative", "negative"]

print(f"准确率: {accuracy(y_true, y_pred):.4f}")
print(f"精确率: {precision(y_true, y_pred):.4f}")
print(f"召回率: {recall(y_true, y_pred):.4f}")
print(f"F1分数: {f1_score(y_true, y_pred):.4f}")

print("\n混淆矩阵:")
print(confusion_matrix(y_true, y_pred))

print("\n分类报告:")
print(classification_report(y_true, y_pred))
```

### 2.6 使用实际应用

```python
from src import SentimentAnalyzer, NewsClassifier, SpamDetector

# 情感分析
sentiment = SentimentAnalyzer(classifier_type="naive_bayes")
sentiment.fit(train_texts, train_labels)
predictions = sentiment.predict(["I love this!"])

# 新闻分类
news = NewsClassifier(classifier_type="logistic_regression")
news.fit(train_texts, train_labels)
predictions = news.predict(["The team won the game."])

# 垃圾邮件检测
spam = SpamDetector(classifier_type="naive_bayes")
spam.fit(train_texts, train_labels)
predictions = spam.predict(["Congratulations! You won!"])
```

## 3. 开发指南

### 3.1 添加新的特征提取器

```python
# src/new_vectorizer.py
class NewVectorizer:
    def __init__(self, param1=default1):
        self.param1 = param1
        self.vocabulary_ = {}
        self.feature_names_ = []

    def fit(self, documents):
        """学习词汇表"""
        # 实现学习逻辑
        return self

    def transform(self, documents):
        """转换文档为特征向量"""
        # 实现转换逻辑
        return result

    def fit_transform(self, documents):
        """拟合并转换"""
        return self.fit(documents).transform(documents)

    def get_feature_names(self):
        """获取特征名称"""
        return self.feature_names_
```

### 3.2 添加新的分类器

```python
# src/new_classifier.py
class NewClassifier:
    def __init__(self, param1=default1):
        self.param1 = param1
        self.classes_ = []

    def fit(self, X, y):
        """训练分类器"""
        self.classes_ = sorted(set(y))
        # 实现训练逻辑
        return self

    def predict(self, X):
        """预测类别"""
        # 实现预测逻辑
        return predictions

    def predict_proba(self, X):
        """预测概率"""
        # 实现概率预测
        return probabilities

    def score(self, X, y):
        """计算准确率"""
        predictions = self.predict(X)
        correct = sum(1 for p, t in zip(predictions, y) if p == t)
        return correct / len(y)

    def get_params(self):
        """获取参数"""
        return {"param1": self.param1}
```

### 3.3 添加新的应用

```python
# src/applications.py
class NewApplication:
    def __init__(self, classifier_type="naive_bayes"):
        self.vectorizer = TFIDFVectorizer(...)
        if classifier_type == "naive_bayes":
            self.classifier = NaiveBayesClassifier(...)
        elif classifier_type == "logistic_regression":
            self.classifier = LogisticRegressionClassifier(...)
        # ...

    def fit(self, texts, labels):
        """训练模型"""
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        return self

    def predict(self, texts):
        """预测"""
        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)

    def evaluate(self, texts, labels):
        """评估"""
        predictions = self.predict(texts)
        return {
            "accuracy": accuracy(labels, predictions),
            "precision": precision(labels, predictions),
            "recall": recall(labels, predictions),
            "f1": f1_score(labels, predictions),
        }
```

## 4. 代码规范

### 4.1 命名规范

- **类名**：PascalCase (如 `NaiveBayesClassifier`)
- **函数名**：snake_case (如 `fit_transform`)
- **变量名**：snake_case (如 `feature_names`)
- **常量**：UPPER_CASE (如 `MAX_FEATURES`)
- **私有属性**：前缀下划线 (如 `_vocabulary`)

### 4.2 文档规范

```python
def function_name(param1: type1, param2: type2) -> return_type:
    """
    简短描述。

    详细描述（如果需要）。

    Parameters
    ----------
    param1 : type1
        参数1描述。
    param2 : type2
        参数2描述。

    Returns
    -------
    return_type
        返回值描述。

    Raises
    ------
    ExceptionType
        异常描述。

    Examples
    --------
    >>> result = function_name(1, 2)
    >>> print(result)
    3
    """
```

### 4.3 类型注解

```python
from typing import Dict, List, Optional, Tuple

def fit(self, X: List[List[float]], y: List[str]) -> "Classifier":
    ...

def predict(self, X: List[List[float]]) -> List[str]:
    ...

def predict_proba(self, X: List[List[float]]) -> List[Dict[str, float]]:
    ...
```

## 5. 测试指南

### 5.1 测试命名

```python
class TestClassName:
    def test_method_name_scenario(self):
        """测试方法名_场景"""
        pass
```

### 5.2 测试结构

```python
def test_function():
    # Arrange - 准备数据
    input_data = [...]

    # Act - 执行操作
    result = function(input_data)

    # Assert - 验证结果
    assert result == expected
```

### 5.3 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_bow.py -v

# 显示覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing
```

## 6. 版本管理

### 6.1 版本号

```python
# src/__init__.py
__version__ = "0.2.0"
```

### 6.2 更新日志

```
## [0.2.0] - 2024-01-01

### Added
- 词袋模型 (BagOfWordsVectorizer)
- N-gram特征提取 (NGramVectorizer)
- 逻辑回归分类器 (LogisticRegressionClassifier)
- SVM分类器 (SVMClassifier)
- 深度学习模型 (TextCNN, LSTM, BiLSTMAttention)
- 评估指标模块 (evaluation.py)
- 实际应用模块 (applications.py)
  - 情感分析 (SentimentAnalyzer)
  - 新闻分类 (NewsClassifier)
  - 垃圾邮件检测 (SpamDetector)

### Changed
- 更新README文档
- 更新所有文档 (01-05)

## [0.1.0] - 2024-01-01

### Added
- TF-IDF向量化器
- 朴素贝叶斯分类器
- 文本分类管道
```

## 7. 部署指南

### 7.1 打包

```bash
# 创建setup.py
# 打包
python setup.py sdist bdist_wheel
```

### 7.2 安装

```bash
# 从源码安装
pip install -e .

# 从打包安装
pip install dist/text_classification-0.2.0.tar.gz
```

## 8. 故障排除

### 8.1 常见问题

**问题**：ImportError: No module named 'src'
```bash
# 解决方案：确保在项目根目录运行
cd projects/text-classification
python -m pytest tests/
```

**问题**：分类器未训练错误
```python
# 解决方案：先调用fit()
classifier.fit(X_train, y_train)
predictions = classifier.predict(X_test)
```

**问题**：维度不匹配错误
```python
# 解决方案：确保训练和测试数据维度一致
vectorizer.fit(train_texts)
X_train = vectorizer.transform(train_texts)
X_test = vectorizer.transform(test_texts)  # 使用transform而不是fit_transform
```

### 8.2 调试技巧

```python
# 打印中间结果
print(f"词汇表大小: {len(vectorizer.vocabulary_)}")
print(f"特征矩阵形状: {len(X)} x {len(X[0])}")
print(f"类别: {classifier.classes_}")

# 使用predict_proba查看概率
probas = classifier.predict_proba(X_test)
for i, proba in enumerate(probas):
    print(f"样本{i}: {proba}")
```

## 9. 扩展阅读

### 9.1 相关项目

- [tokenizer](../tokenizer/) - 中文分词器
- [language-model](../language-model/) - N-gram语言模型
- [random-forest](../random-forest/) - 随机森林

### 9.2 学习资源

- [scikit-learn文档](https://scikit-learn.org/)
- [NLTK文档](https://www.nltk.org/)
- [spaCy文档](https://spacy.io/)
