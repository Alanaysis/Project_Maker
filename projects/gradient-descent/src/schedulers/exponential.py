"""指数学习率调度器"""

from .base import BaseScheduler


class ExponentialLR(BaseScheduler):
    """指数学习率衰减 (Exponential Learning Rate Decay)

    每个 epoch 将学习率乘以衰减因子。

    数学表达:
        lr = base_lr * gamma^epoch

    Args:
        optimizer: 优化器实例
        gamma: 学习率衰减因子 (默认 0.9)
        last_epoch: 上一个 epoch 的索引
    """

    def __init__(
        self,
        optimizer,
        gamma: float = 0.9,
        last_epoch: int = -1
    ):
        """初始化指数学习率调度器

        Args:
            optimizer: 优化器实例
            gamma: 学习率衰减因子 (默认 0.9)
            last_epoch: 上一个 epoch 的索引
        """
        if not 0 < gamma <= 1:
            raise ValueError(f"gamma 必须在 (0, 1] 范围内，当前值: {gamma}")

        self.gamma = gamma
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> float:
        """计算当前学习率

        Returns:
            当前学习率
        """
        return self.base_lr * (self.gamma ** self.last_epoch)

    def __repr__(self) -> str:
        """返回调度器的字符串表示"""
        return (
            f"ExponentialLR(gamma={self.gamma}, "
            f"base_lr={self.base_lr})"
        )
