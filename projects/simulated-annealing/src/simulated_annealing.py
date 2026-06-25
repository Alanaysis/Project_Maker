"""
模拟退火算法核心实现

实现模拟退火优化算法的核心组件：
- 温度调度策略
- Metropolis接受准则
- 优化器类
"""

import numpy as np
from typing import Callable, Tuple, List
from dataclasses import dataclass
from enum import Enum


class CoolingSchedule(Enum):
    """冷却策略枚举"""
    EXPONENTIAL = "exponential"  # 指数冷却
    LINEAR = "linear"           # 线性冷却
    LOGARITHMIC = "logarithmic" # 对数冷却


@dataclass
class SAConfig:
    """模拟退火配置"""
    initial_temp: float = 100.0      # 初始温度
    final_temp: float = 0.01         # 终止温度
    cooling_rate: float = 0.99       # 冷却速率
    max_iterations: int = 1000       # 最大迭代次数
    cooling_schedule: CoolingSchedule = CoolingSchedule.EXPONENTIAL


class SimulatedAnnealing:
    """
    模拟退火优化器

    实现标准的模拟退火算法，支持多种冷却策略。

    参数:
        config: 算法配置
        objective_func: 目标函数（最小化）
        neighbor_func: 邻域函数
        initial_solution: 初始解
    """

    def __init__(
        self,
        config: SAConfig,
        objective_func: Callable,
        neighbor_func: Callable,
        initial_solution: any
    ):
        self.config = config
        self.objective_func = objective_func
        self.neighbor_func = neighbor_func
        self.current_solution = initial_solution
        self.current_cost = objective_func(initial_solution)

        self.best_solution = initial_solution
        self.best_cost = self.current_cost

        self.temperature = config.initial_temp
        self.iteration = 0

        # 记录历史
        self.history = {
            'temperature': [],
            'current_cost': [],
            'best_cost': [],
            'acceptance_rate': []
        }

    def calculate_acceptance_probability(
        self,
        delta_cost: float,
        temperature: float
    ) -> float:
        """
        计算接受概率（Metropolis准则）

        如果新解更优，总是接受（概率为1）
        如果新解较差，以概率 exp(-ΔE/T) 接受

        参数:
            delta_cost: 成本差（新成本 - 旧成本）
            temperature: 当前温度

        返回:
            接受概率 [0, 1]
        """
        if delta_cost <= 0:
            return 1.0
        else:
            return np.exp(-delta_cost / temperature)

    def cooling_exponential(self) -> float:
        """指数冷却: T(t) = T0 * α^t"""
        return self.config.initial_temp * (self.config.cooling_rate ** self.iteration)

    def cooling_linear(self) -> float:
        """线性冷却: T(t) = T0 - (T0 - Tf) * t/max_iter"""
        return self.config.initial_temp - (
            (self.config.initial_temp - self.config.final_temp) *
            self.iteration / self.config.max_iterations
        )

    def cooling_logarithmic(self) -> float:
        """对数冷却: T(t) = T0 / (1 + α * log(1 + t))"""
        return self.config.initial_temp / (1 + self.config.cooling_rate * np.log(1 + self.iteration))

    def update_temperature(self):
        """更新温度"""
        if self.config.cooling_schedule == CoolingSchedule.EXPONENTIAL:
            self.temperature = self.cooling_exponential()
        elif self.config.cooling_schedule == CoolingSchedule.LINEAR:
            self.temperature = self.cooling_linear()
        elif self.config.cooling_schedule == CoolingSchedule.LOGARITHMIC:
            self.temperature = self.cooling_logarithmic()
        else:
            # 默认指数冷却
            self.temperature = self.cooling_exponential()

    def step(self) -> Tuple[float, bool]:
        """
        执行一步迭代

        返回:
            (是否接受新解, 接受概率)
        """
        # 生成邻域解
        new_solution = self.neighbor_func(self.current_solution)
        new_cost = self.objective_func(new_solution)

        # 计算成本差
        delta_cost = new_cost - self.current_cost

        # 计算接受概率
        acceptance_prob = self.calculate_acceptance_probability(
            delta_cost, self.temperature
        )

        # 决定是否接受
        accepted = False
        if np.random.random() < acceptance_prob:
            self.current_solution = new_solution
            self.current_cost = new_cost
            accepted = True

            # 更新最优解
            if new_cost < self.best_cost:
                self.best_solution = new_solution
                self.best_cost = new_cost

        # 记录历史
        self.history['temperature'].append(self.temperature)
        self.history['current_cost'].append(self.current_cost)
        self.history['best_cost'].append(self.best_cost)

        # 更新温度
        self.update_temperature()
        self.iteration += 1

        return accepted, acceptance_prob

    def should_stop(self) -> bool:
        """检查是否应该停止"""
        return (
            self.temperature <= self.config.final_temp or
            self.iteration >= self.config.max_iterations
        )

    def optimize(self) -> Tuple[any, float, dict]:
        """
        执行优化过程

        返回:
            (最优解, 最优成本, 历史记录)
        """
        accepted_count = 0

        while not self.should_stop():
            accepted, _ = self.step()
            if accepted:
                accepted_count += 1

        # 计算最终接受率
        if self.iteration > 0:
            self.history['acceptance_rate'] = accepted_count / self.iteration

        return self.best_solution, self.best_cost, self.history


def simple_test():
    """简单测试：最小化一维函数 f(x) = x^2"""
    print("测试：最小化 f(x) = x^2")
    print("-" * 40)

    # 配置
    config = SAConfig(
        initial_temp=100.0,
        final_temp=0.01,
        cooling_rate=0.99,
        max_iterations=1000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    # 目标函数
    def objective(x):
        return x ** 2

    # 邻域函数：随机扰动
    def neighbor(x):
        return x + np.random.randn() * 2

    # 初始解
    initial_solution = np.random.randn() * 10

    # 创建优化器并运行
    optimizer = SimulatedAnnealing(config, objective, neighbor, initial_solution)
    best_solution, best_cost, history = optimizer.optimize()

    print(f"初始解: {initial_solution:.4f}")
    print(f"最优解: {best_solution:.4f}")
    print(f"最优成本: {best_cost:.6f}")
    print(f"迭代次数: {optimizer.iteration}")
    print(f"最终温度: {optimizer.temperature:.4f}")

    return best_solution, best_cost


if __name__ == "__main__":
    simple_test()
