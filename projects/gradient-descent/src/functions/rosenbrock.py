"""Rosenbrock 函数 - 经典优化测试函数"""

import numpy as np
from typing import Tuple, List
from .base import TestFunction


class RosenbrockFunction(TestFunction):
    """Rosenbrock 函数 (Rosenbrock Function)

    经典的优化测试函数，也称为"香蕉函数"。

    数学表达:
        f(x, y) = (a - x)^2 + b * (y - x^2)^2

    其中通常 a = 1, b = 100。

    特点:
        - 非凸函数
        - 有狭长的"峡谷"
        - 全局最小值在 (1, 1)
        - 优化难度大，需要算法能够处理峡谷型地形

    Args:
        a: 参数 a (默认 1)
        b: 参数 b (默认 100)
    """

    def __init__(self, a: float = 1.0, b: float = 100.0):
        """初始化 Rosenbrock 函数

        Args:
            a: 参数 a (默认 1)
            b: 参数 b (默认 100)
        """
        super().__init__('rosenbrock', ndim=2)
        self.a = a
        self.b = b

    def __call__(self, x: np.ndarray) -> float:
        """计算函数值

        Args:
            x: 输入点 [x, y]

        Returns:
            函数值
        """
        x = np.asarray(x)
        return (self.a - x[0])**2 + self.b * (x[1] - x[0]**2)**2

    def gradient(self, x: np.ndarray) -> np.ndarray:
        """计算梯度

        Args:
            x: 输入点 [x, y]

        Returns:
            梯度向量 [df/dx, df/dy]
        """
        x = np.asarray(x)
        dx = -2 * (self.a - x[0]) - 4 * self.b * x[0] * (x[1] - x[0]**2)
        dy = 2 * self.b * (x[1] - x[0]**2)
        return np.array([dx, dy])

    def minimum(self) -> Tuple[np.ndarray, float]:
        """返回理论最小值点和最小值

        Returns:
            (最小值点, 最小值)
        """
        return np.array([self.a, self.a**2]), 0.0

    def initial_point(self) -> np.ndarray:
        """返回初始点

        Returns:
            初始点
        """
        return np.array([-1.0, 1.0])

    def search_range(self) -> List[Tuple[float, float]]:
        """返回搜索范围

        Returns:
            每个维度的搜索范围
        """
        return [(-2, 2), (-1, 3)]

    def hessian(self, x: np.ndarray) -> np.ndarray:
        """计算海森矩阵

        Args:
            x: 输入点 [x, y]

        Returns:
            海森矩阵
        """
        x = np.asarray(x)
        h11 = 2 - 4 * self.b * (x[1] - 3 * x[0]**2)
        h12 = -4 * self.b * x[0]
        h22 = 2 * self.b
        return np.array([[h11, h12], [h12, h22]])

    def __repr__(self) -> str:
        """返回函数的字符串表示"""
        return f"RosenbrockFunction(a={self.a}, b={self.b})"
