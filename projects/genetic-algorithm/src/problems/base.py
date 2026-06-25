"""
优化问题基类
"""

from abc import ABC, abstractmethod
from typing import Any, List


class Problem(ABC):
    """
    优化问题基类

    所有优化问题都应继承此类并实现抽象方法
    """

    @abstractmethod
    def create_individual(self) -> List[Any]:
        """
        创建随机个体（染色体）

        Returns:
            随机生成的染色体
        """
        pass

    @abstractmethod
    def fitness(self, chromosome: List[Any]) -> float:
        """
        计算适应度

        Args:
            chromosome: 染色体

        Returns:
            适应度值（越高越好）
        """
        pass

    @abstractmethod
    def display(self, chromosome: List[Any]) -> None:
        """
        显示解

        Args:
            chromosome: 染色体
        """
        pass
