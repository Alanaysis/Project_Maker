# Word2Vec 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- NumPy 1.19+
- pytest 6.0+
- matplotlib 3.0+ (可选，用于可视化)

### 1.2 安装依赖

```bash
pip install numpy pytest matplotlib
```

### 1.3 项目结构

```
word2vec/
├── src/
│   ├── __init__.py
│   ├── vocabulary.py
│   ├── skipgram.py
│   ├── cbow.py
│   ├── negative_sampling.py
│   ├── hierarchical_softmax.py
│   ├── subsampling.py
│   ├── evaluation.py
│   ├── applications.py
│   ├── trainer.py
│   └── word2vec.py
├── tests/
│   ├── __init__.py
│   ├── test_vocabulary.py
│   ├── test_skipgram.py
│   ├── test_cbow.py
│   ├── test_negative_sampling.py
│   ├── test_hierarchical_softmax.py
│   ├── test_subsampling.py
│   ├── test_evaluation.py
│   ├── test_applications.py
│   └── test_word2vec.py
└── examples/
    ├── train_example.py
    ├── text_classification.py
    ├── sentiment_analysis.py
    └── word_clustering.py
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
- [x] CBOW 模型
- [x] 层次 Softmax
- [x] 降采样
- [x] 相似词查询
- [x] 模型保存/加载

**Sprint 4: 评估与应用**
- [x] 词相似度评估
- [x] 词类比评估
- [x] t-SNE 可视化
- [x] 文本分类
- [x] 情感分析
- [x] 词聚类

**Sprint 5: 优化测试**
- [x] 完整测试覆盖
- [x] 文档完善
- [x] 示例代码

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
feat(cbow): implement CBOW model
feat(hs): add hierarchical softmax
```

## 3. 核心模块开发

### 3.1 词汇表模块

**开发步骤**:
1. 实现词频统计
2. 实现低频词过滤
3. 实现词索引映射
4. 编写单元测试

### 3.2 负采样模块

**开发步骤**:
1. 实现噪声分布计算（词频的 3/4 次方）
2. 构建采样查找表
3. 实现采样逻辑
4. 测试采样分布

### 3.3 层次 Softmax 模块

**开发步骤**:
1. 实现 Huffman 树构建
2. 预计算每个词的路径
3. 实现前向+反向传播
4. 测试概率计算

### 3.4 Skip-gram 模型

**开发步骤**:
1. 实现参数初始化（Xavier）
2. 实现前向传播
3. 实现反向传播
4. 梯度检查

### 3.5 CBOW 模型

**开发步骤**:
1. 实现参数初始化
2. 实现隐藏层（上下文平均）
3. 实现前向传播
4. 实现反向传播（更新所有上下文词向量）

### 3.6 降采样模块

**开发步骤**:
1. 实现保留概率计算
2. 实现句子降采样
3. 实现语料降采样
4. 测试高频词丢弃率

### 3.7 评估模块

**开发步骤**:
1. 实现词相似度评估（Spearman 相关系数）
2. 实现词类比评估
3. 实现 PCA 降维
4. 实现 t-SNE 降维
5. 实现 K-Means 聚类

### 3.8 应用模块

**开发步骤**:
1. 实现文本分类器
2. 实现情感分析器
3. 实现词聚类器
4. 编写应用示例

## 4. 调试指南

### 4.1 常见问题

**问题1: 训练损失不下降**
```
原因: 学习率过大或过小
解决:
- 尝试学习率 0.025, 0.01, 0.001
- 检查梯度是否正确
- 增加训练轮数
```

**问题2: 相似词查询结果差**
```
原因: 训练不充分或语料不足
解决:
- 增加训练轮数
- 增加语料量
- 调整窗口大小
- 尝试不同的优化方式
```

**问题3: 内存溢出**
```
原因: 词汇表过大
解决:
- 提高 min_count
- 限制词汇表大小
- 使用降采样减少训练数据
```

**问题4: CBOW 训练不稳定**
```
原因: 梯度更新不均匀
解决:
- 降低学习率
- 增加梯度裁剪
- 检查隐藏层计算
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
2. **Huffman 树路径预计算**: 减少重复计算
3. **向量化操作**: 使用 NumPy 广播
4. **动态窗口**: 随机窗口大小
5. **学习率衰减**: 线性衰减到初始值的 1%
6. **梯度裁剪**: 防止梯度爆炸

### 5.2 可进一步优化

1. **多线程训练**: 并行处理训练对
2. **批量更新**: 累积梯度后更新
3. **GPU 加速**: 使用 CuPy 替代 NumPy
4. **内存映射**: 处理大文件

## 6. 版本历史

### v2.0.0 (当前版本)
- 实现 CBOW 模型
- 实现层次 Softmax
- 实现降采样
- 实现评估模块
- 实现应用模块
- 完整测试覆盖

### v1.0.0
- 实现 Skip-gram 模型
- 实现负采样
- 实现相似词查询
- 基础测试覆盖

## 7. 后续计划

### 7.1 功能扩展

- [ ] 在线学习（增量更新）
- [ ] 多语言支持
- [ ] 短语向量
- [ ] 模型压缩

### 7.2 性能优化

- [ ] 多线程支持
- [ ] GPU 加速（可选）
- [ ] 内存映射大文件
- [ ] 分布式训练
