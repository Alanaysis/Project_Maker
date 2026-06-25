# 决策树 (Decision Tree)

从零实现决策树，理解信息增益、基尼系数和方差减少。

## 项目简介

本项目是一个从零开始实现的决策树库，包含以下算法：

- **ID3**: 基于信息增益的决策树
- **C4.5**: 基于信息增益率的决策树
- **CART分类**: 基于基尼系数的决策树
- **CART回归**: 基于方差减少的决策树

## 功能特性

### 决策树算法

- ID3 算法（信息增益）
- C4.5 算法（信息增益率）
- CART 分类算法（基尼系数）
- CART 回归算法（方差减少）

### 剪枝技术

- 预剪枝：在构建树的过程中提前停止
- 后剪枝：代价复杂度剪枝（CCP）
- 减少错误剪枝（Reduced Error Pruning）

### 可视化

- 树结构可视化
- 决策边界可视化
- 特征重要性可视化
- 学习曲线
- 混淆矩阵

### 模型评估

- 准确率、精确率、召回率、F1 分数
- 均方误差（MSE）、均方根误差（RMSE）
- 平均绝对误差（MAE）
- R² 分数、调整 R² 分数

## 项目结构

```
decision-tree/
├── README.md                           # 项目说明文档
├── docs/                               # 文档目录
│   ├── 01-RESEARCH.md                  # 调研文档
│   ├── 02-ARCHITECTURE.md              # 架构设计
│   ├── 03-IMPLEMENTATION.md            # 实现细节
│   ├── 04-TESTING.md                   # 测试文档
│   └── 05-DEVELOPMENT.md               # 开发文档
├── src/                                # 源代码目录
│   ├── __init__.py                     # 包初始化
│   ├── decision_tree.py                # 基础决策树实现
│   ├── id3.py                          # ID3 算法
│   ├── c45.py                          # C4.5 算法
│   ├── cart_classifier.py              # CART 分类树
│   ├── cart_regressor.py               # CART 回归树
│   ├── pruning.py                      # 剪枝算法
│   ├── visualization.py                # 可视化模块
│   ├── evaluation.py                   # 评估指标
│   ├── utils.py                        # 工具函数
│   └── metrics.py                      # 评估指标
├── tests/                              # 测试目录
│   ├── __init__.py                     # 测试包初始化
│   ├── test_decision_tree.py           # 决策树测试
│   └── test_utils.py                   # 工具函数测试
├── examples/                           # 示例目录
│   ├── iris_classification.py          # 鸢尾花分类
│   ├── house_price_prediction.py       # 房价预测
│   └── feature_importance_analysis.py  # 特征重要性分析
└── LEARNING_NOTES.md                   # 学习笔记
```

## 快速开始

### 安装依赖

```bash
# 确保已安装 Python 3.6+
pip install numpy matplotlib
```

### 使用示例

#### CART 分类树

```python
import numpy as np
from src.cart_classifier import CARTClassifier

# 创建数据集
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([0, 0, 1, 1])

# 创建并训练决策树
tree = CARTClassifier(max_depth=3)
tree.fit(X, y)

# 预测
predictions = tree.predict(X)
print(f"预测结果: {predictions}")

# 评估
accuracy = tree.score(X, y)
print(f"准确率: {accuracy}")

# 特征重要性
print(f"特征重要性: {tree.feature_importances_}")
```

#### CART 回归树

```python
import numpy as np
from src.cart_regressor import CARTRegressor

# 创建数据集
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

# 创建并训练回归树
tree = CARTRegressor(max_depth=3)
tree.fit(X, y)

# 预测
predictions = tree.predict(X)
print(f"预测结果: {predictions}")

# 评估
r2 = tree.score(X, y)
print(f"R² 分数: {r2}")
```

#### ID3 决策树

```python
from src.id3 import ID3DecisionTree

# 创建并训练 ID3 决策树
tree = ID3DecisionTree(max_depth=3)
tree.fit(X, y)

# 预测
predictions = tree.predict(X)
```

#### 剪枝

```python
from src.pruning import PrePruningTree, PostPruningTree

# 预剪枝
pre_tree = PrePruningTree(
    max_depth=5,
    min_samples_split=5,
    min_samples_leaf=2,
    min_impurity_decrease=0.01
)
pre_tree.fit(X_train, y_train)

# 后剪枝
post_tree = PostPruningTree(max_depth=10, ccp_alpha=0.1)
post_tree.fit(X_train, y_train)
```

### 运行示例

```bash
# 鸢尾花分类
python examples/iris_classification.py

# 房价预测
python examples/house_price_prediction.py

# 特征重要性分析
python examples/feature_importance_analysis.py
```

## API 文档

### ID3DecisionTree

ID3 决策树分类器，使用信息增益作为特征选择标准。

#### 参数

- `max_depth` (int, optional): 最大深度，默认 None
- `min_samples_split` (int): 最小分裂样本数，默认 2
- `min_samples_leaf` (int): 最小叶节点样本数，默认 1

#### 方法

- `fit(X, y)`: 训练模型
- `predict(X)`: 预测新数据
- `score(X, y)`: 计算准确率
- `get_params()`: 获取模型参数
- `print_tree()`: 打印决策树结构

### C45DecisionTree

C4.5 决策树分类器，使用信息增益率作为特征选择标准。

#### 参数

- `max_depth` (int, optional): 最大深度，默认 None
- `min_samples_split` (int): 最小分裂样本数，默认 2
- `min_samples_leaf` (int): 最小叶节点样本数，默认 1
- `handle_continuous` (bool): 是否处理连续特征，默认 True

### CARTClassifier

CART 分类决策树，使用基尼系数作为特征选择标准。

#### 参数

- `max_depth` (int, optional): 最大深度，默认 None
- `min_samples_split` (int): 最小分裂样本数，默认 2
- `min_samples_leaf` (int): 最小叶节点样本数，默认 1
- `max_features` (int, optional): 最大特征数，默认 None

#### 方法

- `fit(X, y)`: 训练模型
- `predict(X)`: 预测新数据
- `predict_proba(X)`: 预测概率
- `score(X, y)`: 计算准确率
- `get_depth()`: 获取树的深度
- `get_n_leaves()`: 获取叶节点数量

### CARTRegressor

CART 回归决策树，使用方差减少作为特征选择标准。

#### 参数

- `max_depth` (int, optional): 最大深度，默认 None
- `min_samples_split` (int): 最小分裂样本数，默认 2
- `min_samples_leaf` (int): 最小叶节点样本数，默认 1

#### 方法

- `fit(X, y)`: 训练模型
- `predict(X)`: 预测新数据
- `score(X, y)`: 计算 R² 分数
- `mse(X, y)`: 计算均方误差
- `rmse(X, y)`: 计算均方根误差
- `mae(X, y)`: 计算平均绝对误差

### 工具函数

- `train_test_split(X, y, test_size=0.2, random_state=None)`: 划分数据集
- `accuracy_score(y_true, y_pred)`: 计算准确率
- `normalize(X)`: 数据标准化

### 评估指标

#### 分类指标

- `accuracy(y_true, y_pred)`: 准确率
- `precision(y_true, y_pred, average='macro')`: 精确率
- `recall(y_true, y_pred, average='macro')`: 召回率
- `f1_score(y_true, y_pred, average='macro')`: F1 分数
- `confusion_matrix(y_true, y_pred)`: 混淆矩阵

#### 回归指标

- `mean_squared_error(y_true, y_pred)`: 均方误差
- `root_mean_squared_error(y_true, y_pred)`: 均方根误差
- `mean_absolute_error(y_true, y_pred)`: 平均绝对误差
- `r2_score(y_true, y_pred)`: R² 分数
- `adjusted_r2_score(y_true, y_pred, n_features)`: 调整 R² 分数

### 可视化

- `plot_tree(tree, feature_names=None, class_names=None)`: 绘制决策树结构
- `plot_decision_boundary(tree, X, y, feature_indices=None)`: 绘制决策边界
- `plot_feature_importance(tree, feature_names=None)`: 绘制特征重要性
- `plot_learning_curve(tree_class, X, y)`: 绘制学习曲线
- `plot_confusion_matrix(y_true, y_pred, class_names=None)`: 绘制混淆矩阵
- `print_tree_text(tree, feature_names=None)`: 以文本形式打印决策树

## 测试

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行带详细输出的测试
python -m pytest tests/ -v

# 运行特定测试
python tests/test_decision_tree.py
```

### 测试覆盖率

- 语句覆盖率：>90%
- 分支覆盖率：>80%
- 函数覆盖率：100%

## 学习资源

### 文档

1. [调研文档](docs/01-RESEARCH.md) - 决策树的基本概念和原理
2. [架构设计](docs/02-ARCHITECTURE.md) - 项目的整体架构设计
3. [实现细节](docs/03-IMPLEMENTATION.md) - 核心算法的实现细节
4. [测试文档](docs/04-TESTING.md) - 测试策略和测试用例
5. [开发文档](docs/05-DEVELOPMENT.md) - 开发流程和最佳实践

### 学习笔记

- [学习笔记](LEARNING_NOTES.md) - 决策树学习过程中的心得体会

## 扩展阅读

### 相关算法

- 随机森林 (Random Forest)
- 梯度提升树 (Gradient Boosting Tree)
- XGBoost
- LightGBM

### 参考资料

- [scikit-learn 决策树文档](https://scikit-learn.org/stable/modules/tree.html)
- [机器学习实战](https://book.douban.com/subject/26708119/)
- [统计学习方法](https://book.douban.com/subject/33437381/)

## 许可证

本项目采用 MIT 许可证

## 致谢

- 感谢 scikit-learn 项目的启发
- 感谢所有贡献者的努力
- 感谢开源社区的支持
