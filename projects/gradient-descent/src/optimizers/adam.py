"""Adam 优化器 - 自适应矩估计"""

import numpy as np
from .base import BaseOptimizer


class Adam(BaseOptimizer):
    """Adam (Adaptive Moment Estimation)

    结合动量法和 RMSProp 的优点，是目前最常用的优化算法之一。

    数学表达:
        m_t = β1 * m_{t-1} + (1-β1) * ∇J(θ_t)      # 一阶矩估计
        v_t = β2 * v_{t-1} + (1-β2) * (∇J(θ_t))^2    # 二阶矩估计
        m̂_t = m_t / (1 - β1^t)                        # 偏差修正
        v̂_t = v_t / (1 - β2^t)                        # 偏差修正
        θ_{t+1} = θ_t - (η / (√v̂_t + ε)) * m̂_t

    默认超参数:
        - β1 = 0.9
        - β2 = 0.999
        - ε = 1e-8

    优点:
        - 自适应学习率
        - 偏差修正机制
        - 适用于大多数问题
        - 对超参数不敏感

    Attributes:
        learning_rate: 学习率
        betas: 一阶矩和二阶矩的衰减率
        eps: 数值稳定性常数
        weight_decay: 权重衰减系数
        amsgrad: 是否使用 AMSGrad 变体
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0,
        amsgrad: bool = False
    ):
        """初始化 Adam 优化器

        Args:
            learning_rate: 学习率 (默认 0.001)
            betas: 一阶矩和二阶矩的衰减率 (默认 (0.9, 0.999))
            eps: 数值稳定性常数 (默认 1e-8)
            weight_decay: 权重衰减系数 (默认 0)
            amsgrad: 是否使用 AMSGrad 变体 (默认 False)
        """
        super().__init__(learning_rate)

        if not 0 <= betas[0] < 1:
            raise ValueError(f"beta1 必须在 [0, 1) 范围内，当前值: {betas[0]}")
        if not 0 <= betas[1] < 1:
            raise ValueError(f"beta2 必须在 [0, 1) 范围内，当前值: {betas[1]}")

        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        self.amsgrad = amsgrad

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 Adam 更新

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
            if self.amsgrad:
                self.state['max_exp_avg_sq'] = np.zeros_like(params)

        # 应用权重衰减 (AdamW 风格)
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

        if self.amsgrad:
            # AMSGrad: 维护二阶矩的最大值
            self.state['max_exp_avg_sq'] = np.maximum(
                self.state['max_exp_avg_sq'],
                self.state['exp_avg_sq']
            )
            corrected_exp_avg_sq = self.state['max_exp_avg_sq']
        else:
            corrected_exp_avg_sq = self.state['exp_avg_sq']

        corrected_exp_avg_sq = corrected_exp_avg_sq / bias_correction2

        # 计算更新量
        update = corrected_exp_avg / (np.sqrt(corrected_exp_avg_sq) + self.eps)

        # 更新参数
        params = params - self.learning_rate * update

        return params

    def reset(self) -> None:
        """重置优化器状态"""
        super().reset()
        # state 已经被清空，不需要设置为 None

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"Adam(learning_rate={self.learning_rate}, "
            f"betas={self.betas}, "
            f"amsgrad={self.amsgrad})"
        )


class AdamW(Adam):
    """AdamW - 解耦权重衰减的 Adam

    将权重衰减与梯度更新解耦，通常比 L2 正则化的 Adam 更有效。

    数学表达:
        m_t = β1 * m_{t-1} + (1-β1) * ∇J(θ_t)
        v_t = β2 * v_{t-1} + (1-β2) * (∇J(θ_t))^2
        m̂_t = m_t / (1 - β1^t)
        v̂_t = v_t / (1 - β2^t)
        θ_{t+1} = θ_t - η * (m̂_t / (√v̂_t + ε) + λ * θ_t)

    优点:
        - 更好的泛化性能
        - 现代深度学习的默认选择
        - 权重衰减与梯度更新解耦

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
        weight_decay: float = 0.01
    ):
        """初始化 AdamW 优化器

        Args:
            learning_rate: 学习率 (默认 0.001)
            betas: 一阶矩和二阶矩的衰减率 (默认 (0.9, 0.999))
            eps: 数值稳定性常数 (默认 1e-8)
            weight_decay: 权重衰减系数 (默认 0.01)
        """
        super().__init__(learning_rate, betas, eps, weight_decay, amsgrad=False)

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 AdamW 更新

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
            self.state['exp_avg'] = np.zeros_like(params)
            self.state['exp_avg_sq'] = np.zeros_like(params)

        # 注意：AdamW 不对梯度应用权重衰减，而是直接对参数应用

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

        # 计算更新量 (不包含权重衰减)
        update = corrected_exp_avg / (np.sqrt(corrected_exp_avg_sq) + self.eps)

        # 更新参数 (包含权重衰减)
        params = params - self.learning_rate * (update + self.weight_decay * params)

        return params

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return (
            f"AdamW(learning_rate={self.learning_rate}, "
            f"betas={self.betas}, "
            f"weight_decay={self.weight_decay})"
        )
