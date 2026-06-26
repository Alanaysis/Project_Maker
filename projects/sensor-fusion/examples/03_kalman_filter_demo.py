"""
示例 3: 卡尔曼滤波器演示

演示扩展卡尔曼滤波 (EKF) 在姿态估计中的应用。
对比仅用加速度计、仅用磁力计和两者融合的效果。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kalman_filter import AttitudeEKF, KalmanFilter
from src.complementary_filter import ComplementaryFilter
from src.coordinate_transform import euler_to_quaternion


def generate_simulated_data(n_samples=500, dt=0.01):
    """生成模拟的 IMU 数据"""
    t = np.arange(n_samples) * dt
    
    # 真实俯仰角 (缓慢振荡)
    true_pitch = 0.1 * np.sin(2 * np.pi * 0.05 * t)
    true_roll = 0.05 * np.cos(2 * np.pi * 0.03 * t)
    true_yaw = np.zeros(n_samples)  # 无偏航旋转，简化演示
    
    # 真实角速度
    true_gyro_x = -0.05 * 2 * np.pi * 0.03 * np.sin(2 * np.pi * 0.03 * t)
    true_gyro_y = 0.1 * 2 * np.pi * 0.05 * np.cos(2 * np.pi * 0.05 * t)
    true_gyro_z = np.zeros(n_samples)
    
    # 陀螺仪 (带偏置和噪声)
    gyro = np.column_stack([
        true_gyro_x + np.random.randn(n_samples) * 0.0087,
        true_gyro_y + np.random.randn(n_samples) * 0.0087,
        true_gyro_z + 0.02 + np.random.randn(n_samples) * 0.0087
    ])
    
    # 加速度计 (重力投影，考虑俯仰和横滚)
    cos_p = np.cos(true_pitch)
    sin_p = np.sin(true_pitch)
    cos_r = np.cos(true_roll)
    sin_r = np.sin(true_roll)
    
    ax = 9.81 * (-sin_p * cos_r)
    ay = 9.81 * (sin_r * cos_p)
    az = 9.81 * (cos_p * cos_r)
    
    accel = np.column_stack([
        ax + np.random.randn(n_samples) * 0.02,
        ay + np.random.randn(n_samples) * 0.02,
        az + np.random.randn(n_samples) * 0.02
    ])
    
    # 磁力计 (无偏航旋转，磁场基本不变)
    # 参考磁场: Hx=50, Hy=0, Hz=30 (与 EKF 内部参考一致)
    mag = np.column_stack([
        50 + np.random.randn(n_samples) * 0.5,
        np.random.randn(n_samples) * 0.5,
        30 + np.random.randn(n_samples) * 0.5
    ])
    
    return gyro, accel, mag, true_yaw, true_pitch, true_roll, dt


def main():
    print("=" * 60)
    print("示例 3: 卡尔曼滤波器演示")
    print("=" * 60)
    
    n_samples = 500
    dt = 0.01
    gyro, accel, mag, true_yaw, true_pitch, true_roll, dt = generate_simulated_data(n_samples, dt)
    
    print(f"\n模拟参数:")
    print(f"  采样率: {1/dt:.0f} Hz")
    print(f"  偏航角范围: 0 ~ {np.degrees(true_yaw[-1]):.1f} 度")
    
    # EKF (加速度计 + 磁力计)
    print(f"\n--- EKF (加速度计+磁力计融合) ---")
    ekf = AttitudeEKF(process_noise=1e-4, accel_noise=1e-2, mag_noise=1e-2)
    # 设置参考磁场方向 (与模拟数据一致)
    ekf.h0 = np.array([50.0, 0.0, 30.0])
    ekf.h0 = ekf.h0 / np.linalg.norm(ekf.h0)
    
    ekf_yaw = []
    ekf_pitch = []
    ekf_roll = []
    ekf_bias = []
    
    for i in range(n_samples):
        q = ekf.update(accel[i], mag[i], gyro[i])
        attitude = ekf.get_attitude()
        r, p, y = attitude['euler']
        ekf_yaw.append(y)
        ekf_pitch.append(p)
        ekf_roll.append(r)
        ekf_bias.append(ekf.x[4:7].copy())
    
    ekf_yaw = np.array(ekf_yaw)
    ekf_pitch = np.array(ekf_pitch)
    ekf_roll = np.array(ekf_roll)
    ekf_bias = np.array(ekf_bias)
    
    yaw_rmse = np.sqrt(np.mean((ekf_yaw - true_yaw)**2))
    print(f"偏航角 RMSE: {np.degrees(yaw_rmse):.4f} 度")
    print(f"最终陀螺仪偏置估计: {np.degrees(ekf_bias[-1]).tolist()} 度")
    
    # 互补滤波器对比
    print(f"\n--- 互补滤波器对比 ---")
    comp = ComplementaryFilter(gain=0.98)
    comp_yaw = []
    
    for i in range(n_samples):
        q = comp.update(accel[i], gyro[i], dt)
        r, p, y = comp.get_euler_angles()
        comp_yaw.append(y)
    
    comp_yaw = np.array(comp_yaw)
    comp_rmse = np.sqrt(np.mean((comp_yaw - true_yaw)**2))
    print(f"互补滤波器偏航角 RMSE: {np.degrees(comp_rmse):.4f} 度")
    
    # 仅用加速度计
    print(f"\n--- 仅用加速度计的局限性 ---")
    accel_only_pitch = []
    for i in range(n_samples):
        ax, ay, az = accel[i]
        p = np.arctan2(ay, np.sqrt(ax**2 + az**2))
        accel_only_pitch.append(p)
    accel_only_pitch = np.array(accel_only_pitch)
    accel_rmse = np.sqrt(np.mean((accel_only_pitch - true_pitch)**2))
    print(f"仅加速度计俯仰角 RMSE: {np.degrees(accel_rmse):.4f} 度")
    print(f"  (加速度计易受振动干扰)")
    
    # 展示结果
    print(f"\n--- 姿态估计结果 (部分时间步) ---")
    print(f"{'时间(s)':>8} | {'真实 yaw':>10} | {'EKF yaw':>10} | {'互补 yaw':>10}")
    print("-" * 50)
    
    step = max(1, n_samples // 15)
    for i in range(0, n_samples, step):
        t_sec = i * dt
        print(f"{t_sec:>8.2f} | {np.degrees(true_yaw[i]):>10.2f} | "
              f"{np.degrees(ekf_yaw[i]):>10.2f} | {np.degrees(comp_yaw[i]):>10.2f}")
    
    print(f"\n关键观察:")
    print(f"  - EKF 能有效估计并补偿陀螺仪偏置")
    print(f"  - EKF 比互补滤波更精确 (自适应权重)")
    print(f"  - 仅用加速度计无法估计偏航角")
    print(f"\n完成!")


if __name__ == '__main__':
    main()
