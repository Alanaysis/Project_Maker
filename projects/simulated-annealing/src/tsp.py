"""
旅行商问题（TSP）实现

实现TSP问题的：
- 问题定义
- 邻域操作
- 距离计算
"""

import numpy as np
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class City:
    """城市坐标"""
    x: float
    y: float
    name: str = ""


class TSP:
    """
    旅行商问题

    实现TSP问题的核心逻辑：
    - 城市管理
    - 路径评估
    - 邻域操作

    参数:
        cities: 城市坐标列表
    """

    def __init__(self, cities: List[City]):
        self.cities = cities
        self.n_cities = len(cities)
        self.distance_matrix = self._calculate_distance_matrix()

    def _calculate_distance_matrix(self) -> np.ndarray:
        """计算城市间距离矩阵"""
        n = self.n_cities
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                dist = self._calculate_distance(
                    self.cities[i], self.cities[j]
                )
                matrix[i][j] = dist
                matrix[j][i] = dist
        return matrix

    def _calculate_distance(self, city1: City, city2: City) -> float:
        """计算两个城市之间的欧几里得距离"""
        return np.sqrt(
            (city1.x - city2.x) ** 2 +
            (city1.y - city2.y) ** 2
        )

    def calculate_total_distance(self, path: List[int]) -> float:
        """
        计算路径的总距离

        参数:
            path: 路径（城市索引列表）

        返回:
            总距离
        """
        total_distance = 0
        n = len(path)
        for i in range(n):
            from_city = path[i]
            to_city = path[(i + 1) % n]  # 回到起点
            total_distance += self.distance_matrix[from_city][to_city]
        return total_distance

    def random_neighbor(self, path: List[int]) -> List[int]:
        """
        生成随机邻域解

        使用2-opt交换：随机选择两个位置并交换

        参数:
            path: 当前路径

        返回:
            新路径
        """
        new_path = path.copy()
        n = len(new_path)

        # 随机选择两个不同的位置
        i, j = sorted(np.random.choice(n, 2, replace=False))

        # 反转子路径
        new_path[i:j + 1] = reversed(new_path[i:j + 1])

        return new_path

    def or_opt_neighbor(self, path: List[int]) -> List[int]:
        """
        Or-opt邻域操作

        将一段连续的城市移动到另一个位置

        参数:
            path: 当前路径

        返回:
            新路径
        """
        new_path = path.copy()
        n = len(new_path)

        # 随机选择要移动的段长度（1-3个城市）
        seg_len = np.random.randint(1, min(4, n))
        seg_start = np.random.randint(0, n - seg_len)
        insert_pos = np.random.randint(0, n - seg_len)

        # 提取段
        segment = new_path[seg_start:seg_start + seg_len]
        remaining = new_path[:seg_start] + new_path[seg_start + seg_len:]

        # 插入到新位置
        new_path = remaining[:insert_pos] + segment + remaining[insert_pos:]

        return new_path

    def generate_random_solution(self) -> List[int]:
        """生成随机初始解"""
        solution = list(range(self.n_cities))
        np.random.shuffle(solution)
        return solution

    @staticmethod
    def create_random_instance(n_cities: int, seed: int = None) -> 'TSP':
        """
        创建随机TSP实例

        参数:
            n_cities: 城市数量
            seed: 随机种子

        返回:
            TSP实例
        """
        if seed is not None:
            np.random.seed(seed)

        cities = []
        for i in range(n_cities):
            x = np.random.uniform(0, 100)
            y = np.random.uniform(0, 100)
            cities.append(City(x, y, f"City_{i}"))

        return TSP(cities)


def example_tsp():
    """TSP示例"""
    print("旅行商问题（TSP）示例")
    print("-" * 40)

    # 创建城市
    cities = [
        City(0, 0, "A"),
        City(10, 0, "B"),
        City(10, 10, "C"),
        City(0, 10, "D"),
        City(5, 5, "E"),
    ]

    # 创建TSP实例
    tsp = TSP(cities)

    # 生成随机解
    solution = tsp.generate_random_solution()
    distance = tsp.calculate_total_distance(solution)

    print(f"城市数量: {tsp.n_cities}")
    print(f"随机路径: {solution}")
    print(f"总距离: {distance:.2f}")

    # 测试邻域操作
    new_solution = tsp.random_neighbor(solution)
    new_distance = tsp.calculate_total_distance(new_solution)

    print(f"\n邻域操作后:")
    print(f"新路径: {new_solution}")
    print(f"新距离: {new_distance:.2f}")
    print(f"距离变化: {new_distance - distance:.2f}")

    return tsp, solution


if __name__ == "__main__":
    example_tsp()
