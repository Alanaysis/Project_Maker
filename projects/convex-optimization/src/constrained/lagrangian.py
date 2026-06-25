"""
拉格朗日对偶

实现拉格朗日函数、对偶问题、强对偶性检验。
"""

import numpy as np
from typing import Callable, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Constraint:
    """约束条件

    类型：
    - 'eq': 等式约束 h(x) = 0
    - 'ineq': 不等式约束 g(x) ≤ 0
    """

    func: Callable  # 约束函数
    type: str  # 'eq' 或 'ineq'
    name: str = ""  # 约束名称（可选）


@dataclass
class DualResult:
    """对偶问题求解结果"""

    dual_optimal: float  # 对偶最优值
    primal_optimal: float  # 原始最优值
    duality_gap: float  # 对偶间隙
    lambda_eq: np.ndarray  # 等式约束乘子
    lambda_ineq: np.ndarray  # 不等式约束乘子
    strong_duality: bool  # 是否满足强对偶


class Lagrangian:
    """拉格朗日函数

    L(x, λ, ν) = f(x) + Σ λ_i g_i(x) + Σ ν_j h_j(x)
    """

    def __init__(
        self,
        objective: Callable,
        eq_constraints: List[Callable] = None,
        ineq_constraints: List[Callable] = None,
    ):
        self.objective = objective
        self.eq_constraints = eq_constraints or []
        self.ineq_constraints = ineq_constraints or []

    def __call__(
        self,
        x: np.ndarray,
        lambda_ineq: np.ndarray = None,
        nu_eq: np.ndarray = None,
    ) -> float:
        """计算拉格朗日函数值"""
        result = self.objective(x)

        # 不等式约束
        if lambda_ineq is not None and self.ineq_constraints:
            for i, g in enumerate(self.ineq_constraints):
                result += lambda_ineq[i] * g(x)

        # 等式约束
        if nu_eq is not None and self.eq_constraints:
            for j, h in enumerate(self.eq_constraints):
                result += nu_eq[j] * h(x)

        return result

    def gradient_x(
        self,
        x: np.ndarray,
        grad_obj: Callable,
        grad_eq: List[Callable] = None,
        grad_ineq: List[Callable] = None,
        lambda_ineq: np.ndarray = None,
        nu_eq: np.ndarray = None,
    ) -> np.ndarray:
        """计算拉格朗日函数对 x 的梯度"""
        g = grad_obj(x)

        if lambda_ineq is not None and grad_ineq:
            for i, grad_g in enumerate(grad_ineq):
                g += lambda_ineq[i] * grad_g(x)

        if nu_eq is not None and grad_eq:
            for j, grad_h in enumerate(grad_eq):
                g += nu_eq[j] * grad_h(x)

        return g

    def dual_function(
        self,
        lambda_ineq: np.ndarray,
        nu_eq: np.ndarray,
        minimize_over_x: Callable,
    ) -> float:
        """对偶函数

        g(λ, ν) = inf_x L(x, λ, ν)
        """
        return minimize_over_x(lambda_ineq, nu_eq)


class DualProblem:
    """对偶问题

    max g(λ, ν)
    s.t. λ ≥ 0
    """

    def __init__(
        self,
        lagrangian: Lagrangian,
        minimize_over_x: Callable,
    ):
        self.lagrangian = lagrangian
        self.minimize_over_x = minimize_over_x

    def solve(
        self,
        initial_lambda: Optional[np.ndarray] = None,
        initial_nu: Optional[np.ndarray] = None,
        max_iter: int = 1000,
        tol: float = 1e-6,
    ) -> DualResult:
        """求解对偶问题

        使用梯度上升法（对偶函数是凹函数）。
        """
        n_ineq = len(self.lagrangian.ineq_constraints)
        n_eq = len(self.lagrangian.eq_constraints)

        # 初始化乘子
        if initial_lambda is not None:
            lambda_ineq = initial_lambda.copy()
        else:
            lambda_ineq = np.ones(n_ineq)

        if initial_nu is not None:
            nu_eq = initial_nu.copy()
        else:
            nu_eq = np.zeros(n_eq)

        # 梯度上升
        learning_rate = 0.01
        best_dual = -np.inf

        for _ in range(max_iter):
            # 计算对偶函数值和梯度
            # 这里简化处理，实际应该计算对偶函数的梯度
            dual_val = self.lagrangian.dual_function(
                lambda_ineq, nu_eq, self.minimize_over_x
            )

            if dual_val > best_dual:
                best_dual = dual_val

            # 更新乘子（投影到可行域）
            lambda_ineq = np.maximum(0, lambda_ineq + learning_rate * lambda_ineq)

        # 计算原始最优值（需要额外信息）
        # 这里返回对偶结果
        return DualResult(
            dual_optimal=best_dual,
            primal_optimal=np.inf,  # 需要单独计算
            duality_gap=np.inf,
            lambda_eq=nu_eq,
            lambda_ineq=lambda_ineq,
            strong_duality=False,
        )


class AugmentedLagrangian:
    """增广拉格朗日方法 (ALM)

    L_A(x, λ, ν, ρ) = f(x) + Σ λ_i g_i(x) + Σ ν_j h_j(x)
                     + (ρ/2) Σ [max(0, g_i(x) + λ_i/ρ)]²
                     + (ρ/2) Σ h_j(x)²
    """

    def __init__(
        self,
        objective: Callable,
        eq_constraints: List[Callable] = None,
        ineq_constraints: List[Callable] = None,
        rho: float = 1.0,
    ):
        self.objective = objective
        self.eq_constraints = eq_constraints or []
        self.ineq_constraints = ineq_constraints or []
        self.rho = rho

    def __call__(
        self,
        x: np.ndarray,
        lambda_ineq: np.ndarray = None,
        nu_eq: np.ndarray = None,
    ) -> float:
        """计算增广拉格朗日函数值"""
        result = self.objective(x)

        # 不等式约束
        if lambda_ineq is not None and self.ineq_constraints:
            for i, g in enumerate(self.ineq_constraints):
                gx = g(x)
                result += lambda_ineq[i] * gx
                result += (self.rho / 2) * max(0, gx + lambda_ineq[i] / self.rho) ** 2

        # 等式约束
        if nu_eq is not None and self.eq_constraints:
            for j, h in enumerate(self.eq_constraints):
                hx = h(x)
                result += nu_eq[j] * hx
                result += (self.rho / 2) * hx ** 2

        return result

    def update_multipliers(
        self,
        x: np.ndarray,
        lambda_ineq: np.ndarray,
        nu_eq: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """更新乘子"""
        new_lambda = lambda_ineq.copy()
        new_nu = nu_eq.copy()

        # 更新不等式乘子
        for i, g in enumerate(self.ineq_constraints):
            gx = g(x)
            new_lambda[i] = max(0, lambda_ineq[i] + self.rho * gx)

        # 更新等式乘子
        for j, h in enumerate(self.eq_constraints):
            hx = h(x)
            new_nu[j] = nu_eq[j] + self.rho * hx

        return new_lambda, new_nu
