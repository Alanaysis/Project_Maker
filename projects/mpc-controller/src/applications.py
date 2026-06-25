"""
MPC 实际应用 - 温度控制和轨迹跟踪

本模块实现两个典型的 MPC 应用场景：
1. 温度控制 - 过程控制的典型应用
2. 轨迹跟踪 - 运动控制的典型应用

这两个应用展示了 MPC 在不同领域的通用性。
"""

import numpy as np
from typing import Optional, Tuple, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .plant_model import NonlinearPlantModel, LinearPlantModel
from .mpc_controller import MPCController, MPCConfig, MPCResult
from .optimizer import MPCConstraints, MPCWeights
from .simulation import MPCSimulation, SimulationConfig, SimulationResult


# ============================================================================
# 温度控制系统
# ============================================================================

class ThermalPlant(NonlinearPlantModel):
    """
    热力学系统模型

    模型描述：
        简化的热力学系统，包含加热器和环境热交换

    动力学方程：
        dT/dt = (1/(m*c)) * (Q_in - Q_loss - Q_dist)

    其中：
        Q_in = eta * P * u         （加热功率）
        Q_loss = h * A * (T - T_env) （环境热损失）
        Q_dist                      （外部扰动）

    参数：
        m: 物体质量 (kg)
        c: 比热容 (J/(kg*K))
        eta: 加热效率
        P: 加热器最大功率 (W)
        h: 传热系数 (W/(m^2*K))
        A: 传热面积 (m^2)
        T_env: 环境温度 (K)
    """

    def __init__(self, m: float = 1.0, c: float = 4186.0, eta: float = 0.9,
                 P_max: float = 1000.0, h: float = 10.0, A: float = 0.1,
                 T_env: float = 293.15):
        """
        初始化热力学系统

        Args:
            m: 物体质量 (kg)，默认水 1kg
            c: 比热容 (J/(kg*K))，默认水的比热容
            eta: 加热效率 (0~1)
            P_max: 加热器最大功率 (W)
            h: 传热系数 (W/(m^2*K))
            A: 传热面积 (m^2)
            T_env: 环境温度 (K)，默认 20°C
        """
        self.m = m
        self.c = c
        self.eta = eta
        self.P_max = P_max
        self.h = h
        self.A = A
        self.T_env = T_env

        # 时间常数
        self.tau = m * c / (h * A) if h * A > 0 else float('inf')
        # 增益
        self.K = eta * P_max / (h * A) if h * A > 0 else float('inf')

        def dynamics(x, u):
            T = x[0]
            # 输入 u 是归一化的加热功率 [0, 1]
            Q_in = eta * P_max * np.clip(u[0], 0, 1)
            Q_loss = h * A * (T - T_env)
            dT = (Q_in - Q_loss) / (m * c)
            return np.array([dT])

        def output(x):
            return np.array([x[0]])  # 输出温度

        super().__init__(
            n_states=1,
            n_inputs=1,
            n_outputs=1,
            dynamics_fn=dynamics,
            output_fn=output
        )

    def get_operating_point(self, T_set: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算给定温度设定点的工作点

        Args:
            T_set: 设定温度 (K)

        Returns:
            (state_op, u_op) 工作点
        """
        # 稳态时: Q_in = Q_loss
        # eta * P_max * u_op = h * A * (T_set - T_env)
        u_op = self.h * self.A * (T_set - self.T_env) / (self.eta * self.P_max)
        u_op = np.clip(u_op, 0.0, 1.0)

        state_op = np.array([T_set])
        u_op = np.array([u_op])

        return state_op, u_op


@dataclass
class TemperatureControllerConfig:
    """温度控制器配置"""
    T_setpoint: float = 353.15          # 设定温度 (K)，默认 80°C
    T_initial: float = 293.15           # 初始温度 (K)，默认 20°C
    T_min: float = 273.15               # 最低温度 (K)
    T_max: float = 393.15               # 最高温度 (K)，默认 120°C
    u_min: float = 0.0                  # 最小加热功率
    u_max: float = 1.0                  # 最大加热功率
    du_max: float = 0.1                 # 最大功率变化率
    prediction_horizon: int = 20        # 预测时域
    control_horizon: int = 10           # 控制时域
    sample_time: float = 1.0            # 采样时间 (s)
    Q_temp: float = 10.0                # 温度跟踪权重
    R_power: float = 0.1                # 功率变化权重
    simulation_time: float = 600.0      # 仿真时间 (s)


class TemperatureController:
    """
    温度控制器

    使用 MPC 控制加热系统，实现精确温度控制

    特点：
    - 处理输入约束（加热功率限制）
    - 处理温度约束（安全范围）
    - 处理变化率约束（保护设备）
    - 跟踪温度设定点
    """

    def __init__(self, config: Optional[TemperatureControllerConfig] = None,
                 thermal_plant: Optional[ThermalPlant] = None):
        """
        初始化温度控制器

        Args:
            config: 控制器配置
            thermal_plant: 热力学系统模型
        """
        self.config = config or TemperatureControllerConfig()

        # 创建或使用提供的热力学系统
        if thermal_plant is not None:
            self.plant = thermal_plant
        else:
            self.plant = ThermalPlant()

        # 创建 MPC 控制器
        self._setup_mpc()

    def _setup_mpc(self):
        """设置 MPC 控制器"""
        cfg = self.config

        # MPC 配置
        mpc_config = MPCConfig(
            prediction_horizon=cfg.prediction_horizon,
            control_horizon=cfg.control_horizon,
            sample_time=cfg.sample_time
        )

        # 权重配置
        weights = MPCWeights(
            Q=np.array([[cfg.Q_temp]]),
            R=np.array([[cfg.R_power]]),
            Rd=np.array([[0.01]])
        )

        # 约束配置
        constraints = MPCConstraints(
            u_min=np.array([cfg.u_min]),
            u_max=np.array([cfg.u_max]),
            du_min=np.array([-cfg.du_max]),
            du_max=np.array([cfg.du_max])
        )

        # 创建 MPC 控制器
        self.controller = MPCController(
            plant=self.plant,
            config=mpc_config,
            weights=weights,
            constraints=constraints
        )

        # 设置工作点
        state_op, u_op = self.plant.get_operating_point(cfg.T_setpoint)
        self.controller.set_operating_point(state_op, u_op)

    def compute_control(self, T_current: float) -> MPCResult:
        """
        计算控制输入

        Args:
            T_current: 当前温度 (K)

        Returns:
            MPC 控制结果
        """
        state = np.array([T_current])
        reference = np.array([self.config.T_setpoint])

        return self.controller.compute_control(state, reference)

    def simulate(self, T_profile: Optional[Callable[[float], float]] = None,
                 disturbance: Optional[Callable[[float], float]] = None
                 ) -> SimulationResult:
        """
        运行温度控制仿真

        Args:
            T_profile: 温度设定点变化函数 f(t) -> T_setpoint
            disturbance: 外部扰动函数 f(t) -> disturbance

        Returns:
            仿真结果
        """
        cfg = self.config

        if T_profile is None:
            # 默认：阶跃变化
            def T_profile(t):
                if t < 60:
                    return 293.15  # 20°C
                elif t < 300:
                    return 353.15  # 80°C
                else:
                    return 333.15  # 60°C

        # 创建仿真环境
        sim_config = SimulationConfig(
            total_time=cfg.simulation_time,
            sample_time=cfg.sample_time
        )

        sim = MPCSimulation(self.plant, self.controller, sim_config)

        # 运行仿真
        x0 = np.array([cfg.T_initial])

        def reference_fn(t):
            return np.array([T_profile(t)])

        result = sim.run(x0, reference_fn)

        return result

    def reset(self):
        """重置控制器"""
        self.controller.reset()


# ============================================================================
# 轨迹跟踪系统
# ============================================================================

class DubinsCar(NonlinearPlantModel):
    """
    Dubins 车模型

    模型描述：
        简化的车辆运动模型，用于轨迹跟踪

    状态: [x, y, theta]
        x, y: 位置坐标
        theta: 航向角

    输入: [v, omega]
        v: 线速度
        omega: 角速度

    动力学方程：
        dx/dt = v * cos(theta)
        dy/dt = v * sin(theta)
        dtheta/dt = omega
    """

    def __init__(self, v_max: float = 2.0, omega_max: float = 1.0):
        """
        初始化 Dubins 车模型

        Args:
            v_max: 最大线速度 (m/s)
            omega_max: 最大角速度 (rad/s)
        """
        self.v_max = v_max
        self.omega_max = omega_max

        def dynamics(x, u):
            _, _, theta = x
            v = np.clip(u[0], -v_max, v_max)
            omega = np.clip(u[1], -omega_max, omega_max)

            dx = v * np.cos(theta)
            dy = v * np.sin(theta)
            dtheta = omega

            return np.array([dx, dy, dtheta])

        def output(x):
            return x[:2].copy()  # 输出位置 [x, y]

        super().__init__(
            n_states=3,
            n_inputs=2,
            n_outputs=2,
            dynamics_fn=dynamics,
            output_fn=output
        )


@dataclass
class TrajectoryTrackerConfig:
    """轨迹跟踪器配置"""
    # 参考轨迹参数
    trajectory_type: str = "circle"     # 轨迹类型: circle, figure8, line
    radius: float = 5.0                 # 圆形轨迹半径 (m)
    speed: float = 1.0                  # 轨迹速度 (m/s)
    center_x: float = 0.0              # 圆心 x 坐标
    center_y: float = 5.0              # 圆心 y 坐标

    # 车辆参数
    v_max: float = 2.0                  # 最大线速度
    omega_max: float = 1.0             # 最大角速度

    # MPC 参数
    prediction_horizon: int = 15        # 预测时域
    control_horizon: int = 8            # 控制时域
    sample_time: float = 0.1           # 采样时间

    # 权重参数
    Q_position: float = 10.0           # 位置跟踪权重
    Q_heading: float = 1.0             # 航向权重
    R_velocity: float = 0.1            # 速度权重
    R_acceleration: float = 0.05       # 加速度权重

    # 约束参数
    v_min: float = 0.0                 # 最小线速度
    v_max_constraint: float = 2.0      # 最大线速度
    omega_min: float = -1.0            # 最小角速度
    omega_max_constraint: float = 1.0  # 最大角速度

    # 仿真参数
    simulation_time: float = 60.0      # 仿真时间
    initial_x: float = 0.0            # 初始 x 位置
    initial_y: float = 0.0            # 初始 y 位置
    initial_theta: float = 0.0         # 初始航向角


class TrajectoryTracker:
    """
    轨迹跟踪器

    使用 MPC 控制车辆跟踪参考轨迹

    特点：
    - 处理非线性车辆动力学
    - 处理速度和转向约束
    - 跟踪时变参考轨迹
    - 支持多种轨迹类型
    """

    def __init__(self, config: Optional[TrajectoryTrackerConfig] = None,
                 car_model: Optional[DubinsCar] = None):
        """
        初始化轨迹跟踪器

        Args:
            config: 跟踪器配置
            car_model: 车辆模型
        """
        self.config = config or TrajectoryTrackerConfig()

        # 创建车辆模型
        if car_model is not None:
            self.plant = car_model
        else:
            self.plant = DubinsCar(
                v_max=self.config.v_max,
                omega_max=self.config.omega_max
            )

        # 创建 MPC 控制器
        self._setup_mpc()

    def _setup_mpc(self):
        """设置 MPC 控制器"""
        cfg = self.config

        # MPC 配置
        mpc_config = MPCConfig(
            prediction_horizon=cfg.prediction_horizon,
            control_horizon=cfg.control_horizon,
            sample_time=cfg.sample_time
        )

        # 权重配置
        weights = MPCWeights(
            Q=np.diag([cfg.Q_position, cfg.Q_position]),
            R=np.diag([cfg.R_velocity, cfg.R_acceleration]),
            Rd=np.diag([0.01, 0.01])
        )

        # 约束配置
        constraints = MPCConstraints(
            u_min=np.array([cfg.v_min, cfg.omega_min]),
            u_max=np.array([cfg.v_max_constraint, cfg.omega_max_constraint])
        )

        # 创建 MPC 控制器
        self.controller = MPCController(
            plant=self.plant,
            config=mpc_config,
            weights=weights,
            constraints=constraints
        )

    def get_reference_trajectory(self, t: float) -> np.ndarray:
        """
        计算参考轨迹点

        Args:
            t: 当前时间

        Returns:
            参考位置 [x_ref, y_ref]
        """
        cfg = self.config

        if cfg.trajectory_type == "circle":
            # 圆形轨迹
            omega = cfg.speed / cfg.radius
            x_ref = cfg.center_x + cfg.radius * np.cos(omega * t)
            y_ref = cfg.center_y + cfg.radius * np.sin(omega * t)

        elif cfg.trajectory_type == "figure8":
            # 8 字形轨迹
            omega = cfg.speed / cfg.radius
            x_ref = cfg.center_x + cfg.radius * np.sin(omega * t)
            y_ref = cfg.center_y + cfg.radius * np.sin(omega * t) * np.cos(omega * t)

        elif cfg.trajectory_type == "line":
            # 直线轨迹
            x_ref = cfg.center_x + cfg.speed * t
            y_ref = cfg.center_y

        elif cfg.trajectory_type == "sine":
            # 正弦轨迹
            x_ref = cfg.center_x + cfg.speed * t
            y_ref = cfg.center_y + cfg.radius * np.sin(0.5 * t)

        else:
            raise ValueError(f"未知的轨迹类型: {cfg.trajectory_type}")

        return np.array([x_ref, y_ref])

    def get_reference_sequence(self, t: float, N: int) -> np.ndarray:
        """
        计算参考轨迹序列

        Args:
            t: 当前时间
            N: 序列长度

        Returns:
            参考轨迹序列 (N x 2)
        """
        dt = self.config.sample_time
        ref_seq = np.zeros((N, 2))

        for i in range(N):
            ref_seq[i] = self.get_reference_trajectory(t + i * dt)

        return ref_seq

    def compute_control(self, state: np.ndarray, t: float) -> MPCResult:
        """
        计算控制输入

        Args:
            state: 当前状态 [x, y, theta]
            t: 当前时间

        Returns:
            MPC 控制结果
        """
        # 获取参考轨迹序列
        ref_seq = self.get_reference_sequence(t, self.config.prediction_horizon)

        return self.controller.compute_control(state, ref_seq)

    def simulate(self, trajectory_type: Optional[str] = None
                 ) -> SimulationResult:
        """
        运行轨迹跟踪仿真

        Args:
            trajectory_type: 轨迹类型覆盖

        Returns:
            仿真结果
        """
        cfg = self.config

        if trajectory_type is not None:
            cfg.trajectory_type = trajectory_type

        # 创建仿真环境
        sim_config = SimulationConfig(
            total_time=cfg.simulation_time,
            sample_time=cfg.sample_time
        )

        sim = MPCSimulation(self.plant, self.controller, sim_config)

        # 初始状态
        x0 = np.array([cfg.initial_x, cfg.initial_y, cfg.initial_theta])

        # 参考函数
        def reference_fn(t):
            return self.get_reference_trajectory(t)

        result = sim.run(x0, reference_fn)

        return result

    def reset(self):
        """重置跟踪器"""
        self.controller.reset()


# ============================================================================
# 辅助函数
# ============================================================================

def create_temperature_controller(T_setpoint: float = 353.15,
                                   T_initial: float = 293.15
                                   ) -> TemperatureController:
    """
    创建温度控制器的便捷函数

    Args:
        T_setpoint: 设定温度 (K)
        T_initial: 初始温度 (K)

    Returns:
        温度控制器实例
    """
    config = TemperatureControllerConfig(
        T_setpoint=T_setpoint,
        T_initial=T_initial
    )
    return TemperatureController(config)


def create_trajectory_tracker(trajectory_type: str = "circle",
                               radius: float = 5.0
                               ) -> TrajectoryTracker:
    """
    创建轨迹跟踪器的便捷函数

    Args:
        trajectory_type: 轨迹类型
        radius: 轨迹半径

    Returns:
        轨迹跟踪器实例
    """
    config = TrajectoryTrackerConfig(
        trajectory_type=trajectory_type,
        radius=radius
    )
    return TrajectoryTracker(config)
