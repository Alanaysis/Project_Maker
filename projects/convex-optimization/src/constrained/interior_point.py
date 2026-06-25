"""
内点法

实现原始-对偶内点法和障碍函数法。
"""

import numpy as np
from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class InteriorPointResult:
    """内点法求解结果"""

    x: np.ndarray  # 最优解
    fun: float  # 最优函数值
    nit: int  # 迭代次数
    success: bool  # 是否收敛
    message: str  # 收敛信息
    lambda_ineq: np.ndarray  # 不等式约束乘子
    nu_eq: np.ndarray  # 等式约束乘子


class BarrierMethod:
    """障碍函数法（内点法）

    将约束问题转化为一系列无约束问题：
    min f(x) - (1/t) Σ log(-g_i(x))
    """

    def __init__(
        self,
        objective: Callable,
        grad_obj: Callable,
        ineq_constraints: List[Callable],
        grad_ineq: List[Callable] = None,
        eq_constraints: List[Callable] = None,
        grad_eq: List[Callable] = None,
        t0: float = 1.0,
        mu: float = 10.0,
        max_iter: int = 100,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        self.objective = objective
        self.grad_obj = grad_obj
        self.ineq_constraints = ineq_constraints
        self.grad_ineq = grad_ineq or []
        self.eq_constraints = eq_constraints or []
        self.grad_eq = grad_eq or []
        self.t0 = t0
        self.mu = mu
        self.max_iter = max_iter
        self.tol = tol
        self.verbose = verbose

    def barrier_function(self, x: np.ndarray, t: float) -> float:
        """障碍函数

        φ(x) = f(x) - (1/t) Σ log(-g_i(x))
        """
        result = self.objective(x)

        for g in self.ineq_constraints:
            gx = g(x)
            if gx >= 0:
                return np.inf  # 不可行
            result -= np.log(-gx) / t

        return result

    def barrier_gradient(self, x: np.ndarray, t: float) -> np.ndarray:
        """障碍函数的梯度"""
        grad = self.grad_obj(x)

        for i, g in enumerate(self.ineq_constraints):
            gx = g(x)
            if gx >= 0:
                return np.full_like(x, np.inf)
            grad -= self.grad_ineq[i](x) / (t * gx)

        return grad

    def solve_barrier_problem(
        self,
        x0: np.ndarray,
        t: float,
    ) -> np.ndarray:
        """求解障碍问题

        使用牛顿法求解 min φ(x)
        """
        x = x0.copy()

        for _ in range(50):  # 内层迭代
            grad = self.barrier_gradient(x, t)
            grad_norm = np.linalg.norm(grad)

            if grad_norm < self.tol:
                break

            # 简单梯度下降（实际应该用牛顿法）
            learning_rate = 0.01
            x = x - learning_rate * grad

            # 确保在可行域内
            for g in self.ineq_constraints:
                if g(x) >= 0:
                    x = x0.copy()  # 回退
                    break

        return x

    def solve(self, x0: np.ndarray) -> InteriorPointResult:
        """求解约束优化问题"""
        x = x0.copy()
        t = self.t0

        for i in range(self.max_iter):
            # 求解障碍问题
            x = self.solve_barrier_problem(x, t)

            # 检查收敛
            gap = len(self.ineq_constraints) / t
            if self.verbose:
                print(f"Iter {i}: t={t:.2e}, gap={gap:.2e}")

            if gap < self.tol:
                # 计算乘子
                lambda_ineq = np.zeros(len(self.ineq_constraints))
                for j, g in enumerate(self.ineq_constraints):
                    lambda_ineq[j] = 1.0 / (t * (-g(x)))

                return InteriorPointResult(
                    x=x,
                    fun=self.objective(x),
                    nit=i,
                    success=True,
                    message=f"收敛: 对偶间隙 {gap:.2e}",
                    lambda_ineq=lambda_ineq,
                    nu_eq=np.zeros(len(self.eq_constraints)),
                )

            # 增加 t
            t *= self.mu

        return InteriorPointResult(
            x=x,
            fun=self.objective(x),
            nit=self.max_iter,
            success=False,
            message=f"达到最大迭代次数 {self.max_iter}",
            lambda_ineq=np.zeros(len(self.ineq_constraints)),
            nu_eq=np.zeros(len(self.eq_constraints)),
        )


class PrimalDualInteriorPoint:
    """原始-对偶内点法

    同时更新原始变量和对偶变量，更稳定。
    """

    def __init__(
        self,
        objective: Callable,
        grad_obj: Callable,
        hessian_obj: Callable,
        ineq_constraints: List[Callable],
        grad_ineq: List[Callable],
        hessian_ineq: List[Callable] = None,
        eq_constraints: List[Callable] = None,
        grad_eq: List[Callable] = None,
        max_iter: int = 100,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        self.objective = objective
        self.grad_obj = grad_obj
        self.hessian_obj = hessian_obj
        self.ineq_constraints = ineq_constraints
        self.grad_ineq = grad_ineq
        self.hessian_ineq = hessian_ineq or []
        self.eq_constraints = eq_constraints or []
        self.grad_eq = grad_eq or []
        self.max_iter = max_iter
        self.tol = tol
        self.verbose = verbose

    def solve(
        self,
        x0: np.ndarray,
        lambda0: np.ndarray = None,
        nu0: np.ndarray = None,
    ) -> InteriorPointResult:
        """求解约束优化问题"""
        n = len(x0)
        m = len(self.ineq_constraints)
        p = len(self.eq_constraints)

        x = x0.copy()
        if lambda0 is not None:
            lam = lambda0.copy()
        else:
            lam = np.ones(m)
        if nu0 is not None:
            nu = nu0.copy()
        else:
            nu = np.zeros(p)

        for iteration in range(self.max_iter):
            # 计算残差
            # 平稳性残差
            r_dual = self.grad_obj(x)
            for i in range(m):
                r_dual += lam[i] * self.grad_ineq[i](x)
            for j in range(p):
                r_dual += nu[j] * self.grad_eq[j](x)

            # 原始可行性残差
            r_pri = np.zeros(p)
            for j in range(p):
                r_pri[j] = self.eq_constraints[j](x)

            # 互补性残差
            r_comp = np.zeros(m)
            for i in range(m):
                r_comp[i] = lam[i] * self.ineq_constraints[i](x)

            # 检查收敛
            residual = np.linalg.norm(r_dual) + np.linalg.norm(r_pri) + np.linalg.norm(r_comp)
            if self.verbose and iteration % 10 == 0:
                print(f"Iter {iteration}: residual={residual:.2e}")

            if residual < self.tol:
                return InteriorPointResult(
                    x=x,
                    fun=self.objective(x),
                    nit=iteration,
                    success=True,
                    message=f"收敛: 残差 {residual:.2e}",
                    lambda_ineq=lam,
                    nu_eq=nu,
                )

            # 构建 KKT 系统
            # H = ∇²f + Σ λ_i ∇²g_i
            H = self.hessian_obj(x)
            for i in range(m):
                if i < len(self.hessian_ineq):
                    H += lam[i] * self.hessian_ineq[i](x)

            # 构建雅可比矩阵
            A = np.zeros((p, n))
            for j in range(p):
                A[j] = self.grad_eq[j](x)

            G = np.zeros((m, n))
            for i in range(m):
                G[i] = self.ineq_constraints[i](x)

            # 简化的牛顿步（实际应该求解完整 KKT 系统）
            # 这里使用简化的更新
            alpha = 0.01
            x = x - alpha * r_dual[:n]
            lam = np.maximum(0, lam - alpha * r_comp)
            nu = nu - alpha * r_pri

        return InteriorPointResult(
            x=x,
            fun=self.objective(x),
            nit=self.max_iter,
            success=False,
            message=f"达到最大迭代次数 {self.max_iter}",
            lambda_ineq=lam,
            nu_eq=nu,
        )
