"""Warmup 学习率调度器"""

from .base import BaseScheduler


class WarmupScheduler(BaseScheduler):
    """Warmup 学习率调度器

    训练初期使用较小学习率，逐渐增加到目标学习率，然后可选地应用其他衰减策略。

    优势:
        - 稳定训练初期
        - 防止梯度爆炸
        - 通常与其他调度策略结合使用

    Args:
        optimizer: 优化器实例
        warmup_epochs: 预热 epoch 数
        target_lr: 目标学习率 (默认为基础学习率)
        scheduler: 后续调度器 (可选)
        last_epoch: 上一个 epoch 的索引
    """

    def __init__(
        self,
        optimizer,
        warmup_epochs: int,
        target_lr: float = None,
        scheduler: BaseScheduler = None,
        last_epoch: int = -1
    ):
        """初始化 Warmup 学习率调度器

        Args:
            optimizer: 优化器实例
            warmup_epochs: 预热 epoch 数
            target_lr: 目标学习率 (默认为基础学习率)
            scheduler: 后续调度器 (可选)
            last_epoch: 上一个 epoch 的索引
        """
        if warmup_epochs <= 0:
            raise ValueError(f"warmup_epochs 必须为正整数，当前值: {warmup_epochs}")

        self.warmup_epochs = warmup_epochs
        self.target_lr = target_lr if target_lr is not None else optimizer.learning_rate
        self.scheduler = scheduler
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> float:
        """计算当前学习率

        Returns:
            当前学习率
        """
        if self.last_epoch < self.warmup_epochs:
            # Warmup 阶段：线性增加学习率
            progress = self.last_epoch / self.warmup_epochs
            return self.base_lr + (self.target_lr - self.base_lr) * progress
        else:
            # Warmup 结束后：应用后续调度器或保持目标学习率
            if self.scheduler is not None:
                # 调整后续调度器的 epoch
                self.scheduler.last_epoch = self.last_epoch - self.warmup_epochs
                return self.scheduler.get_lr()
            else:
                return self.target_lr

    def step(self) -> None:
        """更新学习率"""
        super().step()
        # 如果有后续调度器，也更新它
        if self.scheduler is not None and self.last_epoch >= self.warmup_epochs:
            self.scheduler.step()

    def __repr__(self) -> str:
        """返回调度器的字符串表示"""
        return (
            f"WarmupScheduler(warmup_epochs={self.warmup_epochs}, "
            f"target_lr={self.target_lr}, "
            f"scheduler={self.scheduler})"
        )
