"""
风险管理器 - 综合风险管理

⭐ 重点理解：风险管理器的职责
- 汇总多个风险规则
- 检查订单是否符合所有规则
- 记录风险事件
- 提供风险报告

💡 值得思考：
- 风险规则的优先级如何设定？
- 如何处理规则冲突？
- 风险管理如何影响交易效率？
"""

from typing import Dict, List, Tuple
from ..core.events import OrderEvent, RiskCheckEvent, EventType
from .rules import (
    RiskRule,
    MaxPositionRule,
    MaxOrderSizeRule,
    StopLossRule,
    MaxDrawdownRule,
    CashReserveRule
)


class RiskManager:
    """
    风险管理器

    ⭐ 重点：风险管理器是订单执行前的最后一道关卡
    - 汇总所有风险规则
    - 逐条检查订单
    - 只有通过所有规则的订单才能执行

    💡 值得思考：
    - 风险管理应该在策略层面还是执行层面？
    - 如何实现风险规则的动态调整？
    - 风险管理如何影响策略收益？
    """

    def __init__(self):
        self._rules: List[RiskRule] = []
        self._risk_events: List[Dict] = []
        self._peak_equity: float = 0.0

        # 添加默认规则
        self._add_default_rules()

    def _add_default_rules(self) -> None:
        """添加默认风险规则"""
        self._rules.append(MaxPositionRule(max_position_pct=0.3))
        self._rules.append(MaxOrderSizeRule(max_order_value=50000))
        self._rules.append(StopLossRule(stop_loss_pct=0.05))
        self._rules.append(MaxDrawdownRule(max_drawdown_pct=0.15))
        self._rules.append(CashReserveRule(min_cash_pct=0.1))

    def add_rule(self, rule: RiskRule) -> None:
        """
        添加风险规则

        Args:
            rule: 风险规则实例
        """
        self._rules.append(rule)

    def remove_rule(self, rule_type: type) -> None:
        """
        移除指定类型的风险规则

        Args:
            rule_type: 规则类型
        """
        self._rules = [r for r in self._rules if not isinstance(r, rule_type)]

    def check_order(self, order: OrderEvent, portfolio: Dict) -> Tuple[bool, str]:
        """
        检查订单是否符合所有风险规则

        ⭐ 重点：风险检查流程
        1. 更新最高资产
        2. 逐条检查规则
        3. 记录风险事件
        4. 返回检查结果

        Args:
            order: 待检查的订单
            portfolio: 当前投资组合状态

        Returns:
            Tuple[bool, str]: (是否通过, 原因)

        💡 值得思考：
        - 如何优化风险检查的性能？
        - 如何处理实时交易中的风险检查延迟？
        """
        # 更新最高资产
        total_equity = portfolio.get("total_equity", 0)
        self._peak_equity = max(self._peak_equity, total_equity)

        # 添加最高资产到 portfolio
        portfolio["peak_equity"] = self._peak_equity

        # 逐条检查规则
        for rule in self._rules:
            passed, reason = rule.check_order(order, portfolio)

            if not passed:
                # 记录风险事件
                self._record_risk_event(order, rule, reason)
                return False, reason

        return True, ""

    def _record_risk_event(self, order: OrderEvent, rule: RiskRule, reason: str) -> None:
        """记录风险事件"""
        self._risk_events.append({
            "timestamp": order.timestamp,
            "order_id": order.order_id,
            "symbol": order.symbol,
            "direction": order.direction,
            "rule": rule.__class__.__name__,
            "reason": reason
        })

    def create_risk_check_event(
        self,
        order: OrderEvent,
        portfolio: Dict
    ) -> RiskCheckEvent:
        """
        创建风险检查事件

        Args:
            order: 待检查的订单
            portfolio: 当前投资组合状态

        Returns:
            RiskCheckEvent: 风险检查结果
        """
        passed, reason = self.check_order(order, portfolio)

        return RiskCheckEvent(
            order_id=order.order_id,
            passed=passed,
            reason=reason
        )

    def get_risk_events(self) -> List[Dict]:
        """获取所有风险事件"""
        return self._risk_events.copy()

    def clear_risk_events(self) -> None:
        """清空风险事件记录"""
        self._risk_events.clear()

    def get_risk_summary(self) -> Dict:
        """
        获取风险摘要

        💡 值得思考：还需要哪些风险指标？
        - VaR (Value at Risk)
        - CVaR (Conditional VaR)
        - Beta
        - Sharpe Ratio
        """
        return {
            "total_risk_events": len(self._risk_events),
            "peak_equity": self._peak_equity,
            "rules_count": len(self._rules),
            "rules": [rule.__class__.__name__ for rule in self._rules]
        }
