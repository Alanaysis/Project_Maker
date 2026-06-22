# 05 - 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- NumPy 1.20+
- pytest 6.0+

### 1.2 安装依赖

```bash
pip install numpy pytest
```

### 1.3 项目结构

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

## 2. 开发流程

### 2.1 开发步骤

1. **调研阶段**：理解 SVM 原理和实现方法
2. **设计阶段**：设计模块结构和接口
3. **实现阶段**：编写核心代码
4. **测试阶段**：编写和运行测试
5. **文档阶段**：编写文档和学习笔记

### 2.2 开发顺序

```
1. kernel.py     # 核函数模块
2. smo.py        # SMO 算法模块
3. svm.py        # SVM 分类器模块
4. test_svm.py   # 测试套件
5. docs/         # 文档
```

### 2.3 版本控制

```bash
# 初始化 git 仓库
git init

# 添加文件
git add .

# 提交
git commit -m "Initial commit: SVM implementation"
```

## 3. 代码规范

### 3.1 命名规范

- **类名**：使用 PascalCase，如 `SVM`, `SMO`
- **函数名**：使用 snake_case，如 `linear_kernel`, `precompute_kernel_matrix`
- **变量名**：使用 snake_case，如 `n_samples`, `alpha`
- **常量名**：使用大写字母，如 `MAX_PASSES`

### 3.2 文档规范

- 每个模块必须有模块级文档字符串
- 每个类必须有类级文档字符串
- 每个公共方法必须有方法级文档字符串
- 使用中文注释，便于学习理解

### 3.3 类型注解

```python
from typing import Callable, Optional, Tuple, Literal

def rbf_kernel(gamma: float = 1.0) -> Callable[[np.ndarray, np.ndarray], float]:
    pass

class SVM:
    alpha: Optional[np.ndarray] = None
    b: Optional[float] = None
```

### 3.4 代码风格

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 行长度不超过 88 字符
- 使用空行分隔函数和类

## 4. 模块开发

### 4.1 核函数模块 (kernel.py)

**开发步骤**：
1. 实现线性核函数
2. 实现 RBF 核函数
3. 实现多项式核函数
4. 实现核矩阵预计算

**关键代码**：

```python
def linear_kernel() -> Callable[[np.ndarray, np.ndarray], float]:
    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        return np.dot(x, y)
    return kernel
```

**测试要点**：
- 验证数学正确性
- 验证对称性
- 验证参数有效性

### 4.2 SMO 模块 (smo.py)

**开发步骤**：
1. 实现主优化循环
2. 实现误差计算
3. 实现 KKT 条件检查
4. 实现边界计算
5. 实现变量选择

**关键代码**：

```python
def optimize(self, K: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
    n_samples = K.shape[0]
    alpha = np.zeros(n_samples)
    b = 0.0
    passes = 0

    while passes < self.max_passes:
        num_changed_alphas = 0

        for i in range(n_samples):
            Ei = self._compute_error(i, K, y, alpha, b)

            if self._violates_kkt(y[i], Ei, alpha[i]):
                # ... 更新 alpha 和 b
                num_changed_alphas += 1

        if num_changed_alphas == 0:
            passes += 1
        else:
            passes = 0

    return alpha, b
```

**测试要点**：
- 验证收敛性
- 验证约束满足
- 验证 KKT 条件

### 4.3 SVM 模块 (svm.py)

**开发步骤**：
1. 实现初始化
2. 实现训练方法
3. 实现预测方法
4. 实现决策函数
5. 实现准确率计算

**关键代码**：

```python
def fit(self, X: np.ndarray, y: np.ndarray) -> "SVM":
    # 验证标签
    unique_labels = np.unique(y)
    if not np.array_equal(unique_labels, [-1, 1]):
        raise ValueError("标签必须为 +1 或 -1")

    # 预计算核矩阵
    K = precompute_kernel_matrix(X, self._kernel_func)

    # 使用 SMO 算法求解
    smo = SMO(C=self.C, tol=self.tol, max_passes=self.max_passes)
    self.alpha, self.b = smo.optimize(K, y)

    # 提取支持向量
    support_mask = self.alpha > 1e-7
    self.support_vectors = X[support_mask]
    self.support_vector_labels = y[support_mask]
    self.support_vector_alphas = self.alpha[support_mask]

    return self
```

**测试要点**：
- 验证训练功能
- 验证预测功能
- 验证支持向量提取

## 5. 测试开发

### 5.1 测试文件结构

```python
# tests/test_svm.py

import pytest
import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/svm/src')

from kernel import linear_kernel, rbf_kernel, polynomial_kernel, precompute_kernel_matrix
from smo import SMO
from svm import SVM


class TestLinearKernel:
    pass

class TestRBFKernel:
    pass

class TestPolynomialKernel:
    pass

class TestKernelMatrix:
    pass

class TestSMO:
    pass

class TestSVM:
    pass

class TestIntegration:
    pass
```

### 5.2 测试编写规范

- 每个测试方法只测试一个功能
- 测试方法名应该描述测试内容
- 使用 assert 进行断言
- 使用 pytest.raises 测试异常

### 5.3 测试数据准备

```python
# 简单线性可分数据
X_simple = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
y_simple = np.array([1, 1, -1, -1])

# XOR 问题数据
X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y_xor = np.array([-1, 1, 1, -1])

# 随机数据
np.random.seed(42)
X_random = np.random.randn(100, 2)
y_random = np.array([1] * 50 + [-1] * 50)
```

## 6. 文档开发

### 6.1 README.md

- 项目简介
- 学习目标
- 项目结构
- 核心概念
- 快速开始
- 代码示例
- 数学原理
- 参数说明
- 参考资料

### 6.2 LEARNING_NOTES.md

- 核心概念理解
- 数学推导
- 实现细节
- 调试经验
- 性能优化
- 与其他算法对比
- 进一步学习
- 总结

### 6.3 docs/ 目录

- 01-RESEARCH.md：调研文档
- 02-DESIGN.md：设计文档
- 03-IMPLEMENTATION.md：实现文档
- 04-TESTING.md：测试文档
- 05-DEVELOPMENT.md：开发文档

## 7. 调试技巧

### 7.1 常见问题

**问题 1**：导入错误
```python
# 解决方案：添加路径
import sys
sys.path.insert(0, '/path/to/svm/src')
```

**问题 2**：数值不稳定
```python
# 解决方案：使用容差
if abs(alpha[j] - alpha_j_old) < 1e-5:
    continue
```

**问题 3**：收敛慢
```python
# 解决方案：增加迭代次数
smo = SMO(C=1.0, tol=1e-3, max_passes=100)
```

### 7.2 调试工具

```python
# 打印调试信息
print(f"alpha: {alpha}")
print(f"b: {b}")
print(f"support vectors: {np.sum(alpha > 1e-7)}")

# 使用 pdb
import pdb; pdb.set_trace()
```

### 7.3 性能分析

```python
import time

start = time.time()
svm.fit(X, y)
end = time.time()

print(f"Training time: {end - start:.2f}s")
```

## 8. 部署和发布

### 8.1 打包

```bash
# 创建 setup.py
# 打包
python setup.py sdist bdist_wheel
```

### 8.2 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 上传
twine upload dist/*
```

### 8.3 版本管理

```python
# src/__init__.py
__version__ = "1.0.0"
```

## 9. 维护指南

### 9.1 代码维护

- 定期检查依赖更新
- 修复 bug
- 优化性能
- 添加新功能

### 9.2 文档维护

- 更新 README.md
- 更新学习笔记
- 更新文档

### 9.3 测试维护

- 添加新测试
- 修复失败的测试
- 提高测试覆盖率

## 10. 进一步开发

### 10.1 功能扩展

- [ ] 软间隔 SVM
- [ ] 多分类 SVM
- [ ] 支持向量回归 (SVR)
- [ ] 更多核函数

### 10.2 性能优化

- [ ] 使用 Cython 加速
- [ ] 并行计算
- [ ] 近似核方法

### 10.3 接口优化

- [ ] 添加概率输出
- [ ] 添加模型保存/加载
- [ ] 添加可视化工具
