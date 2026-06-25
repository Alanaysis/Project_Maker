"""AdaGrad 优化器 - 自适应学习率算法"""

import numpy as np
from .base import BaseOptimizer


class AdaGrad(BaseOptimizer):
    """AdaGrad (Adaptive Gradient)

    为不同参数自适应调整学习率，特别适合稀疏特征。

    数学表达:
        G_t = G_{t-1} + (∇J(θ_t))^2
        θ_{t+1} = θ_t - (η / √(G_t + ε)) * ∇J(θ_t)

    其中 G_t 是梯度平方的累积和，ε 是防止除零的小常数。

    优点:
        - 对稀疏特征友好
        - 自适应调整学习率

    缺点:
        - 学习率单调递减，可能过早停止学习
        - 需要手动设置全局学习率

    Attributes:
        learning_rate: 学习率
        eps: 数值稳定性常数
        weight_decay: 权重衰减系数
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        eps: float = 1e-10,
        weight_decay: float = 0.0
    ):
        """初始化 AdaGrad 优化器

        Args:
            learning_rate: 学习率
            eps: 数值稳定性常数
            weight_decay: 权重衰减系数
        """
        super().__init__(learning_rate)
        self.eps = eps
        self.weight_decay = weight_decay

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 AdaGrad 更新

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        # 检查数值稳定性
        params, grads = self._check_numerical_stability(params, grads)

        # 初始化梯度平方累积和
        if 'sum_square_grads' not in self.state:
            self.state['sum_square_grads'] = np.zeros_like(params)

        # 应用权重衰减
        if self.weight_decay != 0:
            grads = grads + self.weight_decay * params

        # 累积梯度平方
        self.state['sum_square_grads'] += grads ** 2

        # 计算自适应学习率
        adjusted_lr = self.learning_rate / (
            np.sqrt(self.state['sum_square_grads']) + self.eps
        )

        # 更新参数
        params = params - adjusted_lr * grads

        # 更新迭代次数
        self._update_step_count()

        return params

    def reset(self) -> None:
        """重置优化器状态"""
        super().reset()
        self.state['sum_square_grads'] = None

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"AdaGrad(learning_rate={self.learning_rate}, "
            f"eps={self.eps})"
        )
