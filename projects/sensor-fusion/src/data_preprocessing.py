"""
传感器数据预处理模块

本模块提供 IMU 数据的预处理功能:
- 数据滤波 (移动平均、低通滤波)
- 异常值检测与处理
- 数据对齐 (时间戳同步)
- 坐标系转换
"""

import numpy as np
from collections import deque


class MovingAverageFilter:
    """
    移动平均滤波器
    
    简单的平滑滤波器，对最近 N 个采样取平均。
    
    优点: 简单高效
    缺点: 相位延迟，对突发噪声无效
    """
    
    def __init__(self, window_size=10):
        """
        Args:
            window_size: 窗口大小 (采样点数)
        """
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)
    
    def update(self, value):
        """
        更新滤波值
        
        Args:
            value: 原始值 (标量或数组)
        
        Returns:
            滤波后的值
        """
        self.buffer.append(value)
        return np.mean(self.buffer, axis=0)
    
    def reset(self):
        """重置滤波器"""
        self.buffer.clear()


class LowPassFilter:
    """
    一阶低通滤波器 (指数移动平均)
    
    y[n] = alpha * x[n] + (1 - alpha) * y[n-1]
    
    其中 alpha = dt / (RC + dt)
    RC 是时间常数，截止频率 fc = 1 / (2*pi*RC)
    
    优点: 计算简单，内存占用小
    缺点: 不能去除接近截止频率的噪声
    """
    
    def __init__(self, cutoff_freq=10.0, sample_rate=100.0):
        """
        Args:
            cutoff_freq: 截止频率 (Hz)
            sample_rate: 采样率 (Hz)
        """
        dt = 1.0 / sample_rate
        rc = 1.0 / (2 * np.pi * cutoff_freq)
        self.alpha = dt / (rc + dt)
        self.output = None
    
    def update(self, value):
        """
        更新滤波值
        
        Args:
            value: 原始值
        
        Returns:
            滤波后的值
        """
        value = np.asarray(value, dtype=float)
        if self.output is None:
            self.output = value.copy()
        else:
            self.output = self.alpha * value + (1 - self.alpha) * self.output
        return self.output.copy()
    
    def reset(self):
        """重置滤波器"""
        self.output = None


class ButterworthHighPassFilter:
    """
    简易高通滤波器 (用于去除加速度计中的直流分量)
    
    用于分离振动分量 (高频) 和重力分量 (低频)
    
    y[n] = alpha * (y[n-1] + x[n] - x[n-1])
    """
    
    def __init__(self, cutoff_freq=10.0, sample_rate=100.0):
        dt = 1.0 / sample_rate
        rc = 1.0 / (2 * np.pi * cutoff_freq)
        self.alpha = rc / (rc + dt)
        self.prev_input = None
        self.output = None
    
    def update(self, value):
        if self.prev_input is None:
            self.prev_input = value.copy()
            self.output = np.zeros_like(value)
        
        if self.output is None:
            self.output = np.zeros_like(value)
        
        self.output = self.alpha * (self.output + value - self.prev_input)
        self.prev_input = value.copy()
        
        return self.output.copy()
    
    def reset(self):
        self.prev_input = None
        self.output = None


class OutlierDetector:
    """
    异常值检测器
    
    使用统计方法检测传感器数据中的异常值:
    - 基于标准差
    - 基于变化率
    """
    
    def __init__(self, max_std=3.0, max_rate=np.inf):
        """
        Args:
            max_std: 最大标准差倍数
            max_rate: 最大变化率 (相对于前一时刻)
        """
        self.max_std = max_std
        self.max_rate = max_rate
        self.mean = None
        self.std = None
        self.count = 0
        self.buffer = deque(maxlen=100)
    
    def update(self, value):
        """
        检测并处理异常值
        
        Args:
            value: 原始值
        
        Returns:
            (is_outlier, corrected_value) 元组
        """
        self.buffer.append(value)
        self.count += 1
        
        # 计算统计量
        if self.count > 1:
            self.mean = np.mean(self.buffer, axis=0)
            self.std = np.std(self.buffer, axis=0)
        else:
            self.mean = value.copy()
            self.std = np.ones_like(value) * 0.1
        
        # 检测异常
        deviation = np.abs(value - self.mean) / np.maximum(self.std, 1e-10)
        is_outlier = np.any(deviation > self.max_std)
        
        # 检测突变
        if self.count > 1:
            prev = self.buffer[-2]
            rate = np.abs(value - prev) / np.maximum(np.abs(prev), 1e-10)
            is_outlier = is_outlier or np.any(rate > self.max_rate)
        
        # 修正
        if is_outlier:
            corrected = self.mean.copy()
        else:
            corrected = value.copy()
        
        return is_outlier, corrected
    
    def reset(self):
        self.buffer.clear()
        self.count = 0
        self.mean = None
        self.std = None


class SensorDataProcessor:
    """
    传感器数据处理器
    
    组合多种预处理步骤:
    1. 异常值检测
    2. 低通滤波
    3. 坐标系转换
    
    使用方式:
        processor = SensorDataProcessor(cutoff_freq=10.0)
        for raw_data in sensor_stream:
            clean_data = processor.process(raw_data)
    """
    
    def __init__(self, cutoff_freq=10.0, sample_rate=100.0, 
                 max_std=3.0, window_size=5):
        """
        Args:
            cutoff_freq: 低通滤波器截止频率 (Hz)
            sample_rate: 采样率 (Hz)
            max_std: 异常值检测标准差倍数
            window_size: 移动平均窗口大小
        """
        self.accel_lp = LowPassFilter(cutoff_freq, sample_rate)
        self.gyro_lp = LowPassFilter(cutoff_freq, sample_rate)
        self.mag_lp = LowPassFilter(cutoff_freq, sample_rate)
        
        self.accel_outlier = OutlierDetector(max_std)
        self.gyro_outlier = OutlierDetector(max_std)
        self.mag_outlier = OutlierDetector(max_std)
        
        self.accel_ma = MovingAverageFilter(window_size)
        self.gyro_ma = MovingAverageFilter(window_size)
        self.mag_ma = MovingAverageFilter(window_size)
    
    def process(self, accel, gyro, mag=None):
        """
        处理传感器数据
        
        Args:
            accel: 原始加速度 [ax, ay, az]
            gyro: 原始角速度 [wx, wy, wz]
            mag: 原始磁力计 [mx, my, mz] (可选)
        
        Returns:
            (accel_clean, gyro_clean, mag_clean) 元组
        """
        # 异常值检测
        _, accel_clean = self.accel_outlier.update(accel)
        _, gyro_clean = self.gyro_outlier.update(gyro)
        
        # 低通滤波
        accel_clean = self.accel_lp.update(accel_clean)
        gyro_clean = self.gyro_lp.update(gyro_clean)
        
        if mag is not None:
            _, mag_clean = self.mag_outlier.update(mag)
            mag_clean = self.mag_lp.update(mag_clean)
        else:
            mag_clean = None
        
        return accel_clean, gyro_clean, mag_clean
    
    def get_status(self):
        """获取处理状态"""
        return {
            'accel_outlier_count': self.accel_outlier.count,
            'gyro_outlier_count': self.gyro_outlier.count,
            'mag_outlier_count': self.mag_outlier.count if hasattr(self, 'mag_outlier') else 0
        }
