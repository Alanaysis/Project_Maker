# 逻辑回归 (Logistic Regression)

从零实现逻辑回归，深入理解分类算法原理。

## 项目简介

本项目是一个学习型项目，旨在通过手动实现逻辑回归算法，深入理解：
- 逻辑回归的数学原理
- Sigmoid激活函数的作用
- 交叉熵损失函数的意义
- 梯度下降优化算法
- 二分类问题的解决方法

## 核心循环

```
数据 → Sigmoid → 损失计算 → 梯度更新 → 分类
```

## 项目结构

```
logistic-regression/
├── src/                        # 源代码
│   ├── logistic_regression.py # 逻辑回归实现
│   └── metrics.py             # 评估指标
├── tests/                      # 测试代码
│   ├── test_logistic_regression.py
│   └── test_metrics.py
├── examples/                   # 示例代码
│   ├── basic_usage.py
│   └── compare_sklearn.py
├── docs/                       # 文档
│   ├── 01-RESEARCH.md         # 调研报告
│   ├── 02-DESIGN.md           # 设计文档
│   ├── 03-IMPLEMENTATION.md   # 实现细节
│   ├── 04-TESTING.md          # 测试文档
│   └── 05-DEVELOPMENT.md      # 开发日志
├── main.py                     # 主入口
├── README.md                   # 本文件
└── LEARNING_NOTES.md           # 学习笔记
```

## 快速开始

### 环境要求

- Python 3.7+
- NumPy

### 安装依赖

```bash
pip install numpy
```

### 运行示例

```bash
# 运行基本示例
python main.py

# 运行与sklearn对比
python examples/compare_sklearn.py
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ --cov=src
```

## 使用示例

### 基本使用

```python
from src import LogisticRegression
import numpy as np

# 创建数据集
X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
y = np.array([1, 1, 0, 0])

# 创建并训练模型
model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
model.fit(X, y)

# 预测
predictions = model.predict(X)
probabilities = model.predict_proba(X)

# 评估
accuracy = model.score(X, y)
print(f"准确率: {accuracy:.2f}")
```

### 使用评估指标

```python
from src import classification_report
import numpy as np

y_true = np.array([1, 1, 0, 0, 1])
y_pred = np.array([1, 0, 0, 1, 1])

print(classification_report(y_true, y_pred))
```

## 核心API

### LogisticRegression类

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| learning_rate | float | 0.01 | 学习率 |
| n_iterations | int | 1000 | 迭代次数 |
| regularization | float | 0.0 | L2正则化强度 |
| threshold | float | 0.5 | 分类阈值 |
| verbose | bool | False | 是否打印训练过程 |

| 方法 | 说明 |
|------|------|
| fit(X, y) | 训练模型 |
| predict(X) | 预测类别 |
| predict_proba(X) | 预测概率 |
| score(X, y) | 计算准确率 |

### 评估指标函数

| 函数 | 说明 |
|------|------|
| accuracy_score(y_true, y_pred) | 准确率 |
| precision_score(y_true, y_pred) | 精确率 |
| recall_score(y_true, y_pred) | 召回率 |
| f1_score(y_true, y_pred) | F1分数 |
| confusion_matrix(y_true, y_pred) | 混淆矩阵 |
| classification_report(y_true, y_pred) | 分类报告 |

## 学习目标

通过本项目，你将学到：

1. **逻辑回归原理**
   - 线性模型 + Sigmoid激活
   - 概率解释
   - 决策边界

2. **损失函数**
   - 交叉熵损失的推导
   - 为什么选择交叉熵而非MSE
   - L2正则化

3. **优化算法**
   - 梯度下降原理
   - 梯度计算与推导
   - 学习率的影响

4. **评估指标**
   - 混淆矩阵
   - 准确率、精确率、召回率、F1
   - 不同指标的适用场景

## 与scikit-learn对比

本项目实现与scikit-learn的LogisticRegression对比：

```python
from examples.compare_sklearn import main
main()
```

## 文档说明

- [调研报告](docs/01-RESEARCH.md)：算法原理与背景
- [设计文档](docs/02-DESIGN.md)：架构设计与接口定义
- [实现细节](docs/03-IMPLEMENTATION.md)：核心代码解析
- [测试文档](docs/04-TESTING.md)：测试策略与用例
- [开发日志](docs/05-DEVELOPMENT.md)：开发过程记录

## 参考资源

- [scikit-learn LogisticRegression](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression)
- [Andrew Ng机器学习课程](https://www.coursera.org/learn/machine-learning)
- [周志华《机器学习》](https://book.douban.com/subject/26708119/)

## 许可证

本项目仅用于学习目的。
