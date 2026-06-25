"""Himmelblau 函数 - 多模态优化测试函数"""

import numpy as np
from typing import Tuple, List
from .base import TestFunction


class HimmelblauFunction(TestFunction):
    """Himmelblau 函数 (Himmelblau's Function)

    经典的多模态优化测试函数，有四个全局最小值。

    数学表达:
        f(x, y) = (x^2 + y - 11)^2 + (x + y^2 - 7)^2

    特点:
        - 非凸函数
        - 有四个全局最小值点：
          (3, 2), (-2.805118, 3.131312), (-3.779310, -3.283186), (3.584428, -1.848126)
        - 所有最小值 f(x) = 0
        - 适合测试多起点优化

    Args:
        无参数
    """

    def __init__(self):
        """初始化 Himmelblau 函数"""
        super().__init__('himmelblau', ndim=2)

    def __call__(self, x: np.ndarray) -> float:
        """计算函数值

        Args:
            x: 输入点 [x, y]

        Returns:
            函数值
        """
        x = np.asarray(x)
        return (x[0]**2 + x[1] - 11)**2 + (x[0] + x[1]**2 - 7)**2

    def gradient(self, x: np.ndarray) -> np.ndarray:
        """计算梯度

        Args:
            x: 输入点 [x, y]

        Returns:
            梯度向量 [df/dx, df/dy]
        """
        x = np.asarray(x)
        dx = 4 * x[0] * (x[0]**2 + x[1] - 11) + 2 * (x[0] + x[1]**2 - 7)
        dy = 2 * (x[0]**2 + x[1] - 11) + 4 * x[1] * (x[0] + x[1]**2 - 7)
        return np.array([dx, dy])

    def minimum(self) -> Tuple[np.ndarray, float]:
        """返回理论最小值点和最小值

        返回第一个最小值点 (3, 2)

        Returns:
            (最小值点, 最小值)
        """
        return np.array([3.0, 2.0]), 0.0

    def all_minima(self) -> List[np.ndarray]:
        """返回所有最小值点

        Returns:
            所有最小值点列表
        """
        return [
            np.array([3.0, 2.0]),
            np.array([-2.805118, 3.131312]),
            np.array([-3.779310, -3.283186]),
            np.array([3.584428, -1.848126])
        ]

    def initial_point(self) -> np.ndarray:
        """返回初始点

        Returns:
            初始点
        """
        return np.array([0.0, 0.0])

    def search_range(self) -> List[Tuple[float, float]]:
        """返回搜索范围

        Returns:
            每个维度的搜索范围
        """
        return [(-5, 5), (-5, 5)]

    def __repr__(self) -> str:
        """返回函数的字符串表示"""
        return "HimmelblauFunction()"
