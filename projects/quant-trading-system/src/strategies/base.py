"""
策略基类 - 定义策略的标准接口

⭐ 重点理解：策略模式是量化交易的核心设计模式
- 所有策略继承基类，实现统一接口
- 策略只负责生成信号，不关心订单执行
- 策略通过事件系统与引擎通信

💡 值得思考：
- 策略参数如何优化？
- 如何避免过拟合？
- 多策略如何组合？
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from ..core.events import MarketDataEvent, SignalEvent, EventType


class Strategy(ABC):
    """
    策略基类

    ⭐ 重点：策略的生命周期
    1. __init__: 初始化参数
    2. on_init: 引擎初始化时调用
    3. on_market_data: 收到市场数据时调用
    4. on_signal: 信号处理（可选）
    5. on_shutdown: 引擎关闭时调用

    💡 值得思考：为什么策略不直接操作订单？
    - 解耦：策略专注于信号生成
    - 可测试：信号可以独立验证
    - 可组合：多个信号可以合并
    """

    def __init__(self, name: str, symbols: List[str], params: Dict = None):
        """
        初始化策略

        Args:
            name: 策略名称
            symbols: 交易标的列表
            params: 策略参数
        """
        self.name = name
        self.symbols = symbols
        self.params = params or {}
        self.is_initialized = False
        self._signals: List[SignalEvent] = []

    @abstractmethod
    def on_init(self) -> None:
        """
        策略初始化

        💡 值得思考：在初始化阶段应该做什么？
        - 加载历史数据
        - 计算初始指标
        - 设置参数默认值
        """
        pass

    @abstractmethod
    def on_market_data(self, event: MarketDataEvent) -> Optional[SignalEvent]:
        """
        处理市场数据，生成交易信号

        ⭐ 重点：这是策略的核心方法
        - 接收市场数据
        - 分析价格和指标
        - 决定是否生成信号

        Args:
            event: 市场数据事件

        Returns:
            SignalEvent or None: 交易信号
        """
        pass

    def on_bar(self, symbol: str, bar: Dict) -> Optional[SignalEvent]:
        """
        处理K线数据（便捷方法）

        💡 值得思考：bar 和 MarketDataEvent 的区别？
        - bar 是字典格式，便于快速开发
        - MarketDataEvent 是事件格式，便于事件驱动
        """
        event = MarketDataEvent(
            symbol=symbol,
            open=bar.get("open", 0),
            high=bar.get("high", 0),
            low=bar.get("low", 0),
            close=bar.get("close", 0),
            volume=bar.get("volume", 0)
        )
        return self.on_market_data(event)

    def generate_signal(self, symbol: str, direction: str,
                        strength: float = 1.0) -> SignalEvent:
        """
        生成交易信号

        Args:
            symbol: 交易标的
            direction: 买卖方向 "BUY" or "SELL"
            strength: 信号强度 [-1, 1]

        Returns:
            SignalEvent: 交易信号
        """
        signal = SignalEvent(
            symbol=symbol,
            direction=direction,
            strength=strength,
            strategy_name=self.name
        )
        self._signals.append(signal)
        return signal

    def get_signals(self) -> List[SignalEvent]:
        """获取所有生成的信号"""
        return self._signals.copy()

    def clear_signals(self) -> None:
        """清空信号列表"""
        self._signals.clear()

    def on_shutdown(self) -> None:
        """策略关闭时的清理工作"""
        pass

    def __repr__(self) -> str:
        return f"Strategy(name={self.name}, symbols={self.symbols})"
