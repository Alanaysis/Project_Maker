"""
参数估计器

实现在线参数估计方法，用于自适应控制。

主要方法：
- 最小二乘法 (RLS)
- 梯度下降法
- 最大似然估计
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class EstimationMethod(Enum):
    """参数估计方法"""
    RLS = "rls"  # 递归最小二乘
    GRADIENT = "gradient"  # 梯度下降
    FORGETTING_FACTOR = "forgetting_factor"  # 带遗忘因子的 RLS


@dataclass
class EstimationState:
    """参数估计状态"""
    parameters: np.ndarray
    covariance: np.ndarray
    time: float
    estimation_error: float


class ParameterEstimator:
    """
    参数估计器

    实现在线参数估计，用于自适应控制中的参数辨识。

    参数：
        n_params: 待估计参数数量
        estimation_method: 估计方法
        adaptation_gain: 自适应增益
        forgetting_factor: 遗忘因子 (0-1，越小遗忘越快)
    """

    def __init__(
        self,
        n_params: int,
        estimation_method: EstimationMethod = EstimationMethod.RLS,
        adaptation_gain: float = 0.1,
        forgetting_factor: float = 0.99,
        initial_covariance: float = 100.0,
    ):
        self.n_params = n_params
        self.method = estimation_method
        self.gamma = adaptation_gain
        self.lambda_ff = forgetting_factor

        # 参数估计值
        self.theta = np.zeros(n_params)

        # 协方差矩阵 (RLS)
        self.P = np.eye(n_params) * initial_covariance

        # 历史记录
        self._history: List[EstimationState] = []
        self._time = 0.0

    def update(
        self,
        phi: np.ndarray,
        y: float,
        dt: float,
    ) -> Tuple[np.ndarray, float]:
        """
        更新参数估计

        参数：
            phi: 回归向量 (与参数相关的特征)
            y: 观测输出
            dt: 时间步长

        返回：
            更新后的参数估计值和估计误差
        """
        # 计算预测输出
        y_hat = np.dot(phi, self.theta)
        error = y - y_hat

        if self.method == EstimationMethod.RLS:
            self._rls_update(phi, error)
        elif self.method == EstimationMethod.GRADIENT:
            self._gradient_update(phi, error, dt)
        elif self.method == EstimationMethod.FORGETTING_FACTOR:
            self._rls_with_forgetting(phi, error)

        self._time += dt

        # 记录历史
        state = EstimationState(
            parameters=self.theta.copy(),
            covariance=self.P.copy(),
            time=self._time,
            estimation_error=error,
        )
        self._history.append(state)

        return self.theta.copy(), error

    def _rls_update(self, phi: np.ndarray, error: float):
        """
        递归最小二乘 (RLS) 更新

        K = P * φ / (λ + φ^T * P * φ)
        θ = θ + K * e
        P = (I - K * φ^T) * P / λ

        参数：
            phi: 回归向量
            error: 估计误差
        """
        # 计算卡尔曼增益
        S = np.dot(phi, np.dot(self.P, phi))
        K = np.dot(self.P, phi) / (1.0 + S)

        # 更新参数估计
        self.theta += K * error

        # 更新协方差矩阵
        I = np.eye(self.n_params)
        self.P = np.dot(I - np.outer(K, phi), self.P)

    def _gradient_update(self, phi: np.ndarray, error: float, dt: float):
        """
        梯度下降更新

        θ = θ + γ * e * φ

        参数：
            phi: 回归向量
            error: 估计误差
            dt: 时间步长
        """
        self.theta += self.gamma * error * phi * dt

    def _rls_with_forgetting(self, phi: np.ndarray, error: float):
        """
        带遗忘因子的 RLS

        使用指数遗忘因子 λ (0 < λ < 1)
        λ 越小，对旧数据遗忘越快

        参数：
            phi: 回归向量
            error: 估计误差
        """
        # 计算卡尔曼增益
        S = np.dot(phi, np.dot(self.P, phi))
        K = np.dot(self.P, phi) / (self.lambda_ff + S)

        # 更新参数估计
        self.theta += K * error

        # 更新协方差矩阵 (带遗忘因子)
        I = np.eye(self.n_params)
        self.P = (np.dot(I - np.outer(K, phi), self.P)) / self.lambda_ff

    def get_parameters(self) -> np.ndarray:
        """获取当前参数估计值"""
        return self.theta.copy()

    def get_covariance(self) -> np.ndarray:
        """获取当前协方差矩阵"""
        return self.P.copy()

    def get_estimation_history(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取估计历史"""
        times = np.array([s.time for s in self._history])
        params = np.array([s.parameters for s in self._history])
        return times, params

    def get_error_history(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取估计误差历史"""
        times = np.array([s.time for s in self._history])
        errors = np.array([s.estimation_error for s in self._history])
        return times, errors

    def get_parameter_variance(self) -> np.ndarray:
        """获取参数估计方差 (协方差矩阵对角线)"""
        return np.diag(self.P)

    def reset(self):
        """重置估计器状态"""
        self.theta = np.zeros(self.n_params)
        self.P = np.eye(self.n_params) * 100.0
        self._history.clear()
        self._time = 0.0


class RecursiveLeastSquares:
    """
    递归最小二乘估计器

    用于估计线性系统参数: y = φ^T * θ + ε

    参数：
        n_params: 参数数量
        forgetting_factor: 遗忘因子 (默认 1.0，无遗忘)
    """

    def __init__(self, n_params: int, forgetting_factor: float = 1.0):
        self.n = n_params
        self.lambda_ff = forgetting_factor
        self.theta = np.zeros(n_params)
        self.P = np.eye(n_params) * 1000.0

    def estimate(self, phi: np.ndarray, y: float) -> Tuple[np.ndarray, float]:
        """
        更新估计

        参数：
            phi: 回归向量
            y: 观测值

        返回：
            参数估计值和预测误差
        """
        # 预测
        y_hat = np.dot(phi, self.theta)
        error = y - y_hat

        # 更新
        K = np.dot(self.P, phi) / (self.lambda_ff + np.dot(phi, np.dot(self.P, phi)))
        self.theta += K * error
        self.P = (np.eye(self.n) - np.outer(K, phi)) @ self.P / self.lambda_ff

        return self.theta.copy(), error

    def predict(self, phi: np.ndarray) -> float:
        """预测输出"""
        return np.dot(phi, self.theta)

    def reset(self):
        """重置估计器"""
        self.theta = np.zeros(self.n)
        self.P = np.eye(self.n) * 1000.0
