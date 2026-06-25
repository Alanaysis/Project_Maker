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

## 2. 开发流程

### 2.1 开发步骤

1. **调研阶段**：理解 SVM 原理和实现方法
2. **设计阶段**：设计模块结构和接口
3. **实现阶段**：编写核心代码
4. **测试阶段**：编写和运行测试
5. **文档阶段**：编写文档和学习笔记

### 2.2 开发顺序

```
1. kernel.py      # 核函数模块
2. smo.py         # SMO 算法模块
3. svm.py         # SVM 分类器模块
4. svr.py         # SVR 回归器模块
5. multiclass.py  # 多分类策略模块
6. metrics.py     # 模型评估指标模块
7. test_svm.py    # 测试套件
8. examples/      # 实际应用示例
9. docs/          # 文档
```

## 3. 代码规范

### 3.1 命名规范

- **类名**：使用 PascalCase，如 `SVM`, `SMO`, `OneVsRestSVM`
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

## 4. 模块开发

### 4.1 核函数模块 (kernel.py)

**开发步骤**：
1. 实现线性核函数
2. 实现 RBF 核函数
3. 实现多项式核函数
4. 实现 Sigmoid 核函数
5. 实现核矩阵预计算

### 4.2 SMO 模块 (smo.py)

**开发步骤**：
1. 实现主优化循环
2. 实现误差计算
3. 实现 KKT 条件检查
4. 实现边界计算
5. 实现变量选择

### 4.3 SVM 模块 (svm.py)

**开发步骤**：
1. 实现初始化
2. 实现训练方法
3. 实现预测方法
4. 实现决策函数
5. 实现准确率计算

### 4.4 SVR 模块 (svr.py)

**开发步骤**：
1. 实现 SVR 的 SMO 算法
2. 实现 epsilon 不敏感损失
3. 实现训练和预测

### 4.5 多分类模块 (multiclass.py)

**开发步骤**：
1. 实现 One-vs-Rest 策略
2. 实现 One-vs-One 策略
3. 实现投票机制

### 4.6 评估指标模块 (metrics.py)

**开发步骤**：
1. 实现准确率
2. 实现精确率、召回率、F1
3. 实现混淆矩阵
4. 实现 MSE、R2、MAE

## 5. 测试开发

### 5.1 测试文件结构

```python
class TestLinearKernel:
    def test_basic_dot_product(self):
        kernel = linear_kernel()
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        assert kernel(x, y) == 32.0
```

### 5.2 测试编写规范

- 每个测试方法只测试一个功能
- 测试方法名应该描述测试内容
- 使用 assert 进行断言
- 使用 pytest.raises 测试异常

## 6. 运行示例

```bash
cd projects/svm

# 鸢尾花分类
python3 examples/iris_classification.py

# 手写数字识别
python3 examples/digit_recognition.py

# 文本分类
python3 examples/text_classification.py
```

## 7. 调试技巧

### 7.1 常见问题

**问题 1**：导入错误
```python
import sys
sys.path.insert(0, '/path/to/svm')
```

**问题 2**：数值不稳定
```python
if abs(alpha[j] - alpha_j_old) < 1e-5:
    continue
```

**问题 3**：收敛慢
```python
smo = SMO(C=1.0, tol=1e-3, max_passes=100)
```

### 7.2 性能分析

```python
import time

start = time.time()
svm.fit(X, y)
end = time.time()

print(f"Training time: {end - start:.2f}s")
```
