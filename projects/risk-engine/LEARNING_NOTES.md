# 风险管理引擎 - 学习笔记

## 项目概述

本项目实现了一个风险管理引擎，支持 VaR 计算和压力测试。通过这个项目，我学习了风险度量方法、VaR 计算和压力测试的核心概念。

## 学习目标

1. **理解风险度量方法**
   - VaR (Value at Risk)
   - CVaR (Conditional VaR / Expected Shortfall)
   - 波动率
   - Beta

2. **掌握 VaR 计算**
   - 历史模拟法
   - 参数法
   - 蒙特卡洛模拟法

3. **学会压力测试**
   - 历史情景压力测试
   - 假设情景压力测试
   - 反向压力测试
   - 敏感性分析

## 核心概念

### 1. Value at Risk (VaR)

**定义**：在给定的置信水平下，投资组合在特定时间范围内可能遭受的最大损失。

**示例**：95% 的日 VaR 为 100 万美元意味着：
- 在 95% 的情况下，每日损失不会超过 100 万美元
- 在 5% 的情况下，损失可能超过 100 万美元

**数学表示**：
```
P(Loss > VaR_α) = 1 - α
```

### 2. Conditional VaR (CVaR)

**定义**：当损失超过 VaR 时的预期损失。

**优势**：
- 比 VaR 更保守
- 满足一致性风险度量的次可加性
- 能更好地捕捉尾部风险

**数学表示**：
```
CVaR_α = E[Loss | Loss > VaR_α]
```

### 3. VaR 计算方法

#### 历史模拟法
- **原理**：直接使用历史收益率分布
- **优点**：不需要分布假设
- **缺点**：依赖历史数据

#### 参数法
- **原理**：假设正态分布，使用均值和方差
- **公式**：VaR = μ + z_α × σ
- **优点**：计算快速
- **缺点**：低估尾部风险

#### 蒙特卡洛模拟法
- **原理**：随机模拟生成收益率路径
- **优点**：灵活性高
- **缺点**：计算量大

### 4. 压力测试

**定义**：评估投资组合在极端市场条件下的表现。

**类型**：
- 历史情景：使用历史危机事件
- 假设情景：自定义极端情景
- 反向压力测试：从目标损失反向推导

## 实现细节

### 1. Portfolio 模块

**职责**：管理投资组合的持仓数据。

**关键实现**：
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

**学习点**：
- 使用 dataclass 简化数据类定义
- 使用 @property 实现计算属性
- 组合模式管理多个持仓

### 2. VaR Calculator 模块

**职责**：实现多种 VaR 计算方法。

**关键实现**：
```python
def _historical_var(self, returns, confidence_level):
    alpha = 1 - confidence_level
    var = np.percentile(returns, alpha * 100)
    losses_below_var = returns[returns <= var]
    cvar = np.mean(losses_below_var) if len(losses_below_var) > 0 else var
    return var, cvar
```

**学习点**：
- 使用 NumPy 的 percentile 函数计算分位数
- 条件平均值计算 CVaR
- 处理边界情况（空数组）

### 3. Stress Tester 模块

**职责**：实现压力测试功能。

**关键实现**：
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

**学习点**：
- 情景设计与应用
- 加权损失计算
- 敏感性分析实现

### 4. Risk Reporter 模块

**职责**：生成风险分析报告。

**关键实现**：
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

**学习点**：
- 综合多种风险指标
- 风险等级评估
- 报告格式化

## 关键收获

### 1. 风险度量的重要性
- VaR 是最广泛使用的风险度量方法
- CVaR 比 VaR 更保守，能更好地捕捉尾部风险
- 不同的 VaR 方法有各自的优缺点

### 2. 压力测试的价值
- 历史情景压力测试提供现实的参考
- 反向压力测试帮助识别脆弱点
- 敏感性分析帮助理解风险因子的影响

### 3. 实现技巧
- 使用 NumPy 进行高效的数值计算
- 使用 dataclass 简化数据结构
- 使用枚举类型管理常量
- 使用类型注解提高代码可读性

### 4. 测试的重要性
- 单元测试确保各个模块的正确性
- 边界测试处理异常情况
- 集成测试验证模块间的协作

## 遇到的挑战

### 1. CVaR 计算
**问题**：当没有损失超过 VaR 时，CVaR 的计算。

**解决**：检查是否有足够的数据点，如果没有则使用 VaR 作为 CVaR。

```python
losses_below_var = returns[returns <= var]
cvar = np.mean(losses_below_var) if len(losses_below_var) > 0 else var
```

### 2. 蒙特卡洛模拟的随机性
**问题**：每次运行结果不同。

**解决**：设置随机种子确保可重复性。

```python
np.random.seed(42)
```

### 3. 压力测试的冲击设计
**问题**：如何设计合理的冲击幅度。

**解决**：参考历史危机数据，并提供自定义选项。

## 进一步学习

### 1. 扩展功能
- 添加更多 VaR 方法（如 Cornish-Fisher VaR）
- 实现 Copula 模型处理相关性
- 添加流动性风险度量

### 2. 性能优化
- 使用 Cython 或 Numba 加速计算
- 实现并行计算处理大组合
- 优化内存使用

### 3. 实际应用
- 接入实时市场数据
- 集成到交易系统
- 实现自动化风险监控

## 参考资源

### 书籍
- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*
- Hull, J. C. (2018). *Risk Management and Financial Institutions*
- McNeil, A. J., Frey, R., & Embrechts, P. (2015). *Quantitative Risk Management*

### 在线资源
- [Investopedia - Value at Risk (VaR)](https://www.investopedia.com/terms/v/var.asp)
- [Federal Reserve - Stress Testing](https://www.federalreserve.gov/supervisionreg/stress-tests.htm)
- [Basel Committee on Banking Supervision](https://www.bis.org/bcbs/)

## 总结

通过本项目，我深入理解了风险管理的核心概念和实现方法。VaR 计算和压力测试是金融风险管理的基础工具，掌握这些工具对于理解和管理金融风险至关重要。

项目的设计遵循了模块化、可测试和可扩展的原则，为后续的功能扩展和性能优化奠定了基础。
