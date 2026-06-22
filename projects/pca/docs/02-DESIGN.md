# 02 - 设计文档：PCA 主成分分析

## 1. 设计目标

从零实现一个完整的 PCA 降维算法，满足以下要求：

1. **教学性**：代码清晰，注释详细，便于理解算法原理
2. **完整性**：包含 PCA 的完整流程，从数据输入到降维输出
3. **可用性**：提供简洁的 API，方便使用
4. **可测试性**：模块化设计，便于编写单元测试
5. **可扩展性**：支持多种特征值分解方法

## 2. 架构设计

### 2.1 模块划分

```
src/
├── __init__.py          # 包入口，导出公共 API
├── pca.py               # PCA 核心类
├── covariance.py        # 协方差矩阵计算
├── eigen.py             # 特征值分解
└── visualization.py     # 可视化工具
```

### 2.2 模块职责

#### covariance.py - 协方差矩阵模块

职责：
- 数据中心化
- 协方差矩阵计算（向量化和手动两种实现）

主要函数：
- `center_data(X)` - 数据中心化
- `compute_covariance_matrix(X)` - 向量化计算协方差矩阵
- `compute_covariance_matrix_manual(X)` - 手动计算协方差矩阵（教学用）

#### eigen.py - 特征值分解模块

职责：
- 幂迭代法求解特征值
- QR 算法求解特征值
- 统一的分解接口

主要函数：
- `power_iteration(A)` - 幂迭代求最大特征值
- `deflate(A, λ, v)` - 矩阵压缩
- `eigen_decomposition_power(A, k)` - 幂迭代法求前 k 个特征值
- `qr_algorithm(A)` - QR 算法求所有特征值
- `eigen_decomposition(A, k, method)` - 统一接口

#### pca.py - PCA 核心类

职责：
- 封装完整的 PCA 流程
- 提供 fit/transform/fit_transform 接口
- 支持逆变换和重建误差计算

主要类：
- `PCA` - 主成分分析类

#### visualization.py - 可视化模块

职责：
- 2D/3D 散点图
- 解释方差图
- 双标图

主要函数：
- `plot_pca_2d()` - 2D 散点图
- `plot_pca_3d()` - 3D 散点图
- `plot_explained_variance()` - 解释方差图
- `plot_biplot()` - 双标图

## 3. 接口设计

### 3.1 PCA 类接口

```python
class PCA:
    def __init__(self, n_components=2, method="qr"):
        """
        Parameters
        ----------
        n_components : int or float
            - int: 保留的主成分数量
            - float (0, 1]: 按解释方差比例选择
        method : str
            特征值分解方法: "qr" 或 "power"
        """

    def fit(self, X) -> PCA:
        """拟合模型。"""

    def transform(self, X) -> np.ndarray:
        """投影数据。"""

    def fit_transform(self, X) -> np.ndarray:
        """拟合并投影。"""

    def inverse_transform(self, X_projected) -> np.ndarray:
        """反投影。"""

    def reconstruction_error(self, X) -> float:
        """计算重建误差。"""
```

### 3.2 函数接口

```python
# 协方差矩阵
def center_data(X) -> tuple[np.ndarray, np.ndarray]:
def compute_covariance_matrix(X) -> np.ndarray:

# 特征值分解
def eigen_decomposition(A, n_components=None, method="qr") -> tuple[np.ndarray, np.ndarray]:

# 可视化
def plot_pca_2d(X_projected, labels=None, ...) -> Figure:
def plot_explained_variance(ratio, ...) -> Figure:
def plot_biplot(X_projected, components, ...) -> Figure:
```

## 4. 数据流设计

### 4.1 PCA 拟合流程

```
输入数据 X (n_samples, n_features)
    │
    ▼
中心化: X_centered = X - mean(X)
    │
    ▼
协方差矩阵: C = (1/(n-1)) * X_centered^T * X_centered
    │
    ▼
特征值分解: C = V * Λ * V^T
    │
    ▼
选择前 k 个特征向量
    │
    ▼
保存: components_, explained_variance_, mean_
```

### 4.2 PCA 变换流程

```
新数据 X_new (n_samples, n_features)
    │
    ▼
中心化: X_centered = X_new - mean_
    │
    ▼
投影: X_projected = X_centered @ components_.T
    │
    ▼
输出: X_projected (n_samples, n_components)
```

### 4.3 逆变换流程

```
低维数据 X_projected (n_samples, n_components)
    │
    ▼
反投影: X_reconstructed = X_projected @ components_ + mean_
    │
    ▼
输出: X_reconstructed (n_samples, n_features)
```

## 5. 算法设计

### 5.1 协方差矩阵计算

选择矩阵乘法实现，而非逐元素计算：

```python
# 高效实现
cov = (1/(n-1)) * X.T @ X

# 教学实现
for i in range(d):
    for j in range(d):
        cov[i,j] = sum(X[:,i] * X[:,j]) / (n-1)
```

### 5.2 特征值分解

实现两种方法：

#### QR 算法（默认）
- 使用 Wilkinson shift 加速收敛
- 可以求解所有特征值
- 收敛速度快

#### 幂迭代法
- 使用压缩（Deflation）技术
- 只能求解前 k 个特征值
- 实现简单，便于理解

### 5.3 数值稳定性

- 对称化处理：A = (A + A.T) / 2
- Bessel 校正：使用 n-1 而非 n
- 归一化：特征向量归一化为单位向量

## 6. 错误处理设计

### 6.1 输入验证

- 检查输入维度（必须是 2D）
- 检查样本数量（至少 2 个）
- 检查特征数量（n_components 不能超过特征数）
- 检查 n_components 类型（int 或 float）

### 6.2 状态检查

- 检查模型是否已拟合
- 检查输入特征数是否匹配

### 6.3 异常类型

- `ValueError`: 输入参数不合法
- `RuntimeError`: 模型状态不正确

## 7. 可视化设计

### 7.1 设计原则

- 可选依赖：matplotlib 不是必需的
- 保存功能：支持保存图片到文件
- 自定义：支持自定义标题、大小等参数

### 7.2 图表类型

1. **2D 散点图**：展示降维后的数据分布
2. **3D 散点图**：展示三维投影
3. **解释方差图**：柱状图 + 累积曲线
4. **双标图**：同时展示样本和特征方向

## 8. 测试设计

### 8.1 测试策略

- 单元测试：测试每个函数/方法
- 集成测试：测试完整流程
- 边界测试：测试异常情况

### 8.2 测试覆盖

| 模块 | 测试内容 |
|------|----------|
| covariance | 中心化、协方差矩阵计算、与 numpy 结果对比 |
| eigen | 幂迭代、QR 算法、特征值分解、与 numpy 结果对比 |
| pca | fit、transform、fit_transform、inverse_transform、重建误差 |
| visualization | 函数调用不报错 |

### 8.3 验证方法

- 与 numpy.linalg.eigh 结果对比
- 已知矩阵的解析解验证
- 数值精度检查（小数点后 6 位）

## 9. 性能考虑

### 9.1 计算复杂度

- 中心化：O(n×d)
- 协方差矩阵：O(n×d²)
- QR 算法：O(d³ × iterations)
- 幂迭代：O(d² × iterations × k)
- 投影：O(n×d×k)

### 9.2 内存使用

- 主要内存消耗：数据矩阵 X (n×d)
- 协方差矩阵：d×d
- 特征向量：d×d

### 9.3 优化空间

- 使用 numpy 矩阵运算
- 避免不必要的数据复制
- 对于大规模数据，考虑使用随机化算法

## 10. 未来扩展

### 10.1 可能的扩展

- 核 PCA
- 增量 PCA
- 稀疏 PCA
- 标准化（StandardScaler）

### 10.2 接口兼容性

参考 scikit-learn 的接口设计，便于迁移和比较。
