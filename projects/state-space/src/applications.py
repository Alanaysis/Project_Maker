"""
实际应用案例

1. 倒立摆控制
2. 直流电机控制
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any

from .state_space_model import ContinuousStateSpace, StateSpaceModel
from .controller import LQRController, StateFeedbackController
from .observer import FullOrderObserver
from .kalman_filter import KalmanFilter
from .analysis import is_controllable, is_observable


class InvertedPendulum:
    """
    倒立摆系统

    状态变量: x = [theta, theta_dot, x, x_dot]
    - theta: 摆杆角度（相对于垂直方向）
    - theta_dot: 摆杆角速度
    - x: 小车位置
    - x_dot: 小车速度

    控制输入: u = F（施加在小车上的水平力）

    非线性模型:
      (M+m)*x_ddot + b*x_ddot + m*l*theta_ddot*cos(theta)
          - m*l*theta_dot^2*sin(theta) = F
      (I+m*l^2)*theta_ddot + m*g*l*sin(theta)
          + m*l*x_ddot*cos(theta) = 0

    线性化模型（在theta=0附近）:
      x_ddot = -(b*(I+m*l^2)) / denom * x_dot
               + (m^2*g*l^2) / denom * theta
               - (m*l) / denom * u
      theta_ddot = (m*g*l*(M+m)) / denom * theta
                   + (b*m*l) / denom * x_dot
                   + (m*l) / denom * u
    其中 denom = (M+m)*(I+m*l^2) - (m*l)^2
    """

    def __init__(
        self,
        M: float = 0.5,     # 小车质量 (kg)
        m: float = 0.2,     # 摆杆质量 (kg)
        l: float = 0.3,     # 摆杆半长 (m)
        b: float = 0.1,     # 摩擦系数
        I: float = 0.006,   # 摆杆转动惯量 (kg*m^2)
        g: float = 9.81,    # 重力加速度 (m/s^2)
    ):
        """
        初始化倒立摆参数

        Args:
            M: 小车质量 (kg)
            m: 摆杆质量 (kg)
            l: 摆杆半长 (m)
            b: 摩擦系数
            I: 摆杆转动惯量 (kg*m^2)
            g: 重力加速度 (m/s^2)
        """
        self.M = M
        self.m = m
        self.l = l
        self.b = b
        self.I = I
        self.g = g

        # 计算线性化模型
        self._build_linearized_model()

    def _build_linearized_model(self):
        """构建线性化状态空间模型（在竖直位置theta=0附近）"""
        M = self.M
        m = self.m
        l = self.l
        b = self.b
        I = self.I
        g = self.g

        denom = (M + m) * (I + m * l**2) - (m * l) ** 2

        # 状态: [x, x_dot, theta, theta_dot]
        A_c = np.array([
            [0, 1, 0, 0],
            [0, -(b * (I + m * l**2)) / denom,
             (m**2 * g * l**2) / denom, 0],
            [0, 0, 0, 1],
            [0, -(b * m * l) / denom,
             (m * g * l * (M + m)) / denom, 0],
        ])

        B_c = np.array([
            [0],
            [(I + m * l**2) / denom],
            [0],
            [m * l / denom],
        ])

        # 输出: 测量角度和位置
        C = np.array([
            [1, 0, 0, 0],  # 测量位置 x
            [0, 0, 1, 0],  # 测量角度 theta
        ])

        D = np.array([
            [0],
            [0],
        ])

        self.A_c = A_c
        self.B_c = B_c
        self.C = C
        self.D = D

        # 创建连续时间模型
        self.continuous_model = ContinuousStateSpace(A_c, B_c, C, D)

    def discretize(self, dt: float = 0.01) -> StateSpaceModel:
        """
        离散化模型

        Args:
            dt: 采样时间

        Returns:
            离散时间状态空间模型
        """
        return self.continuous_model.discretize(dt, method="zoh")

    def design_lqr(
        self,
        dt: float = 0.01,
        Q: Optional[np.ndarray] = None,
        R: Optional[np.ndarray] = None,
    ) -> LQRController:
        """
        设计LQR控制器

        Args:
            dt: 采样时间
            Q: 状态权重矩阵 (4x4)，默认为对角矩阵
            R: 输入权重矩阵 (1x1)，默认为标量

        Returns:
            LQR控制器
        """
        model = self.discretize(dt)

        if Q is None:
            # 默认权重: 位置和角度权重较大
            Q = np.diag([100, 1, 100, 1])

        if R is None:
            R = np.array([[1.0]])

        return LQRController(model.A, model.B, Q, R)

    def design_observer(
        self,
        dt: float = 0.01,
        desired_poles: Optional[np.ndarray] = None,
    ) -> Tuple[FullOrderObserver, StateSpaceModel]:
        """
        设计状态观测器

        Args:
            dt: 采样时间
            desired_poles: 期望观测器极点

        Returns:
            观测器和离散模型
        """
        model = self.discretize(dt)
        observer = FullOrderObserver(model.A, model.B, model.C)

        if desired_poles is None:
            # 观测器极点应比控制器快
            desired_poles = np.array([0.5, 0.5, 0.5, 0.5])

        observer.design_by_poles(desired_poles)
        return observer, model

    def get_parameters(self) -> Dict[str, float]:
        """获取系统参数"""
        return {
            "M": self.M,
            "m": self.m,
            "l": self.l,
            "b": self.b,
            "I": self.I,
            "g": self.g,
        }

    def check_controllability(self, dt: float = 0.01) -> bool:
        """检查离散化系统的可控性"""
        model = self.discretize(dt)
        return is_controllable(model.A, model.B)

    def check_observability(self, dt: float = 0.01) -> bool:
        """检查离散化系统的可观性"""
        model = self.discretize(dt)
        return is_observable(model.A, model.C)

    def simulate_nonlinear(
        self,
        x0: np.ndarray,
        u_func,
        t_span: Tuple[float, float],
        dt: float = 0.001,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        仿真非线性倒立摆模型（使用前向欧拉法）

        Args:
            x0: 初始状态 [x, x_dot, theta, theta_dot]
            u_func: 控制输入函数 u(t, x) -> F
            t_span: 时间范围
            dt: 仿真步长

        Returns:
            t: 时间向量
            states: 状态序列
        """
        M = self.M
        m = self.m
        l = self.l
        b = self.b
        I = self.I
        g = self.g

        t_start, t_end = t_span
        t = np.arange(t_start, t_end + dt / 2, dt)
        n_steps = len(t)

        states = np.zeros((n_steps, 4))
        states[0] = x0

        for k in range(n_steps - 1):
            x = states[k]
            theta = x[2]
            theta_dot = x[3]
            x_dot = x[1]

            # 控制输入
            F = u_func(t[k], x)

            # 非线性动力学
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            denom = (M + m) * (I + m * l**2) - (m * l * cos_theta) ** 2

            theta_ddot = (
                (M + m) * m * g * l * sin_theta
                - m * l * cos_theta * (b * x_dot - m * l * theta_dot**2 * sin_theta + F)
            ) / (denom + 1e-10)

            x_ddot = (
                F - b * x_dot + m * l * (theta_dot**2 * sin_theta - theta_ddot * cos_theta)
            ) / (M + m)

            # 前向欧拉积分
            states[k + 1] = x + dt * np.array([
                x_dot,
                x_ddot,
                theta_dot,
                theta_ddot,
            ])

        return t, states

    def __repr__(self) -> str:
        return (
            f"InvertedPendulum(M={self.M}, m={self.m}, "
            f"l={self.l}, b={self.b}, I={self.I})"
        )


class DCmotor:
    """
    直流电机系统

    电路方程: L * di/dt + R * i + Ke * omega = V
    机械方程: J * d_omega/dt + B * omega = Kt * i

    状态变量: x = [theta, omega, i]
    - theta: 转子角度 (rad)
    - omega: 转子角速度 (rad/s)
    - i: 电枢电流 (A)

    控制输入: u = V（电枢电压）

    输出: y = theta（转子角度）
    """

    def __init__(
        self,
        R: float = 1.0,      # 电枢电阻 (Ohm)
        L: float = 0.5,      # 电枢电感 (H)
        Ke: float = 0.01,    # 反电动势常数 (V*s/rad)
        Kt: float = 0.01,    # 转矩常数 (N*m/A)
        J: float = 0.01,     # 转子转动惯量 (kg*m^2)
        B: float = 0.1,      # 粘性摩擦系数 (N*m*s/rad)
    ):
        """
        初始化直流电机参数

        Args:
            R: 电枢电阻 (Ohm)
            L: 电枢电感 (H)
            Ke: 反电动势常数 (V*s/rad)
            Kt: 转矩常数 (N*m/A)
            J: 转子转动惯量 (kg*m^2)
            B: 粘性摩擦系数 (N*m*s/rad)
        """
        self.R = R
        self.L = L
        self.Ke = Ke
        self.Kt = Kt
        self.J = J
        self.B = B

        self._build_model()

    def _build_model(self):
        """构建状态空间模型"""
        R = self.R
        L = self.L
        Ke = self.Ke
        Kt = self.Kt
        J = self.J
        B = self.B

        # 连续时间状态空间模型
        # 状态: [theta, omega, i]
        A_c = np.array([
            [0, 1, 0],
            [0, -B / J, Kt / J],
            [0, -Ke / L, -R / L],
        ])

        B_c = np.array([
            [0],
            [0],
            [1 / L],
        ])

        # 输出: 测量角度
        C = np.array([
            [1, 0, 0],       # 角度
        ])

        D = np.array([[0]])

        self.A_c = A_c
        self.B_c = B_c
        self.C = C
        self.D = D

        self.continuous_model = ContinuousStateSpace(A_c, B_c, C, D)

    def discretize(self, dt: float = 0.001) -> StateSpaceModel:
        """
        离散化模型

        Args:
            dt: 采样时间

        Returns:
            离散时间状态空间模型
        """
        return self.continuous_model.discretize(dt, method="zoh")

    def design_lqr(
        self,
        dt: float = 0.001,
        Q: Optional[np.ndarray] = None,
        R: Optional[np.ndarray] = None,
    ) -> LQRController:
        """
        设计LQR控制器

        Args:
            dt: 采样时间
            Q: 状态权重矩阵 (3x3)
            R: 输入权重矩阵 (1x1)

        Returns:
            LQR控制器
        """
        model = self.discretize(dt)

        if Q is None:
            Q = np.diag([100, 1, 1])  # 角度权重最大

        if R is None:
            R = np.array([[0.1]])

        return LQRController(model.A, model.B, Q, R)

    def design_speed_controller(
        self,
        dt: float = 0.001,
        desired_poles: Optional[np.ndarray] = None,
    ) -> Tuple[StateFeedbackController, StateSpaceModel]:
        """
        设计速度控制器（降阶模型，忽略电感）

        Args:
            dt: 采样时间
            desired_poles: 期望闭环极点

        Returns:
            控制器和离散模型
        """
        # 简化模型: [omega, i]（忽略角度）
        A_simplified = self.A_c[1:, 1:]
        B_simplified = self.B_c[1:]
        C_simplified = np.array([[0, 1]])  # 测量电流

        model = ContinuousStateSpace(A_simplified, B_simplified, C_simplified)
        model_d = model.discretize(dt)

        controller = StateFeedbackController(model_d.A, model_d.B)

        if desired_poles is None:
            desired_poles = np.array([0.9, 0.8])

        controller.place_poles(desired_poles)
        return controller, model_d

    def get_parameters(self) -> Dict[str, float]:
        """获取系统参数"""
        return {
            "R": self.R,
            "L": self.L,
            "Ke": self.Ke,
            "Kt": self.Kt,
            "J": self.J,
            "B": self.B,
        }

    def check_controllability(self, dt: float = 0.001) -> bool:
        """检查离散化系统的可控性"""
        model = self.discretize(dt)
        return is_controllable(model.A, model.B)

    def check_observability(self, dt: float = 0.001) -> bool:
        """检查离散化系统的可观性"""
        model = self.discretize(dt)
        return is_observable(model.A, model.C)

    def simulate_linear(
        self,
        x0: np.ndarray,
        u_func,
        t_span: Tuple[float, float],
        dt: float = 0.001,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        仿真线性电机模型

        Args:
            x0: 初始状态 [theta, omega, i]
            u_func: 输入函数 u(t) -> V
            t_span: 时间范围
            dt: 仿真步长

        Returns:
            t: 时间向量
            states: 状态序列
            outputs: 输出序列
        """
        return self.continuous_model.simulate(x0, u_func, t_span, dt)

    def __repr__(self) -> str:
        return (
            f"DCmotor(R={self.R}, L={self.L}, Ke={self.Ke}, "
            f"Kt={self.Kt}, J={self.J}, B={self.B})"
        )
