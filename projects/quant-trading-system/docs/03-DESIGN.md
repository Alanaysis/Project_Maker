# 技术设计

## 1. 架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Backtest Engine                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Data     │  │ Strategy │  │   Risk   │  │ Portfolio │  │
│  │  Engine   │  │  Engine  │  │ Manager  │  │  Manager  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                          │                                  │
│                    Event Bus                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| BacktestEngine | 协调所有模块 | 所有模块 |
| DataEngine | 数据加载和管理 | 无 |
| StrategyEngine | 策略执行 | Event Bus |
| RiskManager | 风险检查 | Portfolio |
| PortfolioManager | 持仓和资金管理 | 无 |
| Event Bus | 事件分发 | 无 |

---

## 2. 核心设计

### 2.1 事件驱动架构

#### 2.1.1 事件类型

```python
class EventType(Enum):
    MARKET_DATA = auto()      # 市场数据
    SIGNAL = auto()           # 交易信号
    ORDER = auto()            # 订单
    FILL = auto()             # 成交
    RISK_CHECK = auto()       # 风险检查
    POSITION_UPDATE = auto()  # 持仓更新
```

#### 2.1.2 事件流程

```
MarketData → Strategy → Signal → RiskCheck → Order → Fill → Portfolio
```

#### 2.1.3 事件总线设计

```python
class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_queue: List[Event] = []

    def subscribe(self, event_type: EventType, handler: Callable) -> None
    def publish(self, event: Event) -> None
    def process_events(self) -> None
```

**设计要点**：
- 发布-订阅模式
- 支持多个处理器
- 同步处理（可扩展为异步）

---

### 2.2 策略抽象

#### 2.2.1 策略接口

```python
class Strategy(ABC):
    @abstractmethod
    def on_init(self) -> None

    @abstractmethod
    def on_market_data(self, event: MarketDataEvent) -> Optional[SignalEvent]

    def generate_signal(self, symbol, direction, strength) -> SignalEvent
```

#### 2.2.2 策略生命周期

```
__init__ → on_init → on_market_data (多次) → on_shutdown
```

#### 2.2.3 策略参数

```python
class Strategy:
    def __init__(self, name: str, symbols: List[str], params: Dict = None):
        self.name = name
        self.symbols = symbols
        self.params = params or {}
```

---

### 2.3 数据结构

#### 2.3.1 市场数据

```python
@dataclass
class MarketDataEvent:
    event_type: EventType = EventType.MARKET_DATA
    symbol: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    timestamp: datetime = None
```

#### 2.3.2 交易信号

```python
@dataclass
class SignalEvent:
    event_type: EventType = EventType.SIGNAL
    symbol: str = ""
    direction: str = ""  # "BUY" or "SELL"
    strength: float = 0.0  # [-1, 1]
    strategy_name: str = ""
```

#### 2.3.3 订单

```python
@dataclass
class OrderEvent:
    event_type: EventType = EventType.ORDER
    symbol: str = ""
    direction: str = ""
    order_type: str = "MARKET"  # "MARKET" or "LIMIT"
    quantity: int = 0
    price: float = 0.0
    order_id: str = ""
    status: str = "PENDING"
```

#### 2.3.4 成交

```python
@dataclass
class FillEvent:
    event_type: EventType = EventType.FILL
    symbol: str = ""
    direction: str = ""
    quantity: int = 0
    fill_price: float = 0.0
    commission: float = 0.0
    order_id: str = ""
```

#### 2.3.5 持仓

```python
@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
```

---

### 2.4 风险管理设计

#### 2.4.1 风险规则接口

```python
class RiskRule(ABC):
    @abstractmethod
    def check_order(self, order: OrderEvent, portfolio: Dict) -> Tuple[bool, str]
```

#### 2.4.2 内置风险规则

| 规则 | 说明 | 参数 |
|------|------|------|
| MaxPositionRule | 最大仓位限制 | max_position_pct |
| MaxOrderSizeRule | 最大订单规模 | max_order_value |
| StopLossRule | 止损规则 | stop_loss_pct |
| MaxDrawdownRule | 最大回撤限制 | max_drawdown_pct |
| CashReserveRule | 现金储备要求 | min_cash_pct |

#### 2.4.3 风险管理器

```python
class RiskManager:
    def __init__(self):
        self._rules: List[RiskRule] = []

    def check_order(self, order, portfolio) -> Tuple[bool, str]
    def add_rule(self, rule: RiskRule) -> None
```

---

### 2.5 投资组合管理

#### 2.5.1 核心指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 总资产 | 现金 + 持仓市值 | 投资组合总价值 |
| 总盈亏 | 总资产 - 初始资金 | 绝对收益 |
| 收益率 | 总盈亏 / 初始资金 | 相对收益 |
| 最大回撤 | (峰值 - 谷值) / 峰值 | 最大亏损 |

#### 2.5.2 交易记录

```python
{
    "timestamp": datetime,
    "symbol": str,
    "direction": str,
    "quantity": int,
    "price": float,
    "commission": float,
    "pnl": float
}
```

---

## 3. 接口设计

### 3.1 回测引擎接口

```python
class BacktestEngine:
    def add_strategy(self, strategy: Strategy) -> None
    def load_data(self, data: pd.DataFrame, symbol: str) -> None
    def run(self) -> Dict
```

### 3.2 数据加载器接口

```python
class DataLoader:
    def load_csv(self, filepath: str, symbol: str = None) -> None
    def load_dataframe(self, df: pd.DataFrame, symbol: str) -> None
    def get_bar(self, symbol: str, index: int) -> Optional[Dict]
    def get_bars(self, symbol: str, start: int, end: int) -> List[Dict]
```

### 3.3 策略接口

```python
class Strategy(ABC):
    def on_init(self) -> None
    def on_market_data(self, event: MarketDataEvent) -> Optional[SignalEvent]
    def generate_signal(self, symbol, direction, strength) -> SignalEvent
```

---

## 4. 算法设计

### 4.1 均线计算

```python
def calculate_ma(prices: List[float], window: int) -> float:
    if len(prices) < window:
        return 0.0
    return sum(prices[-window:]) / window
```

### 4.2 动量计算

```python
def calculate_momentum(prices: List[float], lookback: int) -> float:
    if len(prices) < lookback + 1:
        return 0.0
    return (prices[-1] - prices[0]) / prices[0]
```

### 4.3 最大回撤计算

```python
def calculate_max_drawdown(equity_curve: List[float]) -> float:
    peak = equity_curve[0]
    max_dd = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        drawdown = (peak - equity) / peak
        max_dd = max(max_dd, drawdown)
    return max_dd
```

### 4.4 年化收益率计算

```python
def calculate_annualized_return(total_return: float, days: int) -> float:
    if days <= 0:
        return 0.0
    return (1 + total_return) ** (252 / days) - 1
```

---

## 5. 数据流设计

### 5.1 回测数据流

```
历史数据
    ↓
DataLoader
    ↓
BacktestEngine
    ↓
EventBus (MarketDataEvent)
    ↓
Strategy
    ↓
EventBus (SignalEvent)
    ↓
RiskManager
    ↓
EventBus (OrderEvent)
    ↓
OrderManager
    ↓
EventBus (FillEvent)
    ↓
Portfolio
    ↓
结果输出
```

### 5.2 事件处理顺序

1. 市场数据事件 → 更新价格 → 传递给策略
2. 信号事件 → 计算仓位 → 创建订单
3. 订单事件 → 风险检查 → 模拟成交
4. 成交事件 → 更新持仓 → 记录交易

---

## 6. 错误处理设计

### 6.1 异常类型

```python
class QuantError(Exception):
    """量化系统基础异常"""
    pass

class DataError(QuantError):
    """数据相关异常"""
    pass

class StrategyError(QuantError):
    """策略相关异常"""
    pass

class RiskError(QuantError):
    """风险相关异常"""
    pass
```

### 6.2 错误处理策略

- 数据错误：记录警告，跳过该数据点
- 策略错误：记录错误，停止策略执行
- 风险错误：拒绝订单，记录风险事件

---

## 7. 性能设计

### 7.1 性能瓶颈

1. **数据处理**：大量数据的读取和转换
2. **事件处理**：事件队列的管理
3. **指标计算**：技术指标的实时计算

### 7.2 优化策略

1. **数据缓存**：缓存已加载的数据
2. **批量处理**：批量处理事件
3. **向量化计算**：使用 numpy 进行计算

---

## 8. 扩展性设计

### 8.1 策略扩展

```python
class MyStrategy(Strategy):
    def on_init(self):
        # 初始化逻辑
        pass

    def on_market_data(self, event):
        # 交易逻辑
        signal = self.generate_signal(...)
        return signal
```

### 8.2 风险规则扩展

```python
class MyRiskRule(RiskRule):
    def check_order(self, order, portfolio):
        # 风险检查逻辑
        return passed, reason
```

### 8.3 数据源扩展

```python
class MyDataLoader(DataLoader):
    def load_from_api(self, api_url):
        # 从 API 加载数据
        pass
```

---

## 9. 测试设计

### 9.1 单元测试

- 事件系统测试
- 投资组合测试
- 策略测试
- 风险规则测试
- 回测引擎测试

### 9.2 集成测试

- 完整回测流程测试
- 多标的回测测试
- 风险管理集成测试

### 9.3 性能测试

- 大数据量回测测试
- 内存使用测试
- 响应时间测试

---

## 10. 部署设计

### 10.1 依赖管理

```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
pytest>=7.0.0
```

### 10.2 目录结构

```
quant-trading-system/
├── src/
│   ├── core/
│   ├── strategies/
│   ├── data/
│   ├── risk/
│   └── utils/
├── tests/
├── examples/
├── docs/
└── requirements.txt
```

### 10.3 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/run_backtest.py

# 运行测试
pytest tests/
```
