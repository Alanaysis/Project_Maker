"""风险报告生成模块

生成格式化的风险分析报告。
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .portfolio import Portfolio
from .var_calculator import VaRCalculator, VaRResult, VaRMethod
from .stress_tester import StressTester, StressTestResult


@dataclass
class RiskReport:
    """风险报告"""
    portfolio_name: str
    report_date: str
    portfolio_value: float
    var_results: List[VaRResult]
    stress_test_results: List[StressTestResult]
    summary: Dict

    def to_dict(self) -> Dict:
        return {
            "portfolio_name": self.portfolio_name,
            "report_date": self.report_date,
            "portfolio_value": self.portfolio_value,
            "var_results": [r.to_dict() for r in self.var_results],
            "stress_test_results": [r.to_dict() for r in self.stress_test_results],
            "summary": self.summary
        }


class RiskReporter:
    """风险报告生成器

    生成包含 VaR 分析和压力测试结果的风险报告。
    """

    def __init__(
        self,
        portfolio: Portfolio,
        returns: np.ndarray,
        weights: Dict[str, float]
    ):
        """
        Args:
            portfolio: 投资组合
            returns: 组合历史收益率
            weights: 资产类别权重
        """
        self.portfolio = portfolio
        self.returns = returns
        self.weights = weights
        self.var_calculator = VaRCalculator(portfolio.total_value)
        self.stress_tester = StressTester(portfolio.total_value)

    def generate_report(
        self,
        confidence_levels: Optional[List[float]] = None,
        scenarios: Optional[List[str]] = None
    ) -> RiskReport:
        """生成风险报告

        Args:
            confidence_levels: 置信水平列表
            scenarios: 历史情景名称列表

        Returns:
            风险报告
        """
        if confidence_levels is None:
            confidence_levels = [0.90, 0.95, 0.99]

        if scenarios is None:
            scenarios = list(StressTester.HISTORICAL_SCENARIOS.keys())

        # 计算各置信水平的 VaR
        var_results = []
        for level in confidence_levels:
            # 使用历史模拟法
            result = self.var_calculator.calculate(
                self.returns,
                VaRMethod.HISTORICAL,
                level
            )
            var_results.append(result)

        # 运行压力测试
        stress_test_results = []
        for scenario_name in scenarios:
            try:
                result = self.stress_tester.historical_stress_test(
                    scenario_name,
                    self.weights
                )
                stress_test_results.append(result)
            except ValueError:
                continue

        # 生成摘要
        summary = self._generate_summary(var_results, stress_test_results)

        return RiskReport(
            portfolio_name=self.portfolio.name,
            report_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            portfolio_value=self.portfolio.total_value,
            var_results=var_results,
            stress_test_results=stress_test_results,
            summary=summary
        )

    def _generate_summary(
        self,
        var_results: List[VaRResult],
        stress_test_results: List[StressTestResult]
    ) -> Dict:
        """生成风险摘要

        Args:
            var_results: VaR 结果列表
            stress_test_results: 压力测试结果列表

        Returns:
            摘要字典
        """
        # VaR 摘要
        var_summary = {}
        for result in var_results:
            level_key = f"{int(result.confidence_level * 100)}%"
            var_summary[level_key] = {
                "var": f"{abs(result.var)*100:.2f}%",
                "var_amount": f"${result.var_amount:,.2f}",
                "cvar": f"{abs(result.cvar)*100:.2f}%",
                "cvar_amount": f"${result.cvar_amount:,.2f}"
            }

        # 压力测试摘要
        stress_summary = {}
        for result in stress_test_results:
            stress_summary[result.scenario.name] = {
                "loss": f"{abs(result.portfolio_loss)*100:.2f}%",
                "loss_amount": f"${abs(result.portfolio_loss_amount):,.2f}"
            }

        # 风险等级评估
        risk_level = self._assess_risk_level(var_results, stress_test_results)

        # 最大潜在损失
        max_loss_scenario = None
        max_loss = 0
        for result in stress_test_results:
            if abs(result.portfolio_loss) > max_loss:
                max_loss = abs(result.portfolio_loss)
                max_loss_scenario = result.scenario.name

        return {
            "var_summary": var_summary,
            "stress_test_summary": stress_summary,
            "risk_level": risk_level,
            "max_potential_loss": {
                "scenario": max_loss_scenario,
                "loss": f"{max_loss*100:.2f}%",
                "loss_amount": f"{self.portfolio.total_value * max_loss:,.2f}"
            }
        }

    def _assess_risk_level(
        self,
        var_results: List[VaRResult],
        stress_test_results: List[StressTestResult]
    ) -> str:
        """评估风险等级

        Args:
            var_results: VaR 结果列表
            stress_test_results: 压力测试结果列表

        Returns:
            风险等级 (低/中/高/极高)
        """
        # 获取 95% VaR
        var_95 = None
        for result in var_results:
            if result.confidence_level == 0.95:
                var_95 = abs(result.var)
                break

        if var_95 is None:
            var_95 = abs(var_results[0].var) if var_results else 0

        # 获取最大压力测试损失
        max_stress_loss = 0
        for result in stress_test_results:
            if abs(result.portfolio_loss) > max_stress_loss:
                max_stress_loss = abs(result.portfolio_loss)

        # 风险等级判断
        if var_95 < 0.02 and max_stress_loss < 0.10:
            return "低"
        elif var_95 < 0.05 and max_stress_loss < 0.20:
            return "中"
        elif var_95 < 0.10 and max_stress_loss < 0.35:
            return "高"
        else:
            return "极高"

    def format_text_report(self, report: RiskReport) -> str:
        """生成文本格式的风险报告

        Args:
            report: 风险报告

        Returns:
            格式化的文本报告
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"风险管理报告")
        lines.append("=" * 60)
        lines.append(f"组合名称: {report.portfolio_name}")
        lines.append(f"报告日期: {report.report_date}")
        lines.append(f"组合市值: ${report.portfolio_value:,.2f}")
        lines.append("")

        # VaR 分析
        lines.append("-" * 60)
        lines.append("VaR 分析")
        lines.append("-" * 60)
        for result in report.var_results:
            level = f"{int(result.confidence_level * 100)}%"
            lines.append(f"\n{level} 置信水平:")
            lines.append(f"  VaR: {abs(result.var)*100:.2f}% (${result.var_amount:,.2f})")
            lines.append(f"  CVaR: {abs(result.cvar)*100:.2f}% (${result.cvar_amount:,.2f})")
        lines.append("")

        # 压力测试
        lines.append("-" * 60)
        lines.append("压力测试结果")
        lines.append("-" * 60)
        for result in report.stress_test_results:
            lines.append(f"\n情景: {result.scenario.name}")
            lines.append(f"  描述: {result.scenario.description}")
            lines.append(f"  损失: {abs(result.portfolio_loss)*100:.2f}% "
                        f"(${abs(result.portfolio_loss_amount):,.2f})")
        lines.append("")

        # 风险摘要
        lines.append("-" * 60)
        lines.append("风险摘要")
        lines.append("-" * 60)
        summary = report.summary
        lines.append(f"风险等级: {summary['risk_level']}")
        max_loss = summary['max_potential_loss']
        lines.append(f"最大潜在损失: {max_loss['loss']} "
                    f"(${max_loss['loss_amount']})")
        lines.append(f"来自情景: {max_loss['scenario']}")
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
