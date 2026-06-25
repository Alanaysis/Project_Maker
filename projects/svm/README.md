# SVM 支持向量机 - 从零实现

从零实现支持向量机 (SVM)，包含分类、回归、多分类和模型评估的完整实现。

## 学习目标

- 理解 SVM 的数学原理和几何直觉
- 掌握核函数的作用和实现 (线性核、RBF核、多项式核、Sigmoid核)
- 学会 SMO 优化算法
- 实现完整的 SVM 分类器和 SVR 回归器
- 掌握多分类策略 (One-vs-Rest, One-vs-One)
- 理解模型评估指标 (准确率、精确率、召回率、F1、MSE、R²)

## 项目结构

```
svm/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
├── src/                    # 源代码
│   ├── __init__.py         # 包初始化
│   ├── kernel.py           # 核函数实现
│   ├── smo.py              # SMO 算法
│   ├── svm.py              # SVM 分类器
│   ├── svr.py              # SVR 回归器
│   ├── multiclass.py       # 多分类策略
│   └── metrics.py          # 模型评估指标
├── tests/                  # 测试
│   └── test_svm.py         # 测试套件 (76 个测试)
└── examples/               # 实际应用示例
    ├── iris_classification.py    # 鸢尾花分类
    ├── digit_recognition.py      # 手写数字识别
    └── text_classification.py    # 文本分类
```

## 核心功能

### 1. 核函数

| 核函数 | 公式 | 适用场景 |
|--------|------|----------|
| 线性核 | K(x,y) = x·y | 线性可分数据 |
| RBF 核 | K(x,y) = exp(-γ‖x-y‖²) | 通用，非线性数据 |
| 多项式核 | K(x,y) = (x·y + c)^d | 特定非线性数据 |
| Sigmoid 核 | K(x,y) = tanh(γx·y + c) | 类似神经网络 |

### 2. SVM 分类器

```python
from src.svm import SVM

# 创建训练数据
X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
y = np.array([1, 1, -1, -1])

# 训练 SVM
svm = SVM(kernel="rbf", C=1.0, gamma=1.0)
svm.fit(X, y)

# 预测
predictions = svm.predict(X)
accuracy = svm.score(X, y)
```

### 3. SVR 回归器

```python
from src.svr import SVR

# 训练 SVR
svr = SVR(kernel="rbf", C=10.0, epsilon=0.1)
svr.fit(X, y)

# 预测
predictions = svr.predict(X)
r2 = svr.score(X, y)
```

### 4. 多分类策略

```python
from src.multiclass import OneVsRestSVM, OneVsOneSVM

# One-vs-Rest
ovr = OneVsRestSVM(kernel="rbf", C=1.0)
ovr.fit(X, y)  # y 可以是任意类别标签

# One-vs-One
ovo = OneVsOneSVM(kernel="rbf", C=1.0)
ovo.fit(X, y)
```

### 5. 模型评估

```python
from src.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, mean_squared_error,
    r2_score, mean_absolute_error,
)

# 分类指标
acc = accuracy_score(y_true, y_pred)
prec = precision_score(y_true, y_pred, average='macro')
rec = recall_score(y_true, y_pred, average='macro')
f1 = f1_score(y_true, y_pred, average='macro')
cm = confusion_matrix(y_true, y_pred)

# 回归指标
mse = mean_squared_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)
mae = mean_absolute_error(y_true, y_pred)
```

## 快速开始

### 安装依赖

```bash
pip install numpy pytest
```

### 运行示例

```bash
cd projects/svm

# 鸢尾花分类
python3 examples/iris_classification.py

# 手写数字识别
python3 examples/digit_recognition.py

# 文本分类
python3 examples/text_classification.py
```

### 运行测试

```bash
python3 -m pytest tests/ -v
```

## 数学原理

### SVM 原始问题

最小化:
$$\frac{1}{2} \|w\|^2 + C\sum_i \xi_i$$

约束:
$$y_i(w \cdot x_i + b) \geq 1 - \xi_i, \quad \xi_i \geq 0$$

### SVM 对偶问题

最大化:
$$\sum_i \alpha_i - \frac{1}{2} \sum_{i,j} \alpha_i \alpha_j y_i y_j K(x_i, x_j)$$

约束:
$$0 \leq \alpha_i \leq C, \quad \sum_i \alpha_i y_i = 0$$

### 决策函数

$$f(x) = \text{sign}\left(\sum_i \alpha_i y_i K(x_i, x) + b\right)$$

### SVR epsilon 不敏感损失

$$L_\epsilon(y, f(x)) = \max(0, |y - f(x)| - \epsilon)$$

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| kernel | 核函数类型: "linear", "rbf", "polynomial", "sigmoid" | "rbf" |
| C | 正则化参数，控制误分类惩罚 | 1.0 |
| gamma | RBF/Sigmoid 核的宽度参数 | 1.0 |
| degree | 多项式核的阶数 | 3 |
| coef0 | 多项式/Sigmoid 核的独立项系数 | 1.0 |
| epsilon | SVR 的 epsilon 不敏感损失宽度 | 0.1 |
| tol | SMO 算法的容差 | 1e-3 |
| max_passes | SMO 最大无变化迭代次数 | 10 |

## 参考资料

- [支持向量机通俗导论](https://blog.csdn.net/v_JULY_v/article/details/7624837)
- [Platt, J. (1998). Sequential Minimal Optimization](https://www.microsoft.com/en-us/research/publication/sequential-minimal-optimization-a-fast-algorithm-for-training-support-vector-machines/)
- [sklearn SVM 文档](https://scikit-learn.org/stable/modules/svm.html)

## License

MIT

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
