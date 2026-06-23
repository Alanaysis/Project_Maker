# 系统设计

## 整体架构

```
数据层 (data.py)
  ├── generate_stock_data()   生成模拟股票数据
  ├── load_example_data()     加载示例数据
  └── split_train_test()      训练/测试分割

因子层 (factors.py)
  └── FactorCalculator
       ├── 动量因子: momentum, short_term_reversal, weighted_momentum
       ├── 波动率因子: volatility, downside_volatility, atr
       ├── 流动性因子: turnover_rate, amihud_illiquidity, volume_momentum
       ├── 技术因子: rsi, bollinger_width, price_to_ma
       └── 组合因子: composite_score

评估层 (evaluation.py)
  └── FactorEvaluator
       ├── IC分析: rank_ic, ic_summary
       ├── 分组收益: group_returns, long_short_return
       ├── 因子属性: factor_turnover, factor_decay
       └── 绩效摘要: performance_summary

回测层 (backtest.py)
  ├── BacktestConfig        回测配置
  ├── BacktestEngine        回测引擎
  ├── BacktestResult        回测结果
  └── multi_factor_backtest 多因子回测
```

## 数据结构设计

### DataFrame 统一格式
所有数据使用 Pandas DataFrame, 统一格式:
- **index**: 日期 (DatetimeIndex)
- **columns**: 股票代码

```python
price_df:
              STOCK_000  STOCK_001  STOCK_002
2023-01-02     45.23      78.56      12.34
2023-01-03     45.67      78.12      12.45
```

### 因子计算的 NaN 处理
- 滚动窗口前 N 行为 NaN
- 因子值本身为 NaN 的位置在评估时自动排除
- 使用 `dropna()` 进行截面对齐

## 因子计算设计

### 统一接口
```python
class FactorCalculator:
    def __init__(self, price, volume, returns=None, high=None, low=None)
    def momentum(self, window=20) -> pd.DataFrame
    def volatility(self, window=20) -> pd.DataFrame
    ...
```

### 截面标准化
组合因子时使用 z-score 标准化:
```python
z = (x - mean) / std
```

## 评估框架设计

### IC 计算流程
```
对每个日期 t:
  1. 获取截面因子值 f_t
  2. 获取截面未来收益 r_{t+1}
  3. 计算 rank 相关系数
汇总: IC均值, IC标准差, ICIR, t统计量
```

### 分组回测流程
```
对每个日期 t:
  1. 按因子值将股票分为 N 组 (分位数)
  2. 计算每组的等权平均收益
  3. 多空收益 = G_N - G_1
```

## 回测框架设计

### 权重分配
- **等权**: 每组内股票等权重
- **多空**: 最高组正权重, 最低组负权重
- **纯多头**: 仅最高组有正权重

### 交易成本
- 每次换仓扣除双边交易成本
- 成本 = 换手率 * 2 * 单边费率

### 换仓逻辑
- 支持自定义换仓频率 (每日/每周/每月)
- 换手率计算: |新权重 - 旧权重| 的总变化 / 2

## 扩展设计

### 添加新因子
继承或扩展 `FactorCalculator` 类:
```python
def my_custom_factor(self, param):
    # 实现因子逻辑
    return factor_df
```

### 添加新评估指标
扩展 `FactorEvaluator` 类:
```python
def my_metric(self):
    # 实现评估逻辑
    return value
```
