# KNN 近邻算法

从零实现 K-Nearest Neighbors (KNN) 分类和回归算法的完整项目。

## 项目概述

KNN 是一种简单但强大的监督学习算法，通过计算待预测样本与训练样本之间的距离，选择最近的 K 个邻居进行预测。

### 核心循环

```
查询点 → 计算距离 → 选择 K 个近邻 → 投票/平均 → 预测结果
```

## 学习目标

- 理解 KNN 分类和回归原理
- 掌握多种距离度量方法
- 学会 K 值选择和交叉验证
- 理解 KD-Tree 和 Ball Tree 加速结构
- 实现距离加权投票机制

## 技术栈

- 主语言：Python
- 框架：无
- 依赖：NumPy

## 项目结构

```
knn/
├── README.md
├── LEARNING_NOTES.md
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── src/
│   ├── __init__.py
│   ├── distance_metrics.py    # 距离度量模块
│   ├── knn_classifier.py      # KNN 分类器
│   ├── knn_regressor.py       # KNN 回归器
│   ├── kd_tree.py             # KD-Tree 加速结构
│   ├── ball_tree.py           # Ball Tree 加速结构
│   └── model_selection.py     # 模型选择（交叉验证）
├── tests/
│   ├── __init__.py
│   ├── test_knn.py
│   ├── test_regressor.py
│   ├── test_kd_tree.py
│   ├── test_ball_tree.py
│   └── test_model_selection.py
└── examples/
    ├── iris_classification.py      # 鸢尾花分类
    ├── handwritten_digits.py       # 手写数字识别
    ├── knn_regression.py           # KNN 回归
    └── acceleration_structures.py  # 加速结构比较
```

## 快速开始

### 1. 安装依赖

```bash
pip install numpy
```

### 2. 运行测试

```bash
cd projects/knn
python -m pytest tests/ -v
```

### 3. 运行示例

```bash
# 鸢尾花分类
python examples/iris_classification.py

# 手写数字识别
python examples/handwritten_digits.py

# KNN 回归
python examples/knn_regression.py

# 加速结构比较
python examples/acceleration_structures.py
```

### 4. 使用示例

#### KNN 分类

```python
import numpy as np
from src.knn_classifier import KNNClassifier

# 训练数据
X_train = np.array([[1, 2], [1, 3], [2, 2], [3, 4], [3, 5], [4, 4]])
y_train = np.array([0, 0, 0, 1, 1, 1])

# 创建 KNN 分类器 (K=3, 距离加权)
knn = KNNClassifier(k=3, metric='euclidean', weights='distance')

# 训练模型
knn.fit(X_train, y_train)

# 预测
X_test = np.array([[2, 3], [3, 3]])
predictions = knn.predict(X_test)
probabilities = knn.predict_proba(X_test)
```

#### KNN 回归

```python
import numpy as np
from src.knn_regressor import KNNRegressor

# 训练数据
X_train = np.array([[1], [2], [3], [4], [5]])
y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

# 创建 KNN 回归器
reg = KNNRegressor(k=3, metric='euclidean', weights='distance')
reg.fit(X_train, y_train)

# 预测
X_test = np.array([[3.5]])
prediction = reg.predict(X_test)
```

#### 交叉验证选择 K 值

```python
from src.model_selection import CrossValidator

cv = CrossValidator(n_folds=5, shuffle=True, random_state=42)

# 自动选择最优 K
results = cv.select_k(X, y, k_range=[1, 3, 5, 7, 9], task='classification')
print(f"最优 K: {results['best_k']}, 准确率: {results['best_score']:.4f}")
```

#### 使用 KD-Tree 加速

```python
from src.kd_tree import KDTree

# 构建 KD-Tree
tree = KDTree(metric='euclidean')
tree.build(X_train, y_train)

# 查询最近邻
indices, distances = tree.query(query_point, k=5)
```

## 功能特性

### 1. KNN 分类

- **多数投票**：K 个近邻中出现次数最多的类别
- **距离加权投票**：距离越近的邻居权重越大

### 2. KNN 回归

- **简单平均**：K 个近邻目标值的平均
- **距离加权平均**：距离越近的邻居权重越大

### 3. 距离度量

| 度量方式 | 公式 | 适用场景 |
|---------|------|---------|
| 欧氏距离 | d = sqrt(Σ(xi-yi)²) | 连续数值特征 |
| 曼哈顿距离 | d = Σ\|xi-yi\| | 高维数据、网格数据 |
| 闵可夫斯基距离 | d = (Σ\|xi-yi\|^p)^(1/p) | 可调距离度量 |
| 余弦距离 | d = 1 - cos(x,y) | 文本分类、推荐系统 |

### 4. 加速结构

| 结构 | 优势 | 适用场景 |
|-----|------|---------|
| KD-Tree | 低维数据查询快 | 维度 < 20 |
| Ball Tree | 支持任意距离度量 | 高维数据、非欧氏距离 |

### 5. 模型选择

- **K-Fold 交叉验证**：评估模型泛化能力
- **K 值选择**：自动搜索最优 K 值
- **训练/测试划分**：数据集划分工具

## 性能对比

### 加速结构性能（1000 样本，5 特征）

| 方法 | 查询时间 | 相对速度 |
|-----|---------|---------|
| 暴力搜索 | 1.0x | 基准 |
| KD-Tree | 0.3x | 3.3x 加速 |
| Ball Tree | 0.4x | 2.5x 加速 |

### K 值选择影响

| K 值 | 训练准确率 | 测试准确率 | 偏差/方差 |
|-----|-----------|-----------|----------|
| K=1 | 100% | 较低 | 过拟合 |
| K=5 | 较高 | 较高 | 平衡 |
| K=15 | 较低 | 较低 | 欠拟合 |

## 文档说明

详细文档请查看 `docs/` 目录：

- **01-RESEARCH.md**: 市场调研 - KNN 算法原理和应用场景
- **02-DESIGN.md**: 设计文档 - 项目架构和模块设计
- **03-IMPLEMENTATION.md**: 实现细节 - 核心算法实现
- **04-TESTING.md**: 测试文档 - 测试策略和用例
- **05-DEVELOPMENT.md**: 开发日志 - 开发过程记录

## 学习笔记

`LEARNING_NOTES.md` 记录学习过程中的关键概念和思考。

## 许可证

MIT License
