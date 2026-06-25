"""
电机速度控制自适应示例

演示自适应控制器在电机速度控制系统中的应用。

电机控制系统特点：
- 二阶动态特性 (电气 + 机械)
- 非线性特性 (摩擦、饱和)
- 负载扰动
- 参数变化 (温度影响电阻)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from src import (
    MRACController,
    SimulationEngine,
    PerformanceAnalyzer,
)
from src.reference_model import create_second_order_model
from src.plant_model import (
    PlantModel, PlantType, PlantParameters,
    create_second_order_plant,
)
from src.simulation import SimulationConfig, ReferenceSignal
from src.adaptive_controller import AdaptationLaw, SelfTuningController


class MotorPlant:
    """
    直流电机速度控制系统

    电气方程: L * di/dt = -R * i - Ke * omega + V
    机械方程: J * domega/dt = Kt * i - B * omega - T_load

    状态空间:
    x = [i, omega]^T
    ẋ = A * x + B * V + E * T_load

    其中:
    - i: 电枢电流 (A)
    - omega: 转速 (rad/s)
    - V: 电枢电压 (V)
    - T_load: 负载转矩 (Nm)
    - R: 电枢电阻 (Ohm), 随温度变化
    - L: 电枢电感 (H)
    - Ke: 反电动势常数 (V*s/rad)
    - Kt: 转矩常数 (Nm/A)
    - J: 转动惯量 (kg*m^2)
    - B: 粘性摩擦系数 (Nm*s/rad)
    """

    def __init__(
        self,
        resistance: float = 1.0,        # 电枢电阻 Ohm
        inductance: float = 0.01,       # 电枢电感 H
        back_emf_const: float = 0.1,    # 反电动势常数 V*s/rad
        torque_const: float = 0.1,      # 转矩常数 Nm/A
        inertia: float = 0.01,          # 转动惯量 kg*m^2
        friction: float = 0.001,        # 粘性摩擦 Nm*s/rad
        max_voltage: float = 48.0,      # 最大电压 V
        noise_std: float = 0.1,         # 速度传感器噪声 rad/s
    ):
        self.R = resistance
        self.L = inductance
        self.Ke = back_emf_const
        self.Kt = torque_const
        self.J = inertia
        self.B = friction
        self.V_max = max_voltage
        self.noise_std = noise_std

        # 状态变量
        self.current = 0.0      # 电枢电流 A
        self.omega = 0.0        # 转速 rad/s
        self.time = 0.0

        # 负载
        self.T_load = 0.0

        self._history = []

    def update(self, control_voltage: float, dt: float) -> float:
        """
        更新电机状态

        参数：
            control_voltage: 控制电压 V
            dt: 时间步长 s

        返回：
            测量转速 (含噪声)
        """
        # 限制电压范围
        V = np.clip(control_voltage, -self.V_max, self.V_max)

        # 电阻随温度变化 (模拟温升)
        R_t = self.R * (1.0 + 0.004 * self.time * 0.01)

        # RK4 积分
        def derivatives(i, omega, V, T_load):
            di_dt = (-R_t * i - self.Ke * omega + V) / self.L
            domega_dt = (self.Kt * i - self.B * omega - T_load) / self.J
            return di_dt, domega_dt

        # RK4
        k1_i, k1_w = derivatives(self.current, self.omega, V, self.T_load)
        k2_i, k2_w = derivatives(
            self.current + 0.5 * dt * k1_i,
            self.omega + 0.5 * dt * k1_w,
            V, self.T_load
        )
        k3_i, k3_w = derivatives(
            self.current + 0.5 * dt * k2_i,
            self.omega + 0.5 * dt * k2_w,
            V, self.T_load
        )
        k4_i, k4_w = derivatives(
            self.current + dt * k3_i,
            self.omega + dt * k3_w,
            V, self.T_load
        )

        self.current += (dt / 6.0) * (k1_i + 2 * k2_i + 2 * k3_i + k4_i)
        self.omega += (dt / 6.0) * (k1_w + 2 * k2_w + 2 * k3_w + k4_w)

        # 添加传感器噪声
        noise = np.random.normal(0, self.noise_std)
        measured_omega = self.omega + noise

        self.time += dt

        self._history.append({
            "time": self.time,
            "actual_omega": self.omega,
            "measured_omega": measured_omega,
            "current": self.current,
            "voltage": V,
            "load_torque": self.T_load,
        })

        return measured_omega

    def get_output(self) -> float:
        """获取当前转速"""
        return self.omega

    def set_load_torque(self, T_load: float):
        """设置负载转矩"""
        self.T_load = T_load

    def reset(self):
        """重置状态"""
        self.current = 0.0
        self.omega = 0.0
        self.time = 0.0
        self.T_load = 0.0
        self._history.clear()


def motor_mrac_control():
    """
    电机速度控制 - MRAC 方法

    使用模型参考自适应控制实现速度跟踪
    """
    print("=" * 60)
    print("电机速度控制 - MRAC 自适应控制")
    print("=" * 60)

    # 创建参考模型 (期望的速度响应)
    # 自然频率 10 rad/s, 阻尼比 0.7
    ref_model = create_second_order_model(
        natural_frequency=10.0,
        damping_ratio=0.7,
    )

    # 创建电机对象
    motor = MotorPlant(
        resistance=1.0,
        inductance=0.01,
        back_emf_const=0.1,
        torque_const=0.1,
        inertia=0.01,
        friction=0.001,
        max_voltage=48.0,
        noise_std=0.5,
    )

    # 创建 MRAC 控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.1,
        initial_params={
            "theta_r": 5.0,
            "theta_x": np.array([5.0]),
            "theta_d": 0.0,
        },
    )

    # 目标速度曲线
    def target_speed(t):
        """目标速度曲线 (rad/s)"""
        if t < 0.5:
            return 100.0 * (t / 0.5)  # 加速到 100 rad/s
        elif t < 2.0:
            return 100.0  # 保持 100 rad/s
        elif t < 3.0:
            return 100.0 + 50.0 * ((t - 2.0) / 1.0)  # 加速到 150 rad/s
        elif t < 5.0:
            return 150.0  # 保持 150 rad/s
        elif t < 6.0:
            return 150.0 - 100.0 * ((t - 5.0) / 1.0)  # 减速到 50 rad/s
        else:
            return 50.0 + 30.0 * np.sin(2 * np.pi * (t - 6.0) / 2.0)  # 正弦跟踪

    # 仿真参数
    dt = 0.001  # 1ms 时间步长
    duration = 10.0  # 10秒
    n_steps = int(duration / dt)

    # 记录数据
    times = np.zeros(n_steps)
    targets = np.zeros(n_steps)
    actual_speeds = np.zeros(n_steps)
    control_voltages = np.zeros(n_steps)
    currents = np.zeros(n_steps)

    # 运行仿真
    for i in range(n_steps):
        t = i * dt
        target = target_speed(t)
        measured = motor.get_output()

        # 归一化: 将速度转换为归一化值
        ref_input = target / 150.0  # 归一化到 [0, 1]
        plant_output = measured / 150.0

        # 计算控制信号
        u = controller.compute_control(ref_input, plant_output, dt)

        # 转换为电压 (限制范围)
        voltage = np.clip(u * 48.0, -48.0, 48.0)

        # 负载扰动
        if t > 3.0 and t < 5.0:
            motor.set_load_torque(0.5)  # 施加负载
        else:
            motor.set_load_torque(0.0)

        # 更新电机
        motor.update(voltage, dt)

        # 记录数据
        times[i] = t
        targets[i] = target
        actual_speeds[i] = measured
        control_voltages[i] = voltage
        currents[i] = motor.current

    # 性能分析
    tracking_errors = actual_speeds - targets
    rmse = np.sqrt(np.mean(tracking_errors ** 2))
    mae = np.mean(np.abs(tracking_errors))
    max_error = np.max(np.abs(tracking_errors))

    print(f"\n电机速度控制性能:")
    print(f"  RMSE: {rmse:.3f} rad/s")
    print(f"  MAE:  {mae:.3f} rad/s")
    print(f"  最大误差: {max_error:.3f} rad/s")

    # 绘制结果
    fig, axes = plt.subplots(4, 1, figsize=(12, 12))

    axes[0].plot(times, targets, 'b--', label='目标速度', linewidth=2)
    axes[0].plot(times, actual_speeds, 'r-', label='实际速度', linewidth=1.5)
    axes[0].set_ylabel('速度 (rad/s)')
    axes[0].set_title('电机速度控制 - MRAC 自适应控制')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, tracking_errors, 'g-', linewidth=1.5)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_ylabel('跟踪误差 (rad/s)')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(times, control_voltages, 'm-', linewidth=1.5)
    axes[2].set_ylabel('控制电压 (V)')
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(times, currents, 'c-', linewidth=1.5)
    axes[3].set_xlabel('时间 (s)')
    axes[3].set_ylabel('电枢电流 (A)')
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('motor_mrac.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n结果已保存到 motor_mrac.png")

    return times, targets, actual_speeds, control_voltages


def motor_str_control():
    """
    电机速度控制 - 自校正方法

    使用自校正控制实现速度调节
    """
    print("\n" + "=" * 60)
    print("电机速度控制 - 自校正控制 (STR)")
    print("=" * 60)

    # 创建电机对象
    motor = MotorPlant(
        resistance=1.0,
        inductance=0.01,
        back_emf_const=0.1,
        torque_const=0.1,
        inertia=0.01,
        friction=0.001,
        max_voltage=48.0,
        noise_std=0.3,
    )

    # 创建自校正控制器
    controller = SelfTuningController(
        n_params=2,
        desired_poles=[0.8],
        estimation_method="forgetting_factor",
        forgetting_factor=0.99,
        adaptation_gain=0.01,
    )

    # 目标速度
    target_speed = 120.0  # rad/s

    # 仿真参数
    dt = 0.001
    duration = 10.0
    n_steps = int(duration / dt)

    # 记录数据
    times = np.zeros(n_steps)
    targets = np.full(n_steps, target_speed)
    actual_speeds = np.zeros(n_steps)
    control_voltages = np.zeros(n_steps)
    param_estimates = np.zeros((n_steps, 2))

    # 运行仿真
    for i in range(n_steps):
        t = i * dt
        measured = motor.get_output()

        # 归一化
        ref_input = target_speed / 150.0
        plant_output = measured / 150.0

        # 构造回归向量
        phi = np.array([ref_input, -plant_output])

        # 计算控制信号
        u = controller.compute_control(ref_input, plant_output, dt, phi)

        # 转换为电压
        voltage = np.clip(u * 48.0, -48.0, 48.0)

        # 负载扰动
        if t > 3.0:
            motor.set_load_torque(0.3)
        else:
            motor.set_load_torque(0.0)

        # 更新电机
        motor.update(voltage, dt)

        # 记录数据
        times[i] = t
        actual_speeds[i] = measured
        control_voltages[i] = voltage
        param_estimates[i] = controller.estimated_params

    # 性能分析
    tracking_errors = actual_speeds - target_speed
    rmse = np.sqrt(np.mean(tracking_errors ** 2))
    mae = np.mean(np.abs(tracking_errors))

    print(f"\n电机速度控制性能:")
    print(f"  RMSE: {rmse:.3f} rad/s")
    print(f"  MAE:  {mae:.3f} rad/s")
    print(f"  最终速度: {actual_speeds[-1]:.2f} rad/s")
    print(f"  估计参数: {controller.estimated_params}")

    # 绘制结果
    fig, axes = plt.subplots(4, 1, figsize=(12, 12))

    axes[0].plot(times, targets, 'b--', label='目标速度', linewidth=2)
    axes[0].plot(times, actual_speeds, 'r-', label='实际速度', linewidth=1.5)
    axes[0].set_ylabel('速度 (rad/s)')
    axes[0].set_title('电机速度控制 - 自校正控制 (STR)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, tracking_errors, 'g-', linewidth=1.5)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_ylabel('跟踪误差 (rad/s)')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(times, control_voltages, 'm-', linewidth=1.5)
    axes[2].set_ylabel('控制电压 (V)')
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(times, param_estimates[:, 0], 'b-', label='参数 a', linewidth=1.5)
    axes[3].plot(times, param_estimates[:, 1], 'r-', label='参数 b', linewidth=1.5)
    axes[3].set_xlabel('时间 (s)')
    axes[3].set_ylabel('参数估计值')
    axes[3].legend()
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('motor_str.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n结果已保存到 motor_str.png")

    return times, targets, actual_speeds, control_voltages


if __name__ == "__main__":
    # 运行 MRAC 电机控制
    motor_mrac_control()

    # 运行自校正电机控制
    motor_str_control()
