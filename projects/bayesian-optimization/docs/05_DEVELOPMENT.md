# 贝叶斯优化 - 开发文档

## 1. 开发环境设置

### 1.1 系统要求

- Python 3.8+
- pip 或 conda
- Git

### 1.2 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd bayesian-optimization

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 安装项目（开发模式）
pip install -e .
```

### 1.3 依赖管理

#### 核心依赖 (`requirements.txt`)

```
numpy>=1.20
scipy>=1.7
matplotlib>=3.4
scikit-learn>=0.24
```

#### 开发依赖 (`requirements-dev.txt`)

```
pytest>=6.0
pytest-cov>=2.0
flake8>=3.9
black>=21.0
mypy>=0.900
sphinx>=4.0
```

## 2. 代码规范

### 2.1 代码风格

使用 Black 格式化代码：

```bash
# 格式化代码
black src/ tests/ examples/

# 检查格式
black --check src/ tests/ examples/
```

### 2.2 代码检查

使用 flake8 检查代码：

```bash
# 检查代码风格
flake8 src/ tests/ examples/

# 配置文件 .flake8
[flake8]
max-line-length = 88
extend-ignore = E203
exclude = .git,__pycache__,build,dist
```

### 2.3 类型检查

使用 mypy 进行类型检查：

```bash
# 类型检查
mypy src/

# 配置文件 mypy.ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### 2.4 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写 + 下划线 | `gaussian_process.py` |
| 类 | 驼峰命名 | `GaussianProcess` |
| 函数 | 小写 + 下划线 | `predict_mean()` |
| 常量 | 大写 + 下划线 | `DEFAULT_KERNEL` |
| 私有 | 前缀下划线 | `_internal_method()` |

## 3. 项目结构

### 3.1 目录结构

```
bayesian-optimization/
├── src/                          # 源代码
│   ├── __init__.py              # 包初始化
│   ├── kernels.py               # 核函数
│   ├── gaussian_process.py      # 高斯过程
│   ├── acquisition.py           # 采集函数
│   └── optimizer.py             # 优化器
├── tests/                        # 测试文件
│   ├── __init__.py
│   ├── test_gaussian_process.py
│   ├── test_acquisition.py
│   └── test_optimizer.py
├── examples/                     # 示例代码
│   ├── branin_function.py
│   └── hyperparameter_tuning.py
├── docs/                         # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_TESTING.md
│   └── 05_DEVELOPMENT.md
├── setup.py                      # 安装脚本
├── requirements.txt              # 依赖
├── requirements-dev.txt          # 开发依赖
├── pytest.ini                    # pytest 配置
├── .flake8                       # flake8 配置
├── mypy.ini                      # mypy 配置
└── README.md                     # 项目说明
```

### 3.2 模块职责

| 模块 | 职责 |
|------|------|
| `kernels.py` | 核函数实现和组合 |
| `gaussian_process.py` | 高斯过程回归 |
| `acquisition.py` | 采集函数实现 |
| `optimizer.py` | 贝叶斯优化循环 |

## 4. 开发流程

### 4.1 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发代码
# ...

# 提交代码
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/new-feature

# 创建 Pull Request
# ...

# 合并后删除分支
git checkout master
git pull
git branch -d feature/new-feature
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
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat(acquisition): add Thompson sampling

- Implement Thompson sampling acquisition function
- Add unit tests
- Update documentation

Closes #123
```

### 4.3 版本管理

使用 Semantic Versioning：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 变更
MINOR: 向后兼容的功能添加
PATCH: 向后兼容的 bug 修复
```

## 5. 测试开发

### 5.1 编写测试

```python
import pytest
import numpy as np
from src.gaussian_process import GaussianProcess

class TestGaussianProcess:
    """高斯过程测试类"""

    def setup_method(self):
        """测试前准备"""
        np.random.seed(42)
        self.X_train = np.random.randn(20, 2)
        self.y_train = np.random.randn(20)

    def test_fit(self):
        """测试拟合"""
        gp = GaussianProcess()
        gp.fit(self.X_train, self.y_train)

        assert gp.X_train is not None
        assert gp.y_train is not None
        assert gp.alpha is not None

    def test_predict_shape(self):
        """测试预测形状"""
        gp = GaussianProcess()
        gp.fit(self.X_train, self.y_train)

        X_test = np.random.randn(10, 2)
        y_mean, y_std = gp.predict(X_test, return_std=True)

        assert y_mean.shape == (10,)
        assert y_std.shape == (10,)
```

### 5.2 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_gaussian_process.py::TestGaussianProcess::test_fit

# 显示详细输出
pytest -v tests/

# 显示覆盖率
pytest --cov=src tests/

# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html tests/
```

### 5.3 测试最佳实践

1. **独立性**: 每个测试用例独立运行
2. **可重复性**: 使用固定随机种子
3. **快速性**: 单元测试 < 1 秒
4. **全面性**: 覆盖正常和异常情况

## 6. 文档开发

### 6.1 代码文档

使用 Google 风格的 docstring：

```python
def predict(self, X, return_std=False):
    """
    预测均值和方差

    参数：
        X: 测试输入，形状 (n_test, n_features)
        return_std: 是否返回标准差

    返回：
        y_mean: 预测均值
        y_std: 预测标准差（如果 return_std=True）

    示例：
        >>> gp = GaussianProcess()
        >>> gp.fit(X_train, y_train)
        >>> y_mean, y_std = gp.predict(X_test, return_std=True)
    """
    pass
```

### 6.2 API 文档

使用 Sphinx 生成 API 文档：

```bash
# 安装 Sphinx
pip install sphinx

# 初始化文档
cd docs
sphinx-quickstart

# 生成文档
make html

# 查看文档
open _build/html/index.html
```

### 6.3 示例文档

每个示例应包含：

1. 问题描述
2. 代码实现
3. 运行结果
4. 解释说明

## 7. 性能优化

### 7.1 性能分析

```python
import cProfile

def profile_optimization():
    """性能分析"""
    def objective(x):
        return -np.sum(x**2)

    optimizer = BayesianOptimizer(
        objective_function=objective,
        bounds=[(-5, 5)] * 5,
        n_initial=10,
        random_state=42
    )

    cProfile.run('optimizer.optimize(n_iterations=20, verbose=False)')
```

### 7.2 优化技巧

1. **缓存计算结果**
   - 缓存 Cholesky 因子
   - 缓存 alpha 向量

2. **使用高效算法**
   - Cholesky 分解代替矩阵求逆
   - 使用 BLAS/LAPACK

3. **避免不必要的计算**
   - 使用视图代替复制
   - 避免重复计算

4. **并行化**
   - 多起点并行优化
   - 批量预测

## 8. 调试技巧

### 8.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 核矩阵非正定 | 数值问题 | 添加正则化项 |
| 预测方差为负 | 数值问题 | 裁剪到 0 |
| Cholesky 分解失败 | 矩阵病态 | 添加对角项 |
| 优化不收敛 | 采集函数问题 | 调整参数 |

### 8.2 调试工具

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 添加调试信息
logger = logging.getLogger(__name__)
logger.debug("核矩阵形状: %s", K.shape)
logger.debug("条件数: %f", np.linalg.cond(K))
```

### 8.3 可视化调试

```python
import matplotlib.pyplot as plt

def visualize_gp(gp, X_train, y_train, X_test):
    """可视化高斯过程"""
    y_mean, y_std = gp.predict(X_test, return_std=True)

    plt.figure(figsize=(10, 6))
    plt.plot(X_test, y_mean, 'b-', label='预测均值')
    plt.fill_between(X_test.ravel(),
                     y_mean - 2*y_std,
                     y_mean + 2*y_std,
                     alpha=0.2, label='95% 置信区间')
    plt.scatter(X_train, y_train, c='r', label='训练点')
    plt.legend()
    plt.show()
```

## 9. 发布流程

### 9.1 准备发布

```bash
# 更新版本号
# setup.py: version='0.2.0'
# src/__init__.py: __version__ = '0.2.0'

# 更新 CHANGELOG.md

# 运行所有测试
pytest tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

### 9.2 构建和发布

```bash
# 构建包
python setup.py sdist bdist_wheel

# 检查包
twine check dist/*

# 上传到 PyPI
twine upload dist/*

# 或上传到 TestPyPI
twine upload --repository testpypi dist/*
```

### 9.3 版本标签

```bash
# 创建标签
git tag -a v0.2.0 -m "Release version 0.2.0"

# 推送标签
git push origin v0.2.0
```

## 10. 贡献指南

### 10.1 如何贡献

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request
5. 等待代码审查

### 10.2 Pull Request 规范

- 清晰的标题和描述
- 包含相关测试
- 更新文档
- 通过所有检查

### 10.3 代码审查

- 代码风格一致性
- 测试覆盖率
- 文档完整性
- 性能影响

## 11. 参考资料

1. Python 项目结构: https://docs.python.org/3/tutorial/modules.html
2. pytest 文档: https://docs.pytest.org/
3. Black 文档: https://black.readthedocs.io/
4. Sphinx 文档: https://www.sphinx-doc.org/
5. Semantic Versioning: https://semver.org/
6. Conventional Commits: https://www.conventionalcommits.org/
