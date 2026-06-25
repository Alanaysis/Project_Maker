"""Nadam 优化器 - Nesterov 加速自适应矩估计"""

import numpy as np
from .base import BaseOptimizer


class Nadam(BaseOptimizer):
    """Nadam (Nesterov-accelerated Adaptive Moment Estimation)

    结合 Nesterov 动量和 Adam 的优点，提供更准确的梯度估计。

    数学表达:
        m_t = β1 * m_{t-1} + (1-β1) * ∇J(θ_t)
        v_t = β2 * v_{t-1} + (1-β2) * (∇J(θ_t))^2
        m̂_t = m_t / (1 - β1^t)
        v̂_t = v_t / (1 - β2^t)
        θ_{t+1} = θ_t - η * ((1-β1) * ∇J(θ_t) + β1 * m̂_t) / (√v̂_t + ε)

    默认超参数:
        - β1 = 0.9
        - β2 = 0.999
        - ε = 1e-8

    优点:
        - 结合 Nesterov 动量的前瞻性和 Adam 的自适应学习率
        - 通常比 Adam 收敛更快
        - 对超参数不敏感

    Attributes:
        learning_rate: 学习率
        betas: 一阶矩和二阶矩的衰减率
        eps: 数值稳定性常数
        weight_decay: 权重衰减系数
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0
    ):
        """初始化 Nadam 优化器

        Args:
            learning_rate: 学习率 (默认 0.001)
            betas: 一阶矩和二阶矩的衰减率 (默认 (0.9, 0.999))
            eps: 数值稳定性常数 (默认 1e-8)
            weight_decay: 权重衰减系数 (默认 0)
        """
        super().__init__(learning_rate)

        if not 0 <= betas[0] < 1:
            raise ValueError(f"beta1 必须在 [0, 1) 范围内，当前值: {betas[0]}")
        if not 0 <= betas[1] < 1:
            raise ValueError(f"beta2 必须在 [0, 1) 范围内，当前值: {betas[1]}")

        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 Nadam 更新

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        # 检查数值稳定性
        params, grads = self._check_numerical_stability(params, grads)

        # 初始化状态
        if 'exp_avg' not in self.state:
            self.state['exp_avg'] = np.zeros_like(params)  # 一阶矩
            self.state['exp_avg_sq'] = np.zeros_like(params)  # 二阶矩

        # 应用权重衰减
        if self.weight_decay != 0:
            grads = grads + self.weight_decay * params

        # 更新迭代次数（先更新 step_count，再计算偏差修正）
        self._update_step_count()

        # 更新一阶矩估计
        self.state['exp_avg'] = (
            self.betas[0] * self.state['exp_avg'] +
            (1 - self.betas[0]) * grads
        )

        # 更新二阶矩估计
        self.state['exp_avg_sq'] = (
            self.betas[1] * self.state['exp_avg_sq'] +
            (1 - self.betas[1]) * grads ** 2
        )

        # 偏差修正
        bias_correction1 = 1 - self.betas[0] ** self.step_count
        bias_correction2 = 1 - self.betas[1] ** self.step_count

        corrected_exp_avg = self.state['exp_avg'] / bias_correction1
        corrected_exp_avg_sq = self.state['exp_avg_sq'] / bias_correction2

        # Nadam 更新：结合 Nesterov 动量
        # 使用当前梯度和修正后的一阶矩的加权平均
        nesterov_update = (
            (1 - self.betas[0]) * grads + self.betas[0] * corrected_exp_avg
        )

        # 计算更新量
        update = nesterov_update / (np.sqrt(corrected_exp_avg_sq) + self.eps)

        # 更新参数
        params = params - self.learning_rate * update

        return params

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"Nadam(learning_rate={self.learning_rate}, "
            f"betas={self.betas}, "
            f"weight_decay={self.weight_decay})"
        )
