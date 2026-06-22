# 05 - 开发文档：文本分类

## 1. 开发环境

### 1.1 依赖要求

- Python 3.7+
- pytest (测试)
- 无其他外部依赖

### 1.2 项目结构

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
│   ├── __init__.py             # 包初始化
│   ├── tfidf.py                # TF-IDF 向量化器
│   ├── naive_bayes.py          # 朴素贝叶斯分类器
│   └── text_classifier.py      # 文本分类管道
└── tests/
    ├── __init__.py
    ├── test_tfidf.py           # TF-IDF 测试
    ├── test_naive_bayes.py     # 朴素贝叶斯测试
    └── test_text_classifier.py # 文本分类器测试
```

## 2. 开发流程

### 2.1 测试驱动开发 (TDD)

1. **编写测试**：先定义预期行为
2. **运行测试**：确认测试失败
3. **编写代码**：实现功能
4. **运行测试**：确认测试通过
5. **重构**：优化代码

### 2.2 开发步骤

**步骤 1：实现 TF-IDF 向量化器**

```python
# 1. 编写测试
def test_basic_fit_transform():
    documents = ["hello world", "hello python"]
    vectorizer = TFIDFVectorizer()
    result = vectorizer.fit_transform(documents)
    assert len(result) == 2

# 2. 实现功能
class TFIDFVectorizer:
    def fit(self, documents):
        # 实现词汇表构建
        pass

    def transform(self, documents):
        # 实现 TF-IDF 计算
        pass
```

**步骤 2：实现朴素贝叶斯分类器**

```python
# 1. 编写测试
def test_basic_fit_predict():
    X = [[1, 0], [0, 1]]
    y = ["a", "b"]
    clf = NaiveBayesClassifier()
    clf.fit(X, y)
    predictions = clf.predict([[1, 0]])
    assert predictions[0] == "a"

# 2. 实现功能
class NaiveBayesClassifier:
    def fit(self, X, y):
        # 实现概率计算
        pass

    def predict(self, X):
        # 实现预测
        pass
```

**步骤 3：实现文本分类管道**

```python
# 1. 编写测试
def test_basic_pipeline():
    texts = ["I love this", "I hate this"]
    labels = ["positive", "negative"]
    classifier = TextClassifier()
    classifier.fit(texts, labels)
    predictions = classifier.predict(["I love this"])
    assert predictions[0] == "positive"

# 2. 实现功能
class TextClassifier:
    def __init__(self):
        self.vectorizer = TFIDFVectorizer()
        self.classifier = NaiveBayesClassifier()

    def fit(self, texts, labels):
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
```

## 3. 代码规范

### 3.1 命名规范

- **类名**：PascalCase (`TFIDFVectorizer`, `NaiveBayesClassifier`)
- **方法名**：snake_case (`fit_transform`, `predict_proba`)
- **变量名**：snake_case (`feature_names`, `class_log_prior_`)
- **常量**：UPPER_SNAKE_CASE (`MAX_FEATURES`)

### 3.2 文档规范

```python
def fit(self, documents: List[str]) -> "TFIDFVectorizer":
    """
    Learn vocabulary and IDF weights from training documents.

    Parameters
    ----------
    documents : list of str
        Raw text documents.

    Returns
    -------
    self
        Fitted vectorizer.

    Raises
    ------
    ValueError
        If documents is empty.
    """
```

### 3.3 类型注解

```python
from typing import Dict, List, Optional, Tuple

def transform(self, documents: List[str]) -> List[List[float]]:
    """Transform documents to TF-IDF feature vectors."""
    pass
```

### 3.4 错误处理

```python
def predict(self, X: List[List[float]]) -> List[str]:
    """Predict class labels."""
    if not self.classes_:
        raise RuntimeError("Classifier has not been fitted. Call fit() first.")
    # ...
```

## 4. 测试规范

### 4.1 测试命名

```python
def test_basic_fit_transform(self):
    """Test basic fit and transform functionality."""

def test_tf_computation(self):
    """Test term frequency computation."""

def test_predict_before_fit(self):
    """Test that predict raises error before fit."""
```

### 4.2 测试结构

```python
class TestTFIDFVectorizer:
    """Test suite for TFIDFVectorizer."""

    def test_basic_fit_transform(self):
        """Test basic fit and transform functionality."""
        # Arrange
        documents = ["hello world", "hello python"]

        # Act
        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        # Assert
        assert len(result) == 2
        assert len(result[0]) > 0
```

### 4.3 边界测试

```python
def test_empty_document(self):
    """Test with empty document."""
    documents = ["", "hello world"]
    vectorizer = TFIDFVectorizer()
    result = vectorizer.fit_transform(documents)
    assert len(result) == 2

def test_transform_before_fit(self):
    """Test that transform raises error before fit."""
    vectorizer = TFIDFVectorizer()
    with pytest.raises(RuntimeError, match="not been fitted"):
        vectorizer.transform(["test"])
```

## 5. 调试技巧

### 5.1 打印调试

```python
def fit(self, documents):
    print(f"Number of documents: {len(documents)}")
    print(f"Vocabulary size: {len(self.vocabulary_)}")
    print(f"IDF weights: {self.idf_}")
    # ...
```

### 5.2 断言调试

```python
def transform(self, documents):
    assert self.vocabulary_, "Vocabulary is empty"
    assert self.idf_, "IDF weights are empty"
    # ...
```

### 5.3 日志调试

```python
import logging

logger = logging.getLogger(__name__)

def fit(self, documents):
    logger.info(f"Building vocabulary from {len(documents)} documents")
    # ...
    logger.info(f"Vocabulary size: {len(self.vocabulary_)}")
```

## 6. 性能优化

### 6.1 对数空间计算

```python
# 不好的方式
prob = p1 * p2 * p3  # 可能下溢

# 好的方式
log_prob = log_p1 + log_p2 + log_p3  # 稳定
```

### 6.2 log-sum-exp 技巧

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

### 6.3 稀疏特征优化

```python
# 只计算非零特征
for j, value in enumerate(x):
    if value != 0:
        score += value * self.feature_log_prob_[cls][j]
```

## 7. 扩展开发

### 7.1 添加新的向量化方法

```python
class Word2VecVectorizer:
    """词嵌入向量化器"""

    def __init__(self, vector_size=100, window=5, min_count=1):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count

    def fit(self, documents):
        # 训练 Word2Vec 模型
        pass

    def transform(self, documents):
        # 将文档转换为词嵌入向量
        pass
```

### 7.2 添加新的分类器

```python
class LogisticRegressionClassifier:
    """逻辑回归分类器"""

    def __init__(self, learning_rate=0.01, n_iterations=1000):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations

    def fit(self, X, y):
        # 训练逻辑回归模型
        pass

    def predict(self, X):
        # 预测类别
        pass
```

### 7.3 添加新的预处理

```python
class TextPreprocessor:
    """文本预处理器"""

    def __init__(self, remove_stopwords=True, stemming=True):
        self.remove_stopwords = remove_stopwords
        self.stemming = stemming

    def preprocess(self, text):
        # 预处理文本
        pass
```

## 8. 文档维护

### 8.1 README 更新

- 保持 README 简洁
- 包含快速开始示例
- 更新项目结构

### 8.2 学习笔记

- 记录关键概念
- 总结实现细节
- 分享调试经验

### 8.3 API 文档

- 使用 docstring
- 包含参数说明
- 提供使用示例

## 9. 版本控制

### 9.1 Git 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
style: 代码格式
perf: 性能优化
```

### 9.2 分支策略

```
master
  └── feature/tfidf-vectorizer
  └── feature/naive-bayes
  └── fix/bug-fix
```

## 10. 部署发布

### 10.1 打包

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="text-classification",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.7",
)
```

### 10.2 发布

```bash
# 构建
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

## 11. 参考资源

### 11.1 Python 开发

- PEP 8 风格指南
- Python 类型注解
- pytest 官方文档

### 11.2 NLP 资源

- NLTK 文档
- scikit-learn 文档
- 《统计自然语言处理》

### 11.3 机器学习

- 《机器学习》周志华
- 《Pattern Recognition and Machine Learning》
- scikit-learn 用户指南

## 12. 常见问题

### 12.1 测试失败

**问题**：测试失败，但代码看起来正确

**解决**：
1. 检查测试数据是否正确
2. 检查断言条件是否正确
3. 使用 print 调试

### 12.2 性能问题

**问题**：代码运行缓慢

**解决**：
1. 使用 profiling 工具
2. 优化算法复杂度
3. 使用缓存

### 12.3 内存问题

**问题**：内存占用过高

**解决**：
1. 使用稀疏矩阵
2. 分批处理数据
3. 释放不需要的变量

## 13. 总结

本文档提供了文本分类项目的开发指南，包括：

1. 开发环境配置
2. 开发流程规范
3. 代码规范
4. 测试规范
5. 调试技巧
6. 性能优化
7. 扩展开发
8. 文档维护

遵循这些规范可以帮助开发出高质量、可维护的代码。
