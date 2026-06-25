"""
核函数模块
==========

实现高斯过程常用的核函数：
- RBF (径向基函数/高斯核)
- Matérn 核
"""

import numpy as np
from abc import ABC, abstractmethod


class Kernel(ABC):
    """核函数基类"""

    @abstractmethod
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """计算核矩阵"""
        pass

    @abstractmethod
    def get_params(self) -> dict:
        """获取核函数参数"""
        pass

    @abstractmethod
    def set_params(self, **params) -> None:
        """设置核函数参数"""
        pass


class RBF(Kernel):
    """
    径向基函数核（高斯核）

    k(x, y) = sigma_f^2 * exp(-||x - y||^2 / (2 * l^2))

    参数：
    - length_scale: 长度尺度参数 l
    - signal_variance: 信号方差 sigma_f^2
    """

    def __init__(self, length_scale: float = 1.0, signal_variance: float = 1.0):
        self.length_scale = length_scale
        self.signal_variance = signal_variance

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        计算 RBF 核矩阵

        参数：
            X1: 形状 (n1, d) 的输入矩阵
            X2: 形状 (n2, d) 的输入矩阵

        返回：
            形状 (n1, n2) 的核矩阵
        """
        # 计算欧氏距离的平方
        sq_dist = np.sum(X1**2, axis=1, keepdims=True) + \
                  np.sum(X2**2, axis=1, keepdims=True).T - \
                  2 * X1 @ X2.T

        # 防止数值问题
        sq_dist = np.maximum(sq_dist, 0)

        return self.signal_variance * np.exp(-0.5 * sq_dist / self.length_scale**2)

    def get_params(self) -> dict:
        return {
            'length_scale': self.length_scale,
            'signal_variance': self.signal_variance
        }

    def set_params(self, **params) -> None:
        if 'length_scale' in params:
            self.length_scale = params['length_scale']
        if 'signal_variance' in params:
            self.signal_variance = params['signal_variance']


class Matern(Kernel):
    """
    Matérn 核函数

    对于 nu = 1/2: 指数核
    对于 nu = 3/2: 一阶可微
    对于 nu = 5/2: 二阶可微（默认，最常用）
    对于 nu -> inf: RBF 核

    参数：
    - length_scale: 长度尺度参数
    - signal_variance: 信号方差
    - nu: 平滑度参数
    """

    def __init__(self, length_scale: float = 1.0,
                 signal_variance: float = 1.0,
                 nu: float = 2.5):
        self.length_scale = length_scale
        self.signal_variance = signal_variance
        self.nu = nu

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        计算 Matérn 核矩阵

        参数：
            X1: 形状 (n1, d) 的输入矩阵
            X2: 形状 (n2, d) 的输入矩阵

        返回：
            形状 (n1, n2) 的核矩阵
        """
        from scipy.special import gamma, kv

        # 计算欧氏距离
        sq_dist = np.sum(X1**2, axis=1, keepdims=True) + \
                  np.sum(X2**2, axis=1, keepdims=True).T - \
                  2 * X1 @ X2.T
        sq_dist = np.maximum(sq_dist, 0)
        dist = np.sqrt(sq_dist)

        # 归一化距离
        r = np.sqrt(2 * self.nu) * dist / self.length_scale
        r = np.maximum(r, 1e-10)  # 避免零除

        if self.nu == 0.5:
            # 指数核
            K = self.signal_variance * np.exp(-r)
        elif self.nu == 1.5:
            # 一阶可微
            K = self.signal_variance * (1 + r) * np.exp(-r)
        elif self.nu == 2.5:
            # 二阶可微
            K = self.signal_variance * (1 + r + r**2 / 3) * np.exp(-r)
        else:
            # 一般情况
            K = self.signal_variance * \
                (2**(1 - self.nu) / gamma(self.nu)) * \
                r**self.nu * kv(self.nu, r)
            K = np.real(K)

        return K

    def get_params(self) -> dict:
        return {
            'length_scale': self.length_scale,
            'signal_variance': self.signal_variance,
            'nu': self.nu
        }

    def set_params(self, **params) -> None:
        if 'length_scale' in params:
            self.length_scale = params['length_scale']
        if 'signal_variance' in params:
            self.signal_variance = params['signal_variance']
        if 'nu' in params:
            self.nu = params['nu']


class WhiteNoise(Kernel):
    """
    白噪声核

    k(x, y) = sigma_n^2 * delta(x, y)

    用于建模观测噪声
    """

    def __init__(self, noise_variance: float = 1.0):
        self.noise_variance = noise_variance

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        if X1 is X2 or np.array_equal(X1, X2):
            return self.noise_variance * np.eye(len(X1))
        return np.zeros((len(X1), len(X2)))

    def get_params(self) -> dict:
        return {'noise_variance': self.noise_variance}

    def set_params(self, **params) -> None:
        if 'noise_variance' in params:
            self.noise_variance = params['noise_variance']


class CompositeKernel(Kernel):
    """复合核函数：支持核函数的加法和乘法组合"""

    def __init__(self, kernel1: Kernel, kernel2: Kernel, operation: str = '+'):
        self.kernel1 = kernel1
        self.kernel2 = kernel2
        self.operation = operation

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        K1 = self.kernel1(X1, X2)
        K2 = self.kernel2(X1, X2)

        if self.operation == '+':
            return K1 + K2
        elif self.operation == '*':
            return K1 * K2
        else:
            raise ValueError(f"不支持的操作: {self.operation}")

    def get_params(self) -> dict:
        return {
            'kernel1': self.kernel1.get_params(),
            'kernel2': self.kernel2.get_params(),
            'operation': self.operation
        }

    def set_params(self, **params) -> None:
        if 'kernel1' in params:
            self.kernel1.set_params(**params['kernel1'])
        if 'kernel2' in params:
            self.kernel2.set_params(**params['kernel2'])
