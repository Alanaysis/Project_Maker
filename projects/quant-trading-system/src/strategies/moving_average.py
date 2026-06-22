"""
均线策略 - 经典的趋势跟踪策略

⭐ 重点理解：均线策略的原理
- 短期均线上穿长期均线 → 金叉 → 买入信号
- 短期均线下穿长期均线 → 死叉 → 卖出信号

💡 值得思考：
- 均线周期如何选择？
- 如何处理震荡市中的假信号？
- 均线策略的优缺点是什么？
"""

from typing import Dict, List, Optional
from collections import deque
import numpy as np

from .base import Strategy
from ..core.events import MarketDataEvent, SignalEvent


class MovingAverageStrategy(Strategy):
    """
    均线交叉策略

    ⭐ 重点：均线策略是量化交易的入门策略
    - 简单易懂，便于学习
    - 适合趋势市场
    - 在震荡市中表现较差

    💡 值得思考：
    - SMA vs EMA 哪个更好？
    - 如何优化均线周期？
    - 如何加入过滤条件减少假信号？
    """

    def __init__(
        self,
        name: str = "MA_Cross",
        symbols: List[str] = None,
        short_window: int = 5,
        long_window: int = 20,
        params: Dict = None
    ):
        """
        初始化均线策略

        Args:
            name: 策略名称
            symbols: 交易标的
            short_window: 短期均线周期
            long_window: 长期均线周期
            params: 其他参数
        """
        super().__init__(name, symbols or [], params)
        self.short_window = short_window
        self.long_window = long_window

        # 存储历史价格
        self._prices: Dict[str, deque] = {}
        self._short_ma: Dict[str, float] = {}
        self._long_ma: Dict[str, float] = {}
        self._prev_short_ma: Dict[str, float] = {}
        self._prev_long_ma: Dict[str, float] = {}

    def on_init(self) -> None:
        """
        初始化策略

        💡 值得思考：为什么需要预填充数据？
        - 均线计算需要足够的历史数据
        - 避免在数据不足时产生错误信号
        """
        self.is_initialized = True
        for symbol in self.symbols:
            self._prices[symbol] = deque(maxlen=self.long_window + 1)
            self._short_ma[symbol] = 0.0
            self._long_ma[symbol] = 0.0
            self._prev_short_ma[symbol] = 0.0
            self._prev_long_ma[symbol] = 0.0

    def on_market_data(self, event: MarketDataEvent) -> Optional[SignalEvent]:
        """
        处理市场数据，判断是否产生信号

        ⭐ 重点：信号生成逻辑
        1. 更新价格数据
        2. 计算均线
        3. 判断金叉/死叉
        4. 生成信号

        💡 值得思考：为什么用收盘价而不是开盘价？
        - 收盘价代表当日最终价格
        - 更能反映市场共识
        """
        symbol = event.symbol
        if symbol not in self.symbols:
            return None

        # 初始化价格序列
        if symbol not in self._prices:
            self._prices[symbol] = deque(maxlen=self.long_window + 1)

        # 添加新价格
        self._prices[symbol].append(event.close)

        # 数据不足时不生成信号
        if len(self._prices[symbol]) < self.long_window:
            return None

        # 保存上一次的均线值
        self._prev_short_ma[symbol] = self._short_ma.get(symbol, 0)
        self._prev_long_ma[symbol] = self._long_ma.get(symbol, 0)

        # 计算均线
        prices = list(self._prices[symbol])
        self._short_ma[symbol] = np.mean(prices[-self.short_window:])
        self._long_ma[symbol] = np.mean(prices)

        # 判断交叉
        return self._check_crossover(symbol)

    def _check_crossover(self, symbol: str) -> Optional[SignalEvent]:
        """
        检查均线交叉

        ⭐ 重点：金叉和死叉的判断
        - 金叉：短期均线从下方穿越长期均线
        - 死叉：短期均线从上方穿越长期均线

        💡 值得思考：如何避免假交叉？
        - 增加确认条件（连续N天）
        - 增加幅度要求（穿越幅度 > 阈值）
        - 结合其他指标
        """
        short_ma = self._short_ma[symbol]
        long_ma = self._long_ma[symbol]
        prev_short = self._prev_short_ma[symbol]
        prev_long = self._prev_long_ma[symbol]

        # 检查数据是否有效
        if prev_short == 0 or prev_long == 0:
            return None

        # 金叉：短期均线从下方穿越长期均线
        if prev_short <= prev_long and short_ma > long_ma:
            return self.generate_signal(
                symbol=symbol,
                direction="BUY",
                strength=0.8
            )

        # 死叉：短期均线从上方穿越长期均线
        if prev_short >= prev_long and short_ma < long_ma:
            return self.generate_signal(
                symbol=symbol,
                direction="SELL",
                strength=-0.8
            )

        return None

    def get_current_ma(self, symbol: str) -> Dict[str, float]:
        """获取当前均线值"""
        return {
            "short_ma": self._short_ma.get(symbol, 0),
            "long_ma": self._long_ma.get(symbol, 0)
        }

    def on_shutdown(self) -> None:
        """策略关闭清理"""
        self._prices.clear()
        self._short_ma.clear()
        self._long_ma.clear()
