"""
状态反馈控制和LQR控制示例

演示极点配置、LQR控制和观测器设计
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.state_space_model import StateSpaceModel
from src.controller import StateFeedbackController, LQRController
from src.observer import FullOrderObserver


def main():
    print("=" * 60)
    print("状态反馈控制和LQR控制示例")
    print("=" * 60)

    # 1. 系统定义
    # 倒立摆线性化模型（离散化）
    dt = 0.01
    g = 9.81
    l = 1.0
    m = 1.0

    # 连续时间模型
    A_c = np.array([[0, 1],
                    [g/l, 0]])
    B_c = np.array([[0],
                    [1/(m*l**2)]])
    C = np.array([[1, 0]])

    # 简单离散化（前向欧拉）
    A = np.eye(2) + A_c * dt
    B = B_c * dt

    print("\n1. 系统模型（倒立摆）:")
    print(f"状态转移矩阵 A:\n{A}")
    print(f"输入矩阵 B:\n{B}")

    # 2. 极点配置控制
    print("\n2. 极点配置控制:")
    controller_pp = StateFeedbackController(A, B)
    desired_poles = np.array([0.9, 0.8])  # 期望闭环极点
    K_pp = controller_pp.place_poles(desired_poles)
    print(f"反馈增益 K: {K_pp}")
    print(f"闭环极点: {controller_pp.get_closed_loop_poles()}")

    # 3. LQR控制
    print("\n3. LQR控制:")
    Q = np.array([[100, 0],    # 位置权重
                  [0, 1]])     # 速度权重
    R = np.array([[0.01]])     # 控制权重

    lqr = LQRController(A, B, Q, R)
    print(f"LQR增益 K: {lqr.K}")
    print(f"Riccati方程解 P:\n{lqr.P}")

    # 4. 仿真比较
    print("\n4. 仿真比较:")
    x0 = np.array([0.1, 0.0])  # 初始偏角0.1弧度
    n_steps = 200

    # 极点配置仿真
    states_pp, controls_pp = controller_pp.simulate(x0, n_steps, r=np.zeros(1))

    # LQR仿真
    states_lqr, controls_lqr = lqr.simulate(x0, n_steps)

    # 开环仿真
    model = StateSpaceModel(A, B, C)
    states_open, _ = model.simulate(x0, np.zeros((n_steps, 1)))

    print(f"开环最终位置: {states_open[-1, 0]:.4f}")
    print(f"极点配置最终位置: {states_pp[-1, 0]:.6f}")
    print(f"LQR最终位置: {states_lqr[-1, 0]:.6f}")

    # 5. 计算LQR成本
    cost_pp = np.sum(states_pp[:-1]**2 @ Q + controls_pp**2 @ R)
    cost_lqr = lqr.get_cost(x0, n_steps)
    print(f"\n5. 控制成本:")
    print(f"极点配置成本: {cost_pp:.4f}")
    print(f"LQR成本: {cost_lqr:.4f}")

    # 6. 可视化
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    t = np.arange(n_steps + 1) * dt

    # 状态响应
    axes[0, 0].plot(t, np.degrees(states_open[:, 0]), "k--", label="开环", linewidth=2)
    axes[0, 0].plot(t[:len(states_pp)], np.degrees(states_pp[:, 0]), "b-", label="极点配置", linewidth=2)
    axes[0, 0].plot(t[:len(states_lqr)], np.degrees(states_lqr[:, 0]), "r-", label="LQR", linewidth=2)
    axes[0, 0].set_xlabel("时间 (s)")
    axes[0, 0].set_ylabel("角度 (度)")
    axes[0, 0].set_title("状态响应（角度）")
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    # 速度响应
    axes[0, 1].plot(t[:len(states_pp)], states_pp[:, 1], "b-", label="极点配置", linewidth=2)
    axes[0, 1].plot(t[:len(states_lqr)], states_lqr[:, 1], "r-", label="LQR", linewidth=2)
    axes[0, 1].set_xlabel("时间 (s)")
    axes[0, 1].set_ylabel("角速度 (rad/s)")
    axes[0, 1].set_title("状态响应（角速度）")
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # 控制输入
    t_ctrl = np.arange(n_steps) * dt
    axes[1, 0].plot(t_ctrl, controls_pp[:, 0], "b-", label="极点配置", linewidth=2)
    axes[1, 0].plot(t_ctrl, controls_lqr[:, 0], "r-", label="LQR", linewidth=2)
    axes[1, 0].set_xlabel("时间 (s)")
    axes[1, 0].set_ylabel("控制力矩")
    axes[1, 0].set_title("控制输入")
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # 相平面
    axes[1, 1].plot(states_pp[:, 0], states_pp[:, 1], "b-", label="极点配置", linewidth=2)
    axes[1, 1].plot(states_lqr[:, 0], states_lqr[:, 1], "r-", label="LQR", linewidth=2)
    axes[1, 1].plot(states_pp[0, 0], states_pp[0, 1], "go", markersize=10, label="起点")
    axes[1, 1].plot(0, 0, "ks", markersize=10, label="平衡点")
    axes[1, 1].set_xlabel("角度 (rad)")
    axes[1, 1].set_ylabel("角速度 (rad/s)")
    axes[1, 1].set_title("相平面图")
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "control_response.png"), dpi=150)
    plt.close()

    print("\n6. 图表已保存到 examples/control_response.png")

    # 7. 观测器设计
    print("\n7. 观测器设计:")
    observer = FullOrderObserver(A, B, C)
    obs_poles = np.array([0.85, 0.8])  # 观测器极点应比控制器快
    L = observer.design_by_poles(obs_poles)
    print(f"观测器增益 L: {L}")
    print(f"观测器极点: {observer.get_observer_poles()}")

    # 基于观测器的控制仿真
    x_true = x0.copy()
    observer.x_hat = np.array([0.0, 0.0])  # 初始估计为零

    states_est = [observer.x_hat.copy()]
    states_true = [x_true.copy()]

    for k in range(n_steps):
        # 测量
        y = C @ x_true

        # 状态估计
        x_hat = observer.update(y)

        # 控制
        u = lqr.compute_control(x_hat)

        # 状态演化
        x_true = A @ x_true + B @ u

        states_est.append(x_hat.copy())
        states_true.append(x_true.copy())

    states_est = np.array(states_est)
    states_true = np.array(states_true)

    print(f"最终真实状态: {states_true[-1]}")
    print(f"最终估计状态: {states_est[-1]}")
    print(f"估计误差: {np.linalg.norm(states_true[-1] - states_est[-1]):.6f}")

    print("\n示例完成!")


if __name__ == "__main__":
    main()
