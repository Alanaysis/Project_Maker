# 学习笔记：随机森林

## 1. 项目目标

从零实现随机森林，深入理解集成学习的核心原理：
- 理解 Bagging 原理
- 掌握随机特征选择
- 学会集成学习

## 2. 核心概念

### 2.1 什么是随机森林？

随机森林是一种集成学习方法，通过构建多个决策树并将其预测结果进行组合来提高模型的准确性和稳定性。

**核心思想**："三个臭皮匠，顶个诸葛亮"

- 单棵决策树容易过拟合（高方差）
- 通过构建多棵树并取平均/投票，可以显著降低方差
- 同时保持决策树的低偏差特性

### 2.2 Bagging 原理

**Bootstrap Aggregating** 的核心步骤：

1. **Bootstrap 采样**：从原始数据集 D 中有放回地随机抽取 n 个样本
2. **训练基学习器**：在每个 bootstrap 样本上训练一个基学习器
3. **聚合**：对分类问题使用多数投票，对回归问题使用平均值

**为什么有效？**

- 数学上：假设每棵树的误差是独立的，那么 n 棵树的平均误差的方差是单棵树的 1/n
- 实际上：虽然树之间不是完全独立的，但通过随机化可以近似达到这个效果
- 袋外数据：每次 bootstrap 采样约有 37% 的数据未被选中，可以用于验证

### 2.3 随机特征选择

**为什么要随机选择特征？**

在标准 Bagging 中，每棵树虽然看到不同的数据，但在每个节点分裂时考虑的特征是相同的。这会导致：
- 树之间有较强的相关性
- 集成效果受限

**解决方案**：在每个节点分裂时只考虑部分特征

| 策略 | 公式 | 适用场景 |
|------|------|----------|
| sqrt | √p | 分类问题（默认） |
| log2 | log₂(p) | 特征较多时 |
| p/3 | p/3 | 回归问题 |

### 2.4 集成学习理论

**Condorcet 陪审团定理**：
- 如果每个分类器的准确率 > 0.5
- 那么多数投票的准确率会随着分类器数量增加而提高
- 最终趋近于 1

**偏差-方差分解**：

```
Error = Bias² + Variance + Noise
```

- 偏差 (Bias)：模型预测的期望值与真实值的差距
- 方差 (Variance)：模型预测的波动程度
- 噪声 (Noise)：数据本身的噪声，无法消除

**随机森林的作用**：
- 保持低偏差（决策树的特性）
- 显著降低方差（通过集成）

## 3. 实现细节

### 3.1 决策树

**CART 算法**：

1. **分裂准则**：
   - Gini 不纯度：`Gini(D) = 1 - Σ p_i²`
   - 信息熵：`Entropy(D) = -Σ p_i log₂(p_i)`

2. **分裂过程**：
   - 对每个特征，尝试所有可能的阈值
   - 选择使信息增益最大的特征和阈值
   - 递归构建左右子树

3. **停止条件**：
   - 达到最大深度
   - 节点样本数小于阈值
   - 节点纯度达到要求

**关键代码**：

```python
# Gini 不纯度
def _gini(self, y):
    counts = np.bincount(y.astype(int))
    probabilities = counts / len(y)
    return 1.0 - np.sum(probabilities ** 2)

# 信息增益
def _information_gain(self, y, left_y, right_y):
    n = len(y)
    parent_impurity = self._impurity(y)
    left_weight = len(left_y) / n
    right_weight = len(right_y) / n
    child_impurity = (left_weight * self._impurity(left_y) +
                      right_weight * self._impurity(right_y))
    return parent_impurity - child_impurity
```

### 3.2 随机森林

**训练流程**：

```python
for i in range(n_estimators):
    # 1. Bagging 采样
    X_sample, y_sample = bootstrap_sample(X, y)

    # 2. 创建决策树（带随机特征选择）
    tree = DecisionTreeClassifier(max_features='sqrt', random_state=seed)

    # 3. 训练决策树
    tree.fit(X_sample, y_sample)

    # 4. 保存树
    trees.append(tree)
```

**预测流程**：

```python
# 收集所有树的预测
all_predictions = [tree.predict(X) for tree in trees]

# 多数投票
final_predictions = majority_vote(all_predictions)
```

**OOB 分数计算**：

```python
# 记录每个样本的 OOB 预测
for tree_idx, tree in enumerate(trees):
    oob_indices = get_oob_indices(tree_idx)
    predictions = tree.predict(X[oob_indices])
    # 累积预测...

# 计算准确率
oob_score = accuracy(oob_predictions, y)
```

## 4. 关键收获

### 4.1 Bagging 的力量

- 通过有放回采样，每棵树看到的训练数据略有不同
- 这种差异性减少了模型的方差
- 袋外数据可以用来评估模型，无需额外的验证集

### 4.2 随机特征选择的重要性

- 增加树之间的多样性
- 减少过拟合
- 自动进行特征选择

### 4.3 集成学习的原理

- 多个"弱"学习器可以组合成"强"学习器
- 关键是学习器的准确性和多样性
- 多数投票可以减少单个学习器的错误

### 4.4 偏差-方差权衡

- 单棵决策树：低偏差、高方差
- 随机森林：保持低偏差，显著降低方差
- 这就是为什么随机森林通常比单棵决策树表现更好

## 5. 实际应用

### 5.1 优势

- 准确率高
- 不容易过拟合
- 能处理高维数据
- 能评估特征重要性
- 可以并行训练
- 对缺失值和异常值鲁棒

### 5.2 局限性

- 模型较大，预测较慢
- 不适合线性关系
- 对高基数特征（如 ID）敏感

### 5.3 应用场景

- 客户流失预测
- 信用风险评估
- 医疗诊断
- 图像分类
- 特征选择

## 6. 超参数调优

### 6.1 关键超参数

| 超参数 | 作用 | 建议值 |
|--------|------|--------|
| n_estimators | 树的数量 | 100-500 |
| max_depth | 树的最大深度 | None 或 10-20 |
| max_features | 每次分裂考虑的特征数 | 'sqrt' (分类) |
| min_samples_split | 分裂所需最小样本数 | 2-10 |
| min_samples_leaf | 叶节点最小样本数 | 1-5 |

### 6.2 调优策略

- **n_estimators**：越大越好，但有边际递减效应
- **max_depth**：控制过拟合，None 表示不限制
- **max_features**：控制多样性，sqrt 是好的默认值
- **min_samples_split** 和 **min_samples_leaf**：控制树的复杂度

## 7. 与其他方法的对比

| 方法 | 偏差 | 方差 | 特点 |
|------|------|------|------|
| 单棵决策树 | 低 | 高 | 容易过拟合 |
| Bagging | 低 | 中 | 只有数据随机化 |
| 随机森林 | 低 | 低 | 数据 + 特征随机化 |
| Boosting | 低 | 低 | 顺序构建，修正错误 |

## 8. 数学基础

### 8.1 Bootstrap 采样概率

每个样本被选中的概率：
```
p_selected = 1 - (1 - 1/n)^n ≈ 1 - 1/e ≈ 0.632
```

因此约有 36.8% 的数据是"袋外"的：
```
p_oob = 1/e ≈ 0.368
```

### 8.2 多数投票的准确率

假设每个分类器的准确率为 p，n 个分类器多数投票的准确率：
```
P(majority correct) = Σ C(n, k) * p^k * (1-p)^(n-k), k > n/2
```

当 p > 0.5 时，随着 n 增加，这个概率趋近于 1。

### 8.3 方差减少

假设每棵树的方差为 σ²，相关系数为 ρ，n 棵树的平均的方差：
```
Var(average) = ρσ² + (1-ρ)σ²/n
```

当 ρ 很小（树之间相关性低）时，方差显著减少。

## 9. 调试经验

### 9.1 常见问题

1. **训练时间过长**：减少 n_estimators，限制 max_depth
2. **过拟合**：增加 n_estimators，限制 max_depth，增加 min_samples_leaf
3. **欠拟合**：增加 max_depth，减少 min_samples_split

### 9.2 调试技巧

- 打印树的结构和深度
- 检查特征重要性是否合理
- 使用 OOB 分数评估泛化能力
- 与 scikit-learn 的实现对比

## 10. 进一步学习

### 10.1 相关算法

- **Extra Trees**：更极端的随机化，阈值也是随机的
- **AdaBoost**：顺序构建，关注错误样本
- **Gradient Boosting**：顺序构建，拟合残差

### 10.2 深入主题

- 特征重要性的置换方法
- 偏依赖图 (Partial Dependence Plots)
- SHAP 值

### 10.3 参考资料

- Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.
- Hastie, T., Tibshirani, R., & Friedman, J. (2009). The Elements of Statistical Learning.
- [scikit-learn RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
