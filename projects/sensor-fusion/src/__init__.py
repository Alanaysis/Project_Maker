"""
传感器融合 (Sensor Fusion) 学习项目

实现 IMU/加速度计传感器融合算法的学习项目。

模块:
    - coordinate_transform: 坐标变换 (欧拉角、四元数、旋转矩阵)
    - sensor_calibration: 传感器校准 (加速度计、陀螺仪、磁力计)
    - data_preprocessing: 数据预处理 (滤波、异常值检测)
    - complementary_filter: 互补滤波器
    - kalman_filter: 卡尔曼滤波器 (含扩展卡尔曼滤波)
    - madgwick_filter: Madgwick 滤波器
    - mahony_filter: Mahony 滤波器
"""

from .coordinate_transform import *
from .sensor_calibration import *
from .data_preprocessing import *
from .complementary_filter import *
from .kalman_filter import *
from .madgwick_filter import *
from .mahony_filter import *

__all__ = [
    'coordinate_transform',
    'sensor_calibration',
    'data_preprocessing',
    'complementary_filter',
    'kalman_filter',
    'madgwick_filter',
    'mahony_filter',
]

__version__ = '1.0.0'
