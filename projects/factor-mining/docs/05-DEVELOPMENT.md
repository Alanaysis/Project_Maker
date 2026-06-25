# 因子挖掘框架 - 开发手册

## 1. 环境配置

### 1.1 Python 环境

```bash
# 推荐使用 Python 3.8+
python --version

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 1.2 安装依赖

```bash
cd projects/factor-mining
pip install -r requirements.txt
```

### 1.3 依赖说明

| 包 | 用途 | 必需 |
|---|------|------|
| numpy | 数值计算 | 是 |
| pandas | 数据处理 | 是 |
| scipy | 统计分析 | 是 |
| scikit-learn | 机器学习 | 是 |
| matplotlib | 可视化 | 否 |
| seaborn | 统计图表 | 否 |
| statsmodels | 统计建模 | 否 |
| tqdm | 进度条 | 否 |
| pyarrow | 数据存储 | 否 |

## 2. 编译说明

本项目为纯 Python 项目，无需编译。

### 2.1 开发模式安装

```bash
# 如果需要以开发模式安装
pip install -e .
```

### 2.2 代码检查

```bash
# 使用 flake8 检查代码风格
pip install flake8
flake8 src/ --max-line-length=100

# 使用 mypy 检查类型
pip install mypy
mypy src/
```

## 3. 运行方式

### 3.1 运行示例

```bash
# 基础示例
python examples/basic_usage.py

# 高级示例
python examples/advanced_usage.py
```

### 3.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_technical.py -v

# 运行并显示覆盖率
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

### 3.3 作为库使用

```python
# 导入因子计算模块
from src.factors.technical import TechnicalFactors
from src.factors.fundamental import FundamentalFactors

# 导入评估模块
from src.evaluation.ic_analysis import ICAnalysis
from src.evaluation.group_backtest import GroupBacktest

# 导入优化模块
from src.optimization.standardizer import FactorStandardizer
from src.optimization.neutralizer import FactorNeutralizer

# 导入组合模块
from src.combination.equal_weight import EqualWeightCombination

# 导入回测模块
from src.backtest.portfolio_backtest import PortfolioBacktest
from src.backtest.performance import PerformanceAnalyzer
```

## 4. 开发指南

### 4.1 添加新因子

1. 在 `src/factors/` 目录下创建或编辑因子文件
2. 实现因子计算函数，遵循统一接口
3. 在 `__init__.py` 中导出新因子
4. 编写测试用例
5. 更新文档

示例:
```python
# src/factors/technical.py
@staticmethod
def my_new_factor(close: pd.Series, window: int = 20) -> pd.Series:
    """
    我的新因子

    原理: ...
    计算: ...

    参数:
        close: 收盘价序列
        window: 回看窗口

    返回:
        因子值序列
    """
    # 实现因子计算逻辑
    return result
```

### 4.2 添加新评估方法

1. 在 `src/evaluation/` 目录下创建或编辑文件
2. 实现评估函数
3. 在 `FactorBacktest` 中集成新方法
4. 编写测试用例

### 4.3 代码规范

- 遵循 PEP 8 代码风格
- 每个函数都要有 docstring
- 类型注解: 使用 typing 模块
- 命名规范:
  - 类名: PascalCase
  - 函数名: snake_case
  - 常量: UPPER_SNAKE_CASE

### 4.4 测试规范

- 每个模块都要有对应的测试文件
- 测试函数命名: `test_功能名`
- 使用 pytest fixtures 提供测试数据
- 测试覆盖率目标: > 80%

## 5. 常见问题

### 5.1 导入错误

如果遇到 `ModuleNotFoundError`，确保:
1. 在项目根目录下运行
2. 或者将 `src` 目录添加到 Python 路径

```bash
# 方法 1: 在项目根目录运行
cd projects/factor-mining
python examples/basic_usage.py

# 方法 2: 设置 PYTHON_PATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
python examples/basic_usage.py
```

### 5.2 数据格式问题

确保输入数据:
1. 使用 pd.DatetimeIndex 作为日期索引
2. 股票代码使用字符串格式
3. 数值列使用 float 类型

### 5.3 性能优化

对于大规模数据:
1. 使用向量化操作代替循环
2. 使用 `apply` 代替逐行处理
3. 考虑使用 multiprocessing 并行计算
4. 使用 pyarrow 进行高效数据存储
