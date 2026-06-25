"""RMSProp 优化器 - 均方根传播"""

import numpy as np
from .base import BaseOptimizer


class RMSProp(BaseOptimizer):
    """RMSProp (Root Mean Square Propagation)

    使用移动平均代替累积平方和，解决 AdaGrad 学习率过早衰减的问题。

    数学表达:
        G_t = β * G_{t-1} + (1-β) * (∇J(θ_t))^2
        θ_{t+1} = θ_t - (η / √(G_t + ε)) * ∇J(θ_t)

    其中 β 是衰减率，通常设为 0.999。

    优点:
        - 解决 AdaGrad 学习率过早衰减的问题
        - 适合非平稳目标函数

    Attributes:
        learning_rate: 学习率
        alpha: 衰减率 (通常为 0.999)
        eps: 数值稳定性常数
        weight_decay: 权重衰减系数
        momentum: 动量系数
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        alpha: float = 0.99,
        eps: float = 1e-8,
        weight_decay: float = 0.0,
        momentum: float = 0.0
    ):
        """初始化 RMSProp 优化器

        Args:
            learning_rate: 学习率
            alpha: 衰减率 (通常为 0.999)
            eps: 数值稳定性常数
            weight_decay: 权重衰减系数
            momentum: 动量系数
        """
        super().__init__(learning_rate)

        if not 0 <= alpha < 1:
            raise ValueError(f"衰减率必须在 [0, 1) 范围内，当前值: {alpha}")

        self.alpha = alpha
        self.eps = eps
        self.weight_decay = weight_decay
        self.momentum = momentum

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 RMSProp 更新

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        # 检查数值稳定性
        params, grads = self._check_numerical_stability(params, grads)

        # 初始化状态
        if 'square_avg' not in self.state:
            self.state['square_avg'] = np.zeros_like(params)
            if self.momentum > 0:
                self.state['momentum_buffer'] = np.zeros_like(params)

        # 应用权重衰减
        if self.weight_decay != 0:
            grads = grads + self.weight_decay * params

        # 更新平方平均
        self.state['square_avg'] = (
            self.alpha * self.state['square_avg'] +
            (1 - self.alpha) * grads ** 2
        )

        # 计算更新量
        if self.momentum > 0:
            # 带动量的 RMSProp
            self.state['momentum_buffer'] = (
                self.momentum * self.state['momentum_buffer'] +
                grads / (np.sqrt(self.state['square_avg']) + self.eps)
            )
            update = self.state['momentum_buffer']
        else:
            # 标准 RMSProp
            update = grads / (np.sqrt(self.state['square_avg']) + self.eps)

        # 更新参数
        params = params - self.learning_rate * update

        # 更新迭代次数
        self._update_step_count()

        return params

    def reset(self) -> None:
        """重置优化器状态"""
        super().reset()
        self.state['square_avg'] = None
        if self.momentum > 0:
            self.state['momentum_buffer'] = None

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"RMSProp(learning_rate={self.learning_rate}, "
            f"alpha={self.alpha}, "
            f"momentum={self.momentum})"
        )
