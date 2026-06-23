# 风险管理引擎

一个基于 Python 的风险管理引擎，支持 VaR 计算和压力测试。

## 功能特性

### VaR 计算
- **历史模拟法 (Historical Simulation)**: 直接使用历史收益率分布
- **参数法 (Parametric/Variance-Covariance)**: 假设正态分布
- **蒙特卡洛模拟法 (Monte Carlo Simulation)**: 随机模拟

### 压力测试
- **历史情景压力测试**: 使用历史危机事件作为情景
- **假设情景压力测试**: 自定义压力测试情景
- **反向压力测试**: 计算达到目标损失所需的冲击
- **敏感性分析**: 分析单个风险因子的影响

### 风险报告
- 综合 VaR 和压力测试结果
- 风险等级评估
- 格式化文本报告

## 项目结构

```
risk-engine/
├── src/
│   ├── __init__.py
│   ├── portfolio.py          # 持仓数据管理
│   ├── var_calculator.py     # VaR 计算
│   ├── stress_tester.py      # 压力测试
│   └── risk_reporter.py      # 风险报告
├── tests/
│   ├── test_portfolio.py
│   ├── test_var_calculator.py
│   └── test_stress_tester.py
├── examples/
│   ├── basic_usage.py        # 基本使用示例
│   ├── stress_test_example.py # 压力测试示例
│   └── risk_report_example.py # 风险报告示例
├── docs/
│   ├── 01-RESEARCH.md        # 研究文档
│   ├── 02-DESIGN.md          # 设计文档
│   ├── 03-IMPLEMENTATION.md  # 实现文档
│   ├── 04-TESTING.md         # 测试文档
│   └── 05-DEVELOPMENT.md     # 开发文档
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from src import Portfolio, Position, VaRCalculator, StressTester
from src.var_calculator import VaRMethod
import numpy as np

# 创建投资组合
portfolio = Portfolio("我的组合")
portfolio.add_position(Position("AAPL", 1000, 150.0, "equity"))
portfolio.add_position(Position("BND", 2000, 85.0, "bond"))

# 准备收益率数据
returns = np.random.normal(0.001, 0.02, 252)

# 计算 VaR
calculator = VaRCalculator(portfolio.total_value)
result = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)

print(f"95% VaR: {abs(result.var):.2%}")
print(f"VaR 金额: ${result.var_amount:,.2f}")
```

### 压力测试

```python
from src import StressTester

# 创建压力测试器
tester = StressTester(portfolio.total_value)

# 定义权重
weights = {"equity": 0.7, "bond": 0.3}

# 运行历史情景压力测试
result = tester.historical_stress_test("2008_financial_crisis", weights)

print(f"情景: {result.scenario.name}")
print(f"损失: {abs(result.portfolio_loss):.2%}")
```

### 生成风险报告

```python
from src import RiskReporter

# 创建报告生成器
reporter = RiskReporter(portfolio, returns, weights)

# 生成报告
report = reporter.generate_report()

# 打印报告
print(reporter.format_text_report(report))
```

## 示例

运行示例脚本查看完整功能演示：

```bash
# 基本使用示例
python examples/basic_usage.py

# 压力测试示例
python examples/stress_test_example.py

# 风险报告示例
python examples/risk_report_example.py
```

## 测试

运行测试套件：

```bash
# 运行所有测试
pytest tests/

# 运行详细输出
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_var_calculator.py
```

## VaR 计算方法

### 历史模拟法
直接使用历史收益率分布来估计 VaR。

**优点**：
- 不需要假设特定分布
- 能捕捉实际的分布特征

**缺点**：
- 依赖历史数据的代表性

### 参数法
假设收益率服从正态分布，使用均值和方差来估计 VaR。

**优点**：
- 计算快速
- 易于理解

**缺点**：
- 依赖正态分布假设
- 低估尾部风险

### 蒙特卡洛模拟法
通过随机模拟生成大量可能的收益率路径。

**优点**：
- 可以处理复杂的分布
- 灵活性高

**缺点**：
- 计算量大

## 压力测试类型

### 历史情景压力测试
使用历史上发生过的危机事件作为情景。

预定义情景：
- 2008 金融危机
- 2020 新冠疫情
- 2000 互联网泡沫
- 黑色星期一

### 假设情景压力测试
设计假设的极端情景进行测试。

### 反向压力测试
从目标损失出发，反向推导需要多大的冲击。

## 学习目标

通过本项目，你将学习到：

1. **风险度量方法**: 理解 VaR、CVaR 等风险指标
2. **VaR 计算**: 掌握三种 VaR 计算方法
3. **压力测试**: 学会设计和执行压力测试
4. **风险报告**: 生成专业的风险分析报告

## 依赖

- Python 3.8+
- NumPy >= 1.21.0
- SciPy >= 1.7.0
- Pandas >= 1.3.0
- pytest >= 6.0.0

## 许可证

MIT License

## 参考资源

- [Investopedia - Value at Risk (VaR)](https://www.investopedia.com/terms/v/var.asp)
- [Jorion, P. (2006). Value at Risk: The New Benchmark for Managing Financial Risk](https://www.amazon.com/Value-Risk-Benchmark-Managing-Financial/dp/0071464956)
- [Federal Reserve - Stress Testing](https://www.federalreserve.gov/supervisionreg/stress-tests.htm)
