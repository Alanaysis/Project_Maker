"""
遗传算法 - 参数配置模块
Genetic Algorithm - Parameter Configuration Module

提供 GA 运行参数的集中管理。

GA 关键参数：
    1. 种群大小 (population_size): 50-200
    2. 交叉概率 (crossover_rate): 0.6-0.9
    3. 变异概率 (mutation_rate): 0.01-0.1
    4. 最大代数 (max_generations): 100-1000
    5. 选择方法: tournament/roulette/rank/elitism
    6. 交叉算子: single_point/multi_point/uniform/arithmetic
    7. 变异算子: bit_flip/swap/gaussian/boundary
    8. 精英数量 (elite_count): 1-5
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict


@dataclass
class GAParameters:
    """
    遗传算法参数配置类

    封装所有 GA 运行参数，提供默认值和便捷修改方法。

    Attributes:
        population_size: 种群大小
        crossover_rate: 交叉概率
        mutation_rate: 变异概率
        max_generations: 最大进化代数
        tournament_size: 锦标赛大小（锦标赛选择时有效）
        elite_count: 精英保留数量
        selection_method: 选择方法名称
        crossover_operator: 交叉算子名称
        mutation_operator: 变异算子名称
        crossover_params: 交叉算子额外参数
        mutation_params: 变异算子额外参数
        seed: 随机种子（用于可复现性）
        verbose: 是否打印详细信息
        stop_fitness: 目标适应度（达到即停止，None 表示无上限）
        steady_state_rate: 稳态模式替换率（0-1，默认 0 为世代模式）
    """
    # 种群参数
    population_size: int = 100
    max_generations: int = 500

    # 遗传算子参数
    crossover_rate: float = 0.8
    mutation_rate: float = 0.01

    # 选择参数
    selection_method: str = "tournament"
    tournament_size: int = 3
    elite_count: int = 2

    # 算子名称
    crossover_operator: str = "single_point"
    mutation_operator: str = "bit_flip"

    # 算子额外参数
    crossover_params: Dict[str, Any] = field(default_factory=dict)
    mutation_params: Dict[str, Any] = field(default_factory=dict)

    # 终止条件
    stop_fitness: Optional[float] = None
    convergence_detector: str = "combined"
    convergence_params: Dict[str, Any] = field(default_factory=dict)

    # 运行参数
    seed: Optional[int] = None
    verbose: bool = True
    steady_state_rate: float = 0.0  # 0 = 世代模式, (0, 1] = 稳态模式

    def __post_init__(self):
        # 参数验证
        if self.population_size < 10:
            raise ValueError("population_size must be >= 10")
        if not (0 <= self.crossover_rate <= 1):
            raise ValueError("crossover_rate must be in [0, 1]")
        if not (0 <= self.mutation_rate <= 1):
            raise ValueError("mutation_rate must be in [0, 1]")
        if not (0 <= self.steady_state_rate <= 1):
            raise ValueError("steady_state_rate must be in [0, 1]")
        if self.elite_count >= self.population_size:
            raise ValueError("elite_count must be < population_size")

    def set_seed(self, seed: int):
        """设置随机种子"""
        self.seed = seed
        import random
        random.seed(seed)

    def to_dict(self) -> Dict[str, Any]:
        """将参数转换为字典"""
        return {
            'population_size': self.population_size,
            'crossover_rate': self.crossover_rate,
            'mutation_rate': self.mutation_rate,
            'max_generations': self.max_generations,
            'selection_method': self.selection_method,
            'crossover_operator': self.crossover_operator,
            'mutation_operator': self.mutation_operator,
            'elite_count': self.elite_count,
            'tournament_size': self.tournament_size,
        }

    def __repr__(self):
        return f"GAParameters({self.to_dict()})"
