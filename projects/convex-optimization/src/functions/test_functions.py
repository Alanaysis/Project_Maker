"""
常用测试函数

包含二次函数、Rosenbrock 函数、逻辑损失、Huber 损失等。
"""

import numpy as np
from typing import Optional
from .convex_function import ConvexFunction


class QuadraticFunction(ConvexFunction):
    """二次函数 f(x) = 0.5 * x^T A x + b^T x + c

    当 A 半正定时为凸函数，正定时为强凸函数。
    """

    def __init__(
        self,
        A: np.ndarray,
        b: Optional[np.ndarray] = None,
        c: float = 0.0,
    ):
        self.A = np.atleast_2d(A)
        n = self.A.shape[0]
        self.b = np.zeros(n) if b is None else np.atleast_1d(b)
        self.c = c

    def __call__(self, x: np.ndarray) -> float:
        x = np.atleast_1d(x)
        return 0.5 * x @ self.A @ x + self.b @ x + self.c

    def gradient(self, x: np.ndarray) -> np.ndarray:
        x = np.atleast_1d(x)
        return self.A @ x + self.b

    def hessian(self, x: np.ndarray) -> np.ndarray:
        return self.A.copy()

    @staticmethod
    def create_diagonal(
        eigenvalues: np.ndarray,
        b: Optional[np.ndarray] = None,
    ) -> "QuadraticFunction":
        """创建对角二次函数"""
        A = np.diag(eigenvalues)
        return QuadraticFunction(A, b)


class RosenbrockFunction(ConvexFunction):
    """Rosenbrock 函数（非凸）

    f(x, y) = (a - x)² + b(y - x²)²
    """

    def __init__(self, a: float = 1.0, b: float = 100.0):
        self.a = a
        self.b = b

    def __call__(self, x: np.ndarray) -> float:
        x = np.atleast_1d(x)
        return (self.a - x[0]) ** 2 + self.b * (x[1] - x[0] ** 2) ** 2

    def gradient(self, x: np.ndarray) -> np.ndarray:
        x = np.atleast_1d(x)
        dx = -2 * (self.a - x[0]) - 4 * self.b * x[0] * (x[1] - x[0] ** 2)
        dy = 2 * self.b * (x[1] - x[0] ** 2)
        return np.array([dx, dy])

    def hessian(self, x: np.ndarray) -> np.ndarray:
        x = np.atleast_1d(x)
        h00 = 2 - 4 * self.b * (x[1] - 3 * x[0] ** 2)
        h01 = -4 * self.b * x[0]
        h10 = -4 * self.b * x[0]
        h11 = 2 * self.b
        return np.array([[h00, h01], [h10, h11]])


class LogisticLoss(ConvexFunction):
    """逻辑损失函数（凸）

    f(w) = (1/n) Σ log(1 + exp(-y_i * w^T x_i))
    """

    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = np.atleast_2d(X)
        self.y = np.atleast_1d(y)
        self.n = len(y)

    def __call__(self, w: np.ndarray) -> float:
        w = np.atleast_1d(w)
        z = -self.y * (self.X @ w)
        return np.mean(np.logaddexp(0, z))

    def gradient(self, w: np.ndarray) -> np.ndarray:
        w = np.atleast_1d(w)
        z = -self.y * (self.X @ w)
        sigma = 1 / (1 + np.exp(-z))
        return -self.X.T @ (self.y * (1 - sigma)) / self.n

    def hessian(self, w: np.ndarray) -> np.ndarray:
        w = np.atleast_1d(w)
        z = -self.y * (self.X @ w)
        sigma = 1 / (1 + np.exp(-z))
        D = sigma * (1 - sigma)
        return (self.X.T * D) @ self.X / self.n


class HuberLoss(ConvexFunction):
    """Huber 损失函数（凸，非光滑）

    L_δ(a) = 0.5 * a²           if |a| ≤ δ
           = δ * (|a| - 0.5δ)  otherwise
    """

    def __init__(self, delta: float = 1.0):
        self.delta = delta

    def __call__(self, x: np.ndarray) -> float:
        x = np.atleast_1d(x)
        result = 0.0
        for xi in x:
            if abs(xi) <= self.delta:
                result += 0.5 * xi ** 2
            else:
                result += self.delta * (abs(xi) - 0.5 * self.delta)
        return result

    def gradient(self, x: np.ndarray) -> np.ndarray:
        x = np.atleast_1d(x)
        grad = np.zeros_like(x)
        for i, xi in enumerate(x):
            if abs(xi) <= self.delta:
                grad[i] = xi
            else:
                grad[i] = self.delta * np.sign(xi)
        return grad

    def subgradient(self, x: np.ndarray) -> np.ndarray:
        """Huber 损失的次梯度（实际上 Huber 损失是可微的）"""
        return self.gradient(x)


class L1Norm(ConvexFunction):
    """L1 范数（凸，非光滑）

    f(x) = ||x||_1
    """

    def __call__(self, x: np.ndarray) -> float:
        return np.sum(np.abs(x))

    def gradient(self, x: np.ndarray) -> np.ndarray:
        raise ValueError("L1 范数在零点不可微，使用 subgradient")

    def subgradient(self, x: np.ndarray) -> np.ndarray:
        """L1 范数的次梯度"""
        return np.sign(x)


class ElasticNet(ConvexFunction):
    """弹性网络（凸）

    f(x) = 0.5 * ||Ax - b||² + λ₁||x||₁ + 0.5λ₂||x||²
    """

    def __init__(
        self,
        A: np.ndarray,
        b: np.ndarray,
        lambda1: float = 0.1,
        lambda2: float = 0.1,
    ):
        self.A = np.atleast_2d(A)
        self.b = np.atleast_1d(b)
        self.lambda1 = lambda1
        self.lambda2 = lambda2

    def __call__(self, x: np.ndarray) -> float:
        x = np.atleast_1d(x)
        residual = self.A @ x - self.b
        return (
            0.5 * np.sum(residual ** 2)
            + self.lambda1 * np.sum(np.abs(x))
            + 0.5 * self.lambda2 * np.sum(x ** 2)
        )

    def gradient(self, x: np.ndarray) -> np.ndarray:
        raise ValueError("弹性网络在零点不可微，使用 subgradient")

    def subgradient(self, x: np.ndarray) -> np.ndarray:
        x = np.atleast_1d(x)
        residual = self.A @ x - self.b
        return (
            self.A.T @ residual
            + self.lambda1 * np.sign(x)
            + self.lambda2 * x
        )
