"""
粒子群优化算法核心实现

实现标准 PSO 算法，支持：
- 自适应惯性权重（线性递减、自适应）
- 多种拓扑结构（全局、环形）
- 收敛检测
- 历史记录
"""

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass, field
from .particle import Particle


@dataclass
class PSOResult:
    """PSO 优化结果"""

    best_position: np.ndarray
    best_fitness: float
    iterations: int
    convergence_history: list[float]
    particle_trajectories: Optional[list[list[np.ndarray]]] = None

    def __repr__(self) -> str:
        return (
            f"PSOResult(best_fitness={self.best_fitness:.6f}, "
            f"iterations={self.iterations})"
        )


@dataclass
class PSOConfig:
    """PSO 配置参数"""

    # 粒子群参数
    n_particles: int = 30
    dimensions: int = 2
    bounds: tuple[float, float] = (-100.0, 100.0)

    # 速度更新参数
    w: float = 0.7  # 惯性权重
    c1: float = 1.5  # 认知系数
    c2: float = 1.5  # 社会系数

    # 自适应惯性权重
    w_strategy: str = "fixed"  # "fixed", "linear_decay", "adaptive"
    w_max: float = 0.9
    w_min: float = 0.4

    # 终止条件
    max_iterations: int = 100
    tolerance: float = 1e-6
    patience: int = 20  # 连续多少代无改善则停止

    # 其他
    random_seed: Optional[int] = None
    track_trajectories: bool = False


class Swarm:
    """
    粒子群优化算法

    实现标准 PSO 算法，包含惯性权重、认知和社会学习因子。
    支持线性递减惯性权重策略以平衡全局探索和局部开发。
    """

    def __init__(self, config: PSOConfig):
        """
        初始化粒子群

        参数:
            config: PSO 配置参数
        """
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

        # 收敛历史
        self.convergence_history: list[float] = []
        self._stagnation_count: int = 0

    def _get_inertia_weight(self, iteration: int) -> float:
        """
        获取当前迭代的惯性权重

        参数:
            iteration: 当前迭代次数

        返回:
            惯性权重值
        """
        if self.config.w_strategy == "fixed":
            return self.config.w
        elif self.config.w_strategy == "linear_decay":
            # 线性递减：从 w_max 衰减到 w_min
            return self.config.w_max - (
                self.config.w_max - self.config.w_min
            ) * (iteration / self.config.max_iterations)
        elif self.config.w_strategy == "adaptive":
            # 自适应：根据收敛情况调整
            if len(self.convergence_history) < 2:
                return self.config.w_max
            # 如果连续多代无改善，增大惯性（探索）
            if self._stagnation_count > 5:
                return min(self.config.w * 1.1, self.config.w_max)
            else:
                return max(self.config.w * 0.9, self.config.w_min)
        else:
            return self.config.w

    def _evaluate_swarm(self, objective_function: Callable) -> None:
        """
        评估所有粒子并更新全局最佳

        参数:
            objective_function: 目标函数
        """
        for particle in self.particles:
            fitness = particle.evaluate(objective_function)

            # 更新全局最佳
            if fitness < self.global_best_fitness:
                self.global_best_fitness = fitness
                self.global_best = particle.position.copy()
                self._stagnation_count = 0

    def _check_convergence(self, tolerance: float) -> bool:
        """
        检查是否收敛

        参数:
            tolerance: 收敛阈值

        返回:
            是否收敛
        """
        if len(self.convergence_history) < 2:
            return False

        # 检查最近的改善是否足够小
        recent_improvement = abs(
            self.convergence_history[-1] - self.convergence_history[-2]
        )
        return recent_improvement < tolerance

    def optimize(
        self,
        objective_function: Callable,
        verbose: bool = False,
        callback: Optional[Callable] = None,
    ) -> PSOResult:
        """
        执行 PSO 优化

        参数:
            objective_function: 目标函数（最小化）
            verbose: 是否打印进度
            callback: 每代结束后的回调函数

        返回:
            PSOResult 优化结果
        """
        trajectories = None
        if self.config.track_trajectories:
            trajectories = [[] for _ in range(self.config.n_particles)]

        for iteration in range(self.config.max_iterations):
            # 评估所有粒子
            self._evaluate_swarm(objective_function)

            # 记录收敛历史
            self.convergence_history.append(self.global_best_fitness)

            # 记录轨迹
            if trajectories is not None:
                for i, particle in enumerate(self.particles):
                    trajectories[i].append(particle.position.copy())

            # 获取当前惯性权重
            w = self._get_inertia_weight(iteration)

            # 更新所有粒子的速度和位置
            for particle in self.particles:
                particle.update_velocity(
                    global_best=self.global_best,
                    w=w,
                    c1=self.config.c1,
                    c2=self.config.c2,
                )
                particle.update_position(bounds=self.config.bounds)

            # 检查收敛
            if self._check_convergence(self.config.tolerance):
                self._stagnation_count += 1
            else:
                self._stagnation_count = 0

            # 检查是否应该提前停止
            if self._stagnation_count >= self.config.patience:
                if verbose:
                    print(f"提前停止于第 {iteration + 1} 代（连续 {self.config.patience} 代无改善）")
                break

            # 回调
            if callback is not None:
                callback(iteration, self.global_best_fitness, self.global_best)

            # 打印进度
            if verbose and (iteration + 1) % 10 == 0:
                print(
                    f"迭代 {iteration + 1}/{self.config.max_iterations}: "
                    f"最佳适应度 = {self.global_best_fitness:.6f}"
                )

        # 最终评估（确保所有粒子的最佳位置都被正确评估）
        self._evaluate_swarm(objective_function)

        return PSOResult(
            best_position=self.global_best.copy(),
            best_fitness=self.global_best_fitness,
            iterations=len(self.convergence_history),
            convergence_history=self.convergence_history,
            particle_trajectories=trajectories,
        )

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
        self.convergence_history = []
        self._stagnation_count = 0
