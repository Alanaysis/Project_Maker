# PCA 主成分分析

从零实现 PCA 降维算法，深入理解降维原理、协方差矩阵和特征值分解。

## 项目概述

主成分分析（Principal Component Analysis, PCA）是一种经典的无监督降维方法。本项目从零开始实现 PCA，不依赖任何机器学习库，仅使用 NumPy 进行数值计算。

### 核心循环

```
数据 → 中心化 → 协方差矩阵 → 特征值分解 → 投影
```

### 学习目标

- 理解降维原理
- 掌握协方差矩阵
- 学会特征值分解
- 掌握核 PCA 非线性降维
- 理解增量 PCA 大数据处理

## 项目结构

```
pca/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记
├── docs/                     # 文档目录
│   ├── 01-RESEARCH.md        # 调研报告
│   ├── 02-DESIGN.md          # 设计文档
│   ├── 03-IMPLEMENTATION.md  # 实现细节
│   ├── 04-TESTING.md         # 测试文档
│   └── 05-DEVELOPMENT.md     # 开发日志
├── src/                      # 源代码
│   ├── __init__.py
│   ├── pca.py                # PCA 核心类
│   ├── kernel_pca.py         # 核 PCA（非线性降维）
│   ├── incremental_pca.py    # 增量 PCA（大数据处理）
│   ├── covariance.py         # 协方差矩阵计算
│   ├── eigen.py              # 特征值分解
│   └── visualization.py      # 可视化工具
├── tests/                    # 测试代码
│   ├── test_covariance.py
│   ├── test_eigen.py
│   ├── test_pca.py
│   ├── test_kernel_pca.py
│   └── test_incremental_pca.py
├── examples/                 # 示例代码
│   ├── basic_usage.py        # 基本使用
│   ├── visualization_demo.py # 可视化示例
│   ├── practical_application.py  # 实际应用
│   ├── kernel_pca_demo.py    # 核 PCA 演示
│   ├── incremental_pca_demo.py  # 增量 PCA 演示
│   ├── denoising_demo.py     # 去噪演示
│   └── face_recognition_demo.py  # 人脸识别演示
└── data/                     # 数据目录
```

## 快速开始

### 环境要求

- Python >= 3.10
- NumPy >= 1.24
- matplotlib >= 3.7（可选，用于可视化）

### 安装依赖

```bash
pip install numpy matplotlib
```

### 基本使用

```python
import numpy as np
from src.pca import PCA

# 创建示例数据
np.random.seed(42)
X = np.random.randn(100, 5)

# PCA 降维到 2 维
pca = PCA(n_components=2)
X_reduced = pca.fit_transform(X)

print(f"原始形状: {X.shape}")
print(f"降维后形状: {X_reduced.shape}")
print(f"解释方差比例: {pca.explained_variance_ratio_}")
```

### 运行示例

```bash
cd projects/pca

# 基本使用示例
python examples/basic_usage.py

# 可视化示例
python examples/visualization_demo.py

# 实际应用示例
python examples/practical_application.py

# 核 PCA 演示
python examples/kernel_pca_demo.py

# 增量 PCA 演示
python examples/incremental_pca_demo.py

# 去噪演示
python examples/denoising_demo.py

# 人脸识别演示
python examples/face_recognition_demo.py
```

### 运行测试

```bash
cd projects/pca
python -m pytest tests/ -v
```

## API 参考

### PCA 类

```python
class PCA:
    def __init__(self, n_components=2, method="qr"):
        """
        Parameters
        ----------
        n_components : int or float
            保留的主成分数量。
            - int: 直接指定数量
            - float (0, 1]: 按解释方差比例选择
        method : str
            特征值分解方法: "qr" 或 "power"
        """
```

#### 主要方法

| 方法 | 说明 |
|------|------|
| `fit(X)` | 拟合 PCA 模型 |
| `transform(X)` | 将数据投影到主成分空间 |
| `fit_transform(X)` | 拟合并投影（组合方法） |
| `inverse_transform(X)` | 反投影回原始空间 |
| `reconstruction_error(X)` | 计算重建误差 |

#### 属性

| 属性 | 说明 |
|------|------|
| `components_` | 主成分方向（特征向量） |
| `explained_variance_` | 各主成分解释的方差（特征值） |
| `explained_variance_ratio_` | 各主成分解释的方差比例 |
| `mean_` | 训练数据的均值 |

## API 参考（续）

### KernelPCA 类

```python
class KernelPCA:
    def __init__(self, n_components=2, kernel='rbf', gamma=None, degree=3, coef0=1.0):
        """
        核主成分分析，用于非线性降维。

        Parameters
        ----------
        n_components : int
            保留的主成分数量。
        kernel : str
            核函数类型: 'rbf', 'poly', 'sigmoid', 'linear'
        gamma : float or None
            RBF 核参数。None 表示使用 1/n_features。
        degree : int
            多项式核的阶数。
        coef0 : float
            poly 和 sigmoid 核的常数项。
        """
```

#### 使用示例

```python
from src.kernel_pca import KernelPCA

# RBF 核 PCA
kpca = KernelPCA(n_components=2, kernel='rbf', gamma=0.1)
X_transformed = kpca.fit_transform(X)
```

### IncrementalPCA 类

```python
class IncrementalPCA:
    def __init__(self, n_components=None, batch_size=None):
        """
        增量主成分分析，适用于大数据集。

        Parameters
        ----------
        n_components : int or None
            保留的主成分数量。None 表示保留所有成分。
        batch_size : int or None
            每批处理的样本数量。
        """
```

#### 使用示例

```python
from src.incremental_pca import IncrementalPCA

# 增量 PCA
ipca = IncrementalPCA(n_components=5, batch_size=100)
X_transformed = ipca.fit_transform(X)

# 或者分批处理
ipca = IncrementalPCA(n_components=5)
for batch in data_batches:
    ipca.partial_fit(batch)
```

## 算法详解

### 1. 数据中心化

```python
X_centered = X - np.mean(X, axis=0)
```

将数据的每个特征减去其均值，使数据以原点为中心。

### 2. 协方差矩阵

```python
cov = (1 / (n-1)) * X_centered.T @ X_centered
```

协方差矩阵描述特征之间的线性关系：
- 对角线元素：各特征的方差
- 非对角线元素：特征间的协方差

### 3. 特征值分解

```python
eigenvalues, eigenvectors = np.linalg.eigh(cov)
```

将协方差矩阵分解为特征值和特征向量：
- 特征值：表示各主成分方向上的方差
- 特征向量：主成分方向

### 4. 投影

```python
X_projected = X_centered @ eigenvectors[:, :k]
```

将数据投影到前 k 个主成分方向上，实现降维。

## 实际应用

### 数据压缩

PCA 可以减少数据维度，同时保留主要信息。例如，将 50 维数据压缩到 5 维，可以节省 90% 的存储空间。

### 噪声过滤

通过保留主要成分，去除低方差成分（通常是噪声），可以提高数据质量。参见 `examples/denoising_demo.py`。

### 特征工程

PCA 降维后的特征可以作为机器学习模型的输入，通常能提高模型性能。

### 数据探索

通过分析解释方差比例，可以发现数据的内在维度和结构。

### 人脸识别（特征脸）

PCA 可以提取人脸的主要特征（特征脸），用于人脸识别。参见 `examples/face_recognition_demo.py`。

### 非线性降维

核 PCA 通过核技巧实现非线性降维，适用于线性不可分的数据。参见 `examples/kernel_pca_demo.py`。

### 大数据处理

增量 PCA 可以分批处理数据，适用于无法一次性加载到内存的大数据集。参见 `examples/incremental_pca_demo.py`。

## 可视化

### 2D 散点图

```python
from src.visualization import plot_pca_2d

fig = plot_pca_2d(X_reduced, labels=labels)
```

### 解释方差图

```python
from src.visualization import plot_explained_variance

fig = plot_explained_variance(pca.explained_variance_ratio_)
```

### 双标图

```python
from src.visualization import plot_biplot

fig = plot_biplot(X_reduced, pca.components_, feature_names=names)
```

## 扩展阅读

- [PCA 维基百科](https://en.wikipedia.org/wiki/Principal_component_analysis)
- [特征值分解](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix)
- [协方差矩阵](https://en.wikipedia.org/wiki/Covariance_matrix)

## 许可证

本项目仅用于学习目的。
