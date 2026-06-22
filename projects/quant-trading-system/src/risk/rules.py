"""
风险规则 - 定义各种风险控制规则

⭐ 重点理解：风险规则的类型
1. 仓位控制：限制单个标的的仓位
2. 止损规则：限制单笔交易的最大亏损
3. 回撤控制：限制组合的最大回撤
4. 集中度控制：限制行业/板块集中度

💡 值得思考：
- 风险规则如何平衡收益和风险？
- 动态风险规则 vs 静态风险规则
- 如何处理极端市场情况？
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from ..core.events import OrderEvent, FillEvent


class RiskRule(ABC):
    """
    风险规则基类

    ⭐ 重点：风险规则的接口设计
    - check_order: 检查订单是否符合规则
    - 返回 (通过, 原因) 元组
    """

    @abstractmethod
    def check_order(self, order: OrderEvent, portfolio: Dict) -> tuple:
        """
        检查订单是否符合风险规则

        Args:
            order: 待检查的订单
            portfolio: 当前投资组合状态

        Returns:
            tuple: (passed: bool, reason: str)
        """
        pass


class MaxPositionRule(RiskRule):
    """
    最大仓位规则

    ⭐ 重点：限制单个标的的最大仓位比例
    - 避免过度集中
    - 降低单一标的风险

    💡 值得思考：
    - 最大仓位比例如何设定？
    - 是否应该动态调整？
    """

    def __init__(self, max_position_pct: float = 0.2):
        """
        Args:
            max_position_pct: 最大仓位比例（占总资产）
        """
        self.max_position_pct = max_position_pct

    def check_order(self, order: OrderEvent, portfolio: Dict) -> tuple:
        """
        检查订单是否超过最大仓位限制

        💡 值得思考：如何计算订单执行后的仓位？
        """
        if order.direction != "BUY":
            return True, ""

        total_equity = portfolio.get("total_equity", 0)
        if total_equity <= 0:
            return False, "Insufficient equity"

        # 计算当前持仓价值
        positions = portfolio.get("positions", {})
        current_value = positions.get(order.symbol, {}).get("market_value", 0)

        # 计算订单价值
        order_value = order.quantity * order.price

        # 计算新的仓位比例
        new_position_value = current_value + order_value
        new_position_pct = new_position_value / total_equity

        if new_position_pct > self.max_position_pct:
            return False, f"Position would exceed {self.max_position_pct:.0%} limit"

        return True, ""


class MaxOrderSizeRule(RiskRule):
    """
    最大订单规模规则

    💡 值得思考：为什么限制单笔订单规模？
    - 防止误操作
    - 控制交易冲击成本
    """

    def __init__(self, max_order_value: float = 50000):
        """
        Args:
            max_order_value: 最大订单金额
        """
        self.max_order_value = max_order_value

    def check_order(self, order: OrderEvent, portfolio: Dict) -> tuple:
        order_value = order.quantity * order.price
        if order_value > self.max_order_value:
            return False, f"Order value {order_value:.0f} exceeds limit {self.max_order_value:.0f}"
        return True, ""


class StopLossRule(RiskRule):
    """
    止损规则

    ⭐ 重点：止损是风险管理的核心
    - 限制单笔交易的最大亏损
    - 保护本金

    💡 值得思考：
    - 固定止损 vs 追踪止损
    - 止损比例如何设定？
    - 止损后何时重新入场？
    """

    def __init__(self, stop_loss_pct: float = 0.05):
        """
        Args:
            stop_loss_pct: 止损比例
        """
        self.stop_loss_pct = stop_loss_pct

    def check_order(self, order: OrderEvent, portfolio: Dict) -> tuple:
        """
        对于卖出订单，检查是否触发止损

        💡 值得思考：止损应该在风险管理中还是策略中实现？
        """
        if order.direction != "SELL":
            return True, ""

        positions = portfolio.get("positions", {})
        position = positions.get(order.symbol, {})

        if not position:
            return True, ""

        avg_cost = position.get("avg_cost", 0)
        if avg_cost <= 0:
            return True, ""

        # 计算亏损比例
        loss_pct = (avg_cost - order.price) / avg_cost

        if loss_pct > self.stop_loss_pct:
            return False, f"Stop loss triggered: {loss_pct:.2%} > {self.stop_loss_pct:.2%}"

        return True, ""


class MaxDrawdownRule(RiskRule):
    """
    最大回撤规则

    ⭐ 重点：控制组合的最大回撤
    - 保护投资者的本金
    - 避免大幅亏损

    💡 值得思考：
    - 如何计算最大回撤？
    - 回撤达到阈值后如何处理？
    """

    def __init__(self, max_drawdown_pct: float = 0.1):
        """
        Args:
            max_drawdown_pct: 最大回撤比例
        """
        self.max_drawdown_pct = max_drawdown_pct

    def check_order(self, order: OrderEvent, portfolio: Dict) -> tuple:
        """
        检查订单是否会导致超过最大回撤

        💡 值得思考：如何预测订单执行后的回撤？
        """
        total_equity = portfolio.get("total_equity", 0)
        peak_equity = portfolio.get("peak_equity", total_equity)

        if peak_equity <= 0:
            return True, ""

        current_drawdown = (peak_equity - total_equity) / peak_equity

        if current_drawdown > self.max_drawdown_pct:
            return False, f"Max drawdown exceeded: {current_drawdown:.2%} > {self.max_drawdown_pct:.2%}"

        return True, ""


class CashReserveRule(RiskRule):
    """
    现金储备规则

    💡 值得思考：为什么需要保留现金？
    - 应对突发情况
    - 抓住投资机会
    - 满足流动性需求
    """

    def __init__(self, min_cash_pct: float = 0.1):
        """
        Args:
            min_cash_pct: 最小现金比例
        """
        self.min_cash_pct = min_cash_pct

    def check_order(self, order: OrderEvent, portfolio: Dict) -> tuple:
        if order.direction != "BUY":
            return True, ""

        total_equity = portfolio.get("total_equity", 0)
        cash = portfolio.get("cash", 0)

        if total_equity <= 0:
            return False, "Insufficient equity"

        # 计算订单成本
        order_cost = order.quantity * order.price

        # 计算订单执行后的现金
        new_cash = cash - order_cost
        new_cash_pct = new_cash / total_equity

        if new_cash_pct < self.min_cash_pct:
            return False, f"Cash reserve would drop below {self.min_cash_pct:.0%}"

        return True, ""
