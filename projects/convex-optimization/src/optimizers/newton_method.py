"""
牛顿法

实现标准牛顿法和阻尼牛顿法。
"""

import numpy as np
from typing import Callable, Optional
from .base_optimizer import BaseOptimizer


class NewtonMethod(BaseOptimizer):
    """牛顿法

    x_{k+1} = x_k - [∇²f(x_k)]^{-1} ∇f(x_k)

    支持：
    - 标准牛顿法
    - 阻尼牛顿法（带线搜索）
    - 正则化牛顿法（处理非正定海森矩阵）
    """

    def __init__(
        self,
        damping: float = 0.0,
        regularization: float = 1e-6,
        use_line_search: bool = True,
        max_iter: int = 100,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.damping = damping
        self.regularization = regularization
        self.use_line_search = use_line_search

    def solve_newton_system(
        self,
        H: np.ndarray,
        g: np.ndarray,
    ) -> np.ndarray:
        """求解牛顿方程 H * d = -g

        使用 Cholesky 分解或 LDL 分解处理不定矩阵。
        """
        n = len(g)

        # 添加正则化项确保正定
        H_reg = H + self.regularization * np.eye(n)

        try:
            # 尝试 Cholesky 分解
            L = np.linalg.cholesky(H_reg)
            d = np.linalg.solve(L, -g)
            d = np.linalg.solve(L.T, d)
        except np.linalg.LinAlgError:
            # 使用 LDL 分解
            d = np.linalg.solve(H_reg, -g)

        return d

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
        hessian: Optional[Callable] = None,
    ) -> np.ndarray:
        g = grad(x)

        if hessian is None:
            raise ValueError("牛顿法需要海森矩阵")

        H = hessian(x)

        # 求解牛顿方向
        d = self.solve_newton_system(H, g)

        # 阻尼或线搜索
        if self.use_line_search:
            alpha = super().line_search(x, d, func, grad)
        elif self.damping > 0:
            alpha = self.damping
        else:
            alpha = 1.0

        return x + alpha * d

    def optimize(
        self,
        func: Callable,
        grad: Callable,
        x0: np.ndarray,
        hessian: Optional[Callable] = None,
    ):
        """重写优化方法以支持海森矩阵"""
        x = np.atleast_1d(x0.copy()).astype(float)
        trajectory = [x.copy()]
        grad_norms = []
        nfev = 0

        for i in range(self.max_iter):
            g = grad(x)
            grad_norm = np.linalg.norm(g)
            grad_norms.append(grad_norm)
            nfev += 1

            if self.verbose and i % 10 == 0:
                print(f"Iter {i:4d}: f={func(x):.6e}, ||g||={grad_norm:.6e}")

            # 收敛检查
            if grad_norm < self.tol:
                from .base_optimizer import OptimizationResult

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
            x = self.step(x, func, grad, hessian)
            trajectory.append(x.copy())

        from .base_optimizer import OptimizationResult

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


class TrustRegionNewton(BaseOptimizer):
    """信赖域牛顿法

    在信赖域内求解牛顿步，更稳定。
    """

    def __init__(
        self,
        initial_radius: float = 1.0,
        max_radius: float = 10.0,
        eta: float = 0.1,
        max_iter: int = 100,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.radius = initial_radius
        self.max_radius = max_radius
        self.eta = eta

    def solve_trust_region(
        self,
        g: np.ndarray,
        H: np.ndarray,
        radius: float,
    ) -> np.ndarray:
        """求解信赖域子问题

        min_d  g^T d + 0.5 * d^T H d
        s.t.   ||d|| ≤ radius
        """
        n = len(g)

        # 尝试精确牛顿步
        try:
            d = np.linalg.solve(H, -g)
            if np.linalg.norm(d) <= radius:
                return d
        except np.linalg.LinAlgError:
            pass

        # 使用 Cauchy 点
        gHg = g @ H @ g
        if gHg > 0:
            tau = min(1.0, np.linalg.norm(g) ** 3 / (radius * gHg))
        else:
            tau = 1.0

        d = -tau * radius * g / np.linalg.norm(g)
        return d

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
        hessian: Optional[Callable] = None,
    ) -> np.ndarray:
        g = grad(x)
        H = hessian(x)

        # 求解信赖域子问题
        d = self.solve_trust_region(g, H, self.radius)

        # 计算实际下降与预测下降的比值
        f_current = func(x)
        f_new = func(x + d)
        actual_decrease = f_current - f_new
        predicted_decrease = -(g @ d + 0.5 * d @ H @ d)

        if predicted_decrease > 0:
            rho = actual_decrease / predicted_decrease
        else:
            rho = 0

        # 更新信赖域半径
        if rho < 0.25:
            self.radius *= 0.25
        elif rho > 0.75 and np.linalg.norm(d) >= 0.9 * self.radius:
            self.radius = min(2 * self.radius, self.max_radius)

        # 接受或拒绝步长
        if rho > self.eta:
            return x + d
        else:
            return x

    def optimize(
        self,
        func: Callable,
        grad: Callable,
        x0: np.ndarray,
        hessian: Optional[Callable] = None,
    ):
        """重写优化方法以支持海森矩阵"""
        x = np.atleast_1d(x0.copy()).astype(float)
        trajectory = [x.copy()]
        grad_norms = []
        nfev = 0

        for i in range(self.max_iter):
            g = grad(x)
            grad_norm = np.linalg.norm(g)
            grad_norms.append(grad_norm)
            nfev += 1

            if self.verbose and i % 10 == 0:
                print(f"Iter {i:4d}: f={func(x):.6e}, ||g||={grad_norm:.6e}")

            # 收敛检查
            if grad_norm < self.tol:
                from .base_optimizer import OptimizationResult

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
            x = self.step(x, func, grad, hessian)
            trajectory.append(x.copy())

        from .base_optimizer import OptimizationResult

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
