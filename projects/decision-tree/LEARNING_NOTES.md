# 决策树学习笔记

## 1. 决策树基本概念

### 1.1 什么是决策树？
决策树是一种树形结构，其中：
- 每个内部节点表示对某个属性的判断
- 每个分支表示一个判断结果的输出
- 每个叶节点表示一种分类结果

决策树模拟了人类做决策的过程，通过一系列问题逐步缩小选择范围，最终得出结论。

### 1.2 决策树的优缺点

**优点**：
- 模型可解释性强，易于理解
- 不需要特征缩放
- 可以处理混合类型特征
- 计算复杂度相对较低
- 可以处理多分类问题

**缺点**：
- 容易过拟合
- 对噪声数据敏感
- 不稳定性（数据微小变化可能导致树结构完全不同）
- 贪心算法，可能找不到全局最优解

## 2. 信息论基础

### 2.1 熵 (Entropy)
熵是信息论中衡量不确定性的指标。

**定义**：
$$H(D) = -\sum_{i=1}^{n} p_i \log_2(p_i)$$

**理解**：
- 当数据完全确定时（所有样本属于同一类别），熵为0
- 当数据完全不确定时（样本均匀分布），熵最大
- 熵越小，数据越纯

**例子**：
假设有10个样本，7个属于类别A，3个属于类别B：
$$H(D) = -\frac{7}{10} \log_2\frac{7}{10} - \frac{3}{10} \log_2\frac{3}{10} \approx 0.88$$

### 2.2 条件熵 (Conditional Entropy)
条件熵表示在已知某个特征的条件下，数据集的不确定性。

**定义**：
$$H(D|A) = \sum_{i=1}^{n} \frac{|D_i|}{|D|} H(D_i)$$

**理解**：
- 条件熵越小，说明特征A对分类越有帮助
- 条件熵为0时，特征A可以完全确定分类

### 2.3 信息增益 (Information Gain)
信息增益表示使用特征A进行分裂后，不确定性减少的程度。

**定义**：
$$g(D, A) = H(D) - H(D|A)$$

**理解**：
- 信息增益越大，特征A的分类能力越强
- ID3算法使用信息增益作为特征选择标准

## 3. 决策树构建算法

### 3.1 ID3算法
**核心思想**：
- 使用信息增益作为特征选择标准
- 递归构建决策树

**步骤**：
1. 计算当前节点的熵
2. 对每个特征计算信息增益
3. 选择信息增益最大的特征进行分裂
4. 递归构建子树

**缺点**：
- 只能处理离散特征
- 偏向于选择取值较多的特征
- 容易过拟合

### 3.2 C4.5算法
**改进点**：
- 使用信息增益比代替信息增益
- 可以处理连续特征
- 引入了剪枝机制

**信息增益比**：
$$g_R(D, A) = \frac{g(D, A)}{H_A(D)}$$

其中：
$$H_A(D) = -\sum_{i=1}^{n} \frac{|D_i|}{|D|} \log_2\frac{|D_i|}{|D|}$$

### 3.3 CART算法
**特点**：
- 使用基尼指数作为特征选择标准
- 生成二叉树
- 可以处理分类和回归问题

**基尼指数**：
$$Gini(D) = 1 - \sum_{i=1}^{n} p_i^2$$

## 4. 剪枝策略

### 4.1 预剪枝 (Pre-pruning)
在构建过程中提前停止，常用条件：
- 最大深度
- 最小样本数
- 最小信息增益
- 最小叶节点样本数

**优点**：
- 简单高效
- 防止过拟合

**缺点**：
- 可能欠拟合
- 需要调整多个参数

### 4.2 后剪枝 (Post-pruning)
先构建完整树，再从下往上剪枝。

**常用方法**：
- 错误率降低剪枝 (REP)
- 悲观剪枝 (PEP)
- 代价复杂度剪枝 (CCP)

**优点**：
- 更准确
- 不需要预先设定参数

**缺点**：
- 计算复杂度高
- 需要验证集

## 5. 实现细节

### 5.1 信息增益计算
```python
def _find_best_split(self, X, y):
    best_gain = -1
    best_feature = None
    best_threshold = None
    
    for feature_index in range(n_features):
        thresholds = np.unique(X[:, feature_index])
        for threshold in thresholds:
            # 计算信息增益
            gain = current_impurity - (left_weight * left_impurity + right_weight * right_impurity)
            
            if gain > best_gain:
                best_gain = gain
                best_feature = feature_index
                best_threshold = threshold
    
    return best_feature, best_threshold
```

### 5.2 递归构建
```python
def _build_tree(self, X, y, depth=0):
    # 停止条件
    if 满足停止条件:
        return TreeNode(value=预测值)
    
    # 寻找最佳分裂
    best_feature, best_threshold = self._find_best_split(X, y)
    
    # 递归构建子树
    left_subtree = self._build_tree(X[left_indices], y[left_indices], depth + 1)
    right_subtree = self._build_tree(X[right_indices], y[right_indices], depth + 1)
    
    return TreeNode(feature_index=best_feature, threshold=best_threshold,
                   left=left_subtree, right=right_subtree)
```

### 5.3 预测过程
```python
def _traverse_tree(self, x, node):
    if node.is_leaf_node():
        return node.value
    
    if x[node.feature_index] <= node.threshold:
        return self._traverse_tree(x, node.left)
    else:
        return self._traverse_tree(x, node.right)
```

## 6. 应用场景

### 6.1 客户分类
- 根据客户特征进行分类
- 预测客户购买行为
- 客户细分

### 6.2 信用评分
- 评估贷款申请人的信用风险
- 预测违约概率
- 制定贷款策略

### 6.3 医疗诊断
- 根据症状诊断疾病
- 预测疾病风险
- 制定治疗方案

### 6.4 故障检测
- 预测设备故障
- 识别异常行为
- 预防性维护

## 7. 优化技巧

### 7.1 特征工程
- 特征选择：选择最相关的特征
- 特征变换：标准化、归一化
- 特征组合：创建新特征

### 7.2 参数调优
- 使用交叉验证选择参数
- 网格搜索最佳参数组合
- 学习曲线分析

### 7.3 集成学习
- 随机森林：多棵决策树的集成
- 梯度提升树：逐步改进的决策树
- AdaBoost：自适应提升

## 8. 常见问题

### 8.1 过拟合问题
**表现**：
- 训练集准确率高，测试集准确率低
- 树结构过于复杂

**解决方案**：
- 使用剪枝策略
- 限制树的最大深度
- 增加最小样本数
- 使用集成学习方法

### 8.2 欠拟合问题
**表现**：
- 训练集和测试集准确率都低
- 树结构过于简单

**解决方案**：
- 增加树的深度
- 减少最小样本数
- 使用更复杂的特征

### 8.3 不稳定问题
**表现**：
- 数据微小变化导致树结构完全不同
- 预测结果不稳定

**解决方案**：
- 使用集成学习方法
- 增加训练数据
- 使用更稳定的算法

## 9. 扩展学习

### 9.1 相关算法
- 随机森林
- 梯度提升树
- XGBoost
- LightGBM

### 9.2 进阶主题
- 多输出决策树
- 决策树回归
- 在线学习决策树
- 分布式决策树

## 10. 总结

决策树是机器学习中最基础、最直观的算法之一。通过信息增益进行特征选择，递归构建树结构，最终实现分类或回归任务。理解决策树的原理对于掌握更复杂的集成学习方法至关重要。

在实现过程中，需要注意：
- 信息增益的计算
- 递归构建的停止条件
- 剪枝策略的选择
- 参数调优的方法

通过不断实践和学习，可以深入理解决策树的原理和应用，为后续的机器学习学习打下坚实的基础。