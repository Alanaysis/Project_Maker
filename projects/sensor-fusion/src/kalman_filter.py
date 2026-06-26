"""
卡尔曼滤波器 (Kalman Filter)

卡尔曼滤波是一种最优递归估计算法，用于从噪声观测中估计系统状态。
在传感器融合中，它被广泛用于融合 IMU 数据以获得精确的姿态估计。

核心思想:
1. 预测 (Prediction): 用系统模型预测下一时刻状态
2. 更新 (Update): 用新观测修正预测

卡尔曼滤波的关键方程:
    预测:
        x_pred = F * x_prev + B * u
        P_pred = F * P_prev * F^T + Q
    
    更新:
        K = P_pred * H^T * (H * P_pred * H^T + R)^(-1)
        x_update = x_pred + K * (z - H * x_pred)
        P_update = (I - K * H) * P_pred

其中:
    x: 状态向量
    P: 状态协方差矩阵
    F: 状态转移矩阵
    Q: 过程噪声协方差
    H: 观测矩阵
    R: 观测噪声协方差
    K: 卡尔曼增益
"""

import numpy as np
from .coordinate_transform import (
    quaternion_multiply, quaternion_normalize,
    rotate_vector_by_quaternion, skew_symmetric
)


class KalmanFilter:
    """
    标准卡尔曼滤波器
    
    适用于线性系统。对于非线性系统 (如姿态估计)，
    需要使用扩展卡尔曼滤波 (EKF) 或无迹卡尔曼滤波 (UKF)。
    
    参数:
        state_dim: 状态维度
        obs_dim: 观测维度
    """
    
    def __init__(self, state_dim, obs_dim):
        """
        Args:
            state_dim: 状态向量维度
            obs_dim: 观测向量维度
        """
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        
        # 状态向量
        self.x = np.zeros(state_dim)
        
        # 状态协方差矩阵
        self.P = np.eye(state_dim) * 10.0
        
        # 状态转移矩阵 (线性系统)
        self.F = np.eye(state_dim)
        
        # 控制矩阵
        self.B = np.zeros((state_dim, 1))
        
        # 观测矩阵
        self.H = np.zeros((obs_dim, state_dim))
        
        # 过程噪声协方差
        self.Q = np.eye(state_dim) * 0.01
        
        # 观测噪声协方差
        self.R = np.eye(obs_dim)
        
        # 卡尔曼增益 (缓存)
        self.K = np.zeros((state_dim, obs_dim))
        
        # 创新 (观测残差)
        self.innovation = np.zeros(obs_dim)
        self.innovation_diag = np.zeros(obs_dim)
    
    def predict(self, u=None):
        """
        预测步骤
        
        Args:
            u: 控制输入 (可选)
        """
        # x_pred = F * x + B * u
        if u is not None:
            self.x = self.F @ self.x + self.B.flatten() * u
        else:
            self.x = self.F @ self.x
        
        # P_pred = F * P * F^T + Q
        self.P = self.F @ self.P @ self.F.T + self.Q
    
    def update(self, z):
        """
        更新步骤
        
        Args:
            z: 观测向量
        """
        # 创新: y = z - H * x_pred
        self.innovation = z - self.H @ self.x
        
        # 创新协方差: S = H * P_pred * H^T + R
        S = self.H @ self.P @ self.H.T + self.R
        
        # 卡尔曼增益: K = P_pred * H^T * S^(-1)
        self.K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # 状态更新: x_update = x_pred + K * y
        self.x = self.x + self.K @ self.innovation
        
        # 协方差更新: P_update = (I - K * H) * P_pred
        I_KH = np.eye(self.state_dim) - self.K @ self.H
        self.P = I_KH @ self.P
        
        # 计算创新对角线 (用于监控)
        self.innovation_diag = np.diag(S)
    
    def get_state(self):
        """获取当前状态估计"""
        return self.x.copy()
    
    def get_covariance(self):
        """获取状态协方差"""
        return self.P.copy()


class ExtendedKalmanFilter:
    """
    扩展卡尔曼滤波器 (EKF)
    
    用于非线性系统的卡尔曼滤波。
    通过线性化 (泰勒展开一阶近似) 处理非线性系统。
    
    EKF 的关键修改:
    - 用雅可比矩阵 J_F = dF/dx 代替 F
    - 用雅可比矩阵 J_H = dH/dx 代替 H
    
    姿态估计中，状态通常包含四元数，需要特殊处理。
    """
    
    def __init__(self, state_dim, obs_dim, process_noise=1e-4, observation_noise=1e-2):
        """
        Args:
            state_dim: 状态维度
            obs_dim: 观测维度
            process_noise: 过程噪声强度
            observation_noise: 观测噪声强度
        """
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim) * 0.1
        
        self.Q = np.eye(state_dim) * process_noise
        self.R = np.eye(obs_dim) * observation_noise
        
        # 雅可比矩阵缓存
        self.J_F = np.eye(state_dim)
        self.J_H = np.zeros((obs_dim, state_dim))
        
        self.K = np.zeros((state_dim, obs_dim))
        self.innovation = np.zeros(obs_dim)
    
    def _linearize_f(self, state, control):
        """
        线性化状态转移函数: J_F = dF/dx
        
        子类需要重写此方法以定义具体的状态转移模型。
        
        默认: 恒速模型 (状态转移矩阵为单位矩阵)
        """
        return np.eye(self.state_dim)
    
    def _linearize_h(self, state):
        """
        线性化观测函数: J_H = dH/dx
        
        子类需要重写此方法以定义具体的观测模型。
        
        默认: 直接观测所有状态
        """
        return np.eye(min(self.obs_dim, self.state_dim))
    
    def predict(self, control=None):
        """
        EKF 预测步骤
        
        Args:
            control: 控制输入 (角速度等)
        """
        # 非线性预测
        self.x = self._predict_state(self.x, control)
        
        # 线性化
        self.J_F = self._linearize_f(self.x, control)
        
        # P_pred = J_F * P * J_F^T + Q
        self.P = self.J_F @ self.P @ self.J_F.T + self.Q
    
    def update(self, observation):
        """
        EKF 更新步骤
        
        Args:
            observation: 观测值
        """
        # 线性化观测模型
        self.J_H = self._linearize_h(self.x)
        
        # 创新: y = z - h(x_pred)
        predicted_obs = self._predict_observation(self.x)
        self.innovation = observation - predicted_obs
        
        # 创新协方差: S = J_H * P * J_H^T + R
        S = self.J_H @ self.P @ self.J_H.T + self.R
        
        # 卡尔曼增益: K = P * J_H^T * S^(-1)
        try:
            S_inv = np.linalg.inv(S)
            self.K = self.P @ self.J_H.T @ S_inv
        except np.linalg.LinAlgError:
            # 如果 S 奇异，使用伪逆
            self.K = self.P @ self.J_H.T @ np.linalg.pinv(S)
        
        # 状态更新
        self.x = self.x + self.K @ self.innovation
        
        # Joseph 形式协方差更新 (数值更稳定)
        I_KH = np.eye(self.state_dim) - self.K @ self.J_H
        self.P = (I_KH @ self.P @ I_KH.T) + self.K @ self.R @ self.K.T
        
        # 确保协方差矩阵对称
        self.P = (self.P + self.P.T) / 2
    
    def _predict_state(self, state, control):
        """预测状态 (子类重写)"""
        return state.copy()
    
    def _predict_observation(self, state):
        """预测观测 (子类重写)"""
        return state[:self.obs_dim].copy()
    
    def get_state(self):
        return self.x.copy()
    
    def get_covariance(self):
        return self.P.copy()


class AttitudeEKF(ExtendedKalmanFilter):
    """
    姿态估计扩展卡尔曼滤波器
    
    状态: [qw, qx, qy, qz, bw, by, bz] (四元数 + 陀螺仪偏置)
    观测: 加速度计 (重力方向) + 磁力计 (磁场方向)
    
    这是一个经典的 IMU 姿态估计 EKF 实现。
    
    状态向量:
        x[0:4]:   四元数 [qw, qx, qy, qz]
        x[4:7]:   陀螺仪零偏 [bx, by, bz]
    
    观测模型:
        z_accel: 加速度计读数 -> 重力方向
        z_mag:   磁力计读数 -> 磁场方向
    """
    
    def __init__(self, process_noise=1e-4, accel_noise=1e-2, mag_noise=1e-2):
        """
        Args:
            process_noise: 过程噪声强度
            accel_noise: 加速度计观测噪声
            mag_noise: 磁力计观测噪声
        """
        # 7 维状态: 4(四元数) + 3(陀螺偏置)
        super().__init__(state_dim=7, obs_dim=6)
        
        self.x = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.P = np.eye(7) * 0.01
        
        self.Q = np.eye(7)
        self.Q[0:4, 0:4] *= process_noise    # 四元数噪声
        self.Q[4:7, 4:7] *= process_noise * 10  # 偏置噪声 (更大)
        
        self.R_accel = np.eye(3) * accel_noise
        self.R_mag = np.eye(3) * mag_noise
        
        self.g0 = np.array([0.0, 0.0, 1.0])   # 参考重力方向 (导航系)
        self.h0 = np.array([0.0, 0.0, 1.0])   # 参考磁场方向 (导航系)
        
        self.prev_gyro = np.zeros(3)
    
    def _predict_state(self, state, gyro):
        """
        状态预测: 用陀螺仪数据传播四元数
        
        四元数微分方程:
        q_dot = 0.5 * omega_q ⊗ q
        
        其中 omega_q = [0, wx-bx, wy-by, wz-bz]
        """
        if gyro is None:
            return state.copy()
        
        qw, qx, qy, qz = state[0:4]
        bx, by, bz = state[4:7]
        
        # 去偏的角速度
        wx, wy, wz = gyro - state[4:7]
        
        # 四元数微分方程
        dt = 1.0  # 假设 dt=1，实际使用时需要乘以真实 dt
        
        # omega_q = [0, wx, wy, wz]
        # q_dot = 0.5 * omega_q ⊗ q
        dq = np.array([
            -wx*qx - wy*qy - wz*qz,
             wx*qw + wz*qy - wy*qz,
             wy*qw - wz*qx + wx*qz,
             wz*qw + wy*qx - wx*qy
        ])
        
        # 更新四元数
        new_q = state[0:4] + 0.5 * dq * dt
        new_q = quaternion_normalize(new_q)
        
        # 偏置假设随机游走 (缓慢变化)
        new_bias = state[4:7]
        
        return np.concatenate([new_q, new_bias])
    
    def _linearize_f(self, state, gyro):
        """
        线性化状态转移函数
        
        计算 J_F = dF/dx，其中 F 是四元数传播函数
        """
        # 简化的雅可比矩阵
        # 对于四元数传播，雅可比近似为单位矩阵 + 小修正
        J = np.eye(7)
        
        if gyro is None:
            return J
        
        # 角速度 (去偏)
        wx, wy, wz = gyro - state[4:7]
        
        # 四元数部分的雅可比 (简化)
        dt_real = 1.0
        omega_skew = skew_symmetric(np.array([wx, wy, wz]))
        J[0:4, 0:4] += -0.5 * dt_real * np.pad(omega_skew, ((0,1),(0,1)), constant_values=0)[:4, :4]
        
        # 四元数对偏置的雅可比 (简化)
        J[0:4, 4:7] = 0.0
        
        return J
    
    def _predict_observation_accel(self, state):
        """
        预测加速度计观测: 重力在机体系的投影
        
        导航系重力 g = [0, 0, g]^T
        机体系重力 = R^n_b * g = q_conj ⊗ [0, g] ⊗ q
        """
        qw, qx, qy, qz = state[0:4]
        
        # 导航系重力旋转到机体系
        q_conj = np.array([qw, -qx, -qy, -qz])
        q_g = np.array([0, 0, 0, 1.0])
        
        temp = quaternion_multiply(q_conj, q_g)
        g_body_q = quaternion_multiply(temp, state[0:4])
        
        return g_body_q[1:]
    
    def _predict_observation_mag(self, state):
        """
        预测磁力计观测: 地磁场在机体系的投影
        """
        qw, qx, qy, qz = state[0:4]
        
        q_conj = np.array([qw, -qx, -qy, -qz])
        q_h = np.array([0, 0, 0, 1.0])
        
        temp = quaternion_multiply(q_conj, q_h)
        h_body_q = quaternion_multiply(temp, state[0:4])
        
        return h_body_q[1:]
    
    def update_accel(self, accel_reading):
        """
        仅用加速度计更新
        
        Args:
            accel_reading: 加速度计读数 [ax, ay, az]
        """
        # 归一化加速度 (假设静止或缓慢运动)
        mag = np.linalg.norm(accel_reading)
        if mag < 1e-10:
            return
        
        z = accel_reading / mag
        
        # 预测观测
        z_pred = self._predict_observation_accel(self.x)
        z_pred_norm = z_pred / np.linalg.norm(z_pred)
        
        # 创新
        self.innovation = z - z_pred_norm
        
        # 观测雅可比 (简化: 假设直接观测)
        self.J_H = np.zeros((3, 7))
        self.J_H[0:3, 0:4] = self._compute_accel_jacobian(self.x)
        
        # 更新
        S = self.J_H @ self.P @ self.J_H.T + self.R_accel
        try:
            K = self.P @ self.J_H.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            K = self.P @ self.J_H.T @ np.linalg.pinv(S)
        
        self.x = self.x + K @ self.innovation
        
        # 归一化四元数
        self.x[0:4] = quaternion_normalize(self.x[0:4])
        
        # 协方差更新 (Joseph 形式)
        I_KH = np.eye(7) - K @ self.J_H
        self.P = (I_KH @ self.P @ I_KH.T) + K @ self.R_accel @ K.T
        self.P = (self.P + self.P.T) / 2
    
    def update_mag(self, mag_reading):
        """
        仅用磁力计更新
        
        Args:
            mag_reading: 磁力计读数 [mx, my, mz]
        """
        mag = np.linalg.norm(mag_reading)
        if mag < 1e-10:
            return
        
        z = mag_reading / mag
        
        z_pred = self._predict_observation_mag(self.x)
        z_pred_norm = z_pred / np.linalg.norm(z_pred)
        
        self.innovation = z - z_pred_norm
        
        self.J_H = np.zeros((3, 7))
        self.J_H[0:3, 0:4] = self._compute_mag_jacobian(self.x)
        
        S = self.J_H @ self.P @ self.J_H.T + self.R_mag
        try:
            K = self.P @ self.J_H.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            K = self.P @ self.J_H.T @ np.linalg.pinv(S)
        
        self.x = self.x + K @ self.innovation
        self.x[0:4] = quaternion_normalize(self.x[0:4])
        
        I_KH = np.eye(7) - K @ self.J_H
        self.P = (I_KH @ self.P @ I_KH.T) + K @ self.R_mag @ K.T
        self.P = (self.P + self.P.T) / 2
    
    def update(self, accel_reading=None, mag_reading=None, gyro=None):
        """
        完整更新: 预测 + 观测更新
        
        Args:
            accel_reading: 加速度计读数
            mag_reading: 磁力计读数
            gyro: 角速度读数
        
        Returns:
            更新后的四元数
        """
        # 预测
        self.predict(gyro)
        
        # 加速度计更新
        if accel_reading is not None:
            self.update_accel(accel_reading)
        
        # 磁力计更新
        if mag_reading is not None:
            self.update_mag(mag_reading)
        
        return self.x[0:4].copy()
    
    def _compute_accel_jacobian(self, state):
        """
        计算加速度计观测的雅可比矩阵
        
        d(g_body)/dq 的近似
        """
        qw, qx, qy, qz = state[0:4]
        
        # 重力在机体系的表达式:
        # gx = 2*(qx*qz - qw*qy)
        # gy = 2*(qw*qx + qy*qz)
        # gz = 1 - 2*(qx^2 + qy^2)
        
        J = np.zeros((3, 4))
        J[0, 0] = -2*qy
        J[0, 1] = 2*qz
        J[0, 2] = -2*qw
        J[0, 3] = 2*qx
        
        J[1, 0] = 2*qx
        J[1, 1] = 2*qw
        J[1, 2] = 2*qz
        J[1, 3] = 0
        
        J[2, 0] = 0
        J[2, 1] = -4*qx
        J[2, 2] = -4*qy
        J[2, 3] = 0
        
        return J
    
    def _compute_mag_jacobian(self, state):
        """
        计算磁力计观测的雅可比矩阵
        """
        qw, qx, qy, qz = state[0:4]
        
        # 类似重力，但参考磁场方向可能不同
        J = np.zeros((3, 4))
        J[0, 0] = -2*qy
        J[0, 1] = 2*qz
        J[0, 2] = -2*qw
        J[0, 3] = 2*qx
        
        J[1, 0] = 2*qx
        J[1, 1] = 2*qw
        J[1, 2] = 2*qz
        J[1, 3] = 0
        
        J[2, 0] = 0
        J[2, 1] = -4*qx
        J[2, 2] = -4*qy
        J[2, 3] = 0
        
        return J
    
    def get_attitude(self):
        """
        获取姿态估计
        
        Returns:
            包含四元数和欧拉角的字典
        """
        q = self.x[0:4]
        q = quaternion_normalize(q)
        
        # 计算欧拉角
        roll = np.arctan2(
            2*(q[0]*q[1] + q[2]*q[3]),
            1 - 2*(q[1]**2 + q[2]**2)
        )
        pitch = np.arcsin(np.clip(2*(q[0]*q[2] - q[3]*q[1]), -1, 1))
        yaw = np.arctan2(
            2*(q[0]*q[3] + q[1]*q[2]),
            1 - 2*(q[2]**2 + q[3]**2)
        )
        
        from .coordinate_transform import quaternion_to_rotation_matrix
        R = quaternion_to_rotation_matrix(q)
        
        return {
            'quaternion': q,
            'euler': (roll, pitch, yaw),
            'rotation_matrix': R,
            'gyro_bias': self.x[4:7].copy()
        }


class ComplementaryEKF:
    """
    互补卡尔曼滤波器
    
    结合互补滤波和卡尔曼滤波的优点:
    - 用互补滤波做快速预测
    - 用卡尔曼滤波做精确修正
    
    这种方法计算效率高，适合嵌入式系统。
    """
    
    def __init__(self, alpha=0.98, process_noise=1e-5, observation_noise=1e-3):
        """
        Args:
            alpha: 互补滤波增益
            process_noise: 过程噪声
            observation_noise: 观测噪声
        """
        self.alpha = alpha
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        
        # EKF 状态: [qw, qx, qy, qz, wx_bias, wy_bias, wz_bias]
        self.x_ekf = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.P_ekf = np.eye(7) * 0.01
        
        self.Q_ekf = np.eye(7)
        self.Q_ekf[0:4, 0:4] *= process_noise
        self.Q_ekf[4:7, 4:7] *= process_noise * 100
        
        self.R_obs = np.eye(3) * observation_noise
    
    def update(self, accel, gyro, dt):
        """
        更新姿态估计
        
        Args:
            accel: 加速度计读数
            gyro: 陀螺仪读数
            dt: 时间步长
        
        Returns:
            更新后的四元数
        """
        # Step 1: 互补滤波预测
        wx, wy, wz = gyro
        qw, qx, qy, qz = self.q
        
        dq = np.array([
            -wx*qx - wy*qy - wz*qz,
             wx*qw + wz*qy - wy*qz,
             wy*qw - wz*qx + wx*qz,
             wz*qw + wy*qx - wx*qy
        ])
        
        q_pred = self.q + self.alpha * dq * dt
        self.q = quaternion_normalize(q_pred)
        
        # Step 2: 用加速度计修正 (EKF 更新)
        gravity_body = accel / np.linalg.norm(accel)
        gravity_nav = np.array([0.0, 0.0, 1.0])
        gravity_predicted = rotate_vector_by_quaternion(self.q, gravity_nav)
        
        # 创新
        innovation = gravity_body - gravity_predicted
        
        # 简单增益 (替代完整 EKF 更新以节省计算)
        k = 0.1
        error_angle = np.linalg.norm(innovation)
        if error_angle > 1e-6:
            error_axis = innovation / error_angle
            # 用误差轴旋转四元数
            q_error = quaternion_normalize(
                np.array([
                    np.cos(error_angle * k / 2),
                    error_axis[0] * np.sin(error_angle * k / 2),
                    error_axis[1] * np.sin(error_angle * k / 2),
                    error_axis[2] * np.sin(error_angle * k / 2)
                ])
            )
            self.q = quaternion_multiply(self.q, q_error)
        
        return self.q.copy()
    
    def get_euler_angles(self):
        """获取欧拉角"""
        q = self.q
        roll = np.arctan2(2*(q[0]*q[1] + q[2]*q[3]), 1 - 2*(q[1]**2 + q[2]**2))
        pitch = np.arcsin(np.clip(2*(q[0]*q[2] - q[3]*q[1]), -1, 1))
        yaw = np.arctan2(2*(q[0]*q[3] + q[1]*q[2]), 1 - 2*(q[2]**2 + q[3]**2))
        return roll, pitch, yaw
