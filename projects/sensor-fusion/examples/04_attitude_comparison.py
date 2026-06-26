"""
示例 4: 姿态估计算法对比

对比互补滤波、卡尔曼滤波、Madgwick 和 Mahony 滤波器的性能。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.complementary_filter import ComplementaryFilter, AdaptiveComplementaryFilter
from src.kalman_filter import AttitudeEKF
from src.madgwick_filter import MadgwickFilter
from src.mahony_filter import MahonyFilter


def generate_test_data(n_samples=1000, dt=0.00390625):
    """
    生成更真实的测试数据
    
    模拟典型的 IMU 运动场景:
    - 缓慢的俯仰运动
    - 恒定的偏航旋转
    -  realistic 噪声水平
    """
    t = np.arange(n_samples) * dt
    
    # 真实姿态
    true_pitch = 0.2 * np.sin(2 * np.pi * 0.1 * t)
    true_roll = 0.1 * np.sin(2 * np.pi * 0.05 * t + np.pi/4)
    true_yaw = 0.3 * t
    
    # 计算真实角速度
    true_gyro_x = 0.1 * 2 * np.pi * 0.05 * np.cos(2 * np.pi * 0.05 * t + np.pi/4)
    true_gyro_y = 0.2 * 2 * np.pi * 0.1 * np.cos(2 * np.pi * 0.1 * t)
    true_gyro_z = 0.3
    
    # 陀螺仪 (MPU6050 级别噪声)
    gyro = np.column_stack([
        true_gyro_x + np.random.randn(n_samples) * 0.0087,  # ~0.5 deg/s noise
        true_gyro_y + np.random.randn(n_samples) * 0.0087,
        true_gyro_z + np.random.randn(n_samples) * 0.0087
    ])
    
    # 加速度计 (重力 + 线性加速度)
    cos_p = np.cos(true_pitch)
    sin_p = np.sin(true_pitch)
    cos_r = np.cos(true_roll)
    sin_r = np.sin(true_roll)
    cos_y = np.cos(true_yaw)
    sin_y = np.sin(true_yaw)
    
    # R_z(yaw) * R_y(pitch) * R_x(roll) * [0, 0, g]
    ax = 9.81 * (-sin_p * cos_r + cos_p * sin_r * sin_y)
    ay = 9.81 * (sin_r * cos_y + cos_r * sin_p * sin_y)
    az = 9.81 * (cos_p * cos_y)
    
    accel = np.column_stack([
        ax + np.random.randn(n_samples) * 0.02,
        ay + np.random.randn(n_samples) * 0.02,
        az + np.random.randn(n_samples) * 0.02
    ])
    
    # 磁力计
    Hx = 50
    Hy = 0
    Hz = 30
    
    # 旋转磁场
    mx = Hx * (cos_p * cos_y) + Hy * (sin_y) + Hz * (-sin_p * cos_y)
    my = Hx * (cos_p * sin_y) + Hy * (cos_y) + Hz * (-sin_p * sin_y)
    mz = Hx * (sin_p) + Hz * (cos_p)
    
    mag = np.column_stack([
        mx + np.random.randn(n_samples) * 0.5,
        my + np.random.randn(n_samples) * 0.5,
        mz + np.random.randn(n_samples) * 0.5
    ])
    
    return gyro, accel, mag, true_pitch, true_roll, true_yaw, dt


def run_algorithms(gyro, accel, mag, dt):
    """运行所有算法"""
    n_samples = len(gyro)
    
    results = {}
    
    # 互补滤波
    comp = ComplementaryFilter(gain=0.98)
    comp_euler = []
    for i in range(n_samples):
        q = comp.update(accel[i], gyro[i], dt)
        comp_euler.append(comp.get_euler_angles())
    results['complementary'] = np.array(comp_euler)
    
    # 自适应互补滤波
    adcomp = AdaptiveComplementaryFilter(base_gain=0.98)
    adcomp_euler = []
    for i in range(n_samples):
        q = adcomp.update(accel[i], gyro[i], dt)
        adcomp_euler.append(adcomp.get_euler_angles())
    results['adaptive_complementary'] = np.array(adcomp_euler)
    
    # EKF
    ekf = AttitudeEKF(process_noise=1e-4, accel_noise=1e-2, mag_noise=1e-2)
    ekf_euler = []
    for i in range(n_samples):
        q = ekf.update(accel[i], mag[i], gyro[i])
        ekf_euler.append(ekf.get_attitude()['euler'])
    results['ekf'] = np.array(ekf_euler)
    
    # Madgwick
    madgwick = MadgwickFilter(beta=0.1, sample_period=dt)
    madgwick_euler = []
    for i in range(n_samples):
        q = madgwick.update(gyro[i], accel[i], mag[i], dt)
        madgwick_euler.append(madgwick.get_euler_angles())
    results['madgwick'] = np.array(madgwick_euler)
    
    # Mahony
    mahony = MahonyFilter(Kp=2.0, Ki=0.1, sample_period=dt)
    mahony_euler = []
    for i in range(n_samples):
        q = mahony.update(gyro[i], accel[i], mag[i], dt)
        mahony_euler.append(mahony.get_euler_angles())
    results['mahony'] = np.array(mahony_euler)
    
    return results


def main():
    print("=" * 60)
    print("示例 4: 姿态估计算法对比")
    print("=" * 60)
    
    n_samples = 1000
    dt = 0.00390625  # 256 Hz
    gyro, accel, mag, true_pitch, true_roll, true_yaw, dt = generate_test_data(n_samples, dt)
    
    print(f"\n测试参数:")
    print(f"  采样率: {1/dt:.0f} Hz")
    print(f"  持续时间: {n_samples * dt:.1f} 秒")
    print(f"  俯仰角范围: [{np.degrees(true_pitch).min():.1f}, "
          f"{np.degrees(true_pitch).max():.1f}] 度")
    print(f"  偏航角范围: [{np.degrees(true_yaw).min():.1f}, "
          f"{np.degrees(true_yaw).max():.1f}] 度")
    
    # 运行所有算法
    print(f"\n运行所有算法...")
    results = run_algorithms(gyro, accel, mag, dt)
    
    # 计算误差
    print(f"\n--- 算法性能对比 ---")
    print(f"算法                  | 俯仰角 RMSE | 横滚角 RMSE | 偏航角 RMSE")
    print("-" * 60)
    
    algorithms = ['complementary', 'adaptive_complementary', 'ekf', 'madgwick', 'mahony']
    names = ['互补滤波', '自适应互补', 'EKF', 'Madgwick', 'Mahony']
    
    for name, alg_name in zip(names, algorithms):
        euler = results[alg_name]
        pitch_rmse = np.sqrt(np.mean((euler[:, 1] - true_pitch)**2))
        roll_rmse = np.sqrt(np.mean((euler[:, 0] - true_roll)**2))
        yaw_rmse = np.sqrt(np.mean((euler[:, 2] - true_yaw)**2))
        print(f"{name:20s} | {np.degrees(pitch_rmse):>10.4f} | "
              f"{np.degrees(roll_rmse):>10.4f} | {np.degrees(yaw_rmse):>10.4f}")
    
    # 总结
    print(f"\n--- 总结 ---")
    print(f"各算法特点:")
    print(f"  互补滤波:     简单快速，适合资源受限的嵌入式系统")
    print(f"  自适应互补:   根据振动自动调整，更鲁棒")
    print(f"  EKF:          最优估计，但计算量较大")
    print(f"  Madgwick:     计算效率高，只需调一个参数")
    print(f"  Mahony:       PI 反馈，对磁力计鲁棒")
    print(f"\n完成!")


if __name__ == '__main__':
    main()
