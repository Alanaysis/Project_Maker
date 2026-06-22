# Word2Vec 测试文档

## 1. 测试策略

### 1.1 测试层次

```
单元测试
    ├── 词汇表测试
    ├── 负采样测试
    ├── 模型测试
    └── 相似度测试
集成测试
    └── 完整训练流程测试
```

### 1.2 测试覆盖目标

| 模块 | 目标覆盖率 |
|------|-----------|
| vocabulary.py | 90% |
| negative_sampling.py | 85% |
| skipgram.py | 85% |
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
        assert "the" in vocab.word2idx
        
    def test_min_count_filter(self):
        """测试低频词过滤"""
        corpus = [["a", "b", "c"], ["a", "b", "d"]]
        vocab = Vocabulary(min_count=2)
        vocab.build(corpus)
        assert "a" in vocab.word2idx  # freq=2
        assert "c" not in vocab.word2idx  # freq=1
        
    def test_word_freq(self):
        """测试词频统计"""
        corpus = [["a", "a", "b"]]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)
        assert vocab.word_freq["a"] == 2
        assert vocab.word_freq["b"] == 1
```

### 2.2 负采样测试 (test_negative_sampling.py)

```python
class TestNegativeSampling:
    def test_sample_size(self):
        """测试采样数量"""
        sampler = NegativeSampler(100, {i: 1 for i in range(100)})
        samples = sampler.sample(positive=0, k=5)
        assert len(samples) == 5
        
    def test_no_positive_in_samples(self):
        """测试采样不包含正样本"""
        sampler = NegativeSampler(100, {i: 1 for i in range(100)})
        for _ in range(100):
            samples = sampler.sample(positive=0, k=10)
            assert 0 not in samples
            
    def test_sample_distribution(self):
        """测试采样分布"""
        # 高频词应该被采样更多
        word_freqs = {0: 100, 1: 10, 2: 1}
        sampler = NegativeSampler(3, word_freqs, table_size=100000)
        
        counts = [0, 0, 0]
        for _ in range(10000):
            idx = sampler.table[np.random.randint(0, 100000)]
            counts[idx] += 1
            
        assert counts[0] > counts[1] > counts[2]
```

### 2.3 模型测试 (test_skipgram.py)

```python
class TestSkipGramModel:
    def test_initialization(self):
        """测试模型初始化"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        assert model.W_in.shape == (100, 50)
        assert model.W_out.shape == (100, 50)
        
    def test_forward_shape(self):
        """测试前向传播输出形状"""
        model = SkipGramModel(100, 50)
        loss, *rest = model.forward(0, 1, np.array([2, 3, 4]))
        assert isinstance(loss, float)
        assert loss > 0
        
    def test_backward_updates(self):
        """测试反向传播更新参数"""
        model = SkipGramModel(100, 50)
        W_before = model.W_in.copy()
        
        loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
            model.forward(0, 1, np.array([2, 3, 4]))
        model.backward(0, 1, np.array([2, 3, 4]),
                      v_center, pos_sig, neg_sig, 0.025)
        
        assert not np.array_equal(W_before, model.W_in)
```

### 2.4 相似度测试 (test_word2vec.py)

```python
class TestWord2Vec:
    def test_most_similar(self):
        """测试相似词查询"""
        model = Word2Vec(vector_size=50, min_count=1)
        
        # 训练简单语料
        corpus = [
            ["king", "queen", "royal"],
            ["king", "man", "woman"],
            ["queen", "woman", "man"]
        ] * 100  # 重复多次
        model.train(corpus, epochs=50)
        
        # 查询
        similar = model.most_similar("king", topn=3)
        assert len(similar) == 3
        assert all(isinstance(s, tuple) for s in similar)
        
    def test_get_vector(self):
        """测试获取词向量"""
        model = Word2Vec(vector_size=50, min_count=1)
        corpus = [["hello", "world"]] * 10
        model.train(corpus, epochs=10)
        
        vec = model.get_vector("hello")
        assert vec is not None
        assert len(vec) == 50
        
    def test_unknown_word(self):
        """测试未知词处理"""
        model = Word2Vec(vector_size=50, min_count=1)
        corpus = [["hello", "world"]] * 10
        model.train(corpus, epochs=10)
        
        vec = model.get_vector("unknown")
        assert vec is None
```

## 3. 集成测试

```python
class TestIntegration:
    def test_full_pipeline(self):
        """测试完整训练流程"""
        # 准备语料
        corpus = self._generate_corpus()
        
        # 创建模型
        model = Word2Vec(
            vector_size=100,
            window=5,
            min_count=2,
            negative=5,
            learning_rate=0.025
        )
        
        # 训练
        model.train(corpus, epochs=50)
        
        # 验证
        assert model.get_vector("king") is not None
        assert len(model.most_similar("king")) > 0
        
    def test_analogy(self):
        """测试词类比能力"""
        # king - man + woman ≈ queen
        corpus = self._generate_analogy_corpus()
        model = Word2Vec(vector_size=100, min_count=1)
        model.train(corpus, epochs=100)
        
        result = model.analogy("king", "man", "woman")
        assert "queen" in [w for w, _ in result[:5]]
```

## 4. 性能测试

```python
class TestPerformance:
    def test_training_speed(self):
        """测试训练速度"""
        corpus = self._generate_large_corpus(size=10000)
        model = Word2Vec(vector_size=100)
        
        start = time.time()
        model.train(corpus, epochs=10)
        elapsed = time.time() - start
        
        words_per_sec = len(corpus) * 10 / elapsed
        assert words_per_sec > 100  # 至少 100 words/sec
        
    def test_memory_usage(self):
        """测试内存占用"""
        import tracemalloc
        
        tracemalloc.start()
        model = Word2Vec(vector_size=100)
        corpus = self._generate_large_corpus(size=5000)
        model.train(corpus, epochs=10)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        assert peak < 100 * 1024 * 1024  # < 100MB
```

## 5. 测试工具

### 5.1 测试数据生成

```python
def generate_simple_corpus():
    """生成简单测试语料"""
    return [
        ["the", "king", "loves", "the", "queen"],
        ["the", "queen", "loves", "the", "king"],
        ["the", "prince", "is", "the", "son", "of", "the", "king"],
        ["the", "princess", "is", "the", "daughter", "of", "the", "queen"]
    ]

def generate_analogy_corpus():
    """生成用于类比测试的语料"""
    # 确保有足够的语义关系
    templates = [
        ["king", "is", "a", "man"],
        ["queen", "is", "a", "woman"],
        ["prince", "is", "a", "boy"],
        ["princess", "is", "a", "girl"]
    ]
    return templates * 100
```

### 5.2 断言工具

```python
def assert_vectors_similar(model, word1, word2, threshold=0.5):
    """断言两个词向量相似"""
    v1 = model.get_vector(word1)
    v2 = model.get_vector(word2)
    similarity = cosine_similarity(v1, v2)
    assert similarity > threshold, f"{word1} and {word2} similarity: {similarity}"

def assert_vectors_different(model, word1, word2, threshold=0.5):
    """断言两个词向量不同"""
    v1 = model.get_vector(word1)
    v2 = model.get_vector(word2)
    similarity = cosine_similarity(v1, v2)
    assert similarity < threshold, f"{word1} and {word2} similarity: {similarity}"
```

## 6. 持续集成

### 6.1 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_vocabulary.py

# 显示覆盖率
pytest --cov=src tests/

# 生成 HTML 报告
pytest --cov=src --cov-report=html tests/
```

### 6.2 测试配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```
