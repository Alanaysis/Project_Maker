"""
混沌粒子群优化 (Chaos PSO)

引入混沌序列替代随机数，增强搜索能力和跳出局部最优的能力。

特点：
- 混沌初始化：使用混沌序列初始化粒子位置
- 混沌扰动：在搜索过程中引入混沌扰动
- 多种混沌映射：支持 Logistic、Tent、Sinusoidal 等映射
"""

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass
from .particle import Particle


def logistic_map(x: np.ndarray, r: float = 4.0) -> np.ndarray:
    """
    Logistic 混沌映射

    x_{n+1} = r * x_n * (1 - x_n)

    参数:
        x: 当前值（范围 [0, 1]）
        r: 控制参数（通常 r=4 时完全混沌）

    返回:
        下一个混沌值
    """
    return r * x * (1 - x)


def tent_map(x: np.ndarray) -> np.ndarray:
    """
    Tent 混沌映射

    x_{n+1} = 2 * x_n        if x_n < 0.5
    x_{n+1} = 2 * (1 - x_n)  if x_n >= 0.5

    参数:
        x: 当前值（范围 [0, 1]）

    返回:
        下一个混沌值
    """
    result = np.where(x < 0.5, 2 * x, 2 * (1 - x))
    return result


def sinusoidal_map(x: np.ndarray) -> np.ndarray:
    """
    Sinusoidal 混沌映射

    x_{n+1} = sin(pi * x_n)

    参数:
        x: 当前值（范围 [0, 1]）

    返回:
        下一个混沌值
    """
    return np.sin(np.pi * x)


# 混沌映射注册表
CHAOS_MAPS = {
    "logistic": logistic_map,
    "tent": tent_map,
    "sinusoidal": sinusoidal_map,
}


@dataclass
class ChaosPSOConfig:
    """混沌 PSO 配置"""

    # 基础参数
    n_particles: int = 30
    dimensions: int = 2
    bounds: tuple[float, float] = (-100.0, 100.0)

    # PSO 参数
    w: float = 0.7
    c1: float = 1.5
    c2: float = 1.5

    # 混沌参数
    chaos_map: str = "logistic"  # 混沌映射类型
    chaos_weight: float = 0.1  # 混沌扰动权重
    chaos_decay: float = 0.99  # 混沌扰动衰减系数

    # 惯性权重策略
    w_strategy: str = "linear_decay"
    w_max: float = 0.9
    w_min: float = 0.4

    # 终止条件
    max_iterations: int = 200
    tolerance: float = 1e-6
    patience: int = 30

    # 其他
    random_seed: Optional[int] = None
    track_trajectories: bool = False


class ChaosSwarm:
    """
    混沌粒子群优化算法

    使用混沌序列增强 PSO 的搜索能力：
    1. 混沌初始化：用混沌序列初始化粒子位置，提高初始多样性
    2. 混沌扰动：在速度更新中加入混沌扰动，帮助跳出局部最优
    3. 混沌惯性权重：用混沌序列扰动惯性权重，增加搜索随机性
    """

    def __init__(self, config: ChaosPSOConfig):
        """初始化混沌粒子群"""
        self.config = config
        self._rng = np.random.default_rng(config.random_seed)

        # 获取混沌映射函数
        if config.chaos_map not in CHAOS_MAPS:
            raise ValueError(f"未知的混沌映射: {config.chaos_map}，可用: {list(CHAOS_MAPS.keys())}")
        self._chaos_map = CHAOS_MAPS[config.chaos_map]

        # 混沌序列状态
        self._chaos_state = self._rng.uniform(0.1, 0.9, size=config.dimensions)

        # 初始化粒子群（使用混沌序列）
        self.particles = self._chaos_init_particles()

        # 全局最佳
        self.global_best: Optional[np.ndarray] = None
        self.global_best_fitness: float = float("inf")

        # 历史记录
        self.convergence_history: list[float] = []
        self._stagnation_count: int = 0
        self._current_chaos_weight = config.chaos_weight

    def _chaos_init_particles(self) -> list[Particle]:
        """
        使用混沌序列初始化粒子

        相比随机初始化，混沌初始化能提供更好的初始分布
        """
        particles = []
        low, high = self.config.bounds

        for _ in range(self.config.n_particles):
            particle = Particle(
                dimensions=self.config.dimensions,
                bounds=self.config.bounds,
                rng=self._rng,
            )

            # 使用混沌序列生成位置
            self._chaos_state = self._chaos_map(self._chaos_state)
            # 将 [0, 1] 映射到 [low, high]
            particle.position = low + self._chaos_state * (high - low)

            # 使用混沌序列生成速度
            self._chaos_state = self._chaos_map(self._chaos_state)
            v_max = (high - low) * 0.1
            particle.velocity = -v_max + 2 * self._chaos_state * v_max

            particles.append(particle)

        return particles

    def _get_chaos_perturbation(self) -> np.ndarray:
        """
        生成混沌扰动向量

        返回:
            混沌扰动向量
        """
        self._chaos_state = self._chaos_map(self._chaos_state)
        # 映射到 [-1, 1]
        perturbation = 2 * self._chaos_state - 1
        return perturbation

    def _get_inertia_weight(self, iteration: int) -> float:
        """获取当前迭代的惯性权重"""
        if self.config.w_strategy == "fixed":
            w = self.config.w
        elif self.config.w_strategy == "linear_decay":
            w = self.config.w_max - (
                self.config.w_max - self.config.w_min
            ) * (iteration / self.config.max_iterations)
        else:
            w = self.config.w

        # 混沌扰动惯性权重
        self._chaos_state = self._chaos_map(self._chaos_state)
        chaos_factor = 0.1 * (self._chaos_state[0] - 0.5)  # [-0.05, 0.05]
        w = np.clip(w + chaos_factor, 0.0, 1.0)

        return w

    def _evaluate_swarm(self, objective_function: Callable) -> None:
        """评估所有粒子并更新全局最佳"""
        for particle in self.particles:
            fitness = particle.evaluate(objective_function)

            if fitness < self.global_best_fitness:
                self.global_best_fitness = fitness
                self.global_best = particle.position.copy()
                self._stagnation_count = 0

    def _apply_chaos_perturbation(self, particle: Particle) -> None:
        """
        对粒子应用混沌扰动

        当粒子陷入局部最优时，通过混沌扰动帮助跳出
        """
        perturbation = self._get_chaos_perturbation()
        particle.velocity += self._current_chaos_weight * perturbation

        # 衰减混沌扰动权重
        self._current_chaos_weight *= self.config.chaos_decay

    def optimize(
        self,
        objective_function: Callable,
        verbose: bool = False,
        callback: Optional[Callable] = None,
    ) -> dict:
        """
        执行混沌 PSO 优化

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

            # 获取惯性权重
            w = self._get_inertia_weight(iteration)

            # 更新粒子
            for particle in self.particles:
                # 标准速度更新
                particle.update_velocity(
                    global_best=self.global_best,
                    w=w,
                    c1=self.config.c1,
                    c2=self.config.c2,
                )

                # 应用混沌扰动
                self._apply_chaos_perturbation(particle)

                # 更新位置
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
                    f"混沌权重={self._current_chaos_weight:.4f}"
                )

        return {
            "best_position": self.global_best.copy(),
            "best_fitness": self.global_best_fitness,
            "iterations": len(self.convergence_history),
            "convergence_history": self.convergence_history,
            "particle_trajectories": trajectories,
        }

    def reset(self) -> None:
        """重置粒子群状态"""
        self._chaos_state = self._rng.uniform(0.1, 0.9, size=self.config.dimensions)
        self.particles = self._chaos_init_particles()
        self.global_best = None
        self.global_best_fitness = float("inf")
        self.convergence_history = []
        self._stagnation_count = 0
        self._current_chaos_weight = self.config.chaos_weight
