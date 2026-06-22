# 04 - 测试文档：文本分类

## 1. 测试策略

### 1.1 测试金字塔

```
        /\
       /  \  集成测试 (10%)
      /    \
     /------\  单元测试 (90%)
    /        \
```

- **单元测试**：测试单个组件的功能
- **集成测试**：测试组件之间的协作

### 1.2 测试覆盖率目标

| 组件 | 目标覆盖率 |
|------|-----------|
| TFIDFVectorizer | 95%+ |
| NaiveBayesClassifier | 95%+ |
| TextClassifier | 90%+ |

## 2. TF-IDF 向量化器测试

### 2.1 基本功能测试

```python
def test_basic_fit_transform(self):
    """测试基本的 fit 和 transform 功能"""
    documents = [
        "the cat sat on the mat",
        "the dog sat on the log",
        "cats and dogs are friends",
    ]

    vectorizer = TFIDFVectorizer()
    result = vectorizer.fit_transform(documents)

    # 检查维度
    assert len(result) == 3  # 3 个文档
    assert len(result[0]) > 0  # 有特征

    # 检查词汇表
    assert len(vectorizer.vocabulary_) > 0
    assert len(vectorizer.feature_names_) > 0
```

### 2.2 TF 计算测试

```python
def test_tf_computation(self):
    """测试词频计算"""
    vectorizer = TFIDFVectorizer()

    tokens = ["the", "cat", "sat", "on", "the", "mat"]
    tf = vectorizer._compute_tf(tokens)

    # "the" 出现 2 次，共 6 个词
    assert abs(tf["the"] - 2 / 6) < 1e-6
    # "cat" 出现 1 次
    assert abs(tf["cat"] - 1 / 6) < 1e-6
```

### 2.3 IDF 计算测试

```python
def test_idf_computation(self):
    """测试逆文档频率计算"""
    documents = [
        ["the", "cat", "sat"],
        ["the", "dog", "ran"],
        ["the", "bird", "flew"],
    ]

    vectorizer = TFIDFVectorizer(smooth_idf=True)
    idf = vectorizer._compute_idf(documents)

    # "the" 出现在所有 3 个文档中
    # IDF = log((1 + 3) / (1 + 3)) + 1 = 1.0
    assert abs(idf["the"] - 1.0) < 1e-6

    # "cat" 出现在 1 个文档中
    # IDF = log((1 + 3) / (1 + 1)) + 1 = log(2) + 1
    expected_cat_idf = math.log(4 / 2) + 1
    assert abs(idf["cat"] - expected_cat_idf) < 1e-6
```

### 2.4 归一化测试

```python
def test_l2_normalization(self):
    """测试 L2 归一化"""
    documents = ["hello world", "hello python"]

    vectorizer = TFIDFVectorizer(norm="l2")
    result = vectorizer.fit_transform(documents)

    # 检查每个向量的 L2 范数为 1
    for vector in result:
        norm = math.sqrt(sum(x * x for x in vector))
        assert abs(norm - 1.0) < 1e-6

def test_l1_normalization(self):
    """测试 L1 归一化"""
    documents = ["hello world", "hello python"]

    vectorizer = TFIDFVectorizer(norm="l1")
    result = vectorizer.fit_transform(documents)

    # 检查每个向量的 L1 范数为 1
    for vector in result:
        norm = sum(abs(x) for x in vector)
        assert abs(norm - 1.0) < 1e-6
```

### 2.5 文档频率过滤测试

```python
def test_min_df(self):
    """测试最小文档频率过滤"""
    documents = [
        "the cat sat on the mat",
        "the dog sat on the log",
        "cats and dogs are friends",
    ]

    # min_df=2: 只保留在至少 2 个文档中出现的词
    vectorizer = TFIDFVectorizer(min_df=2)
    vectorizer.fit(documents)

    # "the" 出现在 2 个文档中，应该保留
    assert "the" in vectorizer.vocabulary_
    # "cat" 出现在 1 个文档中，应该被过滤
    assert "cat" not in vectorizer.vocabulary_
```

### 2.6 边界情况测试

```python
def test_empty_document(self):
    """测试空文档"""
    documents = ["", "hello world"]
    vectorizer = TFIDFVectorizer()
    result = vectorizer.fit_transform(documents)

    assert len(result) == 2
    # 空文档应该有零向量
    assert all(x == 0.0 for x in result[0])

def test_transform_before_fit(self):
    """测试在 fit 之前调用 transform"""
    vectorizer = TFIDFVectorizer()

    with pytest.raises(RuntimeError, match="not been fitted"):
        vectorizer.transform(["test document"])
```

## 3. 朴素贝叶斯分类器测试

### 3.1 基本功能测试

```python
def test_basic_fit_predict(self):
    """测试基本的 fit 和 predict 功能"""
    X = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0],
    ]
    y = ["a", "b", "c", "a"]

    clf = NaiveBayesClassifier(alpha=1.0)
    clf.fit(X, y)

    assert len(clf.classes_) == 3
    assert "a" in clf.classes_
    assert "b" in clf.classes_
    assert "c" in clf.classes_
```

### 3.2 预测测试

```python
def test_predict(self):
    """测试预测功能"""
    X_train = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0],
    ]
    y_train = ["a", "b", "c", "a", "b"]

    clf = NaiveBayesClassifier(alpha=1.0)
    clf.fit(X_train, y_train)

    X_test = [
        [1, 0, 0],  # 应该是 "a"
        [0, 1, 0],  # 应该是 "b"
        [0, 0, 1],  # 应该是 "c"
    ]
    predictions = clf.predict(X_test)

    assert len(predictions) == 3
    assert predictions[0] == "a"
    assert predictions[1] == "b"
    assert predictions[2] == "c"
```

### 3.3 概率预测测试

```python
def test_predict_proba(self):
    """测试概率预测"""
    X_train = [
        [1, 0],
        [0, 1],
        [1, 0],
        [0, 1],
    ]
    y_train = ["a", "b", "a", "b"]

    clf = NaiveBayesClassifier(alpha=1.0)
    clf.fit(X_train, y_train)

    X_test = [[1, 0]]
    probas = clf.predict_proba(X_test)

    assert len(probas) == 1
    assert "a" in probas[0]
    assert "b" in probas[0]

    # 概率之和应该为 1
    total = sum(probas[0].values())
    assert abs(total - 1.0) < 1e-6

    # 类别 "a" 应该有更高的概率
    assert probas[0]["a"] > probas[0]["b"]
```

### 3.4 拉普拉斯平滑测试

```python
def test_laplace_smoothing(self):
    """测试拉普拉斯平滑"""
    X_train = [
        [1, 0],
        [0, 1],
    ]
    y_train = ["a", "b"]

    # 使用 alpha=1.0（拉普拉斯平滑）
    clf = NaiveBayesClassifier(alpha=1.0)
    clf.fit(X_train, y_train)

    predictions = clf.predict([[1, 0]])
    assert predictions[0] == "a"

def test_no_smoothing(self):
    """测试无平滑"""
    X_train = [
        [1, 0],
        [0, 1],
    ]
    y_train = ["a", "b"]

    clf = NaiveBayesClassifier(alpha=0.0)
    clf.fit(X_train, y_train)

    predictions = clf.predict([[1, 0]])
    assert predictions[0] == "a"
```

### 3.5 高斯朴素贝叶斯测试

```python
def test_gaussian_basic(self):
    """测试高斯朴素贝叶斯基本功能"""
    X_train = [
        [1.0, 2.0],
        [2.0, 3.0],
        [10.0, 11.0],
        [11.0, 12.0],
    ]
    y_train = ["a", "a", "b", "b"]

    clf = NaiveBayesClassifier(model_type="gaussian")
    clf.fit(X_train, y_train)

    X_test = [
        [1.0, 2.0],  # 接近类别 "a"
        [10.0, 11.0],  # 接近类别 "b"
    ]
    predictions = clf.predict(X_test)

    assert predictions[0] == "a"
    assert predictions[1] == "b"

def test_gaussian_parameters(self):
    """测试高斯参数计算"""
    X_train = [
        [1.0, 2.0],
        [3.0, 4.0],
    ]
    y_train = ["a", "a"]

    clf = NaiveBayesClassifier(model_type="gaussian")
    clf.fit(X_train, y_train)

    # 均值应该是 [2.0, 3.0]
    assert abs(clf.theta_["a"][0] - 2.0) < 1e-6
    assert abs(clf.theta_["a"][1] - 3.0) < 1e-6

    # 方差应该是 [1.0, 1.0]
    assert abs(clf.sigma_["a"][0] - 1.0) < 1e-6
    assert abs(clf.sigma_["a"][1] - 1.0) < 1e-6
```

### 3.6 边界情况测试

```python
def test_predict_before_fit(self):
    """测试在 fit 之前调用 predict"""
    clf = NaiveBayesClassifier()

    with pytest.raises(RuntimeError, match="not been fitted"):
        clf.predict([[1, 0]])

def test_single_class(self):
    """测试单类别情况"""
    X_train = [
        [1, 0],
        [0, 1],
    ]
    y_train = ["a", "a"]

    clf = NaiveBayesClassifier(alpha=1.0)
    clf.fit(X_train, y_train)

    predictions = clf.predict([[1, 0]])
    assert predictions[0] == "a"
```

## 4. 文本分类器测试

### 4.1 基本功能测试

```python
def test_basic_fit_predict(self):
    """测试基本的 fit 和 predict 功能"""
    texts = [
        "I love this movie, it is great",
        "This movie is excellent and wonderful",
        "I hate this movie, it is terrible",
        "This movie is awful and boring",
    ]
    labels = ["positive", "positive", "negative", "negative"]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    assert classifier.is_fitted is True

def test_predict(self):
    """测试预测功能"""
    texts = [
        "I love this movie, it is great",
        "This movie is excellent and wonderful",
        "I hate this movie, it is terrible",
        "This movie is awful and boring",
    ]
    labels = ["positive", "positive", "negative", "negative"]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    test_texts = [
        "This movie is great and wonderful",
        "This movie is terrible and awful",
    ]
    predictions = classifier.predict(test_texts)

    assert len(predictions) == 2
    assert predictions[0] == "positive"
    assert predictions[1] == "negative"
```

### 4.2 概率预测测试

```python
def test_predict_proba(self):
    """测试概率预测"""
    texts = [
        "I love this movie",
        "This movie is great",
        "I hate this movie",
        "This movie is terrible",
    ]
    labels = ["positive", "positive", "negative", "negative"]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    probas = classifier.predict_proba(["This movie is great"])

    assert len(probas) == 1
    assert "positive" in probas[0]
    assert "negative" in probas[0]

    # 概率之和应该为 1
    total = sum(probas[0].values())
    assert abs(total - 1.0) < 1e-6

    # 正面应该有更高的概率
    assert probas[0]["positive"] > probas[0]["negative"]
```

### 4.3 顶级特征测试

```python
def test_get_top_features(self):
    """测试获取顶级特征"""
    texts = [
        "the cat sat on the mat",
        "the dog played in the park",
        "cats are cute pets",
        "dogs are loyal animals",
    ]
    labels = ["cat", "dog", "cat", "dog"]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    top_features = classifier.get_top_features(n=5)

    assert "cat" in top_features
    assert "dog" in top_features

    for cls, features in top_features.items():
        assert isinstance(features, list)
        assert len(features) <= 5
        for feature, importance in features:
            assert isinstance(feature, str)
            assert isinstance(importance, float)
```

### 4.4 错误处理测试

```python
def test_predict_before_fit(self):
    """测试在 fit 之前调用 predict"""
    classifier = TextClassifier()

    with pytest.raises(RuntimeError, match="not been fitted"):
        classifier.predict(["test text"])

def test_different_lengths_raises_error(self):
    """测试长度不匹配"""
    texts = ["text1", "text2"]
    labels = ["label1"]

    classifier = TextClassifier()

    with pytest.raises(ValueError, match="same length"):
        classifier.fit(texts, labels)
```

## 5. 集成测试

### 5.1 情感分析测试

```python
def test_sentiment_analysis(self):
    """测试情感分析场景"""
    texts = [
        "This movie is absolutely wonderful and amazing",
        "I really enjoyed this film, it was fantastic",
        "The acting was superb and the story was compelling",
        "This is the worst movie I have ever seen",
        "Terrible acting and a boring storyline",
        "I wasted two hours of my life watching this garbage",
    ]
    labels = [
        "positive", "positive", "positive",
        "negative", "negative", "negative",
    ]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    test_texts = [
        "This film was amazing and I loved it",
        "What a terrible waste of time",
    ]
    predictions = classifier.predict(test_texts)

    assert predictions[0] == "positive"
    assert predictions[1] == "negative"
```

### 5.2 主题分类测试

```python
def test_topic_classification(self):
    """测试主题分类场景"""
    texts = [
        "The stock market crashed today losing 500 points",
        "Investors are worried about the economic downturn",
        "Apple released a new iPhone with amazing features",
        "The latest Android update includes many improvements",
        "The football team won the championship game",
        "The basketball player scored 50 points in the game",
    ]
    labels = [
        "finance", "finance",
        "technology", "technology",
        "sports", "sports",
    ]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    test_texts = [
        "The Dow Jones index fell sharply today",
        "Google announced a new AI assistant",
        "The team scored a touchdown in the final seconds",
    ]
    predictions = classifier.predict(test_texts)

    assert predictions[0] == "finance"
    assert predictions[1] == "technology"
    assert predictions[2] == "sports"
```

### 5.3 垃圾邮件检测测试

```python
def test_spam_detection(self):
    """测试垃圾邮件检测场景"""
    texts = [
        "You have won a million dollars! Click here now!",
        "Congratulations! You are our lucky winner!",
        "Free money! No strings attached!",
        "Hey, are you coming to the party tonight?",
        "The meeting is scheduled for tomorrow at 3pm",
        "Can you send me the report by end of day?",
    ]
    labels = [
        "spam", "spam", "spam",
        "ham", "ham", "ham",
    ]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    test_texts = [
        "You have been selected to win a prize!",
        "Don't forget about our meeting tomorrow",
    ]
    predictions = classifier.predict(test_texts)

    assert predictions[0] == "spam"
    assert predictions[1] == "ham"
```

## 6. 性能测试

### 6.1 大数据集测试

```python
def test_large_dataset(self):
    """测试大数据集"""
    # 生成 1000 个文档
    texts = [f"document {i} with word{i % 10}" for i in range(1000)]
    labels = ["class_a" if i % 2 == 0 else "class_b" for i in range(1000)]

    classifier = TextClassifier()
    classifier.fit(texts, labels)

    predictions = classifier.predict(texts[:10])
    assert len(predictions) == 10
```

### 6.2 高维特征测试

```python
def test_high_dimensional_features(self):
    """测试高维特征"""
    # 创建包含许多唯一词的文档
    texts = [f"word{i} " * 10 for i in range(100)]
    labels = ["class_a" if i % 2 == 0 else "class_b" for i in range(100)]

    classifier = TextClassifier(max_features=50)
    classifier.fit(texts, labels)

    assert len(classifier.vectorizer.vocabulary_) <= 50
```

## 7. 测试运行

### 7.1 运行所有测试

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

### 7.2 测试输出示例

```
tests/test_tfidf.py::TestTFIDFVectorizer::test_basic_fit_transform PASSED
tests/test_tfidf.py::TestTFIDFVectorizer::test_vocabulary_building PASSED
tests/test_tfidf.py::TestTFIDFVectorizer::test_tf_computation PASSED
tests/test_tfidf.py::TestTFIDFVectorizer::test_idf_computation PASSED
tests/test_tfidf.py::TestTFIDFVectorizer::test_l2_normalization PASSED
tests/test_naive_bayes.py::TestNaiveBayesMultinomial::test_basic_fit_predict PASSED
tests/test_naive_bayes.py::TestNaiveBayesMultinomial::test_predict PASSED
tests/test_naive_bayes.py::TestNaiveBayesMultinomial::test_predict_proba PASSED
tests/test_text_classifier.py::TestTextClassifier::test_basic_fit_predict PASSED
tests/test_text_classifier.py::TestTextClassifier::test_predict PASSED
tests/test_text_classifier.py::TestTextClassifierIntegration::test_sentiment_analysis PASSED
```

## 8. 测试最佳实践

### 8.1 测试命名

- 使用描述性的测试名称
- 格式：`test_<功能>_<场景>_<预期结果>`

### 8.2 测试结构

- **Arrange**: 准备测试数据
- **Act**: 执行被测试的操作
- **Assert**: 验证结果

### 8.3 测试独立性

- 每个测试应该独立运行
- 不依赖其他测试的状态
- 使用 fixture 共享测试数据

### 8.4 测试覆盖

- 测试正常流程
- 测试边界情况
- 测试错误处理
- 测试性能

## 9. 参考文献

1. pytest 官方文档: https://docs.pytest.org/
2. Python 测试最佳实践
3. scikit-learn 测试套件
