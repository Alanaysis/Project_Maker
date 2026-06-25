# 自适应控制器 - 开发指南

## 1. 开发环境搭建

### 1.1 系统要求

- Python 3.8+
- pip 或 conda 包管理器
- Git 版本控制

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install numpy scipy matplotlib pytest

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 1.3 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| numpy | >=1.20 | 数值计算 |
| scipy | >=1.7 | 科学计算 |
| matplotlib | >=3.4 | 数据可视化 |
| pytest | >=7.0 | 单元测试 |

## 2. 项目结构

```
adaptive-controller/
├── README.md                 # 项目说明
├── requirements.txt         # 依赖列表
├── setup.py                 # 安装配置
├── src/                     # 源代码
│   ├── __init__.py
│   ├── adaptive_controller.py
│   ├── reference_model.py
│   ├── parameter_estimator.py
│   ├── plant_model.py
│   ├── simulation.py
│   └── analyzer.py
├── tests/                   # 测试代码
│   ├── __init__.py
│   └── test_*.py
├── examples/                # 示例代码
│   ├── basic_mrac.py
│   └── advanced_mrac.py
├── docs/                    # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
└── LEARNING_NOTES.md        # 学习笔记
```

## 3. 编码规范

### 3.1 代码风格

遵循 PEP 8 规范：

```python
# 好的写法
def compute_control_signal(
    reference_input: float,
    plant_output: float,
    dt: float,
) -> float:
    """计算控制信号"""
    # 实现细节
    pass

# 不好的写法
def compute_control_signal(reference_input, plant_output, dt):
    # 实现细节
    pass
```

### 3.2 命名规范

```python
# 类名：大驼峰
class MRACController:
    pass

# 函数名：小写下划线
def compute_control():
    pass

# 变量名：小写下划线
tracking_error = 0.0

# 常量：大写下划线
MAX_ITERATIONS = 1000
```

### 3.3 类型注解

```python
from typing import Optional, Tuple, List, Dict
import numpy as np

def update(
    self,
    phi: np.ndarray,
    y: float,
    dt: float,
) -> Tuple[np.ndarray, float]:
    """更新参数估计"""
    pass
```

### 3.4 文档字符串

```python
def compute_control(
    self,
    reference_input: float,
    plant_output: float,
    dt: float,
) -> float:
    """
    计算控制信号

    参数：
        reference_input: 参考输入 r(t)
        plant_output: 被控对象输出 y(t)
        dt: 时间步长

    返回：
        控制信号 u(t)

    示例：
        >>> controller = MRACController()
        >>> u = controller.compute_control(1.0, 0.5, 0.01)
    """
    pass
```

## 4. 开发流程

### 4.1 功能开发

1. **创建分支**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **编写代码**
   - 实现功能
   - 添加测试
   - 更新文档

3. **运行测试**
   ```bash
   pytest tests/ -v
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **合并分支**
   ```bash
   git checkout master
   git merge feature/new-feature
   ```

### 4.2 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat(controller): add Lyapunov adaptation law

- Implement Lyapunov-based adaptive control
- Add parameter stability guarantees
- Update documentation

Closes #123
```

## 5. 测试驱动开发 (TDD)

### 5.1 TDD 流程

```
1. 编写失败的测试
2. 编写最少代码使测试通过
3. 重构代码
4. 重复
```

### 5.2 示例

```python
# 1. 编写测试
def test_controller_initialization():
    controller = MRACController()
    assert controller.params["theta_r"] == 0.0

# 2. 运行测试（失败）
# pytest tests/test_controller.py -v

# 3. 编写实现
class MRACController:
    def __init__(self):
        self.params = {"theta_r": 0.0}

# 4. 运行测试（通过）
# pytest tests/test_controller.py -v

# 5. 重构
```

## 6. 调试技巧

### 6.1 日志记录

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def compute_control(self, r, y, dt):
    logger.debug(f"Input: r={r}, y={y}, dt={dt}")
    u = self._compute_control_signal(r, y, 0)
    logger.debug(f"Output: u={u}")
    return u
```

### 6.2 断点调试

```python
import pdb

def compute_control(self, r, y, dt):
    pdb.set_trace()  # 设置断点
    # 代码执行到这里会暂停
    # 可以检查变量值、单步执行等
    pass
```

### 6.3 可视化调试

```python
import matplotlib.pyplot as plt

def debug_plot(times, values, title="Debug"):
    plt.figure()
    plt.plot(times, values)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title(title)
    plt.grid(True)
    plt.savefig(f'debug_{title}.png')
```

## 7. 性能优化

### 7.1 性能分析

```python
import cProfile

def run_simulation():
    # 仿真代码
    pass

# 分析性能
cProfile.run('run_simulation()', 'profile_output')
```

### 7.2 优化技巧

1. **向量化计算**
   ```python
   # 差的写法
   for i in range(n):
       result[i] = a[i] * b[i]

   # 好的写法
   result = a * b
   ```

2. **预分配数组**
   ```python
   # 差的写法
   result = []
   for i in range(n):
       result.append(compute(i))

   # 好的写法
   result = np.zeros(n)
   for i in range(n):
       result[i] = compute(i)
   ```

3. **使用 Numba 加速**
   ```python
   from numba import jit

   @jit(nopython=True)
   def fast_compute(x, y):
       return x * y
   ```

## 8. 版本管理

### 8.1 版本号规范

使用 Semantic Versioning：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 变更
MINOR: 向后兼容的功能性新增
PATCH: 向后兼容的问题修正
```

### 8.2 版本更新

```python
# src/__init__.py
__version__ = "1.0.0"
```

### 8.3 变更日志

```markdown
# Changelog

## [1.0.0] - 2024-01-01
### Added
- 基本 MRAC 控制器实现
- 参考模型支持
- 参数估计器
- 仿真引擎
- 性能分析器
```

## 9. 文档编写

### 9.1 README.md

包含：
- 项目简介
- 安装说明
- 使用示例
- API 文档链接
- 贡献指南

### 9.2 API 文档

使用 docstring 生成：

```bash
# 安装 Sphinx
pip install sphinx

# 生成文档
sphinx-quickstart docs
make html
```

### 9.3 示例代码

```python
# examples/basic_mrac.py
"""
基本 MRAC 示例

演示模型参考自适应控制器的基本使用方法。
"""

# 示例代码应可直接运行
```

## 10. 部署发布

### 10.1 打包

```bash
# 安装打包工具
pip install build twine

# 构建包
python -m build

# 检查包
twine check dist/*

# 上传到 PyPI
twine upload dist/*
```

### 10.2 Docker 部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "examples/basic_mrac.py"]
```

## 11. 实际应用示例

### 11.1 温度控制

温度控制系统特点：
- 一阶惯性环节 (热容量)
- 参数时变 (环境温度变化、材料老化)
- 存在扰动 (环境温度、负载变化)
- 传感器噪声

运行示例：
```bash
python examples/temperature_control.py
```

### 11.2 电机速度控制

电机控制系统特点：
- 二阶动态特性 (电气 + 机械)
- 非线性特性 (摩擦、饱和)
- 负载扰动
- 参数变化 (温度影响电阻)

运行示例：
```bash
python examples/motor_control.py
```

## 12. 贡献指南

### 11.1 Fork 项目

1. 在 GitHub 上 Fork 项目
2. 克隆到本地
3. 创建功能分支
4. 提交 Pull Request

### 11.2 代码审查

- 确保所有测试通过
- 代码符合规范
- 文档已更新
- 变更日志已更新

### 11.3 问题报告

使用 GitHub Issues 报告问题：
- 清晰描述问题
- 提供复现步骤
- 包含错误信息
- 提供环境信息

## 12. 学习资源

### 12.1 自适应控制

- Astrom, K.J. & Wittenmark, B. "Adaptive Control"
- Ioannou, P.A. & Sun, J. "Robust Adaptive Control"
- Slotine, J.J.E. & Li, W. "Applied Nonlinear Control"

### 12.2 Python 开发

- Python 官方文档
- Real Python 教程
- Fluent Python

### 12.3 控制系统

- Control Systems Library (Python)
- MATLAB Control System Toolbox
- ROS Control Framework
