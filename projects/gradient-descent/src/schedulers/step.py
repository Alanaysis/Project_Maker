"""阶梯学习率调度器"""

from .base import BaseScheduler


class StepLR(BaseScheduler):
    """阶梯学习率衰减 (Step Learning Rate Decay)

    每隔固定数量的 epoch 将学习率乘以衰减因子。

    数学表达:
        lr = base_lr * gamma^(epoch // step_size)

    Args:
        optimizer: 优化器实例
        step_size: 学习率衰减的周期
        gamma: 学习率衰减因子 (默认 0.1)
        last_epoch: 上一个 epoch 的索引
    """

    def __init__(
        self,
        optimizer,
        step_size: int,
        gamma: float = 0.1,
        last_epoch: int = -1
    ):
        """初始化阶梯学习率调度器

        Args:
            optimizer: 优化器实例
            step_size: 学习率衰减的周期
            gamma: 学习率衰减因子 (默认 0.1)
            last_epoch: 上一个 epoch 的索引
        """
        if step_size <= 0:
            raise ValueError(f"step_size 必须为正整数，当前值: {step_size}")
        if not 0 < gamma <= 1:
            raise ValueError(f"gamma 必须在 (0, 1] 范围内，当前值: {gamma}")

        self.step_size = step_size
        self.gamma = gamma
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> float:
        """计算当前学习率

        Returns:
            当前学习率
        """
        # 计算衰减次数
        decay_count = self.last_epoch // self.step_size
        return self.base_lr * (self.gamma ** decay_count)

    def __repr__(self) -> str:
        """返回调度器的字符串表示"""
        return (
            f"StepLR(step_size={self.step_size}, "
            f"gamma={self.gamma}, "
            f"base_lr={self.base_lr})"
        )
