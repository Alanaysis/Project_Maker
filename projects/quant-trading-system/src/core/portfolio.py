"""
投资组合管理 - 跟踪持仓、资金和交易记录

⭐ 重点理解：
- 持仓管理：跟踪每个标的的持仓数量和成本
- 资金管理：计算可用资金、冻结资金、总资产
- 盈亏计算：浮动盈亏和已实现盈亏

💡 值得思考：
- 如何处理分红和拆股？
- 多币种账户如何管理？
- 如何计算年化收益率？
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from .events import FillEvent, OrderEvent


@dataclass
class Position:
    """
    持仓信息

    💡 值得思考：为什么需要区分平均成本和最新成本？
    - 平均成本用于计算已实现盈亏
    - 最新成本用于计算浮动盈亏
    """
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    realized_pnl: float = 0.0  # 已实现盈亏
    unrealized_pnl: float = 0.0  # 浮动盈亏

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """持仓成本"""
        return self.quantity * self.avg_cost

    @property
    def total_pnl(self) -> float:
        """总盈亏"""
        return self.realized_pnl + self.unrealized_pnl

    def update_price(self, price: float) -> None:
        """更新当前价格和浮动盈亏"""
        self.current_price = price
        if self.quantity > 0:
            self.unrealized_pnl = (price - self.avg_cost) * self.quantity
        else:
            self.unrealized_pnl = 0.0


class Portfolio:
    """
    投资组合

    ⭐ 重点：投资组合管理的核心职责
    1. 跟踪所有持仓
    2. 管理资金流动
    3. 计算盈亏
    4. 维护交易记录

    💡 值得思考：T+0 vs T+1 交割制度的影响
    - T+0：当日买入可当日卖出
    - T+1：当日买入次日才能卖出
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []

    @property
    def total_equity(self) -> float:
        """
        总资产 = 现金 + 所有持仓市值

        ⭐ 重点：总资产是衡量投资组合价值的核心指标
        """
        position_value = sum(
            pos.market_value for pos in self.positions.values()
        )
        return self.cash + position_value

    @property
    def total_pnl(self) -> float:
        """总盈亏"""
        return self.total_equity - self.initial_capital

    @property
    def returns(self) -> float:
        """收益率"""
        if self.initial_capital == 0:
            return 0.0
        return self.total_pnl / self.initial_capital

    def get_position(self, symbol: str) -> Position:
        """获取持仓，不存在则创建"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def update_fill(self, fill: FillEvent) -> None:
        """
        处理成交事件

        ⭐ 重点：成交处理的核心逻辑
        1. 更新持仓数量和成本
        2. 扣除/增加资金
        3. 计算已实现盈亏
        4. 记录交易

        💡 值得思考：如何处理部分成交？
        """
        position = self.get_position(fill.symbol)

        if fill.direction == "BUY":
            # 买入：增加持仓，扣除资金
            total_cost = position.avg_cost * position.quantity
            new_cost = fill.fill_price * fill.quantity
            position.quantity += fill.quantity
            position.avg_cost = (total_cost + new_cost) / position.quantity
            self.cash -= (fill.fill_price * fill.quantity + fill.commission)

        elif fill.direction == "SELL":
            # 卖出：减少持仓，增加资金
            pnl = (fill.fill_price - position.avg_cost) * fill.quantity
            position.realized_pnl += pnl
            position.quantity -= fill.quantity
            self.cash += (fill.fill_price * fill.quantity - fill.commission)

            if position.quantity == 0:
                position.avg_cost = 0.0

        # 更新持仓价格
        position.update_price(fill.fill_price)

        # 记录交易
        self.trades.append({
            "timestamp": fill.timestamp,
            "symbol": fill.symbol,
            "direction": fill.direction,
            "quantity": fill.quantity,
            "price": fill.fill_price,
            "commission": fill.commission,
            "pnl": pnl if fill.direction == "SELL" else 0.0
        })

    def update_market_data(self, symbol: str, price: float) -> None:
        """更新市场价格"""
        if symbol in self.positions:
            self.positions[symbol].update_price(price)

    def record_equity(self, timestamp: datetime) -> None:
        """记录权益曲线点"""
        self.equity_curve.append({
            "timestamp": timestamp,
            "equity": self.total_equity,
            "cash": self.cash,
            "positions_value": self.total_equity - self.cash
        })

    def get_summary(self) -> Dict:
        """
        获取投资组合摘要

        💡 值得思考：还需要哪些统计指标？
        - 夏普比率
        - 最大回撤
        - 胜率
        - 盈亏比
        """
        return {
            "initial_capital": self.initial_capital,
            "total_equity": self.total_equity,
            "cash": self.cash,
            "total_pnl": self.total_pnl,
            "returns": self.returns,
            "positions": {
                sym: {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "realized_pnl": pos.realized_pnl
                }
                for sym, pos in self.positions.items()
                if pos.quantity > 0
            },
            "trade_count": len(self.trades)
        }
