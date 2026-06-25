"""
最小二乘问题

实现普通最小二乘、岭回归、Lasso 回归。
"""

import numpy as np
from typing import Optional, Tuple


class LeastSquares:
    """普通最小二乘

    min ||Ax - b||²

    解析解: x = (A^T A)^{-1} A^T b
    """

    def __init__(self, A: np.ndarray, b: np.ndarray):
        self.A = np.atleast_2d(A)
        self.b = np.atleast_1d(b)
        self.m, self.n = self.A.shape

    def solve_analytical(self) -> np.ndarray:
        """解析解"""
        return np.linalg.lstsq(self.A, self.b, rcond=None)[0]

    def solve_gradient_descent(
        self,
        x0: Optional[np.ndarray] = None,
        learning_rate: float = 0.01,
        max_iter: int = 1000,
        tol: float = 1e-6,
    ) -> np.ndarray:
        """梯度下降求解"""
        if x0 is None:
            x0 = np.zeros(self.n)

        x = x0.copy()
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b

        for _ in range(max_iter):
            grad = AtA @ x - Atb
            if np.linalg.norm(grad) < tol:
                break
            x = x - learning_rate * grad

        return x

    def solve_normal_equations(self) -> np.ndarray:
        """正规方程求解"""
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b
        return np.linalg.solve(AtA, Atb)

    def solve_qr(self) -> np.ndarray:
        """QR 分解求解"""
        Q, R = np.linalg.qr(self.A)
        return np.linalg.solve(R, Q.T @ self.b)

    def solve_svd(self) -> np.ndarray:
        """SVD 分解求解"""
        U, s, Vt = np.linalg.svd(self.A, full_matrices=False)
        return Vt.T @ (np.diag(1 / s) @ (U.T @ self.b))

    def residual(self, x: np.ndarray) -> np.ndarray:
        """计算残差"""
        return self.A @ x - self.b

    def cost(self, x: np.ndarray) -> float:
        """计算目标函数值"""
        r = self.residual(x)
        return 0.5 * np.sum(r ** 2)


class RidgeRegression:
    """岭回归（L2 正则化）

    min ||Ax - b||² + λ||x||²

    解析解: x = (A^T A + λI)^{-1} A^T b
    """

    def __init__(self, A: np.ndarray, b: np.ndarray, lambda_: float = 1.0):
        self.A = np.atleast_2d(A)
        self.b = np.atleast_1d(b)
        self.lambda_ = lambda_
        self.m, self.n = self.A.shape

    def solve_analytical(self) -> np.ndarray:
        """解析解"""
        AtA = self.A.T @ self.A + self.lambda_ * np.eye(self.n)
        Atb = self.A.T @ self.b
        return np.linalg.solve(AtA, Atb)

    def solve_gradient_descent(
        self,
        x0: Optional[np.ndarray] = None,
        learning_rate: float = 0.01,
        max_iter: int = 1000,
        tol: float = 1e-6,
    ) -> np.ndarray:
        """梯度下降求解"""
        if x0 is None:
            x0 = np.zeros(self.n)

        x = x0.copy()
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b

        for _ in range(max_iter):
            grad = AtA @ x - Atb + self.lambda_ * x
            if np.linalg.norm(grad) < tol:
                break
            x = x - learning_rate * grad

        return x

    def cost(self, x: np.ndarray) -> float:
        """计算目标函数值"""
        residual = self.A @ x - self.b
        return 0.5 * np.sum(residual ** 2) + 0.5 * self.lambda_ * np.sum(x ** 2)


class LassoRegression:
    """Lasso 回归（L1 正则化）

    min ||Ax - b||² + λ||x||₁

    使用坐标下降法或近端梯度法求解。
    """

    def __init__(self, A: np.ndarray, b: np.ndarray, lambda_: float = 1.0):
        self.A = np.atleast_2d(A)
        self.b = np.atleast_1d(b)
        self.lambda_ = lambda_
        self.m, self.n = self.A.shape

    def soft_threshold(self, x: np.ndarray, threshold: float) -> np.ndarray:
        """软阈值函数"""
        return np.sign(x) * np.maximum(0, np.abs(x) - threshold)

    def solve_coordinate_descent(
        self,
        x0: Optional[np.ndarray] = None,
        max_iter: int = 1000,
        tol: float = 1e-6,
    ) -> np.ndarray:
        """坐标下降法求解"""
        if x0 is None:
            x0 = np.zeros(self.n)

        x = x0.copy()

        # 预计算 A^T A 和 A^T b
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b

        for _ in range(max_iter):
            x_old = x.copy()

            for j in range(self.n):
                # 计算残差（排除第 j 个特征）
                residual = Atb[j] - AtA[j] @ x + AtA[j, j] * x[j]

                # 软阈值更新
                if abs(residual) > self.lambda_:
                    x[j] = np.sign(residual) * (abs(residual) - self.lambda_) / AtA[j, j]
                else:
                    x[j] = 0

            # 检查收敛
            if np.linalg.norm(x - x_old) < tol:
                break

        return x

    def solve_proximal_gradient(
        self,
        x0: Optional[np.ndarray] = None,
        learning_rate: float = 0.001,
        max_iter: int = 1000,
        tol: float = 1e-6,
    ) -> np.ndarray:
        """近端梯度法求解"""
        if x0 is None:
            x0 = np.zeros(self.n)

        x = x0.copy()
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b

        for _ in range(max_iter):
            # 梯度步
            grad = AtA @ x - Atb
            z = x - learning_rate * grad

            # 近端步（软阈值）
            x_new = self.soft_threshold(z, learning_rate * self.lambda_)

            # 检查收敛
            if np.linalg.norm(x_new - x) < tol:
                x = x_new
                break

            x = x_new

        return x

    def cost(self, x: np.ndarray) -> float:
        """计算目标函数值"""
        residual = self.A @ x - self.b
        return 0.5 * np.sum(residual ** 2) + self.lambda_ * np.sum(np.abs(x))


class ElasticNetRegression:
    """弹性网络回归

    min ||Ax - b||² + λ₁||x||₁ + 0.5λ₂||x||²
    """

    def __init__(
        self,
        A: np.ndarray,
        b: np.ndarray,
        lambda1: float = 1.0,
        lambda2: float = 1.0,
    ):
        self.A = np.atleast_2d(A)
        self.b = np.atleast_1d(b)
        self.lambda1 = lambda1
        self.lambda2 = lambda2
        self.m, self.n = self.A.shape

    def solve_coordinate_descent(
        self,
        x0: Optional[np.ndarray] = None,
        max_iter: int = 1000,
        tol: float = 1e-6,
    ) -> np.ndarray:
        """坐标下降法求解"""
        if x0 is None:
            x0 = np.zeros(self.n)

        x = x0.copy()
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b

        for _ in range(max_iter):
            x_old = x.copy()

            for j in range(self.n):
                residual = Atb[j] - AtA[j] @ x + AtA[j, j] * x[j]
                denominator = AtA[j, j] + self.lambda2

                if abs(residual) > self.lambda1:
                    x[j] = np.sign(residual) * (abs(residual) - self.lambda1) / denominator
                else:
                    x[j] = 0

            if np.linalg.norm(x - x_old) < tol:
                break

        return x

    def cost(self, x: np.ndarray) -> float:
        """计算目标函数值"""
        residual = self.A @ x - self.b
        return (
            0.5 * np.sum(residual ** 2)
            + self.lambda1 * np.sum(np.abs(x))
            + 0.5 * self.lambda2 * np.sum(x ** 2)
        )
