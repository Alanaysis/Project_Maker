"""
温度控制自适应示例

演示自适应控制器在温度控制系统中的应用。

温度控制系统特点：
- 一阶惯性环节 (热容量)
- 参数时变 (环境温度变化、材料老化)
- 存在扰动 (环境温度、负载变化)
- 传感器噪声
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
from src.reference_model import create_first_order_model
from src.plant_model import (
    PlantModel, PlantType, PlantParameters,
    create_first_order_plant,
)
from src.simulation import SimulationConfig, ReferenceSignal
from src.adaptive_controller import AdaptationLaw, SelfTuningController


class TemperaturePlant:
    """
    温度控制系统被控对象

    模型: C * dT/dt = -h * (T - T_env) + P * u + d(t)

    其中:
    - C: 热容量 (J/K)
    - h: 传热系数 (W/K)
    - T_env: 环境温度 (K)
    - P: 加热功率系数 (W)
    - u: 控制信号 (0~1)
    - d(t): 扰动 (W)

    参数会随时间缓慢变化 (模拟材料老化、环境变化)
    """

    def __init__(
        self,
        thermal_capacity: float = 500.0,  # 热容量 J/K
        heat_transfer: float = 10.0,       # 传热系数 W/K
        power_coefficient: float = 100.0,  # 功率系数 W
        ambient_temp: float = 25.0,        # 环境温度 C
        initial_temp: float = 25.0,        # 初始温度 C
        noise_std: float = 0.5,            # 传感器噪声 C
    ):
        self.C = thermal_capacity
        self.h = heat_transfer
        self.P = power_coefficient
        self.T_env = ambient_temp
        self.T = initial_temp
        self.noise_std = noise_std

        self.time = 0.0
        self._history = []

    def update(self, control_input: float, dt: float) -> float:
        """
        更新温度状态

        参数：
            control_input: 控制信号 u (0~1)
            dt: 时间步长 (s)

        返回：
            测量温度 (含噪声)
        """
        # 限制控制信号范围
        u = np.clip(control_input, 0.0, 1.0)

        # 参数随时间缓慢变化 (模拟老化)
        h_t = self.h * (1.0 + 0.1 * np.sin(0.05 * self.time))
        P_t = self.P * (1.0 - 0.05 * self.time / 1000.0)  # 功率缓慢下降

        # 环境温度变化 (昼夜温差)
        T_env_t = self.T_env + 3.0 * np.sin(2 * np.pi * self.time / 86400.0)

        # 热力学方程: C * dT/dt = -h * (T - T_env) + P * u
        dT_dt = (-h_t * (self.T - T_env_t) + P_t * u) / self.C
        self.T += dT_dt * dt

        # 添加传感器噪声
        noise = np.random.normal(0, self.noise_std)
        measured_temp = self.T + noise

        self.time += dt

        self._history.append({
            "time": self.time,
            "actual_temp": self.T,
            "measured_temp": measured_temp,
            "control": u,
            "ambient_temp": T_env_t,
        })

        return measured_temp

    def get_output(self) -> float:
        """获取当前温度"""
        return self.T

    def reset(self):
        """重置状态"""
        self.T = self.T_env
        self.time = 0.0
        self._history.clear()


def temperature_mrac_control():
    """
    温度控制 - MRAC 方法

    使用模型参考自适应控制实现温度跟踪
    """
    print("=" * 60)
    print("温度控制系统 - MRAC 自适应控制")
    print("=" * 60)

    # 创建参考模型 (期望的温度响应)
    # 时间常数 30s, 稳态增益 1.0 (归一化)
    ref_model = create_first_order_model(
        time_constant=30.0,
        steady_state_gain=1.0,
    )

    # 创建温度控制对象
    temp_plant = TemperaturePlant(
        thermal_capacity=500.0,
        heat_transfer=10.0,
        power_coefficient=100.0,
        ambient_temp=25.0,
        initial_temp=25.0,
        noise_std=0.3,
    )

    # 创建 MRAC 控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.01,
        initial_params={
            "theta_r": 0.3,
            "theta_x": np.array([0.3]),
            "theta_d": 0.0,
        },
    )

    # 目标温度曲线
    def target_temperature(t):
        """目标温度曲线"""
        if t < 60:
            return 25.0 + 20.0 * (t / 60.0)  # 升温到 45C
        elif t < 180:
            return 45.0  # 保持 45C
        elif t < 240:
            return 45.0 - 15.0 * ((t - 180) / 60.0)  # 降温到 30C
        else:
            return 30.0 + 5.0 * np.sin(2 * np.pi * (t - 240) / 120.0)  # 波动

    # 仿真参数
    dt = 1.0  # 1秒时间步长
    duration = 600.0  # 10分钟
    n_steps = int(duration / dt)

    # 记录数据
    times = np.zeros(n_steps)
    targets = np.zeros(n_steps)
    actual_temps = np.zeros(n_steps)
    control_signals = np.zeros(n_steps)
    tracking_errors = np.zeros(n_steps)

    # 运行仿真
    for i in range(n_steps):
        t = i * dt
        target = target_temperature(t)
        measured = temp_plant.get_output()

        # 归一化: 将温度差转换为归一化误差
        ref_input = (target - 25.0) / 20.0  # 归一化到 [0, 1]
        plant_output = (measured - 25.0) / 20.0

        # 计算控制信号
        u = controller.compute_control(ref_input, plant_output, dt)

        # 限制控制信号
        u = np.clip(u, 0.0, 1.0)

        # 更新温度
        temp_plant.update(u, dt)

        # 记录数据
        times[i] = t
        targets[i] = target
        actual_temps[i] = measured
        control_signals[i] = u
        tracking_errors[i] = measured - target

    # 性能分析
    mse = np.mean(tracking_errors ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(tracking_errors))
    max_error = np.max(np.abs(tracking_errors))

    print(f"\n温度控制性能:")
    print(f"  RMSE: {rmse:.3f} C")
    print(f"  MAE:  {mae:.3f} C")
    print(f"  最大误差: {max_error:.3f} C")

    # 绘制结果
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    axes[0].plot(times, targets, 'b--', label='目标温度', linewidth=2)
    axes[0].plot(times, actual_temps, 'r-', label='实际温度', linewidth=1.5)
    axes[0].set_ylabel('温度 (C)')
    axes[0].set_title('温度控制 - MRAC 自适应控制')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, tracking_errors, 'g-', linewidth=1.5)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_ylabel('跟踪误差 (C)')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(times, control_signals, 'm-', linewidth=1.5)
    axes[2].set_xlabel('时间 (s)')
    axes[2].set_ylabel('控制信号')
    axes[2].set_ylim(-0.1, 1.1)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('temperature_mrac.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n结果已保存到 temperature_mrac.png")

    return times, targets, actual_temps, control_signals


def temperature_str_control():
    """
    温度控制 - 自校正方法

    使用自校正控制实现温度调节
    """
    print("\n" + "=" * 60)
    print("温度控制系统 - 自校正控制 (STR)")
    print("=" * 60)

    # 创建温度控制对象
    temp_plant = TemperaturePlant(
        thermal_capacity=500.0,
        heat_transfer=10.0,
        power_coefficient=100.0,
        ambient_temp=25.0,
        initial_temp=25.0,
        noise_std=0.3,
    )

    # 创建自校正控制器
    controller = SelfTuningController(
        n_params=2,
        desired_poles=[0.9],
        estimation_method="forgetting_factor",
        forgetting_factor=0.98,
        adaptation_gain=0.05,
    )

    # 目标温度
    target_temp = 50.0  # 目标温度 50C

    # 仿真参数
    dt = 1.0
    duration = 600.0
    n_steps = int(duration / dt)

    # 记录数据
    times = np.zeros(n_steps)
    targets = np.full(n_steps, target_temp)
    actual_temps = np.zeros(n_steps)
    control_signals = np.zeros(n_steps)
    param_estimates = np.zeros((n_steps, 2))

    # 运行仿真
    for i in range(n_steps):
        t = i * dt
        measured = temp_plant.get_output()

        # 归一化
        ref_input = (target_temp - 25.0) / 20.0
        plant_output = (measured - 25.0) / 20.0

        # 构造回归向量
        phi = np.array([ref_input, -plant_output])

        # 计算控制信号
        u = controller.compute_control(ref_input, plant_output, dt, phi)
        u = np.clip(u, 0.0, 1.0)

        # 更新温度
        temp_plant.update(u, dt)

        # 记录数据
        times[i] = t
        actual_temps[i] = measured
        control_signals[i] = u
        param_estimates[i] = controller.estimated_params

    # 性能分析
    tracking_errors = actual_temps - target_temp
    rmse = np.sqrt(np.mean(tracking_errors ** 2))
    mae = np.mean(np.abs(tracking_errors))

    print(f"\n温度控制性能:")
    print(f"  RMSE: {rmse:.3f} C")
    print(f"  MAE:  {mae:.3f} C")
    print(f"  最终温度: {actual_temps[-1]:.2f} C")
    print(f"  估计参数: {controller.estimated_params}")

    # 绘制结果
    fig, axes = plt.subplots(4, 1, figsize=(12, 12))

    axes[0].plot(times, targets, 'b--', label='目标温度', linewidth=2)
    axes[0].plot(times, actual_temps, 'r-', label='实际温度', linewidth=1.5)
    axes[0].set_ylabel('温度 (C)')
    axes[0].set_title('温度控制 - 自校正控制 (STR)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, tracking_errors, 'g-', linewidth=1.5)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_ylabel('跟踪误差 (C)')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(times, control_signals, 'm-', linewidth=1.5)
    axes[2].set_ylabel('控制信号')
    axes[2].set_ylim(-0.1, 1.1)
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(times, param_estimates[:, 0], 'b-', label='参数 a', linewidth=1.5)
    axes[3].plot(times, param_estimates[:, 1], 'r-', label='参数 b', linewidth=1.5)
    axes[3].set_xlabel('时间 (s)')
    axes[3].set_ylabel('参数估计值')
    axes[3].legend()
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('temperature_str.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n结果已保存到 temperature_str.png")

    return times, targets, actual_temps, control_signals


if __name__ == "__main__":
    # 运行 MRAC 温度控制
    temperature_mrac_control()

    # 运行自校正温度控制
    temperature_str_control()
