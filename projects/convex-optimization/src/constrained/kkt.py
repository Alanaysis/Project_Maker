"""
KKT 条件

实现 KKT 条件检验和相关工具。
"""

import numpy as np
from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class KKTResult:
    """KKT 条件检验结果"""

    stationarity: bool  # 平稳性条件
    primal_feasibility: bool  # 原始可行性
    dual_feasibility: bool  # 对偶可行性
    complementary_slackness: bool  # 互补松弛性
    is_satisfied: bool  # 是否满足所有 KKT 条件
    violation: float  # 违背程度


class KKTChecker:
    """KKT 条件检验器

    对于问题：
    min f(x)
    s.t. g_i(x) ≤ 0, i = 1, ..., m
         h_j(x) = 0, j = 1, ..., p

    KKT 条件：
    1. 平稳性: ∇f(x*) + Σ λ_i ∇g_i(x*) + Σ ν_j ∇h_j(x*) = 0
    2. 原始可行性: g_i(x*) ≤ 0, h_j(x*) = 0
    3. 对偶可行性: λ_i ≥ 0
    4. 互补松弛性: λ_i g_i(x*) = 0
    """

    def __init__(
        self,
        grad_obj: Callable,
        grad_eq: List[Callable] = None,
        grad_ineq: List[Callable] = None,
        eq_constraints: List[Callable] = None,
        ineq_constraints: List[Callable] = None,
        tol: float = 1e-6,
    ):
        self.grad_obj = grad_obj
        self.grad_eq = grad_eq or []
        self.grad_ineq = grad_ineq or []
        self.eq_constraints = eq_constraints or []
        self.ineq_constraints = ineq_constraints or []
        self.tol = tol

    def check_stationarity(
        self,
        x: np.ndarray,
        lambda_ineq: np.ndarray,
        nu_eq: np.ndarray,
    ) -> Tuple[bool, float]:
        """检查平稳性条件

        ∇f(x*) + Σ λ_i ∇g_i(x*) + Σ ν_j ∇h_j(x*) = 0
        """
        grad = self.grad_obj(x).copy()  # 复制以避免修改原数组

        # 加上不等式约束的贡献
        for i, grad_g in enumerate(self.grad_ineq):
            grad += lambda_ineq[i] * grad_g(x)

        # 加上等式约束的贡献
        for j, grad_h in enumerate(self.grad_eq):
            grad += nu_eq[j] * grad_h(x)

        violation = np.linalg.norm(grad)
        return violation < self.tol, violation

    def check_primal_feasibility(self, x: np.ndarray) -> Tuple[bool, float]:
        """检查原始可行性

        g_i(x*) ≤ 0, h_j(x*) = 0
        """
        max_violation = 0.0

        # 检查不等式约束
        for g in self.ineq_constraints:
            gx = g(x)
            if gx > self.tol:
                max_violation = max(max_violation, gx)

        # 检查等式约束
        for h in self.eq_constraints:
            hx = h(x)
            max_violation = max(max_violation, abs(hx))

        return max_violation < self.tol, max_violation

    def check_dual_feasibility(self, lambda_ineq: np.ndarray) -> Tuple[bool, float]:
        """检查对偶可行性

        λ_i ≥ 0
        """
        violation = np.sum(np.maximum(0, -lambda_ineq))
        return violation < self.tol, violation

    def check_complementary_slackness(
        self,
        x: np.ndarray,
        lambda_ineq: np.ndarray,
    ) -> Tuple[bool, float]:
        """检查互补松弛性

        λ_i g_i(x*) = 0
        """
        max_violation = 0.0

        for i, g in enumerate(self.ineq_constraints):
            product = lambda_ineq[i] * g(x)
            max_violation = max(max_violation, abs(product))

        return max_violation < self.tol, max_violation

    def check(
        self,
        x: np.ndarray,
        lambda_ineq: np.ndarray,
        nu_eq: np.ndarray,
    ) -> KKTResult:
        """检查所有 KKT 条件"""
        stat_ok, stat_viol = self.check_stationarity(x, lambda_ineq, nu_eq)
        primal_ok, primal_viol = self.check_primal_feasibility(x)
        dual_ok, dual_viol = self.check_dual_feasibility(lambda_ineq)
        comp_ok, comp_viol = self.check_complementary_slackness(x, lambda_ineq)

        total_violation = stat_viol + primal_viol + dual_viol + comp_viol

        return KKTResult(
            stationarity=stat_ok,
            primal_feasibility=primal_ok,
            dual_feasibility=dual_ok,
            complementary_slackness=comp_ok,
            is_satisfied=stat_ok and primal_ok and dual_ok and comp_ok,
            violation=total_violation,
        )


def verify_kkt_for_qp(
    Q: np.ndarray,
    c: np.ndarray,
    A: np.ndarray = None,
    b: np.ndarray = None,
    G: np.ndarray = None,
    h: np.ndarray = None,
    x: np.ndarray = None,
    lambda_ineq: np.ndarray = None,
    nu_eq: np.ndarray = None,
) -> KKTResult:
    """验证二次规划的 KKT 条件

    问题：
    min 0.5 x^T Q x + c^T x
    s.t. A x = b
         G x ≤ h

    KKT 条件：
    Q x + c + A^T ν + G^T λ = 0
    A x = b
    G x ≤ h
    λ ≥ 0
    λ_i (G x - h)_i = 0
    """
    n = len(x)
    violations = []

    # 平稳性
    grad = Q @ x + c
    if nu_eq is not None and A is not None:
        grad += A.T @ nu_eq
    if lambda_ineq is not None and G is not None:
        grad += G.T @ lambda_ineq
    stat_viol = np.linalg.norm(grad)

    # 原始可行性
    primal_viol = 0.0
    if A is not None and b is not None:
        primal_viol += np.linalg.norm(A @ x - b)
    if G is not None and h is not None:
        slack = G @ x - h
        primal_viol += np.sum(np.maximum(0, slack))

    # 对偶可行性
    dual_viol = 0.0
    if lambda_ineq is not None:
        dual_viol = np.sum(np.maximum(0, -lambda_ineq))

    # 互补松弛性
    comp_viol = 0.0
    if lambda_ineq is not None and G is not None and h is not None:
        slack = G @ x - h
        comp_viol = np.sum(np.abs(lambda_ineq * slack))

    total_violation = stat_viol + primal_viol + dual_viol + comp_viol
    tol = 1e-6

    return KKTResult(
        stationarity=stat_viol < tol,
        primal_feasibility=primal_viol < tol,
        dual_feasibility=dual_viol < tol,
        complementary_slackness=comp_viol < tol,
        is_satisfied=total_violation < tol,
        violation=total_violation,
    )
