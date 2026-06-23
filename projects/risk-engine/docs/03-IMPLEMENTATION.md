# 风险管理引擎 - 实现文档

## 1. 项目结构

```
risk-engine/
├── src/
│   ├── __init__.py
│   ├── portfolio.py
│   ├── var_calculator.py
│   ├── stress_tester.py
│   └── risk_reporter.py
├── tests/
│   ├── __init__.py
│   ├── test_portfolio.py
│   ├── test_var_calculator.py
│   └── test_stress_tester.py
├── examples/
│   ├── basic_usage.py
│   ├── stress_test_example.py
│   └── risk_report_example.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 2. 核心实现

### 2.1 Portfolio 模块实现

#### Position 类
```python
@dataclass
class Position:
    symbol: str
    quantity: float
    current_price: float
    asset_class: str = "equity"

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
```

#### Portfolio 类
关键方法：
- `add_position()`: 添加持仓
- `remove_position()`: 移除持仓
- `total_value`: 计算组合总市值
- `weights`: 计算各持仓权重
- `calculate_portfolio_returns()`: 计算组合收益率

### 2.2 VaR Calculator 模块实现

#### 历史模拟法
```python
def _historical_var(self, returns, confidence_level):
    alpha = 1 - confidence_level
    var = np.percentile(returns, alpha * 100)
    losses_below_var = returns[returns <= var]
    cvar = np.mean(losses_below_var) if len(losses_below_var) > 0 else var
    return var, cvar
```

#### 参数法
```python
def _parametric_var(self, returns, confidence_level):
    mu = np.mean(returns)
    sigma = np.std(returns, ddof=1)
    z = stats.norm.ppf(1 - confidence_level)
    var = mu + z * sigma
    cvar = mu - sigma * stats.norm.pdf(z) / (1 - confidence_level)
    return var, cvar
```

#### 蒙特卡洛模拟法
```python
def _monte_carlo_var(self, returns, confidence_level, num_simulations):
    mu = np.mean(returns)
    sigma = np.std(returns, ddof=1)
    simulated_returns = np.random.normal(mu, sigma, num_simulations)
    var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
    losses_below_var = simulated_returns[simulated_returns <= var]
    cvar = np.mean(losses_below_var) if len(losses_below_var) > 0 else var
    return var, cvar
```

### 2.3 Stress Tester 模块实现

#### 历史情景
预定义了 4 个历史危机情景：
- 2008 金融危机
- 2020 新冠疫情
- 2000 互联网泡沫
- 黑色星期一

#### 反向压力测试
```python
def reverse_stress_test(self, target_loss, weights, risk_factor):
    factor_weight = weights[risk_factor]
    required_shock = target_loss / factor_weight
    return StressScenario(
        name="反向压力测试",
        description=f"要达到 {abs(target_loss)*100:.1f}% 的损失，"
                   f"{risk_factor} 需要下跌 {abs(required_shock)*100:.1f}%",
        shocks={risk_factor: required_shock}
    )
```

### 2.4 Risk Reporter 模块实现

#### 风险等级评估
```python
def _assess_risk_level(self, var_results, stress_test_results):
    # 获取 95% VaR
    # 获取最大压力测试损失
    # 根据阈值判断风险等级
    if var_95 < 0.02 and max_stress_loss < 0.10:
        return "低"
    elif var_95 < 0.05 and max_stress_loss < 0.20:
        return "中"
    elif var_95 < 0.10 and max_stress_loss < 0.35:
        return "高"
    else:
        return "极高"
```

## 3. 关键算法详解

### 3.1 CVaR 计算

CVaR (Conditional VaR) 也称为 Expected Shortfall，是 VaR 的扩展。

**历史模拟法 CVaR**：
1. 找到 VaR 对应的分位数
2. 计算所有低于 VaR 的损失的平均值

**参数法 CVaR**：
对于正态分布，CVaR 有解析公式：
```
CVaR = μ - σ × φ(z_α) / (1 - α)
```
其中 φ 是标准正态分布的概率密度函数。

### 3.2 蒙特卡洛模拟

**步骤**：
1. 估计参数（均值和标准差）
2. 生成随机数
3. 转换为收益率
4. 计算统计量

**注意事项**：
- 随机数种子设置确保可重复性
- 模拟次数影响精度（通常 10,000 次以上）
- 正态分布假设的局限性

### 3.3 压力测试损失计算

```python
def _apply_scenario(self, scenario, weights):
    position_losses = {}
    total_loss = 0.0

    for asset_class, weight in weights.items():
        shock = scenario.shocks.get(asset_class, 0)
        loss = weight * shock
        position_losses[asset_class] = loss
        total_loss += loss

    return total_loss
```

## 4. 数据处理

### 4.1 收益率数据格式

输入数据应为 Pandas DataFrame，列名为标的代码：
```python
returns_df = pd.DataFrame({
    "AAPL": [0.01, -0.02, 0.03, ...],
    "GOOGL": [0.02, -0.01, 0.01, ...],
    ...
})
```

### 4.2 权重计算

权重表示各资产类别在组合中的占比：
```python
weights = {
    "equity": 0.60,
    "bond": 0.30,
    "commodity": 0.10
}
```

## 5. 错误处理

### 5.1 输入验证
- 空数组检查
- 无效置信水平检查
- 缺失数据检查

### 5.2 异常处理
```python
if len(returns) == 0:
    raise ValueError("Returns array is empty")

if confidence_level <= 0 or confidence_level >= 1:
    raise ValueError("Confidence level must be between 0 and 1")
```

## 6. 性能优化

### 6.1 NumPy 向量化
使用 NumPy 的向量化操作代替循环：
```python
# 好的实现
portfolio_returns = returns_data @ weight_values

# 不好的实现
for i in range(len(returns_data)):
    total += returns_data[i] * weight_values[i]
```

### 6.2 内存管理
- 使用 `ddof=1` 计算样本标准差
- 避免不必要的数据复制

## 7. 代码规范

### 7.1 命名规范
- 类名：PascalCase
- 函数/方法：snake_case
- 常量：UPPER_SNAKE_CASE

### 7.2 文档规范
- 使用 Google 风格的 docstring
- 包含参数说明和返回值说明
- 提供使用示例

### 7.3 类型注解
```python
def calculate(
    self,
    returns: np.ndarray,
    method: VaRMethod = VaRMethod.HISTORICAL,
    confidence_level: float = 0.95,
    **kwargs
) -> VaRResult:
```
