"""
冷却方案管理模块 (Cooling Schedule Management)

冷却方案控制温度随时间的下降方式。选择合适的冷却方案对算法性能至关重要。

冷却方案的设计原则：
1. 初始温度要足够高，使初期接受差解的概率较高（约 0.8-0.95）
2. 冷却速率要适中，太快则退化为贪心，太慢则计算量大
3. 终止温度要足够低，使算法充分收敛
4. 每个温度的迭代次数要足够，使系统在该温度下达到准平衡
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable


class CoolingSchedule(ABC):
    """冷却方案基类"""

    @abstractmethod
    def compute_temperature(self, initial_temp: float, iteration: int, total_iterations: int) -> float:
        """
        计算指定迭代次数时的温度

        Args:
            initial_temp: 初始温度
            iteration: 当前迭代次数
            total_iterations: 总迭代次数（用于某些方案）

        Returns:
            当前温度
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """返回冷却方案的名称"""
        pass


class ExponentialCooling(CoolingSchedule):
    """
    指数冷却方案

    T(k) = T0 * alpha^k

    其中：
    - T0 是初始温度
    - alpha 是冷却系数 (0 < alpha < 1)
    - k 是迭代次数

    这是最常用的冷却方案，实现简单且效果稳定。

    典型参数：alpha = 0.80 ~ 0.999
    - alpha 接近 1：降温慢，搜索充分
    - alpha 接近 0：降温快，可能陷入局部最优
    """

    def __init__(self, alpha: float = 0.95):
        if not 0 < alpha < 1:
            raise ValueError(f"冷却系数必须在 (0, 1) 范围内，当前值: {alpha}")
        self.alpha = alpha

    def compute_temperature(self, initial_temp: float, iteration: int, total_iterations: int = 0) -> float:
        return initial_temp * (self.alpha ** iteration)

    def name(self) -> str:
        return f"exponential(alpha={self.alpha})"


class LinearCooling(CoolingSchedule):
    """
    线性冷却方案

    T(k) = T0 * (1 - k / K)

    其中：
    - T0 是初始温度
    - K 是总迭代次数
    - k 是当前迭代次数

    线性冷却在每次迭代中固定降温，温度从 T0 线性下降到 0。
    需要预先估计总迭代次数。
    """

    def __init__(self):
        pass

    def compute_temperature(self, initial_temp: float, iteration: int, total_iterations: int) -> float:
        if total_iterations <= 0:
            return initial_temp
        # 防止除以零或负数
        progress = min(iteration / total_iterations, 1.0)
        return max(initial_temp * (1 - progress), 1e-10)

    def name(self) -> str:
        return "linear"


class AdaptiveCooling(CoolingSchedule):
    """
    自适应冷却方案

    根据算法运行状态动态调整冷却速率：
    - 如果连续多次未找到更优解，减慢冷却（增加探索）
    - 如果频繁找到更优解，加快冷却（加速收敛）

    适用于：不知道合适冷却速率的问题。
    """

    def __init__(
        self,
        base_alpha: float = 0.95,
        min_alpha: float = 0.80,
        max_alpha: float = 0.999,
        adjustment_threshold: int = 10,
    ):
        self.base_alpha = base_alpha
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.adjustment_threshold = adjustment_threshold
        self._no_improve_count = 0
        self._current_alpha = base_alpha

    def update(self, improved: bool) -> float:
        """
        根据是否改进更新冷却速率

        Args:
            improved: 当前迭代是否找到更优解

        Returns:
            当前冷却速率
        """
        if improved:
            self._no_improve_count = 0
        else:
            self._no_improve_count += 1

        if self._no_improve_count >= self.adjustment_threshold:
            # 长时间未改进，减慢冷却
            self._current_alpha = min(self._current_alpha + 0.001, self.max_alpha)
            self._no_improve_count = 0
        elif self._no_improve_count == 0:
            # 频繁改进，可以稍微加快冷却
            self._current_alpha = max(self._current_alpha - 0.0001, self.min_alpha)

        return self._current_alpha

    def compute_temperature(self, initial_temp: float, iteration: int, total_iterations: int = 0) -> float:
        return initial_temp * (self._current_alpha ** iteration)

    def name(self) -> str:
        return f"adaptive(alpha={self._current_alpha:.4f})"

    def reset(self):
        """重置状态"""
        self._no_improve_count = 0
        self._current_alpha = self.base_alpha


def create_cooling_schedule(schedule_type: str, **kwargs) -> CoolingSchedule:
    """
    工厂函数：创建冷却方案

    Args:
        schedule_type: 方案类型 ("exponential", "linear", "adaptive")
        **kwargs: 方案参数

    Returns:
        CoolingSchedule 实例
    """
    schedule_map = {
        "exponential": ExponentialCooling,
        "linear": LinearCooling,
        "adaptive": AdaptiveCooling,
    }

    if schedule_type not in schedule_map:
        raise ValueError(
            f"未知的冷却方案: {schedule_type}，可选: {list(schedule_map.keys())}"
        )

    return schedule_map[schedule_type](**kwargs)
