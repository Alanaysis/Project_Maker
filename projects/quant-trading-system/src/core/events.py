"""
事件系统 - 量化交易系统的核心事件驱动架构

⭐ 重点理解：事件驱动模式是量化交易系统的基础架构模式。
所有模块通过事件进行通信，实现松耦合。

💡 值得思考：为什么不用直接函数调用？
- 事件驱动允许模块独立演化
- 便于扩展新的事件类型
- 支持异步处理和事件回放
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict


class EventType(Enum):
    """事件类型枚举"""
    MARKET_DATA = auto()      # 市场数据事件
    SIGNAL = auto()           # 交易信号事件
    ORDER = auto()            # 订单事件
    FILL = auto()             # 成交事件
    RISK_CHECK = auto()       # 风险检查事件
    POSITION_UPDATE = auto()  # 持仓更新事件
    LOG = auto()              # 日志事件


@dataclass
class Event:
    """事件基类"""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Any = None


@dataclass
class MarketDataEvent(Event):
    """
    市场数据事件

    💡 值得思考：为什么将 OHLCV 数据封装为事件？
    - 统一数据格式，便于策略处理
    - 支持不同频率的数据（tick/分钟/日线）
    - 便于记录和回放
    """
    event_type: EventType = EventType.MARKET_DATA
    symbol: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


@dataclass
class SignalEvent(Event):
    """
    交易信号事件

    ⭐ 重点：信号是策略的输出，订单的输入
    信号包含方向（买/卖）和强度，但不包含具体数量
    """
    event_type: EventType = EventType.SIGNAL
    symbol: str = ""
    direction: str = ""  # "BUY" or "SELL"
    strength: float = 0.0  # 信号强度 [-1, 1]
    strategy_name: str = ""


@dataclass
class OrderEvent(Event):
    """
    订单事件

    ⭐ 重点：订单类型和状态管理
    - MARKET: 市价单，以当前价格立即成交
    - LIMIT: 限价单，达到指定价格才成交
    """
    event_type: EventType = EventType.ORDER
    symbol: str = ""
    direction: str = ""  # "BUY" or "SELL"
    order_type: str = "MARKET"  # "MARKET" or "LIMIT"
    quantity: int = 0
    price: float = 0.0
    order_id: str = ""
    status: str = "PENDING"  # PENDING, SUBMITTED, FILLED, CANCELLED, REJECTED


@dataclass
class FillEvent(Event):
    """
    成交事件

    💡 值得思考：成交价格和订单价格可能不同
    - 滑点：实际成交价与预期价格的偏差
    - 手续费：交易成本
    """
    event_type: EventType = EventType.FILL
    symbol: str = ""
    direction: str = ""
    quantity: int = 0
    fill_price: float = 0.0
    commission: float = 0.0
    order_id: str = ""


@dataclass
class RiskCheckEvent(Event):
    """
    风险检查事件

    ⭐ 重点：风险检查在订单执行前进行
    包含检查结果和拒绝原因
    """
    event_type: EventType = EventType.RISK_CHECK
    order_id: str = ""
    passed: bool = True
    reason: str = ""


class EventBus:
    """
    事件总线 - 事件驱动架构的核心

    ⭐ 重点理解：事件总线是发布-订阅模式的实现
    - 发布者不需要知道订阅者
    - 订阅者可以动态注册和注销
    - 支持事件过滤和优先级

    💡 值得思考：事件总线的性能瓶颈在哪里？
    - 大量事件时的内存管理
    - 事件处理的顺序保证
    - 异常处理和错误传播
    """

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_queue: List[Event] = []

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """订阅事件"""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """取消订阅"""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def publish(self, event: Event) -> None:
        """
        发布事件

        💡 值得思考：同步 vs 异步发布？
        - 同步：简单，但可能阻塞
        - 异步：性能好，但调试困难
        """
        self._event_queue.append(event)

    def process_events(self) -> None:
        """处理所有待处理事件"""
        while self._event_queue:
            event = self._event_queue.pop(0)
            self._dispatch(event)

    def _dispatch(self, event: Event) -> None:
        """分发事件给订阅者"""
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error handling event {event.event_type}: {e}")

    @property
    def pending_count(self) -> int:
        """待处理事件数量"""
        return len(self._event_queue)
