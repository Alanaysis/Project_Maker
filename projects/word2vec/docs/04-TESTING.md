# Word2Vec 测试文档

## 1. 测试策略

### 1.1 测试层次

```
单元测试
    ├── 词汇表测试
    ├── Skip-gram 模型测试
    ├── CBOW 模型测试
    ├── 负采样测试
    ├── 层次 Softmax 测试
    ├── 降采样测试
    ├── 评估模块测试
    └── 应用模块测试
集成测试
    └── 完整训练流程测试
```

### 1.2 测试覆盖目标

| 模块 | 目标覆盖率 |
|------|-----------|
| vocabulary.py | 90% |
| skipgram.py | 85% |
| cbow.py | 85% |
| negative_sampling.py | 85% |
| hierarchical_softmax.py | 85% |
| subsampling.py | 85% |
| evaluation.py | 80% |
| applications.py | 80% |
| word2vec.py | 80% |

## 2. 单元测试

### 2.1 词汇表测试 (test_vocabulary.py)

```python
class TestVocabulary:
    def test_build_vocab(self):
        """测试词汇表构建"""
        corpus = [["the", "cat", "sat"], ["the", "dog", "ran"]]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)
        assert len(vocab) == 5
        assert "the" in vocab

    def test_min_count_filter(self):
        """测试低频词过滤"""
        corpus = [["a", "b", "c"], ["a", "b", "d"]]
        vocab = Vocabulary(min_count=2)
        vocab.build(corpus)
        assert "a" in vocab
        assert "c" not in vocab
```

### 2.2 Skip-gram 测试 (test_skipgram.py)

```python
class TestSkipGramModel:
    def test_forward(self):
        """测试前向传播"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
            model.forward(0, 1, np.array([2, 3, 4]))
        assert isinstance(loss, float)
        assert loss > 0

    def test_backward_updates(self):
        """测试反向传播更新参数"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        W_before = model.W_in.copy()
        loss, *rest = model.forward(0, 1, np.array([2, 3, 4]))
        model.backward(0, 1, np.array([2, 3, 4]), *rest, 0.025)
        assert not np.array_equal(W_before, model.W_in)
```

### 2.3 CBOW 测试 (test_cbow.py)

```python
class TestCBOWModel:
    def test_forward_hidden_layer(self):
        """测试隐藏层是上下文向量的平均"""
        model = CBOWModel(vocab_size=10, vector_size=5)
        context_indices = np.array([0, 1, 2])
        expected_h = np.mean(model.W_in[context_indices], axis=0)
        _, h, _, _, _, _ = model.forward(context_indices, 5, np.array([6, 7]))
        np.testing.assert_allclose(h, expected_h, rtol=1e-5)

    def test_backward_updates_all_context(self):
        """测试反向传播更新所有上下文词向量"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        context_indices = np.array([0, 1, 2])
        W_in_before = model.W_in.copy()
        loss, h, v_center, v_neg, pos_sig, neg_sig = \
            model.forward(context_indices, 5, np.array([6, 7]))
        model.backward(context_indices, 5, np.array([6, 7]),
                       h, v_center, v_neg, pos_sig, neg_sig, 0.025)
        for idx in context_indices:
            assert not np.array_equal(W_in_before[idx], model.W_in[idx])
```

### 2.4 层次 Softmax 测试 (test_hierarchical_softmax.py)

```python
class TestHierarchicalSoftmax:
    def test_high_freq_shorter_path(self):
        """测试高频词路径更短"""
        word_freqs = np.array([1000, 10, 1])
        hs = HierarchicalSoftmax(vocab_size=3, vector_size=10, word_freqs=word_freqs)
        len_0 = len(hs.word_paths[0])
        len_2 = len(hs.word_paths[2])
        assert len_0 <= len_2

    def test_forward_backward(self):
        """测试前向+反向传播"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)
        context_vector = np.random.randn(10)
        loss = hs.forward_backward(context_vector, center_idx=0, lr=0.01)
        assert isinstance(loss, float)
        assert loss >= 0
```

### 2.5 降采样测试 (test_subsampling.py)

```python
class TestSubSampler:
    def test_high_freq_dropped_more(self):
        """测试高频词被丢弃更多"""
        word_freq = {"the": 10000, "cat": 10, "sat": 5}
        total_words = 10015
        sampler = SubSampler(word_freq, total_words, threshold=1e-4)

        keep_count = {"the": 0, "cat": 0, "sat": 0}
        for _ in range(10000):
            for word in keep_count:
                if sampler.should_keep(word):
                    keep_count[word] += 1

        assert keep_count["the"] < keep_count["cat"]
        assert keep_count["cat"] < keep_count["sat"]
```

### 2.6 评估测试 (test_evaluation.py)

```python
class TestWordSimilarityEvaluator:
    def test_cosine_similarity_self(self, evaluator):
        """测试自身相似度"""
        sim = evaluator.cosine_similarity("word0", "word0")
        assert sim == pytest.approx(1.0, abs=1e-5)

class TestTSNEVisualizer:
    def test_pca_reduce(self):
        """测试 PCA 降维"""
        vectors = np.random.randn(20, 50)
        reduced = TSNEVisualizer.pca_reduce(vectors, n_components=2)
        assert reduced.shape == (20, 2)
```

### 2.7 应用测试 (test_applications.py)

```python
class TestTextClassifier:
    def test_train_and_predict(self, classifier):
        """测试训练和预测"""
        sentences = [["word0", "word1"], ["word2", "word3"]]
        labels = [0, 1]
        classifier.train(sentences, labels)
        pred = classifier.predict(["word0", "word1"])
        assert pred is not None
        assert pred in [0, 1]

class TestSentimentAnalyzer:
    def test_analyze(self, analyzer):
        """测试情感分析"""
        positive = ["word0", "word1"]
        negative = ["word3", "word4"]
        analyzer.build_sentiment_lexicon(positive, negative)
        result = analyzer.analyze(["word0", "word1"])
        assert 'sentiment' in result
```

## 3. 集成测试

```python
class TestWord2VecIntegration:
    def test_skipgram_pipeline(self):
        """测试 Skip-gram 完整流程"""
        corpus = [["king", "queen", "royal"]] * 50
        model = Word2Vec(vector_size=50, model_type='skipgram', min_count=1)
        model.train(corpus, epochs=20, verbose=False)
        assert model.is_trained
        assert model.get_vector("king") is not None

    def test_cbow_pipeline(self):
        """测试 CBOW 完整流程"""
        corpus = [["king", "queen", "royal"]] * 50
        model = Word2Vec(vector_size=50, model_type='cbow', min_count=1)
        model.train(corpus, epochs=20, verbose=False)
        assert model.is_trained

    def test_hierarchical_softmax_pipeline(self):
        """测试层次 Softmax 完整流程"""
        corpus = [["king", "queen", "royal"]] * 50
        model = Word2Vec(vector_size=50, use_hs=True, min_count=1)
        model.train(corpus, epochs=20, verbose=False)
        assert model.is_trained

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        corpus = [["hello", "world"]] * 10
        model = Word2Vec(vector_size=50, min_count=1)
        model.train(corpus, epochs=10, verbose=False)

        filepath = str(tmp_path / "model")
        model.save(filepath)
        loaded = Word2Vec.load(filepath)

        assert loaded.is_trained
        assert loaded.vocab_size == model.vocab_size
        vec1 = model.get_vector("hello")
        vec2 = loaded.get_vector("hello")
        assert np.allclose(vec1, vec2)
```

## 4. 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_vocabulary.py

# 显示覆盖率
pytest --cov=src tests/

# 生成 HTML 报告
pytest --cov=src --cov-report=html tests/

# 运行特定测试类
pytest tests/test_cbow.py::TestCBOWModel -v
```

## 5. 测试配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```
