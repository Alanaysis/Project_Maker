# 04 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
+------------------+
|   集成测试       |  完整流程验证
+------------------+
|   单元测试       |  各模块独立测试
+------------------+
|   边界测试       |  异常情况处理
+------------------+
```

### 1.2 测试覆盖

| 模块 | 测试文件 | 测试数量 |
|------|----------|----------|
| Vocabulary | test_vocabulary.py | 9 |
| NGramModel | test_ngram.py | 20 |
| LanguageModel | test_language_model.py | 17 |

## 2. 单元测试

### 2.1 词汇表测试 (test_vocabulary.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_init | 初始化 | 特殊标记 ID |
| test_build | 构建词汇表 | 词汇表大小、词映射 |
| test_min_freq | 最小词频 | 低频词过滤 |
| test_encode_decode | 编码解码 | 双向转换一致性 |
| test_encode_unknown | 未知词编码 | UNK 映射 |
| test_tokenize | 分词 | 小写转换、空格分割 |
| test_tokenize_empty | 空文本 | 空列表返回 |
| test_get_freq | 词频获取 | 计数正确性 |
| test_chain_build | 链式调用 | 返回 self |

### 2.2 N-gram 测试 (test_ngram.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_init | 初始化 | 参数默认值 |
| test_init_invalid_n | 无效 N | ValueError 异常 |
| test_train | 训练 | 词汇表、计数 |
| test_train_unigram | Unigram 训练 | N=1 正常工作 |
| test_ngram_counts | N-gram 计数 | 计数正确性 |
| test_context_counts | 上下文计数 | 计数正确性 |
| test_probability | 概率计算 | 概率在 [0,1] |
| test_probability_sum | 概率和 | 和接近 1 |
| test_probability_untrained | 未训练状态 | RuntimeError |
| test_sentence_probability | 句子概率 | 负对数概率 |
| test_sentence_probability_unlikely | 不太可能的句子 | 概率更低 |
| test_perplexity | 困惑度 | 正数、有限值 |
| test_perplexity_lower_better | 更好的模型 | 困惑度更低 |
| test_perplexity_untrained | 未训练状态 | RuntimeError |
| test_generate | 文本生成 | 非空列表 |
| test_generate_with_seed | 带种子生成 | 生成结果 |
| test_generate_greedy | 贪婪生成 | 确定性结果 |
| test_generate_deterministic_greedy | 贪婪确定性 | 两次结果相同 |
| test_generate_temperature | 温度控制 | 正常工作 |
| test_generate_invalid_temperature | 无效温度 | ValueError |
| test_generate_untrained | 未训练状态 | RuntimeError |
| test_top_ngrams | 常见 N-gram | 列表格式 |
| test_unigram_model | Unigram 模型 | 完整功能 |
| test_trigram_model | Trigram 模型 | 完整功能 |
| test_repr | 字符串表示 | 格式正确 |

### 2.3 语言模型测试 (test_language_model.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_init | 初始化 | 参数正确 |
| test_train | 训练 | 词汇表、模型状态 |
| test_probability | 概率计算 | 负对数概率 |
| test_perplexity | 困惑度 | 正数 |
| test_perplexity_on_new_text | 新文本困惑度 | 训练集更低 |
| test_generate | 文本生成 | 非空字符串 |
| test_generate_with_seed | 带种子生成 | 包含种子词 |
| test_generate_greedy | 贪婪生成 | 字符串 |
| test_top_words | 常见词 | 列表格式 |
| test_top_ngrams | 常见 N-gram | 列表格式 |
| test_evaluate | 全面评估 | 指标完整 |
| test_evaluate_coverage | 词汇覆盖率 | 1.0 |
| test_repr | 字符串表示 | 格式正确 |
| test_different_n_values | 不同 N 值 | 都能工作 |
| test_different_smoothing | 不同平滑 | 都能工作 |
| test_unigram_generate | Unigram 生成 | 字符串 |

## 3. 集成测试

### 3.1 完整流程测试

```python
def test_full_pipeline(self):
    """测试完整流程"""
    corpus = [
        "i love natural language processing",
        "natural language processing is fun",
        "i love machine learning",
        "machine learning and natural language processing",
        "deep learning is part of machine learning",
        "i study deep learning every day",
    ]

    # 训练
    lm = LanguageModel(n=2, smoothing="add_k", k=0.5)
    lm.train(corpus)

    # 评估
    ppl = lm.perplexity(corpus)
    assert ppl > 0

    # 生成
    text = lm.generate(seed="i", max_length=5, temperature=0.8)
    assert isinstance(text, str)

    # 全面评估
    results = lm.evaluate(corpus)
    assert results["perplexity"] > 0
```

### 3.2 模型质量测试

```python
def test_model_improves_with_more_data(self):
    """测试模型随数据量增加而改善"""
    small_corpus = ["the cat sat on the mat"] * 5
    big_corpus = [
        "the cat sat on the mat",
        "the dog sat on the rug",
        "the cat ate the fish",
        ...
    ] * 5

    lm_small = LanguageModel(n=2)
    lm_small.train(small_corpus)

    lm_big = LanguageModel(n=2)
    lm_big.train(big_corpus)

    ppl_small = lm_small.perplexity(test)
    ppl_big = lm_big.perplexity(test)
```

## 4. 边界测试

### 4.1 异常输入

| 输入 | 预期行为 |
|------|----------|
| n=0 | ValueError |
| temperature=0 | ValueError |
| 未训练时调用 probability | RuntimeError |
| 未训练时调用 generate | RuntimeError |

### 4.2 边界情况

| 情况 | 测试方法 |
|------|----------|
| 空语料 | 测试 perplexity 返回 inf |
| 单词句子 | 测试正常工作 |
| 未知词 | 测试 UNK 处理 |

## 5. 测试运行

### 5.1 运行所有测试

```bash
cd projects/language-model
python -m pytest tests/ -v
```

### 5.2 运行特定测试

```bash
# 运行词汇表测试
python -m pytest tests/test_vocabulary.py -v

# 运行 N-gram 测试
python -m pytest tests/test_ngram.py -v

# 运行语言模型测试
python -m pytest tests/test_language_model.py -v
```

### 5.3 运行带覆盖率

```bash
python -m pytest tests/ -v --cov=src
```

## 6. 测试结果示例

```
tests/test_vocabulary.py::TestVocabulary::test_init PASSED
tests/test_vocabulary.py::TestVocabulary::test_build PASSED
tests/test_vocabulary.py::TestVocabulary::test_min_freq PASSED
tests/test_vocabulary.py::TestVocabulary::test_encode_decode PASSED
tests/test_vocabulary.py::TestVocabulary::test_encode_unknown PASSED
tests/test_vocabulary.py::TestVocabulary::test_tokenize PASSED
tests/test_vocabulary.py::TestVocabulary::test_tokenize_empty PASSED
tests/test_vocabulary.py::TestVocabulary::test_get_freq PASSED
tests/test_vocabulary.py::TestVocabulary::test_chain_build PASSED

tests/test_ngram.py::TestNGramModel::test_init PASSED
tests/test_ngram.py::TestNGramModel::test_train PASSED
tests/test_ngram.py::TestNGramModel::test_probability PASSED
tests/test_ngram.py::TestNGramModel::test_perplexity PASSED
tests/test_ngram.py::TestNGramModel::test_generate PASSED
...

tests/test_language_model.py::TestLanguageModel::test_train PASSED
tests/test_language_model.py::TestLanguageModel::test_probability PASSED
tests/test_language_model.py::TestLanguageModel::test_perplexity PASSED
tests/test_language_model.py::TestLanguageModel::test_generate PASSED
tests/test_language_model.py::TestLanguageModel::test_evaluate PASSED
...

tests/test_language_model.py::TestLanguageModelIntegration::test_full_pipeline PASSED
tests/test_language_model.py::TestLanguageModelIntegration::test_model_improves_with_more_data PASSED
```

## 7. 测试总结

### 7.1 测试覆盖

- 词汇表：构建、编码、解码、分词、特殊标记
- N-gram：训练、计数、概率、困惑度、生成
- 语言模型：完整流程、评估、不同参数

### 7.2 测试质量

- 单元测试覆盖所有公共方法
- 集成测试验证完整流程
- 边界测试处理异常情况
- 测试结果可重复
