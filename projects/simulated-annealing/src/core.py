"""
模拟退火核心算法模块

模拟退火算法流程：
1. 初始化解 S 和温度 T
2. 在温度 T 下，重复：
   a. 生成邻域解 S_new
   b. 计算能量差 ΔE = E(S_new) - E(S)
   c. 如果 ΔE < 0 或随机数 < exp(-ΔE/T)，则接受 S_new
   d. 降低温度 T
3. 满足终止条件时停止，返回最优解
"""

import random
import time
import copy
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Tuple, Any
from .acceptance import metropolis_criterion
from .temperature import TemperatureScheduler, ExponentialScheduler


@dataclass
class SAResult:
    """模拟退火算法的运行结果"""
    best_solution: Any
    best_energy: float
    energy_history: List[float] = field(default_factory=list)
    acceptance_history: List[float] = field(default_factory=list)
    temperature_history: List[float] = field(default_factory=list)
    iteration_count: int = 0
    runtime: float = 0.0
    convergence_iteration: Optional[int] = None

    def summary(self) -> str:
        """返回结果的摘要信息"""
        lines = [
            "=== 模拟退火优化结果 ===",
            f"最优能量值: {self.best_energy:.6f}",
            f"迭代次数: {self.iteration_count}",
            f"运行时间: {self.runtime:.4f} 秒",
        ]
        if self.convergence_iteration is not None:
            lines.append(f"收敛迭代: {self.convergence_iteration}")
        lines.append(f"最终温度: {self.temperature_history[-1]:.6e}" if self.temperature_history else "最终温度: N/A")
        avg_accept = sum(self.acceptance_history) / len(self.acceptance_history) if self.acceptance_history else 0
        lines.append(f"平均接受率: {avg_accept:.4f}")
        return "\n".join(lines)


class SimulatedAnnealing:
    """
    模拟退火算法主类

    模拟退火 (Simulated Annealing, SA) 是一种概率优化算法，
    灵感来自金属退火过程。它通过接受差解的概率来避免陷入局部最优。

    关键参数：
    - initial_temp: 初始温度，较高的初始温度允许更多探索
    - min_temp: 最小温度，温度低于此值时停止
    - cooling_rate: 冷却率，控制温度下降速度 (0 < cooling_rate < 1)
    - iterations_per_temp: 每个温度下的迭代次数
    - acceptance_threshold: 接受率阈值，低于此值可能提前终止
    """

    def __init__(
        self,
        initial_temp: float = 1000.0,
        min_temp: float = 1e-8,
        cooling_rate: float = 0.995,
        iterations_per_temp: int = 100,
        acceptance_threshold: float = 0.01,
        seed: Optional[int] = None,
    ):
        self.initial_temp = initial_temp
        self.min_temp = min_temp
        self.cooling_rate = cooling_rate
        self.iterations_per_temp = iterations_per_temp
        self.acceptance_threshold = acceptance_threshold

        if seed is not None:
            random.seed(seed)

        self.current_temp = initial_temp
        self._result: Optional[SAResult] = None

    def optimize(
        self,
        objective: Callable,
        initial_solution: Any,
        neighbor_generator: Callable,
        max_iterations: int = 10000,
        time_limit: Optional[float] = None,
        temperature_scheduler: Optional[TemperatureScheduler] = None,
    ) -> SAResult:
        """
        执行模拟退火优化

        核心循环：
        初始解 → 邻域搜索 → 接受判断 → 温度降低 → 终止

        Args:
            objective: 目标函数，接受解并返回能量值（越小越好）
            initial_solution: 初始解
            neighbor_generator: 邻域生成函数，接受当前解返回新解
            max_iterations: 最大迭代次数
            time_limit: 时间限制（秒）
            temperature_scheduler: 温度调度器，如果为 None 则使用指数冷却

        Returns:
            SAResult: 优化结果
        """
        # 初始化
        self.current_temp = self.initial_temp
        current_solution = copy.deepcopy(initial_solution)
        current_energy = objective(current_solution)

        best_solution = copy.deepcopy(current_solution)
        best_energy = current_energy

        # 记录历史
        energy_history = [current_energy]
        acceptance_history = []
        temperature_history = [self.current_temp]

        iteration_count = 0
        start_time = time.time()
        consecutive_no_improve = 0
        no_improve_threshold = max(100, self.iterations_per_temp * 10)

        # 选择温度调度器
        if temperature_scheduler is None:
            temperature_scheduler = ExponentialScheduler(rate=self.cooling_rate)

        while iteration_count < max_iterations:
            # 检查时间限制
            if time_limit is not None:
                elapsed = time.time() - start_time
                if elapsed >= time_limit:
                    break

            # 检查温度下限
            if self.current_temp < self.min_temp:
                break

            # 本温度下的迭代
            accepted_this_round = 0
            total_this_round = 0

            for _ in range(self.iterations_per_temp):
                if iteration_count >= max_iterations:
                    break

                # 检查时间限制
                if time_limit is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= time_limit:
                        break

                # Step 1: 邻域搜索 - 生成候选解
                new_solution = neighbor_generator(current_solution)
                new_energy = objective(new_solution)

                # Step 2: 接受判断 - Metropolis 准则
                delta_e = new_energy - current_energy
                if metropolis_criterion(delta_e, self.current_temp):
                    current_solution = new_solution
                    current_energy = new_energy
                    accepted_this_round += 1

                # Step 3: 更新最优解
                if current_energy < best_energy:
                    best_solution = copy.deepcopy(current_solution)
                    best_energy = current_energy
                    consecutive_no_improve = 0
                else:
                    consecutive_no_improve += 1

                total_this_round += 1
                iteration_count += 1

                # 记录历史
                energy_history.append(current_energy)
                acceptance_history.append(1.0 if accepted_this_round > 0 else 0.0)
                temperature_history.append(self.current_temp)

            # 记录本轮接受率
            if total_this_round > 0:
                acceptance_history[-1] = accepted_this_round / total_this_round

            # Step 4: 温度降低
            self.current_temp = temperature_scheduler.next_temperature(self.current_temp)

            # 检查收敛（连续多次未改进）
            if consecutive_no_improve >= no_improve_threshold:
                break

        # 构建结果
        self._result = SAResult(
            best_solution=best_solution,
            best_energy=best_energy,
            energy_history=energy_history,
            acceptance_history=acceptance_history,
            temperature_history=temperature_history,
            iteration_count=iteration_count,
            runtime=time.time() - start_time,
        )

        return self._result
