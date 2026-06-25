"""
反馈校正 - 实现 MPC 的反馈校正机制

MPC 的三大核心要素：
1. 预测模型 - 预测未来系统行为
2. 滚动优化 - 在线求解最优控制序列
3. 反馈校正 - 基于实际测量修正预测

本模块实现反馈校正的两种主要方式：
1. 误差预测校正 - 基于预测误差修正未来预测
2. 模型参数校正 - 在线更新模型参数（自适应）
"""

import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


class CorrectionMethod(Enum):
    """校正方法"""
    ERROR_FEEDBACK = "error_feedback"         # 误差反馈校正
    MODEL_ADAPTIVE = "model_adaptive"         # 自适应模型校正
    EXTENDED_STATE = "extended_state"         # 增广状态方法
    DISTURBANCE_OBSERVER = "disturbance_observer"  # 扰动观测器


@dataclass
class CorrectionConfig:
    """校正配置"""
    method: CorrectionMethod = CorrectionMethod.ERROR_FEEDBACK
    correction_gain: float = 1.0          # 校正增益 (0~1)
    history_length: int = 10              # 历史数据长度
    adaptation_rate: float = 0.1          # 自适应速率
    forgetting_factor: float = 0.95       # 遗忘因子（递推最小二乘）
    disturbance_gain: float = 0.5         # 扰动观测器增益


class ErrorFeedbackCorrection:
    """
    误差反馈校正

    原理：利用当前时刻的预测误差修正未来预测
        y_corrected(k+i) = y_predicted(k+i) + correction_gain * e(k)

    其中:
        e(k) = y_measured(k) - y_predicted(k)
        correction_gain: 校正增益，通常取 0.5~1.0

    优点：
        - 简单易实现
        - 能有效抑制模型失配
        - 提高鲁棒性
    """

    def __init__(self, n_outputs: int, config: Optional[CorrectionConfig] = None):
        """
        初始化误差反馈校正器

        Args:
            n_outputs: 输出维度
            config: 校正配置
        """
        self.n_outputs = n_outputs
        self.config = config or CorrectionConfig()

        # 误差历史
        self._error_history = deque(maxlen=self.config.history_length)
        self._y_predicted_prev = None

    def compute_correction(self, y_measured: np.ndarray,
                           y_predicted: np.ndarray,
                           Y_predicted: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算校正量

        Args:
            y_measured: 当前测量输出
            y_predicted: 当前预测输出（上一时刻对当前时刻的预测）
            Y_predicted: 未来预测序列 (Np x p)

        Returns:
            校正后的预测序列 (Np x p)
        """
        # 计算当前误差
        error = y_measured - y_predicted
        self._error_history.append(error.copy())

        # 如果没有提供未来预测，返回误差
        if Y_predicted is None:
            return error

        # 校正未来预测
        Np = Y_predicted.shape[0]
        Y_corrected = Y_predicted.copy()

        for i in range(Np):
            # 使用衰减的误差校正
            # 距离越远，校正量越小
            decay = self.config.correction_gain * (0.9 ** i)
            Y_corrected[i] += decay * error

        return Y_corrected

    def get_error_trend(self) -> np.ndarray:
        """
        获取误差趋势（用于预测未来误差）

        Returns:
            误差趋势向量
        """
        if len(self._error_history) < 2:
            return np.zeros(self.n_outputs)

        # 使用最近的误差变化趋势
        errors = np.array(list(self._error_history))
        # 简单线性拟合误差趋势
        if len(errors) >= 3:
            # 使用最近3个点的趋势
            recent = errors[-3:]
            trend = (recent[-1] - recent[0]) / 2.0
        else:
            trend = errors[-1] - errors[-2]

        return trend

    def reset(self):
        """重置校正器"""
        self._error_history.clear()
        self._y_predicted_prev = None


class ModelAdaptiveCorrection:
    """
    自适应模型校正

    原理：在线更新模型参数以减少预测误差
    使用递推最小二乘法 (RLS) 更新模型参数

    模型形式:
        y(k) = φ(k)^T * θ

    其中:
        φ(k): 回归向量（包含输入输出历史）
        θ: 模型参数
    """

    def __init__(self, n_params: int, config: Optional[CorrectionConfig] = None):
        """
        初始化自适应模型校正器

        Args:
            n_params: 模型参数数量
            config: 校正配置
        """
        self.n_params = n_params
        self.config = config or CorrectionConfig()

        # RLS 参数
        self._theta = np.zeros(n_params)  # 参数估计
        self._P = np.eye(n_params) * 100  # 协方差矩阵
        self._lambda = self.config.forgetting_factor  # 遗忘因子

        # 历史数据
        self._phi_history = deque(maxlen=self.config.history_length)
        self._y_history = deque(maxlen=self.config.history_length)

    def update(self, phi: np.ndarray, y_measured: float):
        """
        递推最小二乘更新

        Args:
            phi: 回归向量
            y_measured: 测量输出
        """
        phi = phi.reshape(-1, 1)

        # 计算增益
        K = self._P @ phi / (self._lambda + phi.T @ self._P @ phi)

        # 更新参数
        y_pred = (phi.T @ self._theta.reshape(-1, 1)).item()
        e = y_measured - y_pred
        self._theta += (K.flatten() * e)

        # 更新协方差
        self._P = (1 / self._lambda) * (self._P - K @ phi.T @ self._P)

        # 保存历史
        self._phi_history.append(phi.flatten())
        self._y_history.append(y_measured)

    def predict(self, phi: np.ndarray) -> float:
        """
        使用当前参数预测

        Args:
            phi: 回归向量

        Returns:
            预测输出
        """
        return float(phi @ self._theta)

    def get_parameters(self) -> np.ndarray:
        """获取当前参数估计"""
        return self._theta.copy()

    def get_covariance(self) -> np.ndarray:
        """获取参数协方差"""
        return self._P.copy()

    def reset(self):
        """重置校正器"""
        self._theta = np.zeros(self.n_params)
        self._P = np.eye(self.n_params) * 100
        self._phi_history.clear()
        self._y_history.clear()


class ExtendedStateCorrection:
    """
    增广状态反馈校正

    原理：将扰动/偏移量作为增广状态进行估计
    增广状态: x_aug = [x, d]

    其中 d 是常值扰动估计

    增广模型:
        x(k+1) = A * x(k) + B * u(k) + Bd * d(k)
        d(k+1) = d(k)
        y(k) = C * x(k) + Cd * d(k)
    """

    def __init__(self, A: np.ndarray, B: np.ndarray, C: np.ndarray,
                 config: Optional[CorrectionConfig] = None):
        """
        初始化增广状态校正器

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            C: 输出矩阵 (p x n)
            config: 校正配置
        """
        self.A = np.array(A, dtype=float)
        self.B = np.array(B, dtype=float)
        self.C = np.array(C, dtype=float)

        self.n_states = A.shape[0]
        self.n_inputs = B.shape[1]
        self.n_outputs = C.shape[0]
        self.config = config or CorrectionConfig()

        # 扰动对输出的影响矩阵
        self.Cd = np.eye(self.n_outputs)

        # 增广系统矩阵
        n = self.n_states
        p = self.n_outputs
        m = self.n_inputs

        # 增广状态: [x, d]
        self.A_aug = np.block([
            [A, np.zeros((n, p))],
            [np.zeros((p, n)), np.eye(p)]
        ])
        self.B_aug = np.vstack([B, np.zeros((p, m))])
        self.C_aug = np.hstack([C, self.Cd])

        # 卡尔曼滤波器参数
        self.Q_kf = np.eye(n + p) * 0.01
        self.R_kf = np.eye(p) * 0.1
        self.P_kf = np.eye(n + p) * 1.0

        # 增广状态估计
        self.x_aug_est = np.zeros(n + p)

    def predict(self, x: np.ndarray, u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测并估计扰动

        Args:
            x: 当前状态估计
            u: 控制输入

        Returns:
            (下一状态估计, 扰动估计)
        """
        # 更新增广状态
        self.x_aug_est[:self.n_states] = x
        x_aug = self.x_aug_est

        # 预测
        x_aug_pred = self.A_aug @ x_aug + self.B_aug @ u

        return x_aug_pred[:self.n_states], x_aug_pred[self.n_states:]

    def update(self, x: np.ndarray, y_measured: np.ndarray,
               u: np.ndarray) -> np.ndarray:
        """
        使用测量值更新扰动估计

        Args:
            x: 当前状态估计
            y_measured: 测量输出
            u: 控制输入

        Returns:
            更新后的扰动估计
        """
        # 预测
        x_aug = np.concatenate([x, self.x_aug_est[self.n_states:]])
        x_aug_pred = self.A_aug @ x_aug + self.B_aug @ u

        # 预测误差协方差
        P_pred = self.A_aug @ self.P_kf @ self.A_aug.T + self.Q_kf

        # 卡尔曼增益
        S = self.C_aug @ P_pred @ self.C_aug.T + self.R_kf
        K = P_pred @ self.C_aug.T @ np.linalg.inv(S)

        # 输出预测
        y_pred = self.C_aug @ x_aug_pred

        # 状态更新
        self.x_aug_est = x_aug_pred + K @ (y_measured - y_pred)

        # 协方差更新
        I = np.eye(len(self.x_aug_est))
        self.P_kf = (I - K @ self.C_aug) @ P_pred

        return self.x_aug_est[self.n_states:]

    def get_disturbance(self) -> np.ndarray:
        """获取当前扰动估计"""
        return self.x_aug_est[self.n_states:].copy()

    def correct_prediction(self, Y_predicted: np.ndarray) -> np.ndarray:
        """
        使用扰动估计修正预测

        Args:
            Y_predicted: 原始预测序列 (Np x p)

        Returns:
            修正后的预测序列
        """
        d = self.get_disturbance()
        Y_corrected = Y_predicted.copy()

        for i in range(Y_corrected.shape[0]):
            Y_corrected[i] += d

        return Y_corrected

    def reset(self):
        """重置校正器"""
        self.x_aug_est = np.zeros(self.n_states + self.n_outputs)
        self.P_kf = np.eye(self.n_states + self.n_outputs) * 1.0


class DisturbanceObserverCorrection:
    """
    扰动观测器校正

    原理：使用扰动观测器 (DOB) 估计外部扰动和模型不确定性
    然后在预测中补偿这些扰动

    扰动观测器:
        d_hat(k) = L * (x(k) - x_hat(k))
        x_hat(k+1) = A * x_hat(k) + B * u(k) + Bd * d_hat(k)

    其中 L 是观测器增益
    """

    def __init__(self, A: np.ndarray, B: np.ndarray, C: np.ndarray,
                 config: Optional[CorrectionConfig] = None):
        """
        初始化扰动观测器

        Args:
            A: 状态转移矩阵
            B: 输入矩阵
            C: 输出矩阵
            config: 校正配置
        """
        self.A = np.array(A, dtype=float)
        self.B = np.array(B, dtype=float)
        self.C = np.array(C, dtype=float)

        self.n_states = A.shape[0]
        self.n_inputs = B.shape[1]
        self.n_outputs = C.shape[0]
        self.config = config or CorrectionConfig()

        # 扰动输入矩阵（假设扰动影响所有状态）
        self.Bd = np.eye(self.n_states)

        # 观测器增益
        self.L = np.eye(self.n_states) * self.config.disturbance_gain

        # 内部状态
        self._x_hat = np.zeros(self.n_states)
        self._d_hat = np.zeros(self.n_states)

    def estimate_disturbance(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """
        估计扰动

        Args:
            x: 当前状态测量值
            u: 控制输入

        Returns:
            扰动估计
        """
        # 预测状态
        x_pred = self.A @ self._x_hat + self.B @ u

        # 观测误差
        e = x - x_pred

        # 更新扰动估计
        self._d_hat = self.L @ e

        # 更新状态估计
        self._x_hat = x

        return self._d_hat.copy()

    def correct_state_prediction(self, x: np.ndarray, u: np.ndarray,
                                  Np: int) -> np.ndarray:
        """
        校正状态预测

        Args:
            x: 当前状态
            u: 控制输入（用于预测）
            Np: 预测时域

        Returns:
            校正后的状态预测序列 (Np+1 x n)
        """
        X_corrected = np.zeros((Np + 1, self.n_states))
        X_corrected[0] = x

        for i in range(Np):
            # 带扰动补偿的状态预测
            X_corrected[i + 1] = (self.A @ X_corrected[i] +
                                   self.B @ u +
                                   self.Bd @ self._d_hat)

        return X_corrected

    def reset(self):
        """重置观测器"""
        self._x_hat = np.zeros(self.n_states)
        self._d_hat = np.zeros(self.n_states)


class FeedbackCorrection:
    """
    反馈校正管理器

    统一管理不同的校正方法，提供统一接口
    """

    def __init__(self, method: CorrectionMethod,
                 n_states: int, n_inputs: int, n_outputs: int,
                 A: Optional[np.ndarray] = None,
                 B: Optional[np.ndarray] = None,
                 C: Optional[np.ndarray] = None,
                 config: Optional[CorrectionConfig] = None):
        """
        初始化反馈校正器

        Args:
            method: 校正方法
            n_states: 状态维度
            n_inputs: 输入维度
            n_outputs: 输出维度
            A: 状态转移矩阵（增广状态和扰动观测器方法需要）
            B: 输入矩阵
            C: 输出矩阵
            config: 校正配置
        """
        self.method = method
        self.config = config or CorrectionConfig()

        if method == CorrectionMethod.ERROR_FEEDBACK:
            self._corrector = ErrorFeedbackCorrection(n_outputs, self.config)
        elif method == CorrectionMethod.MODEL_ADAPTIVE:
            # 参数数量 = 状态维度 + 输入维度 + 1（偏置）
            n_params = n_states + n_inputs + 1
            self._corrector = ModelAdaptiveCorrection(n_params, self.config)
        elif method == CorrectionMethod.EXTENDED_STATE:
            if A is None or B is None or C is None:
                raise ValueError("增广状态方法需要 A, B, C 矩阵")
            self._corrector = ExtendedStateCorrection(A, B, C, self.config)
        elif method == CorrectionMethod.DISTURBANCE_OBSERVER:
            if A is None or B is None or C is None:
                raise ValueError("扰动观测器方法需要 A, B, C 矩阵")
            self._corrector = DisturbanceObserverCorrection(A, B, C, self.config)
        else:
            raise ValueError(f"未知的校正方法: {method}")

    def correct(self, **kwargs) -> Any:
        """
        执行校正

        根据不同方法调用对应的校正函数
        """
        if self.method == CorrectionMethod.ERROR_FEEDBACK:
            return self._corrector.compute_correction(
                kwargs['y_measured'],
                kwargs['y_predicted'],
                kwargs.get('Y_predicted')
            )
        elif self.method == CorrectionMethod.MODEL_ADAPTIVE:
            self._corrector.update(
                kwargs['phi'],
                kwargs['y_measured']
            )
            return self._corrector.get_parameters()
        elif self.method == CorrectionMethod.EXTENDED_STATE:
            return self._corrector.update(
                kwargs['x'],
                kwargs['y_measured'],
                kwargs['u']
            )
        elif self.method == CorrectionMethod.DISTURBANCE_OBSERVER:
            return self._corrector.estimate_disturbance(
                kwargs['x'],
                kwargs['u']
            )

    def get_corrector(self):
        """获取内部校正器实例"""
        return self._corrector

    def reset(self):
        """重置校正器"""
        self._corrector.reset()
