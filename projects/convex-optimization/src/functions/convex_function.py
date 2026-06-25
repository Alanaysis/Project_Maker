"""
凸函数基类

提供凸性判断、强凸性检验、次梯度计算等功能。
"""

import numpy as np
from typing import Callable, Optional, Tuple
from abc import ABC, abstractmethod


class ConvexFunction(ABC):
    """凸函数基类

    所有凸函数应继承此类并实现基本方法。
    """

    @abstractmethod
    def __call__(self, x: np.ndarray) -> float:
        """计算函数值 f(x)"""
        pass

    @abstractmethod
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """计算梯度 ∇f(x)"""
        pass

    def hessian(self, x: np.ndarray) -> Optional[np.ndarray]:
        """计算海森矩阵 ∇²f(x)，默认返回 None（不可用）"""
        return None

    def subgradient(self, x: np.ndarray) -> np.ndarray:
        """计算次梯度（对于非光滑函数），默认使用梯度"""
        return self.gradient(x)

    def is_convex_by_definition(
        self,
        x: np.ndarray,
        y: np.ndarray,
        alpha: float = 0.5,
        num_samples: int = 100,
    ) -> bool:
        """通过定义判断凸性

        检查 f(αx + (1-α)y) ≤ αf(x) + (1-α)f(y)
        """
        for _ in range(num_samples):
            a = np.random.uniform(0, 1)
            z = a * x + (1 - a) * y
            lhs = self(z)
            rhs = a * self(x) + (1 - a) * self(y)
            if lhs > rhs + 1e-8:
                return False
        return True

    def is_convex_by_hessian(self, x: np.ndarray) -> bool:
        """通过海森矩阵判断凸性

        检查海森矩阵是否半正定（所有特征值 ≥ 0）
        """
        H = self.hessian(x)
        if H is None:
            raise ValueError("海森矩阵不可用")
        eigenvalues = np.linalg.eigvalsh(H)
        return np.all(eigenvalues >= -1e-8)

    def is_strongly_convex(
        self, x: np.ndarray, mu: float
    ) -> bool:
        """判断是否为强凸函数

        检查海森矩阵特征值是否都 ≥ μ
        """
        H = self.hessian(x)
        if H is None:
            raise ValueError("海森矩阵不可用")
        eigenvalues = np.linalg.eigvalsh(H)
        return np.all(eigenvalues >= mu - 1e-8)

    def lipschitz_constant(
        self,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        num_samples: int = 1000,
    ) -> float:
        """估计梯度的 Lipschitz 常数 L

        L = max ||∇f(x) - ∇f(y)|| / ||x - y||
        """
        max_ratio = 0.0
        for _ in range(num_samples):
            x = np.random.uniform(x_range[0], x_range[1])
            y = np.random.uniform(y_range[0], y_range[1])
            grad_diff = np.linalg.norm(self.gradient(x) - self.gradient(y))
            point_diff = np.linalg.norm(x - y)
            if point_diff > 1e-10:
                max_ratio = max(max_ratio, grad_diff / point_diff)
        return max_ratio

    def descent_lemma(
        self,
        x: np.ndarray,
        y: np.ndarray,
        L: float,
    ) -> bool:
        """验证下降引理

        f(y) ≤ f(x) + ∇f(x)^T(y - x) + L/2 ||y - x||²
        """
        lhs = self(y)
        rhs = (
            self(x)
            + self.gradient(x) @ (y - x)
            + L / 2 * np.linalg.norm(y - x) ** 2
        )
        return lhs <= rhs + 1e-8
