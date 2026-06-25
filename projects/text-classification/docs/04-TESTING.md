# 04 - 测试文档：文本分类系统

## 1. 测试策略

### 1.1 测试金字塔

```
        /\
       /  \        E2E测试 (少量)
      /    \       - 完整管道测试
     /------\
    /        \     集成测试 (适量)
   /          \    - 模块间交互测试
  /------------\
 /              \  单元测试 (大量)
/                \ - 单个函数/类测试
```

### 1.2 测试覆盖目标

| 模块 | 目标覆盖率 | 测试文件 |
|------|-----------|----------|
| bow.py | 90%+ | test_bow.py |
| tfidf.py | 90%+ | test_tfidf.py |
| ngram.py | 90%+ | test_ngram.py |
| naive_bayes.py | 90%+ | test_naive_bayes.py |
| logistic_regression.py | 90%+ | test_logistic_regression.py |
| svm_classifier.py | 90%+ | test_svm.py |
| deep_learning.py | 85%+ | test_deep_learning.py |
| evaluation.py | 90%+ | test_evaluation.py |
| applications.py | 85%+ | test_applications.py |
| text_classifier.py | 90%+ | test_text_classifier.py |

## 2. 单元测试

### 2.1 词袋模型测试 (test_bow.py)

```python
class TestBagOfWordsVectorizer:
    def test_init(self):
        """测试初始化"""
        vectorizer = BagOfWordsVectorizer()
        assert vectorizer.max_features is None
        assert vectorizer.binary is False

    def test_tokenize(self):
        """测试分词"""
        vectorizer = BagOfWordsVectorizer()
        tokens = vectorizer._tokenize("Hello, World!")
        assert tokens == ["hello", "world"]

    def test_fit_transform(self):
        """测试拟合和转换"""
        documents = ["the cat sat", "the dog ran"]
        vectorizer = BagOfWordsVectorizer()
        result = vectorizer.fit_transform(documents)
        assert len(result) == 2

    def test_word_counts(self):
        """测试词频计算"""
        documents = ["the cat sat on the cat"]
        vectorizer = BagOfWordsVectorizer()
        result = vectorizer.fit_transform(documents)
        # "the"出现2次
        the_idx = vectorizer.vocabulary_["the"]
        assert result[0][the_idx] == 2

    def test_binary_mode(self):
        """测试二值模式"""
        documents = ["the the the"]
        vectorizer = BagOfWordsVectorizer(binary=True)
        result = vectorizer.fit_transform(documents)
        # 所有计数应为0或1
        assert all(c in [0, 1] for c in result[0])

    def test_max_features(self):
        """测试特征数量限制"""
        documents = ["a b c d e f"]
        vectorizer = BagOfWordsVectorizer(max_features=3)
        vectorizer.fit(documents)
        assert len(vectorizer.vocabulary_) <= 3

    def test_transform_before_fit(self):
        """测试未拟合时转换报错"""
        vectorizer = BagOfWordsVectorizer()
        with pytest.raises(RuntimeError):
            vectorizer.transform(["test"])
```

### 2.2 TF-IDF测试 (test_tfidf.py)

```python
class TestTFIDFVectorizer:
    def test_tf_computation(self):
        """测试TF计算"""
        vectorizer = TFIDFVectorizer()
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        tf = vectorizer._compute_tf(tokens)
        assert abs(tf["the"] - 2/6) < 1e-6

    def test_idf_computation(self):
        """测试IDF计算"""
        documents = [["the", "cat"], ["the", "dog"]]
        vectorizer = TFIDFVectorizer(smooth_idf=True)
        idf = vectorizer._compute_idf(documents)
        # "the"出现在所有文档中，IDF应该较低
        assert idf["the"] < idf["cat"]

    def test_l2_normalization(self):
        """测试L2归一化"""
        documents = ["the cat sat"]
        vectorizer = TFIDFVectorizer(norm="l2")
        result = vectorizer.fit_transform(documents)
        # L2范数应为1
        norm = sum(x * x for x in result[0])
        assert abs(norm - 1.0) < 1e-6

    def test_sublinear_tf(self):
        """测试次线性TF"""
        vectorizer = TFIDFVectorizer(sublinear_tf=True)
        tokens = ["the", "the", "cat"]
        tf = vectorizer._compute_tf(tokens)
        # 次线性TF应该是 1 + log(tf)
        assert tf["the"] == 1 + math.log(2/3)
```

### 2.3 N-gram测试 (test_ngram.py)

```python
class TestNGramVectorizer:
    def test_unigram_generation(self):
        """测试Unigram生成"""
        vectorizer = NGramVectorizer(ngram_range=(1, 1))
        tokens = ["the", "cat", "sat"]
        ngrams = vectorizer._generate_ngrams(tokens)
        assert ngrams == ["the", "cat", "sat"]

    def test_bigram_generation(self):
        """测试Bigram生成"""
        vectorizer = NGramVectorizer(ngram_range=(2, 2))
        tokens = ["the", "cat", "sat"]
        ngrams = vectorizer._generate_ngrams(tokens)
        assert ngrams == ["the cat", "cat sat"]

    def test_combined_ngrams(self):
        """测试组合N-gram"""
        vectorizer = NGramVectorizer(ngram_range=(1, 2))
        tokens = ["the", "cat"]
        ngrams = vectorizer._generate_ngrams(tokens)
        assert "the" in ngrams
        assert "cat" in ngrams
        assert "the cat" in ngrams

    def test_char_ngrams(self):
        """测试字符N-gram"""
        vectorizer = NGramVectorizer(ngram_range=(2, 3), analyzer="char")
        ngrams = vectorizer._generate_char_ngrams("abc")
        assert "ab" in ngrams
        assert "bc" in ngrams
        assert "abc" in ngrams
```

### 2.4 朴素贝叶斯测试 (test_naive_bayes.py)

```python
class TestNaiveBayesClassifier:
    def test_fit_predict(self):
        """测试训练和预测"""
        X = [[1, 0], [0, 1], [1, 0], [0, 1]]
        y = ["a", "b", "a", "b"]

        clf = NaiveBayesClassifier()
        clf.fit(X, y)
        predictions = clf.predict([[1, 0]])
        assert predictions[0] == "a"

    def test_predict_proba(self):
        """测试概率预测"""
        X = [[1, 0], [0, 1]]
        y = ["a", "b"]

        clf = NaiveBayesClassifier()
        clf.fit(X, y)
        probas = clf.predict_proba([[1, 0]])
        assert sum(probas[0].values()) == pytest.approx(1.0)

    def test_laplace_smoothing(self):
        """测试拉普拉斯平滑"""
        clf = NaiveBayesClassifier(alpha=1.0)
        # 即使某个特征在训练集中未出现，也不会有零概率
```

### 2.5 逻辑回归测试 (test_logistic_regression.py)

```python
class TestLogisticRegressionClassifier:
    def test_sigmoid(self):
        """测试Sigmoid函数"""
        clf = LogisticRegressionClassifier()
        assert abs(clf._sigmoid(0) - 0.5) < 1e-6
        assert clf._sigmoid(100) > 0.99
        assert clf._sigmoid(-100) < 0.01

    def test_convergence(self):
        """测试收敛性"""
        X = [[i, 0] for i in range(10)] + [[0, i] for i in range(10)]
        y = ["a"] * 10 + ["b"] * 10

        clf = LogisticRegressionClassifier(max_iter=1000)
        clf.fit(X, y)
        score = clf.score(X, y)
        assert score > 0.9
```

### 2.6 SVM测试 (test_svm.py)

```python
class TestSVMClassifier:
    def test_decision_function(self):
        """测试决策函数"""
        X = [[1, 0], [0, 1]]
        y = ["a", "b"]

        clf = SVMClassifier()
        clf.fit(X, y)
        scores = clf.decision_function([1, 0])
        assert scores["a"] > scores["b"]

    def test_predict_proba(self):
        """测试概率预测"""
        X = [[1, 0], [0, 1]]
        y = ["a", "b"]

        clf = SVMClassifier()
        clf.fit(X, y)
        probas = clf.predict_proba([[1, 0]])
        assert sum(probas[0].values()) == pytest.approx(1.0)
```

### 2.7 深度学习测试 (test_deep_learning.py)

```python
class TestTextCNN:
    def test_forward(self):
        """测试前向传播"""
        model = TextCNN(vocab_size=100, embedding_dim=50, num_classes=3)
        x = np.array([0, 1, 2, 3, 4])
        logits = model.forward(x)
        assert logits.shape == (3,)

    def test_predict_proba(self):
        """测试概率预测"""
        model = TextCNN(vocab_size=100, embedding_dim=50, num_classes=3)
        x = np.array([0, 1, 2, 3, 4])
        proba = model.predict_proba(x)
        assert abs(sum(proba) - 1.0) < 1e-6

class TestBiLSTMAttention:
    def test_attention_weights(self):
        """测试注意力权重"""
        model = BiLSTMAttention(vocab_size=100, embedding_dim=50, num_classes=3)
        x = np.array([0, 1, 2, 3, 4])
        weights = model.get_attention_weights(x)
        assert len(weights) == 5
        assert abs(sum(weights) - 1.0) < 1e-6
```

### 2.8 评估指标测试 (test_evaluation.py)

```python
class TestEvaluationMetrics:
    def test_accuracy_perfect(self):
        """测试完美准确率"""
        y_true = ["a", "b", "c"]
        y_pred = ["a", "b", "c"]
        assert accuracy(y_true, y_pred) == 1.0

    def test_precision_macro(self):
        """测试宏平均精确率"""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]
        p = precision(y_true, y_pred, average="macro")
        assert 0 <= p <= 1

    def test_confusion_matrix(self):
        """测试混淆矩阵"""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]
        matrix = confusion_matrix(y_true, y_pred)
        assert matrix["a"]["a"] == 1
        assert matrix["b"]["b"] == 1
```

### 2.9 应用测试 (test_applications.py)

```python
class TestSentimentAnalyzer:
    def test_fit_predict(self):
        """测试训练和预测"""
        texts, labels = create_sample_sentiment_data()
        analyzer = SentimentAnalyzer()
        analyzer.fit(texts, labels)
        predictions = analyzer.predict(["I love this!"])
        assert predictions[0] in ["positive", "negative"]

    def test_evaluate(self):
        """测试评估"""
        texts, labels = create_sample_sentiment_data()
        analyzer = SentimentAnalyzer()
        analyzer.fit(texts, labels)
        metrics = analyzer.evaluate(texts, labels)
        assert "accuracy" in metrics
```

## 3. 集成测试

### 3.1 管道测试

```python
class TestTextClassifier:
    def test_full_pipeline(self):
        """测试完整管道"""
        texts = ["I love this", "I hate this"]
        labels = ["positive", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)
        predictions = classifier.predict(["I love this"])
        assert predictions[0] == "positive"
```

### 3.2 模块交互测试

```python
def test_vectorizer_classifier_integration():
    """测试向量化器和分类器的集成"""
    documents = ["the cat sat", "the dog ran"]
    labels = ["animal", "animal"]

    # 使用TF-IDF + 朴素贝叶斯
    vectorizer = TFIDFVectorizer()
    X = vectorizer.fit_transform(documents)

    clf = NaiveBayesClassifier()
    clf.fit(X, labels)

    X_test = vectorizer.transform(["a cat"])
    predictions = clf.predict(X_test)
    assert predictions[0] == "animal"
```

## 4. 边界测试

### 4.1 空输入

```python
def test_empty_input():
    """测试空输入处理"""
    vectorizer = BagOfWordsVectorizer()
    result = vectorizer.fit_transform(["", "hello"])
    assert len(result) == 2
    assert sum(result[0]) == 0  # 空文档应全为0
```

### 4.2 单样本

```python
def test_single_sample():
    """测试单样本训练"""
    clf = NaiveBayesClassifier()
    clf.fit([[1, 0]], ["a"])
    predictions = clf.predict([[1, 0]])
    assert predictions[0] == "a"
```

### 4.3 大词汇表

```python
def test_large_vocabulary():
    """测试大词汇表处理"""
    # 生成大量唯一词
    documents = [" ".join([f"word{i}" for i in range(1000)])]
    vectorizer = BagOfWordsVectorizer(max_features=100)
    vectorizer.fit(documents)
    assert len(vectorizer.vocabulary_) == 100
```

## 5. 运行测试

### 5.1 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行并显示覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing
```

### 5.2 运行特定测试

```bash
# 运行特定测试文件
pytest tests/test_bow.py -v

# 运行特定测试类
pytest tests/test_bow.py::TestBagOfWordsVectorizer -v

# 运行特定测试方法
pytest tests/test_bow.py::TestBagOfWordsVectorizer::test_fit -v
```

### 5.3 测试配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 6. 测试数据

### 6.1 样本数据

```python
# 情感分析数据
texts = [
    "I love this movie, it is wonderful!",
    "This is the best film ever.",
    "I hate this movie, it is terrible.",
    "Worst film ever, waste of time.",
]
labels = ["positive", "positive", "negative", "negative"]

# 新闻分类数据
texts = [
    "The team won the championship.",
    "New smartphone released today.",
    "Election results announced.",
]
labels = ["sports", "technology", "politics"]

# 垃圾邮件数据
texts = [
    "Congratulations! You won a prize!",
    "Meeting tomorrow at 3pm.",
]
labels = ["spam", "ham"]
```

### 6.2 数据生成函数

```python
from src.applications import (
    create_sample_sentiment_data,
    create_sample_news_data,
    create_sample_spam_data,
)

texts, labels = create_sample_sentiment_data()
```
