# 量化交易系统 (Quantitative Trading System)

## 项目简介

从零实现一个量化交易系统，支持策略回测、实盘交易模拟、风险管理。通过本项目深入理解量化交易的核心原理和工程实践。

## 学习目标

- 理解量化交易策略的设计与实现
- 掌握回测框架的事件驱动架构
- 学会风险管理和订单管理的工程实现
- 理解数据管道和信号处理流程

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Python 3.10+ | 主语言 | ⭐⭐ |
| pandas | 数据处理 | ⭐⭐ |
| numpy | 数值计算 | ⭐⭐ |
| matplotlib | 可视化 | ⭐⭐ |
| pytest | 单元测试 | ⭐ |

## 核心架构

```
数据获取 → 策略计算 → 信号生成 → 订单执行 → 风险检查 → 成交确认
```

### 事件驱动架构

```
┌─────────────┐
│  DataEngine  │ ──→ MarketDataEvent
└─────────────┘
        ↓
┌─────────────┐
│  Strategy    │ ──→ SignalEvent
└─────────────┘
        ↓
┌─────────────┐
│ RiskManager  │ ──→ OrderEvent (通过/拒绝)
└─────────────┘
        ↓
┌─────────────┐
│ OrderManager│ ──→ FillEvent
└─────────────┘
        ↓
┌─────────────┐
│ Portfolio    │ ──→ 持仓更新
└─────────────┘
```

## 重点难点

### ⭐ 事件驱动架构
- 理解事件循环和事件类型
- 解耦各模块，实现可扩展性
- 处理事件的时序和优先级

### ⭐ 回测引擎设计
- 历史数据的时间序列处理
- 模拟成交和滑点
- 资金曲线计算

### ⭐ 风险管理
- 仓位控制算法
- 止损止盈策略
- 最大回撤控制

## 值得思考

- 💡 为什么选择事件驱动而非向量化回测？
- 💡 如何平衡回测速度和模拟精度？
- 💡 实盘和回测的代码如何最大程度复用？
- 💡 如何设计可扩展的策略接口？

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行回测示例
python examples/run_backtest.py

# 运行测试
pytest tests/ -v
```

## 项目结构

```
quant-trading-system/
├── src/
│   ├── core/
│   │   ├── engine.py          # 回测引擎
│   │   ├── events.py          # 事件系统
│   │   └── portfolio.py       # 投资组合管理
│   ├── strategies/
│   │   ├── base.py            # 策略基类
│   │   ├── moving_average.py  # 均线策略
│   │   └── momentum.py        # 动量策略
│   ├── data/
│   │   ├── loader.py          # 数据加载器
│   │   └── generator.py       # 模拟数据生成
│   ├── risk/
│   │   ├── manager.py         # 风险管理器
│   │   └── rules.py           # 风险规则
│   └── utils/
│       └── logger.py          # 日志工具
├── tests/
├── examples/
├── docs/
└── requirements.txt
```

## 参考资源

- [Backtrader](https://github.com/mementum/backtrader) - 成熟的回测框架
- [Zipline](https://github.com/quantopian/zipline) - 事件驱动回测
- [vnpy](https://github.com/vnpy/vnpy) - 中国量化交易平台
- [QuantConnect Lean](https://github.com/QuantConnect/Lean) - 云端量化引擎
- [VectorBT](https://github.com/polakowo/vectorbt) - 向量化回测

## License

MIT
