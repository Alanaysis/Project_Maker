# 05 - 开发文档：随机森林

## 1. 开发环境

### 1.1 依赖

- Python 3.8+
- NumPy
- pytest (测试)

### 1.2 安装

```bash
# 克隆项目
cd projects/random-forest

# 安装依赖
pip install numpy pytest
```

## 2. 项目结构

```
random-forest/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档 (本文件)
├── src/
│   ├── __init__.py
│   ├── decision_tree.py        # 决策树实现
│   └── random_forest.py        # 随机森林实现
└── tests/
    ├── __init__.py
    ├── test_decision_tree.py    # 决策树测试
    └── test_random_forest.py    # 随机森林测试
```

## 3. 开发流程

### 3.1 开发顺序

1. **决策树基础**
   - Node 类
   - 不纯度计算 (Gini, Entropy)
   - 信息增益
   - 最佳分裂查找
   - 树构建

2. **决策树功能**
   - fit() 方法
   - predict() 方法
   - score() 方法
   - 特征重要性

3. **随机森林基础**
   - Bagging 采样
   - 随机特征选择
   - 多树训练

4. **随机森林功能**
   - 多数投票预测
   - 概率预测
   - OOB 分数
   - 特征重要性平均

### 3.2 测试驱动开发

每个功能都应该先写测试，再写实现：

1. 编写测试用例
2. 运行测试（应该失败）
3. 实现功能
4. 运行测试（应该通过）
5. 重构代码

## 4. 代码规范

### 4.1 命名规范

- 类名：PascalCase (如 `DecisionTreeClassifier`)
- 方法名：snake_case (如 `fit`, `predict`)
- 私有方法：前缀下划线 (如 `_build_tree`)
- 常量：大写 (如 `CRITERIA`)

### 4.2 文档规范

- 每个类和方法都应该有 docstring
- 使用 Google 风格的 docstring
- 包含参数说明和返回值说明

### 4.3 类型注解

```python
def fit(self, X: np.ndarray, y: np.ndarray) -> "DecisionTreeClassifier":
    """..."""
    pass
```

### 4.4 错误处理

- 使用 `ValueError` 处理参数错误
- 使用 `RuntimeError` 处理状态错误
- 提供清晰的错误消息

## 5. 关键实现细节

### 5.1 随机种子管理

```python
# 整体随机种子
self._rng = np.random.RandomState(random_state)

# 每棵树的随机种子
tree_seed = self._rng.randint(0, 2**31)
```

这样可以：
- 保证整体可重复性
- 每棵树有不同的随机性
- 便于调试和复现

### 5.2 OOB 分数计算

```python
# 记录每个样本的 OOB 预测
oob_predictions = np.zeros((n_samples, n_classes))
oob_counts = np.zeros(n_samples)

# 对每棵树
for tree_idx, tree in enumerate(trees):
    # 找到 OOB 样本
    oob_indices = get_oob_indices(tree_idx)
    # 预测
    preds = tree.predict(X[oob_indices])
    # 累积
    for idx, pred in zip(oob_indices, preds):
        oob_predictions[idx, class_idx] += 1
        oob_counts[idx] += 1

# 计算准确率
oob_mask = oob_counts > 0
oob_pred_classes = np.argmax(oob_predictions[oob_mask], axis=1)
oob_score = np.mean(oob_pred_classes == y[oob_mask])
```

### 5.3 特征重要性计算

```python
# 基于不纯度减少
importance = n_samples * (parent_impurity - child_impurity)

# 所有树的平均
feature_importances = sum(tree.feature_importances_ for tree in trees) / n_trees
```

## 6. 性能优化

### 6.1 当前优化

- NumPy 向量化操作
- 布尔索引进行数据分裂
- 提前停止条件检查

### 6.2 可能的优化

- 并行训练 (multiprocessing)
- 更高效的数据结构
- 特征预排序

## 7. 扩展计划

### 7.1 短期扩展

- [ ] 回归支持 (RandomForestRegressor)
- [ ] 更多分裂准则
- [ ] 特征重要性的置换方法

### 7.2 长期扩展

- [ ] 并行训练 (n_jobs)
- [ ] 增量学习
- [ ] 更多集成方法 (AdaBoost, Gradient Boosting)

## 8. 调试技巧

### 8.1 打印调试

```python
# 在 _build_tree 中添加
print(f"Depth: {depth}, Samples: {n_samples}, Impurity: {impurity:.4f}")
```

### 8.2 可视化调试

```python
# 打印树结构
def print_tree(node, indent=""):
    if node.is_leaf:
        print(f"{indent}Leaf: {node.value}")
    else:
        print(f"{indent}Feature {node.feature_index} <= {node.threshold:.4f}")
        print_tree(node.left, indent + "  ")
        print_tree(node.right, indent + "  ")
```

### 8.3 测试调试

```bash
# 详细输出
pytest tests/ -v --tb=long

# 只运行失败的测试
pytest tests/ --lf

# 在第一个失败处停止
pytest tests/ -x
```

## 9. 常见问题

### 9.1 训练时间过长

- 减少 `n_estimators`
- 限制 `max_depth`
- 增加 `min_samples_split`

### 9.2 过拟合

- 增加 `n_estimators`
- 限制 `max_depth`
- 增加 `min_samples_leaf`
- 使用 `max_features='sqrt'`

### 9.3 欠拟合

- 增加 `max_depth`
- 减少 `min_samples_split`
- 增加 `n_estimators`

## 10. 学习资源

### 10.1 论文

- Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.

### 10.2 书籍

- Hastie, T., Tibshirani, R., & Friedman, J. (2009). The Elements of Statistical Learning.
- Bishop, C. M. (2006). Pattern Recognition and Machine Learning.

### 10.3 在线资源

- [scikit-learn RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [Understanding Random Forests](https://towardsdatascience.com/understanding-random-forest-58381e0602d2)
