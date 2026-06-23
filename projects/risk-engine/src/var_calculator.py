"""VaR 计算模块

实现多种 VaR (Value at Risk) 计算方法：
- 历史模拟法 (Historical Simulation)
- 参数法 (Parametric/Variance-Covariance)
- 蒙特卡洛模拟法 (Monte Carlo Simulation)
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class VaRMethod(Enum):
    """VaR 计算方法"""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class VaRResult:
    """VaR 计算结果"""
    method: str
    confidence_level: float
    var: float
    cvar: float  # Conditional VaR (Expected Shortfall)
    portfolio_value: float
    var_amount: float  # VaR 金额
    cvar_amount: float  # CVaR 金额

    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "confidence_level": self.confidence_level,
            "var": self.var,
            "cvar": self.cvar,
            "portfolio_value": self.portfolio_value,
            "var_amount": self.var_amount,
            "cvar_amount": self.cvar_amount
        }


class VaRCalculator:
    """VaR 计算器

    支持多种 VaR 计算方法，用于评估投资组合的风险价值。
    """

    def __init__(self, portfolio_value: float):
        """
        Args:
            portfolio_value: 投资组合当前市值
        """
        self.portfolio_value = portfolio_value

    def calculate(
        self,
        returns: np.ndarray,
        method: VaRMethod = VaRMethod.HISTORICAL,
        confidence_level: float = 0.95,
        **kwargs
    ) -> VaRResult:
        """计算 VaR

        Args:
            returns: 历史收益率序列
            method: VaR 计算方法
            confidence_level: 置信水平 (默认 0.95)
            **kwargs: 各方法的特定参数

        Returns:
            VaR 计算结果
        """
        if method == VaRMethod.HISTORICAL:
            var, cvar = self._historical_var(returns, confidence_level)
        elif method == VaRMethod.PARAMETRIC:
            var, cvar = self._parametric_var(returns, confidence_level)
        elif method == VaRMethod.MONTE_CARLO:
            num_simulations = kwargs.get("num_simulations", 10000)
            var, cvar = self._monte_carlo_var(
                returns, confidence_level, num_simulations
            )
        else:
            raise ValueError(f"Unknown VaR method: {method}")

        return VaRResult(
            method=method.value,
            confidence_level=confidence_level,
            var=var,
            cvar=cvar,
            portfolio_value=self.portfolio_value,
            var_amount=self.portfolio_value * abs(var),
            cvar_amount=self.portfolio_value * abs(cvar)
        )

    def _historical_var(
        self,
        returns: np.ndarray,
        confidence_level: float
    ) -> Tuple[float, float]:
        """历史模拟法计算 VaR

        Args:
            returns: 历史收益率序列
            confidence_level: 置信水平

        Returns:
            (VaR, CVaR) 元组
        """
        if len(returns) == 0:
            raise ValueError("Returns array is empty")

        # 计算分位数
        alpha = 1 - confidence_level
        var = np.percentile(returns, alpha * 100)

        # 计算 CVaR (Expected Shortfall)
        # CVaR 是低于 VaR 的所有损失的平均值
        losses_below_var = returns[returns <= var]
        if len(losses_below_var) > 0:
            cvar = np.mean(losses_below_var)
        else:
            cvar = var

        return var, cvar

    def _parametric_var(
        self,
        returns: np.ndarray,
        confidence_level: float
    ) -> Tuple[float, float]:
        """参数法计算 VaR (假设正态分布)

        Args:
            returns: 历史收益率序列
            confidence_level: 置信水平

        Returns:
            (VaR, CVaR) 元组
        """
        if len(returns) == 0:
            raise ValueError("Returns array is empty")

        mu = np.mean(returns)
        sigma = np.std(returns, ddof=1)  # 样本标准差

        # 正态分布的 z 分位数
        z = stats.norm.ppf(1 - confidence_level)

        # VaR = mu + z * sigma (注意 z 是负数)
        var = mu + z * sigma

        # CVaR 对于正态分布的计算公式
        # CVaR = mu - sigma * phi(z) / (1 - confidence_level)
        cvar = mu - sigma * stats.norm.pdf(z) / (1 - confidence_level)

        return var, cvar

    def _monte_carlo_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        num_simulations: int = 10000
    ) -> Tuple[float, float]:
        """蒙特卡洛模拟法计算 VaR

        Args:
            returns: 历史收益率序列
            confidence_level: 置信水平
            num_simulations: 模拟次数

        Returns:
            (VaR, CVaR) 元组
        """
        if len(returns) == 0:
            raise ValueError("Returns array is empty")

        mu = np.mean(returns)
        sigma = np.std(returns, ddof=1)

        # 生成模拟收益率
        simulated_returns = np.random.normal(mu, sigma, num_simulations)

        # 使用模拟数据计算 VaR
        alpha = 1 - confidence_level
        var = np.percentile(simulated_returns, alpha * 100)

        # 计算 CVaR
        losses_below_var = simulated_returns[simulated_returns <= var]
        if len(losses_below_var) > 0:
            cvar = np.mean(losses_below_var)
        else:
            cvar = var

        return var, cvar

    def calculate_multiple_confidence_levels(
        self,
        returns: np.ndarray,
        method: VaRMethod = VaRMethod.HISTORICAL,
        confidence_levels: Optional[List[float]] = None
    ) -> List[VaRResult]:
        """计算多个置信水平下的 VaR

        Args:
            returns: 历史收益率序列
            method: VaR 计算方法
            confidence_levels: 置信水平列表

        Returns:
            VaR 结果列表
        """
        if confidence_levels is None:
            confidence_levels = [0.90, 0.95, 0.99]

        results = []
        for level in confidence_levels:
            result = self.calculate(returns, method, level)
            results.append(result)

        return results

    def compare_methods(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict[str, VaRResult]:
        """比较不同 VaR 方法的计算结果

        Args:
            returns: 历史收益率序列
            confidence_level: 置信水平

        Returns:
            各方法结果的字典
        """
        results = {}
        for method in VaRMethod:
            result = self.calculate(returns, method, confidence_level)
            results[method.value] = result

        return results
