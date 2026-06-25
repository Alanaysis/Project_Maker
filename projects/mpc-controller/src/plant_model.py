"""
被控对象模型 - 实现线性和非线性系统模型
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BasePlantModel(ABC):
    """被控对象基类"""

    def __init__(self, n_states: int, n_inputs: int, n_outputs: int):
        """
        初始化被控对象模型

        Args:
            n_states: 状态维度
            n_inputs: 输入维度
            n_outputs: 输出维度
        """
        self.n_states = n_states
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs

    @abstractmethod
    def step(self, state: np.ndarray, u: np.ndarray, dt: float) -> np.ndarray:
        """
        执行一步仿真

        Args:
            state: 当前状态
            u: 控制输入
            dt: 时间步长

        Returns:
            下一时刻状态
        """
        pass

    @abstractmethod
    def output(self, state: np.ndarray) -> np.ndarray:
        """
        计算系统输出

        Args:
            state: 当前状态

        Returns:
            系统输出
        """
        pass

    def linearize(self, state_op: np.ndarray, u_op: np.ndarray,
                  dt: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        在工作点处线性化（数值方法）

        Args:
            state_op: 状态工作点
            u_op: 输入工作点
            dt: 时间步长

        Returns:
            (A, B, C, D) 状态空间矩阵
        """
        eps = 1e-6
        n_x = self.n_states
        n_u = self.n_inputs

        # 计算 A 矩阵 (df/dx)
        A = np.zeros((n_x, n_x))
        f0 = self.step(state_op, u_op, dt)
        for i in range(n_x):
            state_pert = state_op.copy()
            state_pert[i] += eps
            f_pert = self.step(state_pert, u_op, dt)
            A[:, i] = (f_pert - f0) / eps

        # 计算 B 矩阵 (df/du)
        B = np.zeros((n_x, n_u))
        for i in range(n_u):
            u_pert = u_op.copy()
            u_pert[i] += eps
            f_pert = self.step(state_op, u_pert, dt)
            B[:, i] = (f_pert - f0) / eps

        # 计算 C 矩阵 (dg/dx)
        C = np.zeros((self.n_outputs, n_x))
        g0 = self.output(state_op)
        for i in range(n_x):
            state_pert = state_op.copy()
            state_pert[i] += eps
            g_pert = self.output(state_pert)
            C[:, i] = (g_pert - g0) / eps

        # D 矩阵通常为零
        D = np.zeros((self.n_outputs, n_u))

        return A, B, C, D


class LinearPlantModel(BasePlantModel):
    """
    线性时不变系统模型

    状态空间表示:
        x(k+1) = A*x(k) + B*u(k)
        y(k)   = C*x(k) + D*u(k)
    """

    def __init__(self, A: np.ndarray, B: np.ndarray,
                 C: Optional[np.ndarray] = None,
                 D: Optional[np.ndarray] = None):
        """
        初始化线性系统

        Args:
            A: 状态转移矩阵 (n x n)
            B: 输入矩阵 (n x m)
            C: 输出矩阵 (p x n)，默认为单位矩阵
            D: 前馈矩阵 (p x m)，默认为零矩阵
        """
        n_states = A.shape[0]
        n_inputs = B.shape[1]

        if C is None:
            C = np.eye(n_states)
        if D is None:
            D = np.zeros((C.shape[0], n_inputs))

        super().__init__(n_states, n_inputs, C.shape[0])

        self.A = np.array(A, dtype=float)
        self.B = np.array(B, dtype=float)
        self.C = np.array(C, dtype=float)
        self.D = np.array(D, dtype=float)

    def step(self, state: np.ndarray, u: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """
        线性系统状态更新

        Args:
            state: 当前状态 x(k)
            u: 控制输入 u(k)
            dt: 时间步长（线性系统中通常已离散化，此参数保留接口一致性）

        Returns:
            下一时刻状态 x(k+1)
        """
        return self.A @ state + self.B @ u

    def output(self, state: np.ndarray, u: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算系统输出

        Args:
            state: 当前状态
            u: 控制输入（可选）

        Returns:
            系统输出 y(k)
        """
        y = self.C @ state
        if u is not None:
            y = y + self.D @ u
        return y

    def linearize(self, state_op: np.ndarray, u_op: np.ndarray,
                  dt: float = 1.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """线性系统直接返回自身矩阵"""
        return self.A, self.B, self.C, self.D


class NonlinearPlantModel(BasePlantModel):
    """
    非线性系统模型

    支持连续时间模型，在仿真时进行离散化
    """

    def __init__(self, n_states: int, n_inputs: int, n_outputs: int,
                 dynamics_fn, output_fn=None):
        """
        初始化非线性系统

        Args:
            n_states: 状态维度
            n_inputs: 输入维度
            n_outputs: 输出维度
            dynamics_fn: 连续时间动力学函数 f(x, u) -> dx/dt
            output_fn: 输出函数 g(x) -> y，默认为全状态输出
        """
        super().__init__(n_states, n_inputs, n_outputs)
        self.dynamics_fn = dynamics_fn
        self.output_fn = output_fn

    def step(self, state: np.ndarray, u: np.ndarray, dt: float) -> np.ndarray:
        """
        使用四阶 Runge-Kutta 方法进行状态更新

        Args:
            state: 当前状态
            u: 控制输入
            dt: 时间步长

        Returns:
            下一时刻状态
        """
        # 四阶 Runge-Kutta 方法
        k1 = self.dynamics_fn(state, u)
        k2 = self.dynamics_fn(state + 0.5 * dt * k1, u)
        k3 = self.dynamics_fn(state + 0.5 * dt * k2, u)
        k4 = self.dynamics_fn(state + dt * k3, u)

        return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

    def output(self, state: np.ndarray) -> np.ndarray:
        """
        计算系统输出

        Args:
            state: 当前状态

        Returns:
            系统输出
        """
        if self.output_fn is not None:
            return self.output_fn(state)
        return state.copy()


class DoubleIntegrator(LinearPlantModel):
    """
    双积分器系统

    经典的控制问题：位置和速度的二阶系统
    状态: [位置, 速度]
    输入: 加速度

    连续时间模型:
        dx1/dt = x2
        dx2/dt = u

    离散化（零阶保持）:
        x1(k+1) = x1(k) + dt*x2(k) + 0.5*dt^2*u(k)
        x2(k+1) = x2(k) + dt*u(k)
    """

    def __init__(self, dt: float = 0.1):
        """
        初始化双积分器

        Args:
            dt: 时间步长
        """
        A = np.array([
            [1.0, dt],
            [0.0, 1.0]
        ])
        B = np.array([
            [0.5 * dt**2],
            [dt]
        ])
        super().__init__(A, B)
        self.dt = dt


class PendulumModel(NonlinearPlantModel):
    """
    倒立摆模型

    非线性动力学：
        dtheta/dt = omega
        domega/dt = -(g/L)*sin(theta) - b*omega + u/(m*L^2)

    参数:
        m: 质量 (kg)
        L: 摆长 (m)
        b: 阻尼系数
        g: 重力加速度 (m/s^2)
    """

    def __init__(self, m: float = 1.0, L: float = 1.0,
                 b: float = 0.1, g: float = 9.81):
        """
        初始化倒立摆

        Args:
            m: 质量
            L: 摆长
            b: 阻尼系数
            g: 重力加速度
        """
        self.m = m
        self.L = L
        self.b = b
        self.g = g

        def dynamics(x, u):
            theta, omega = x
            dtheta = omega
            domega = -(g / L) * np.sin(theta) - b * omega + u[0] / (m * L**2)
            return np.array([dtheta, domega])

        def output(x):
            return np.array([x[0]])  # 输出角度

        super().__init__(
            n_states=2,
            n_inputs=1,
            n_outputs=1,
            dynamics_fn=dynamics,
            output_fn=output
        )


class TankSystem(NonlinearPlantModel):
    """
    双水箱系统

    非线性动力学：
        dh1/dt = (1/A1) * (u - k1*sqrt(h1))
        dh2/dt = (1/A2) * (k1*sqrt(h1) - k2*sqrt(h2))

    参数:
        A1, A2: 水箱截面积
        k1, k2: 流出系数
    """

    def __init__(self, A1: float = 1.0, A2: float = 1.0,
                 k1: float = 0.5, k2: float = 0.5):
        """
        初始化双水箱系统

        Args:
            A1: 水箱1截面积
            A2: 水箱2截面积
            k1: 水箱1流出系数
            k2: 水箱2流出系数
        """
        self.A1 = A1
        self.A2 = A2
        self.k1 = k1
        self.k2 = k2

        def dynamics(x, u):
            h1, h2 = np.maximum(x, 0.0)  # 液位非负
            dh1 = (1.0 / A1) * (u[0] - k1 * np.sqrt(h1))
            dh2 = (1.0 / A2) * (k1 * np.sqrt(h1) - k2 * np.sqrt(h2))
            return np.array([dh1, dh2])

        def output(x):
            return np.array([x[1]])  # 输出水箱2液位

        super().__init__(
            n_states=2,
            n_inputs=1,
            n_outputs=1,
            dynamics_fn=dynamics,
            output_fn=output
        )
