"""
卡尔曼滤波演示

演示卡尔曼滤波在目标跟踪中的应用:
1. 创建模拟目标轨迹
2. 添加观测噪声
3. 使用卡尔曼滤波估计真实位置
4. 可视化结果
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kalman_filter import KalmanFilter, AdaptiveKalmanFilter


def generate_trajectory(
    n_points: int = 100,
    motion_type: str = "linear"
) -> np.ndarray:
    """生成目标轨迹

    Args:
        n_points: 轨迹点数
        motion_type: 运动类型 ("linear", "circular", "accelerating")

    Returns:
        轨迹数组 (n_points, 2)
    """
    if motion_type == "linear":
        # 匀速运动
        t = np.arange(n_points)
        x = 100 + 3 * t
        y = 200 + 2 * t
    elif motion_type == "circular":
        # 圆周运动
        t = np.arange(n_points) * 2 * np.pi / n_points
        x = 300 + 100 * np.cos(t)
        y = 300 + 100 * np.sin(t)
    elif motion_type == "accelerating":
        # 加速运动
        t = np.arange(n_points)
        x = 100 + 0.5 * t + 0.02 * t**2
        y = 200 + 0.3 * t + 0.015 * t**2
    else:
        raise ValueError(f"未知运动类型: {motion_type}")

    return np.column_stack([x, y])


def add_noise(
    trajectory: np.ndarray,
    noise_std: float = 5.0
) -> np.ndarray:
    """添加观测噪声

    Args:
        trajectory: 真实轨迹
        noise_std: 噪声标准差

    Returns:
        带噪声的观测
    """
    noise = np.random.randn(*trajectory.shape) * noise_std
    return trajectory + noise


def run_kalman_filter(
    measurements: np.ndarray,
    dt: float = 1.0,
    process_noise: float = 1e-3,
    measurement_noise: float = 1.0
) -> tuple:
    """运行卡尔曼滤波

    Args:
        measurements: 观测序列
        dt: 时间步长
        process_noise: 过程噪声
        measurement_noise: 测量噪声

    Returns:
        (滤波轨迹, 预测轨迹)
    """
    kf = KalmanFilter(
        dt=dt,
        process_noise=process_noise,
        measurement_noise=measurement_noise
    )

    # 初始化
    kf.set_state(measurements[0, 0], measurements[0, 1])

    filtered = []
    predicted = []

    for i in range(len(measurements)):
        # 预测
        pred = kf.predict()
        predicted.append(pred[:2].copy())

        # 更新
        meas = measurements[i]
        state = kf.update(meas)
        filtered.append(state[:2].copy())

    return np.array(filtered), np.array(predicted)


def run_adaptive_kalman_filter(
    measurements: np.ndarray,
    dt: float = 1.0
) -> np.ndarray:
    """运行自适应卡尔曼滤波

    Args:
        measurements: 观测序列
        dt: 时间步长

    Returns:
        滤波轨迹
    """
    akf = AdaptiveKalmanFilter(
        dt=dt,
        process_noise=1e-3,
        measurement_noise=1.0,
        window_size=10,
        adaptation_rate=0.1
    )

    # 初始化
    akf.set_state(measurements[0, 0], measurements[0, 1])

    filtered = []
    for i in range(len(measurements)):
        akf.predict()
        state = akf.update(measurements[i])
        filtered.append(state[:2].copy())

    return np.array(filtered)


def calculate_errors(
    true_trajectory: np.ndarray,
    estimated_trajectory: np.ndarray
) -> np.ndarray:
    """计算误差

    Args:
        true_trajectory: 真实轨迹
        estimated_trajectory: 估计轨迹

    Returns:
        误差序列
    """
    errors = np.sqrt(np.sum((true_trajectory - estimated_trajectory)**2, axis=1))
    return errors


def plot_results(
    true_trajectory: np.ndarray,
    measurements: np.ndarray,
    filtered: np.ndarray,
    predicted: np.ndarray,
    title: str = "卡尔曼滤波跟踪结果"
):
    """绘制结果

    Args:
        true_trajectory: 真实轨迹
        measurements: 观测
        filtered: 滤波结果
        predicted: 预测结果
        title: 图表标题
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(title, fontsize=16)

    # 轨迹图
    ax1 = axes[0, 0]
    ax1.plot(true_trajectory[:, 0], true_trajectory[:, 1],
             'g-', linewidth=2, label='真实轨迹')
    ax1.scatter(measurements[:, 0], measurements[:, 1],
                c='red', s=10, alpha=0.5, label='观测')
    ax1.plot(filtered[:, 0], filtered[:, 1],
             'b-', linewidth=2, label='滤波结果')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_title('轨迹对比')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # X轴时间序列
    ax2 = axes[0, 1]
    t = np.arange(len(true_trajectory))
    ax2.plot(t, true_trajectory[:, 0], 'g-', label='真实')
    ax2.scatter(t, measurements[:, 0], c='red', s=10, alpha=0.5, label='观测')
    ax2.plot(t, filtered[:, 0], 'b-', label='滤波')
    ax2.set_xlabel('时间步')
    ax2.set_ylabel('X')
    ax2.set_title('X轴跟踪')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Y轴时间序列
    ax3 = axes[1, 0]
    ax3.plot(t, true_trajectory[:, 1], 'g-', label='真实')
    ax3.scatter(t, measurements[:, 1], c='red', s=10, alpha=0.5, label='观测')
    ax3.plot(t, filtered[:, 1], 'b-', label='滤波')
    ax3.set_xlabel('时间步')
    ax3.set_ylabel('Y')
    ax3.set_title('Y轴跟踪')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 误差图
    ax4 = axes[1, 1]
    meas_errors = calculate_errors(true_trajectory, measurements)
    filt_errors = calculate_errors(true_trajectory, filtered)
    pred_errors = calculate_errors(true_trajectory, predicted)

    ax4.plot(t, meas_errors, 'r-', label=f'观测误差 (均值:{np.mean(meas_errors):.2f})')
    ax4.plot(t, filt_errors, 'b-', label=f'滤波误差 (均值:{np.mean(filt_errors):.2f})')
    ax4.plot(t, pred_errors, 'g--', label=f'预测误差 (均值:{np.mean(pred_errors):.2f})')
    ax4.set_xlabel('时间步')
    ax4.set_ylabel('误差 (像素)')
    ax4.set_title('跟踪误差')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('kalman_filter_demo.png', dpi=150, bbox_inches='tight')
    plt.show()

    print(f"\n误差统计:")
    print(f"  观测误差均值: {np.mean(meas_errors):.2f} 像素")
    print(f"  滤波误差均值: {np.mean(filt_errors):.2f} 像素")
    print(f"  预测误差均值: {np.mean(pred_errors):.2f} 像素")
    print(f"\n结果已保存: kalman_filter_demo.png")


def main():
    """主函数"""
    print("=" * 60)
    print("卡尔曼滤波目标跟踪演示")
    print("=" * 60)

    # 设置随机种子
    np.random.seed(42)

    # 1. 生成轨迹
    print("\n1. 生成目标轨迹...")
    motion_types = ["linear", "circular", "accelerating"]

    for motion_type in motion_types:
        print(f"\n--- {motion_type} 运动 ---")

        # 生成真实轨迹
        true_trajectory = generate_trajectory(100, motion_type)

        # 添加噪声
        measurements = add_noise(true_trajectory, noise_std=8.0)

        # 运行卡尔曼滤波
        filtered, predicted = run_kalman_filter(
            measurements,
            dt=1.0,
            process_noise=1e-2,
            measurement_noise=1.0
        )

        # 计算误差
        meas_errors = calculate_errors(true_trajectory, measurements)
        filt_errors = calculate_errors(true_trajectory, filtered)

        print(f"  观测噪声标准差: 8.0 像素")
        print(f"  观测误差均值: {np.mean(meas_errors):.2f} 像素")
        print(f"  滤波误差均值: {np.mean(filt_errors):.2f} 像素")
        print(f"  误差降低: {(1 - np.mean(filt_errors)/np.mean(meas_errors))*100:.1f}%")

    # 2. 详细演示
    print("\n2. 详细演示 (线性运动)...")
    true_trajectory = generate_trajectory(100, "linear")
    measurements = add_noise(true_trajectory, noise_std=10.0)
    filtered, predicted = run_kalman_filter(measurements)

    plot_results(
        true_trajectory,
        measurements,
        filtered,
        predicted,
        "卡尔曼滤波跟踪演示 (线性运动)"
    )

    # 3. 自适应卡尔曼滤波
    print("\n3. 自适应卡尔曼滤波演示...")
    true_trajectory = generate_trajectory(100, "accelerating")

    # 添加变化的噪声
    noise_std = np.concatenate([
        np.ones(30) * 3.0,
        np.ones(40) * 15.0,
        np.ones(30) * 5.0
    ])
    measurements = true_trajectory + np.random.randn(*true_trajectory.shape) * noise_std[:, np.newaxis]

    # 标准卡尔曼
    filtered_std, _ = run_kalman_filter(measurements, measurement_noise=1.0)

    # 自适应卡尔曼
    filtered_adaptive = run_adaptive_kalman_filter(measurements)

    # 比较误差
    errors_std = calculate_errors(true_trajectory, filtered_std)
    errors_adaptive = calculate_errors(true_trajectory, filtered_adaptive)

    print(f"  标准卡尔曼误差均值: {np.mean(errors_std):.2f} 像素")
    print(f"  自适应卡尔曼误差均值: {np.mean(errors_adaptive):.2f} 像素")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
