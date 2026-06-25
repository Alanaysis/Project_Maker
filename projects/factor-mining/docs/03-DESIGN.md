# 因子挖掘框架 - 技术设计

## 1. 架构设计

### 1.1 模块划分

```
┌─────────────────────────────────────────────────────┐
│                    应用层 (app)                       │
│  FactorLibrary │ FactorMonitor │ FactorReport        │
├─────────────────────────────────────────────────────┤
│                    回测层 (backtest)                   │
│  DataReplay │ FactorBacktest │ PortfolioBacktest      │
├─────────────────────────────────────────────────────┤
│                    组合层 (combination)                │
│  EqualWeight │ ICWeight │ Optimized │ MLCombination   │
├─────────────────────────────────────────────────────┤
│                    优化层 (optimization)               │
│  Neutralizer │ Standardizer │ Winsorizer │ Filler     │
├─────────────────────────────────────────────────────┤
│                    评估层 (evaluation)                 │
│  ICAnalysis │ IRAnalysis │ GroupBacktest │ Decay       │
├─────────────────────────────────────────────────────┤
│                    因子层 (factors)                    │
│  Technical │ Fundamental │ Alternative │ Combinator   │
└─────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
原始数据 → 因子计算 → 预处理 → 评估 → 组合 → 回测 → 报告
   │          │         │        │       │       │       │
 OHLCV    因子面板   标准化    IC/IR   组合因子  收益    指标
 财务数据  截面数据   中性化    分组    权重     风险    评级
```

## 2. 文件组织

### 2.1 因子计算模块

```
factors/
├── __init__.py           # 导出所有因子类
├── technical.py          # 技术因子类
│   ├── momentum()        # 动量因子
│   ├── realized_volatility()  # 波动率
│   ├── turnover_rate()   # 换手率
│   ├── rsi()             # RSI 指标
│   ├── macd()            # MACD 指标
│   └── compute_all()     # 批量计算
├── fundamental.py        # 基本面因子类
│   ├── earnings_yield()  # 盈利收益率
│   ├── book_to_price()   # 账面市值比
│   ├── roe_factor()      # ROE 因子
│   ├── growth_score()    # 成长因子
│   └── compute_all()     # 批量计算
├── alternative.py        # 另类因子类
│   ├── smart_money_flow() # 聪明资金
│   ├── reversal_factor()  # 短期反转
│   ├── skewness_factor()  # 偏度因子
│   └── compute_all()     # 批量计算
└── combinator.py         # 因子组合类
    ├── equal_weight()    # 等权组合
    ├── ic_weight()       # IC 加权
    └── max_ic_ir_combination()  # 最大化 IR
```

### 2.2 评估模块

```
evaluation/
├── __init__.py
├── ic_analysis.py        # IC 分析
│   ├── rank_ic()         # 单期 Rank IC
│   ├── pearson_ic()      # 单期 Pearson IC
│   ├── compute_ic_series()    # IC 时间序列
│   ├── compute_ic_summary()   # IC 统计摘要
│   └── ic_decay()        # IC 衰减
├── ir_analysis.py        # IR 分析
│   ├── compute_ir()      # IR 计算
│   ├── rolling_ir()      # 滚动 IR
│   └── multi_factor_ir_comparison()  # 多因子对比
├── group_backtest.py     # 分组回测
│   ├── assign_groups()   # 分组
│   ├── run()             # 执行回测
│   └── _compute_group_stats()  # 统计指标
└── decay_analysis.py     # 衰减分析
    ├── ic_decay_by_horizon()  # 不同持仓期 IC
    ├── estimate_half_life()   # 半衰期估计
    └── factor_persistence_score()  # 持续性评分
```

## 3. 示例设计

### 3.1 基础因子计算

```python
# 场景: 计算 A 股市场的动量因子
from src.factors.technical import TechnicalFactors

tf = TechnicalFactors()

# 为每只股票计算因子
factors = {}
for stock in stock_list:
    stock_data = get_price_data(stock)  # 获取 OHLCV
    factors[stock] = tf.momentum(stock_data["close"], window=20)

# 构造因子面板
factor_panel = pd.DataFrame(factors)
```

### 3.2 因子评估流程

```python
# 场景: 评估动量因子的有效性
from src.evaluation.ic_analysis import ICAnalysis
from src.evaluation.group_backtest import GroupBacktest

# IC 分析
ic_analyzer = ICAnalysis()
ic_summary = ic_analyzer.compute_ic_summary(factor_panel, return_panel)

# 判断因子是否有效
if ic_summary["ic_ir"] > 0.3:
    print("因子有效，IR 足够高")

# 分组回测
group_bt = GroupBacktest(n_groups=5)
result = group_bt.run(factor_panel, return_panel)

# 检查单调性
if result["monotonicity"] > 0.7:
    print("分组收益单调性好")
```

### 3.3 完整因子研究流程

```python
# 场景: 完整的因子研究流程
from src.factors.technical import TechnicalFactors
from src.optimization.standardizer import FactorStandardizer
from src.optimization.winsorizer import FactorWinsorizer
from src.evaluation.ic_analysis import ICAnalysis
from src.combination.equal_weight import EqualWeightCombination
from src.backtest.portfolio_backtest import PortfolioBacktest

# 1. 计算多个因子
tf = TechnicalFactors()
momentum = tf.compute_all(price_data, windows=[5, 20])

# 2. 预处理
winsorizer = FactorWinsorizer()
standardizer = FactorStandardizer()
clean_factor = winsorizer.mad_winsorize(factor)
normalized = standardizer.zscore(clean_factor)

# 3. 评估
ic_summary = ICAnalysis.compute_ic_summary(factor_panel, return_panel)

# 4. 组合
combined = EqualWeightCombination.combine(factor_df)

# 5. 回测
bt = PortfolioBacktest(top_n=50)
result = bt.run(combined_panel, return_panel)
```

## 4. 接口设计

### 4.1 因子计算接口

所有因子计算函数遵循统一接口:
- 输入: pd.Series 或 pd.DataFrame
- 输出: pd.Series (因子值)
- 参数: 包含窗口、阈值等可调参数

### 4.2 因子面板格式

因子面板统一使用以下格式:
- index: 日期 (pd.DatetimeIndex)
- columns: 股票代码 (str)
- values: 因子值 (float)

### 4.3 回测结果格式

回测结果统一使用字典格式:
```python
{
    "portfolio_returns": pd.Series,     # 每日收益率
    "cumulative": pd.Series,            # 累计收益
    "metrics": Dict[str, float],        # 性能指标
    "holdings": List[Dict],             # 持仓记录
}
```
