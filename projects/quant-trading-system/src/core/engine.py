"""
回测引擎 - 量化交易系统的核心

⭐ 重点理解：回测引擎的职责
- 协调所有模块的工作
- 按时间顺序处理事件
- 模拟真实的交易流程
- 计算回测结果

💡 值得思考：
- 事件驱动 vs 向量化回测的优劣
- 如何保证回测结果的准确性？
- 如何提高回测的性能？
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from .events import (
    EventBus, EventType, Event,
    MarketDataEvent, SignalEvent, OrderEvent, FillEvent, RiskCheckEvent
)
from .portfolio import Portfolio
from ..strategies.base import Strategy
from ..data.loader import DataLoader
from ..risk.manager import RiskManager
from ..utils.logger import logger


class BacktestEngine:
    """
    回测引擎

    ⭐ 重点：回测引擎的核心循环
    1. 加载历史数据
    2. 按时间顺序推送数据
    3. 策略处理数据并生成信号
    4. 风险管理器检查信号
    5. 执行订单并更新投资组合
    6. 记录回测结果

    💡 值得思考：
    - 如何避免未来函数（look-ahead bias）？
    - 如何处理停牌和涨跌停？
    - 如何模拟滑点和手续费？
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_pct: float = 0.001
    ):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage_pct: 滑点比例

        💡 值得思考：
        - 手续费如何影响策略收益？
        - 滑点如何影响回测准确性？
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_pct = slippage_pct

        # 初始化核心组件
        self.event_bus = EventBus()
        self.portfolio = Portfolio(initial_capital)
        self.data_loader = DataLoader()
        self.risk_manager = RiskManager()
        self.strategies: List[Strategy] = []

        # 回测状态
        self.is_running = False
        self.current_date: Optional[datetime] = None
        self.trade_count = 0

        # 当前市场数据缓存（用于新标的的价格获取）
        self.current_data: Dict = {}

        # 注册事件处理器
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        注册事件处理器

        ⭐ 重点：事件处理的顺序很重要
        1. 市场数据 → 策略
        2. 信号 → 风险检查
        3. 订单 → 执行
        4. 成交 → 更新投资组合
        """
        self.event_bus.subscribe(EventType.MARKET_DATA, self._on_market_data)
        self.event_bus.subscribe(EventType.SIGNAL, self._on_signal)
        self.event_bus.subscribe(EventType.ORDER, self._on_order)
        self.event_bus.subscribe(EventType.FILL, self._on_fill)

    def add_strategy(self, strategy: Strategy) -> None:
        """
        添加交易策略

        Args:
            strategy: 策略实例
        """
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")

    def load_data(self, data: pd.DataFrame, symbol: str) -> None:
        """
        加载历史数据

        Args:
            data: OHLCV 数据
            symbol: 标的代码
        """
        self.data_loader.load_dataframe(data, symbol)
        logger.info(f"Loaded {len(data)} bars for {symbol}")

    def _on_market_data(self, event: MarketDataEvent) -> None:
        """
        处理市场数据事件

        ⭐ 重点：市场数据的处理流程
        1. 更新投资组合中的价格
        2. 将数据传递给所有策略
        3. 处理策略生成的信号
        """
        # 缓存当前市场数据
        self.current_data[event.symbol] = event

        # 更新投资组合价格
        self.portfolio.update_market_data(event.symbol, event.close)

        # 传递给策略
        for strategy in self.strategies:
            signal = strategy.on_market_data(event)
            if signal:
                self.event_bus.publish(signal)

    def _on_signal(self, event: SignalEvent) -> None:
        """
        处理信号事件

        ⭐ 重点：信号转换为订单
        1. 根据信号强度计算订单数量
        2. 创建订单事件
        3. 提交给风险检查
        """
        # 计算订单数量
        quantity = self._calculate_order_quantity(event)
        if quantity <= 0:
            return

        # 获取订单价格：新标的持仓价格为0，使用市场数据的当前价格
        position = self.portfolio.get_position(event.symbol)
        if position.quantity == 0 and event.direction == "BUY":
            price = self.current_data[event.symbol].close
        else:
            price = position.current_price

        # 创建订单
        order = OrderEvent(
            symbol=event.symbol,
            direction=event.direction,
            order_type="MARKET",
            quantity=quantity,
            price=price,
            order_id=str(uuid.uuid4())[:8],
            status="PENDING"
        )

        self.event_bus.publish(order)

    def _calculate_order_quantity(self, signal: SignalEvent) -> int:
        """
        计算订单数量

        💡 值得思考：
        - 如何根据信号强度调整仓位？
        - 如何实现 Kelly 公式？
        - 如何实现等权重分配？
        """
        # 简单的固定仓位策略
        max_position_value = self.portfolio.total_equity * 0.2
        position = self.portfolio.get_position(signal.symbol)
        if position.quantity == 0 and signal.direction == "BUY":
            current_price = self.current_data[signal.symbol].close
        else:
            current_price = position.current_price

        if current_price <= 0:
            return 0

        quantity = int(max_position_value / current_price)

        # 卖出时不能超过持仓
        if signal.direction == "SELL":
            current_quantity = self.portfolio.get_position(signal.symbol).quantity
            quantity = min(quantity, current_quantity)

        return quantity

    def _on_order(self, event: OrderEvent) -> None:
        """
        处理订单事件

        ⭐ 重点：订单处理流程
        1. 风险检查
        2. 模拟成交
        3. 生成成交事件
        """
        # 风险检查
        portfolio_state = self.portfolio.get_summary()
        risk_check = self.risk_manager.create_risk_check_event(event, portfolio_state)

        if not risk_check.passed:
            logger.risk(f"Order rejected: {risk_check.reason}")
            event.status = "REJECTED"
            return

        # 模拟成交
        fill = self._simulate_fill(event)
        if fill:
            self.event_bus.publish(fill)

    def _simulate_fill(self, order: OrderEvent) -> Optional[FillEvent]:
        """
        模拟成交

        ⭐ 重点：成交模拟需要考虑
        - 滑点：实际成交价与预期价格的偏差
        - 手续费：交易成本
        - 部分成交：大单可能分多次成交

        💡 值得思考：
        - 如何模拟真实的市场冲击？
        - 如何处理涨跌停？
        """
        # 计算滑点
        slippage = order.price * self.slippage_pct
        if order.direction == "BUY":
            fill_price = order.price + slippage
        else:
            fill_price = order.price - slippage

        # 计算手续费
        commission = order.quantity * fill_price * self.commission_rate

        # 检查资金是否充足
        if order.direction == "BUY":
            total_cost = order.quantity * fill_price + commission
            if total_cost > self.portfolio.cash:
                logger.risk(f"Insufficient cash for order {order.order_id}")
                return None

        # 创建成交事件
        fill = FillEvent(
            symbol=order.symbol,
            direction=order.direction,
            quantity=order.quantity,
            fill_price=round(fill_price, 2),
            commission=round(commission, 2),
            order_id=order.order_id
        )

        order.status = "FILLED"
        self.trade_count += 1

        return fill

    def _on_fill(self, event: FillEvent) -> None:
        """
        处理成交事件

        ⭐ 重点：更新投资组合
        """
        self.portfolio.update_fill(event)
        logger.trade(
            f"{event.direction} {event.quantity} {event.symbol} "
            f"@ {event.fill_price} (commission: {event.commission:.2f})"
        )

    def run(self) -> Dict:
        """
        运行回测

        ⭐ 重点：回测的主循环
        1. 初始化策略
        2. 按时间顺序推送数据
        3. 处理事件
        4. 记录权益曲线
        5. 计算回测结果

        💡 值得思考：
        - 如何处理多标的的时间对齐？
        - 如何实现进度显示？
        """
        logger.info("Starting backtest...")

        # 初始化策略
        for strategy in self.strategies:
            strategy.on_init()

        self.is_running = True

        # 获取所有标的
        symbols = self.data_loader.get_symbols()
        if not symbols:
            logger.error("No data loaded")
            return {}

        # 获取最大数据长度
        max_bars = max(self.data_loader.get_bar_count(s) for s in symbols)

        # 主循环：按时间顺序推送数据
        for i in range(max_bars):
            for symbol in symbols:
                bar = self.data_loader.get_bar(symbol, i)
                if bar is None:
                    continue

                # 创建市场数据事件
                event = MarketDataEvent(
                    symbol=symbol,
                    open=bar["open"],
                    high=bar["high"],
                    low=bar["low"],
                    close=bar["close"],
                    volume=bar["volume"],
                    timestamp=bar.get("date")
                )

                # 发布事件
                self.event_bus.publish(event)

            # 处理所有事件
            self.event_bus.process_events()

            # 记录权益曲线
            self.portfolio.record_equity(bar.get("date", datetime.now()))

        # 关闭策略
        for strategy in self.strategies:
            strategy.on_shutdown()

        self.is_running = False

        # 计算回测结果
        results = self._calculate_results()

        logger.info("Backtest completed")
        return results

    def _calculate_results(self) -> Dict:
        """
        计算回测结果

        ⭐ 重点：回测结果的指标
        - 总收益率
        - 年化收益率
        - 最大回撤
        - 夏普比率
        - 胜率

        💡 值得思考：
        - 如何计算年化收益率？
        - 夏普比率的计算公式是什么？
        """
        summary = self.portfolio.get_summary()
        equity_curve = pd.DataFrame(self.portfolio.equity_curve)

        # 计算收益率
        total_return = self.portfolio.returns

        # 计算最大回撤
        max_drawdown = 0.0
        if len(equity_curve) > 0:
            equity_series = equity_curve["equity"]
            cummax = equity_series.cummax()
            drawdown = (cummax - equity_series) / cummax
            max_drawdown = drawdown.max()

        # 计算胜率
        trades = self.portfolio.trades
        winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        win_rate = winning_trades / len(trades) if trades else 0

        # 计算年化收益率（假设252个交易日）
        if len(equity_curve) > 0:
            days = len(equity_curve)
            annualized_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        else:
            annualized_return = 0

        results = {
            "initial_capital": self.initial_capital,
            "final_equity": summary["total_equity"],
            "total_return": total_return,
            "annualized_return": annualized_return,
            "max_drawdown": max_drawdown,
            "total_trades": self.trade_count,
            "win_rate": win_rate,
            "risk_summary": self.risk_manager.get_risk_summary(),
            "equity_curve": equity_curve
        }

        # 打印结果
        self._print_results(results)

        return results

    def _print_results(self, results: Dict) -> None:
        """打印回测结果"""
        logger.performance("=" * 50)
        logger.performance("Backtest Results")
        logger.performance("=" * 50)
        logger.performance(f"Initial Capital: ${results['initial_capital']:,.2f}")
        logger.performance(f"Final Equity: ${results['final_equity']:,.2f}")
        logger.performance(f"Total Return: {results['total_return']:.2%}")
        logger.performance(f"Annualized Return: {results['annualized_return']:.2%}")
        logger.performance(f"Max Drawdown: {results['max_drawdown']:.2%}")
        logger.performance(f"Total Trades: {results['total_trades']}")
        logger.performance(f"Win Rate: {results['win_rate']:.2%}")
        logger.performance("=" * 50)
