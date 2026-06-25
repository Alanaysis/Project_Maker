"""
个体类：表示遗传算法中的一个个体（解）
"""

from typing import Any, Callable, List


class Individual:
    """
    表示遗传算法中的一个个体

    每个个体包含一个染色体（问题解的编码）和适应度值
    """

    def __init__(self, chromosome: List[Any]):
        """
        初始化个体

        Args:
            chromosome: 染色体，表示问题解的编码
        """
        self.chromosome = chromosome
        self.fitness = 0.0

    def evaluate(self, fitness_func: Callable[[List[Any]], float]) -> float:
        """
        评估个体适应度

        Args:
            fitness_func: 适应度函数，接受染色体返回适应度值

        Returns:
            适应度值
        """
        self.fitness = fitness_func(self.chromosome)
        return self.fitness

    def copy(self) -> 'Individual':
        """
        深拷贝个体

        Returns:
            新的个体实例，染色体和适应度相同
        """
        new_ind = Individual(self.chromosome.copy())
        new_ind.fitness = self.fitness
        return new_ind

    def __repr__(self) -> str:
        return f"Individual(chromosome={self.chromosome}, fitness={self.fitness:.4f})"

    def __len__(self) -> int:
        return len(self.chromosome)

    def __getitem__(self, index: int) -> Any:
        return self.chromosome[index]

    def __setitem__(self, index: int, value: Any):
        self.chromosome[index] = value
