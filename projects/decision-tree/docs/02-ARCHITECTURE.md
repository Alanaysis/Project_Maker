# 02 - 决策树项目架构设计

## 1. 项目结构

```
decision-tree/
├── README.md
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── src/
│   ├── __init__.py
│   ├── decision_tree.py
│   ├── utils.py
│   └── metrics.py
├── tests/
│   ├── __init__.py
│   ├── test_decision_tree.py
│   └── test_utils.py
├── examples/
│   └── example_usage.py
└── LEARNING_NOTES.md
```

## 2. 核心模块设计

### 2.1 决策树分类器 (`src/decision_tree.py`)

#### 主要类：
- `DecisionTreeClassifier`: 决策树分类器主类

#### 主要方法：
- `fit(X, y)`: 训练模型
- `predict(X)`: 预测新数据
- `score(X, y)`: 计算准确率

#### 内部方法：
- `_build_tree(X, y)`: 递归构建决策树
- `_calculate_entropy(y)`: 计算熵
- `_calculate_information_gain(X, y, feature_index)`: 计算信息增益
- `_find_best_split(X, y)`: 寻找最佳分裂特征
- `_split_dataset(X, y, feature_index, value)`: 分裂数据集
- `_create_leaf_node(y)`: 创建叶节点

### 2.2 工具函数 (`src/utils.py`)

#### 主要函数：
- `train_test_split(X, y, test_size=0.2, random_state=None)`: 数据集划分
- `accuracy_score(y_true, y_pred)`: 准确率计算

### 2.3 评估指标 (`src/metrics.py`)

#### 主要函数：
- `confusion_matrix(y_true, y_pred)`: 混淆矩阵
- `precision_score(y_true, y_pred)`: 精确率
- `recall_score(y_true, y_pred)`: 召回率
- `f1_score(y_true, y_pred)`: F1分数

## 3. 数据结构设计

### 3.1 节点结构

```python
class TreeNode:
    def __init__(self, feature_index=None, threshold=None, left=None, right=None, value=None):
        self.feature_index = feature_index  # 分裂特征索引
        self.threshold = threshold          # 分裂阈值
        self.left = left                   # 左子树
        self.right = right                 # 右子树
        self.value = value                 # 叶节点的预测值
```

### 3.2 决策树结构

```python
class DecisionTreeClassifier:
    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1):
        self.root = None                    # 树的根节点
        self.max_depth = max_depth          # 最大深度
        self.min_samples_split = min_samples_split  # 最小分裂样本数
        self.min_samples_leaf = min_samples_leaf    # 最小叶节点样本数
```

## 4. 算法流程设计

### 4.1 训练流程

```
输入: 训练数据 (X, y)
1. 从根节点开始
2. 计算当前节点的熵
3. 如果满足停止条件，创建叶节点并返回
4. 对每个特征计算信息增益
5. 选择信息增益最大的特征进行分裂
6. 根据特征值将数据集分为左右子集
7. 递归构建左子树和右子树
8. 返回构建好的树
```

### 4.2 预测流程

```
输入: 待预测数据 x
1. 从根节点开始
2. 如果当前节点是叶节点，返回预测值
3. 根据特征值选择左子树或右子树
4. 递归进行预测
5. 返回最终预测结果
```

## 5. 接口设计

### 5.1 公共接口

```python
class DecisionTreeClassifier:
    def fit(self, X, y):
        """
        训练决策树模型
        
        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 目标向量 (n_samples,)
        
        返回:
        self: 训练后的模型
        """
        pass
    
    def predict(self, X):
        """
        预测新数据
        
        参数:
        X: 特征矩阵 (n_samples, n_features)
        
        返回:
        predictions: 预测结果 (n_samples,)
        """
        pass
    
    def score(self, X, y):
        """
        计算准确率
        
        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 真实标签 (n_samples,)
        
        返回:
        accuracy: 准确率
        """
        pass
```

## 6. 扩展性设计

### 6.1 支持多种特征选择标准

通过参数化设计，支持：
- 信息增益 (ID3)
- 信息增益比 (C4.5)
- 基尼指数 (CART)

### 6.2 支持剪枝策略

- 预剪枝：通过参数控制最大深度、最小样本数等
- 后剪枝：预留接口，未来可扩展

## 7. 性能考虑

### 7.1 时间复杂度
- 构建：O(n * m * log n)，其中 n 是样本数，m 是特征数
- 预测：O(log n)

### 7.2 空间复杂度
- 存储：O(n)

## 8. 错误处理

- 输入验证：检查数据类型、维度一致性
- 边界情况处理：空数据集、单类别数据等
- 数值稳定性：避免对数计算中的零值

## 9. 总结

本项目采用模块化设计，将决策树的核心算法、工具函数和评估指标分离，便于维护和扩展。通过清晰的接口设计和合理的类结构，实现了一个功能完整、易于理解的决策树分类器。