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
| Smoothing | test_smoothing.py | 19 |
| NeuralLM | test_neural_lm.py | 34 |
| Evaluation | test_evaluation.py | 38 |
| Applications | test_applications.py | 18 |
| **总计** | | **155** |

## 2. 单元测试

### 2.1 词汇表测试 (9 tests)

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

### 2.2 N-gram 测试 (20 tests)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_init | 初始化 | 参数默认值 |
| test_init_invalid_n | 无效 N | ValueError |
| test_train | 训练 | 词汇表、计数 |
| test_train_unigram | Unigram | N=1 正常工作 |
| test_ngram_counts | 计数 | 正确性 |
| test_context_counts | 上下文计数 | 正确性 |
| test_probability | 概率 | 在 [0,1] |
| test_probability_sum | 概率和 | 接近 1 |
| test_sentence_probability | 句子概率 | 负对数概率 |
| test_sentence_probability_unlikely | 不太可能句子 | 概率更低 |
| test_perplexity | 困惑度 | 正数、有限值 |
| test_perplexity_lower_better | 更好模型 | 困惑度更低 |
| test_generate | 生成 | 非空列表 |
| test_generate_greedy | 贪婪生成 | 确定性 |
| test_generate_temperature | 温度 | 正常工作 |
| test_unigram/trigram | 不同 N 值 | 正常工作 |
| test_repr | 字符串表示 | 格式正确 |

### 2.3 语言模型测试 (17 tests)

测试完整流程：训练、概率计算、困惑度、文本生成、评估。

### 2.4 平滑技术测试 (19 tests)

**LaplaceSmoothing (8 tests)**:
- 初始化、无效参数、基本概率、零计数、概率和、不同 k 值、标准拉普拉斯、字符串表示

**GoodTuringSmoothing (7 tests)**:
- 初始化、无效参数、拟合、调整计数、概率计算、未拟合错误、字符串表示

**KneserNeySmoothing (8 tests)**:
- 初始化、无效参数、拟合、概率计算、概率和、未见上下文、低阶概率、字符串表示

### 2.5 神经语言模型测试 (34 tests)

**ActivationFunction (8 tests)**:
- sigmoid、sigmoid 导数、tanh、tanh 导数、softmax、softmax 数值稳定性、relu、relu 导数

**FeedforwardNeuralLM (7 tests)**:
- 初始化、前向传播、预测、训练步骤、损失下降、困惑度、获取嵌入

**RNNLanguageModel (6 tests)**:
- 初始化、前向传播、预测、训练步骤、损失下降、字符串表示

**LSTMLanguageModel (9 tests)**:
- 初始化、LSTM 单步、门控范围、前向传播、预测、训练步骤、损失下降、困惑度、遗忘门偏置

### 2.6 评估指标测试 (38 tests)

**Perplexity (5 tests)**: 完美预测、均匀分布、空输入、单个词、概率越高困惑度越低

**CrossEntropy (5 tests)**: base-2、自然对数、空输入、与困惑度关系、零概率

**BPC (2 tests)**: 基本计算、等于交叉熵

**Entropy (2 tests)**: 基本计算、空输入

**PerplexityFromProbs (3 tests)**: 从概率计算困惑度、交叉熵、空输入

**WordErrorRate (6 tests)**: 相同序列、一个替换、一个删除、一个插入、空参考、都为空

**BLEU (5 tests)**: 完美匹配、无匹配、部分匹配、空输入、短句惩罚

**CompareModels (1 test)**: 多模型比较

### 2.7 应用测试 (18 tests)

**TextGenerator (4 tests)**: 初始化、生成、多样生成、前缀续写

**SpellingCorrector (8 tests)**: 初始化、编辑距离 1、编辑距离 2、词纠正、带上下文纠正、文本纠正、建议、未知词建议

**InputMethod (6 tests)**: 初始化、前缀补全、带上下文补全、预测下一个词、获取候选词、带上下文候选词

## 3. 集成测试

### 3.1 完整流程测试

```python
def test_full_pipeline(self):
    corpus = [...]
    lm = LanguageModel(n=2, smoothing="add_k", k=0.5)
    lm.train(corpus)
    ppl = lm.perplexity(corpus)
    text = lm.generate(seed="i", max_length=5, temperature=0.8)
    results = lm.evaluate(corpus)
```

### 3.2 模型质量测试

测试模型随数据量增加而改善。

## 4. 边界测试

### 4.1 异常输入

| 输入 | 预期行为 |
|------|----------|
| n=0 | ValueError |
| temperature=0 | ValueError |
| discount=0 or 1 | ValueError |
| 未训练时调用方法 | RuntimeError |

### 4.2 数值稳定性

- Softmax 大数值输入
- Sigmoid 极端值
- LSTM 门控值范围 [0, 1]
- 梯度裁剪

## 5. 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 -m pytest tests/test_smoothing.py -v
python3 -m pytest tests/test_neural_lm.py -v

# 带覆盖率
python3 -m pytest tests/ -v --cov=src
```

## 6. 测试结果

```
155 passed in 0.15s
```

## 7. 测试总结

- 155 个测试用例覆盖所有 7 个模块
- 单元测试覆盖所有公共方法和边界情况
- 集成测试验证完整流程
- 数值稳定性测试确保极端情况下不崩溃
- 测试结果可重复
