# 风险管理引擎 - 设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    风险管理引擎                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Portfolio   │  │VaR Calculator│  │Stress Tester │      │
│  │    模块       │  │    模块       │  │    模块       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                 │
│                    ┌──────────────┐                         │
│                    │Risk Reporter │                         │
│                    │    模块       │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心流程

```
持仓数据 → 风险计算 → VaR 估计 → 压力测试 → 风险报告
```

## 2. 模块设计

### 2.1 Portfolio 模块

**职责**：管理投资组合的持仓数据。

**核心类**：
- `Position`: 表示单个持仓
- `Portfolio`: 表示投资组合

**主要功能**：
- 添加/移除持仓
- 计算组合总市值
- 计算各持仓权重
- 计算组合收益率

### 2.2 VaR Calculator 模块

**职责**：实现多种 VaR 计算方法。

**核心类**：
- `VaRCalculator`: VaR 计算器
- `VaRResult`: VaR 计算结果

**支持的方法**：
- 历史模拟法 (Historical Simulation)
- 参数法 (Parametric / Variance-Covariance)
- 蒙特卡洛模拟法 (Monte Carlo Simulation)

**主要功能**：
- 单一方法 VaR 计算
- 多置信水平 VaR 计算
- 不同方法结果比较

### 2.3 Stress Tester 模块

**职责**：实现压力测试功能。

**核心类**：
- `StressTester`: 压力测试器
- `StressScenario`: 压力测试情景
- `StressTestResult`: 压力测试结果

**支持的测试类型**：
- 历史情景压力测试
- 假设情景压力测试
- 反向压力测试
- 敏感性分析

**预定义历史情景**：
- 2008 金融危机
- 2020 新冠疫情
- 2000 互联网泡沫
- 黑色星期一

### 2.4 Risk Reporter 模块

**职责**：生成风险分析报告。

**核心类**：
- `RiskReporter`: 风险报告生成器
- `RiskReport`: 风险报告

**主要功能**：
- 综合 VaR 和压力测试结果
- 评估风险等级
- 生成格式化报告

## 3. 数据结构设计

### 3.1 Position 数据结构

```python
@dataclass
class Position:
    symbol: str           # 标的代码
    quantity: float       # 持仓数量
    current_price: float  # 当前价格
    asset_class: str      # 资产类别
```

### 3.2 VaR Result 数据结构

```python
@dataclass
class VaRResult:
    method: str            # 计算方法
    confidence_level: float # 置信水平
    var: float             # VaR 值
    cvar: float            # CVaR 值
    portfolio_value: float # 组合市值
    var_amount: float      # VaR 金额
    cvar_amount: float     # CVaR 金额
```

### 3.3 Stress Scenario 数据结构

```python
@dataclass
class StressScenario:
    name: str              # 情景名称
    description: str       # 情景描述
    shocks: Dict[str, float]  # 各因子冲击
    probability: float     # 发生概率
```

## 4. 算法设计

### 4.1 历史模拟法 VaR

```python
def historical_var(returns, confidence_level):
    alpha = 1 - confidence_level
    var = np.percentile(returns, alpha * 100)
    cvar = np.mean(returns[returns <= var])
    return var, cvar
```

### 4.2 参数法 VaR

```python
def parametric_var(returns, confidence_level):
    mu = np.mean(returns)
    sigma = np.std(returns)
    z = norm.ppf(1 - confidence_level)
    var = mu + z * sigma
    cvar = mu - sigma * norm.pdf(z) / (1 - confidence_level)
    return var, cvar
```

### 4.3 蒙特卡洛模拟法 VaR

```python
def monte_carlo_var(returns, confidence_level, num_simulations):
    mu = np.mean(returns)
    sigma = np.std(returns)
    simulated = np.random.normal(mu, sigma, num_simulations)
    var = np.percentile(simulated, (1 - confidence_level) * 100)
    cvar = np.mean(simulated[simulated <= var])
    return var, cvar
```

## 5. 接口设计

### 5.1 VaRCalculator 接口

```python
class VaRCalculator:
    def calculate(self, returns, method, confidence_level, **kwargs) -> VaRResult
    def calculate_multiple_confidence_levels(self, returns, method, levels) -> List[VaRResult]
    def compare_methods(self, returns, confidence_level) -> Dict[str, VaRResult]
```

### 5.2 StressTester 接口

```python
class StressTester:
    def historical_stress_test(self, scenario_name, weights) -> StressTestResult
    def hypothetical_stress_test(self, scenario, weights) -> StressTestResult
    def reverse_stress_test(self, target_loss, weights, risk_factor) -> StressScenario
    def run_multiple_scenarios(self, scenarios, weights) -> List[StressTestResult]
    def sensitivity_analysis(self, weights, factor, shock_range, steps) -> List[Tuple]
```

### 5.3 RiskReporter 接口

```python
class RiskReporter:
    def generate_report(self, confidence_levels, scenarios) -> RiskReport
    def format_text_report(self, report) -> str
```

## 6. 依赖关系

### 6.1 外部依赖
- NumPy: 数值计算
- SciPy: 统计分布
- Pandas: 数据处理

### 6.2 内部依赖
- Portfolio → VaRCalculator (提供组合收益率)
- Portfolio + VaRCalculator → RiskReporter (生成报告)
- Portfolio + StressTester → RiskReporter (生成报告)

## 7. 扩展性设计

### 7.1 新增 VaR 方法
1. 在 `VaRMethod` 枚举中添加新方法
2. 在 `VaRCalculator` 中实现新方法
3. 更新 `calculate` 方法的分发逻辑

### 7.2 新增压力测试情景
1. 在 `StressTester.HISTORICAL_SCENARIOS` 中添加情景
2. 或创建自定义 `StressScenario` 对象

### 7.3 新增报告格式
1. 在 `RiskReporter` 中添加新的格式化方法
2. 如 `format_html_report`, `format_json_report` 等
