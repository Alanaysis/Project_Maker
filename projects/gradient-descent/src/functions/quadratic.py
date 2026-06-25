"""二次函数 - 简单的凸优化测试函数"""

import numpy as np
from typing import Tuple, List
from .base import TestFunction


class QuadraticFunction(TestFunction):
    """二次函数 (Quadratic Function)

    最简单的凸优化测试函数，用于验证优化算法的基本功能。

    数学表达:
        f(x) = 0.5 * x^T A x + b^T x + c

    或者简化形式:
        f(x, y) = a * (x - x0)^2 + b * (y - y0)^2

    特点:
        - 凸函数
        - 有唯一最小值
        - 梯度是线性的

    Args:
        a: x 方向的系数 (默认 1)
        b: y 方向的系数 (默认 1)
        center: 最小值点 (默认 [0, 0])
    """

    def __init__(
        self,
        a: float = 1.0,
        b: float = 1.0,
        center: np.ndarray = None
    ):
        """初始化二次函数

        Args:
            a: x 方向的系数
            b: y 方向的系数
            center: 最小值点
        """
        super().__init__('quadratic', ndim=2)
        self.a = a
        self.b = b
        self.center = center if center is not None else np.zeros(2)

    def __call__(self, x: np.ndarray) -> float:
        """计算函数值

        Args:
            x: 输入点 [x, y]

        Returns:
            函数值
        """
        x = np.asarray(x)
        dx = x[0] - self.center[0]
        dy = x[1] - self.center[1]
        return 0.5 * (self.a * dx**2 + self.b * dy**2)

    def gradient(self, x: np.ndarray) -> np.ndarray:
        """计算梯度

        Args:
            x: 输入点 [x, y]

        Returns:
            梯度向量 [df/dx, df/dy]
        """
        x = np.asarray(x)
        dx = x[0] - self.center[0]
        dy = x[1] - self.center[1]
        return np.array([self.a * dx, self.b * dy])

    def minimum(self) -> Tuple[np.ndarray, float]:
        """返回理论最小值点和最小值

        Returns:
            (最小值点, 最小值)
        """
        return self.center.copy(), 0.0

    def initial_point(self) -> np.ndarray:
        """返回初始点

        Returns:
            初始点
        """
        return np.array([3.0, 3.0])

    def search_range(self) -> List[Tuple[float, float]]:
        """返回搜索范围

        Returns:
            每个维度的搜索范围
        """
        return [(-5, 5), (-5, 5)]

    def __repr__(self) -> str:
        """返回函数的字符串表示"""
        return (
            f"QuadraticFunction(a={self.a}, b={self.b}, "
            f"center={self.center})"
        )


class IllConditionedQuadratic(QuadraticFunction):
    """病态二次函数

    条件数很大的二次函数，用于测试优化算法在病态问题上的表现。

    Args:
        condition_number: 条件数 (b/a)
    """

    def __init__(self, condition_number: float = 100.0):
        """初始化病态二次函数

        Args:
            condition_number: 条件数 (b/a)
        """
        a = 1.0
        b = condition_number
        super().__init__(a=a, b=b)
        self.condition_number = condition_number
        self.name = 'ill_conditioned_quadratic'

    def __repr__(self) -> str:
        """返回函数的字符串表示"""
        return f"IllConditionedQuadratic(condition_number={self.condition_number})"
