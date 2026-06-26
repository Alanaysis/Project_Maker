"""
Madgwick 滤波器

Madgwick 滤波器是一种基于梯度下降的姿态估计算法。
由 Sebastian Madgwick 提出，计算效率高，适合嵌入式实现。

核心思想:
- 用陀螺仪积分预测姿态
- 用加速度计和磁力计计算观测误差
- 用梯度下降修正姿态

与卡尔曼滤波相比:
- 不需要定义协方差矩阵
- 计算量更小
- 只需调整一个参数 (beta)

论文参考:
"Fast Attitude Estimation using a Gradient Descent Approach"
https://www.x-io.co.uk/open-source-imu-and-ahrs-algorithms/
"""

import numpy as np
from .coordinate_transform import (
    quaternion_multiply, quaternion_normalize,
    quaternion_conjugate, rotate_vector_by_quaternion
)


class MadgwickFilter:
    """
    Madgwick 滤波器
    
    实现论文中的四元数姿态估计算法。
    
    使用方式:
        filter = MadgwickFilter(beta=0.1, sample_period=1/256)
        for accel, gyro, mag in sensor_stream:
            q = filter.update(gyro, accel, mag, sample_period)
    """
    
    def __init__(self, beta=0.1, sample_period=1.0/256.0):
        """
        Args:
            beta: 滤波器增益参数 (0~1)
                  越大 -> 更快收敛到传感器观测
                  越小 -> 更信任陀螺仪
            sample_period: 采样周期 (秒)
        """
        self.beta = beta
        self.sample_period = sample_period
        
        # 初始姿态 (单位四元数)
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        
        # 半梯度
        self.f = np.zeros(6)
        # 雅可比矩阵 (6x4)
        self.J = np.zeros((6, 4))
    
    def update(self, gyro, accel, mag=None, sample_period=None):
        """
        更新姿态估计
        
        Args:
            gyro: 角速度 [wx, wy, wz] (rad/s)
            accel: 加速度 [ax, ay, az] (m/s^2)
            mag: 磁力计 [mx, my, mz] (可选)
            sample_period: 采样周期 (秒)，如果为 None 则使用初始化值
        
        Returns:
            更新后的四元数 [w, x, y, z]
        """
        dt = sample_period if sample_period is not None else self.sample_period
        
        # Step 1: 用陀螺仪预测姿态
        wx, wy, wz = gyro
        qw, qx, qy, qz = self.q
        
        # 四元数导数 (陀螺仪)
        q_dot = np.array([
            0.5 * (-wx*qx - wy*qy - wz*qz),
            0.5 * ( wx*qw + wz*qy - wy*qz),
            0.5 * ( wy*qw - wz*qx + wx*qz),
            0.5 * ( wz*qw + wy*qx - wx*qy)
        ])
        
        # Euler 积分
        q_pred = self.q + q_dot * dt
        self.q = quaternion_normalize(q_pred)
        
        # Step 2: 计算测量残差 (gradient)
        qw, qx, qy, qz = self.q
        
        # 归一化加速度和磁力计
        norm_accel = np.linalg.norm(accel)
        if norm_accel > 0:
            accel = accel / norm_accel
        else:
            accel = np.array([0.0, 0.0, 1.0])
        
        if mag is not None and np.linalg.norm(mag) > 0:
            mag = mag / np.linalg.norm(mag)
        else:
            mag = None
        
        # 计算期望的重力和磁场方向 (机体坐标系)
        # 从四元数反算: 导航系单位向量旋转到机体系
        # 重力: [0, 0, 1] in navigation frame
        self.f[0] = 2*(qx*qz - qw*qy) - accel[0]
        self.f[1] = 2*(qw*qx + qy*qz) - accel[1]
        self.f[2] = 1 - 2*(qx**2 + qy**2) - accel[2]
        
        if mag is not None:
            # 磁场: [0, 0, 1] in navigation frame (简化)
            self.f[3] = 2*qw*qy + 2*qx*qz - mag[0]
            self.f[4] = -2*qw*qx + 2*qy*qz - mag[1]
            self.f[5] = 1 - 2*(qx**2 + qy**2) - mag[2]
        else:
            # 无磁力计，只用加速度计
            self.f[3] = 0
            self.f[4] = 0
            self.f[5] = 0
        
        # Step 3: 计算雅可比矩阵
        self.J[0, 0] = qy
        self.J[0, 1] = 0
        self.J[0, 2] = -qw
        self.J[0, 3] = -qx
        
        self.J[1, 0] = qw
        self.J[1, 1] = qz
        self.J[1, 2] = -qx
        self.J[1, 3] = -qy
        
        self.J[2, 0] = 2*qx
        self.J[2, 1] = 2*qy
        self.J[2, 2] = 0
        self.J[2, 3] = 0
        
        if mag is not None:
            self.J[3, 0] = 2*qy
            self.J[3, 1] = 2*qz
            self.J[3, 2] = 0
            self.J[3, 3] = 0
            
            self.J[4, 0] = -2*qx
            self.J[4, 1] = -2*qw
            self.J[4, 2] = 2*qz
            self.J[4, 3] = 0
            
            self.J[5, 0] = 0
            self.J[5, 1] = 0
            self.J[5, 2] = -4*qx
            self.J[5, 3] = -4*qy
        else:
            self.J[3:, :] = 0
        
        # Step 4: 计算梯度 (J^T * f)
        Jt_f = self.J.T @ self.f
        
        # Step 5: 归一化梯度
        norm_grad = np.sqrt(np.sum(Jt_f**2))
        if norm_grad > 0:
            Jt_f_norm = Jt_f / norm_grad
        else:
            Jt_f_norm = Jt_f
        
        # Step 6: 四元数修正
        q_correction = np.array([
            0.5 * (-wx*qx - wy*qy - wz*qz),
            0.5 * ( wx*qw + wz*qy - wy*qz),
            0.5 * ( wy*qw - wz*qx + wx*qz),
            0.5 * ( wz*qw + wy*qx - wx*qy)
        ])
        
        # 结合陀螺仪预测和梯度修正
        q_dot_total = q_correction - self.beta * Jt_f_norm
        
        # Euler 积分
        q_new = self.q + q_dot_total * dt
        self.q = quaternion_normalize(q_new)
        
        return self.q.copy()
    
    def update_accel(self, gyro, accel, sample_period=None):
        """
        仅用加速度计更新 (无磁力计)
        
        Args:
            gyro: 角速度 [wx, wy, wz]
            accel: 加速度 [ax, ay, az]
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
            'rotation_matrix': R
        }


class MadgwickFilterAdaptive(MadgwickFilter):
    """
    自适应 Madgwick 滤波器
    
    根据加速度计的可靠性动态调整 beta:
    - 振动大时: 减小 beta (更信任陀螺仪)
    - 振动小时: 增大 beta (更快收敛)
    """
    
    def __init__(self, base_beta=0.1, min_beta=0.01, max_beta=1.0, 
                 jerk_threshold=5.0, sample_period=1.0/256.0):
        """
        Args:
            base_beta: 基础 beta 值
            min_beta: 最小 beta (高振动)
            max_beta: 最大 beta (低振动)
            jerk_threshold: 振动阈值
            sample_period: 采样周期
        """
        super().__init__(beta=base_beta, sample_period=sample_period)
        self.base_beta = base_beta
        self.min_beta = min_beta
        self.max_beta = max_beta
        self.jerk_threshold = jerk_threshold
        self.prev_accel = None
        self.jerk = 0.0
    
    def update(self, gyro, accel, mag=None, sample_period=None):
        """
        自适应更新
        """
        # 计算振动强度
        if self.prev_accel is not None:
            jerk = np.linalg.norm((accel - self.prev_accel) / 
                                  (sample_period or self.sample_period))
            self.jerk = 0.9 * self.jerk + 0.1 * jerk
        self.prev_accel = accel.copy()
        
        # 动态调整 beta
        if self.jerk > self.jerk_threshold:
            ratio = min(self.jerk / (self.jerk_threshold * 2), 1.0)
            self.beta = self.base_beta + ratio * (self.max_beta - self.base_beta)
        else:
            self.beta = self.min_beta
        
        return super().update(gyro, accel, mag, sample_period)
    
    def get_beta(self):
        """获取当前 beta 值"""
        return self.beta
