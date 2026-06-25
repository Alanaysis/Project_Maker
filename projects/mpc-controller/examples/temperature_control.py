"""
温度控制示例

演示如何使用 MPC 控制温度系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.applications import (
    TemperatureController,
    TemperatureControllerConfig,
    ThermalPlant,
)


def main():
    """主函数：演示温度控制"""

    print("=" * 60)
    print("MPC 温度控制示例")
    print("=" * 60)

    # 1. 创建温度控制器配置
    print("\n[1] 创建温度控制器配置")
    config = TemperatureControllerConfig(
        T_setpoint=353.15,      # 设定温度: 80°C
        T_initial=293.15,       # 初始温度: 20°C
        T_min=273.15,           # 最低温度: 0°C
        T_max=393.15,           # 最高温度: 120°C
        u_min=0.0,              # 最小加热功率
        u_max=1.0,              # 最大加热功率
        du_max=0.1,             # 最大功率变化率
        prediction_horizon=20,  # 预测时域
        control_horizon=10,     # 控制时域
        sample_time=1.0,        # 采样时间 1s
        Q_temp=10.0,            # 温度跟踪权重
        R_power=0.1,            # 功率变化权重
        simulation_time=600.0   # 仿真时间 10 分钟
    )
    print(f"  设定温度: {config.T_setpoint - 273.15:.1f}°C")
    print(f"  初始温度: {config.T_initial - 273.15:.1f}°C")
    print(f"  采样时间: {config.sample_time} s")
    print(f"  仿真时间: {config.simulation_time} s")

    # 2. 创建热力学系统
    print("\n[2] 创建热力学系统")
    plant = ThermalPlant(
        m=1.0,          # 1 kg 水
        c=4186.0,       # 水的比热容
        eta=0.9,        # 加热效率
        P_max=1000.0,   # 1000W 加热器
        h=10.0,         # 传热系数
        A=0.1,          # 传热面积
        T_env=293.15    # 环境温度 20°C
    )
    print(f"  质量: {plant.m} kg")
    print(f"  比热容: {plant.c} J/(kg·K)")
    print(f"  加热功率: {plant.P_max} W")
    print(f"  时间常数: {plant.tau:.1f} s")

    # 3. 创建温度控制器
    print("\n[3] 创建 MPC 温度控制器")
    controller = TemperatureController(config, plant)
    print("  控制器创建成功")

    # 4. 运行仿真
    print("\n[4] 运行温度控制仿真")

    # 定义温度设定点变化
    def temperature_profile(t):
        if t < 60:
            return 293.15      # 20°C (预热)
        elif t < 180:
            return 353.15      # 80°C (加热)
        elif t < 360:
            return 333.15      # 60°C (保温)
        elif t < 480:
            return 373.15      # 100°C (高温)
        else:
            return 293.15      # 20°C (冷却)

    result = controller.simulate(T_profile=temperature_profile)

    print(f"  仿真完成")
    print(f"  仿真步数: {result.info['n_steps']}")

    # 5. 分析结果
    print("\n[5] 分析控制效果")

    # 计算跟踪误差
    T_outputs = result.outputs[:, 0]
    T_references = result.references[:, 0]

    # 只分析稳定后的误差
    steady_start = 100  # 100s 后
    if len(T_outputs) > steady_start:
        steady_error = T_outputs[steady_start:] - T_references[steady_start:]
        rmse = np.sqrt(np.mean(steady_error**2))
        max_error = np.max(np.abs(steady_error))

        print(f"  稳态 RMSE: {rmse:.2f} K ({rmse:.2f}°C)")
        print(f"  最大误差: {max_error:.2f} K ({max_error:.2f}°C)")

    # 6. 绘制结果
    print("\n[6] 绘制仿真结果")

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle("MPC 温度控制", fontsize=14)

    # 温度曲线
    time = result.time[:len(T_outputs)]
    axes[0].plot(time, T_outputs - 273.15, 'b-', linewidth=1.5, label='实际温度')
    axes[0].plot(time, T_references - 273.15, 'r--', linewidth=1.0, label='设定温度')
    axes[0].set_ylabel('温度 (°C)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title('温度跟踪')

    # 控制输入
    time_input = result.time[:len(result.inputs)]
    axes[1].plot(time_input, result.inputs[:, 0], 'g-', linewidth=1.5)
    axes[1].set_ylabel('加热功率 (归一化)')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title('控制输入')

    # 跟踪误差
    time_error = result.time[:len(T_outputs)]
    error = T_outputs - T_references
    axes[2].plot(time_error, error, 'r-', linewidth=1.5)
    axes[2].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    axes[2].set_xlabel('时间 (s)')
    axes[2].set_ylabel('温度误差 (K)')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_title('跟踪误差')

    plt.tight_layout()

    # 7. 绘制相平面
    fig2, ax = plt.subplots(figsize=(8, 6))

    # 温度 vs 加热功率
    ax.plot(T_outputs - 273.15, result.inputs[:, 0], 'b-', linewidth=1.0, alpha=0.7)
    ax.set_xlabel('温度 (°C)')
    ax.set_ylabel('加热功率')
    ax.set_title('温度-功率相平面')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    print("\n" + "=" * 60)
    print("温度控制示例完成")
    print("=" * 60)

    plt.show()


if __name__ == '__main__':
    main()
