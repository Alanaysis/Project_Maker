"""
直流电机控制示例

演示直流电机的建模、分析和位置控制
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications import DCmotor
from src.controller import LQRController, StateFeedbackController
from src.kalman_filter import KalmanFilter


def main():
    print("=" * 60)
    print("直流电机控制示例")
    print("=" * 60)

    # 1. 创建直流电机系统
    motor = DCmotor(R=1.0, L=0.5, Ke=0.01, Kt=0.01, J=0.01, B=0.1)
    print(f"\n1. 电机参数:")
    params = motor.get_parameters()
    for k, v in params.items():
        print(f"   {k} = {v}")

    # 2. 连续时间模型分析
    print(f"\n2. 连续时间模型:")
    print(f"   A_c:\n{motor.A_c}")
    eigenvalues_c = np.linalg.eigvals(motor.A_c)
    print(f"   特征值: {eigenvalues_c}")
    print(f"   连续系统稳定: {motor.continuous_model.is_stable()}")

    # 3. 离散化
    dt = 0.001
    model = motor.discretize(dt)
    print(f"\n3. 离散化模型 (dt={dt}):")
    print(f"   离散特征值: {model.get_eigenvalues()}")
    print(f"   离散系统稳定: {model.is_stable()}")

    # 4. 可控性和可观性
    print(f"\n4. 系统分析:")
    print(f"   可控: {motor.check_controllability(dt)}")
    print(f"   可观: {motor.check_observability(dt)}")

    # 5. 开环阶跃响应
    print(f"\n5. 开环阶跃响应 (12V):")
    x0 = np.array([0.0, 0.0, 0.0])
    u_func = lambda t: np.array([12.0])
    t_open, states_open, outputs_open = motor.simulate_linear(
        x0, u_func, (0, 0.5), dt=dt
    )
    print(f"   最终角速度: {states_open[-1, 1]:.2f} rad/s")
    print(f"   最终电流: {states_open[-1, 2]:.4f} A")
    print(f"   稳态转速: {states_open[-1, 1] * 60 / (2 * np.pi):.1f} RPM")

    # 6. LQR位置控制
    print(f"\n6. LQR位置控制:")
    Q = np.diag([100, 1, 1])  # 角度权重最大
    R = np.array([[0.1]])
    lqr = motor.design_lqr(dt=dt, Q=Q, R=R)
    print(f"   LQR增益 K: {lqr.K}")
    A_cl, _ = lqr.get_closed_loop_system()
    print(f"   闭环极点: {np.linalg.eigvals(A_cl)}")

    # LQR控制仿真
    n_steps = 1000
    x0_ctrl = np.array([0.0, 0.0, 0.0])
    states_lqr, controls_lqr = lqr.simulate(x0_ctrl, n_steps)
    print(f"   最终角度: {states_lqr[-1, 0]:.4f} rad")
    print(f"   最终角速度: {states_lqr[-1, 1]:.4f} rad/s")

    # 7. 速度控制器设计
    print(f"\n7. 速度控制器:")
    speed_ctrl, speed_model = motor.design_speed_controller(dt=dt)
    print(f"   速度控制器增益 K: {speed_ctrl.K}")
    cl_poles = speed_ctrl.get_closed_loop_poles()
    print(f"   闭环极点: {cl_poles}")

    # 8. 卡尔曼滤波状态估计
    print(f"\n8. 卡尔曼滤波状态估计:")
    Qn = np.diag([1e-6, 1e-4, 1e-4])  # 过程噪声
    Rn = np.array([[1e-4]])  # 测量噪声（角度测量）
    kf = KalmanFilter(model.A, model.B, model.C, Qn, Rn,
                      x0=np.zeros(3), P0=np.eye(3) * 0.1)

    # 带噪声的仿真
    x_true = np.array([0.0, 0.0, 0.0])
    states_true_list = [x_true.copy()]
    states_est_list = [np.zeros(3)]

    for k in range(n_steps):
        # 测量（带噪声）
        y = model.C @ x_true + np.random.randn() * np.sqrt(Rn[0, 0])

        # 状态估计
        kf.predict()
        x_hat, _, _ = kf.update(y)

        # 控制
        u = lqr.compute_control(x_hat)

        # 状态演化
        x_true = model.A @ x_true + model.B @ u

        states_true_list.append(x_true.copy())
        states_est_list.append(x_hat.copy())

    states_true = np.array(states_true_list)
    states_est = np.array(states_est_list)

    est_error = np.sqrt(np.mean((states_true - states_est) ** 2))
    print(f"   状态估计RMSE: {est_error:.6f}")

    # 9. 可视化
    t_open_plot = t_open
    t_ctrl = np.arange(n_steps + 1) * dt

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 开环阶跃响应
    axes[0, 0].plot(t_open_plot, states_open[:, 1], "b-", linewidth=2)
    axes[0, 0].set_xlabel("时间 (s)")
    axes[0, 0].set_ylabel("角速度 (rad/s)")
    axes[0, 0].set_title("开环阶跃响应（角速度）")
    axes[0, 0].grid(True)

    # LQR位置控制
    axes[0, 1].plot(t_ctrl, states_lqr[:, 0], "b-", linewidth=2)
    axes[0, 1].axhline(y=0, color="k", linestyle="--", alpha=0.3)
    axes[0, 1].set_xlabel("时间 (s)")
    axes[0, 1].set_ylabel("角度 (rad)")
    axes[0, 1].set_title("LQR位置控制")
    axes[0, 1].grid(True)

    # 卡尔曼滤波估计
    axes[1, 0].plot(t_ctrl, np.degrees(states_true[:, 0]), "b-", label="真实角度", linewidth=2)
    axes[1, 0].plot(t_ctrl, np.degrees(states_est[:, 0]), "r--", label="估计角度", linewidth=2)
    axes[1, 0].set_xlabel("时间 (s)")
    axes[1, 0].set_ylabel("角度 (度)")
    axes[1, 0].set_title("卡尔曼滤波角度估计")
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # 控制输入
    t_ctrl_input = np.arange(n_steps) * dt
    axes[1, 1].plot(t_ctrl_input, controls_lqr[:, 0], "b-", linewidth=2)
    axes[1, 1].set_xlabel("时间 (s)")
    axes[1, 1].set_ylabel("电压 (V)")
    axes[1, 1].set_title("LQR控制输入")
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "motor_control.png"), dpi=150)
    plt.close()

    print("\n9. 图表已保存到 examples/motor_control.png")
    print("\n示例完成!")


if __name__ == "__main__":
    main()
