"""
优化器基类

定义优化器的基本接口和通用功能。
"""

import numpy as np
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class OptimizationResult:
    """优化结果"""

    x: np.ndarray  # 最优解
    fun: float  # 最优函数值
    nit: int  # 迭代次数
    nfev: int  # 函数评估次数
    success: bool  # 是否收敛
    message: str  # 收敛信息
    trajectory: List[np.ndarray] = field(default_factory=list)  # 迭代轨迹
    grad_norms: List[float] = field(default_factory=list)  # 梯度范数历史


class BaseOptimizer(ABC):
    """优化器基类"""

    def __init__(
        self,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        self.max_iter = max_iter
        self.tol = tol
        self.verbose = verbose

    @abstractmethod
    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        """执行一步优化"""
        pass

    def line_search(
        self,
        x: np.ndarray,
        direction: np.ndarray,
        func: Callable,
        grad: Callable,
        alpha: float = 1.0,
        c1: float = 1e-4,
        c2: float = 0.9,
        max_ls: int = 50,
    ) -> float:
        """Armijo 线搜索

        满足 Wolfe 条件的步长选择。
        """
        f0 = func(x)
        g0 = grad(x)
        directional_grad = g0 @ direction

        for _ in range(max_ls):
            x_new = x + alpha * direction
            f_new = func(x_new)

            # Armijo 条件
            if f_new <= f0 + c1 * alpha * directional_grad:
                # 曲率条件（弱 Wolfe）
                g_new = grad(x_new)
                if g_new @ direction >= c2 * directional_grad:
                    return alpha

            alpha *= 0.5

        return alpha

    def optimize(
        self,
        func: Callable,
        grad: Callable,
        x0: np.ndarray,
        hessian: Optional[Callable] = None,
    ) -> OptimizationResult:
        """执行优化

        Args:
            func: 目标函数
            grad: 梯度函数
            x0: 初始点
            hessian: 海森矩阵函数（可选）

        Returns:
            OptimizationResult: 优化结果
        """
        x = np.atleast_1d(x0.copy()).astype(float)
        trajectory = [x.copy()]
        grad_norms = []
        nfev = 0

        for i in range(self.max_iter):
            g = grad(x)
            grad_norm = np.linalg.norm(g)
            grad_norms.append(grad_norm)
            nfev += 1

            if self.verbose and i % 100 == 0:
                print(f"Iter {i:4d}: f={func(x):.6e}, ||g||={grad_norm:.6e}")

            # 收敛检查
            if grad_norm < self.tol:
                return OptimizationResult(
                    x=x,
                    fun=func(x),
                    nit=i,
                    nfev=nfev,
                    success=True,
                    message=f"梯度范数收敛: {grad_norm:.2e} < {self.tol:.2e}",
                    trajectory=trajectory,
                    grad_norms=grad_norms,
                )

            # 执行一步优化
            x = self.step(x, func, grad)
            trajectory.append(x.copy())

        return OptimizationResult(
            x=x,
            fun=func(x),
            nit=self.max_iter,
            nfev=nfev,
            success=False,
            message=f"达到最大迭代次数 {self.max_iter}",
            trajectory=trajectory,
            grad_norms=grad_norms,
        )
