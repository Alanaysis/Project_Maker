"""
状态空间模型实现

连续时间系统:
  状态方程: dx/dt = A*x + B*u
  输出方程: y = C*x + D*u

离散时间系统:
  状态方程: x(k+1) = A*x(k) + B*u(k)
  输出方程: y(k) = C*x(k) + D*u(k)

其中:
- x: 状态向量 (n x 1)
- u: 输入向量 (m x 1)
- y: 输出向量 (p x 1)
- A: 状态转移矩阵 (n x n)
- B: 输入矩阵 (n x m)
- C: 输出矩阵 (p x n)
- D: 前馈矩阵 (p x m)
"""

import numpy as np
from scipy.linalg import expm, inv
from scipy.signal import ss2tf, tf2ss, cont2discrete
from typing import Optional, Tuple, List


class ContinuousStateSpace:
    """
    连续时间状态空间模型

    dx/dt = A*x + B*u
    y = C*x + D*u
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: Optional[np.ndarray] = None,
    ):
        """
        初始化连续时间状态空间模型

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            C: 输出矩阵 (p x n)
            D: 前馈矩阵 (p x m)，默认为零矩阵
        """
        self.A = np.atleast_2d(np.array(A, dtype=float))
        self.B = np.atleast_2d(np.array(B, dtype=float))
        self.C = np.atleast_2d(np.array(C, dtype=float))

        self.n_states = self.A.shape[0]
        self.n_inputs = self.B.shape[1]
        self.n_outputs = self.C.shape[0]

        if D is None:
            self.D = np.zeros((self.n_outputs, self.n_inputs))
        else:
            self.D = np.atleast_2d(np.array(D, dtype=float))

        self._validate_dimensions()

    def _validate_dimensions(self):
        """验证矩阵维度一致性"""
        n = self.n_states
        m = self.n_inputs
        p = self.n_outputs

        assert self.A.shape == (n, n), f"A矩阵维度错误: {self.A.shape}, 期望 ({n}, {n})"
        assert self.B.shape == (n, m), f"B矩阵维度错误: {self.B.shape}, 期望 ({n}, {m})"
        assert self.C.shape == (p, n), f"C矩阵维度错误: {self.C.shape}, 期望 ({p}, {n})"
        assert self.D.shape == (p, m), f"D矩阵维度错误: {self.D.shape}, 期望 ({p}, {m})"

    def get_eigenvalues(self) -> np.ndarray:
        """获取系统特征值（连续时间极点）"""
        return np.linalg.eigvals(self.A)

    def is_stable(self) -> bool:
        """判断连续时间系统是否稳定（所有特征值实部 < 0）"""
        eigenvalues = self.get_eigenvalues()
        return bool(np.all(np.real(eigenvalues) < 0))

    def get_transfer_function(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取传递函数 G(s) = C*(sI-A)^(-1)*B + D

        仅适用于SISO系统

        Returns:
            num: 分子多项式系数（s的降幂排列）
            den: 分母多项式系数（s的降幂排列）
        """
        if self.n_inputs != 1 or self.n_outputs != 1:
            raise ValueError("传递函数仅适用于SISO系统")

        num, den = ss2tf(self.A, self.B, self.C, self.D)
        return num.flatten(), den

    def simulate(
        self,
        x0: np.ndarray,
        u_func,
        t_span: Tuple[float, float],
        dt: float = 0.01,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        使用前向欧拉法仿真连续时间系统

        Args:
            x0: 初始状态 (n,)
            u_func: 输入函数 u(t) -> (m,)
            t_span: 时间范围 (t_start, t_end)
            dt: 仿真步长

        Returns:
            t: 时间向量
            states: 状态序列
            outputs: 输出序列
        """
        x0 = np.atleast_1d(np.array(x0, dtype=float)).flatten()

        t_start, t_end = t_span
        t = np.arange(t_start, t_end + dt / 2, dt)
        n_steps = len(t)

        states = np.zeros((n_steps, self.n_states))
        outputs = np.zeros((n_steps, self.n_outputs))
        states[0] = x0

        for k in range(n_steps - 1):
            u_k = np.atleast_1d(np.array(u_func(t[k]), dtype=float)).flatten()
            # 输出方程
            outputs[k] = self.C @ states[k] + self.D @ u_k
            # 前向欧拉: x(k+1) = x(k) + dt * (A*x(k) + B*u(k))
            states[k + 1] = states[k] + dt * (self.A @ states[k] + self.B @ u_k)

        # 最后一步的输出
        u_last = np.atleast_1d(np.array(u_func(t[-1]), dtype=float)).flatten()
        outputs[-1] = self.C @ states[-1] + self.D @ u_last

        return t, states, outputs

    def discretize(
        self,
        dt: float,
        method: str = "zoh",
    ) -> "StateSpaceModel":
        """
        将连续时间系统离散化

        Args:
            dt: 采样时间
            method: 离散化方法
                - 'zoh': 零阶保持器（默认）
                - 'foh': 一阶保持器
                - 'impulse': 脉冲不变法
                - 'tustin': 双线性变换（Tustin）
                - 'euler': 前向欧拉法

        Returns:
            离散时间状态空间模型
        """
        if method == "euler":
            # 前向欧拉法
            Ad = np.eye(self.n_states) + self.A * dt
            Bd = self.B * dt
            Cd = self.C.copy()
            Dd = self.D.copy()
        else:
            # 使用scipy的cont2discrete
            Ad, Bd, Cd, Dd, _ = cont2discrete(
                (self.A, self.B, self.C, self.D),
                dt,
                method=method,
            )

        return StateSpaceModel(Ad, Bd, Cd, Dd, dt=dt)

    def __repr__(self) -> str:
        return (
            f"ContinuousStateSpace(n_states={self.n_states}, "
            f"n_inputs={self.n_inputs}, n_outputs={self.n_outputs})"
        )


class StateSpaceModel:
    """
    离散时间状态空间模型

    实现状态方程 x(k+1) = A*x(k) + B*u(k) 和输出方程 y(k) = C*x(k) + D*u(k)
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: Optional[np.ndarray] = None,
        dt: float = 1.0,
    ):
        """
        初始化状态空间模型

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            C: 输出矩阵 (p x n)
            D: 前馈矩阵 (p x m)，默认为零矩阵
            dt: 采样时间间隔
        """
        self.A = np.atleast_2d(np.array(A, dtype=float))
        self.B = np.atleast_2d(np.array(B, dtype=float))
        self.C = np.atleast_2d(np.array(C, dtype=float))
        self.dt = dt

        # 获取维度
        self.n_states = self.A.shape[0]
        self.n_inputs = self.B.shape[1]
        self.n_outputs = self.C.shape[0]

        # 设置D矩阵
        if D is None:
            self.D = np.zeros((self.n_outputs, self.n_inputs))
        else:
            self.D = np.atleast_2d(np.array(D, dtype=float))

        # 验证维度一致性
        self._validate_dimensions()

        # 状态历史
        self._state_history: List[np.ndarray] = []
        self._output_history: List[np.ndarray] = []
        self._input_history: List[np.ndarray] = []

    def _validate_dimensions(self):
        """验证矩阵维度一致性"""
        n = self.n_states
        m = self.n_inputs
        p = self.n_outputs

        assert self.A.shape == (n, n), f"A矩阵维度错误: {self.A.shape}, 期望 ({n}, {n})"
        assert self.B.shape == (n, m), f"B矩阵维度错误: {self.B.shape}, 期望 ({n}, {m})"
        assert self.C.shape == (p, n), f"C矩阵维度错误: {self.C.shape}, 期望 ({p}, {n})"
        assert self.D.shape == (p, m), f"D矩阵维度错误: {self.D.shape}, 期望 ({p}, {m})"

    def simulate(
        self,
        x0: np.ndarray,
        u: np.ndarray,
        n_steps: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        模拟系统响应

        Args:
            x0: 初始状态 (n x 1)
            u: 输入序列 (n_steps x m) 或 (m,) 用于单步输入
            n_steps: 模拟步数（如果u是序列则自动推断）

        Returns:
            states: 状态序列 (n_steps+1 x n)
            outputs: 输出序列 (n_steps x p)
        """
        x0 = np.atleast_1d(np.array(x0, dtype=float)).flatten()
        u = np.atleast_2d(np.array(u, dtype=float))

        if u.shape[0] == 1 and n_steps is not None:
            u = np.tile(u, (n_steps, 1))
        elif n_steps is None:
            n_steps = u.shape[0]
        else:
            u = u[:n_steps]

        states = np.zeros((n_steps + 1, self.n_states))
        outputs = np.zeros((n_steps, self.n_outputs))

        states[0] = x0

        for k in range(n_steps):
            x = states[k]
            u_k = u[k]

            # 输出方程: y = C*x + D*u
            outputs[k] = self.C @ x + self.D @ u_k

            # 状态方程: x(k+1) = A*x + B*u
            states[k + 1] = self.A @ x + self.B @ u_k

        return states, outputs

    def step(self, x: np.ndarray, u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        单步仿真

        Args:
            x: 当前状态 (n,)
            u: 当前输入 (m,)

        Returns:
            x_next: 下一状态 (n,)
            y: 当前输出 (p,)
        """
        x = np.atleast_1d(np.array(x, dtype=float)).flatten()
        u = np.atleast_1d(np.array(u, dtype=float)).flatten()

        y = self.C @ x + self.D @ u
        x_next = self.A @ x + self.B @ u

        return x_next, y

    def get_eigenvalues(self) -> np.ndarray:
        """获取系统特征值（极点）"""
        return np.linalg.eigvals(self.A)

    def is_stable(self) -> bool:
        """判断离散时间系统是否稳定（所有特征值模 < 1）"""
        eigenvalues = self.get_eigenvalues()
        return bool(np.all(np.abs(eigenvalues) < 1.0))

    def get_transfer_function(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取离散传递函数 H(z) = C*(zI-A)^(-1)*B + D

        仅适用于SISO系统

        Returns:
            num: 分子多项式系数（z的降幂排列）
            den: 分母多项式系数（z的降幂排列）
        """
        if self.n_inputs != 1 or self.n_outputs != 1:
            raise ValueError("传递函数仅适用于SISO系统")

        num, den = ss2tf(self.A, self.B, self.C, self.D)
        return num.flatten(), den

    def get_transfer_function_coeffs(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取传递函数系数（SISO系统）- 向后兼容"""
        return self.get_transfer_function()

    def to_continuous(self) -> ContinuousStateSpace:
        """
        将离散时间系统转换为连续时间系统（逆离散化）

        使用矩阵对数: A_c = log(A_d) / dt

        Returns:
            连续时间状态空间模型
        """
        from scipy.linalg import logm

        Ac = logm(self.A) / self.dt
        # B_c = A_c * (A_d - I)^(-1) * B_d （当A_c可逆时）
        Bc = np.linalg.solve(
            self.A - np.eye(self.n_states),
            self.B,
        )
        # 修正: B_c = A * (A_d - I)^(-1) * B_d * dt 近似
        # 更精确: B_c = inv(A_c) * (exp(A_c*dt) - I)^(-1) * B_d
        # 简化处理
        try:
            Bc = np.linalg.solve(Ac, (expm(Ac * self.dt) - np.eye(self.n_states))) @ self.B / self.dt
        except np.linalg.LinAlgError:
            Bc = np.linalg.solve(
                self.A - np.eye(self.n_states),
                self.B,
            )

        return ContinuousStateSpace(Ac, Bc, self.C.copy(), self.D.copy())

    def get_step_response(
        self, n_steps: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算阶跃响应

        Args:
            n_steps: 响应步数

        Returns:
            t: 时间向量
            y: 输出响应
        """
        x0 = np.zeros(self.n_states)
        u = np.ones((n_steps, self.n_inputs))
        states, outputs = self.simulate(x0, u)
        t = np.arange(n_steps + 1) * self.dt
        return t, outputs

    def get_impulse_response(
        self, n_steps: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算脉冲响应

        Args:
            n_steps: 响应步数

        Returns:
            t: 时间向量
            y: 输出响应
        """
        x0 = np.zeros(self.n_states)
        u = np.zeros((n_steps, self.n_inputs))
        u[0] = 1.0
        states, outputs = self.simulate(x0, u)
        t = np.arange(n_steps + 1) * self.dt
        return t, outputs

    @staticmethod
    def from_continuous(
        A_c: np.ndarray,
        B_c: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        dt: float,
        method: str = "zoh",
    ) -> "StateSpaceModel":
        """
        从连续时间系统创建离散时间系统

        Args:
            A_c: 连续时间状态转移矩阵
            B_c: 连续时间输入矩阵
            C: 输出矩阵
            D: 前馈矩阵
            dt: 采样时间
            method: 离散化方法

        Returns:
            离散时间状态空间模型
        """
        cs = ContinuousStateSpace(A_c, B_c, C, D)
        return cs.discretize(dt, method=method)

    def __repr__(self) -> str:
        return (
            f"StateSpaceModel(n_states={self.n_states}, "
            f"n_inputs={self.n_inputs}, n_outputs={self.n_outputs}, dt={self.dt})"
        )
