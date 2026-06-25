"""
卡尔曼滤波器示例

演示卡尔曼滤波器在状态估计中的应用
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.kalman_filter import KalmanFilter


def main():
    print("=" * 60)
    print("卡尔曼滤波器示例")
    print("=" * 60)

    # 1. 系统模型
    # 状态: [位置, 速度]
    # 匀速运动模型
    dt = 1.0
    A = np.array([[1, dt],
                  [0, 1]])
    B = np.array([[0.5 * dt**2],
                  [dt]])
    C = np.array([[1, 0]])  # 只测量位置

    # 噪声参数
    sigma_a = 0.1  # 过程噪声标准差
    sigma_z = 0.5  # 测量噪声标准差

    Q = sigma_a**2 * np.array([[dt**4/4, dt**3/2],
                                [dt**3/2, dt**2]])
    R = np.array([[sigma_z**2]])

    print("\n1. 系统模型:")
    print(f"状态转移矩阵 A:\n{A}")
    print(f"过程噪声协方差 Q:\n{Q}")
    print(f"测量噪声协方差 R:\n{R}")

    # 2. 生成真实轨迹
    n_steps = 50
    true_states = np.zeros((n_steps, 2))
    true_states[0] = [0.0, 1.0]  # 初始位置0，速度1

    for k in range(1, n_steps):
        # 真实状态演化（带过程噪声）
        w = np.random.multivariate_normal([0, 0], Q)
        true_states[k] = A @ true_states[k-1] + w

    # 生成带噪声的测量
    measurements = true_states[:, 0] + np.random.randn(n_steps) * sigma_z

    print(f"\n2. 生成了{n_steps}个时间步的轨迹")
    print(f"真实位置范围: [{true_states[:, 0].min():.2f}, {true_states[:, 0].max():.2f}]")
    print(f"真实速度范围: [{true_states[:, 1].min():.2f}, {true_states[:, 1].max():.2f}]")

    # 3. 运行卡尔曼滤波器
    kf = KalmanFilter(A, B, C, Q, R,
                      x0=np.array([0.0, 0.0]),
                      P0=np.eye(2) * 10)

    estimated_states = np.zeros((n_steps, 2))
    estimated_covariances = np.zeros((n_steps, 2, 2))

    for k in range(n_steps):
        # 预测
        kf.predict()

        # 更新
        x_hat, P, K = kf.update(measurements[k])

        estimated_states[k] = x_hat
        estimated_covariances[k] = P

    print("\n3. 卡尔曼滤波完成")
    print(f"最终估计位置: {estimated_states[-1, 0]:.4f}")
    print(f"最终估计速度: {estimated_states[-1, 1]:.4f}")
    print(f"真实位置: {true_states[-1, 0]:.4f}")
    print(f"真实速度: {true_states[-1, 1]:.4f}")

    # 4. 计算误差
    position_error = np.sqrt(np.mean((true_states[:, 0] - estimated_states[:, 0])**2))
    velocity_error = np.sqrt(np.mean((true_states[:, 1] - estimated_states[:, 1])**2))
    measurement_error = np.sqrt(np.mean((true_states[:, 0] - measurements)**2))

    print(f"\n4. 误差分析:")
    print(f"位置估计RMSE: {position_error:.4f}")
    print(f"速度估计RMSE: {velocity_error:.4f}")
    print(f"测量RMSE: {measurement_error:.4f}")
    print(f"滤波器改善: {(1 - position_error/measurement_error)*100:.1f}%")

    # 5. 可视化
    fig, axes = plt.subplots(3, 1, figsize=(10, 12))

    # 位置估计
    t = np.arange(n_steps) * dt
    axes[0].plot(t, true_states[:, 0], "b-", label="真实位置", linewidth=2)
    axes[0].plot(t, measurements, "gx", label="测量值", markersize=6, alpha=0.6)
    axes[0].plot(t, estimated_states[:, 0], "r--", label="估计位置", linewidth=2)
    axes[0].fill_between(
        t,
        estimated_states[:, 0] - 2 * np.sqrt(estimated_covariances[:, 0, 0]),
        estimated_states[:, 0] + 2 * np.sqrt(estimated_covariances[:, 0, 0]),
        alpha=0.2,
        color="red",
        label="2σ置信区间",
    )
    axes[0].set_xlabel("时间 (s)")
    axes[0].set_ylabel("位置")
    axes[0].set_title("位置估计")
    axes[0].legend()
    axes[0].grid(True)

    # 速度估计
    axes[1].plot(t, true_states[:, 1], "b-", label="真实速度", linewidth=2)
    axes[1].plot(t, estimated_states[:, 1], "r--", label="估计速度", linewidth=2)
    axes[1].fill_between(
        t,
        estimated_states[:, 1] - 2 * np.sqrt(estimated_covariances[:, 1, 1]),
        estimated_states[:, 1] + 2 * np.sqrt(estimated_covariances[:, 1, 1]),
        alpha=0.2,
        color="red",
        label="2σ置信区间",
    )
    axes[1].set_xlabel("时间 (s)")
    axes[1].set_ylabel("速度")
    axes[1].set_title("速度估计")
    axes[1].legend()
    axes[1].grid(True)

    # 估计误差
    position_errors = true_states[:, 0] - estimated_states[:, 0]
    axes[2].plot(t, position_errors, "b-", label="位置估计误差", linewidth=2)
    axes[2].axhline(y=0, color="k", linestyle="--", alpha=0.3)
    axes[2].fill_between(
        t,
        -2 * np.sqrt(estimated_covariances[:, 0, 0]),
        2 * np.sqrt(estimated_covariances[:, 0, 0]),
        alpha=0.2,
        color="red",
        label="2σ边界",
    )
    axes[2].set_xlabel("时间 (s)")
    axes[2].set_ylabel("误差")
    axes[2].set_title("估计误差")
    axes[2].legend()
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "kalman_filter.png"), dpi=150)
    plt.close()

    print("\n5. 图表已保存到 examples/kalman_filter.png")

    # 6. RTS平滑示例
    print("\n6. RTS平滑示例:")
    kf_smooth = KalmanFilter(A, B, C, Q, R,
                             x0=np.array([0.0, 0.0]),
                             P0=np.eye(2) * 10)

    smoothed_states = kf_smooth.smooth(measurements)

    smooth_position_error = np.sqrt(np.mean((true_states[:, 0] - smoothed_states[:, 0])**2))
    print(f"平滑后位置RMSE: {smooth_position_error:.4f}")
    print(f"相比滤波改善: {(1 - smooth_position_error/position_error)*100:.1f}%")

    print("\n示例完成!")


if __name__ == "__main__":
    main()
