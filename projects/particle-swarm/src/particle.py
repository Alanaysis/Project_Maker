"""
粒子类实现

每个粒子代表搜索空间中的一个候选解，具有：
- 位置 (position): 当前在搜索空间中的坐标
- 速度 (velocity): 当前的移动速度
- 最佳位置 (personal_best): 该粒子历史上找到的最优位置
- 最佳适应度 (personal_best_fitness): 该粒子历史上的最优适应度值
"""

import numpy as np
from typing import Optional


class Particle:
    """
    粒子群优化中的单个粒子

    属性:
        position: 当前位置向量
        velocity: 当前速度向量
        personal_best: 个体历史最佳位置
        personal_best_fitness: 个体历史最佳适应度值
        dimensions: 搜索空间维度
    """

    def __init__(
        self,
        dimensions: int,
        bounds: tuple[float, float] = (-100.0, 100.0),
        rng: Optional[np.random.Generator] = None,
    ):
        """
        初始化粒子

        参数:
            dimensions: 搜索空间维度
            bounds: 搜索空间边界 (min, max)
            rng: 随机数生成器
        """
        self.dimensions = dimensions
        self.bounds = bounds
        self._rng = rng or np.random.default_rng()

        # 在边界内随机初始化位置
        low, high = bounds
        self.position = self._rng.uniform(low, high, size=dimensions)

        # 初始化速度（通常设为0或小随机值）
        v_max = (high - low) * 0.1  # 最大速度为搜索范围的10%
        self.velocity = self._rng.uniform(-v_max, v_max, size=dimensions)

        # 个体最佳（初始为当前位置，适应度待评估）
        self.personal_best = self.position.copy()
        self.personal_best_fitness: float = float("inf")

    def evaluate(self, objective_function) -> float:
        """
        评估当前位置的适应度

        参数:
            objective_function: 目标函数

        返回:
            当前位置的适应度值
        """
        fitness = float(objective_function(self.position))

        # 更新个体最佳
        if fitness < self.personal_best_fitness:
            self.personal_best_fitness = fitness
            self.personal_best = self.position.copy()

        return fitness

    def update_velocity(
        self,
        global_best: np.ndarray,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
    ) -> None:
        """
        更新粒子速度

        速度更新公式:
        v_new = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)

        参数:
            w: 惯性权重
            c1: 认知系数（个体学习因子）
            c2: 社会系数（群体学习因子）
            global_best: 全局最佳位置
        """
        r1 = self._rng.random(self.dimensions)
        r2 = self._rng.random(self.dimensions)

        # 惯性部分 + 认知部分 + 社会部分
        inertia = w * self.velocity
        cognitive = c1 * r1 * (self.personal_best - self.position)
        social = c2 * r2 * (global_best - self.position)

        self.velocity = inertia + cognitive + social

    def update_position(self, bounds: Optional[tuple[float, float]] = None) -> None:
        """
        更新粒子位置

        参数:
            bounds: 可选的位置边界约束
        """
        self.position = self.position + self.velocity

        # 边界约束
        if bounds is not None:
            low, high = bounds
            self.position = np.clip(self.position, low, high)

    def __repr__(self) -> str:
        return (
            f"Particle(dimensions={self.dimensions}, "
            f"fitness={self.personal_best_fitness:.6f})"
        )
