"""
示例 2: 互补滤波器演示

演示互补滤波器的工作原理和效果。
对比不同增益参数对滤波结果的影响。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.complementary_filter import ComplementaryFilter, AdaptiveComplementaryFilter
from src.coordinate_transform import euler_to_quaternion


def generate_simulated_motion(n_samples=500, dt=0.01):
    """
    生成模拟的运动数据
    
    模拟一个做周期性俯仰运动的 IMU:
    - 真实俯仰角: sin 波形
    - 陀螺仪: 真实角速度 + 偏置 + 噪声
    - 加速度计: 重力投影 + 振动噪声
    """
    t = np.arange(n_samples) * dt
    
    # 真实俯仰角 (绕 Y 轴旋转)
    true_pitch = 0.3 * np.sin(2 * np.pi * 0.1 * t)
    true_gyro_z = 0.3 * 2 * np.pi * 0.1 * np.cos(2 * np.pi * 0.1 * t)
    
    # 陀螺仪读数 (带偏置和噪声)
    gyro_bias = 0.02  # 2 deg/s 偏置
    gyro = np.column_stack([
        np.zeros(n_samples),
        true_gyro_z + np.random.randn(n_samples) * 0.005,
        np.zeros(n_samples)
    ])
    gyro[:, 1] += gyro_bias  # 添加偏置
    
    # 加速度计读数
    # 静止时: [0, 0, g]
    # 旋转后: R_y(pitch) * [0, 0, g]
    accel = np.column_stack([
        -9.81 * np.sin(true_pitch) + np.random.randn(n_samples) * 0.1,
        np.zeros(n_samples) + np.random.randn(n_samples) * 0.1,
        9.81 * np.cos(true_pitch) + np.random.randn(n_samples) * 0.1
    ])
    
    return true_pitch, gyro, accel, dt


def main():
    print("=" * 60)
    print("示例 2: 互补滤波器演示")
    print("=" * 60)
    
    n_samples = 500
    dt = 0.01
    true_pitch, gyro, accel, dt = generate_simulated_motion(n_samples, dt)
    
    print(f"\n模拟参数:")
    print(f"  采样率: {1/dt:.0f} Hz")
    print(f"  运动频率: 0.1 Hz (周期 10s)")
    print(f"  俯仰角幅度: {np.degrees(0.3):.1f} 度")
    print(f"  陀螺仪偏置: {np.degrees(0.02):.2f} 度/秒")
    
    # 测试不同增益
    gains = [0.90, 0.95, 0.98, 0.99]
    print(f"\n--- 不同增益对比 ---")
    print(f"增益 | 俯仰角 RMSE")
    print("-" * 30)
    
    results = {}
    for gain in gains:
        filter = ComplementaryFilter(gain=gain)
        estimated_pitch = []
        
        for i in range(n_samples):
            q = filter.update(accel[i], gyro[i], dt)
            roll, pitch, yaw = filter.get_euler_angles()
            estimated_pitch.append(pitch)
        
        estimated_pitch = np.array(estimated_pitch)
        rmse = np.sqrt(np.mean((estimated_pitch - true_pitch)**2))
        results[gain] = estimated_pitch
        
        print(f"{gain:.2f}  | {rmse:.6f} rad")
    
    # 自适应互补滤波
    print(f"\n--- 自适应互补滤波 ---")
    adaptive = AdaptiveComplementaryFilter(base_gain=0.98)
    adaptive_pitch = []
    
    for i in range(n_samples):
        q = adaptive.update(accel[i], gyro[i], dt)
        roll, pitch, yaw = adaptive.get_euler_angles()
        adaptive_pitch.append(pitch)
    
    adaptive_pitch = np.array(adaptive_pitch)
    rmse_adaptive = np.sqrt(np.mean((adaptive_pitch - true_pitch)**2))
    print(f"自适应增益 RMSE: {rmse_adaptive:.6f} rad")
    print(f"自适应增益范围: [{adaptive.min_gain}, {adaptive.max_gain}]")
    
    # 展示结果
    print(f"\n--- 姿态估计结果 (部分时间步) ---")
    print(f"{'时间(s)':>8} | {'真实 pitch':>12} | {'增益0.95':>12} | {'增益0.99':>12}")
    print("-" * 55)
    
    step = max(1, n_samples // 20)
    for i in range(0, n_samples, step):
        t_sec = i * dt
        print(f"{t_sec:>8.2f} | {true_pitch[i]:>12.4f} | "
              f"{results[0.95][i]:>12.4f} | {results[0.99][i]:>12.4f}")
    
    print(f"\n关键观察:")
    print(f"  - 增益较高 (0.99): 响应快，但噪声较大")
    print(f"  - 增益较低 (0.90): 响应慢，但更平滑")
    print(f"  - 互补滤波的核心: 在响应速度和噪声抑制之间权衡")
    print(f"\n完成!")


if __name__ == '__main__':
    main()
