"""压力测试模块

实现多种压力测试方法：
- 历史情景压力测试
- 假设情景压力测试
- 反向压力测试
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class StressTestType(Enum):
    """压力测试类型"""
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"
    REVERSE = "reverse"


@dataclass
class StressScenario:
    """压力测试情景"""
    name: str
    description: str
    shocks: Dict[str, float]  # 各标的的冲击幅度 (例如 {"AAPL": -0.20, "GOOGL": -0.15})
    probability: Optional[float] = None  # 情景发生的概率

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "shocks": self.shocks,
            "probability": self.probability
        }


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario: StressScenario
    portfolio_loss: float  # 组合损失率
    portfolio_loss_amount: float  # 组合损失金额
    position_losses: Dict[str, float]  # 各持仓的损失
    var_before: float  # 压力测试前的 VaR
    var_after: float  # 压力测试后的 VaR

    def to_dict(self) -> Dict:
        return {
            "scenario": self.scenario.to_dict(),
            "portfolio_loss": self.portfolio_loss,
            "portfolio_loss_amount": self.portfolio_loss_amount,
            "position_losses": self.position_losses,
            "var_before": self.var_before,
            "var_after": self.var_after
        }


class StressTester:
    """压力测试器

    支持历史情景、假设情景和反向压力测试。
    """

    # 预定义的历史危机情景
    HISTORICAL_SCENARIOS = {
        "2008_financial_crisis": StressScenario(
            name="2008 金融危机",
            description="2008年全球金融危机期间的市场冲击",
            shocks={
                "equity": -0.40,
                "bond": 0.05,
                "commodity": -0.30,
                "real_estate": -0.35
            }
        ),
        "2020_covid": StressScenario(
            name="2020 新冠疫情",
            description="2020年新冠疫情爆发期间的市场冲击",
            shocks={
                "equity": -0.30,
                "bond": 0.02,
                "commodity": -0.25,
                "real_estate": -0.15
            }
        ),
        "2000_dotcom": StressScenario(
            name="2000 互联网泡沫",
            description="2000年互联网泡沫破裂",
            shocks={
                "equity": -0.45,
                "tech": -0.70,
                "bond": 0.10,
                "commodity": -0.10
            }
        ),
        "black_monday": StressScenario(
            name="黑色星期一",
            description="1987年10月19日股市崩盘",
            shocks={
                "equity": -0.22,
                "bond": 0.03,
                "commodity": -0.05
            }
        )
    }

    def __init__(self, portfolio_value: float):
        """
        Args:
            portfolio_value: 投资组合当前市值
        """
        self.portfolio_value = portfolio_value

    def historical_stress_test(
        self,
        scenario_name: str,
        weights: Dict[str, float]
    ) -> StressTestResult:
        """历史情景压力测试

        Args:
            scenario_name: 历史情景名称
            weights: 组合中各资产类别的权重

        Returns:
            压力测试结果
        """
        if scenario_name not in self.HISTORICAL_SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        scenario = self.HISTORICAL_SCENARIOS[scenario_name]
        return self._apply_scenario(scenario, weights)

    def hypothetical_stress_test(
        self,
        scenario: StressScenario,
        weights: Dict[str, float]
    ) -> StressTestResult:
        """假设情景压力测试

        Args:
            scenario: 压力测试情景
            weights: 组合中各资产类别的权重

        Returns:
            压力测试结果
        """
        return self._apply_scenario(scenario, weights)

    def reverse_stress_test(
        self,
        target_loss: float,
        weights: Dict[str, float],
        risk_factor: str = "equity"
    ) -> StressScenario:
        """反向压力测试

        计算要达到目标损失，需要多大的市场冲击。

        Args:
            target_loss: 目标损失率 (例如 -0.20 表示 20% 损失)
            weights: 组合中各资产类别的权重
            risk_factor: 主要风险因子

        Returns:
            达到目标损失所需的冲击情景
        """
        if risk_factor not in weights:
            raise ValueError(f"Risk factor {risk_factor} not in weights")

        # 计算需要的冲击幅度
        # 简化假设：只有单一风险因子受到影响
        factor_weight = weights[risk_factor]
        required_shock = target_loss / factor_weight

        scenario = StressScenario(
            name="反向压力测试",
            description=f"要达到 {abs(target_loss)*100:.1f}% 的损失，"
                       f"{risk_factor} 需要下跌 {abs(required_shock)*100:.1f}%",
            shocks={risk_factor: required_shock}
        )

        return scenario

    def _apply_scenario(
        self,
        scenario: StressScenario,
        weights: Dict[str, float]
    ) -> StressTestResult:
        """应用压力测试情景

        Args:
            scenario: 压力测试情景
            weights: 组合中各资产类别的权重

        Returns:
            压力测试结果
        """
        position_losses = {}
        total_loss = 0.0

        # 计算每个资产类别的损失
        for asset_class, weight in weights.items():
            shock = scenario.shocks.get(asset_class, 0)
            loss = weight * shock
            position_losses[asset_class] = loss
            total_loss += loss

        # 计算损失金额
        loss_amount = self.portfolio_value * total_loss

        # 简化的 VaR 计算（假设冲击后的波动率变化）
        # 实际应用中应该使用更复杂的模型
        var_before = self.portfolio_value * 0.02  # 假设原始 VaR 为 2%
        var_after = self.portfolio_value * abs(total_loss) * 0.5  # 假设冲击后 VaR 增加

        return StressTestResult(
            scenario=scenario,
            portfolio_loss=total_loss,
            portfolio_loss_amount=loss_amount,
            position_losses=position_losses,
            var_before=var_before,
            var_after=var_after
        )

    def run_multiple_scenarios(
        self,
        scenarios: List[StressScenario],
        weights: Dict[str, float]
    ) -> List[StressTestResult]:
        """运行多个压力测试情景

        Args:
            scenarios: 压力测试情景列表
            weights: 组合中各资产类别的权重

        Returns:
            压力测试结果列表
        """
        results = []
        for scenario in scenarios:
            result = self._apply_scenario(scenario, weights)
            results.append(result)

        return results

    def sensitivity_analysis(
        self,
        weights: Dict[str, float],
        risk_factor: str,
        shock_range: Tuple[float, float] = (-0.50, 0.50),
        num_steps: int = 11
    ) -> List[Tuple[float, float]]:
        """敏感性分析

        分析单个风险因子在不同冲击水平下的影响。

        Args:
            weights: 组合中各资产类别的权重
            risk_factor: 风险因子
            shock_range: 冲击范围
            num_steps: 分析步数

        Returns:
            [(冲击水平, 组合损失)] 列表
        """
        if risk_factor not in weights:
            raise ValueError(f"Risk factor {risk_factor} not in weights")

        shocks = np.linspace(shock_range[0], shock_range[1], num_steps)
        results = []

        for shock in shocks:
            scenario = StressScenario(
                name=f"{risk_factor} shock {shock:.1%}",
                description=f"{risk_factor} 冲击 {shock:.1%}",
                shocks={risk_factor: shock}
            )
            result = self._apply_scenario(scenario, weights)
            results.append((shock, result.portfolio_loss))

        return results
