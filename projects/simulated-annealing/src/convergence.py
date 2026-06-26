"""
收敛检测模块 (Convergence Detection)

收敛检测用于判断模拟退火算法是否已经收敛，以便提前终止。

常见的收敛判据：
1. 能量变化小于阈值：连续多次迭代能量变化小于 ε
2. 接受率趋于零：几乎不接受任何差解
3. 温度达到下限：温度已经足够低
4. 连续未改进：连续 N 次迭代未找到更优解
5. 统计检验：能量分布趋于稳定
"""

from typing import List, Optional
import math


class ConvergenceDetector:
    """
    通用收敛检测器

    综合多种判据来判断算法是否收敛。
    """

    def __init__(
        self,
        energy_threshold: float = 1e-6,
        acceptance_threshold: float = 0.01,
        no_improve_threshold: int = 100,
        window_size: int = 20,
        min_iterations: int = 50,
    ):
        """
        Args:
            energy_threshold: 能量变化阈值
            acceptance_threshold: 接受率阈值
            no_improve_threshold: 连续未改进阈值
            window_size: 能量滑动窗口大小
            min_iterations: 最小迭代次数（避免过早终止）
        """
        self.energy_threshold = energy_threshold
        self.acceptance_threshold = acceptance_threshold
        self.no_improve_threshold = no_improve_threshold
        self.window_size = window_size
        self.min_iterations = min_iterations

        self._energy_history: List[float] = []
        self._acceptance_history: List[float] = []
        self._no_improve_count = 0
        self._converged = False
        self._convergence_iteration: Optional[int] = None

    def update(
        self,
        current_energy: float,
        acceptance_rate: float,
        improved: bool,
        iteration: int,
    ) -> bool:
        """
        更新收敛状态

        Args:
            current_energy: 当前能量值
            acceptance_rate: 当前接受率
            improved: 是否找到更优解
            iteration: 当前迭代次数

        Returns:
            True 如果检测到收敛
        """
        self._energy_history.append(current_energy)
        self._acceptance_history.append(abs(acceptance_rate))

        if improved:
            self._no_improve_count = 0
        else:
            self._no_improve_count += 1

        # 检查收敛条件
        if iteration < self.min_iterations:
            return False

        converged = self._check_convergence()
        if converged and not self._converged:
            self._converged = True
            self._convergence_iteration = iteration

        return converged

    def _check_convergence(self) -> bool:
        """检查所有收敛条件"""
        # 条件 1: 能量变化小于阈值
        energy_converged = self._check_energy_convergence()

        # 条件 2: 接受率趋于零
        acceptance_converged = self._check_acceptance_convergence()

        # 条件 3: 连续未改进次数超过阈值
        no_improve_converged = self._no_improve_count >= self.no_improve_threshold

        # 满足任一条件即认为收敛
        return energy_converged or acceptance_converged or no_improve_converged

    def _check_energy_convergence(self) -> bool:
        """检查能量是否稳定"""
        if len(self._energy_history) < self.window_size:
            return False

        window = self._energy_history[-self.window_size:]
        max_e = max(window)
        min_e = min(window)
        energy_range = max_e - min_e

        # 相对变化
        if abs(max_e) > 1e-10:
            relative_change = energy_range / abs(max_e)
        else:
            relative_change = energy_range

        return relative_change < self.energy_threshold

    def _check_acceptance_convergence(self) -> bool:
        """检查接受率是否趋于零"""
        if len(self._acceptance_history) < self.window_size:
            return False

        window = self._acceptance_history[-self.window_size:]
        avg_acceptance = sum(window) / len(window)

        return avg_acceptance < self.acceptance_threshold

    @property
    def is_converged(self) -> bool:
        return self._converged

    @property
    def convergence_iteration(self) -> Optional[int]:
        return self._convergence_iteration

    def reset(self):
        """重置检测器状态"""
        self._energy_history = []
        self._acceptance_history = []
        self._no_improve_count = 0
        self._converged = False
        self._convergence_iteration = None


class EarlyStopDetector:
    """
    早期停止检测器

    基于简单的早停策略，当连续 N 次未改进时停止。
    """

    def __init__(self, patience: int = 100, min_iterations: int = 50):
        self.patience = patience
        self.min_iterations = min_iterations
        self._no_improve_count = 0
        self._best_energy: Optional[float] = None

    def update(self, current_energy: float, iteration: int) -> bool:
        """
        更新并检查是否应该停止

        Args:
            current_energy: 当前能量
            iteration: 当前迭代次数

        Returns:
            True 如果应该停止
        """
        if iteration < self.min_iterations:
            return False

        if self._best_energy is None or current_energy < self._best_energy:
            self._best_energy = current_energy
            self._no_improve_count = 0
        else:
            self._no_improve_count += 1

        return self._no_improve_count >= self.patience

    def reset(self):
        self._no_improve_count = 0
        self._best_energy = None
