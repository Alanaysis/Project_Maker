"""
卡尔曼滤波器实现

离散卡尔曼滤波算法:
预测步骤:
    x̂(k|k-1) = A * x̂(k-1|k-1) + B * u(k)
    P(k|k-1) = A * P(k-1|k-1) * A^T + Q

更新步骤:
    K(k) = P(k|k-1) * C^T * (C * P(k|k-1) * C^T + R)^(-1)
    x̂(k|k) = x̂(k|k-1) + K(k) * (y(k) - C * x̂(k|k-1))
    P(k|k) = (I - K(k) * C) * P(k|k-1)

其中:
- x̂: 状态估计
- P: 误差协方差矩阵
- K: 卡尔曼增益
- Q: 过程噪声协方差
- R: 测量噪声协方差
"""

import numpy as np
from typing import Optional, Tuple, List


class KalmanFilter:
    """
    离散卡尔曼滤波器

    用于线性系统的状态估计
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        Q: np.ndarray,
        R: np.ndarray,
        P0: Optional[np.ndarray] = None,
        x0: Optional[np.ndarray] = None,
    ):
        """
        初始化卡尔曼滤波器

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            C: 观测矩阵 (p x n)
            Q: 过程噪声协方差 (n x n)
            R: 测量噪声协方差 (p x p)
            P0: 初始误差协方差，默认为单位矩阵
            x0: 初始状态估计，默认为零向量
        """
        self.A = np.atleast_2d(np.array(A, dtype=float))
        self.B = np.atleast_2d(np.array(B, dtype=float))
        self.C = np.atleast_2d(np.array(C, dtype=float))
        self.Q = np.atleast_2d(np.array(Q, dtype=float))
        self.R = np.atleast_2d(np.array(R, dtype=float))

        # 获取维度
        self.n = self.A.shape[0]
        self.m = self.B.shape[1]
        self.p = self.C.shape[0]

        # 初始化状态估计和协方差
        if x0 is None:
            self.x_hat = np.zeros(self.n)
        else:
            self.x_hat = np.atleast_1d(np.array(x0, dtype=float)).flatten()

        if P0 is None:
            self.P = np.eye(self.n)
        else:
            self.P = np.atleast_2d(np.array(P0, dtype=float))

        # 历史记录
        self._state_estimates: List[np.ndarray] = [self.x_hat.copy()]
        self._covariances: List[np.ndarray] = [self.P.copy()]
        self._kalman_gains: List[np.ndarray] = []
        self._innovations: List[np.ndarray] = []

    def predict(
        self, u: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测步骤

        Args:
            u: 输入向量 (m,)，默认为零

        Returns:
            x_hat_prior: 先验状态估计
            P_prior: 先验误差协方差
        """
        if u is None:
            u = np.zeros(self.m)
        else:
            u = np.atleast_1d(np.array(u, dtype=float)).flatten()

        # 状态预测: x̂(k|k-1) = A * x̂(k-1) + B * u
        x_hat_prior = self.A @ self.x_hat + self.B @ u

        # 协方差预测: P(k|k-1) = A * P * A^T + Q
        P_prior = self.A @ self.P @ self.A.T + self.Q

        self.x_hat = x_hat_prior
        self.P = P_prior

        return x_hat_prior, P_prior

    def update(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        更新步骤

        Args:
            y: 测量值 (p,)

        Returns:
            x_hat_posterior: 后验状态估计
            P_posterior: 后验误差协方差
            K: 卡尔曼增益
        """
        y = np.atleast_1d(np.array(y, dtype=float)).flatten()

        # 计算卡尔曼增益: K = P * C^T * (C * P * C^T + R)^(-1)
        S = self.C @ self.P @ self.C.T + self.R
        K = self.P @ self.C.T @ np.linalg.inv(S)

        # 新息（测量残差）
        innovation = y - self.C @ self.x_hat

        # 状态更新: x̂(k|k) = x̂(k|k-1) + K * (y - C * x̂(k|k-1))
        x_hat_posterior = self.x_hat + K @ innovation

        # 协方差更新: P(k|k) = (I - K * C) * P(k|k-1)
        I = np.eye(self.n)
        P_posterior = (I - K @ self.C) @ self.P

        # 保存历史
        self.x_hat = x_hat_posterior
        self.P = P_posterior
        self._state_estimates.append(self.x_hat.copy())
        self._covariances.append(self.P.copy())
        self._kalman_gains.append(K.copy())
        self._innovations.append(innovation.copy())

        return x_hat_posterior, P_posterior, K

    def filter_step(
        self, y: np.ndarray, u: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        完整的滤波步骤（预测+更新）

        Args:
            y: 测量值 (p,)
            u: 输入向量 (m,)

        Returns:
            x_hat: 后验状态估计
            P: 后验误差协方差
            K: 卡尔曼增益
        """
        self.predict(u)
        return self.update(y)

    def smooth(
        self, measurements: np.ndarray, inputs: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        固定区间平滑（RTS平滑器）

        Args:
            measurements: 测量序列 (T x p)
            inputs: 输入序列 (T x m)

        Returns:
            smoothed_states: 平滑后的状态估计 (T x n)
        """
        T = measurements.shape[0]

        if inputs is None:
            inputs = np.zeros((T, self.m))

        # 前向滤波，保存预测和更新
        x_hat_priors = []
        P_priors = []
        x_hat_posteriors = []
        P_posteriors = []

        # 重置状态
        x_hat = np.zeros(self.n)
        P = np.eye(self.n)

        for k in range(T):
            # 预测
            x_hat_prior = self.A @ x_hat + self.B @ inputs[k]
            P_prior = self.A @ P @ self.A.T + self.Q

            # 更新
            S = self.C @ P_prior @ self.C.T + self.R
            K = P_prior @ self.C.T @ np.linalg.inv(S)
            innovation = measurements[k] - self.C @ x_hat_prior
            x_hat = x_hat_prior + K @ innovation
            P = (np.eye(self.n) - K @ self.C) @ P_prior

            x_hat_priors.append(x_hat_prior)
            P_priors.append(P_prior)
            x_hat_posteriors.append(x_hat.copy())
            P_posteriors.append(P.copy())

        # 后向平滑
        smoothed_states = np.zeros((T, self.n))
        smoothed_states[-1] = x_hat_posteriors[-1]
        P_smoothed = P_posteriors[-1].copy()

        for k in range(T - 2, -1, -1):
            C_k = P_posteriors[k] @ self.A.T @ np.linalg.inv(P_priors[k + 1])
            smoothed_states[k] = x_hat_posteriors[k] + C_k @ (
                smoothed_states[k + 1] - x_hat_priors[k + 1]
            )

        return smoothed_states

    @property
    def state_estimates(self) -> np.ndarray:
        """获取所有状态估计"""
        return np.array(self._state_estimates)

    @property
    def covariances(self) -> np.ndarray:
        """获取所有协方差矩阵"""
        return np.array(self._covariances)

    @property
    def kalman_gains(self) -> np.ndarray:
        """获取所有卡尔曼增益"""
        return np.array(self._kalman_gains)

    @property
    def innovations(self) -> np.ndarray:
        """获取所有新息"""
        return np.array(self._innovations)

    def get_estimation_error(self, true_states: np.ndarray) -> np.ndarray:
        """
        计算估计误差

        Args:
            true_states: 真实状态序列 (T x n)

        Returns:
            errors: 估计误差序列 (T x n)
        """
        estimates = self.state_estimates[: len(true_states)]
        return true_states - estimates

    def get_estimation_rmse(self, true_states: np.ndarray) -> float:
        """
        计算估计RMSE

        Args:
            true_states: 真实状态序列 (T x n)

        Returns:
            rmse: 均方根误差
        """
        errors = self.get_estimation_error(true_states)
        return float(np.sqrt(np.mean(errors**2)))
