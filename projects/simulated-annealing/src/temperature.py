"""
温度调度模块 (Temperature Scheduling)

温度是模拟退火算法的核心参数，控制着算法的"探索"与"利用"平衡：
- 高温时：接受差解的概率高，算法广泛探索解空间
- 低温时：接受差解的概率低，算法聚焦于局部优化

温度调度策略：
1. 指数冷却 (Exponential): T(k) = T0 * alpha^k，最常用
2. 线性冷却 (Linear): T(k) = T0 - k * delta，简单直观
3. 对数冷却 (Logarithmic): T(k) = T0 / log(1+k)，理论收敛保证
4. 自适应冷却 (Adaptive): 根据接受率动态调整
"""

from abc import ABC, abstractmethod
from typing import Optional


class TemperatureScheduler(ABC):
    """温度调度器基类"""

    @abstractmethod
    def next_temperature(self, current_temp: float) -> float:
        """计算下一个温度值"""
        pass

    @abstractmethod
    def get_rate(self) -> float:
        """获取当前冷却速率"""
        pass


class ExponentialScheduler(TemperatureScheduler):
    """
    指数冷却调度器

    T(k+1) = alpha * T(k)

    其中 alpha 是冷却系数 (0 < alpha < 1)，通常取 0.8 ~ 0.999。
    alpha 越接近 1，降温越慢，搜索越充分，但计算时间越长。

    优点：实现简单，效果稳定
    缺点：需要手动调整 alpha
    """

    def __init__(self, rate: float = 0.99):
        if not 0 < rate < 1:
            raise ValueError(f"冷却率必须在 (0, 1) 范围内，当前值: {rate}")
        self.rate = rate

    def next_temperature(self, current_temp: float) -> float:
        return current_temp * self.rate

    def get_rate(self) -> float:
        return self.rate


class LinearScheduler(TemperatureScheduler):
    """
    线性冷却调度器

    T(k+1) = T(k) - delta

    其中 delta 是每次降温的固定值。
    需要预先估计总迭代次数来设置合适的 delta。

    优点：简单直观，温度线性下降
    缺点：需要预估总迭代次数
    """

    def __init__(self, delta: float = 1.0):
        if delta <= 0:
            raise ValueError(f"降温步长必须为正数，当前值: {delta}")
        self.delta = delta

    def next_temperature(self, current_temp: float) -> float:
        return max(current_temp - self.delta, 0.0)

    def get_rate(self) -> float:
        # 线性冷却的相对速率随温度变化
        return self.delta  # 返回绝对降温量


class LogarithmicScheduler(TemperatureScheduler):
    """
    对数冷却调度器

    T(k) = T0 / log(1 + k)

    根据理论分析，对数冷却能保证算法收敛到全局最优（Geman & Geman, 1984）。
    但收敛速度较慢，适用于对精度要求高的场景。

    优点：理论保证收敛
    缺点：收敛速度慢，需要跟踪迭代次数
    """

    def __init__(self, initial_temp: float = 1000.0):
        self.initial_temp = initial_temp
        self.iteration_count = 0

    def next_temperature(self, current_temp: float) -> float:
        self.iteration_count += 1
        return self.initial_temp / __import__("math").log(1 + self.iteration_count)

    def get_rate(self) -> float:
        if self.iteration_count == 0:
            return 1.0
        return self.initial_temp / (self.iteration_count * __import__("math").log(1 + self.iteration_count))


class AdaptiveScheduler(TemperatureScheduler):
    """
    自适应温度调度器

    根据算法运行过程中的接受率动态调整冷却速率：
    - 接受率过高：加快冷却（增大冷却系数）
    - 接受率过低：减慢冷却（减小冷却系数）

    目标接受率通常设为 0.44 左右（科学文献推荐值）。

    优点：自动适应问题特征
    缺点：需要调整额外参数
    """

    def __init__(
        self,
        initial_rate: float = 0.99,
        target_acceptance: float = 0.44,
        adjustment_factor: float = 0.01,
        min_rate: float = 0.80,
        max_rate: float = 0.9999,
        window_size: int = 50,
    ):
        self.initial_rate = initial_rate
        self.current_rate = initial_rate
        self.target_acceptance = target_acceptance
        self.adjustment_factor = adjustment_factor
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.window_size = window_size
        self._recent_acceptance = []

    def update(self, acceptance_rate: float) -> float:
        """根据接受率更新冷却速率"""
        self._recent_acceptance.append(abs(acceptance_rate - self.target_acceptance))
        if len(self._recent_acceptance) > self.window_size:
            self._recent_acceptance.pop(0)

        if len(self._recent_acceptance) < self.window_size:
            return self.current_rate

        avg_error = sum(self._recent_acceptance) / len(self._recent_acceptance)

        # 如果接受率高于目标值，说明探索过多，加快冷却
        if acceptance_rate > self.target_acceptance:
            self.current_rate = min(
                self.current_rate + self.adjustment_factor, self.max_rate
            )
        # 如果接受率低于目标值，说明探索不足，减慢冷却
        else:
            self.current_rate = max(
                self.current_rate - self.adjustment_factor, self.min_rate
            )

        return self.current_rate

    def next_temperature(self, current_temp: float) -> float:
        return current_temp * self.current_rate

    def get_rate(self) -> float:
        return self.current_rate

    def reset(self):
        """重置自适应状态"""
        self.current_rate = self.initial_rate
        self._recent_acceptance = []
