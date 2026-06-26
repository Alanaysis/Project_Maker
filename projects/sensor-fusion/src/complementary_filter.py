"""
互补滤波器 (Complementary Filter)

互补滤波器是一种简单而有效的传感器融合方法。
它利用加速度计的低频特性和陀螺仪的高频特性，
通过互补的权重组合两者，获得更稳定的姿态估计。

核心思想:
- 陀螺仪: 高频准确 (短期精确)，但存在漂移
- 加速度计: 低频准确 (长期稳定)，但易受振动干扰
- 互补滤波: 高频部分用陀螺仪，低频部分用加速度计

公式:
    theta_fused = alpha * (theta_prev + gyro * dt) + (1 - alpha) * accel_theta

其中 alpha = RC / (RC + dt)，RC 是时间常数
"""

import numpy as np
from .coordinate_transform import (
    euler_to_quaternion, quaternion_multiply, 
    quaternion_normalize, rotate_vector_by_quaternion
)


class ComplementaryFilter:
    """
    互补滤波器
    
    实现基于四元数的互补滤波姿态估计。
    
    使用方式:
        filter = ComplementaryFilter(gain=0.98)
        for raw_data in sensor_stream:
            attitude = filter.update(raw_data.accel, raw_data.gyro, dt)
    """
    
    def __init__(self, gain=0.98, axis='z'):
        """
        初始化互补滤波器
        
        Args:
            gain: 互补滤波增益 (0~1)，越接近 1 越信任陀螺仪
            axis: 参考轴 ('x', 'y', 'z')，用于简化 2D 互补滤波
        """
        self.gain = gain
        self.axis = axis
        
        # 初始姿态 (四元数)
        self.q = np.array([1.0, 0.0, 0.0, 0.0])  # 单位四元数 (无旋转)
        
        # 加速度计计算的重力方向误差 (用于自适应增益)
        self.accel_error = np.array([0.0, 0.0, 0.0])
        
        # 历史数据 (用于自适应增益)
        self.error_history = []
        self.max_history = 100
    
    def _get_accel_pitch_roll(self, accel):
        """
        从加速度计读数计算俯仰角和横滚角
        
        原理: 静止时，加速度计测量的是重力在机体坐标系的投影。
        
        pitch = atan2(ay, az)
        roll  = atan2(-ax, sqrt(ay^2 + az^2))
        
        Args:
            accel: 加速度读数 [ax, ay, az] (m/s^2)
        
        Returns:
            (roll, pitch) 弧度
        """
        ax, ay, az = accel
        
        # 计算俯仰角 (pitch)
        pitch = np.arctan2(ay, np.sqrt(ax**2 + az**2))
        
        # 计算横滚角 (roll)
        roll = np.arctan2(-ax, ay * np.sin(pitch) + az * np.cos(pitch))
        
        return roll, pitch
    
    def _get_accel_gravity_direction(self, accel):
        """
        从加速度计计算重力方向 (归一化)
        
        用于四元数形式的互补滤波
        
        Args:
            accel: 加速度读数 [ax, ay, az]
        
        Returns:
            归一化的重力方向向量
        """
        magnitude = np.linalg.norm(accel)
        if magnitude < 1e-10:
            return np.array([0.0, 0.0, 1.0])  # 默认向下
        return accel / magnitude
    
    def update(self, accel, gyro, dt):
        """
        更新姿态估计
        
        互补滤波步骤:
        1. 用陀螺仪预测新姿态 (积分)
        2. 用加速度计计算重力方向误差
        3. 将误差反馈到姿态估计
        
        Args:
            accel: 加速度读数 [ax, ay, az] (m/s^2)
            gyro: 角速度读数 [wx, wy, wz] (rad/s)
            dt: 时间步长 (秒)
        
        Returns:
            更新后的四元数 [w, x, y, z]
        """
        # Step 1: 用陀螺仪预测姿态
        wx, wy, wz = gyro
        qw, qx, qy, qz = self.q
        
        dq = np.array([
            -wx*qx - wy*qy - wz*qz,
             wx*qw + wz*qy - wy*qz,
             wy*qw - wz*qx + wx*qz,
             wz*qw + wy*qx - wx*qy
        ])
        
        q_pred = self.q + dq * dt
        self.q = quaternion_normalize(q_pred)
        
        # Step 2: 用加速度计计算重力方向误差
        gravity_body = self._get_accel_gravity_direction(accel)
        gravity_nav = np.array([0.0, 0.0, 1.0])
        
        gravity_predicted = rotate_vector_by_quaternion(
            self.q, gravity_nav
        )
        
        self.accel_error = np.cross(gravity_predicted, gravity_body)
        
        # Step 3: 误差反馈
        k_p = 2.0
        error_gyro = self.accel_error * k_p
        gyro_corrected = gyro + error_gyro * (1 - self.gain)
        
        # 用修正后的陀螺仪更新姿态
        wx, wy, wz = gyro_corrected
        qw, qx, qy, qz = self.q
        
        dq = np.array([
            -wx*qx - wy*qy - wz*qz,
             wx*qw + wz*qy - wy*qz,
             wy*qw - wz*qx + wx*qz,
             wz*qw + wy*qx - wx*qy
        ])
        
        q_new = self.q + dq * dt
        self.q = quaternion_normalize(q_new)
        
        return self.q.copy()
    
    def update_2d(self, accel, gyro_z, dt):
        """
        2D 互补滤波 (适用于平面运动)
        
        仅估计俯仰角或横滚角，适用于自平衡车等场景。
        
        Args:
            accel: 加速度读数 [ax, ay, az]
            gyro_z: Z 轴角速度 (rad/s)
            dt: 时间步长
        
        Returns:
            (roll, pitch) 弧度
        """
        # 从加速度计计算角度
        ax, ay, az = accel
        pitch = np.arctan2(ay, np.sqrt(ax**2 + az**2))
        roll = np.arctan2(-ax, ay * np.sin(pitch) + az * np.cos(pitch))
        
        if self.axis == 'z':
            # 绕 Z 轴旋转 (偏航)
            angle = np.arctan2(
                2*(self.q[0]*self.q[3] + self.q[1]*self.q[2]),
                1 - 2*(self.q[2]**2 + self.q[3]**2)
            )
        else:
            angle = pitch
        
        # 互补滤波
        angle_pred = angle + gyro_z * dt
        angle_fused = self.gain * angle_pred + (1 - self.gain) * pitch
        
        # 更新四元数
        if self.axis == 'z':
            cos_a, sin_a = np.cos(angle_fused / 2), np.sin(angle_fused / 2)
            self.q = np.array([cos_a, 0, 0, sin_a])
        else:
            cos_a, sin_a = np.cos(angle_fused / 2), np.sin(angle_fused / 2)
            self.q = np.array([cos_a, sin_a, 0, 0])
        
        return roll, pitch
    
    def get_euler_angles(self):
        """
        从四元数获取欧拉角
        
        Returns:
            (roll, pitch, yaw) 弧度
        """
        q = self.q
        
        # Roll (横滚角)
        sinr_cosp = 2 * (q[0] * q[1] + q[2] * q[3])
        cosr_cosp = 1 - 2 * (q[1]**2 + q[2]**2)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch (俯仰角)
        sinp = 2 * (q[0] * q[2] - q[3] * q[1])
        if np.abs(sinp) >= 1:
            pitch = np.copysign(np.pi / 2, sinp)  # 万向锁
        else:
            pitch = np.arcsin(sinp)
        
        # Yaw (偏航角)
        siny_cosp = 2 * (q[0] * q[3] + q[1] * q[2])
        cosy_cosp = 1 - 2 * (q[2]**2 + q[3]**2)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        return roll, pitch, yaw
    
    def get_attitude(self):
        """
        获取完整姿态信息
        
        Returns:
            字典包含:
                - quaternion: 四元数 [w, x, y, z]
                - euler: (roll, pitch, yaw) 弧度
                - rotation_matrix: 3x3 旋转矩阵
        """
        roll, pitch, yaw = self.get_euler_angles()
        
        from .coordinate_transform import (
            quaternion_to_rotation_matrix, euler_to_quaternion
        )
        R = quaternion_to_rotation_matrix(self.q)
        
        return {
            'quaternion': self.q.copy(),
            'euler': (roll, pitch, yaw),
            'rotation_matrix': R,
            'accel_error': self.accel_error.copy()
        }


class AdaptiveComplementaryFilter(ComplementaryFilter):
    """
    自适应互补滤波器
    
    根据加速度计的可靠性动态调整增益:
    - 振动大时 (加速度变化剧烈): 降低增益，更多信任陀螺仪
    - 振动小时: 提高增益，更多信任加速度计
    
    通过监测加速度的导数 (jerk) 来判断振动程度。
    """
    
    def __init__(self, base_gain=0.98, min_gain=0.8, max_gain=0.999, jerk_threshold=5.0):
        """
        Args:
            base_gain: 基础增益
            min_gain: 最小增益 (高振动时)
            max_gain: 最大增益 (低振动时)
            jerk_threshold: 振动阈值 (m/s^3)
        """
        super().__init__(gain=base_gain)
        self.base_gain = base_gain
        self.min_gain = min_gain
        self.max_gain = max_gain
        self.jerk_threshold = jerk_threshold
        self.prev_accel = None
        self.jerk = 0.0
    
    def update(self, accel, gyro, dt):
        """
        自适应更新姿态
        
        Args:
            accel: 加速度读数 [ax, ay, az]
            gyro: 角速度读数 [wx, wy, wz]
            dt: 时间步长
        
        Returns:
            更新后的四元数
        """
        # 计算振动强度 (加速度变化率)
        if self.prev_accel is not None:
            jerk = np.linalg.norm((accel - self.prev_accel) / dt)
            self.jerk = 0.9 * self.jerk + 0.1 * jerk  # 平滑
        self.prev_accel = accel.copy()
        
        # 根据振动调整增益
        if self.jerk > self.jerk_threshold:
            # 高振动: 降低增益
            ratio = min(self.jerk / (self.jerk_threshold * 2), 1.0)
            self.gain = self.base_gain + (1 - ratio) * (self.base_gain - self.min_gain)
        else:
            # 低振动: 提高增益
            self.gain = self.max_gain
        
        # 调用父类更新
        return super().update(accel, gyro, dt)
    
    def get_gain(self):
        """获取当前增益值"""
        return self.gain
