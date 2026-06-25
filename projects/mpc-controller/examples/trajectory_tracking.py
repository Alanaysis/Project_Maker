"""
轨迹跟踪示例

演示如何使用 MPC 控制车辆跟踪参考轨迹
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.applications import (
    TrajectoryTracker,
    TrajectoryTrackerConfig,
    DubinsCar,
)


def main():
    """主函数：演示轨迹跟踪"""

    print("=" * 60)
    print("MPC 轨迹跟踪示例")
    print("=" * 60)

    # 1. 创建轨迹跟踪器配置
    print("\n[1] 创建轨迹跟踪器配置")
    config = TrajectoryTrackerConfig(
        # 轨迹参数
        trajectory_type="circle",   # 圆形轨迹
        radius=5.0,                 # 半径 5m
        speed=1.0,                  # 速度 1 m/s
        center_x=0.0,              # 圆心
        center_y=5.0,

        # 车辆参数
        v_max=2.0,                  # 最大线速度
        omega_max=1.0,             # 最大角速度

        # MPC 参数
        prediction_horizon=15,
        control_horizon=8,
        sample_time=0.1,

        # 权重参数
        Q_position=10.0,           # 位置跟踪权重
        Q_heading=1.0,             # 航向权重
        R_velocity=0.1,            # 速度权重
        R_acceleration=0.05,       # 加速度权重

        # 约束参数
        v_min=0.0,
        v_max_constraint=2.0,
        omega_min=-1.0,
        omega_max_constraint=1.0,

        # 仿真参数
        simulation_time=60.0,      # 仿真 60s
        initial_x=5.0,            # 初始位置
        initial_y=5.0,
        initial_theta=0.0
    )

    print(f"  轨迹类型: {config.trajectory_type}")
    print(f"  轨迹半径: {config.radius} m")
    print(f"  轨迹速度: {config.speed} m/s")
    print(f"  预测时域: {config.prediction_horizon}")
    print(f"  采样时间: {config.sample_time} s")

    # 2. 创建车辆模型
    print("\n[2] 创建车辆模型")
    car = DubinsCar(
        v_max=config.v_max,
        omega_max=config.omega_max
    )
    print(f"  状态维度: {car.n_states} [x, y, theta]")
    print(f"  输入维度: {car.n_inputs} [v, omega]")
    print(f"  最大线速度: {car.v_max} m/s")
    print(f"  最大角速度: {car.omega_max} rad/s")

    # 3. 创建轨迹跟踪器
    print("\n[3] 创建 MPC 轨迹跟踪器")
    tracker = TrajectoryTracker(config, car)
    print("  跟踪器创建成功")

    # 4. 运行不同轨迹的仿真
    trajectories = ["circle", "figure8", "sine"]

    for traj_type in trajectories:
        print(f"\n[4] 运行 {traj_type} 轨迹跟踪")

        # 更新配置
        config.trajectory_type = traj_type
        tracker = TrajectoryTracker(config, car)

        # 运行仿真
        result = tracker.simulate()

        print(f"  仿真完成")
        print(f"  仿真步数: {result.info['n_steps']}")

        # 计算跟踪误差
        x_actual = result.outputs[:, 0]
        y_actual = result.outputs[:, 1]

        # 生成参考轨迹
        time = result.time[:len(x_actual)]
        x_ref = np.zeros_like(x_actual)
        y_ref = np.zeros_like(y_actual)

        for i, t in enumerate(time):
            ref = tracker.get_reference_trajectory(t)
            x_ref[i] = ref[0]
            y_ref[i] = ref[1]

        # 计算误差
        error_x = x_actual - x_ref
        error_y = y_actual - y_ref
        error_total = np.sqrt(error_x**2 + error_y**2)

        rmse = np.sqrt(np.mean(error_total**2))
        max_error = np.max(error_total)

        print(f"  跟踪 RMSE: {rmse:.3f} m")
        print(f"  最大误差: {max_error:.3f} m")

        # 绘制结果
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"MPC 轨迹跟踪 - {traj_type} 轨迹", fontsize=14)

        # 轨迹图
        ax1 = axes[0, 0]
        ax1.plot(x_ref, y_ref, 'r--', linewidth=1.5, label='参考轨迹')
        ax1.plot(x_actual, y_actual, 'b-', linewidth=1.5, label='实际轨迹')
        ax1.plot(x_actual[0], y_actual[0], 'go', markersize=10, label='起点')
        ax1.plot(x_actual[-1], y_actual[-1], 'rs', markersize=10, label='终点')
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')
        ax1.set_title('轨迹跟踪')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')

        # 位置误差
        ax2 = axes[0, 1]
        ax2.plot(time, error_x, 'b-', linewidth=1.5, label='X 误差')
        ax2.plot(time, error_y, 'r-', linewidth=1.5, label='Y 误差')
        ax2.plot(time, error_total, 'g-', linewidth=2.0, label='总误差')
        ax2.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('时间 (s)')
        ax2.set_ylabel('误差 (m)')
        ax2.set_title('跟踪误差')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 控制输入
        ax3 = axes[1, 0]
        time_input = result.time[:len(result.inputs)]
        ax3.plot(time_input, result.inputs[:, 0], 'b-', linewidth=1.5, label='线速度 v')
        ax3.plot(time_input, result.inputs[:, 1], 'r-', linewidth=1.5, label='角速度 omega')
        ax3.set_xlabel('时间 (s)')
        ax3.set_ylabel('控制输入')
        ax3.set_title('控制输入')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 航向角
        ax4 = axes[1, 1]
        theta = result.states[:len(time), 2]
        ax4.plot(time, np.degrees(theta), 'b-', linewidth=1.5)
        ax4.set_xlabel('时间 (s)')
        ax4.set_ylabel('航向角 (°)')
        ax4.set_title('航向角变化')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

    # 5. 比较不同轨迹
    print("\n[5] 比较不同轨迹的跟踪性能")
    print(f"  {'轨迹类型':<15} {'RMSE (m)':<12} {'最大误差 (m)':<12}")
    print(f"  {'-'*40}")

    for traj_type in trajectories:
        config.trajectory_type = traj_type
        tracker = TrajectoryTracker(config, car)
        result = tracker.simulate()

        x_actual = result.outputs[:, 0]
        y_actual = result.outputs[:, 1]
        time = result.time[:len(x_actual)]

        x_ref = np.zeros_like(x_actual)
        y_ref = np.zeros_like(y_actual)
        for i, t in enumerate(time):
            ref = tracker.get_reference_trajectory(t)
            x_ref[i] = ref[0]
            y_ref[i] = ref[1]

        error_total = np.sqrt((x_actual - x_ref)**2 + (y_actual - y_ref)**2)
        rmse = np.sqrt(np.mean(error_total**2))
        max_error = np.max(error_total)

        print(f"  {traj_type:<15} {rmse:<12.3f} {max_error:<12.3f}")

    print("\n" + "=" * 60)
    print("轨迹跟踪示例完成")
    print("=" * 60)

    plt.show()


if __name__ == '__main__':
    main()
