"""SGD 优化器 - 随机梯度下降"""

import numpy as np
from .base import BaseOptimizer


class SGD(BaseOptimizer):
    """随机梯度下降 (Stochastic Gradient Descent)

    最基本的优化算法，每次使用一个或小批量样本的梯度更新参数。

    数学表达:
        θ_{t+1} = θ_t - η * ∇J(θ_t)

    Attributes:
        learning_rate: 学习率
        weight_decay: 权重衰减系数 (L2 正则化)
        dampening: 动量阻尼系数
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        weight_decay: float = 0.0,
        dampening: float = 0.0
    ):
        """初始化 SGD 优化器

        Args:
            learning_rate: 学习率
            weight_decay: 权重衰减系数
            dampening: 动量阻尼系数
        """
        super().__init__(learning_rate)
        self.weight_decay = weight_decay
        self.dampening = dampening

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 SGD 更新

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        # 检查数值稳定性
        params, grads = self._check_numerical_stability(params, grads)

        # 应用权重衰减
        if self.weight_decay != 0:
            grads = grads + self.weight_decay * params

        # 更新参数
        params = params - self.learning_rate * grads

        # 更新迭代次数
        self._update_step_count()

        return params

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"SGD(learning_rate={self.learning_rate}, "
            f"weight_decay={self.weight_decay}, "
            f"dampening={self.dampening})"
        )
