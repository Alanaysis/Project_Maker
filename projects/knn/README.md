# KNN 近邻分类器

从零实现 K-Nearest Neighbors (KNN) 分类算法的项目。

## 项目概述

KNN 是一种简单但强大的监督学习算法，通过计算待分类样本与训练样本之间的距离，选择最近的 K 个邻居进行投票来决定分类结果。

### 核心循环

```
查询点 → 计算距离 → 选择 K 个近邻 → 投票分类
```

## 学习目标

- 理解 KNN 原理
- 掌握距离度量
- 学会 K 值选择

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
│   ├── knn_classifier.py
│   └── distance_metrics.py
└── tests/
    ├── __init__.py
    └── test_knn.py
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

### 3. 使用示例

```python
import numpy as np
from src.knn_classifier import KNNClassifier

# 训练数据
X_train = np.array([[1, 2], [1, 3], [2, 2], [3, 4], [3, 5], [4, 4]])
y_train = np.array([0, 0, 0, 1, 1, 1])

# 创建 KNN 分类器 (K=3, 使用欧氏距离)
knn = KNNClassifier(k=3, metric='euclidean')

# 训练模型
knn.fit(X_train, y_train)

# 预测新样本
X_test = np.array([[2, 3], [3, 3]])
predictions = knn.predict(X_test)
print(f"预测结果: {predictions}")
```

## 功能特性

### 1. 距离度量

支持多种距离计算方式：
- 欧氏距离 (Euclidean)
- 曼哈顿距离 (Manhattan)
- 闵可夫斯基距离 (Minkowski)
- 余弦相似度 (Cosine)

### 2. K 值选择

提供交叉验证方法选择最优 K 值。

### 3. 分类功能

支持多分类任务，使用多数投票机制。

## 文档说明

详细文档请查看 `docs/` 目录：

- **01-RESEARCH.md**: 市场调研 - 了解 KNN 算法原理和应用场景
- **02-DESIGN.md**: 设计文档 - 项目架构和模块设计
- **03-IMPLEMENTATION.md**: 实现细节 - 核心算法实现
- **04-TESTING.md**: 测试文档 - 测试策略和用例
- **05-DEVELOPMENT.md**: 开发日志 - 开发过程记录

## 学习笔记

`LEARNING_NOTES.md` 记录学习过程中的关键概念和思考。

## 许可证

MIT License