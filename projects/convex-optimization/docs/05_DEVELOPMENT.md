# 凸优化开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- NumPy 1.20+
- pytest 6.0+

### 1.2 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov black flake8 mypy
```

### 1.3 代码风格

- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用 Flake8 检查代码风格
- 使用 MyPy 进行类型检查

```bash
# 格式化代码
black src/ tests/ examples/

# 检查代码风格
flake8 src/ tests/ examples/

# 类型检查
mypy src/
```

## 2. 项目结构

### 2.1 目录结构

```
convex-optimization/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── functions/                # 凸函数模块
│   │   ├── __init__.py
│   │   ├── convex_function.py
│   │   └── test_functions.py
│   ├── optimizers/              # 优化算法模块
│   │   ├── __init__.py
│   │   ├── base_optimizer.py
│   │   ├── gradient_descent.py
│   │   ├── newton_method.py
│   │   └── bfgs.py
│   ├── constrained/             # 约束优化模块
│   │   ├── __init__.py
│   │   ├── lagrangian.py
│   │   ├── kkt.py
│   │   └── interior_point.py
│   └── applications/            # 实际应用模块
│       ├── __init__.py
│       ├── least_squares.py
│       ├── svm.py
│       └── portfolio.py
├── tests/                       # 测试代码
├── examples/                    # 示例代码
├── docs/                        # 文档
├── README.md
└── requirements.txt
```

### 2.2 模块职责

- **functions**: 凸函数定义和凸性判断
- **optimizers**: 优化算法实现
- **constrained**: 约束优化方法
- **applications**: 实际应用案例

## 3. 开发流程

### 3.1 新增功能

1. **创建分支**: `git checkout -b feature/new-feature`
2. **编写代码**: 在相应模块中添加代码
3. **编写测试**: 在 tests/ 目录添加测试
4. **运行测试**: `pytest tests/`
5. **提交代码**: `git commit -m "feat: add new feature"`
6. **创建 PR**: 提交 Pull Request

### 3.2 修复 Bug

1. **创建分支**: `git checkout -b fix/bug-fix`
2. **编写测试**: 先编写复现 Bug 的测试
3. **修复代码**: 修改源代码
4. **运行测试**: 确保测试通过
5. **提交代码**: `git commit -m "fix: fix bug description"`

### 3.3 代码审查

- 确保代码符合 PEP 8 规范
- 确保测试覆盖率 > 80%
- 确保文档完整
- 确保类型注解正确

## 4. 测试指南

### 4.1 编写测试

```python
import pytest
import numpy as np

class TestMyFunction:
    def test_basic_case(self):
        """测试基本功能"""
        # Arrange
        input_data = np.array([1, 2, 3])
        expected = np.array([2, 4, 6])
        
        # Act
        result = my_function(input_data)
        
        # Assert
        np.testing.assert_allclose(result, expected)

    def test_edge_case(self):
        """测试边界情况"""
        # 测试空数组
        result = my_function(np.array([]))
        assert len(result) == 0

    def test_error_handling(self):
        """测试错误处理"""
        with pytest.raises(ValueError):
            my_function(None)
```

### 4.2 测试最佳实践

- 使用描述性的测试名称
- 遵循 AAA 模式（Arrange, Act, Assert）
- 测试边界条件和错误情况
- 使用 fixtures 管理测试数据
- 避免测试间的依赖

### 4.3 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_functions.py

# 运行带详细输出
pytest tests/ -v

# 运行并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 5. 文档指南

### 5.1 文档结构

- **README.md**: 项目概述和快速开始
- **01_RESEARCH.md**: 理论基础和研究背景
- **02_DESIGN.md**: 系统设计和架构
- **03_IMPLEMENTATION.md**: 实现细节和算法
- **04_TESTING.md**: 测试策略和用例
- **05_DEVELOPMENT.md**: 开发指南和流程

### 5.2 编写文档

- 使用 Markdown 格式
- 包含代码示例
- 保持文档与代码同步
- 使用清晰的标题和结构

### 5.3 API 文档

```python
def optimize(func, grad, x0, method='gradient_descent', **kwargs):
    """优化函数
    
    Args:
        func: 目标函数
        grad: 梯度函数
        x0: 初始点
        method: 优化方法
        **kwargs: 其他参数
    
    Returns:
        OptimizationResult: 优化结果
    
    Examples:
        >>> def f(x): return x[0]**2 + x[1]**2
        >>> def g(x): return 2*x
        >>> result = optimize(f, g, [1.0, 1.0])
    """
    pass
```

## 6. 性能优化

### 6.1 性能分析

```bash
# 使用 cProfile
python -m cProfile -s cumulative examples/basic_optimization.py

# 使用 line_profiler
pip install line_profiler
kernprof -l -v examples/basic_optimization.py

# 使用 memory_profiler
pip install memory_profiler
python -m memory_profiler examples/basic_optimization.py
```

### 6.2 优化技巧

1. **向量化计算**: 使用 NumPy 操作代替循环
2. **缓存计算**: 缓存重复计算的结果
3. **内存优化**: 使用 in-place 操作和视图
4. **并行计算**: 使用 multiprocessing 或 joblib

### 6.3 性能基准

```python
import time

def benchmark(func, *args, n_runs=100):
    """性能基准测试"""
    start = time.time()
    for _ in range(n_runs):
        func(*args)
    end = time.time()
    return (end - start) / n_runs
```

## 7. 部署指南

### 7.1 打包

```bash
# 创建 setup.py
# 打包
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

### 7.2 Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "examples/basic_optimization.py"]
```

### 7.3 CI/CD

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest tests/
```

## 8. 常见问题

### 8.1 安装问题

**问题**: NumPy 安装失败
**解决**: 使用 `pip install numpy --only-binary :all:`

**问题**: pytest 版本不兼容
**解决**: 使用 `pip install pytest==6.2.5`

### 8.2 运行问题

**问题**: 优化不收敛
**解决**: 调整学习率、增加迭代次数、检查梯度

**问题**: 数值溢出
**解决**: 添加正则化、使用数值稳定的实现

### 8.3 测试问题

**问题**: 测试失败
**解决**: 检查随机种子、确保测试数据正确

**问题**: 测试覆盖率低
**解决**: 添加边界条件测试、错误处理测试

## 9. 贡献指南

### 9.1 如何贡献

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### 9.2 代码规范

- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 添加单元测试

### 9.3 提交规范

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

## 10. 版本管理

### 10.1 版本号

- 主版本号：不兼容的 API 变更
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 10.2 更新日志

```markdown
# Changelog

## [1.0.0] - 2024-01-01
### Added
- 初始版本
- 凸函数模块
- 优化算法模块
- 约束优化模块
- 实际应用模块
```

## 11. 许可证

MIT License
