"""
梯度下降算法

实现标准梯度下降、动量梯度下降、Nesterov 加速梯度下降。
"""

import numpy as np
from typing import Callable, Optional
from .base_optimizer import BaseOptimizer


class GradientDescent(BaseOptimizer):
    """梯度下降算法

    x_{k+1} = x_k - α * ∇f(x_k)

    支持：
    - 标准梯度下降
    - 动量梯度下降
    - Nesterov 加速梯度下降
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        momentum: float = 0.0,
        nesterov: bool = False,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.nesterov = nesterov
        self.velocity = None

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        if self.velocity is None:
            self.velocity = np.zeros_like(x)

        if self.nesterov:
            # Nesterov 加速梯度
            # 先用当前速度做预测
            x_ahead = x - self.learning_rate * self.momentum * self.velocity
            g_ahead = grad(x_ahead)
            self.velocity = self.momentum * self.velocity + g_ahead
            return x - self.learning_rate * self.velocity
        else:
            g = grad(x)
            # 动量更新
            self.velocity = self.momentum * self.velocity + g
            return x - self.learning_rate * self.velocity

    def reset(self):
        """重置优化器状态"""
        self.velocity = None


class AdaGrad(BaseOptimizer):
    """AdaGrad 算法

    自适应学习率，对稀疏特征友好。
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        epsilon: float = 1e-8,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.G = None  # 梯度平方和

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        g = grad(x)

        if self.G is None:
            self.G = np.zeros_like(x)

        self.G += g ** 2
        adjusted_lr = self.learning_rate / (np.sqrt(self.G) + self.epsilon)
        return x - adjusted_lr * g


class RMSProp(BaseOptimizer):
    """RMSProp 算法

    使用指数移动平均的自适应学习率。
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        rho: float = 0.9,
        epsilon: float = 1e-8,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.learning_rate = learning_rate
        self.rho = rho
        self.epsilon = epsilon
        self.Eg = None  # 梯度平方的指数移动平均

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        g = grad(x)

        if self.Eg is None:
            self.Eg = np.zeros_like(x)

        self.Eg = self.rho * self.Eg + (1 - self.rho) * g ** 2
        adjusted_lr = self.learning_rate / (np.sqrt(self.Eg) + self.epsilon)
        return x - adjusted_lr * g


class Adam(BaseOptimizer):
    """Adam 算法

    结合动量和 RMSProp 的自适应学习率算法。
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        beta1: float = 0.9,
        beta2: float = 0.999,
        epsilon: float = 1e-8,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.m = None  # 一阶矩
        self.v = None  # 二阶矩
        self.t = 0  # 时间步

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        g = grad(x)
        self.t += 1

        if self.m is None:
            self.m = np.zeros_like(x)
            self.v = np.zeros_like(x)

        # 更新矩估计
        self.m = self.beta1 * self.m + (1 - self.beta1) * g
        self.v = self.beta2 * self.v + (1 - self.beta2) * g ** 2

        # 偏差修正
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)

        return x - self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)
