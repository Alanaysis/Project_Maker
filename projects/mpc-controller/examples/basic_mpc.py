"""
基本 MPC 控制示例

演示如何使用 MPC 控制器控制双积分器系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.plant_model import DoubleIntegrator
from src.mpc_controller import MPCController, MPCConfig
from src.optimizer import MPCConstraints, MPCWeights
from src.simulation import MPCSimulation, SimulationConfig, MPCVisualizer


def main():
    """主函数：演示基本 MPC 控制"""

    print("=" * 60)
    print("MPC 控制器 - 基本示例")
    print("=" * 60)

    # 1. 创建被控对象模型
    print("\n[1] 创建被控对象模型")
    plant = DoubleIntegrator(dt=0.1)
    print(f"  系统: 双积分器")
    print(f"  状态维度: {plant.n_states}")
    print(f"  输入维度: {plant.n_inputs}")
    print(f"  采样时间: {plant.dt} s")

    # 2. 配置 MPC 参数
    print("\n[2] 配置 MPC 参数")
    config = MPCConfig(
        prediction_horizon=15,      # 预测时域
        control_horizon=8,          # 控制时域
        sample_time=0.1             # 采样时间
    )
    print(f"  预测时域: {config.prediction_horizon}")
    print(f"  控制时域: {config.control_horizon}")

    # 3. 设置权重
    print("\n[3] 设置权重矩阵")
    weights = MPCWeights(
        Q=np.diag([10.0, 1.0]),     # 状态权重：位置权重高
        R=np.array([[0.1]]),         # 输入权重
        Rd=np.array([[0.01]])        # 输入变化率权重
    )
    print(f"  状态权重 Q: diag([10.0, 1.0])")
    print(f"  输入权重 R: [[0.1]]")
    print(f"  变化率权重 Rd: [[0.01]]")

    # 4. 设置约束
    print("\n[4] 设置约束")
    constraints = MPCConstraints(
        u_min=np.array([-2.0]),      # 输入下界
        u_max=np.array([2.0]),       # 输入上界
    )
    print(f"  输入范围: [{constraints.u_min[0]}, {constraints.u_max[0]}]")

    # 5. 创建 MPC 控制器
    print("\n[5] 创建 MPC 控制器")
    controller = MPCController(
        plant=plant,
        config=config,
        weights=weights,
        constraints=constraints
    )
    print("  控制器创建成功")

    # 6. 运行阶跃响应仿真
    print("\n[6] 运行阶跃响应仿真")
    sim = MPCSimulation(plant, controller)

    x0 = np.array([0.0, 0.0])      # 初始状态：原点
    step_value = np.array([1.0, 0.0])  # 阶跃目标：位置=1

    result = sim.run_step_response(x0, step_value, step_time=0.5)

    print(f"  仿真时间: {result.time[-1]:.1f} s")
    print(f"  仿真步数: {result.info['n_steps']}")
    print(f"  最终位置: {result.states[-1, 0]:.3f}")
    print(f"  最终速度: {result.states[-1, 1]:.3f}")
    print(f"  平均代价: {np.mean(result.costs):.4f}")

    # 7. 绘制结果
    print("\n[7] 绘制仿真结果")

    # 状态和输出图
    fig1 = MPCVisualizer.plot_simulation_result(
        result,
        state_names=['位置', '速度'],
        input_names=['加速度'],
        output_names=['位置', '速度'],
        title="MPC 阶跃响应 - 双积分器系统"
    )

    # 跟踪误差图
    fig2 = MPCVisualizer.plot_tracking_error(
        result,
        output_names=['位置', '速度'],
        title="MPC 跟踪误差"
    )

    # 代价历史图
    fig3 = MPCVisualizer.plot_cost_history(result)

    # 相平面图
    fig4 = MPCVisualizer.plot_phase_portrait(result)

    print("\n[8] 运行正弦响应仿真")

    # 重置控制器
    controller.reset()

    # 正弦响应
    amplitude = np.array([1.0, 0.0])
    frequency = 0.2  # Hz

    result_sine = sim.run_sinusoidal_response(x0, amplitude, frequency)

    fig5 = MPCVisualizer.plot_simulation_result(
        result_sine,
        state_names=['位置', '速度'],
        input_names=['加速度'],
        output_names=['位置', '速度'],
        title="MPC 正弦响应 - 双积分器系统"
    )

    print(f"  正弦响应仿真完成")
    print(f"  跟踪误差 RMS: {np.sqrt(np.mean((result_sine.outputs[:, 0] - result_sine.references[:, 0])**2)):.4f}")

    # 显示图形
    plt.show()

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
