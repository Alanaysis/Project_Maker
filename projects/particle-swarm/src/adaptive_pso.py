"""
自适应粒子群优化 (Adaptive PSO)

实现自适应惯性权重和学习因子的 PSO 变体，能够根据搜索过程动态调整参数。

特点：
- 自适应惯性权重：根据粒子分布和收敛情况动态调整
- 自适应学习因子：根据个体和群体表现调整 c1, c2
- 多样性控制：维持种群多样性，避免早熟收敛
"""

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass
from .particle import Particle


@dataclass
class AdaptivePSOConfig:
    """自适应 PSO 配置"""

    # 基础参数
    n_particles: int = 30
    dimensions: int = 2
    bounds: tuple[float, float] = (-100.0, 100.0)

    # 初始参数
    w_init: float = 0.9  # 初始惯性权重
    c1_init: float = 2.0  # 初始认知系数
    c2_init: float = 2.0  # 初始社会系数

    # 自适应参数范围
    w_min: float = 0.4
    w_max: float = 0.9
    c_min: float = 0.5
    c_max: float = 2.5

    # 终止条件
    max_iterations: int = 200
    tolerance: float = 1e-6
    patience: int = 30

    # 自适应控制
    adaptation_rate: float = 0.1  # 参数调整速率
    diversity_threshold: float = 0.1  # 多样性阈值

    # 其他
    random_seed: Optional[int] = None
    track_trajectories: bool = False


class AdaptiveSwarm:
    """
    自适应粒子群优化算法

    根据搜索过程中的收敛情况和种群多样性，动态调整惯性权重和学习因子。

    自适应策略：
    1. 惯性权重：根据收敛速度调整，收敛慢时增大（探索），收敛快时减小（开发）
    2. 学习因子：根据个体和群体表现平衡 c1 和 c2
    3. 多样性控制：当种群多样性过低时，增加探索性
    """

    def __init__(self, config: AdaptivePSOConfig):
        """初始化自适应粒子群"""
        self.config = config
        self._rng = np.random.default_rng(config.random_seed)

        # 初始化粒子群
        self.particles = [
            Particle(
                dimensions=config.dimensions,
                bounds=config.bounds,
                rng=self._rng,
            )
            for _ in range(config.n_particles)
        ]

        # 全局最佳
        self.global_best: Optional[np.ndarray] = None
        self.global_best_fitness: float = float("inf")

        # 自适应参数
        self.w = config.w_init
        self.c1 = config.c1_init
        self.c2 = config.c2_init

        # 历史记录
        self.convergence_history: list[float] = []
        self.parameter_history: list[dict] = []
        self._stagnation_count: int = 0

    def _calculate_diversity(self) -> float:
        """
        计算种群多样性

        使用粒子位置的标准差衡量多样性
        """
        positions = np.array([p.position for p in self.particles])
        center = np.mean(positions, axis=0)
        diversity = np.mean(np.std(positions, axis=0))
        return diversity

    def _calculate_convergence_rate(self) -> float:
        """
        计算收敛速率

        返回最近几代适应度改善的平均速率
        """
        if len(self.convergence_history) < 5:
            return 0.0

        recent = self.convergence_history[-5:]
        improvements = []
        for i in range(1, len(recent)):
            if recent[i - 1] > 0:
                improvement = (recent[i - 1] - recent[i]) / recent[i - 1]
                improvements.append(improvement)

        return np.mean(improvements) if improvements else 0.0

    def _adapt_parameters(self, iteration: int) -> None:
        """
        自适应调整参数

        根据收敛速率和种群多样性调整 w, c1, c2
        """
        diversity = self._calculate_diversity()
        convergence_rate = self._calculate_convergence_rate()

        # 调整惯性权重
        if convergence_rate < 0.01:  # 收敛慢
            # 增大惯性，增强探索
            self.w = min(self.w * (1 + self.config.adaptation_rate), self.config.w_max)
        elif convergence_rate > 0.1:  # 收敛快
            # 减小惯性，增强开发
            self.w = max(self.w * (1 - self.config.adaptation_rate), self.config.w_min)

        # 调整学习因子
        if diversity < self.config.diversity_threshold:
            # 多样性低，增强个体探索
            self.c1 = min(self.c1 * (1 + self.config.adaptation_rate), self.config.c_max)
            self.c2 = max(self.c2 * (1 - self.config.adaptation_rate), self.config.c_min)
        else:
            # 多样性正常，平衡学习
            target_c = (self.config.c_min + self.config.c_max) / 2
            self.c1 = self.c1 + self.config.adaptation_rate * (target_c - self.c1)
            self.c2 = self.c2 + self.config.adaptation_rate * (target_c - self.c2)

        # 记录参数
        self.parameter_history.append({
            "iteration": iteration,
            "w": self.w,
            "c1": self.c1,
            "c2": self.c2,
            "diversity": diversity,
            "convergence_rate": convergence_rate,
        })

    def _evaluate_swarm(self, objective_function: Callable) -> None:
        """评估所有粒子并更新全局最佳"""
        for particle in self.particles:
            fitness = particle.evaluate(objective_function)

            if fitness < self.global_best_fitness:
                self.global_best_fitness = fitness
                self.global_best = particle.position.copy()
                self._stagnation_count = 0

    def optimize(
        self,
        objective_function: Callable,
        verbose: bool = False,
        callback: Optional[Callable] = None,
    ) -> dict:
        """
        执行自适应 PSO 优化

        参数:
            objective_function: 目标函数（最小化）
            verbose: 是否打印进度
            callback: 回调函数

        返回:
            优化结果字典
        """
        trajectories = None
        if self.config.track_trajectories:
            trajectories = [[] for _ in range(self.config.n_particles)]

        for iteration in range(self.config.max_iterations):
            # 评估
            self._evaluate_swarm(objective_function)
            self.convergence_history.append(self.global_best_fitness)

            # 记录轨迹
            if trajectories is not None:
                for i, particle in enumerate(self.particles):
                    trajectories[i].append(particle.position.copy())

            # 自适应调整参数
            self._adapt_parameters(iteration)

            # 更新粒子
            for particle in self.particles:
                particle.update_velocity(
                    global_best=self.global_best,
                    w=self.w,
                    c1=self.c1,
                    c2=self.c2,
                )
                particle.update_position(bounds=self.config.bounds)

            # 收敛检测
            if len(self.convergence_history) > 1:
                improvement = abs(
                    self.convergence_history[-1] - self.convergence_history[-2]
                )
                if improvement < self.config.tolerance:
                    self._stagnation_count += 1
                else:
                    self._stagnation_count = 0

            # 提前停止
            if self._stagnation_count >= self.config.patience:
                if verbose:
                    print(f"提前停止于第 {iteration + 1} 代")
                break

            # 回调
            if callback:
                callback(iteration, self.global_best_fitness, self.global_best)

            # 打印进度
            if verbose and (iteration + 1) % 10 == 0:
                print(
                    f"迭代 {iteration + 1}: "
                    f"适应度={self.global_best_fitness:.6f}, "
                    f"w={self.w:.3f}, c1={self.c1:.3f}, c2={self.c2:.3f}"
                )

        return {
            "best_position": self.global_best.copy(),
            "best_fitness": self.global_best_fitness,
            "iterations": len(self.convergence_history),
            "convergence_history": self.convergence_history,
            "parameter_history": self.parameter_history,
            "particle_trajectories": trajectories,
        }

    def reset(self) -> None:
        """重置粒子群状态"""
        self.particles = [
            Particle(
                dimensions=self.config.dimensions,
                bounds=self.config.bounds,
                rng=self._rng,
            )
            for _ in range(self.config.n_particles)
        ]
        self.global_best = None
        self.global_best_fitness = float("inf")
        self.w = self.config.w_init
        self.c1 = self.config.c1_init
        self.c2 = self.config.c2_init
        self.convergence_history = []
        self.parameter_history = []
        self._stagnation_count = 0
