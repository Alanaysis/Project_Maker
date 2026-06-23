# 测试文档

## 测试策略

### 测试层次
1. **单元测试**: 每个因子计算的正确性
2. **集成测试**: 因子 -> 评估 -> 回测的完整流程
3. **数值测试**: 验证数学公式的手动计算结果

### 测试数据
使用 `generate_stock_data()` 生成可控的测试数据:
- 固定随机种子确保可复现
- 较小规模 (20只股票, 100天) 加快测试

## 测试用例

### test_factors.py

| 测试类 | 测试内容 | 验证方式 |
|--------|----------|----------|
| TestMomentumFactors | 动量因子形状、值范围 | shape 检查, NaN 位置, 手动计算对比 |
| TestVolatilityFactors | 波动率非负, 下行<=总波动率 | 数值范围检查 |
| TestLiquidityFactors | Amihud 非负, 成交量动量非负 | 数值范围检查 |
| TestTechnicalFactors | RSI 在 0~100, 布林带非负 | 范围约束检查 |
| TestCompositeFactor | 组合因子形状正确 | shape 检查 |

### test_evaluation.py

| 测试类 | 测试内容 | 验证方式 |
|--------|----------|----------|
| TestICAnalysis | IC 返回 Series, 值在 [-1,1] | 类型和范围检查 |
| TestGroupReturns | 分组数正确, 列名正确 | shape 和列名检查 |
| TestFactorProperties | 换手率在 [0,1], 衰减分析有结果 | 范围和类型检查 |
| TestPerformanceSummary | 包含必要指标, Sharpe 合理 | key 存在性, 数值范围 |

### test_backtest.py

| 测试类 | 测试内容 | 验证方式 |
|--------|----------|----------|
| TestBacktestEngine | 运行返回结果, NAV 从1开始 | 结果存在性, 初始值检查 |
| TestBacktestEngine | 结果包含必要指标 | summary key 检查 |
| TestBacktestEngine | 交易成本效果 | 高成本 <= 无成本总收益 |
| TestMultiFactorBacktest | 多因子回测能运行 | 结果存在性 |

## 运行测试

```bash
# 运行所有测试
cd projects/factor-mining
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_factors.py -v

# 运行并显示覆盖率
python -m pytest tests/ -v --tb=short
```

## 测试结果示例

```
tests/test_factors.py::TestMomentumFactors::test_momentum_shape PASSED
tests/test_factors.py::TestMomentumFactors::test_momentum_values PASSED
tests/test_factors.py::TestVolatilityFactors::test_volatility_positive PASSED
tests/test_evaluation.py::TestICAnalysis::test_rank_ic_returns_series PASSED
tests/test_evaluation.py::TestICAnalysis::test_rank_ic_range PASSED
tests/test_backtest.py::TestBacktestEngine::test_run_returns_result PASSED
...
```

## 边界条件

### 数据不足
- 股票数 < 分组数时, 分组返回 NaN
- 日期数 < 窗口长度时, 因子为 NaN

### 全 NaN 输入
- 因子计算返回全 NaN DataFrame
- IC 返回空 Series
- 回测返回零收益

### 单只股票
- 分组无法进行 (需要 >= n_groups 只股票)
- IC 计算正常但样本量=1
