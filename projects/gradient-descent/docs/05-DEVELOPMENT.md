# 梯度下降家族 - 开发指南

## 1. 开发环境设置

### 1.1 系统要求

- Python 3.8+
- pip 或 conda
- Git

### 1.2 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd gradient-descent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 1.3 依赖说明

**requirements.txt**:
```
numpy>=1.20.0
matplotlib>=3.3.0
```

**requirements-dev.txt**:
```
pytest>=6.0.0
pytest-cov>=2.12.0
flake8>=3.9.0
black>=21.0.0
isort>=5.9.0
mypy>=0.900
```

## 2. 项目结构

```
gradient-descent/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── optimizer.py       # 优化工具函数
│   ├── optimizers/        # 优化器实现
│   ├── schedulers/        # 学习率调度器
│   ├── functions/         # 测试函数
│   └── visualizer/        # 可视化模块
├── tests/                 # 测试代码
├── examples/              # 示例代码
├── docs/                  # 文档
├── requirements.txt       # 依赖说明
├── setup.py              # 安装脚本
├── README.md             # 项目说明
└── .gitignore            # Git 忽略文件
```

## 3. 编码规范

### 3.1 代码风格

- 遵循 PEP 8
- 使用 4 空格缩进
- 行长度限制: 88 字符 (Black 默认)
- 使用类型注解

### 3.2 命名规范

- **类名**: PascalCase (如 `AdamOptimizer`)
- **函数名**: snake_case (如 `compute_gradient`)
- **变量名**: snake_case (如 `learning_rate`)
- **常量名**: UPPER_SNAKE_CASE (如 `DEFAULT_LR`)

### 3.3 文档字符串

```python
def optimize(func, optimizer, x_init, max_iter=1000, tol=1e-6):
    """统一优化接口

    Args:
        func: 测试函数
        optimizer: 优化器实例
        x_init: 初始点
        max_iter: 最大迭代次数
        tol: 收敛容差

    Returns:
        优化结果字典

    Raises:
        ValueError: 当输入参数无效时
    """
    pass
```

## 4. 开发工作流

### 4.1 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/new-optimizer

# 开发功能
# ...

# 提交更改
git add .
git commit -m "feat: 添加新优化器"

# 推送到远程
git push origin feature/new-optimizer

# 创建 Pull Request
```

### 4.2 提交规范

使用 Conventional Commits:

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例:
```
feat: 添加 AdamW 优化器
fix: 修复 AdaGrad 学习率计算错误
docs: 更新 README 文档
test: 添加集成测试
```

## 5. 添加新优化器

### 5.1 创建优化器文件

```python
# src/optimizers/new_optimizer.py

import numpy as np
from .base import BaseOptimizer


class NewOptimizer(BaseOptimizer):
    """新优化器描述

    数学公式:
        θ_{t+1} = θ_t - η * ∇J(θ_t)

    Attributes:
        learning_rate: 学习率
        param1: 参数1
    """

    def __init__(self, learning_rate=0.01, param1=0.9):
        """初始化优化器

        Args:
            learning_rate: 学习率
            param1: 参数1
        """
        super().__init__(learning_rate)
        self.param1 = param1

    def step(self, params, grads):
        """执行一步优化

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        # 检查数值稳定性
        params, grads = self._check_numerical_stability(params, grads)

        # 实现优化逻辑
        # ...

        # 更新迭代次数
        self._update_step_count()

        return params

    def __repr__(self):
        """返回优化器的字符串表示"""
        return f"NewOptimizer(learning_rate={self.learning_rate}, param1={self.param1})"
```

### 5.2 注册优化器

```python
# src/optimizers/__init__.py

from .new_optimizer import NewOptimizer

__all__ = [
    # ... 其他优化器
    'NewOptimizer'
]
```

### 5.3 编写测试

```python
# tests/test_optimizers.py

class TestNewOptimizer:
    """新优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = NewOptimizer(learning_rate=0.01, param1=0.9)
        assert optimizer.learning_rate == 0.01
        assert optimizer.param1 == 0.9

    def test_basic_step(self):
        """测试基本更新步骤"""
        optimizer = NewOptimizer(learning_rate=0.1)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        assert new_params.shape == params.shape
        # 添加更多断言...

    def test_invalid_parameters(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            NewOptimizer(learning_rate=-0.01)
```

## 6. 添加新测试函数

### 6.1 创建测试函数文件

```python
# src/functions/new_function.py

import numpy as np
from typing import Tuple, List
from .base import TestFunction


class NewFunction(TestFunction):
    """新测试函数描述

    数学表达:
        f(x, y) = x^2 + y^2

    特点:
        - 凸函数
        - 有唯一最小值
    """

    def __init__(self):
        """初始化测试函数"""
        super().__init__('new_function', ndim=2)

    def __call__(self, x):
        """计算函数值"""
        x = np.asarray(x)
        return x[0]**2 + x[1]**2

    def gradient(self, x):
        """计算梯度"""
        x = np.asarray(x)
        return np.array([2*x[0], 2*x[1]])

    def minimum(self):
        """返回理论最小值"""
        return np.array([0.0, 0.0]), 0.0

    def initial_point(self):
        """返回初始点"""
        return np.array([3.0, 3.0])

    def search_range(self):
        """返回搜索范围"""
        return [(-5, 5), (-5, 5)]
```

### 6.2 注册测试函数

```python
# src/functions/__init__.py

from .new_function import NewFunction

__all__ = [
    # ... 其他函数
    'NewFunction'
]
```

## 7. 添加新调度器

### 7.1 创建调度器文件

```python
# src/schedulers/new_scheduler.py

from .base import BaseScheduler


class NewScheduler(BaseScheduler):
    """新调度器描述

    数学公式:
        lr = base_lr * decay(epoch)
    """

    def __init__(self, optimizer, param1=0.9, last_epoch=-1):
        """初始化调度器"""
        self.param1 = param1
        super().__init__(optimizer, last_epoch)

    def get_lr(self):
        """计算当前学习率"""
        # 实现调度逻辑
        return self.base_lr * self.param1 ** self.last_epoch
```

### 7.2 注册调度器

```python
# src/schedulers/__init__.py

from .new_scheduler import NewScheduler

__all__ = [
    # ... 其他调度器
    'NewScheduler'
]
```

## 8. 代码质量工具

### 8.1 代码格式化

```bash
# 使用 Black 格式化代码
black src/ tests/ examples/

# 使用 isort 排序导入
isort src/ tests/ examples/
```

### 8.2 代码检查

```bash
# 使用 flake8 检查代码风格
flake8 src/ tests/ examples/

# 使用 mypy 检查类型
mypy src/
```

### 8.3 自动化检查

创建 `Makefile`:
```makefile
.PHONY: format lint test

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

lint:
	flake8 src/ tests/ examples/
	mypy src/

test:
	pytest --cov=src --cov-report=term-missing

all: format lint test
```

## 9. 文档编写

### 9.1 代码文档

- 每个模块有模块级文档字符串
- 每个类有类级文档字符串
- 每个公共方法有方法级文档字符串
- 使用类型注解

### 9.2 用户文档

- README.md: 项目概述和快速开始
- docs/: 详细文档
- examples/: 示例代码

### 9.3 API 文档

使用 Sphinx 生成 API 文档:

```bash
# 安装 Sphinx
pip install sphinx sphinx-rtd-theme

# 初始化文档
sphinx-quickstart docs

# 生成文档
cd docs
make html
```

## 10. 测试策略

### 10.1 测试金字塔

```
        /\
       /  \  E2E 测试
      /    \
     /------\  集成测试
    /        \
   /----------\  单元测试
```

### 10.2 测试命名

```python
# 好的命名
def test_adam_optimizer_converges_on_quadratic_function():
    pass

# 不好的命名
def test_adam():
    pass
```

### 10.3 测试数据

使用 fixtures 管理测试数据:

```python
@pytest.fixture
def quadratic_function():
    """创建二次函数"""
    return QuadraticFunction(a=1.0, b=1.0)

@pytest.fixture
def adam_optimizer():
    """创建 Adam 优化器"""
    return Adam(learning_rate=0.01)
```

## 11. 性能优化

### 11.1 NumPy 优化

```python
# 不好: 使用循环
for i in range(len(params)):
    params[i] -= lr * grads[i]

# 好: 使用向量化
params -= lr * grads
```

### 11.2 内存优化

```python
# 不好: 创建新数组
new_params = params - lr * grads

# 好: 原地操作
params -= lr * grads
```

### 11.3 缓存优化

```python
# 缓存中间计算结果
if 'exp_avg' not in self.state:
    self.state['exp_avg'] = np.zeros_like(params)
```

## 12. 发布流程

### 12.1 版本管理

使用语义化版本:

- **主版本号**: 不兼容的 API 更改
- **次版本号**: 向后兼容的功能添加
- **修订号**: 向后兼容的 bug 修复

### 12.2 发布步骤

```bash
# 更新版本号
# setup.py, src/__init__.py

# 更新 CHANGELOG.md

# 提交更改
git add .
git commit -m "chore: bump version to 1.0.0"

# 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签
git push origin v1.0.0

# 构建发布包
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

## 13. 调试技巧

### 13.1 使用调试器

```python
import pdb; pdb.set_trace()  # 设置断点
```

### 13.2 日志记录

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
```

### 13.3 性能分析

```python
import cProfile

def profile_function():
    cProfile.run('optimize(func, optimizer, x0)')
```

## 14. 常见问题

### 14.1 导入错误

```bash
# 确保在项目根目录
cd gradient-descent

# 确保安装了项目
pip install -e .
```

### 14.2 测试失败

```bash
# 运行单个测试
pytest tests/test_optimizers.py::TestSGD::test_basic_step -v

# 显示详细输出
pytest -v --tb=long
```

### 14.3 性能问题

```bash
# 分析性能
python -m cProfile -o profile.stats examples/basic_optimization.py

# 查看统计
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(10)"
```

## 15. 最佳实践总结

### 15.1 代码质量

- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串
- 保持函数简洁

### 15.2 测试覆盖

- 核心功能 100% 覆盖
- 测试边界情况
- 使用参数化测试

### 15.3 文档完整性

- 详细的 README
- 完整的 API 文档
- 丰富的示例代码

### 15.4 版本控制

- 使用语义化版本
- 编写清晰的提交信息
- 维护 CHANGELOG

## 16. 资源链接

- [NumPy 文档](https://numpy.org/doc/)
- [Matplotlib 文档](https://matplotlib.org/stable/contents.html)
- [pytest 文档](https://docs.pytest.org/)
- [Black 文档](https://black.readthedocs.io/)
- [PEP 8](https://pep8.org/)
- [语义化版本](https://semver.org/)
