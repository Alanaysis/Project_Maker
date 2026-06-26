"""
Mahony 滤波器

Mahony 滤波器是另一种基于比例-积分 (PI) 反馈的姿态估计算法。
由 Oliver Mahony 提出。

与 Madgwick 的区别:
- Mahony 使用 PI 控制器修正陀螺仪偏置
- Madgwick 使用梯度下降修正四元数
- Mahony 通常对磁力计更鲁棒

核心方程:
    u = gyro + Kp * error + Ki * integral(error)
    q_dot = 0.5 * q ⊗ [0, u]
    q = normalize(q)
"""

import numpy as np
from .coordinate_transform import (
    quaternion_multiply, quaternion_normalize,
    quaternion_conjugate
)


class MahonyFilter:
    """
    Mahony 互补滤波器
    
    实现基于 PI 反馈的姿态估计。
    
    使用方式:
        filter = MahonyFilter(Kp=2.0, Ki=0.1, sample_period=1/256)
        for gyro, accel, mag in sensor_stream:
            q = filter.update(gyro, accel, mag, sample_period)
    """
    
    def __init__(self, Kp=2.0, Ki=0.1, sample_period=1.0/256.0):
        """
        Args:
            Kp: 比例增益
            Ki: 积分增益
            sample_period: 采样周期 (秒)
        """
        self.Kp = Kp
        self.Ki = Ki
        self.sample_period = sample_period
        
        # 初始姿态
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        
        # 积分误差 (陀螺仪偏置估计)
        self.bias = np.zeros(3)
        self.integral_error = np.zeros(3)
        
        # 测量方向
        self.measured_accel = np.zeros(3)
        self.measured_mag = np.zeros(3)
        
        # 参考方向 (导航系)
        self.ref_accel = np.array([0.0, 0.0, 1.0])
        self.ref_mag = np.array([0.0, 0.0, 1.0])
    
    def _compute_error(self, measured_accel, measured_mag=None):
        """
        计算方向误差
        
        误差 = cross(measured_ref, estimated_ref)
        其中 measured_ref 是传感器测量的方向
        estimated_ref 是从当前姿态估计的方向
        
        Args:
            measured_accel: 归一化的加速度测量 [ax, ay, az]
            measured_mag: 归一化的磁力计测量 [mx, my, mz]
        
        Returns:
            误差向量
        """
        qw, qx, qy, qz = self.q
        
        # 估计的重力方向 (机体坐标系)
        estimated_gravity = np.array([
            2*(qx*qz - qw*qy),
            2*(qw*qx + qy*qz),
            1 - 2*(qx**2 + qy**2)
        ])
        
        # 重力方向误差
        error = np.cross(estimated_gravity, measured_accel)
        
        if measured_mag is not None:
            # 估计的磁场方向
            estimated_mag = np.array([
                2*(qw*qy + qx*qz),
                2*(qw*qx - qy*qz),
                1 - 2*(qx**2 + qy**2)
            ])
            
            # 磁场方向误差
            error_mag = np.cross(estimated_mag, measured_mag)
            
            # 合并误差 (加权)
            error = np.concatenate([error * 0.5, error_mag * 0.5])
        else:
            # 无磁力计，只用加速度计
            pass
        
        return error
    
    def update(self, gyro, accel, mag=None, sample_period=None):
        """
        更新姿态估计
        
        Args:
            gyro: 角速度 [wx, wy, wz] (rad/s)
            accel: 加速度 [ax, ay, az] (归一化)
            mag: 磁力计 [mx, my, mz] (归一化，可选)
            sample_period: 采样周期
        
        Returns:
            更新后的四元数
        """
        dt = sample_period if sample_period is not None else self.sample_period
        
        # 归一化加速度
        norm_accel = np.linalg.norm(accel)
        if norm_accel > 0:
            accel_normalized = accel / norm_accel
        else:
            accel_normalized = self.measured_accel.copy()
        self.measured_accel = accel_normalized
        
        # 归一化磁力计
        if mag is not None and np.linalg.norm(mag) > 0:
            mag_normalized = mag / np.linalg.norm(mag)
        else:
            mag_normalized = self.measured_mag if np.linalg.norm(self.measured_mag) > 0 else None
        if mag_normalized is not None:
            self.measured_mag = mag_normalized
        
        # 计算误差
        error_accel = np.cross(
            np.array([
                2*(self.q[1]*self.q[3] - self.q[0]*self.q[2]),
                2*(self.q[0]*self.q[1] + self.q[2]*self.q[3]),
                1 - 2*(self.q[1]**2 + self.q[2]**2)
            ]),
            accel_normalized
        )
        
        error = error_accel
        
        if mag_normalized is not None:
            error_mag = np.cross(
                np.array([
                    2*(self.q[0]*self.q[3] + self.q[1]*self.q[2]),
                    2*(self.q[0]*self.q[1] - self.q[2]*self.q[3]),
                    1 - 2*(self.q[1]**2 + self.q[2]**2)
                ]),
                mag_normalized
            )
            # 合并加速度和磁力计误差
            error = np.array([
                error_accel[0] + error_mag[0],
                error_accel[1] + error_mag[1],
                error_accel[2] + error_mag[2]
            ])
        
        # PI 控制
        # 积分项
        self.integral_error += error * dt
        # 限幅
        max_integral = 0.5
        self.integral_error = np.clip(self.integral_error, -max_integral, max_integral)
        
        # 修正角速度
        correction = self.Kp * error + self.Ki * self.integral_error
        gyro_corrected = gyro - self.bias - correction
        
        # 四元数积分
        wx, wy, wz = gyro_corrected
        qw, qx, qy, qz = self.q
        
        q_dot = np.array([
            0.5 * (-wx*qx - wy*qy - wz*qz),
            0.5 * ( wx*qw + wz*qy - wy*qz),
            0.5 * ( wy*qw - wz*qx + wx*qz),
            0.5 * ( wz*qw + wy*qx - wx*qy)
        ])
        
        q_new = self.q + q_dot * dt
        self.q = quaternion_normalize(q_new)
        
        # 更新偏置估计 (仅当静止时)
        # 可以通过加速度计判断是否静止
        
        return self.q.copy()
    
    def update_accel_only(self, gyro, accel, sample_period=None):
        """
        仅用加速度计更新
        
        Args:
            gyro: 角速度
            accel: 加速度
            sample_period: 采样周期
        
        Returns:
            更新后的四元数
        """
        return self.update(gyro, accel, mag=None, sample_period=sample_period)
    
    def get_euler_angles(self):
        """
        从四元数获取欧拉角
        
        Returns:
            (roll, pitch, yaw) 弧度
        """
        q = self.q
        
        # Roll
        sinr_cosp = 2 * (q[0]*q[1] + q[2]*q[3])
        cosr_cosp = 1 - 2*(q[1]**2 + q[2]**2)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch
        sinp = 2 * (q[0]*q[2] - q[3]*q[1])
        sinp = np.clip(sinp, -1, 1)
        pitch = np.arcsin(sinp)
        
        # Yaw
        siny_cosp = 2 * (q[0]*q[3] + q[1]*q[2])
        cosy_cosp = 1 - 2*(q[2]**2 + q[3]**2)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        return roll, pitch, yaw
    
    def get_attitude(self):
        """获取完整姿态信息"""
        roll, pitch, yaw = self.get_euler_angles()
        from .coordinate_transform import quaternion_to_rotation_matrix
        R = quaternion_to_rotation_matrix(self.q)
        
        return {
            'quaternion': self.q.copy(),
            'euler': (roll, pitch, yaw),
            'rotation_matrix': R,
            'gyro_bias': self.bias.copy()
        }
    
    def reset(self):
        """重置滤波器状态"""
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.bias = np.zeros(3)
        self.integral_error = np.zeros(3)
        self.measured_accel = np.zeros(3)
        self.measured_mag = np.zeros(3)


class MahonyFilterAdaptive(MahonyFilter):
    """
    自适应 Mahony 滤波器
    
    根据运动状态动态调整 Kp 和 Ki。
    """
    
    def __init__(self, base_Kp=2.0, base_Ki=0.1, sample_period=1.0/256.0):
        super().__init__(Kp=base_Kp, Ki=base_Ki, sample_period=sample_period)
        self.base_Kp = base_Kp
        self.base_Ki = base_Ki
        self.prev_accel = None
    
    def update(self, gyro, accel, mag=None, sample_period=None):
        """自适应更新"""
        # 计算加速度变化率
        if self.prev_accel is not None:
            accel_change = np.linalg.norm(accel - self.prev_accel)
            # 高振动时降低 Kp
            if accel_change > 2.0:
                self.Kp = self.base_Kp * 0.5
                self.Ki = self.base_Ki * 0.5
            else:
                self.Kp = self.base_Kp
                self.Ki = self.base_Ki
        self.prev_accel = accel.copy()
        
        return super().update(gyro, accel, mag, sample_period)
