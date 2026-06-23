# 风险管理引擎 - 测试文档

## 1. 测试策略

### 1.1 测试类型
- 单元测试：测试各个模块的独立功能
- 集成测试：测试模块间的协作
- 边界测试：测试边界条件和异常情况

### 1.2 测试覆盖
- 所有公共接口
- 关键算法
- 错误处理路径
- 边界条件

## 2. 测试环境

### 2.1 依赖
```
pytest>=6.0.0
numpy>=1.21.0
scipy>=1.7.0
pandas>=1.3.0
```

### 2.2 运行测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_var_calculator.py

# 运行详细输出
pytest tests/ -v

# 运行并显示覆盖率
pytest tests/ --cov=src
```

## 3. 单元测试

### 3.1 Portfolio 测试

#### 测试用例：持仓创建
```python
def test_position_creation():
    pos = Position("AAPL", 100, 150.0)
    assert pos.symbol == "AAPL"
    assert pos.quantity == 100
    assert pos.current_price == 150.0
```

#### 测试用例：市值计算
```python
def test_market_value():
    pos = Position("AAPL", 100, 150.0)
    assert pos.market_value == 15000.0
```

#### 测试用例：权重计算
```python
def test_weights():
    portfolio = Portfolio("Test")
    portfolio.add_position(Position("AAPL", 100, 100.0))  # 10000
    portfolio.add_position(Position("GOOGL", 10, 1000.0))  # 10000

    weights = portfolio.weights
    assert weights["AAPL"] == pytest.approx(0.5)
    assert weights["GOOGL"] == pytest.approx(0.5)
```

### 3.2 VaR Calculator 测试

#### 测试用例：历史模拟法 VaR
```python
def test_historical_var():
    calculator = VaRCalculator(portfolio_value=1000000)
    returns = np.random.normal(0.001, 0.02, 252)

    result = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)

    assert result.method == "historical"
    assert result.confidence_level == 0.95
    assert result.var < 0  # VaR 应该是负数（损失）
    assert result.cvar <= result.var  # CVaR 应该小于等于 VaR
```

#### 测试用例：参数法 VaR
```python
def test_parametric_var():
    calculator = VaRCalculator(portfolio_value=1000000)
    returns = np.random.normal(0.001, 0.02, 252)

    result = calculator.calculate(returns, VaRMethod.PARAMETRIC, 0.95)

    assert result.method == "parametric"
    assert result.var < 0
```

#### 测试用例：不同置信水平
```python
def test_var_at_different_confidence_levels():
    calculator = VaRCalculator(portfolio_value=1000000)
    returns = np.random.normal(0.001, 0.02, 252)

    result_90 = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.90)
    result_95 = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)
    result_99 = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.99)

    # 更高的置信水平应该有更大的 VaR（更负）
    assert result_90.var > result_95.var > result_99.var
```

#### 测试用例：空输入
```python
def test_empty_returns():
    calculator = VaRCalculator(portfolio_value=1000000)

    with pytest.raises(ValueError, match="Returns array is empty"):
        calculator.calculate(np.array([]), VaRMethod.HISTORICAL, 0.95)
```

### 3.3 Stress Tester 测试

#### 测试用例：历史情景压力测试
```python
def test_historical_stress_test():
    tester = StressTester(portfolio_value=1000000)
    weights = {"equity": 0.60, "bond": 0.30, "commodity": 0.10}

    result = tester.historical_stress_test("2008_financial_crisis", weights)

    assert result.portfolio_loss < 0  # 应该是负数（损失）
    assert result.portfolio_loss_amount < 0
```

#### 测试用例：反向压力测试
```python
def test_reverse_stress_test():
    tester = StressTester(portfolio_value=1000000)
    weights = {"equity": 0.60, "bond": 0.30, "commodity": 0.10}

    scenario = tester.reverse_stress_test(
        target_loss=-0.20,
        weights=weights,
        risk_factor="equity"
    )

    assert "equity" in scenario.shocks
    assert scenario.shocks["equity"] < 0  # 应该是负冲击
```

#### 测试用例：敏感性分析
```python
def test_sensitivity_analysis():
    tester = StressTester(portfolio_value=1000000)
    weights = {"equity": 0.60, "bond": 0.30, "commodity": 0.10}

    results = tester.sensitivity_analysis(
        weights, "equity", shock_range=(-0.30, 0.10), num_steps=5
    )

    assert len(results) == 5
    for shock, loss in results:
        assert isinstance(shock, float)
        assert isinstance(loss, float)
```

## 4. 集成测试

### 4.1 完整流程测试
```python
def test_full_risk_analysis():
    # 创建组合
    portfolio = Portfolio("Test")
    portfolio.add_position(Position("AAPL", 1000, 150.0))

    # 生成收益率数据
    np.random.seed(42)
    returns_df = pd.DataFrame({
        "AAPL": np.random.normal(0.001, 0.02, 252)
    })

    # 计算组合收益率
    portfolio_returns = portfolio.calculate_portfolio_returns(returns_df)

    # 计算 VaR
    var_calculator = VaRCalculator(portfolio.total_value)
    var_result = var_calculator.calculate(portfolio_returns, VaRMethod.HISTORICAL, 0.95)

    # 压力测试
    stress_tester = StressTester(portfolio.total_value)
    weights = {"equity": 1.0}
    stress_result = stress_tester.historical_stress_test("2008_financial_crisis", weights)

    # 验证
    assert var_result.var < 0
    assert stress_result.portfolio_loss < 0
```

## 5. 边界测试

### 5.1 极端值测试
```python
def test_extreme_values():
    # 测试全为正收益
    returns = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    calculator = VaRCalculator(1000000)
    result = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)
    assert result.var > 0  # 即使 95% VaR 也是正的

    # 测试全为负收益
    returns = np.array([-0.01, -0.02, -0.03, -0.04, -0.05])
    result = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)
    assert result.var < 0
```

### 5.2 单一值测试
```python
def test_single_value():
    returns = np.array([0.01])
    calculator = VaRCalculator(1000000)
    result = calculator.calculate(returns, VaRMethod.HISTORICAL, 0.95)
    assert result.var == 0.01
```

## 6. 测试数据

### 6.1 固定随机种子
```python
@pytest.fixture
def sample_returns():
    np.random.seed(42)  # 确保可重复性
    return np.random.normal(0.001, 0.02, 252)
```

### 6.2 测试夹具
```python
@pytest.fixture
def calculator():
    return VaRCalculator(portfolio_value=1000000)

@pytest.fixture
def sample_weights():
    return {
        "equity": 0.60,
        "bond": 0.30,
        "commodity": 0.10
    }
```

## 7. 测试报告

### 7.1 运行测试
```bash
# 生成详细报告
pytest tests/ -v --tb=short

# 生成 JUnit XML 报告
pytest tests/ --junitxml=test-results.xml

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 7.2 测试指标
- 测试通过率
- 代码覆盖率
- 测试执行时间
- 失败测试详情

## 8. 持续集成

### 8.1 GitHub Actions 配置示例
```yaml
name: Tests

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
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v
```
