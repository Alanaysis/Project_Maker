"""余弦退火学习率调度器"""

import numpy as np
from .base import BaseScheduler


class CosineAnnealingLR(BaseScheduler):
    """余弦退火学习率 (Cosine Annealing Learning Rate)

    使用余弦函数平滑地降低学习率，有助于跳出局部最优。

    数学表达:
        lr = lr_min + 0.5 * (lr_max - lr_min) * (1 + cos(π * t / T))

    其中:
        - lr_min: 最小学习率
        - lr_max: 最大学习率 (基础学习率)
        - t: 当前 epoch
        - T: 总 epoch 数

    Args:
        optimizer: 优化器实例
        T_max: 最大迭代次数
        eta_min: 最小学习率 (默认 0)
        last_epoch: 上一个 epoch 的索引
    """

    def __init__(
        self,
        optimizer,
        T_max: int,
        eta_min: float = 0.0,
        last_epoch: int = -1
    ):
        """初始化余弦退火学习率调度器

        Args:
            optimizer: 优化器实例
            T_max: 最大迭代次数
            eta_min: 最小学习率 (默认 0)
            last_epoch: 上一个 epoch 的索引
        """
        if T_max <= 0:
            raise ValueError(f"T_max 必须为正整数，当前值: {T_max}")
        if eta_min < 0:
            raise ValueError(f"eta_min 不能为负数，当前值: {eta_min}")

        self.T_max = T_max
        self.eta_min = eta_min
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> float:
        """计算当前学习率

        Returns:
            当前学习率
        """
        # 计算余弦退火因子
        cos_factor = 0.5 * (1 + np.cos(np.pi * self.last_epoch / self.T_max))
        return self.eta_min + (self.base_lr - self.eta_min) * cos_factor

    def __repr__(self) -> str:
        """返回调度器的字符串表示"""
        return (
            f"CosineAnnealingLR(T_max={self.T_max}, "
            f"eta_min={self.eta_min}, "
            f"base_lr={self.base_lr})"
        )
