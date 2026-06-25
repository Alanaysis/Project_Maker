"""学习率调度器基类 - 所有调度器的基础接口"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional


class BaseScheduler(ABC):
    """学习率调度器基类

    所有调度器都应继承此类并实现 get_lr 方法。
    """

    def __init__(self, optimizer, last_epoch: int = -1):
        """初始化调度器

        Args:
            optimizer: 优化器实例
            last_epoch: 上一个 epoch 的索引
        """
        self.optimizer = optimizer
        self.last_epoch = last_epoch
        self.base_lr = optimizer.learning_rate

        # 初始化时更新学习率
        if last_epoch == -1:
            self.step()

    def step(self) -> None:
        """更新学习率

        每次调用时增加 epoch 计数并更新优化器的学习率。
        """
        self.last_epoch += 1
        lr = self.get_lr()
        self.optimizer.learning_rate = lr

    @abstractmethod
    def get_lr(self) -> float:
        """计算当前学习率

        Returns:
            当前学习率
        """
        pass

    def get_last_lr(self) -> float:
        """获取上一次设置的学习率

        Returns:
            上一次的学习率
        """
        return self.optimizer.learning_rate

    def get_base_lr(self) -> float:
        """获取基础学习率

        Returns:
            基础学习率
        """
        return self.base_lr

    def state_dict(self) -> dict:
        """获取调度器状态

        Returns:
            包含调度器状态的字典
        """
        return {
            'last_epoch': self.last_epoch,
            'base_lr': self.base_lr
        }

    def load_state_dict(self, state_dict: dict) -> None:
        """加载调度器状态

        Args:
            state_dict: 包含调度器状态的字典
        """
        self.last_epoch = state_dict['last_epoch']
        self.base_lr = state_dict['base_lr']

    def __repr__(self) -> str:
        """返回调度器的字符串表示"""
        return f"{self.__class__.__name__}(base_lr={self.base_lr})"
