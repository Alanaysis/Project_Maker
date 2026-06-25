"""
非线性 MPC 控制示例

演示如何使用 MPC 控制倒立摆系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.plant_model import PendulumModel
from src.mpc_controller import MPCController, MPCConfig, MPCMode
from src.optimizer import MPCConstraints, MPCWeights
from src.simulation import MPCSimulation, SimulationConfig, MPCVisualizer


def main():
    """主函数：演示非线性 MPC 控制"""

    print("=" * 60)
    print("MPC 控制器 - 非线性示例（倒立摆）")
    print("=" * 60)

    # 1. 创建倒立摆模型
    print("\n[1] 创建倒立摆模型")
    plant = PendulumModel(m=1.0, L=1.0, b=0.1, g=9.81)
    print(f"  质量: {plant.m} kg")
    print(f"  摆长: {plant.L} m")
    print(f"  阻尼: {plant.b}")
    print(f"  重力: {plant.g} m/s^2")

    # 2. 配置 MPC 参数
    print("\n[2] 配置 MPC 参数")
    config = MPCConfig(
        prediction_horizon=20,
        control_horizon=10,
        sample_time=0.05,
        mode=MPCMode.LINEAR  # 使用线性化模型
    )
    print(f"  预测时域: {config.prediction_horizon}")
    print(f"  控制时域: {config.control_horizon}")
    print(f"  采样时间: {config.sample_time} s")

    # 3. 设置权重
    print("\n[3] 设置权重矩阵")
    weights = MPCWeights(
        Q=np.diag([100.0, 1.0]),    # 角度权重高
        R=np.array([[0.01]]),        # 输入权重小
        Rd=np.array([[0.1]])         # 变化率权重
    )

    # 4. 设置约束
    print("\n[4] 设置约束")
    constraints = MPCConstraints(
        u_min=np.array([-20.0]),     # 最大力矩
        u_max=np.array([20.0]),
    )
    print(f"  力矩范围: [{constraints.u_min[0]}, {constraints.u_max[0]}] N·m")

    # 5. 创建控制器
    print("\n[5] 创建 MPC 控制器")
    controller = MPCController(
        plant=plant,
        config=config,
        weights=weights,
        constraints=constraints
    )

    # 设置工作点（向上平衡点）
    state_op = np.array([np.pi, 0.0])  # theta=pi, omega=0
    u_op = np.array([0.0])
    controller.set_operating_point(state_op, u_op)
    print("  工作点: theta=π, omega=0")

    # 6. 运行仿真 - 从小角度偏差开始
    print("\n[6] 运行仿真 - 从偏离平衡点开始")
    sim = MPCSimulation(plant, controller)

    # 初始状态：略微偏离向上平衡点
    x0 = np.array([np.pi + 0.2, 0.0])  # 偏离 0.2 弧度

    # 目标：保持在向上平衡点
    def reference(t):
        return np.array([np.pi])

    result = sim.run(x0, reference)

    print(f"  仿真时间: {result.time[-1]:.1f} s")
    print(f"  最终角度: {result.states[-1, 0]:.4f} rad")
    print(f"  最终角速度: {result.states[-1, 1]:.4f} rad/s")
    print(f"  角度误差: {abs(result.states[-1, 0] - np.pi):.4f} rad")

    # 7. 绘制结果
    print("\n[7] 绘制仿真结果")

    # 角度和角速度图
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # 角度
    ax1 = axes[0]
    ax1.plot(result.time, result.states[:, 0], 'b-', linewidth=1.5, label='角度')
    ax1.axhline(y=np.pi, color='r', linestyle='--', label='目标')
    ax1.set_ylabel('角度 (rad)')
    ax1.set_title('倒立摆 MPC 控制')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 角速度
    ax2 = axes[1]
    ax2.plot(result.time, result.states[:, 1], 'g-', linewidth=1.5)
    ax2.set_ylabel('角速度 (rad/s)')
    ax2.grid(True, alpha=0.3)

    # 控制输入
    ax3 = axes[2]
    ax3.step(result.time[:len(result.inputs)], result.inputs[:, 0],
             'r-', linewidth=1.5, where='post')
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('力矩 (N·m)')
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    # 相平面图
    fig2, ax = plt.subplots(figsize=(8, 8))
    ax.plot(result.states[:, 0], result.states[:, 1], 'b-', linewidth=1.5)
    ax.plot(result.states[0, 0], result.states[0, 1], 'go', markersize=10, label='起点')
    ax.plot(result.states[-1, 0], result.states[-1, 1], 'rs', markersize=10, label='终点')
    ax.axvline(x=np.pi, color='r', linestyle='--', alpha=0.5, label='平衡点')
    ax.set_xlabel('角度 (rad)')
    ax.set_ylabel('角速度 (rad/s)')
    ax.set_title('倒立摆相平面图')
    ax.legend()
    ax.grid(True, alpha=0.3)

    print("\n[8] 运行扰动抑制仿真")

    # 重置控制器
    controller.reset()

    # 从平衡点开始，施加扰动
    x0_dist = np.array([np.pi, 0.0])  # 平衡点

    # 参考：保持平衡
    def reference_balanced(t):
        return np.array([np.pi])

    # 添加扰动的仿真
    sim_config = SimulationConfig(
        total_time=5.0,
        sample_time=0.05,
        noise_std=0.01  # 添加过程噪声
    )
    sim_noisy = MPCSimulation(plant, controller, sim_config)

    result_noisy = sim_noisy.run(x0_dist, reference_balanced)

    fig3, ax = plt.subplots(figsize=(10, 4))
    ax.plot(result_noisy.time, result_noisy.states[:, 0], 'b-', linewidth=1.5)
    ax.axhline(y=np.pi, color='r', linestyle='--', label='目标')
    ax.set_xlabel('时间 (s)')
    ax.set_ylabel('角度 (rad)')
    ax.set_title('倒立摆扰动抑制')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.show()

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
