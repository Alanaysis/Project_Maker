# 因子挖掘框架 (Factor Mining Framework)

从零实现量化因子挖掘全流程框架，涵盖因子计算、评估、优化、组合和回测，深入理解多因子选股的核心技术体系。

## 学习目标

- **理解因子挖掘原理**：掌握技术因子、基本面因子、另类因子的计算方法
- **掌握因子评估方法**：学会 IC/IR 分析、分组回测、因子衰减分析
- **学会因子优化技术**：理解中性化、标准化、去极值的工程实践
- **掌握因子组合策略**：从等权组合到机器学习组合的演进

## 核心流程

```
数据输入 → 因子计算 → 因子评估 → 因子优化 → 因子组合 → 组合回测
   ↓          ↓          ↓          ↓          ↓          ↓
  OHLCV    技术/基本面  IC/IR分析  中性化/标准化  等权/ML    收益/风险
  财务数据  另类因子    分组回测    去极值/补全    最优化     性能分析
```

## 项目结构

```
factor-mining/
├── README.md                        # 项目说明
├── LEARNING_NOTES.md                # 学习笔记
├── requirements.txt                 # 依赖包
├── docs/
│   ├── 01-RESEARCH.md              # 市场调研
│   ├── 02-REQUIREMENTS.md          # 需求分析
│   ├── 03-DESIGN.md                # 技术设计
│   ├── 04-PRODUCT.md               # 产品思考
│   └── 05-DEVELOPMENT.md           # 开发手册
├── src/
│   ├── __init__.py
│   ├── factors/                    # 因子计算
│   │   ├── __init__.py
│   │   ├── technical.py            # 技术因子 (动量/波动率/流动性)
│   │   ├── fundamental.py          # 基本面因子 (估值/盈利/成长)
│   │   ├── alternative.py          # 另类因子 (资金流/情绪/微观结构)
│   │   └── combinator.py           # 因子组合 (等权/IC加权/最优化)
│   ├── evaluation/                 # 因子评估
│   │   ├── __init__.py
│   │   ├── ic_analysis.py          # IC 分析
│   │   ├── ir_analysis.py          # IR 分析
│   │   ├── group_backtest.py       # 分组回测
│   │   └── decay_analysis.py       # 因子衰减
│   ├── optimization/               # 因子优化
│   │   ├── __init__.py
│   │   ├── neutralizer.py          # 因子中性化
│   │   ├── standardizer.py         # 因子标准化
│   │   ├── winsorizer.py           # 因子去极值
│   │   └── filler.py               # 因子补全
│   ├── combination/                # 因子组合
│   │   ├── __init__.py
│   │   ├── equal_weight.py         # 等权组合
│   │   ├── ic_weight.py            # IC 加权
│   │   ├── optimized.py            # 最优化组合
│   │   └── ml_combination.py       # 机器学习组合
│   ├── backtest/                   # 回测系统
│   │   ├── __init__.py
│   │   ├── data_replay.py          # 数据回放
│   │   ├── factor_backtest.py      # 因子回测
│   │   ├── portfolio_backtest.py   # 组合回测
│   │   └── performance.py          # 性能分析
│   └── app/                        # 实际应用
│       ├── __init__.py
│       ├── factor_library.py       # 因子库管理
│       ├── factor_monitor.py       # 因子监控
│       ├── factor_updater.py       # 因子更新
│       └── factor_report.py        # 因子报告
├── tests/
│   ├── __init__.py
│   ├── test_technical.py           # 技术因子测试
│   ├── test_evaluation.py          # 评估模块测试
│   ├── test_optimization.py        # 优化模块测试
│   ├── test_combination.py         # 组合模块测试
│   └── test_backtest.py            # 回测模块测试
└── examples/
    ├── basic_usage.py              # 基础用法示例
    └── advanced_usage.py           # 高级用法示例
```

## 快速开始

### 安装依赖

```bash
cd projects/factor-mining
pip install -r requirements.txt
```

### 基础使用

```python
from src.factors.technical import TechnicalFactors
from src.evaluation.ic_analysis import ICAnalysis
from src.optimization.standardizer import FactorStandardizer
from src.combination.equal_weight import EqualWeightCombination
from src.backtest.portfolio_backtest import PortfolioBacktest

# 1. 计算技术因子
tf = TechnicalFactors()
factors = tf.compute_all(price_data, windows=[5, 20])

# 2. 因子标准化
standardizer = FactorStandardizer()
normalized = standardizer.standardize_panel(factor_panel, method="zscore")

# 3. IC 分析
ic_analyzer = ICAnalysis()
ic_summary = ic_analyzer.compute_ic_summary(factor_panel, return_panel)
print(f"IC 均值: {ic_summary['ic_mean']:.4f}")
print(f"IC_IR: {ic_summary['ic_ir']:.4f}")

# 4. 组合回测
bt = PortfolioBacktest(top_n=50, rebalance_freq=20)
result = bt.run(factor_panel, return_panel)
```

### 运行示例

```bash
# 基础示例
python examples/basic_usage.py

# 高级示例
python examples/advanced_usage.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 因子分类

### 技术因子 (基于量价数据)

| 因子 | 类型 | 说明 | 典型窗口 |
|------|------|------|----------|
| 动量 | 趋势 | 过去 N 日收益率 | 5/10/20/60 |
| 波动率 | 风险 | 已实现波动率 | 20/60 |
| 换手率 | 流动性 | 平均换手率 | 20 |
| RSI | 技术指标 | 相对强弱指标 | 14 |
| MACD | 趋势 | 移动平均收敛/发散 | 12/26/9 |

### 基本面因子 (基于财务数据)

| 因子 | 类型 | 说明 |
|------|------|------|
| EP | 估值 | 盈利收益率 (1/PE) |
| BP | 估值 | 账面市值比 (1/PB) |
| ROE | 盈利 | 净资产收益率 |
| 营收增长 | 成长 | 营收同比增长率 |
| 杠杆 | 安全 | 资产负债率 |

### 另类因子 (基于行为/微观结构)

| 因子 | 类型 | 说明 |
|------|------|------|
| 聪明资金 | 资金流向 | 大单净流入比例 |
| 短期反转 | 行为 | 近期收益负值 |
| 偏度 | 行为 | 收益率分布偏度 |
| 换手率异常 | 微观结构 | 换手率偏离程度 |

## 因子评估指标

| 指标 | 含义 | 优秀标准 |
|------|------|----------|
| IC 均值 | 因子预测能力 | > 0.05 |
| IC_IR | 预测稳定性 | > 0.5 |
| 单调性 | 分组收益单调程度 | > 0.8 |
| 半衰期 | IC 衰减速度 | > 10 天 |
| 多空收益 | 高低组收益差 | > 5% 年化 |

## 学习路径

```
因子概念 → 技术因子 → 因子评估 → 因子优化 → 因子组合 → 回测系统
   ↓          ↓          ↓          ↓          ↓          ↓
 什么是因子  计算方法   IC/IR分析  中性化处理  等权组合   历史回放
 因子分类    动量/波动   分组回测   标准化     IC加权    组合回测
 因子经济学  基本面     衰减分析   去极值     最优化    性能分析
```

## 技术栈

- **Python 3.8+**: 核心语言
- **NumPy**: 数值计算
- **Pandas**: 数据处理
- **SciPy**: 统计分析
- **scikit-learn**: 机器学习
- **Matplotlib/Seaborn**: 可视化
- **statsmodels**: 统计建模
