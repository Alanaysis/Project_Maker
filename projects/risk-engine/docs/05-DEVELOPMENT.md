# 风险管理引擎 - 开发文档

## 1. 开发环境设置

### 1.1 系统要求
- Python 3.8+
- pip 或 conda

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

### 1.3 依赖说明
- numpy>=1.21.0: 数值计算
- scipy>=1.7.0: 统计分布
- pandas>=1.3.0: 数据处理
- pytest>=6.0.0: 测试框架

## 2. 快速开始

### 2.1 基本使用
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

### 2.2 压力测试
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

### 2.3 生成风险报告
```python
from src import RiskReporter

# 创建报告生成器
reporter = RiskReporter(portfolio, returns, weights)

# 生成报告
report = reporter.generate_report()

# 打印报告
print(reporter.format_text_report(report))
```

## 3. API 参考

### 3.1 Portfolio 类

#### 构造函数
```python
Portfolio(name: str, positions: List[Position] = [])
```

#### 方法
- `add_position(position: Position) -> None`: 添加持仓
- `remove_position(symbol: str) -> bool`: 移除持仓
- `get_position(symbol: str) -> Optional[Position]`: 获取持仓
- `calculate_portfolio_returns(returns_df: pd.DataFrame) -> np.ndarray`: 计算组合收益率

#### 属性
- `total_value -> float`: 组合总市值
- `symbols -> List[str]`: 标的代码列表
- `weights -> Dict[str, float]`: 各持仓权重

### 3.2 Position 类

#### 构造函数
```python
Position(symbol: str, quantity: float, current_price: float, asset_class: str = "equity")
```

#### 属性
- `market_value -> float`: 持仓市值

### 3.3 VaRCalculator 类

#### 构造函数
```python
VaRCalculator(portfolio_value: float)
```

#### 方法
- `calculate(returns, method, confidence_level, **kwargs) -> VaRResult`: 计算 VaR
- `calculate_multiple_confidence_levels(returns, method, levels) -> List[VaRResult]`: 计算多置信水平 VaR
- `compare_methods(returns, confidence_level) -> Dict[str, VaRResult]`: 比较不同方法

### 3.4 VaRResult 类

#### 属性
- `method: str`: 计算方法
- `confidence_level: float`: 置信水平
- `var: float`: VaR 值
- `cvar: float`: CVaR 值
- `portfolio_value: float`: 组合市值
- `var_amount: float`: VaR 金额
- `cvar_amount: float`: CVaR 金额

#### 方法
- `to_dict() -> Dict`: 转换为字典

### 3.5 StressTester 类

#### 构造函数
```python
StressTester(portfolio_value: float)
```

#### 方法
- `historical_stress_test(scenario_name, weights) -> StressTestResult`: 历史情景压力测试
- `hypothetical_stress_test(scenario, weights) -> StressTestResult`: 假设情景压力测试
- `reverse_stress_test(target_loss, weights, risk_factor) -> StressScenario`: 反向压力测试
- `run_multiple_scenarios(scenarios, weights) -> List[StressTestResult]`: 运行多个情景
- `sensitivity_analysis(weights, factor, shock_range, steps) -> List[Tuple]`: 敏感性分析

#### 预定义历史情景
- `2008_financial_crisis`: 2008 金融危机
- `2020_covid`: 2020 新冠疫情
- `2000_dotcom`: 2000 互联网泡沫
- `black_monday`: 黑色星期一

### 3.6 StressScenario 类

#### 构造函数
```python
StressScenario(name: str, description: str, shocks: Dict[str, float], probability: Optional[float] = None)
```

#### 属性
- `name: str`: 情景名称
- `description: str`: 情景描述
- `shocks: Dict[str, float]`: 各因子冲击
- `probability: Optional[float]`: 发生概率

### 3.7 RiskReporter 类

#### 构造函数
```python
RiskReporter(portfolio: Portfolio, returns: np.ndarray, weights: Dict[str, float])
```

#### 方法
- `generate_report(confidence_levels, scenarios) -> RiskReport`: 生成报告
- `format_text_report(report) -> str`: 格式化文本报告

## 4. 高级用法

### 4.1 自定义压力测试情景
```python
from src.stress_tester import StressScenario

# 创建自定义情景
scenario = StressScenario(
    name="自定义情景",
    description="股市下跌 25%，债券上涨 5%",
    shocks={"equity": -0.25, "bond": 0.05, "commodity": -0.10}
)

# 运行压力测试
result = tester.hypothetical_stress_test(scenario, weights)
```

### 4.2 敏感性分析
```python
# 分析股市不同涨跌幅对组合的影响
sensitivity = tester.sensitivity_analysis(
    weights,
    "equity",
    shock_range=(-0.50, 0.30),
    num_steps=9
)

for shock, loss in sensitivity:
    print(f"股市 {shock:+.0%} → 组合 {loss:+.2%}")
```

### 4.3 反向压力测试
```python
# 计算要达到 20% 损失，股市需要下跌多少
scenario = tester.reverse_stress_test(
    target_loss=-0.20,
    weights=weights,
    risk_factor="equity"
)

print(scenario.description)
```

### 4.4 比较不同 VaR 方法
```python
# 比较三种 VaR 方法
results = calculator.compare_methods(returns, 0.95)

for method, result in results.items():
    print(f"{method}: VaR = {abs(result.var):.2%}")
```

## 5. 错误处理

### 5.1 常见错误

#### ValueError: Returns array is empty
```python
# 错误：传入空数组
calculator.calculate(np.array([]), VaRMethod.HISTORICAL, 0.95)

# 正确：确保有数据
if len(returns) > 0:
    calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)
```

#### ValueError: Unknown scenario
```python
# 错误：使用不存在的情景
tester.historical_stress_test("invalid_scenario", weights)

# 正确：使用预定义情景
tester.historical_stress_test("2008_financial_crisis", weights)
```

#### ValueError: Risk factor not in weights
```python
# 错误：风险因子不在权重中
tester.reverse_stress_test(-0.20, weights, "invalid")

# 正确：使用权重中的因子
tester.reverse_stress_test(-0.20, weights, "equity")
```

## 6. 性能优化

### 6.1 大数据集处理
```python
# 使用 NumPy 向量化操作
portfolio_returns = returns_data @ weight_values

# 避免循环
# 不好
for i in range(len(returns)):
    total += returns[i] * weight[i]

# 好
total = np.sum(returns * weight)
```

### 6.2 蒙特卡洛模拟优化
```python
# 调整模拟次数
result = calculator.calculate(
    returns,
    VaRMethod.MONTE_CARLO,
    0.95,
    num_simulations=50000  # 增加模拟次数提高精度
)
```

## 7. 扩展开发

### 7.1 添加新的 VaR 方法
```python
# 1. 在 VaRMethod 枚举中添加
class VaRMethod(Enum):
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    NEW_METHOD = "new_method"  # 新方法

# 2. 在 VaRCalculator 中实现
def _new_method_var(self, returns, confidence_level):
    # 实现新方法
    pass

# 3. 更新 calculate 方法
def calculate(self, returns, method, confidence_level, **kwargs):
    if method == VaRMethod.NEW_METHOD:
        return self._new_method_var(returns, confidence_level)
```

### 7.2 添加新的压力测试情景
```python
# 在 StressTester.HISTORICAL_SCENARIOS 中添加
HISTORICAL_SCENARIOS = {
    # ... 现有情景
    "new_crisis": StressScenario(
        name="新危机",
        description="新危机的描述",
        shocks={"equity": -0.30, "bond": 0.05}
    )
}
```

### 7.3 添加新的报告格式
```python
# 在 RiskReporter 中添加新方法
def format_html_report(self, report: RiskReport) -> str:
    """生成 HTML 格式报告"""
    html = "<html><body>"
    html += f"<h1>{report.portfolio_name} 风险报告</h1>"
    # ... 添加更多 HTML
    html += "</body></html>"
    return html
```

## 8. 调试技巧

### 8.1 打印中间结果
```python
# 打印 VaR 计算过程
print(f"Mean: {np.mean(returns):.6f}")
print(f"Std: {np.std(returns):.6f}")
print(f"VaR: {result.var:.6f}")
```

### 8.2 使用断点
```python
import pdb; pdb.set_trace()  # 在需要的地方设置断点
```

### 8.3 日志记录
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Calculating VaR with method: {method}")
logger.info(f"VaR result: {result.var:.4%}")
```

## 9. 部署

### 9.1 打包
```bash
# 创建 setup.py
# 打包
python setup.py sdist bdist_wheel
```

### 9.2 发布
```bash
# 发布到 PyPI
twine upload dist/*
```

## 10. 常见问题

### Q: 为什么 VaR 是负数？
A: VaR 表示损失，负数表示相对于当前市值的损失比例。

### Q: CVaR 和 VaR 有什么区别？
A: CVaR 是当损失超过 VaR 时的预期损失，比 VaR 更保守。

### Q: 如何选择 VaR 方法？
A: 
- 历史模拟法：数据充足，不需要分布假设
- 参数法：计算快速，假设正态分布
- 蒙特卡洛：复杂产品，需要模拟

### Q: 压力测试的冲击如何设定？
A: 可以使用历史危机数据，或根据业务场景假设。
