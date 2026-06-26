"""
传感器校准模块

本模块提供 IMU 传感器的校准功能：
- 加速度计校准 (偏置、比例因子、非正交性)
- 陀螺仪校准 (零偏、比例因子、温度补偿)
- 磁力计校准 (偏置、椭圆拟合)
- 传感器融合校准参数管理
"""

import numpy as np


class AccelerometerCalibration:
    """
    加速度计校准器
    
    加速度计校准需要补偿:
    1. 零偏 (bias): 静止时的非零输出
    2. 比例因子 (scale): 实际灵敏度与标称值的偏差
    3. 非正交性 (misalignment): 轴之间不完全垂直
    
    校准方法:
    - 静止校准: 利用重力方向
    - 多位置校准: 6 面静止法
    """
    
    def __init__(self):
        self.bias = np.array([0.0, 0.0, 0.0])
        self.scale = np.array([1.0, 1.0, 1.0])
        self.misalignment = np.eye(3)
        self.calibrated = False
    
    def calibrate_bias(self, readings, gravity_magnitude=9.81):
        """
        通过静止读数估计零偏
        
        原理: 静止时加速度计应只测量重力。
        如果已知重力方向，可以估计偏置。
        
        Args:
            readings: N x 3 的加速度读数矩阵 (m/s^2)
            gravity_magnitude: 重力加速度大小 (m/s^2)
        """
        # 零偏 = 读数的均值 (静止时)
        self.bias = np.mean(readings, axis=0)
        self.calibrated = True
        print(f"[加速度计] 零偏估计: {self.bias}")
    
    def calibrate_from_static_positions(self, position_readings, gravity_directions):
        """
        通过 6 面静止法校准加速度计
        
        将 IMU 放置在 6 个正交方向，利用重力矢量校准
        
        Args:
            position_readings: list of N x 3 读数矩阵
            gravity_directions: list of 3 维重力方向向量 (已知)
        """
        all_readings = np.vstack(position_readings)
        
        # 估计偏置
        self.bias = np.mean(all_readings, axis=0)
        
        # 估计比例因子
        corrected = all_readings - self.bias
        magnitudes = np.linalg.norm(corrected, axis=1)
        expected_mag = gravity_directions[0][0]  # 假设第一个方向重力大小已知
        
        if expected_mag > 0:
            self.scale = magnitudes / expected_mag
            self.scale = np.clip(self.scale, 0.9, 1.1)  # 限制范围
        
        self.calibrated = True
        print(f"[加速度计] 6面校准完成: bias={self.bias}, scale={self.scale}")
    
    def calibrate(self, readings):
        """
        综合校准: 估计偏置和比例因子
        
        Args:
            readings: N x 3 的加速度读数
        """
        self.calibrate_bias(readings)
        
        # 估计比例因子
        corrected = readings - self.bias
        magnitudes = np.linalg.norm(corrected, axis=1)
        # 假设读数围绕重力大小分布
        median_mag = np.median(magnitudes)
        if median_mag > 0:
            self.scale = magnitudes / median_mag
            self.scale = np.mean(self.scale)  # 取平均比例因子
            self.scale = np.ones(3) * np.clip(self.scale, 0.9, 1.1)
        
        self.calibrated = True
        print(f"[加速度计] 校准完成: bias={self.bias}, scale={self.scale}")
    
    def correct(self, raw_reading):
        """
        对原始读数进行校准补偿
        
        reading_calibrated = (reading_raw - bias) / scale
        
        Args:
            raw_reading: 原始加速度读数 [ax, ay, az]
        
        Returns:
            校准后的读数
        """
        corrected = (raw_reading - self.bias) / self.scale
        return corrected
    
    def get_calibration_matrix(self):
        """
        获取校准变换矩阵
        
        Returns:
            (scale_matrix, bias_vector)
        """
        scale_matrix = np.diag(1.0 / self.scale)
        return scale_matrix, self.bias


class GyroscopeCalibration:
    """
    陀螺仪校准器
    
    陀螺仪校准主要补偿:
    1. 零偏 (zero bias): 静止时的角速度输出
    2. 比例因子 (scale factor): 灵敏度偏差
    3. 温度漂移 (temperature drift): 随温度变化的偏置漂移
    
    零偏校准是最关键的步骤。
    """
    
    def __init__(self):
        self.bias = np.array([0.0, 0.0, 0.0])
        self.scale = np.array([1.0, 1.0, 1.0])
        self.temperature_coeff = np.array([0.0, 0.0, 0.0])
        self.calibrated = False
        self.bias_history = []
    
    def calibrate_bias(self, readings, duration=1.0, sample_rate=100):
        """
        通过静止读数估计零偏
        
        原理: 陀螺仪静止时输出应为零。
        取静止期间的均值作为零偏估计。
        
        Args:
            readings: N x 3 的角速度读数 (rad/s)
            duration: 校准持续时间 (秒)，用于打印信息
            sample_rate: 采样率 (Hz)
        """
        n_samples = len(readings)
        self.bias = np.mean(readings, axis=0)
        self.bias_std = np.std(readings, axis=0)  # 噪声水平估计
        self.calibrated = True
        
        print(f"[陀螺仪] 零偏校准完成:")
        print(f"  偏置: {self.bias}")
        print(f"  噪声标准差: {self.bias_std}")
        arv = self.bias_std * np.sqrt(duration)
        print(f"  等效角度随机游走: {[f'{v:.2e}' for v in arv]} rad/sqrt(s)")
    
    def calibrate(self, readings):
        """
        综合校准陀螺仪
        
        Args:
            readings: N x 3 的角速度读数
        """
        self.calibrate_bias(readings)
        self.calibrated = True
        print(f"[陀螺仪] 校准完成")
    
    def correct(self, raw_reading, temperature=None):
        """
        对原始读数进行校准补偿
        
        Args:
            raw_reading: 原始角速度读数 [wx, wy, wz] (rad/s)
            temperature: 温度读数 (可选，用于温度补偿)
        
        Returns:
            校准后的角速度
        """
        corrected = raw_reading - self.bias
        
        # 温度补偿
        if temperature is not None and hasattr(self, 'temperature_coeff'):
            corrected -= self.temperature_coeff * (temperature - 25.0)  # 25度为参考
        
        corrected /= self.scale
        return corrected
    
    def update_bias_estimate(self, new_reading, alpha=0.01):
        """
        在线更新零偏估计 (指数移动平均)
        
        适用于陀螺仪偏置缓慢漂移的场景。
        
        Args:
            new_reading: 新的角速度读数 (假设静止)
            alpha: 更新率 (0 < alpha <= 1)
        """
        self.bias = (1 - alpha) * self.bias + alpha * new_reading
        self.bias_history.append(self.bias.copy())
    
    def get_noise_estimate(self):
        """
        获取噪声估计
        
        Returns:
            (bias_stability, angle_random_walk) 元组
        """
        if not hasattr(self, 'bias_std'):
            return None, None
        
        # 偏置稳定性 (1小时)
        bias_stability = self.bias_std * np.sqrt(3600)
        # 角度随机游走
        arv = self.bias_std / np.sqrt(1.0)  # 假设 1Hz 采样
        
        return bias_stability, arv


class MagnetometerCalibration:
    """
    磁力计校准器
    
    磁力计校准主要补偿:
    1. 硬铁偏置 (hard iron): 永久磁铁效应，导致偏移
    2. 软铁效应 (soft iron): 周围铁磁材料导致的椭圆畸变
    3. 比例因子和非正交性
    
    校准方法: 椭圆拟合 (将椭球拟合到数据)
    """
    
    def __init__(self):
        self.hard_iron_bias = np.array([0.0, 0.0, 0.0])
        self.soft_iron_matrix = np.eye(3)
        self.calibrated = False
    
    def calibrate(self, readings):
        """
        通过椭圆拟合校准磁力计
        
        原理: 旋转磁力计时，读数应落在球面上。
        实际数据形成椭球，通过拟合恢复球面。
        
        Args:
            readings: N x 3 的磁力计读数
        """
        if len(readings) < 6:
            raise ValueError("至少需要 6 个不同方向的读数")
        
        # 硬铁偏置: 数据中心的偏移
        center = np.mean(readings, axis=0)
        self.hard_iron_bias = center
        
        # 软铁效应: 协方差矩阵分析
        centered = readings - center
        cov = np.cov(centered.T)
        
        # 特征值分解
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        
        # 软铁矩阵: 将椭球映射到球
        # D^(-1/2) * V^T 将椭球映射到单位球
        D_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(eigenvalues, 1e-10)))
        self.soft_iron_matrix = D_inv_sqrt @ eigenvectors.T
        
        self.calibrated = True
        print(f"[磁力计] 校准完成:")
        print(f"  硬铁偏置: {self.hard_iron_bias}")
        print(f"  软铁矩阵:\n{self.soft_iron_matrix}")
    
    def correct(self, raw_reading):
        """
        对原始读数进行校准补偿
        
        Args:
            raw_reading: 原始磁力计读数 [mx, my, mz]
        
        Returns:
            校准后的磁力计读数
        """
        # 先补偿软铁效应
        corrected = self.soft_iron_matrix @ raw_reading
        # 再补偿硬铁偏置
        corrected -= self.hard_iron_bias
        return corrected
    
    def get_hard_iron_correction(self):
        """
        获取硬铁补偿向量
        
        Returns:
            硬铁偏置向量
        """
        return self.hard_iron_bias


class SensorCalibrationManager:
    """
    传感器校准管理器
    
    统一管理加速度计、陀螺仪、磁力计的校准参数。
    提供一键校准和综合校准功能。
    """
    
    def __init__(self):
        self.accel_cal = AccelerometerCalibration()
        self.gyro_cal = GyroscopeCalibration()
        self.mag_cal = MagnetometerCalibration()
    
    def full_calibration(self, accel_data=None, gyro_data=None, mag_data=None):
        """
        执行完整校准流程
        
        Args:
            accel_data: 加速度计静止数据 (N x 3)
            gyro_data: 陀螺仪静止数据 (N x 3)
            mag_data: 磁力计旋转数据 (N x 3)
        """
        if accel_data is not None:
            self.accel_cal.calibrate(accel_data)
        
        if gyro_data is not None:
            self.gyro_cal.calibrate(gyro_data)
        
        if mag_data is not None:
            self.mag_cal.calibrate(mag_data)
        
        print("[校准管理器] 完整校准完成")
    
    def correct_all(self, accel_raw, gyro_raw, mag_raw):
        """
        对所有传感器原始数据进行校准
        
        Args:
            accel_raw: 原始加速度 [ax, ay, az]
            gyro_raw: 原始角速度 [wx, wy, wz]
            mag_raw: 原始磁力计 [mx, my, mz]
        
        Returns:
            (accel_corrected, gyro_corrected, mag_corrected)
        """
        accel_corr = self.accel_cal.correct(accel_raw)
        gyro_corr = self.gyro_cal.correct(gyro_raw)
        mag_corr = self.mag_cal.correct(mag_raw)
        
        return accel_corr, gyro_corr, mag_corr
    
    def get_status(self):
        """
        获取校准状态
        
        Returns:
            校准状态字典
        """
        return {
            'accelerometer': self.accel_cal.calibrated,
            'gyroscope': self.gyro_cal.calibrated,
            'magnetometer': self.mag_cal.calibrated,
            'accel_bias': self.accel_cal.bias.tolist(),
            'gyro_bias': self.gyro_cal.bias.tolist(),
            'mag_hard_iron': self.mag_cal.hard_iron_bias.tolist()
        }
