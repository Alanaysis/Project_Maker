"""
遗传算法 - 收敛检测模块
Genetic Algorithm - Convergence Detection Module

Works with the pre-existing Population class from src.core.population.
"""

from typing import Optional, List
from src.core.individual import Individual
from src.core.population import Population


class ConvergenceDetector:
    """收敛检测器基类"""
    def check_convergence(self, population: Population, generation: int,
                          history: Optional[List[float]] = None) -> bool:
        raise NotImplementedError


class DiversityConvergenceDetector(ConvergenceDetector):
    """
    基于多样性的收敛检测

    当种群的平均基因距离低于阈值时，认为种群已收敛。
    """
    def __init__(self, threshold: float = 1e-6, window_size: int = 10):
        self.threshold = threshold
        self.window_size = window_size
        self.diversity_history: List[float] = []

    def check_convergence(self, population: Population, generation: int,
                          history: Optional[List[float]] = None) -> bool:
        diversity = self._compute_diversity(population)
        self.diversity_history.append(diversity)

        if len(self.diversity_history) > self.window_size:
            self.diversity_history.pop(0)

        avg_diversity = sum(self.diversity_history) / len(self.diversity_history)
        return avg_diversity < self.threshold

    @staticmethod
    def _compute_diversity(population: Population) -> float:
        individuals = population.individuals
        if len(individuals) < 2:
            return 0.0

        total_distance = 0.0
        count = 0

        for i in range(len(individuals)):
            for j in range(i + 1, len(individuals)):
                c1 = individuals[i].chromosome
                c2 = individuals[j].chromosome
                if len(c1) != len(c2):
                    continue
                if isinstance(c1[0], (int, float)) if c1 else False:
                    total_distance += sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5
                else:
                    total_distance += sum(1 for a, b in zip(c1, c2) if a != b)
                count += 1

        return total_distance / count if count > 0 else 0.0


class FitnessGainConvergenceDetector(ConvergenceDetector):
    """
    基于适应度增益的收敛检测

    当连续多代最佳适应度的提升小于阈值时，认为收敛。
    """
    def __init__(self, threshold: float = 1e-6, patience: int = 50):
        self.threshold = threshold
        self.patience = patience
        self.stagnation_count: int = 0

    def check_convergence(self, population: Population, generation: int,
                          history: Optional[List[float]] = None) -> bool:
        best_fitness = max((ind.fitness for ind in population.individuals), default=float('-inf'))

        if history is None:
            history = []

        if len(history) >= self.patience:
            history.pop(0)
        history.append(best_fitness)

        if len(history) >= 2:
            gain = abs(history[-1] - history[-2])
            if gain < self.threshold:
                self.stagnation_count += 1
            else:
                self.stagnation_count = 0

            if self.stagnation_count >= self.patience:
                return True

        return False


class CombinedConvergenceDetector(ConvergenceDetector):
    """
    组合收敛检测器

    结合多样性和适应度增益两种检测策略。
    """
    def __init__(self, diversity_threshold: float = 1e-6,
                 fitness_threshold: float = 1e-6,
                 patience: int = 50,
                 diversity_window: int = 10):
        self.diversity_detector = DiversityConvergenceDetector(
            threshold=diversity_threshold, window_size=diversity_window
        )
        self.fitness_detector = FitnessGainConvergenceDetector(
            threshold=fitness_threshold, patience=patience
        )
        self.history: List[float] = []

    def check_convergence(self, population: Population, generation: int,
                          history: Optional[List[float]] = None) -> bool:
        if history is None:
            history = self.history

        diversity_converged = self.diversity_detector.check_convergence(
            population, generation, history
        )
        fitness_converged = self.fitness_detector.check_convergence(
            population, generation, history
        )

        return diversity_converged or fitness_converged


class GenerationLimitDetector(ConvergenceDetector):
    """
    固定代数终止检测器
    """
    def __init__(self, max_generations: int = 1000):
        self.max_generations = max_generations

    def check_convergence(self, population: Population, generation: int,
                          history: Optional[List[float]] = None) -> bool:
        return generation >= self.max_generations


def get_convergence_detector(name: str, **kwargs) -> ConvergenceDetector:
    """工厂函数：获取收敛检测器"""
    detectors = {
        'diversity': DiversityConvergenceDetector,
        'fitness_gain': FitnessGainConvergenceDetector,
        'combined': CombinedConvergenceDetector,
        'generation_limit': GenerationLimitDetector,
    }

    if name not in detectors:
        raise ValueError(f"Unknown convergence detector: {name}. "
                         f"Available: {list(detectors.keys())}")

    return detectors[name](**kwargs)
