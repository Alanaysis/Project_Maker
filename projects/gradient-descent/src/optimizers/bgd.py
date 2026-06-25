"""BGD 优化器 - 批量梯度下降"""

import numpy as np
from .base import BaseOptimizer


class BGD(BaseOptimizer):
    """批量梯度下降 (Batch Gradient Descent)

    使用整个训练集计算梯度，更新参数。是最基础的梯度下降方法。

    数学表达:
        θ_{t+1} = θ_t - η * (1/N) * Σ∇J(θ_t, x_i)

    其中 N 是训练样本数量。

    优点:
        - 收敛稳定，轨迹平滑
        - 保证收敛到局部最小值（凸函数为全局最小值）
        - 梯度估计准确

    缺点:
        - 计算开销大，每次迭代需要遍历整个数据集
        - 内存需求大
        - 不适合大规模数据集
        - 可能陷入局部最小值

    Attributes:
        learning_rate: 学习率
        weight_decay: 权重衰减系数 (L2 正则化)
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        weight_decay: float = 0.0
    ):
        """初始化 BGD 优化器

        Args:
            learning_rate: 学习率
            weight_decay: 权重衰减系数
        """
        super().__init__(learning_rate)
        self.weight_decay = weight_decay

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 BGD 更新

        Args:
            params: 当前参数
            grads: 当前梯度（应为整个数据集的平均梯度）

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
            f"BGD(learning_rate={self.learning_rate}, "
            f"weight_decay={self.weight_decay})"
        )


class MiniBatchBGD(BaseOptimizer):
    """小批量梯度下降 (Mini-Batch Gradient Descent)

    结合 BGD 和 SGD 的优点，每次使用一个小批量的样本计算梯度。

    数学表达:
        θ_{t+1} = θ_t - η * (1/B) * Σ∇J(θ_t, x_i)

    其中 B 是小批量大小。

    优点:
        - 平衡计算效率和收敛稳定性
        - 可以利用向量化计算
        - 适合大规模数据集

    缺点:
        - 需要选择合适的批量大小
        - 可能需要学习率调度

    Attributes:
        learning_rate: 学习率
        batch_size: 批量大小
        weight_decay: 权重衰减系数
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        batch_size: int = 32,
        weight_decay: float = 0.0
    ):
        """初始化 Mini-Batch BGD 优化器

        Args:
            learning_rate: 学习率
            batch_size: 批量大小
            weight_decay: 权重衰减系数
        """
        super().__init__(learning_rate)

        if batch_size < 1:
            raise ValueError(f"批量大小必须大于 0，当前值: {batch_size}")

        self.batch_size = batch_size
        self.weight_decay = weight_decay

    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步 Mini-Batch BGD 更新

        Args:
            params: 当前参数
            grads: 当前梯度（应为小批量的平均梯度）

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
            f"MiniBatchBGD(learning_rate={self.learning_rate}, "
            f"batch_size={self.batch_size}, "
            f"weight_decay={self.weight_decay})"
        )
