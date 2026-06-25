"""优化器基类 - 所有优化器的基础接口"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseOptimizer(ABC):
    """优化器基类

    所有优化器都应继承此类并实现 step 方法。
    """

    def __init__(self, learning_rate: float = 0.01):
        """初始化优化器

        Args:
            learning_rate: 学习率
        """
        if learning_rate < 0:
            raise ValueError(f"学习率不能为负数，当前值: {learning_rate}")

        self.learning_rate = learning_rate
        self.state: Dict[str, Any] = {}
        self.step_count: int = 0

    @abstractmethod
    def step(self, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步优化

        Args:
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        pass

    def zero_grad(self) -> None:
        """清零梯度（对于需要累积梯度的场景）"""
        pass

    def get_state(self) -> Dict[str, Any]:
        """获取优化器状态

        Returns:
            包含优化器状态的字典
        """
        return self.state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """设置优化器状态

        Args:
            state: 包含优化器状态的字典
        """
        self.state = state.copy()

    def reset(self) -> None:
        """重置优化器状态"""
        self.state = {}
        self.step_count = 0

    def _update_step_count(self) -> None:
        """更新迭代次数"""
        self.step_count += 1

    def _clip_grads(self, grads: np.ndarray, max_norm: float = 1.0) -> np.ndarray:
        """裁剪梯度以防止梯度爆炸

        Args:
            grads: 原始梯度
            max_norm: 最大梯度范数

        Returns:
            裁剪后的梯度
        """
        grad_norm = np.linalg.norm(grads)
        if grad_norm > max_norm:
            grads = grads * (max_norm / grad_norm)
        return grads

    def _check_numerical_stability(self, params: np.ndarray, grads: np.ndarray) -> tuple:
        """检查数值稳定性

        Args:
            params: 参数
            grads: 梯度

        Returns:
            处理后的参数和梯度
        """
        # 检查 NaN
        if np.any(np.isnan(params)):
            raise ValueError("参数中存在 NaN 值")
        if np.any(np.isnan(grads)):
            raise ValueError("梯度中存在 NaN 值")

        # 检查 Inf
        if np.any(np.isinf(params)):
            raise ValueError("参数中存在 Inf 值")
        if np.any(np.isinf(grads)):
            raise ValueError("梯度中存在 Inf 值")

        return params, grads

    def __repr__(self) -> str:
        """返回优化器的字符串表示"""
        return f"{self.__class__.__name__}(learning_rate={self.learning_rate})"
