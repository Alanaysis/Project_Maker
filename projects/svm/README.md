# SVM 支持向量机 - 从零实现

从零实现支持向量机 (SVM)，理解最大间隔分类的核心原理。

## 学习目标

- 理解 SVM 的数学原理和几何直觉
- 掌握核函数的作用和实现
- 学会 SMO 优化算法
- 实现完整的 SVM 分类器

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
│   └── svm.py              # SVM 分类器
└── tests/                  # 测试
    └── test_svm.py         # 测试套件
```

## 核心概念

### 什么是 SVM?

支持向量机是一种二分类算法，目标是找到一个超平面，使得两类数据之间的间隔 (margin) 最大化。

```
      o o
    o o o        ← 正类
   o o o o
   =========  ← 决策边界 (超平面)
   x x x x
    x x x        ← 负类
      x x
```

**支持向量**是距离决策边界最近的训练样本点，它们"支撑"了决策边界的位置。

### 核函数

核函数允许 SVM 在高维空间中进行分类，而无需显式计算高维映射。这就是**核技巧** (Kernel Trick)。

| 核函数 | 公式 | 适用场景 |
|--------|------|----------|
| 线性核 | K(x,y) = x·y | 线性可分数据 |
| RBF 核 | K(x,y) = exp(-γ‖x-y‖²) | 通用，非线性数据 |
| 多项式核 | K(x,y) = (x·y + c)^d | 特定非线性数据 |

### SMO 算法

SMO (Sequential Minimal Optimization) 是求解 SVM 对偶问题的高效算法。

**核心思想**：
1. 选择两个拉格朗日乘子 αᵢ 和 αⱼ
2. 固定其他乘子，解析求解这两个乘子的最优值
3. 重复直到收敛

## 快速开始

### 安装依赖

```bash
pip install numpy pytest
```

### 使用示例

```python
import numpy as np
from src.svm import SVM

# 创建训练数据
X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
y = np.array([1, 1, -1, -1])

# 创建并训练 SVM
svm = SVM(kernel="rbf", C=1.0, gamma=1.0)
svm.fit(X, y)

# 预测
predictions = svm.predict(X)
print(f"预测结果: {predictions}")

# 评估
accuracy = svm.score(X, y)
print(f"准确率: {accuracy}")

# 查看支持向量
print(f"支持向量数量: {svm.get_n_support_vectors()}")
print(f"支持向量:\n{svm.get_support_vectors()}")
```

### 运行测试

```bash
cd projects/svm
python -m pytest tests/ -v
```

## 代码示例

### 线性核

```python
from src.kernel import linear_kernel

kernel = linear_kernel()
x = np.array([1.0, 2.0, 3.0])
y = np.array([4.0, 5.0, 6.0])

print(f"线性核: {kernel(x, y)}")  # 输出: 32.0
```

### RBF 核

```python
from src.kernel import rbf_kernel

kernel = rbf_kernel(gamma=1.0)
x = np.array([0.0, 0.0])
y = np.array([1.0, 1.0])

print(f"RBF 核: {kernel(x, y):.4f}")  # 输出: 0.1353
```

### 多项式核

```python
from src.kernel import polynomial_kernel

kernel = polynomial_kernel(degree=2, coef0=1.0)
x = np.array([1.0, 2.0])
y = np.array([3.0, 4.0])

print(f"多项式核: {kernel(x, y)}")  # 输出: 121.0
```

## 数学原理

### SVM 原始问题

最小化:
$$\frac{1}{2} \|w\|^2$$

约束:
$$y_i(w \cdot x_i + b) \geq 1, \quad \forall i$$

### SVM 对偶问题

最大化:
$$\sum_i \alpha_i - \frac{1}{2} \sum_{i,j} \alpha_i \alpha_j y_i y_j K(x_i, x_j)$$

约束:
$$0 \leq \alpha_i \leq C, \quad \forall i$$
$$\sum_i \alpha_i y_i = 0$$

### 决策函数

$$f(x) = \text{sign}\left(\sum_i \alpha_i y_i K(x_i, x) + b\right)$$

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| kernel | 核函数类型: "linear", "rbf", "polynomial" | "rbf" |
| C | 正则化参数，控制误分类惩罚 | 1.0 |
| gamma | RBF 核的宽度参数 | 1.0 |
| degree | 多项式核的阶数 | 3 |
| coef0 | 多项式核的独立项系数 | 1.0 |
| tol | SMO 算法的容差 | 1e-3 |
| max_passes | SMO 最大无变化迭代次数 | 10 |

## 参考资料

- [支持向量机通俗导论](https://blog.csdn.net/v_JULY_v/article/details/7624837)
- [Platt, J. (1998). Sequential Minimal Optimization](https://www.microsoft.com/en-us/research/publication/sequential-minimal-optimization-a-fast-algorithm-for-training-support-vector-machines/)
- [sklearn SVM 文档](https://scikit-learn.org/stable/modules/svm.html)

## License

MIT
