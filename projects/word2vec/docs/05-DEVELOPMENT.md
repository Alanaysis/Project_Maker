# Word2Vec 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- NumPy 1.19+
- pytest 6.0+

### 1.2 安装依赖

```bash
pip install numpy pytest
```

### 1.3 项目结构

```
word2vec/
├── src/
│   ├── __init__.py
│   ├── vocabulary.py
│   ├── skipgram.py
│   ├── negative_sampling.py
│   ├── trainer.py
│   └── word2vec.py
├── tests/
│   ├── __init__.py
│   ├── test_vocabulary.py
│   ├── test_skipgram.py
│   ├── test_negative_sampling.py
│   └── test_word2vec.py
└── examples/
    └── train_example.py
```

## 2. 开发流程

### 2.1 迭代计划

**Sprint 1: 基础框架**
- [x] 项目结构搭建
- [x] 词汇表实现
- [x] 基础测试

**Sprint 2: 核心算法**
- [x] Skip-gram 模型
- [x] 负采样实现
- [x] 训练器实现

**Sprint 3: 功能完善**
- [x] 相似词查询
- [x] 模型保存/加载
- [x] 示例代码

**Sprint 4: 优化测试**
- [x] 性能优化
- [x] 完整测试
- [x] 文档完善

### 2.2 开发规范

**代码风格**
- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串

**提交规范**
```
<type>(<scope>): <subject>

类型:
- feat: 新功能
- fix: 修复
- docs: 文档
- test: 测试
- refactor: 重构

示例:
feat(vocabulary): add min_count filtering
fix(skipgram): correct gradient calculation
```

## 3. 核心模块开发

### 3.1 词汇表模块

**开发步骤**:
1. 实现词频统计
2. 实现低频词过滤
3. 实现词索引映射
4. 编写单元测试

**关键代码**:
```python
def build(self, corpus: List[List[str]]) -> None:
    # 统计词频
    for sentence in corpus:
        for word in sentence:
            self.word_freq[word] = self.word_freq.get(word, 0) + 1
    
    # 过滤并建立索引
    idx = 0
    for word, freq in sorted(self.word_freq.items(), key=lambda x: -x[1]):
        if freq >= self.min_count:
            self.word2idx[word] = idx
            self.idx2word[idx] = word
            idx += 1
```

### 3.2 负采样模块

**开发步骤**:
1. 实现噪声分布计算
2. 构建采样查找表
3. 实现采样逻辑
4. 测试采样分布

**关键代码**:
```python
def _build_table(self, vocab_size, word_freqs):
    freqs = np.array([word_freqs.get(i, 0) for i in range(vocab_size)])
    powered = np.power(freqs, 0.75)
    powered /= powered.sum()
    
    table = np.zeros(self.table_size, dtype=np.int32)
    cumsum = np.cumsum(powered)
    
    j = 0
    for i in range(self.table_size):
        while j < len(cumsum) - 1 and i / self.table_size > cumsum[j]:
            j += 1
        table[i] = j
    return table
```

### 3.3 Skip-gram 模型

**开发步骤**:
1. 实现参数初始化
2. 实现前向传播
3. 实现反向传播
4. 梯度检查

**关键代码**:
```python
def forward(self, center_idx, context_idx, neg_indices):
    v_center = self.W_in[center_idx]
    v_context = self.W_out[context_idx]
    v_neg = self.W_out[neg_indices]
    
    pos_score = sigmoid(np.dot(v_context, v_center))
    neg_scores = sigmoid(-np.dot(v_neg, v_center))
    
    loss = -np.log(pos_score) - np.sum(np.log(neg_scores))
    return loss, v_center, v_context, v_neg, pos_score, neg_scores
```

## 4. 调试指南

### 4.1 常见问题

**问题1: 训练损失不下降**
```
原因: 学习率过大或过小
解决: 
- 尝试学习率 0.025, 0.01, 0.001
- 检查梯度是否正确
```

**问题2: 相似词查询结果差**
```
原因: 训练不充分或语料不足
解决:
- 增加训练轮数
- 增加语料量
- 调整窗口大小
```

**问题3: 内存溢出**
```
原因: 词汇表过大
解决:
- 提高 min_count
- 限制词汇表大小
- 使用 float32
```

### 4.2 调试技巧

**检查梯度**
```python
def check_gradient(model, epsilon=1e-5):
    # 数值梯度 vs 解析梯度
    pass
```

**监控训练**
```python
# 打印损失
print(f"Epoch {epoch}, Loss: {loss:.4f}")

# 检查词向量范数
print(f"Vector norm: {np.linalg.norm(model.W_in[0]):.4f}")

# 测试相似词
print(model.most_similar("king", topn=5))
```

## 5. 性能优化

### 5.1 已实现优化

1. **负采样查找表**: O(1) 采样
2. **向量化操作**: 使用 NumPy 广播
3. **动态窗口**: 随机窗口大小

### 5.2 可进一步优化

1. **多线程训练**: 并行处理训练对
2. **批量更新**: 累积梯度后更新
3. **子采样**: 高频词随机丢弃

## 6. 版本历史

### v1.0.0 (当前版本)
- 实现 Skip-gram 模型
- 实现负采样
- 实现相似词查询
- 完整测试覆盖

## 7. 后续计划

### 7.1 功能扩展

- [ ] CBOW 模型
- [ ] 层次 Softmax
- [ ] 子采样
- [ ] 模型保存/加载
- [ ] 词类比功能

### 7.2 性能优化

- [ ] 多线程支持
- [ ] GPU 加速（可选）
- [ ] 内存映射大文件
