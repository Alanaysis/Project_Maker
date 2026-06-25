"""
状态反馈控制器

状态反馈控制律: u = -K * x + r
其中:
- K: 反馈增益矩阵
- r: 参考输入

LQR控制器: 最小化 J = Σ(x^T Q x + u^T R u)
"""

import numpy as np
from scipy.linalg import solve_discrete_are
from typing import Optional, Tuple


class StateFeedbackController:
    """
    状态反馈控制器

    实现极点配置和状态反馈控制
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        K: Optional[np.ndarray] = None,
    ):
        """
        初始化状态反馈控制器

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            K: 反馈增益矩阵 (m x n)，如果为None则需要设计
        """
        self.A = np.atleast_2d(np.array(A, dtype=float))
        self.B = np.atleast_2d(np.array(B, dtype=float))
        self.n = self.A.shape[0]
        self.m = self.B.shape[1]

        if K is not None:
            self.K = np.atleast_2d(np.array(K, dtype=float))
        else:
            self.K = None

    def compute_control(self, x: np.ndarray, r: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算控制输入

        u = -K * x + r

        Args:
            x: 当前状态 (n,)
            r: 参考输入 (m,)，默认为零

        Returns:
            u: 控制输入 (m,)
        """
        if self.K is None:
            raise ValueError("反馈增益K未设置，请先调用place_poles或set_gain")

        x = np.atleast_1d(np.array(x, dtype=float)).flatten()

        if r is None:
            r = np.zeros(self.m)
        else:
            r = np.atleast_1d(np.array(r, dtype=float)).flatten()

        u = -self.K @ x + r
        return u

    def place_poles(self, desired_poles: np.ndarray) -> np.ndarray:
        """
        极点配置

        Args:
            desired_poles: 期望的闭环极点 (n,)

        Returns:
            K: 反馈增益矩阵
        """
        desired_poles = np.atleast_1d(np.array(desired_poles, dtype=float))

        if len(desired_poles) != self.n:
            raise ValueError(f"期望极点数量({len(desired_poles)})与状态维度({self.n})不匹配")

        # 使用Ackermann公式（SISO情况）
        if self.m == 1:
            K = self._ackermann(desired_poles)
        else:
            # MIMO情况使用数值方法
            K = self._place_poles_mimo(desired_poles)

        self.K = K
        return K

    def _ackermann(self, desired_poles: np.ndarray) -> np.ndarray:
        """
        Ackermann公式（SISO系统）

        Args:
            desired_poles: 期望极点

        Returns:
            K: 反馈增益 (1 x n)
        """
        A = self.A
        B = self.B.flatten()
        n = self.n

        # 计算期望特征多项式
        poly_coeffs = np.poly(desired_poles)

        # 计算 phi(A)
        phi_A = np.zeros_like(A)
        for i, coeff in enumerate(poly_coeffs):
            phi_A += coeff * np.linalg.matrix_power(A, n - i)

        # 可控性矩阵
        from .analysis import controllability_matrix
        Co = controllability_matrix(A, B.reshape(-1, 1))

        # Ackermann公式: K = [0 ... 0 1] * Co^(-1) * phi(A)
        e_n = np.zeros(n)
        e_n[-1] = 1.0
        K = e_n @ np.linalg.inv(Co) @ phi_A

        return K.reshape(1, -1)

    def _place_poles_mimo(self, desired_poles: np.ndarray) -> np.ndarray:
        """
        MIMO系统极点配置（数值方法）

        Args:
            desired_poles: 期望极点

        Returns:
            K: 反馈增益矩阵 (m x n)
        """
        from scipy.signal import place_poles

        result = place_poles(self.A, self.B, desired_poles)
        return result.gain_matrix

    def get_closed_loop_system(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取闭环系统矩阵

        Returns:
            A_cl: 闭环状态转移矩阵
            B_cl: 闭环输入矩阵
        """
        if self.K is None:
            raise ValueError("反馈增益K未设置")

        A_cl = self.A - self.B @ self.K
        B_cl = self.B.copy()

        return A_cl, B_cl

    def get_closed_loop_poles(self) -> np.ndarray:
        """获取闭环极点"""
        A_cl, _ = self.get_closed_loop_system()
        return np.linalg.eigvals(A_cl)

    def set_gain(self, K: np.ndarray):
        """设置反馈增益"""
        self.K = np.atleast_2d(np.array(K, dtype=float))

    def simulate(
        self,
        x0: np.ndarray,
        n_steps: int,
        r: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        模拟状态反馈控制的系统响应

        Args:
            x0: 初始状态 (n,)
            n_steps: 模拟步数
            r: 参考输入 (m,)

        Returns:
            states: 状态序列 (n_steps+1 x n)
            controls: 控制输入序列 (n_steps x m)
        """
        x0 = np.atleast_1d(np.array(x0, dtype=float)).flatten()

        states = np.zeros((n_steps + 1, self.n))
        controls = np.zeros((n_steps, self.m))

        states[0] = x0

        for k in range(n_steps):
            u = self.compute_control(states[k], r)
            controls[k] = u
            states[k + 1] = self.A @ states[k] + self.B @ u

        return states, controls


class LQRController:
    """
    LQR（线性二次型调节器）控制器

    最小化性能指标: J = Σ(x^T Q x + u^T R u)
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        R: np.ndarray,
        N: Optional[np.ndarray] = None,
    ):
        """
        初始化LQR控制器

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            Q: 状态权重矩阵 (n x n)，半正定
            R: 输入权重矩阵 (m x m)，正定
            N: 状态-输入交叉权重 (n x m)，默认为零
        """
        self.A = np.atleast_2d(np.array(A, dtype=float))
        self.B = np.atleast_2d(np.array(B, dtype=float))
        self.Q = np.atleast_2d(np.array(Q, dtype=float))
        self.R = np.atleast_2d(np.array(R, dtype=float))
        self.n = self.A.shape[0]
        self.m = self.B.shape[1]

        if N is not None:
            self.N = np.atleast_2d(np.array(N, dtype=float))
        else:
            self.N = np.zeros((self.n, self.m))

        # 求解离散代数Riccati方程
        self.P = self._solve_dare()
        self.K = self._compute_gain()

    def _solve_dare(self) -> np.ndarray:
        """
        求解离散代数Riccati方程

        P = A^T P A - (A^T P B + N) (R + B^T P B)^(-1) (B^T P A + N^T) + Q

        Returns:
            P: Riccati方程的解
        """
        P = solve_discrete_are(self.A, self.B, self.Q, self.R, s=self.N)
        return P

    def _compute_gain(self) -> np.ndarray:
        """
        计算LQR增益

        K = (R + B^T P B)^(-1) (B^T P A + N^T)

        Returns:
            K: LQR增益矩阵 (m x n)
        """
        BPB = self.B.T @ self.P @ self.B
        BPA = self.B.T @ self.P @ self.A

        K = np.linalg.inv(self.R + BPB) @ (BPA + self.N.T)
        return K

    def compute_control(self, x: np.ndarray, r: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算LQR控制输入

        u = -K * x + r

        Args:
            x: 当前状态 (n,)
            r: 参考输入 (m,)，默认为零

        Returns:
            u: 控制输入 (m,)
        """
        x = np.atleast_1d(np.array(x, dtype=float)).flatten()

        if r is None:
            r = np.zeros(self.m)
        else:
            r = np.atleast_1d(np.array(r, dtype=float)).flatten()

        u = -self.K @ x + r
        return u

    def get_closed_loop_system(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取闭环系统矩阵

        Returns:
            A_cl: 闭环状态转移矩阵
            B_cl: 闭环输入矩阵
        """
        A_cl = self.A - self.B @ self.K
        B_cl = self.B.copy()

        return A_cl, B_cl

    def get_cost(self, x0: np.ndarray, N: int = 100) -> float:
        """
        计算有限时间LQR成本

        J = Σ(k=0 to N-1) (x^T Q x + u^T R u)

        Args:
            x0: 初始状态
            N: 时间步数

        Returns:
            J: 总成本
        """
        x0 = np.atleast_1d(np.array(x0, dtype=float)).flatten()
        x = x0.copy()
        J = 0.0

        for _ in range(N):
            u = self.compute_control(x)
            J += x @ self.Q @ x + u @ self.R @ u
            x = self.A @ x + self.B @ u

        return J

    def simulate(
        self,
        x0: np.ndarray,
        n_steps: int,
        r: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        模拟LQR控制的系统响应

        Args:
            x0: 初始状态 (n,)
            n_steps: 模拟步数
            r: 参考输入 (m,)

        Returns:
            states: 状态序列 (n_steps+1 x n)
            controls: 控制输入序列 (n_steps x m)
        """
        x0 = np.atleast_1d(np.array(x0, dtype=float)).flatten()

        states = np.zeros((n_steps + 1, self.n))
        controls = np.zeros((n_steps, self.m))

        states[0] = x0

        for k in range(n_steps):
            u = self.compute_control(states[k], r)
            controls[k] = u
            states[k + 1] = self.A @ states[k] + self.B @ u

        return states, controls


class LQGController:
    """
    LQG（线性二次高斯）控制器

    结合LQR控制器和卡尔曼滤波器
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        Q: np.ndarray,
        R: np.ndarray,
        Qn: np.ndarray,
        Rn: np.ndarray,
    ):
        """
        初始化LQG控制器

        Args:
            A: 状态转移矩阵
            B: 输入矩阵
            C: 输出矩阵
            Q: LQR状态权重
            R: LQR输入权重
            Qn: 过程噪声协方差
            Rn: 测量噪声协方差
        """
        from .kalman_filter import KalmanFilter

        # LQR控制器
        self.lqr = LQRController(A, B, Q, R)

        # 卡尔曼滤波器
        self.kf = KalmanFilter(A, B, C, Qn, Rn)

    def compute_control(
        self,
        y: np.ndarray,
        u_prev: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        计算LQG控制输入

        Args:
            y: 测量输出
            u_prev: 上一步的控制输入

        Returns:
            u: 控制输入
        """
        # 状态估计
        self.kf.predict(u_prev)
        x_hat, _, _ = self.kf.update(y)

        # LQR控制
        u = self.lqr.compute_control(x_hat)

        return u
