"""
倒立摆控制示例

演示倒立摆系统的建模、分析和控制
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications import InvertedPendulum
from src.controller import LQRController
from src.observer import FullOrderObserver


def main():
    print("=" * 60)
    print("倒立摆控制示例")
    print("=" * 60)

    # 1. 创建倒立摆系统
    ip = InvertedPendulum(M=0.5, m=0.2, l=0.3, b=0.1, I=0.006)
    print(f"\n1. 倒立摆参数:")
    params = ip.get_parameters()
    for k, v in params.items():
        print(f"   {k} = {v}")

    # 2. 连续时间模型分析
    print(f"\n2. 连续时间模型:")
    print(f"   A_c:\n{ip.A_c}")
    print(f"   特征值: {np.linalg.eigvals(ip.A_c)}")
    print(f"   连续系统稳定: {ip.continuous_model.is_stable()}")

    # 3. 离散化
    dt = 0.01
    model = ip.discretize(dt)
    print(f"\n3. 离散化模型 (dt={dt}):")
    print(f"   离散特征值: {model.get_eigenvalues()}")
    print(f"   离散系统稳定: {model.is_stable()}")

    # 4. 可控性和可观性
    print(f"\n4. 系统分析:")
    print(f"   可控: {ip.check_controllability(dt)}")
    print(f"   可观: {ip.check_observability(dt)}")

    # 5. LQR控制器设计
    Q = np.diag([100, 1, 200, 1])  # 角度权重最大
    R = np.array([[1.0]])
    lqr = ip.design_lqr(dt=dt, Q=Q, R=R)
    print(f"\n5. LQR控制器:")
    print(f"   增益 K: {lqr.K}")
    A_cl, _ = lqr.get_closed_loop_system()
    print(f"   闭环极点: {np.linalg.eigvals(A_cl)}")

    # 6. 开环 vs 闭环仿真
    print(f"\n6. 仿真比较:")
    x0 = np.array([0.0, 0.0, 0.1, 0.0])  # 初始偏角0.1弧度
    n_steps = 300

    # 开环仿真
    states_open, _ = model.simulate(x0, np.zeros((n_steps, 1)))

    # 闭环仿真（LQR）
    states_lqr, controls_lqr = lqr.simulate(x0, n_steps)

    print(f"   开环最终角度: {np.degrees(states_open[-1, 2]):.2f} deg")
    print(f"   LQR最终角度: {np.degrees(states_lqr[-1, 2]):.4f} deg")

    # 7. 观测器设计
    obs_desired_poles = np.array([0.5, 0.5, 0.5, 0.5])
    observer, _ = ip.design_observer(dt=dt, desired_poles=obs_desired_poles)
    print(f"\n7. 观测器:")
    print(f"   观测器增益 L:\n{observer.L}")
    print(f"   观测器极点: {observer.get_observer_poles()}")

    # 8. 基于观测器的控制仿真
    x_true = x0.copy()
    observer.x_hat = np.zeros(4)
    states_true_list = [x_true.copy()]
    states_est_list = [observer.x_hat.copy()]

    for _ in range(n_steps):
        y = model.C @ x_true
        x_hat = observer.update(y)
        u = lqr.compute_control(x_hat)
        x_true = model.A @ x_true + model.B @ u
        states_true_list.append(x_true.copy())
        states_est_list.append(x_hat.copy())

    states_true = np.array(states_true_list)
    states_est = np.array(states_est_list)

    print(f"\n8. 基于观测器的控制:")
    print(f"   最终真实角度: {np.degrees(states_true[-1, 2]):.4f} deg")
    print(f"   最终估计误差: {np.linalg.norm(states_true[-1] - states_est[-1]):.6f}")

    # 9. 可视化
    t = np.arange(n_steps + 1) * dt
    t_ctrl = np.arange(n_steps) * dt

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 角度响应
    axes[0, 0].plot(t, np.degrees(states_open[:, 2]), "k--", label="开环", linewidth=2)
    axes[0, 0].plot(t, np.degrees(states_lqr[:, 2]), "b-", label="LQR", linewidth=2)
    axes[0, 0].plot(t, np.degrees(states_true[:, 2]), "r-.", label="观测器+LQR", linewidth=2)
    axes[0, 0].set_xlabel("时间 (s)")
    axes[0, 0].set_ylabel("角度 (度)")
    axes[0, 0].set_title("摆杆角度响应")
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    # 位置响应
    axes[0, 1].plot(t, states_lqr[:, 0], "b-", label="LQR", linewidth=2)
    axes[0, 1].plot(t, states_true[:, 0], "r-.", label="观测器+LQR", linewidth=2)
    axes[0, 1].set_xlabel("时间 (s)")
    axes[0, 1].set_ylabel("位置 (m)")
    axes[0, 1].set_title("小车位置响应")
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # 控制输入
    axes[1, 0].plot(t_ctrl, controls_lqr[:, 0], "b-", label="LQR", linewidth=2)
    axes[1, 0].set_xlabel("时间 (s)")
    axes[1, 0].set_ylabel("力 (N)")
    axes[1, 0].set_title("控制输入")
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # 观测误差
    obs_error = states_true - states_est
    axes[1, 1].plot(t, np.degrees(obs_error[:, 2]), "g-", label="角度估计误差", linewidth=2)
    axes[1, 1].plot(t, obs_error[:, 0], "m-", label="位置估计误差", linewidth=2)
    axes[1, 1].set_xlabel("时间 (s)")
    axes[1, 1].set_ylabel("误差")
    axes[1, 1].set_title("观测器估计误差")
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "inverted_pendulum.png"), dpi=150)
    plt.close()

    print("\n9. 图表已保存到 examples/inverted_pendulum.png")
    print("\n示例完成!")


if __name__ == "__main__":
    main()
