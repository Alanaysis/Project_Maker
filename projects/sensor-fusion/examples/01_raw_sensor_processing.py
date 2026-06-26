"""
示例 1: 原始传感器数据处理

演示如何使用数据预处理模块处理原始传感器数据。
包括异常值检测、低通滤波和移动平均。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_preprocessing import (
    SensorDataProcessor, MovingAverageFilter,
    LowPassFilter, OutlierDetector
)


def generate_simulated_sensor_data(n_samples=1000, dt=0.01):
    """
    生成模拟的 IMU 传感器数据
    
    模拟一个做简单运动的 IMU:
    - 陀螺仪: 恒定旋转 + 噪声
    - 加速度计: 重力 + 线性运动 + 噪声
    - 磁力计: 地磁场 + 旋转效应 + 噪声
    
    Args:
        n_samples: 采样点数
        dt: 时间步长 (秒)
    
    Returns:
        (accel, gyro, mag) 模拟数据
    """
    t = np.arange(n_samples) * dt
    
    # 陀螺仪: 绕 Z 轴匀速旋转 + 噪声
    gyro_z = 0.5 * np.ones(n_samples)  # 0.5 rad/s
    gyro_x = 0.1 * np.sin(2 * np.pi * 0.1 * t)
    gyro_y = 0.05 * np.cos(2 * np.pi * 0.05 * t)
    gyro = np.column_stack([gyro_x, gyro_y, gyro_z])
    gyro += np.random.randn(n_samples, 3) * 0.01  # 高斯噪声
    
    # 加速度计: 重力 + 振动
    accel = np.column_stack([
        np.zeros(n_samples),
        np.zeros(n_samples),
        np.ones(n_samples) * 9.81
    ])
    # 添加振动
    accel[:, 0] += 0.5 * np.sin(2 * np.pi * 1.0 * t)
    accel[:, 1] += 0.3 * np.sin(2 * np.pi * 2.0 * t)
    accel += np.random.randn(n_samples, 3) * 0.1  # 高斯噪声
    
    # 添加几个异常值
    for _ in range(5):
        idx = np.random.randint(0, n_samples)
        accel[idx] += np.random.randn(3) * 10
    
    # 磁力计: 随姿态变化的地磁场
    pitch = 0.1 * np.sin(2 * np.pi * 0.05 * t)
    yaw = 0.5 * t  # 匀速旋转
    mx = 50 * np.cos(yaw) + 30 * np.sin(pitch)
    my = 50 * np.sin(yaw)
    mz = 30 * np.cos(pitch)
    mag = np.column_stack([mx, my, mz])
    mag += np.random.randn(n_samples, 3) * 2  # 高斯噪声
    
    return accel, gyro, mag


def main():
    print("=" * 60)
    print("示例 1: 原始传感器数据处理")
    print("=" * 60)
    
    # 生成模拟数据
    n_samples = 500
    dt = 0.01
    print(f"\n生成 {n_samples} 个采样点 (dt={dt}s)...")
    
    np.random.seed(42)
    accel_raw, gyro_raw, mag_raw = generate_simulated_sensor_data(n_samples, dt)
    
    print(f"\n原始数据统计:")
    print(f"  加速度计: mean={np.mean(accel_raw, axis=0).round(3)}, "
          f"std={np.std(accel_raw, axis=0).round(3)}")
    print(f"  陀螺仪:   mean={np.mean(gyro_raw, axis=0).round(5)}, "
          f"std={np.std(gyro_raw, axis=0).round(5)}")
    print(f"  磁力计:   mean={np.mean(mag_raw, axis=0).round(3)}, "
          f"std={np.std(mag_raw, axis=0).round(3)}")
    
    # 使用数据处理器
    print(f"\n--- 数据预处理 ---")
    processor = SensorDataProcessor(
        cutoff_freq=10.0,
        sample_rate=1.0/dt,
        max_std=3.0,
        window_size=5
    )
    
    # 逐点处理
    accel_clean = []
    gyro_clean = []
    mag_clean = []
    outlier_count = 0
    
    for i in range(n_samples):
        a, g, m = processor.process(accel_raw[i], gyro_raw[i], mag_raw[i])
        accel_clean.append(a)
        gyro_clean.append(g)
        if m is not None:
            mag_clean.append(m)
        if i > 0:
            if np.any(np.abs(accel_raw[i] - np.mean(accel_clean[-10:], axis=0)) > 5):
                outlier_count += 1
    
    accel_clean = np.array(accel_clean)
    gyro_clean = np.array(gyro_clean)
    mag_clean = np.array(mag_clean) if mag_clean else None
    
    print(f"\n处理后数据统计:")
    print(f"  加速度计: mean={np.mean(accel_clean, axis=0).round(3)}, "
          f"std={np.std(accel_clean, axis=0).round(3)}")
    print(f"  陀螺仪:   mean={np.mean(gyro_clean, axis=0).round(5)}, "
          f"std={np.std(gyro_clean, axis=0).round(5)}")
    if mag_clean is not None:
        print(f"  磁力计:   mean={np.mean(mag_clean, axis=0).round(3)}, "
              f"std={np.std(mag_clean, axis=0).round(3)}")
    
    # 展示滤波效果
    print(f"\n--- 滤波效果对比 (前 20 个采样) ---")
    print(f"{'采样':>6} | {'原始 accel[2]':>14} | {'滤波 accel[2]':>14}")
    print("-" * 40)
    for i in range(min(20, n_samples)):
        print(f"{i:>6} | {accel_raw[i, 2]:>14.4f} | {accel_clean[i, 2]:>14.4f}")
    
    # 单独演示各种滤波器
    print(f"\n--- 单独滤波器演示 ---")
    
    # 移动平均
    ma = MovingAverageFilter(window_size=10)
    test_data = np.sin(np.linspace(0, 4*np.pi, 50)) + np.random.randn(50) * 0.3
    ma_output = [ma.update(x) for x in test_data]
    print(f"移动平均: 原始 std={np.std(test_data):.4f}, "
          f"滤波后 std={np.std(ma_output):.4f}")
    
    # 低通滤波
    lp = LowPassFilter(cutoff_freq=5.0, sample_rate=50.0)
    lp_output = [lp.update(x) for x in test_data]
    print(f"低通滤波: 原始 std={np.std(test_data):.4f}, "
          f"滤波后 std={np.std(lp_output):.4f}")
    
    # 异常值检测
    detector = OutlierDetector(max_std=2.0)
    test_with_outlier = test_data.copy()
    test_with_outlier[25] = 100  # 添加异常值
    is_outlier, corrected = detector.update(test_with_outlier[25])
    print(f"异常值检测: 第25个采样 is_outlier={is_outlier}, "
          f"原始={test_with_outlier[25]:.2f}, 修正={corrected:.2f}")
    
    print(f"\n完成!")


if __name__ == '__main__':
    main()
