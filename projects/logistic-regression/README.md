# 逻辑回归 (Logistic Regression)

从零实现逻辑回归，深入理解分类算法原理。

## 项目简介

本项目是一个学习型项目，旨在通过手动实现逻辑回归算法，深入理解：
- 逻辑回归的数学原理
- Sigmoid激活函数的作用
- 交叉熵损失函数的意义
- 梯度下降优化算法
- 多分类问题的解决方法

## 核心循环

```
数据 → Sigmoid → 损失计算 → 梯度更新 → 分类
```

## 项目结构

```
logistic-regression/
├── src/                        # 源代码
│   ├── logistic_regression.py  # 基础逻辑回归实现
│   ├── multiclass.py           # 多分类实现
│   ├── regularization.py       # 正则化实现
│   ├── metrics.py              # 评估指标
│   ├── feature_engineering.py  # 特征工程
│   └── optimizers.py           # 优化算法
├── examples/                   # 示例代码
│   ├── basic_usage.py          # 基本使用
│   ├── spam_classification.py  # 垃圾邮件分类
│   ├── disease_diagnosis.py    # 疾病诊断
│   └── credit_scoring.py       # 信用评分
├── tests/                      # 测试代码
├── docs/                       # 文档
│   ├── 01_RESEARCH.md          # 调研报告
│   ├── 02_REQUIREMENTS.md      # 需求分析
│   ├── 03_DESIGN.md            # 技术设计
│   ├── 04_PRODUCT.md           # 产品思考
│   └── 05_DEVELOPMENT.md       # 开发手册
├── main.py                     # 主入口
├── README.md                   # 本文件
└── requirements.txt            # 依赖
```

## 快速开始

### 环境要求

- Python 3.7+
- NumPy

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例

```bash
# 运行基本示例
python main.py

# 运行实际应用示例
python examples/spam_classification.py
python examples/disease_diagnosis.py
python examples/credit_scoring.py
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

### 使用ROC曲线和AUC

```python
from src import roc_curve, auc_score
import numpy as np

y_true = np.array([1, 1, 0, 0, 1])
y_scores = np.array([0.9, 0.8, 0.3, 0.1, 0.7])

fpr, tpr, thresholds = roc_curve(y_true, y_scores)
auc = auc_score(fpr, tpr)
print(f"AUC: {auc:.4f}")
```

### 多分类

```python
from src import OneVsRestClassifier, SoftmaxRegression
import numpy as np

# One-vs-Rest
X = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
y = np.array([0, 1, 2, 0])

ovr = OneVsRestClassifier(learning_rate=0.1, n_iterations=1000)
ovr.fit(X, y)
predictions = ovr.predict(X)
```

### 正则化

```python
from src import LogisticRegressionL1, LogisticRegressionL2, ElasticNet
import numpy as np

X = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
y = np.array([0, 0, 1, 1])

# L1正则化
model_l1 = LogisticRegressionL1(learning_rate=0.1, n_iterations=1000, lambda_param=0.1)
model_l1.fit(X, y)

# L2正则化
model_l2 = LogisticRegressionL2(learning_rate=0.1, n_iterations=1000, lambda_param=0.1)
model_l2.fit(X, y)

# Elastic Net
model_en = ElasticNet(learning_rate=0.1, n_iterations=1000, l1_ratio=0.5, lambda_param=0.1)
model_en.fit(X, y)
```

### 特征工程

```python
from src import StandardScaler, MinMaxScaler, cross_validate
import numpy as np

X = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
y = np.array([0, 0, 1, 1])

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 交叉验证
from src import LogisticRegression
model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
scores = cross_validate(model, X, y, cv=5)
print(f"交叉验证分数: {scores}")
```

### 优化算法

```python
from src import BatchGradientDescent, StochasticGradientDescent, MiniBatchGradientDescent
import numpy as np

X = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
y = np.array([0, 0, 1, 1])

# 批量梯度下降
model_bgd = BatchGradientDescent(learning_rate=0.1, n_iterations=1000)
model_bgd.fit(X, y)

# 随机梯度下降
model_sgd = StochasticGradientDescent(learning_rate=0.01, n_iterations=100)
model_sgd.fit(X, y)

# 小批量梯度下降
model_mbgd = MiniBatchGradientDescent(learning_rate=0.1, n_iterations=1000, batch_size=32)
model_mbgd.fit(X, y)
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
| roc_curve(y_true, y_scores) | ROC曲线 |
| auc_score(fpr, tpr) | AUC分数 |

## 学习目标

通过本项目，你将学到：

1. **逻辑回归原理**
   - 线性模型 + Sigmoid激活
   - 概率解释
   - 决策边界

2. **损失函数**
   - 交叉熵损失的推导
   - 为什么选择交叉熵而非MSE
   - L1/L2正则化

3. **优化算法**
   - 梯度下降原理
   - 梯度计算与推导
   - 学习率的影响

4. **评估指标**
   - 混淆矩阵
   - 准确率、精确率、召回率、F1
   - ROC曲线和AUC

## 文档说明

- [调研报告](docs/01_RESEARCH.md)：算法原理与背景
- [需求分析](docs/02_REQUIREMENTS.md)：功能需求与算法清单
- [技术设计](docs/03_DESIGN.md)：架构设计与接口定义
- [产品思考](docs/04_PRODUCT.md)：学习目标与关键要点
- [开发手册](docs/05_DEVELOPMENT.md)：环境配置与运行方式

## 参考资源

- [scikit-learn LogisticRegression](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression)
- [Andrew Ng机器学习课程](https://www.coursera.org/learn/machine-learning)
- [周志华《机器学习》](https://book.douban.com/subject/26708119/)

## 许可证

本项目仅用于学习目的。
