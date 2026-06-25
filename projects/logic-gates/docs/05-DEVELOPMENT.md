# 逻辑门模拟器 - 开发文档

## 1. 开发环境搭建

### 1.1 系统要求

- **操作系统**：Linux、macOS、Windows
- **Python版本**：3.8 或更高
- **依赖管理**：pip、virtualenv（可选）

### 1.2 环境配置

#### 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# 升级pip
pip install --upgrade pip
```

#### 安装依赖

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 或者手动安装
pip install pytest pytest-cov black flake8 mypy
```

### 1.3 IDE配置

#### VS Code

创建 `.vscode/settings.json`：

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests",
        "-v",
        "--cov=src",
        "--cov-report=html"
    ]
}
```

#### PyCharm

1. 打开项目设置
2. 配置Python解释器（选择虚拟环境）
3. 配置测试运行器为pytest
4. 启用代码检查和格式化

## 2. 代码规范

### 2.1 代码风格

遵循 PEP 8 规范：

```python
# 好的示例
class AndGate(Gate):
    """与门实现"""
    
    @property
    def name(self):
        return "AND"
    
    def evaluate(self, *inputs):
        """计算输出"""
        return int(all(inputs))

# 不好的示例
class and_gate(Gate):
    def evaluate(self,*inputs):
        return int(all(inputs))
```

### 2.2 命名约定

- **类名**：大驼峰（`AndGate`、`Circuit`）
- **函数名**：小写字母+下划线（`evaluate`、`truth_table`）
- **变量名**：小写字母+下划线（`input_signal`、`output_value`）
- **常量名**：大写字母+下划线（`MAX_INPUTS`、`DEFAULT_VALUE`）

### 2.3 文档字符串

使用Google风格的文档字符串：

```python
def evaluate(self, *inputs):
    """计算逻辑门的输出
    
    Args:
        *inputs: 输入信号，每个为0或1
        
    Returns:
        int: 输出信号，0或1
        
    Raises:
        InvalidInputError: 输入信号无效
        
    Examples:
        >>> gate = AndGate()
        >>> gate.evaluate(1, 1)
        1
    """
    pass
```

### 2.4 类型注解

使用类型注解提高代码可读性：

```python
from typing import List, Tuple, Dict

def truth_table(self) -> List[Tuple[List[int], int]]:
    """生成真值表"""
    pass

def evaluate(self, *inputs: int) -> int:
    """计算输出"""
    pass
```

## 3. 测试策略

### 3.1 测试结构

```
tests/
├── __init__.py
├── test_signal.py      # 信号测试
├── test_gates.py       # 逻辑门测试
├── test_circuit.py     # 电路测试
├── test_truth_table.py # 真值表测试
├── test_registry.py    # 注册表测试
├── conftest.py         # 测试配置
└── fixtures/           # 测试数据
```

### 3.2 单元测试

```python
import pytest
from src.gates import AndGate, OrGate, NotGate
from src.exceptions import InvalidInputError

class TestAndGate:
    """AND门测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.gate = AndGate()
    
    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "AND"
    
    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2
    
    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0
    
    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 0
    
    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 0
    
    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 1
    
    def test_invalid_input_count(self):
        """测试无效输入数量"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0)
    
    def test_invalid_input_value(self):
        """测试无效输入值"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0, 2)
    
    def test_callable(self):
        """测试可调用接口"""
        assert self.gate(1, 1) == 1
    
    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 0) in table
        assert ([1, 1], 1) in table
```

### 3.3 集成测试

```python
class TestHalfAdder:
    """半加器集成测试"""
    
    def setup_method(self):
        """创建半加器电路"""
        from src.circuit import Circuit
        from src.gates import XorGate, AndGate
        
        self.circuit = Circuit("Half Adder")
        self.xor = self.circuit.add_gate(XorGate(), "XOR")
        self.and_ = self.circuit.add_gate(AndGate(), "AND")
        
        # 标记输入输出
        self.circuit.mark_as_input("A")
        self.circuit.mark_as_input("B")
        self.circuit.mark_as_output("XOR")
        self.circuit.mark_as_output("AND")
    
    def test_00(self):
        """测试输入A=0, B=0"""
        self.circuit.set_inputs({"A": 0, "B": 0})
        results = self.circuit.evaluate()
        assert results["XOR"] == 0  # Sum
        assert results["AND"] == 0  # Carry
    
    def test_01(self):
        """测试输入A=0, B=1"""
        self.circuit.set_inputs({"A": 0, "B": 1})
        results = self.circuit.evaluate()
        assert results["XOR"] == 1
        assert results["AND"] == 0
    
    def test_10(self):
        """测试输入A=1, B=0"""
        self.circuit.set_inputs({"A": 1, "B": 0})
        results = self.circuit.evaluate()
        assert results["XOR"] == 1
        assert results["AND"] == 0
    
    def test_11(self):
        """测试输入A=1, B=1"""
        self.circuit.set_inputs({"A": 1, "B": 1})
        results = self.circuit.evaluate()
        assert results["XOR"] == 0
        assert results["AND"] == 1
```

### 3.4 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

目标覆盖率：90%以上

### 3.5 性能测试

```python
import time

class TestPerformance:
    """性能测试"""
    
    def test_large_circuit_performance(self):
        """测试大规模电路性能"""
        from src.circuit import Circuit
        from src.gates import AndGate
        
        # 创建大规模电路
        circuit = Circuit("Large Circuit")
        prev_gate = None
        
        for i in range(1000):
            gate = circuit.add_gate(AndGate(), f"AND_{i}")
            if prev_gate:
                circuit.connect(prev_gate, gate, 0)
            prev_gate = gate
        
        # 测量执行时间
        start = time.time()
        for _ in range(100):
            circuit.set_input("AND_0", 1)
            circuit.evaluate()
        end = time.time()
        
        # 验证性能
        avg_time = (end - start) / 100
        assert avg_time < 0.1  # 平均执行时间应小于100ms
```

## 4. 构建和发布

### 4.1 项目结构

```
logic-gates/
├── src/
│   └── logic_gates/
│       ├── __init__.py
│       ├── signal.py
│       ├── gates.py
│       ├── circuit.py
│       ├── truth_table.py
│       ├── registry.py
│       ├── exceptions.py
│       └── utils.py
├── tests/
├── docs/
├── examples/
├── setup.py
├── setup.cfg
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── LICENSE
```

### 4.2 打包配置

#### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="logic-gates",
    version="1.0.0",
    author="Logic Gates Simulator",
    author_email="author@example.com",
    description="A logic gate simulator for learning digital circuits",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/logic-gates",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Education",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
)
```

#### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py38']

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 4.3 构建流程

```bash
# 清理旧构建
rm -rf build/ dist/ *.egg-info

# 运行测试
python -m pytest tests/ -v

# 代码检查
flake8 src/ tests/
mypy src/
black --check src/ tests/

# 构建包
python setup.py sdist bdist_wheel

# 验证包
twine check dist/*

# 上传到PyPI（测试）
twine upload --repository testpypi dist/*

# 上传到PyPI（正式）
twine upload dist/*
```

## 5. 持续集成

### 5.1 GitHub Actions

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src/ tests/
    
    - name: Type check with mypy
      run: |
        mypy src/
    
    - name: Test with pytest
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### 5.2 发布流程

创建 `.github/workflows/release.yml`：

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install setuptools wheel twine
    
    - name: Build and publish
      env:
        TWINE_USERNAME: ${{ secrets.PYPI_USERNAME }}
        TWINE_PASSWORD: ${{ secrets.PYPI_PASSWORD }}
      run: |
        python setup.py sdist bdist_wheel
        twine upload dist/*
```

## 6. 版本管理

### 6.1 版本号规范

采用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的API更改
- **MINOR**：向后兼容的功能添加
- **PATCH**：向后兼容的错误修复

### 6.2 变更日志

创建 `CHANGELOG.md`：

```markdown
# Changelog

## [1.0.0] - 2026-06-22

### Added
- 实现基本逻辑门（AND、OR、NOT、XOR、NAND、NOR）
- 电路组合功能
- 真值表生成
- 命令行接口
- 示例程序

### Changed
- 无

### Deprecated
- 无

### Removed
- 无

### Fixed
- 无

### Security
- 无
```

## 7. 文档维护

### 7.1 文档结构

```
docs/
├── 01-RESEARCH.md      # 市场调研
├── 02-ARCHITECTURE.md  # 架构设计
├── 03-API.md           # API设计
├── 04-IMPLEMENTATION.md # 实现细节
├── 05-DEVELOPMENT.md   # 开发文档
├── tutorials/          # 教程
├── examples/           # 示例
└── api/                # API参考
```

### 7.2 文档生成

使用Sphinx生成API文档：

```bash
# 安装Sphinx
pip install sphinx sphinx-rtd-theme

# 初始化文档
sphinx-quickstart docs/

# 生成文档
cd docs/
make html
```

### 7.3 文档更新流程

1. 代码变更时同步更新文档
2. 定期审查文档准确性
3. 收集用户反馈并改进
4. 版本发布时更新文档

## 8. 贡献指南

### 8.1 开发流程

1. Fork项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

### 8.2 代码审查

- 所有PR需要至少一个审查者
- 确保测试通过
- 确保代码符合规范
- 确保文档更新

### 8.3 问题报告

使用GitHub Issues报告问题：

1. 描述问题现象
2. 提供复现步骤
3. 提供环境信息
4. 提供错误日志

## 9. 调试技巧

### 9.1 日志配置

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### 9.2 调试工具

```python
# 使用pdb调试
import pdb; pdb.set_trace()

# 使用ipdb（更友好）
import ipdb; ipdb.set_trace()

# 使用断点（Python 3.7+）
breakpoint()
```

### 9.3 常见问题

**问题1：导入错误**
```bash
# 解决方案：确保src目录在Python路径中
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**问题2：测试失败**
```bash
# 解决方案：检查测试环境
python -m pytest tests/ -v --tb=long
```

## 10. 性能调优

### 10.1 性能分析

```python
import cProfile

def profile_function(func):
    """性能分析装饰器"""
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        profiler.print_stats()
        return result
    return wrapper
```

### 10.2 优化建议

1. **使用缓存**：避免重复计算
2. **减少对象创建**：重用对象
3. **使用内置函数**：`all()`、`any()`比循环快
4. **避免深层递归**：使用迭代替代

## 11. 总结

本文档提供了逻辑门模拟器的完整开发指南，包括：
- 开发环境搭建
- 代码规范
- 测试策略
- 构建和发布流程
- 持续集成配置
- 版本管理
- 文档维护
- 贡献指南
- 调试技巧
- 性能调优

遵循这些指南可以确保项目的高质量和可维护性。
