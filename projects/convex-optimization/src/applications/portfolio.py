"""
投资组合优化

实现 Markowitz 均值-方差模型和各种变体。
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class PortfolioResult:
    """投资组合优化结果"""

    weights: np.ndarray  # 资产权重
    expected_return: float  # 期望收益
    risk: float  # 风险（标准差）
    sharpe_ratio: float  # 夏普比率


class PortfolioOptimizer:
    """投资组合优化器

    实现 Markowitz 均值-方差模型。

    问题：
    min w^T Σ w
    s.t. w^T μ = target_return
         w^T 1 = 1
         w ≥ 0 (可选)
    """

    def __init__(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
    ):
        """
        Args:
            returns: 收益率矩阵 (n_periods, n_assets)
            risk_free_rate: 无风险利率
        """
        self.returns = np.atleast_2d(returns)
        self.n_periods, self.n_assets = self.returns.shape
        self.risk_free_rate = risk_free_rate

        # 计算统计量
        self.mean_returns = np.mean(self.returns, axis=0)
        self.cov_matrix = np.cov(self.returns, rowvar=False)

    def min_variance_portfolio(
        self,
        allow_short: bool = False,
    ) -> PortfolioResult:
        """最小方差组合

        min w^T Σ w
        s.t. w^T 1 = 1
        """
        n = self.n_assets
        Sigma = self.cov_matrix
        ones = np.ones(n)

        # 解析解（允许卖空）
        if allow_short:
            Sigma_inv = np.linalg.inv(Sigma)
            w = Sigma_inv @ ones / (ones @ Sigma_inv @ ones)
        else:
            # 使用二次规划（简化版本）
            w = self._solve_qp_no_short(Sigma, ones)

        expected_return = w @ self.mean_returns
        risk = np.sqrt(w @ Sigma @ w)
        sharpe = (expected_return - self.risk_free_rate) / risk if risk > 0 else 0

        return PortfolioResult(
            weights=w,
            expected_return=expected_return,
            risk=risk,
            sharpe_ratio=sharpe,
        )

    def max_sharpe_portfolio(
        self,
        allow_short: bool = False,
    ) -> PortfolioResult:
        """最大夏普比率组合

        max (w^T μ - r_f) / sqrt(w^T Σ w)
        s.t. w^T 1 = 1
        """
        n = self.n_assets
        Sigma = self.cov_matrix
        excess_returns = self.mean_returns - self.risk_free_rate

        # 解析解（允许卖空）
        if allow_short:
            Sigma_inv = np.linalg.inv(Sigma)
            w = Sigma_inv @ excess_returns / (np.ones(n) @ Sigma_inv @ excess_returns)
        else:
            # 使用网格搜索（简化版本）
            w = self._solve_max_sharpe_no_short(Sigma, excess_returns)

        expected_return = w @ self.mean_returns
        risk = np.sqrt(w @ Sigma @ w)
        sharpe = (expected_return - self.risk_free_rate) / risk if risk > 0 else 0

        return PortfolioResult(
            weights=w,
            expected_return=expected_return,
            risk=risk,
            sharpe_ratio=sharpe,
        )

    def efficient_frontier(
        self,
        n_points: int = 100,
        allow_short: bool = False,
    ) -> List[PortfolioResult]:
        """计算有效前沿"""
        # 找到收益范围
        min_ret = np.min(self.mean_returns)
        max_ret = np.max(self.mean_returns)
        target_returns = np.linspace(min_ret, max_ret, n_points)

        portfolios = []
        for target_ret in target_returns:
            try:
                p = self._optimize_for_return(target_ret, allow_short)
                portfolios.append(p)
            except Exception:
                continue

        return portfolios

    def _optimize_for_return(
        self,
        target_return: float,
        allow_short: bool = False,
    ) -> PortfolioResult:
        """为给定目标收益优化"""
        n = self.n_assets
        Sigma = self.cov_matrix
        mu = self.mean_returns
        ones = np.ones(n)

        # 使用拉格朗日乘子法（允许卖空）
        if allow_short:
            # 构建线性系统
            # [2Σ  μ  1] [w ]   [0]
            # [μ^T 0  0] [λ1] = [target_return]
            # [1^T 0  0] [λ2]   [1]
            A = np.zeros((n + 2, n + 2))
            A[:n, :n] = 2 * Sigma
            A[:n, n] = mu
            A[:n, n + 1] = ones
            A[n, :n] = mu
            A[n + 1, :n] = ones

            b = np.zeros(n + 2)
            b[n] = target_return
            b[n + 1] = 1

            solution = np.linalg.solve(A, b)
            w = solution[:n]
        else:
            # 简化：使用二次规划
            w = self._solve_qp_with_return(Sigma, mu, target_return)

        expected_return = w @ mu
        risk = np.sqrt(w @ Sigma @ w)
        sharpe = (expected_return - self.risk_free_rate) / risk if risk > 0 else 0

        return PortfolioResult(
            weights=w,
            expected_return=expected_return,
            risk=risk,
            sharpe_ratio=sharpe,
        )

    def _solve_qp_no_short(
        self,
        Q: np.ndarray,
        c: np.ndarray,
    ) -> np.ndarray:
        """求解二次规划（无卖空约束）的简化版本"""
        n = len(c)
        w = np.ones(n) / n  # 初始等权重

        # 简单的投影梯度下降
        learning_rate = 0.01
        for _ in range(1000):
            grad = Q @ w
            w = w - learning_rate * grad

            # 投影到单纯形
            w = np.maximum(0, w)
            w = w / np.sum(w)

        return w

    def _solve_qp_with_return(
        self,
        Q: np.ndarray,
        mu: np.ndarray,
        target_return: float,
    ) -> np.ndarray:
        """求解带收益约束的二次规划"""
        n = len(mu)
        w = np.ones(n) / n

        # 简单的投影梯度下降
        learning_rate = 0.01
        for _ in range(1000):
            grad = Q @ w
            w = w - learning_rate * grad

            # 投影到约束集
            w = np.maximum(0, w)
            w = w / np.sum(w)

            # 调整以满足收益约束（简化处理）
            current_return = w @ mu
            if abs(current_return - target_return) > 0.01:
                # 简单调整
                diff = target_return - current_return
                w = w + diff * mu / np.sum(mu ** 2)
                w = np.maximum(0, w)
                w = w / np.sum(w)

        return w

    def _solve_max_sharpe_no_short(
        self,
        Q: np.ndarray,
        excess_returns: np.ndarray,
    ) -> np.ndarray:
        """求解最大夏普比率（无卖空约束）"""
        n = len(excess_returns)
        w = np.ones(n) / n

        # 简单的梯度上升
        learning_rate = 0.01
        for _ in range(1000):
            risk = np.sqrt(w @ Q @ w)
            if risk < 1e-10:
                break

            # 夏普比率的梯度
            ret = w @ excess_returns
            grad = (excess_returns * risk - ret * Q @ w / risk) / (risk ** 2)

            w = w + learning_rate * grad
            w = np.maximum(0, w)
            w = w / np.sum(w)

        return w

    def risk_parity(self) -> PortfolioResult:
        """风险平价组合

        每个资产对组合风险的贡献相等。
        """
        n = self.n_assets
        Sigma = self.cov_matrix

        # 使用迭代算法
        w = np.ones(n) / n

        for _ in range(1000):
            risk = np.sqrt(w @ Sigma @ w)
            marginal_risk = Sigma @ w / risk
            risk_contrib = w * marginal_risk

            # 目标：每个资产的风险贡献相等
            target_risk = risk / n
            w = w * (target_risk / risk_contrib) ** 0.5
            w = w / np.sum(w)

        expected_return = w @ self.mean_returns
        risk = np.sqrt(w @ Sigma @ w)
        sharpe = (expected_return - self.risk_free_rate) / risk if risk > 0 else 0

        return PortfolioResult(
            weights=w,
            expected_return=expected_return,
            risk=risk,
            sharpe_ratio=sharpe,
        )

    def black_litterman(
        self,
        views_matrix: np.ndarray,
        views_returns: np.ndarray,
        tau: float = 0.05,
        omega: Optional[np.ndarray] = None,
    ) -> PortfolioResult:
        """Black-Litterman 模型

        结合市场均衡和投资者观点。

        Args:
            views_matrix: 观点矩阵 P
            views_returns: 观点收益向量 Q
            tau: 不确定性参数
            omega: 观点不确定性矩阵
        """
        n = self.n_assets
        Sigma = self.cov_matrix

        # 市场均衡收益（假设等权重）
        w_market = np.ones(n) / n
        pi = tau * Sigma @ w_market

        # 观点不确定性
        if omega is None:
            omega = np.diag(np.diag(tau * views_matrix @ Sigma @ views_matrix.T))

        # 后验收益
        M1 = np.linalg.inv(np.linalg.inv(tau * Sigma) + views_matrix.T @ np.linalg.inv(omega) @ views_matrix)
        posterior_returns = M1 @ (np.linalg.inv(tau * Sigma) @ pi + views_matrix.T @ np.linalg.inv(omega) @ views_returns)

        # 使用后验收益优化
        w = self._solve_qp_no_short(Sigma, -posterior_returns)

        expected_return = w @ self.mean_returns
        risk = np.sqrt(w @ Sigma @ w)
        sharpe = (expected_return - self.risk_free_rate) / risk if risk > 0 else 0

        return PortfolioResult(
            weights=w,
            expected_return=expected_return,
            risk=risk,
            sharpe_ratio=sharpe,
        )
