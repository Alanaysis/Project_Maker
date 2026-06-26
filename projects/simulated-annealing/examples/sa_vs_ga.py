#!/usr/bin/env python3
"""
与遗传算法对比 (Comparison with Genetic Algorithm)

对比模拟退火 (SA) 和遗传算法 (GA) 在优化问题上的表现。

两种算法的特点：
- SA: 单点搜索，通过温度控制探索/利用平衡
- GA: 种群搜索，通过选择/交叉/变异进化

对比维度：
- 收敛速度
- 解的质量
- 参数敏感性
- 适用场景
"""

import random
import math
import sys
import os
from typing import List, Tuple, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import SimulatedAnnealing, SAResult
from src.temperature import ExponentialScheduler
from src.neighborhood import continuous_neighbor


# ============================================================
# 遗传算法实现 (简化版)
# ============================================================

class GeneticAlgorithm:
    """简化版遗传算法"""

    def __init__(
        self,
        population_size: int = 100,
        chromosome_length: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        bounds: Tuple[float, float] = (-5.12, 5.12),
        seed: int = 42,
    ):
        self.population_size = population_size
        self.chromosome_length = chromosome_length
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.bounds = bounds
        self.seed = seed
        random.seed(seed)

    def _decode_chromosome(self, chromosome: List[int]) -> float:
        """将染色体解码为实数"""
        low, high = self.bounds
        # 将二进制染色体映射到 [low, high]
        binary_str = "".join(str(b) for b in chromosome)
        integer_val = int(binary_str, 2)
        max_val = 2 ** self.chromosome_length - 1
        return low + (high - low) * integer_val / max_val

    def _encode_chromosome(self, value: float) -> List[int]:
        """将实数编码为染色体"""
        low, high = self.bounds
        max_val = 2 ** self.chromosome_length - 1
        normalized = (value - low) / (high - low)
        integer_val = int(round(normalized * max_val))
        integer_val = max(0, min(max_val, integer_val))
        binary_str = format(integer_val, f"0{self.chromosome_length}b")
        return [int(c) for c in binary_str]

    def _create_individual(self) -> List[int]:
        """创建随机个体"""
        return [random.randint(0, 1) for _ in range(self.chromosome_length)]

    def _crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """单点交叉"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        point = random.randint(1, self.chromosome_length - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2

    def _mutate(self, chromosome: List[int]) -> List[int]:
        """位变异"""
        mutated = chromosome.copy()
        for i in range(len(mutated)):
            if random.random() < self.mutation_rate:
                mutated[i] = 1 - mutated[i]
        return mutated

    def _tournament_selection(self, population: List[List[int]], fitness: List[float], k: int = 3) -> List[int]:
        """锦标赛选择"""
        candidates = random.sample(list(zip(population, fitness)), k)
        winner = min(candidates, key=lambda x: x[1])  # 最小化问题
        return winner[0]

    def optimize(
        self,
        objective: Callable,
        name: str = "GA",
        max_generations: int = 500,
    ) -> dict:
        """
        执行遗传算法优化

        Returns:
            包含结果的字典
        """
        # 初始化种群
        population = [self._create_individual() for _ in range(self.population_size)]

        best_chromosome = None
        best_fitness = float("inf")
        fitness_history = []

        for gen in range(max_generations):
            # 评估适应度
            fitness = [self._decode_and_evaluate(ind, objective) for ind in population]

            # 记录最优
            min_idx = min(range(len(fitness)), key=lambda i: fitness[i])
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_chromosome = population[min_idx].copy()

            fitness_history.append(best_fitness)

            # 创建新种群
            new_population = []
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(population, fitness)
                parent2 = self._tournament_selection(population, fitness)
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                new_population.extend([child1, child2])

            population = new_population[: self.population_size]

        best_value = self._decode_chromosome(best_chromosome) if best_chromosome else 0

        return {
            "best_value": best_fitness,
            "best_solution": best_value,
            "fitness_history": fitness_history,
            "generations": max_generations,
            "name": name,
        }

    def _decode_and_evaluate(self, chromosome: List[int], objective: Callable) -> float:
        """解码并评估"""
        if self.chromosome_length == 1:
            value = self._decode_chromosome(chromosome)
        else:
            # 多变量：将染色体分成多段
            dim = self.chromosome_length
            segments = max(1, dim // 2)
            segment_len = (dim + segments - 1) // segments
            values = []
            for i in range(segments):
                start = i * segment_len
                end = min(start + segment_len, dim)
                segment = chromosome[start:end]
                values.append(self._decode_chromosome(segment))
            value = objective(values)
        return value


# ============================================================
# 对比测试
# ============================================================

def sphere_function(x):
    """Sphere 函数"""
    return sum(xi ** 2 for xi in x)


def rastrigin_function(x):
    """Rastrigin 函数"""
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def rosenbrock_function(x):
    """Rosenbrock 函数"""
    return sum(100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2 for i in range(len(x) - 1))


def run_comparison(
    objective: Callable,
    name: str,
    dim: int = 5,
    bounds: Tuple[float, float] = (-5.12, 5.12),
    n_runs: int = 10,
) -> dict:
    """
    运行 SA 和 GA 的对比测试

    Args:
        objective: 目标函数
        name: 函数名称
        dim: 维度
        bounds: 搜索范围
        n_runs: 运行次数

    Returns:
        对比结果
    """
    print(f"\n{'=' * 60}")
    print(f"对比测试: {name} (维度={dim}, 运行次数={n_runs})")
    print(f"{'=' * 60}")

    # SA 结果
    sa_results = []
    for run in range(n_runs):
        sa = SimulatedAnnealing(
            initial_temp=1000.0,
            min_temp=1e-10,
            cooling_rate=0.99,
            iterations_per_temp=100,
            seed=run,
        )

        initial_sol = [random.uniform(bounds[0], bounds[1]) for _ in range(dim)]

        def neighbor_gen(sol):
            return continuous_neighbor(sol, magnitude=1.0)

        result = sa.optimize(
            objective=objective,
            initial_solution=initial_sol,
            neighbor_generator=neighbor_gen,
        )
        sa_results.append(result.best_energy)

    # GA 结果
    ga_results = []
    ga_chrom_len = dim * 20
    ga_pop_size = 100
    for run in range(n_runs):
        ga = GeneticAlgorithm(
            population_size=ga_pop_size,
            chromosome_length=ga_chrom_len,
            mutation_rate=0.1,
            crossover_rate=0.8,
            bounds=bounds,
            seed=run,
        )
        ga_result = ga.optimize(objective=objective, name="GA", max_generations=500)
        ga_results.append(ga_result["best_value"])

    # 统计
    sa_mean = sum(sa_results) / len(sa_results)
    sa_std = (sum((x - sa_mean) ** 2 for x in sa_results) / len(sa_results)) ** 0.5
    ga_mean = sum(ga_results) / len(ga_results)
    ga_std = (sum((x - ga_mean) ** 2 for x in ga_results) / len(ga_results)) ** 0.5

    print(f"\n{'算法':<15} {'平均':>15} {'标准差':>15} {'最优':>15} {'最差':>15}")
    print("-" * 65)
    print(
        f"{'SA':<15} {sa_mean:>15.8f} {sa_std:>15.8f} "
        f"{min(sa_results):>15.8f} {max(sa_results):>15.8f}"
    )
    print(
        f"{'GA':<15} {ga_mean:>15.8f} {ga_std:>15.8f} "
        f"{min(ga_results):>15.8f} {max(ga_results):>15.8f}"
    )

    winner = "SA" if sa_mean < ga_mean else "GA"
    print(f"\n胜者: {winner} (平均能量更低)")

    return {
        "name": name,
        "sa_mean": sa_mean,
        "sa_std": sa_std,
        "ga_mean": ga_mean,
        "ga_std": ga_std,
        "sa_best": min(sa_results),
        "ga_best": min(ga_results),
        "winner": winner,
    }


def main():
    """主函数：运行对比测试"""
    print("=" * 60)
    print("模拟退火 vs 遗传算法 - 对比测试")
    print("=" * 60)

    test_functions = [
        (sphere_function, "Sphere", 5),
        (rastrigin_function, "Rastrigin", 5),
        (rosenbrock_function, "Rosenbrock", 5),
    ]

    results = []
    for func, name, dim in test_functions:
        result = run_comparison(func, name, dim=dim, n_runs=10)
        results.append(result)

    # 总结
    print(f"\n{'=' * 60}")
    print("总结")
    print(f"{'=' * 60}")
    print(f"{'函数':<15} {'SA 平均':>12} {'GA 平均':>12} {'胜者':>10}")
    print("-" * 55)
    for r in results:
        print(f"{r['name']:<15} {r['sa_mean']:>12.6f} {r['ga_mean']:>12.6f} {r['winner']:>10}")

    sa_wins = sum(1 for r in results if r["winner"] == "SA")
    ga_wins = sum(1 for r in results if r["winner"] == "GA")
    print(f"\nSA 获胜: {sa_wins}/{len(results)}")
    print(f"GA 获胜: {ga_wins}/{len(results)}")


if __name__ == "__main__":
    main()
