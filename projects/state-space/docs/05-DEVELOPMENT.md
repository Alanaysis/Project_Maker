# 状态空间模型 - 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip 或 conda
- Git

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 requirements.txt

```
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
pytest>=6.0.0
pytest-cov>=2.12.0
```

## 2. 项目结构

```
state-space/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记
├── requirements.txt          # 依赖列表
├── setup.py                  # 包安装配置
├── src/                      # 源代码
│   ├── __init__.py          # 包初始化
│   ├── state_space_model.py # 状态空间模型
│   ├── kalman_filter.py     # 卡尔曼滤波器
│   ├── analysis.py          # 系统分析
│   ├── controller.py        # 控制器
│   └── observer.py          # 观测器
├── tests/                    # 测试代码
│   ├── __init__.py
│   └── test_state_space.py
├── examples/                 # 示例代码
│   ├── basic_example.py
│   ├── kalman_example.py
│   └── control_example.py
└── docs/                     # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 3. 编码规范

### 3.1 Python风格

遵循PEP 8规范：
- 使用4空格缩进
- 行长度限制79字符
- 使用snake_case命名函数和变量
- 使用PascalCase命名类

### 3.2 类型注解

```python
from typing import Optional, Tuple, List, Union

def simulate(
    self,
    x0: np.ndarray,
    u: np.ndarray,
    n_steps: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """仿真系统响应"""
    # ...
```

### 3.3 文档字符串

```python
def predict(self, u: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    预测步骤

    Args:
        u: 输入向量 (m,)，默认为零

    Returns:
        x_hat_prior: 先验状态估计
        P_prior: 先验误差协方差

    Raises:
        ValueError: 如果参数无效
    """
    # ...
```

### 3.4 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 类名 | PascalCase | StateSpaceModel |
| 函数名 | snake_case | controllability_matrix |
| 变量名 | snake_case | state_estimate |
| 常量 | UPPER_CASE | MAX_ITERATIONS |
| 私有成员 | _前缀 | _validate_dimensions |

## 4. 开发流程

### 4.1 Git工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature

# 创建Pull Request
gh pr create --title "feat: 添加新功能" --body "描述..."
```

### 4.2 提交信息规范

使用Conventional Commits格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat(controller): 添加LQR控制器实现

- 实现Riccati方程求解
- 添加LQR增益计算
- 支持交叉权重项

Closes #123
```

### 4.3 版本管理

使用语义化版本号：`MAJOR.MINOR.PATCH`

- MAJOR: 不兼容的API更改
- MINOR: 向后兼容的功能添加
- PATCH: 向后兼容的bug修复

## 5. 测试流程

### 5.1 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_state_space.py::TestKalmanFilter

# 运行带覆盖率的测试
pytest --cov=src tests/

# 生成HTML覆盖率报告
pytest --cov=src --cov-report=html tests/
```

### 5.2 测试前检查

```bash
# 代码格式检查
black --check src/ tests/

# 代码风格检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 5.3 测试覆盖率目标

- 总体覆盖率: >80%
- 核心模块覆盖率: >90%

## 6. 构建和发布

### 6.1 打包

```bash
# 安装setuptools和wheel
pip install setuptools wheel

# 创建分发包
python setup.py sdist bdist_wheel
```

### 6.2 setup.py

```python
from setuptools import setup, find_packages

setup(
    name="state-space",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="状态空间模型和状态估计库",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/state-space",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
    ],
)
```

### 6.3 发布到PyPI

```bash
# 安装twine
pip install twine

# 上传到TestPyPI
twine upload --repository testpypi dist/*

# 上传到PyPI
twine upload dist/*
```

## 7. 文档维护

### 7.1 文档结构

- `README.md`: 项目概述和快速开始
- `LEARNING_NOTES.md`: 学习笔记和核心概念
- `docs/01-RESEARCH.md`: 市场调研
- `docs/02-DESIGN.md`: 项目设计
- `docs/03-IMPLEMENTATION.md`: 实现细节
- `docs/04-TESTING.md`: 测试文档
- `docs/05-DEVELOPMENT.md`: 开发文档

### 7.2 文档更新流程

1. 修改代码时同步更新文档
2. 添加新功能时更新README和API文档
3. 定期审查和更新学习笔记

### 7.3 API文档生成

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

## 8. 持续集成

### 8.1 GitHub Actions配置

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

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
        pip install -r requirements.txt

    - name: Lint with flake8
      run: |
        flake8 src/ tests/

    - name: Test with pytest
      run: |
        pytest --cov=src tests/

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### 8.2 本地CI检查

```bash
# 运行所有检查
make check

# 或手动运行
flake8 src/ tests/
pytest --cov=src tests/
```

## 9. 调试指南

### 9.1 常见问题

#### 问题1: 数值不稳定

**症状:** 协方差矩阵失去正定性

**解决方案:**
```python
# 使用Joseph形式更新协方差
IKC = np.eye(n) - K @ C
P = IKC @ P_prior @ IKC.T + K @ R @ K.T
```

#### 问题2: 收敛慢

**症状:** 观测器或控制器收敛慢

**解决方案:**
```python
# 调整极点位置
desired_poles = np.array([0.2, 0.1])  # 更快的极点
```

### 9.2 调试技巧

#### 打印中间结果

```python
def predict(self, u=None):
    x_hat_prior = self.A @ self.x_hat + self.B @ u
    P_prior = self.A @ self.P @ self.A.T + self.Q

    print(f"x_hat_prior: {x_hat_prior}")
    print(f"P_prior:\n{P_prior}")

    return x_hat_prior, P_prior
```

#### 可视化调试

```python
import matplotlib.pyplot as plt

def plot_state_trajectory(states):
    plt.plot(states[:, 0], states[:, 1])
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.title('State Trajectory')
    plt.grid(True)
    plt.show()
```

#### 使用断言

```python
# 检查协方差矩阵正定性
assert np.all(np.linalg.eigvals(P) > 0), "协方差矩阵非正定"

# 检查稳定性
assert model.is_stable(), "系统不稳定"
```

### 9.3 性能分析

```bash
# 使用cProfile
python -m cProfile -o profile.stats examples/basic_example.py

# 分析结果
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

## 10. 贡献指南

### 10.1 如何贡献

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

### 10.2 代码审查清单

- [ ] 代码符合PEP 8规范
- [ ] 添加了类型注解
- [ ] 编写了文档字符串
- [ ] 添加了单元测试
- [ ] 测试通过
- [ ] 覆盖率达标

### 10.3 Pull Request模板

```markdown
## 描述

简要描述更改内容

## 更改类型

- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 重构

## 测试

- [ ] 添加了新测试
- [ ] 所有测试通过

## 检查清单

- [ ] 代码符合规范
- [ ] 文档已更新
- [ ] 测试覆盖率达标
```

## 11. 发布流程

### 11.1 版本发布

```bash
# 更新版本号
bump2version minor  # 或 major, patch

# 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# 创建GitHub Release
gh release create v1.1.0 --title "Release v1.1.0" --notes "..."
```

### 11.2 变更日志

维护`CHANGELOG.md`文件：

```markdown
# Changelog

## [1.1.0] - 2024-01-15

### Added
- 添加LQR控制器
- 添加RTS平滑器

### Changed
- 优化卡尔曼滤波性能

### Fixed
- 修复维度验证错误

## [1.0.0] - 2024-01-01

### Added
- 初始版本
- 状态空间模型
- 卡尔曼滤波器
- 可控性/可观性分析
```

## 12. 项目维护

### 12.1 依赖更新

```bash
# 检查过时依赖
pip list --outdated

# 更新依赖
pip install --upgrade numpy scipy matplotlib
```

### 12.2 安全审计

```bash
# 安装安全检查工具
pip install safety

# 检查安全漏洞
safety check
```

### 12.3 性能监控

定期运行性能测试，确保没有性能退化：

```bash
pytest tests/test_performance.py -v
```

## 13. 扩展开发

### 13.1 添加新功能

1. 在`src/`目录创建新模块
2. 在`__init__.py`中导出
3. 编写单元测试
4. 更新文档

### 13.2 插件机制

```python
# 基类
class FilterBase:
    def predict(self): ...
    def update(self, y): ...

# 注册机制
FILTER_REGISTRY = {}

def register_filter(name):
    def decorator(cls):
        FILTER_REGISTRY[name] = cls
        return cls
    return decorator

@register_filter("kalman")
class KalmanFilter(FilterBase): ...

@register_filter("extended_kalman")
class ExtendedKalmanFilter(FilterBase): ...
```

### 13.3 配置系统

```python
# config.yaml
system:
  dt: 0.01
  noise:
    process: 0.01
    measurement: 0.1

controller:
  type: lqr
  Q: [[100, 0], [0, 1]]
  R: [[0.01]]
```

```python
import yaml

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)
```

## 14. 故障排除

### 14.1 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| LinAlgError: Singular matrix | 矩阵奇异 | 检查矩阵是否可逆 |
| ValueError: Dimension mismatch | 维度不匹配 | 检查矩阵维度 |
| AssertionError: Not stable | 系统不稳定 | 调整系统参数 |

### 14.2 获取帮助

- 查看文档: `docs/`目录
- 搜索Issues: GitHub Issues
- 提交问题: 创建新Issue

## 15. 未来规划

### 15.1 短期目标

- [ ] 添加EKF实现
- [ ] 支持连续时间系统
- [ ] 优化性能

### 15.2 中期目标

- [ ] 添加UKF实现
- [ ] 支持MIMO极点配置
- [ ] 创建GUI界面

### 15.3 长期目标

- [ ] 支持分布式系统
- [ ] 实现自适应算法
- [ ] 集成机器学习
