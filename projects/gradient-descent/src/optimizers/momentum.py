"""Momentum 优化器 - 动量法"""

import numpy as np
from .base import BaseOptimizer


class Momentum(BaseOptimizer):
    """动量法 (Momentum)

    通过引入动量项来加速 SGD 收敛并减少震荡。

    数学表达:
        v_t = γ * v_{t-1} + η * ∇J(θ_t)
        θ_{t+1} = θ_t - v_t

    其中 γ 是动量系数，通常设为 0.9。

    Attributes:
        learning_rate: 学习率
        momentum: 动量系数
        weight_decay: 权重衰减系数
        nesterov: 是否使用 Nesterov 动量
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        momentum: float = 0.9,
        weight_decay: float = 0.0,
        dampening: float = 0.0,
        nesterov: bool = False
    ):
        """初始化 Momentum 优化器

        Args:
            learning_rate: 学习率
            momentum: 动量系数 (通常为 0.9)
            weight_decay: 权重衰减系数
            dampening: 动量阻尼系数
            nesterov: 是否使用 Nesterov 动量
        """
        super().__init__(learning_rate)

        if not 0 <= momentum < 1:
            raise ValueError(f"动量系数必须在 [0, 1) 范围内，当前值: {momentum}")

        self.momentum = momentum
        self.weight_decay = weight_decay
        self.dampening = dampening
        self.nesterov = nesterov

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 Momentum 更新

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        # 检查数值稳定性
        params, grads = self._check_numerical_stability(params, grads)

        # 初始化动量缓冲区
        if 'momentum_buffer' not in self.state:
            self.state['momentum_buffer'] = np.zeros_like(params)

        # 应用权重衰减
        if self.weight_decay != 0:
            grads = grads + self.weight_decay * params

        # 更新动量缓冲区
        self.state['momentum_buffer'] = (
            self.momentum * self.state['momentum_buffer'] + grads
        )

        # 应用阻尼
        if self.dampening > 0:
            d_p = grads + self.momentum * self.state['momentum_buffer']
        else:
            d_p = self.state['momentum_buffer']

        # Nesterov 动量
        if self.nesterov:
            d_p = grads + self.momentum * d_p

        # 更新参数
        params = params - self.learning_rate * d_p

        # 更新迭代次数
        self._update_step_count()

        return params

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"Momentum(learning_rate={self.learning_rate}, "
            f"momentum={self.momentum}, "
            f"nesterov={self.nesterov})"
        )


class NesterovMomentum(Momentum):
    """Nesterov 加速梯度 (Nesterov Accelerated Gradient)

    在计算梯度前先"向前看一步"，可以提供更准确的梯度估计。

    数学表达:
        v_t = γ * v_{t-1} + η * ∇J(θ_t - γ * v_{t-1})
        θ_{t+1} = θ_t - v_t
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        momentum: float = 0.9,
        weight_decay: float = 0.0
    ):
        """初始化 Nesterov Momentum 优化器

        Args:
            learning_rate: 学习率
            momentum: 动量系数
            weight_decay: 权重衰减系数
        """
        super().__init__(learning_rate, momentum, weight_decay, nesterov=True)

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"NesterovMomentum(learning_rate={self.learning_rate}, "
            f"momentum={self.momentum})"
        )
