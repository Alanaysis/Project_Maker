# 因子挖掘框架 (Factor Mining Framework)

一个用于学习量化因子计算和回测的 Python 框架。

## 项目简介

本项目实现了一个完整的因子挖掘框架，支持:
- **常用因子计算**: 动量、波动率、流动性、技术指标等
- **因子 IC 分析**: Rank IC、ICIR、分组收益
- **回测框架**: 多空策略、纯多头策略、交易成本

## 核心循环

```
数据 → 因子计算 → 因子评估 → 组合优化 → 回测
```

## 项目结构

```
factor-mining/
├── src/
│   ├── data.py           # 数据生成与加载
│   ├── factors.py        # 因子计算 (13种因子)
│   ├── evaluation.py     # 因子评估 (IC、分组收益)
│   └── backtest.py       # 回测框架
├── tests/                # 单元测试
├── examples/             # 使用示例
├── docs/                 # 详细文档
├── README.md
└── requirements.txt
```

## 快速开始

```python
from src.data import generate_stock_data
from src.factors import FactorCalculator
from src.evaluation import FactorEvaluator
from src.backtest import BacktestEngine, BacktestConfig

# 1. 生成模拟数据
data = generate_stock_data(n_stocks=50, n_days=500)

# 2. 计算因子
calc = FactorCalculator(price=data['price'], volume=data['volume'])
momentum = calc.momentum(window=20)
volatility = calc.volatility(window=20)

# 3. 因子评估
evaluator = FactorEvaluator(momentum, data['returns'].shift(-1))
print(evaluator.ic_summary())
print(evaluator.performance_summary())

# 4. 回测
config = BacktestConfig(n_groups=5, transaction_cost=0.001)
engine = BacktestEngine(momentum, data['returns'], config)
result = engine.run()
print(result.summary())
```

## 支持的因子

| 类别 | 因子 | 方法 |
|------|------|------|
| 动量 | 动量 | `momentum(window)` |
| 动量 | 短期反转 | `short_term_reversal(window)` |
| 动量 | 加权动量 | `weighted_momentum(window)` |
| 波动率 | 波动率 | `volatility(window)` |
| 波动率 | 下行波动率 | `downside_volatility(window)` |
| 波动率 | ATR | `atr(window)` |
| 流动性 | Amihud非流动性 | `amihud_illiquidity(window)` |
| 流动性 | 成交量动量 | `volume_momentum(window)` |
| 技术 | RSI | `rsi(window)` |
| 技术 | 布林带宽度 | `bollinger_width(window)` |
| 技术 | 价格/均线比 | `price_to_ma(window)` |

## 评估指标

- **IC**: 因子与未来收益的截面秩相关系数
- **ICIR**: IC均值/IC标准差, 衡量因子稳定性
- **分组收益**: 按因子值分组, 计算各组平均收益
- **多空收益**: 最高组 - 最低组的收益差

## 运行测试

```bash
cd projects/factor-mining
python -m pytest tests/ -v
```

## 运行示例

```bash
python examples/basic_factor_analysis.py
python examples/backtest_example.py
```

## 文档

- [研究背景](docs/01-RESEARCH.md)
- [系统设计](docs/02-DESIGN.md)
- [实现细节](docs/03-IMPLEMENTATION.md)
- [测试文档](docs/04-TESTING.md)
- [开发指南](docs/05-DEVELOPMENT.md)
