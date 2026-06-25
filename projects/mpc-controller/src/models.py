"""
预测模型 - 实现状态空间模型和脉冲响应模型

MPC 的核心是预测模型，本模块实现两种常用的预测模型：
1. 状态空间模型 (State Space Model)
2. 脉冲响应模型 (Impulse Response Model)
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass


class StateSpaceModel:
    """
    离散时间状态空间模型

    模型形式:
        x(k+1) = A * x(k) + B * u(k) + G * w(k)
        y(k)   = C * x(k) + D * u(k) + v(k)

    其中:
        x: 状态向量 (n x 1)
        u: 输入向量 (m x 1)
        y: 输出向量 (p x 1)
        w: 过程噪声 (q x 1)
        v: 测量噪声 (p x 1)
    """

    def __init__(self, A: np.ndarray, B: np.ndarray,
                 C: Optional[np.ndarray] = None,
                 D: Optional[np.ndarray] = None,
                 G: Optional[np.ndarray] = None,
                 Q_noise: Optional[np.ndarray] = None,
                 R_noise: Optional[np.ndarray] = None):
        """
        初始化状态空间模型

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            C: 输出矩阵 (p x n)，默认为单位矩阵
            D: 前馈矩阵 (p x m)，默认为零矩阵
            G: 噪声输入矩阵 (n x q)，默认为单位矩阵
            Q_noise: 过程噪声协方差 (q x q)
            R_noise: 测量噪声协方差 (p x p)
        """
        self.A = np.array(A, dtype=float)
        self.B = np.array(B, dtype=float)
        self.n_states = self.A.shape[0]
        self.n_inputs = self.B.shape[1]

        if C is None:
            C = np.eye(self.n_states)
        self.C = np.array(C, dtype=float)
        self.n_outputs = self.C.shape[0]

        if D is None:
            D = np.zeros((self.n_outputs, self.n_inputs))
        self.D = np.array(D, dtype=float)

        if G is None:
            G = np.eye(self.n_states)
        self.G = np.array(G, dtype=float)

        self.Q_noise = Q_noise
        self.R_noise = R_noise

    def predict(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """
        单步状态预测

        Args:
            x: 当前状态
            u: 控制输入

        Returns:
            下一时刻状态
        """
        return self.A @ x + self.B @ u

    def output(self, x: np.ndarray, u: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算输出

        Args:
            x: 当前状态
            u: 控制输入

        Returns:
            系统输出
        """
        y = self.C @ x
        if u is not None:
            y = y + self.D @ u
        return y

    def predict_sequence(self, x0: np.ndarray, U: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测状态和输出序列

        Args:
            x0: 初始状态
            U: 控制序列 (N x m)

        Returns:
            (状态序列 (N+1 x n), 输出序列 (N x p))
        """
        N = U.shape[0]
        X = np.zeros((N + 1, self.n_states))
        Y = np.zeros((N, self.n_outputs))
        X[0] = x0

        for k in range(N):
            X[k + 1] = self.predict(X[k], U[k])
            Y[k] = self.output(X[k])

        return X, Y

    def compute_prediction_matrices(self, Np: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算预测矩阵（用于构建 QP 问题）

        对于预测时域 Np，计算：
            Y = Psi * x0 + Theta * U

        其中:
            Psi: 自由响应矩阵 (Np*p x n)
            Theta: 强制响应矩阵 (Np*p x Np*m)

        Args:
            Np: 预测时域

        Returns:
            (Psi, Theta) 预测矩阵
        """
        n = self.n_states
        m = self.n_inputs
        p = self.n_outputs

        # 自由响应矩阵
        Psi = np.zeros((Np * p, n))
        # 强制响应矩阵
        Theta = np.zeros((Np * p, Np * m))

        # 计算 CA^k
        CAk = self.C.copy()
        for i in range(Np):
            Psi[i * p:(i + 1) * p, :] = CAk
            CAk = CAk @ self.A

        # 计算强制响应矩阵
        for i in range(Np):
            for j in range(i):
                # Theta[i, j] = C * A^(i-j-1) * B
                CAkB = self.C @ np.linalg.matrix_power(self.A, i - j - 1) @ self.B
                Theta[i * p:(i + 1) * p, j * m:(j + 1) * m] = CAkB
            # 对角块: C * B (当 i == j 时，A^0 = I)
            # 注意：对于离散系统，y(k) = C*x(k)，所以对角块是 C*B
            # 但通常预测从 y(k+1) 开始，这里我们从 y(k) 开始
            if i == 0:
                # y(k) = C*x(k)，不依赖 u(k)
                pass
            else:
                # y(k+i) 依赖 u(k) ... u(k+i-1)
                Theta[i * p:(i + 1) * p, 0:m] = self.C @ np.linalg.matrix_power(self.A, i) @ self.B
                for j in range(1, i + 1):
                    CAkB = self.C @ np.linalg.matrix_power(self.A, i - j) @ self.B
                    Theta[i * p:(i + 1) * p, j * m:(j + 1) * m] = CAkB

        return Psi, Theta

    def is_stable(self) -> bool:
        """
        检查系统稳定性

        Returns:
            如果所有特征值的模小于1则返回True
        """
        eigenvalues = np.linalg.eigvals(self.A)
        return np.all(np.abs(eigenvalues) < 1.0)

    def is_controllable(self) -> bool:
        """
        检查系统可控性

        Returns:
            如果系统可控则返回True
        """
        n = self.n_states
        m = self.n_inputs
        # 构建可控性矩阵
        Ctrb = np.zeros((n, n * m))
        ABk = np.eye(n)
        for i in range(n):
            Ctrb[:, i * m:(i + 1) * m] = ABk @ self.B
            ABk = ABk @ self.A
        # 检查秩
        return np.linalg.matrix_rank(Ctrb) == n

    def is_observable(self) -> bool:
        """
        检查系统可观性

        Returns:
            如果系统可观则返回True
        """
        n = self.n_states
        p = self.n_outputs
        # 构建可观性矩阵
        Obsv = np.zeros((n * p, n))
        CAk = self.C.copy()
        for i in range(n):
            Obsv[i * p:(i + 1) * p, :] = CAk
            CAk = CAk @ self.A
        # 检查秩
        return np.linalg.matrix_rank(Obsv) == n


class ImpulseResponseModel:
    """
    脉冲响应模型（FIR 模型）

    模型形式:
        y(k) = Σ[i=0 to N-1] h(i) * u(k-i)

    其中:
        h(i): 脉冲响应系数
        N: 模型长度（截断长度）

    优点:
        - 不需要知道系统内部结构
        - 可以从实验数据直接获取
        - 适用于非线性系统的线性化近似

    缺点:
        - 需要较长的模型长度
        - 不能直接处理不稳定系统
    """

    def __init__(self, impulse_response: np.ndarray, dt: float = 1.0):
        """
        初始化脉冲响应模型

        Args:
            impulse_response: 脉冲响应系数 (N x p x m) 或 (N,)
                N: 模型长度
                p: 输出维度
                m: 输入维度
            dt: 采样时间
        """
        h = np.array(impulse_response, dtype=float)

        if h.ndim == 1:
            # SISO 系统
            self.N = len(h)
            self.n_inputs = 1
            self.n_outputs = 1
            self.h = h.reshape(self.N, 1, 1)
        elif h.ndim == 2:
            # 假设是 (N, m) 形式，p=1
            self.N = h.shape[0]
            self.n_inputs = h.shape[1]
            self.n_outputs = 1
            self.h = h.reshape(self.N, 1, self.n_inputs)
        else:
            # (N, p, m) 形式
            self.N = h.shape[0]
            self.n_outputs = h.shape[1]
            self.n_inputs = h.shape[2]
            self.h = h

        self.dt = dt

        # 内部状态：存储最近的输入历史
        self._u_history = np.zeros((self.N, self.n_inputs))

    @classmethod
    def from_step_response(cls, step_response: np.ndarray, dt: float = 1.0):
        """
        从阶跃响应创建脉冲响应模型

        Args:
            step_response: 阶跃响应系数
            dt: 采样时间

        Returns:
            脉冲响应模型
        """
        s = np.array(step_response, dtype=float)
        # 脉冲响应 = 阶跃响应的差分
        h = np.diff(s, prepend=0.0)
        return cls(h, dt)

    @classmethod
    def from_state_space(cls, A: np.ndarray, B: np.ndarray,
                         C: np.ndarray, N: int, dt: float = 1.0):
        """
        从状态空间模型计算脉冲响应

        Args:
            A: 状态转移矩阵
            B: 输入矩阵
            C: 输出矩阵
            N: 脉冲响应长度
            dt: 采样时间

        Returns:
            脉冲响应模型
        """
        n = A.shape[0]
        m = B.shape[1]
        p = C.shape[0]

        h = np.zeros((N, p, m))
        ABk = np.eye(n)

        for k in range(N):
            h[k] = C @ ABk @ B
            ABk = ABk @ A

        return cls(h, dt)

    def predict(self, u: np.ndarray) -> np.ndarray:
        """
        单步预测

        Args:
            u: 当前控制输入

        Returns:
            预测输出
        """
        # 更新输入历史
        self._u_history = np.roll(self._u_history, 1, axis=0)
        self._u_history[0] = u

        # 计算输出
        y = np.zeros(self.n_outputs)
        for k in range(self.N):
            y += (self.h[k] @ self._u_history[k]).flatten()

        return y

    def predict_sequence(self, u_history: np.ndarray,
                         U_future: np.ndarray) -> np.ndarray:
        """
        预测输出序列

        Args:
            u_history: 过去的输入 (N_hist x m)
            U_future: 未来控制序列 (N_pred x m)

        Returns:
            预测输出序列 (N_pred x p)
        """
        N_pred = U_future.shape[0]
        Y = np.zeros((N_pred, self.n_outputs))

        # 合并历史和未来输入
        u_all = np.vstack([u_history, U_future])

        for k in range(N_pred):
            y = np.zeros(self.n_outputs)
            for i in range(self.N):
                idx = len(u_history) + k - i
                if 0 <= idx < len(u_all):
                    y += (self.h[i] @ u_all[idx]).flatten()
            Y[k] = y

        return Y

    def compute_prediction_matrix(self, Np: int) -> np.ndarray:
        """
        计算预测矩阵 S

        Y = S * U + Y_free

        其中 S 是下三角 Toeplitz 矩阵

        Args:
            Np: 预测时域

        Returns:
            预测矩阵 S (Np*p x Np*m)
        """
        p = self.n_outputs
        m = self.n_inputs
        S = np.zeros((Np * p, Np * m))

        for i in range(Np):
            for j in range(i + 1):
                if i - j < self.N:
                    S[i * p:(i + 1) * p, j * m:(j + 1) * m] = self.h[i - j]

        return S

    def reset(self):
        """重置内部状态"""
        self._u_history = np.zeros((self.N, self.n_inputs))


class ContinuousTransferFunction:
    """
    连续时间传递函数模型

    G(s) = (b_m * s^m + ... + b_1 * s + b_0) / (a_n * s^n + ... + a_1 * s + a_0)

    用于系统辨识和模型转换
    """

    def __init__(self, numerator: np.ndarray, denominator: np.ndarray):
        """
        初始化传递函数

        Args:
            numerator: 分子系数 [b_m, ..., b_1, b_0]
            denominator: 分母系数 [a_n, ..., a_1, a_0]
        """
        self.num = np.array(numerator, dtype=float)
        self.den = np.array(denominator, dtype=float)

    def to_discrete(self, dt: float, method: str = 'zoh') -> 'DiscreteTransferFunction':
        """
        离散化

        Args:
            dt: 采样时间
            method: 离散化方法 ('zoh', 'foh', 'tustin')

        Returns:
            离散传递函数
        """
        # 简化实现：使用双线性变换（Tustin）
        if method == 'tustin':
            # 双线性变换: s = (2/T) * (z-1)/(z+1)
            return self._tustin_transform(dt)
        else:
            # 默认使用 ZOH
            return self._zoh_transform(dt)

    def _tustin_transform(self, dt: float) -> 'DiscreteTransferFunction':
        """双线性变换离散化"""
        from scipy.signal import bilinear
        num_d, den_d = bilinear(self.num, self.den, fs=1.0 / dt)
        return DiscreteTransferFunction(num_d, den_d, dt)

    def _zoh_transform(self, dt: float) -> 'DiscreteTransferFunction':
        """零阶保持离散化"""
        from scipy.signal import cont2discrete
        # 转换为状态空间，再离散化
        from scipy.signal import tf2ss, ss2tf
        A, B, C, D = tf2ss(self.num, self.den)
        Ad, Bd, Cd, Dd, _ = cont2discrete((A, B, C, D), dt, method='zoh')
        num_d, den_d = ss2tf(Ad, Bd, Cd, Dd)
        return DiscreteTransferFunction(num_d.flatten(), den_d.flatten(), dt)


class DiscreteTransferFunction:
    """
    离散时间传递函数模型

    H(z) = (b_0 + b_1 * z^-1 + ... + b_m * z^-m) / (1 + a_1 * z^-1 + ... + a_n * z^-n)
    """

    def __init__(self, numerator: np.ndarray, denominator: np.ndarray,
                 dt: float = 1.0):
        """
        初始化离散传递函数

        Args:
            numerator: 分子系数
            denominator: 分母系数
            dt: 采样时间
        """
        self.num = np.array(numerator, dtype=float)
        self.den = np.array(denominator, dtype=float)
        self.dt = dt

        # 归一化分母
        if self.den[0] != 0:
            self.num = self.num / self.den[0]
            self.den = self.den / self.den[0]

        # 内部状态
        self._u_buffer = np.zeros(len(self.num))
        self._y_buffer = np.zeros(len(self.den) - 1)

    def step(self, u: float) -> float:
        """
        单步更新

        Args:
            u: 当前输入

        Returns:
            当前输出
        """
        # 更新输入缓冲
        self._u_buffer = np.roll(self._u_buffer, 1)
        self._u_buffer[0] = u

        # 计算输出
        y = np.dot(self.num, self._u_buffer)
        y -= np.dot(self.den[1:], self._y_buffer)

        # 更新输出缓冲
        self._y_buffer = np.roll(self._y_buffer, 1)
        self._y_buffer[0] = y

        return y

    def to_state_space(self) -> StateSpaceModel:
        """
        转换为状态空间模型

        Returns:
            状态空间模型
        """
        from scipy.signal import tf2ss
        A, B, C, D = tf2ss(self.num, self.den)
        return StateSpaceModel(A, B, C, D)

    def impulse_response(self, N: int) -> np.ndarray:
        """
        计算脉冲响应

        Args:
            N: 响应长度

        Returns:
            脉冲响应系数
        """
        h = np.zeros(N)
        self._u_buffer[:] = 0
        self._y_buffer[:] = 0

        for k in range(N):
            if k == 0:
                h[k] = self.step(1.0)
            else:
                h[k] = self.step(0.0)

        return h
