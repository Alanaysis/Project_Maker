"""测试函数基类 - 所有测试函数的基础接口"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, List


class TestFunction(ABC):
    """测试函数基类

    所有测试函数都应继承此类并实现 __call__ 和 gradient 方法。
    """

    def __init__(self, name: str, ndim: int = 2):
        """初始化测试函数

        Args:
            name: 函数名称
            ndim: 维度
        """
        self.name = name
        self.ndim = ndim

    @abstractmethod
    def __call__(self, x: np.ndarray) -> float:
        """计算函数值

        Args:
            x: 输入点

        Returns:
            函数值
        """
        pass

    @abstractmethod
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """计算梯度

        Args:
            x: 输入点

        Returns:
            梯度向量
        """
        pass

    @abstractmethod
    def minimum(self) -> Tuple[np.ndarray, float]:
        """返回理论最小值点和最小值

        Returns:
            (最小值点, 最小值)
        """
        pass

    @abstractmethod
    def initial_point(self) -> np.ndarray:
        """返回初始点

        Returns:
            初始点
        """
        pass

    def hessian(self, x: np.ndarray) -> np.ndarray:
        """计算海森矩阵（可选实现）

        Args:
            x: 输入点

        Returns:
            海森矩阵
        """
        raise NotImplementedError(f"{self.name} 不支持海森矩阵计算")

    def search_range(self) -> List[Tuple[float, float]]:
        """返回搜索范围

        Returns:
            每个维度的搜索范围 [(min, max), ...]
        """
        return [(-5, 5)] * self.ndim

    def is_minimum(self, x: np.ndarray, tol: float = 1e-6) -> bool:
        """检查是否接近最小值

        Args:
            x: 输入点
            tol: 容差

        Returns:
            是否接近最小值
        """
        min_x, min_val = self.minimum()
        return np.linalg.norm(x - min_x) < tol

    def __repr__(self) -> str:
        """返回函数的字符串表示"""
        return f"{self.__class__.__name__}(name='{self.name}', ndim={self.ndim})"
