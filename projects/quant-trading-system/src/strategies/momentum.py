"""
动量策略 - 基于价格动量的交易策略

⭐ 重点理解：动量策略的原理
- 价格上涨趋势会延续 → 追涨
- 价格下跌趋势会延续 → 杀跌

💡 值得思考：
- 动量 vs 均线策略的区别？
- 动量策略在什么市场环境下有效？
- 如何设置动量阈值？
"""

from typing import Dict, List, Optional
from collections import deque
import numpy as np

from .base import Strategy
from ..core.events import MarketDataEvent, SignalEvent


class MomentumStrategy(Strategy):
    """
    动量策略

    ⭐ 重点：动量策略的核心思想
    - 计算价格变化率（ROC）
    - 当动量超过阈值时产生信号
    - 结合成交量确认

    💡 值得思考：
    - 动量周期如何选择？
    - 如何处理动量反转？
    - 动量策略的风险是什么？
    """

    def __init__(
        self,
        name: str = "Momentum",
        symbols: List[str] = None,
        lookback: int = 10,
        threshold: float = 0.05,
        params: Dict = None
    ):
        """
        初始化动量策略

        Args:
            name: 策略名称
            symbols: 交易标的
            lookback: 回看周期
            threshold: 动量阈值（百分比）
            params: 其他参数
        """
        super().__init__(name, symbols or [], params)
        self.lookback = lookback
        self.threshold = threshold

        # 存储历史数据
        self._prices: Dict[str, deque] = {}
        self._volumes: Dict[str, deque] = {}

    def on_init(self) -> None:
        """初始化策略"""
        self.is_initialized = True
        for symbol in self.symbols:
            self._prices[symbol] = deque(maxlen=self.lookback + 1)
            self._volumes[symbol] = deque(maxlen=self.lookback + 1)

    def on_market_data(self, event: MarketDataEvent) -> Optional[SignalEvent]:
        """
        处理市场数据

        ⭐ 重点：动量计算
        - 动量 = (当前价格 - N日前价格) / N日前价格
        - 正动量 → 买入
        - 负动量 → 卖出

        💡 值得思考：如何处理动量的持续性？
        - 连续N天正动量才确认
        - 动量加速/减速判断
        """
        symbol = event.symbol
        if symbol not in self.symbols:
            return None

        # 初始化数据结构
        if symbol not in self._prices:
            self._prices[symbol] = deque(maxlen=self.lookback + 1)
            self._volumes[symbol] = deque(maxlen=self.lookback + 1)

        # 添加数据
        self._prices[symbol].append(event.close)
        self._volumes[symbol].append(event.volume)

        # 数据不足时不生成信号
        if len(self._prices[symbol]) < self.lookback + 1:
            return None

        # 计算动量
        prices = list(self._prices[symbol])
        momentum = (prices[-1] - prices[0]) / prices[0]

        # 计算成交量动量
        volumes = list(self._volumes[symbol])
        volume_ratio = volumes[-1] / np.mean(volumes[:-1]) if np.mean(volumes[:-1]) > 0 else 1

        # 生成信号
        return self._generate_signal(symbol, momentum, volume_ratio)

    def _generate_signal(
        self,
        symbol: str,
        momentum: float,
        volume_ratio: float
    ) -> Optional[SignalEvent]:
        """
        根据动量生成信号

        ⭐ 重点：信号过滤条件
        1. 动量超过阈值
        2. 成交量放大确认
        3. 避免追高杀跌

        💡 值得思考：如何平衡灵敏度和稳定性？
        - 高阈值：信号少但准确
        - 低阈值：信号多但噪音大
        """
        # 强动量 + 成交量确认
        if momentum > self.threshold and volume_ratio > 1.2:
            return self.generate_signal(
                symbol=symbol,
                direction="BUY",
                strength=min(momentum * 10, 1.0)
            )

        # 强负动量 + 成交量确认
        if momentum < -self.threshold and volume_ratio > 1.2:
            return self.generate_signal(
                symbol=symbol,
                direction="SELL",
                strength=max(momentum * 10, -1.0)
            )

        return None

    def get_momentum(self, symbol: str) -> float:
        """获取当前动量"""
        if symbol not in self._prices or len(self._prices[symbol]) < self.lookback + 1:
            return 0.0
        prices = list(self._prices[symbol])
        return (prices[-1] - prices[0]) / prices[0]

    def on_shutdown(self) -> None:
        """策略关闭清理"""
        self._prices.clear()
        self._volumes.clear()
