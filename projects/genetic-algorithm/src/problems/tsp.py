"""
旅行商问题 (TSP) 实现
"""

from typing import Any, List, Tuple
import random
import numpy as np

from .base import Problem


class TSPProblem(Problem):
    """
    旅行商问题

    给定一组城市和每对城市之间的距离，找到访问每个城市一次并返回起点的最短路径。
    """

    def __init__(self, cities: List[Tuple[float, float]]):
        """
        初始化 TSP 问题

        Args:
            cities: 城市坐标列表，每个城市为 (x, y) 元组
        """
        self.cities = cities
        self.n_cities = len(cities)
        self.distance_matrix = self._calculate_distance_matrix()

    def _calculate_distance_matrix(self) -> np.ndarray:
        """
        计算城市间距离矩阵

        Returns:
            距离矩阵
        """
        matrix = np.zeros((self.n_cities, self.n_cities))
        for i in range(self.n_cities):
            for j in range(i + 1, self.n_cities):
                dist = np.sqrt(
                    (self.cities[i][0] - self.cities[j][0]) ** 2 +
                    (self.cities[i][1] - self.cities[j][1]) ** 2
                )
                matrix[i][j] = dist
                matrix[j][i] = dist
        return matrix

    def create_individual(self) -> List[int]:
        """
        创建随机路径

        Returns:
            随机排列的城市访问顺序
        """
        route = list(range(self.n_cities))
        random.shuffle(route)
        return route

    def fitness(self, chromosome: List[int]) -> float:
        """
        计算适应度（路径长度的倒数）

        Args:
            chromosome: 城市访问顺序

        Returns:
            适应度值（路径越短，适应度越高）
        """
        distance = self.calculate_distance(chromosome)
        if distance == 0:
            return float('inf')
        return 1.0 / distance

    def calculate_distance(self, route: List[int]) -> float:
        """
        计算路径总长度

        Args:
            route: 城市访问顺序

        Returns:
            路径总长度
        """
        total = 0.0
        for i in range(len(route)):
            from_city = route[i]
            to_city = route[(i + 1) % len(route)]
            total += self.distance_matrix[from_city][to_city]
        return total

    def display(self, chromosome: List[int]) -> None:
        """
        显示路径

        Args:
            chromosome: 城市访问顺序
        """
        distance = self.calculate_distance(chromosome)
        print(f"Route: {chromosome}")
        print(f"Total distance: {distance:.2f}")

    @staticmethod
    def generate_random_cities(n: int, width: float = 100.0, height: float = 100.0) -> List[Tuple[float, float]]:
        """
        生成随机城市

        Args:
            n: 城市数量
            width: 区域宽度
            height: 区域高度

        Returns:
            随机城市坐标列表
        """
        return [(random.uniform(0, width), random.uniform(0, height)) for _ in range(n)]

    @staticmethod
    def generate_circle_cities(n: int, radius: float = 50.0) -> List[Tuple[float, float]]:
        """
        生成圆形分布的城市

        Args:
            n: 城市数量
            radius: 圆的半径

        Returns:
            圆形分布的城市坐标列表
        """
        cities = []
        for i in range(n):
            angle = 2 * np.pi * i / n
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            cities.append((x, y))
        return cities
