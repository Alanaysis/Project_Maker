# 开发手册

## 1. 环境搭建

### 1.1 系统要求

- Python 3.10+
- pip 或 conda
- Git（可选）

### 1.2 安装步骤

```bash
# 克隆项目（如果使用 Git）
git clone <repository-url>
cd quant-trading-system

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 验证安装

```bash
# 运行测试
pytest tests/ -v

# 运行示例
python examples/run_backtest.py
```

---

## 2. 项目结构详解

```
quant-trading-system/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── core/                     # 核心模块
│   │   ├── __init__.py
│   │   ├── events.py            # 事件系统
│   │   ├── engine.py            # 回测引擎
│   │   └── portfolio.py         # 投资组合管理
│   ├── strategies/               # 策略模块
│   │   ├── __init__.py
│   │   ├── base.py              # 策略基类
│   │   ├── moving_average.py    # 均线策略
│   │   └── momentum.py          # 动量策略
│   ├── data/                     # 数据模块
│   │   ├── __init__.py
│   │   ├── loader.py            # 数据加载器
│   │   └── generator.py         # 数据生成器
│   ├── risk/                     # 风险模块
│   │   ├── __init__.py
│   │   ├── manager.py           # 风险管理器
│   │   └── rules.py             # 风险规则
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       └── logger.py            # 日志工具
├── tests/                        # 测试目录
│   ├── __init__.py
│   ├── test_events.py           # 事件系统测试
│   ├── test_portfolio.py        # 投资组合测试
│   ├── test_strategies.py       # 策略测试
│   ├── test_risk.py             # 风险管理测试
│   └── test_engine.py           # 回测引擎测试
├── examples/                     # 示例目录
│   └── run_backtest.py          # 回测示例
├── docs/                         # 文档目录
│   ├── 01-RESEARCH.md           # 市场调研
│   ├── 02-REQUIREMENTS.md       # 需求分析
│   ├── 03-DESIGN.md             # 技术设计
│   ├── 04-PRODUCT.md            # 产品思维
│   └── 05-DEVELOPMENT.md        # 开发手册
├── README.md                     # 项目说明
├── requirements.txt              # 依赖列表
└── LEARNING_NOTES.md             # 学习笔记模板
```

---

## 3. 核心模块解析

### 3.1 事件系统 (events.py)

**作用**：实现事件驱动架构的核心

**核心类**：
- `EventBus`：事件总线，负责事件的发布和订阅
- `Event`：事件基类
- `MarketDataEvent`：市场数据事件
- `SignalEvent`：交易信号事件
- `OrderEvent`：订单事件
- `FillEvent`：成交事件

**设计要点**：
- 发布-订阅模式
- 支持多个处理器
- 同步处理事件

**代码示例**：
```python
from src.core.events import EventBus, EventType, MarketDataEvent

# 创建事件总线
bus = EventBus()

# 定义处理器
def handle_market_data(event):
    print(f"Received: {event.symbol} @ {event.close}")

# 订阅事件
bus.subscribe(EventType.MARKET_DATA, handle_market_data)

# 发布事件
event = MarketDataEvent(symbol="AAPL", close=150.0)
bus.publish(event)

# 处理事件
bus.process_events()
```

---

### 3.2 回测引擎 (engine.py)

**作用**：协调所有模块，执行回测

**核心方法**：
- `add_strategy()`：添加策略
- `load_data()`：加载数据
- `run()`：运行回测

**回测流程**：
1. 初始化策略
2. 按时间顺序推送数据
3. 处理事件
4. 记录权益曲线
5. 计算回测结果

**代码示例**：
```python
from src.core.engine import BacktestEngine
from src.strategies.moving_average import MovingAverageStrategy
from src.data.generator import DataGenerator

# 创建引擎
engine = BacktestEngine(initial_capital=100000.0)

# 生成数据
generator = DataGenerator(seed=42)
data = generator.generate_gbm(symbol="AAPL", days=252)

# 加载数据
engine.load_data(data, "AAPL")

# 创建策略
strategy = MovingAverageStrategy(symbols=["AAPL"])

# 添加策略
engine.add_strategy(strategy)

# 运行回测
results = engine.run()
```

---

### 3.3 策略基类 (base.py)

**作用**：定义策略的标准接口

**核心方法**：
- `on_init()`：策略初始化
- `on_market_data()`：处理市场数据
- `generate_signal()`：生成交易信号

**策略生命周期**：
```
__init__ → on_init → on_market_data (多次) → on_shutdown
```

**代码示例**：
```python
from src.strategies.base import Strategy
from src.core.events import MarketDataEvent, SignalEvent

class MyStrategy(Strategy):
    def on_init(self):
        # 初始化逻辑
        pass

    def on_market_data(self, event: MarketDataEvent):
        # 交易逻辑
        if event.close > 100:
            return self.generate_signal(
                symbol=event.symbol,
                direction="BUY",
                strength=0.8
            )
        return None
```

---

### 3.4 均线策略 (moving_average.py)

**作用**：实现均线交叉策略

**策略逻辑**：
- 短期均线上穿长期均线 → 金叉 → 买入
- 短期均线下穿长期均线 → 死叉 → 卖出

**参数**：
- `short_window`：短期均线周期
- `long_window`：长期均线周期

**代码示例**：
```python
from src.strategies.moving_average import MovingAverageStrategy

strategy = MovingAverageStrategy(
    name="MA_Cross",
    symbols=["AAPL"],
    short_window=10,
    long_window=30
)
```

---

### 3.5 动量策略 (momentum.py)

**作用**：实现动量策略

**策略逻辑**：
- 计算价格动量
- 动量超过阈值 → 买入
- 动量低于阈值 → 卖出

**参数**：
- `lookback`：回看周期
- `threshold`：动量阈值

**代码示例**：
```python
from src.strategies.momentum import MomentumStrategy

strategy = MomentumStrategy(
    name="Momentum",
    symbols=["AAPL"],
    lookback=10,
    threshold=0.05
)
```

---

### 3.6 数据生成器 (generator.py)

**作用**：生成模拟市场数据

**核心方法**：
- `generate_gbm()`：生成几何布朗运动数据
- `generate_multi_symbols()`：生成多标的相关数据
- `generate_trending_data()`：生成趋势数据

**代码示例**：
```python
from src.data.generator import DataGenerator

generator = DataGenerator(seed=42)

# 生成单标的数据
data = generator.generate_gbm(
    symbol="AAPL",
    start_price=100.0,
    days=252,
    mu=0.1,
    sigma=0.2
)

# 生成多标的数据
data = generator.generate_multi_symbols(
    symbols=["AAPL", "GOOG", "MSFT"],
    days=252,
    correlation=0.5
)
```

---

### 3.7 风险管理器 (manager.py)

**作用**：管理风险规则，检查订单

**核心方法**：
- `check_order()`：检查订单是否符合规则
- `add_rule()`：添加风险规则

**内置规则**：
- `MaxPositionRule`：最大仓位限制
- `MaxOrderSizeRule`：最大订单规模
- `StopLossRule`：止损规则
- `MaxDrawdownRule`：最大回撤限制
- `CashReserveRule`：现金储备要求

**代码示例**：
```python
from src.risk.manager import RiskManager
from src.risk.rules import MaxPositionRule

manager = RiskManager()

# 添加自定义规则
manager.add_rule(MaxPositionRule(max_position_pct=0.2))

# 检查订单
passed, reason = manager.check_order(order, portfolio)
```

---

### 3.8 投资组合 (portfolio.py)

**作用**：管理持仓和资金

**核心功能**：
- 持仓跟踪
- 资金管理
- 盈亏计算
- 交易记录

**核心指标**：
- 总资产
- 总盈亏
- 收益率
- 最大回撤

**代码示例**：
```python
from src.core.portfolio import Portfolio

portfolio = Portfolio(initial_capital=100000.0)

# 获取总资产
total_equity = portfolio.total_equity

# 获取收益率
returns = portfolio.returns

# 获取摘要
summary = portfolio.get_summary()
```

---

## 4. 开发指南

### 4.1 添加新策略

**步骤**：
1. 创建策略文件 `src/strategies/my_strategy.py`
2. 继承 `Strategy` 基类
3. 实现 `on_init()` 和 `on_market_data()` 方法
4. 编写测试 `tests/test_my_strategy.py`
5. 更新文档

**模板**：
```python
from src.strategies.base import Strategy
from src.core.events import MarketDataEvent, SignalEvent

class MyStrategy(Strategy):
    def __init__(self, name="MyStrategy", symbols=None, params=None):
        super().__init__(name, symbols or [], params)

    def on_init(self):
        self.is_initialized = True

    def on_market_data(self, event: MarketDataEvent):
        # 交易逻辑
        return self.generate_signal(
            symbol=event.symbol,
            direction="BUY",
            strength=0.8
        )
```

---

### 4.2 添加新风险规则

**步骤**：
1. 创建规则文件 `src/risk/my_rule.py`
2. 继承 `RiskRule` 基类
3. 实现 `check_order()` 方法
4. 编写测试
5. 更新文档

**模板**：
```python
from src.risk.rules import RiskRule

class MyRiskRule(RiskRule):
    def __init__(self, param=0.1):
        self.param = param

    def check_order(self, order, portfolio):
        # 风险检查逻辑
        passed = True
        reason = ""
        return passed, reason
```

---

### 4.3 添加新数据源

**步骤**：
1. 创建数据加载器 `src/data/my_loader.py`
2. 继承 `DataLoader` 类
3. 实现数据加载方法
4. 编写测试
5. 更新文档

---

## 5. 测试指南

### 5.1 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_events.py

# 运行并显示详细输出
pytest tests/ -v

# 运行并显示覆盖率
pytest tests/ --cov=src
```

### 5.2 编写测试

**测试文件命名**：`test_<module>.py`

**测试类命名**：`Test<ClassName>`

**测试方法命名**：`test_<function_name>`

**示例**：
```python
import pytest
from src.core.events import EventBus, EventType, MarketDataEvent

class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventType.MARKET_DATA, handler)
        bus.publish(MarketDataEvent())
        bus.process_events()

        assert len(received) == 1
```

---

## 6. 调试指南

### 6.1 日志查看

```python
from src.utils.logger import logger

logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
logger.debug("调试日志")
```

### 6.2 常见问题

**问题 1：策略不产生信号**
- 检查数据是否足够
- 检查策略参数是否合理
- 检查信号生成逻辑

**问题 2：回测结果异常**
- 检查数据质量
- 检查交易成本设置
- 检查风险管理规则

**问题 3：性能问题**
- 减少数据量
- 优化计算逻辑
- 使用向量化操作

---

## 7. 部署指南

### 7.1 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 运行回测
python examples/run_backtest.py
```

### 7.2 Docker 部署（可选）

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "examples/run_backtest.py"]
```

---

## 8. 贡献指南

### 8.1 代码规范

- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 保持代码简洁

### 8.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

### 8.3 Pull Request 流程

1. Fork 项目
2. 创建特性分支
3. 提交代码
4. 编写测试
5. 更新文档
6. 提交 PR

---

## 9. 学习资源

### 9.1 量化交易

- 《Python 量化投资》
- 《算法交易：制胜策略与原理》
- 聚宽学院

### 9.2 Python 编程

- Python 官方文档
- Real Python
- Python Cookbook

### 9.3 金融知识

- Investopedia
- 东方财富
- 同花顺

---

## 10. 常见问题

### 10.1 如何选择策略参数？

**建议**：
- 从默认参数开始
- 通过回测优化
- 避免过拟合

### 10.2 如何评估策略好坏？

**指标**：
- 总收益率
- 最大回撤
- 夏普比率
- 胜率

### 10.3 如何避免过拟合？

**方法**：
- 使用样本外数据测试
- 简化策略逻辑
- 使用交叉验证

### 10.4 如何实盘交易？

**步骤**：
1. 选择券商接口
2. 实现实盘适配器
3. 测试模拟交易
4. 小资金试运行
5. 逐步扩大规模
