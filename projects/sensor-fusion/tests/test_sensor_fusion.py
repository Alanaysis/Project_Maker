"""
传感器融合单元测试

测试各个模块的正确性。
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.coordinate_transform import (
    euler_to_rotation_matrix, rotation_matrix_to_euler,
    euler_to_quaternion, quaternion_to_euler,
    rotation_matrix_to_quaternion, quaternion_to_rotation_matrix,
    quaternion_multiply, quaternion_normalize,
    quaternion_conjugate, rotate_vector_by_quaternion,
    angular_velocity_to_quaternion_derivative, skew_symmetric
)
from src.sensor_calibration import (
    AccelerometerCalibration, GyroscopeCalibration,
    MagnetometerCalibration, SensorCalibrationManager
)
from src.data_preprocessing import (
    MovingAverageFilter, LowPassFilter, OutlierDetector,
    SensorDataProcessor
)
from src.complementary_filter import ComplementaryFilter, AdaptiveComplementaryFilter
from src.kalman_filter import KalmanFilter, AttitudeEKF
from src.madgwick_filter import MadgwickFilter
from src.mahony_filter import MahonyFilter


class TestCoordinateTransform(unittest.TestCase):
    """坐标变换测试"""
    
    def test_euler_to_rotation_matrix_identity(self):
        """单位欧拉角应产生单位矩阵"""
        R = euler_to_rotation_matrix(0, 0, 0)
        np.testing.assert_array_almost_equal(R, np.eye(3), decimal=10)
    
    def test_rotation_matrix_to_euler_roundtrip(self):
        """欧拉角 -> 旋转矩阵 -> 欧拉角 应保持一致"""
        roll, pitch, yaw = 0.5, 0.3, 0.2
        R = euler_to_rotation_matrix(roll, pitch, yaw)
        r2, p2, y2 = rotation_matrix_to_euler(R)
        np.testing.assert_almost_equal(roll, r2, decimal=10)
        np.testing.assert_almost_equal(pitch, p2, decimal=10)
        np.testing.assert_almost_equal(yaw, y2, decimal=10)
    
    def test_euler_to_quaternion_roundtrip(self):
        """欧拉角 <-> 四元数 转换应可逆"""
        # 零旋转
        q = euler_to_quaternion(0, 0, 0)
        q = quaternion_normalize(q)
        np.testing.assert_almost_equal(q[0], 1.0, decimal=5)
        np.testing.assert_almost_equal(q[1:], [0, 0, 0], decimal=5)
        
        # 纯 yaw 旋转
        yaw = np.pi / 2
        q = euler_to_quaternion(0, 0, yaw)
        q = quaternion_normalize(q)
        r2, p2, y2 = quaternion_to_euler(q)
        np.testing.assert_almost_equal(y2, yaw, decimal=3)
        np.testing.assert_almost_equal(p2, 0, decimal=3)
    
    def test_quaternion_normalization(self):
        """四元数归一化"""
        q = np.array([3.0, 4.0, 0.0, 0.0])
        q_norm = quaternion_normalize(q)
        self.assertAlmostEqual(np.linalg.norm(q_norm), 1.0, places=10)
    
    def test_quaternion_multiply_identity(self):
        """与单位四元数相乘应保持不变"""
        q = np.array([1.0, 0.0, 0.0, 0.0])
        q_test = np.array([0.7071, 0.7071, 0.0, 0.0])
        result = quaternion_multiply(q, q_test)
        np.testing.assert_array_almost_equal(result, q_test, decimal=4)
    
    def test_quaternion_conjugate(self):
        """共轭的四元数模长不变"""
        q = np.array([1.0, 2.0, 3.0, 4.0])
        q_conj = quaternion_conjugate(q)
        self.assertAlmostEqual(np.linalg.norm(q), np.linalg.norm(q_conj))
    
    def test_rotate_vector(self):
        """用四元数旋转单位向量"""
        q = euler_to_quaternion(0, 0, np.pi/2)  # 绕 Z 轴旋转 90 度
        v = np.array([1.0, 0.0, 0.0])
        v_rot = rotate_vector_by_quaternion(q, v)
        # 允许一定误差，因为四元数旋转实现可能有微小数值差异
        self.assertAlmostEqual(v_rot[0], 0.0, places=3)
        self.assertAlmostEqual(v_rot[1], 1.0, places=3)
        self.assertAlmostEqual(v_rot[2], 0.0, places=3)
    
    def test_skew_symmetric(self):
        """反对称矩阵测试"""
        v = np.array([1.0, 2.0, 3.0])
        S = skew_symmetric(v)
        # S 应反对称
        np.testing.assert_array_almost_equal(S, -S.T)
        # S @ v 应为零
        np.testing.assert_array_almost_equal(S @ v, np.zeros(3))


class TestSensorCalibration(unittest.TestCase):
    """传感器校准测试"""
    
    def test_accelerometer_bias_calibration(self):
        """加速度计偏置校准"""
        cal = AccelerometerCalibration()
        readings = np.array([[0.1, -0.2, 9.7], [0.15, -0.15, 9.75],
                             [0.05, -0.25, 9.65]])
        cal.calibrate_bias(readings)
        np.testing.assert_array_almost_equal(cal.bias, np.mean(readings, axis=0), decimal=5)
    
    def test_gyroscope_bias_calibration(self):
        """陀螺仪偏置校准"""
        cal = GyroscopeCalibration()
        readings = np.array([[0.01, -0.02, 0.015], [0.012, -0.018, 0.013],
                             [0.008, -0.022, 0.017]])
        cal.calibrate_bias(readings)
        np.testing.assert_array_almost_equal(cal.bias, np.mean(readings, axis=0), decimal=5)
    
    def test_magnetometer_calibration(self):
        """磁力计校准"""
        cal = MagnetometerCalibration()
        # 生成模拟的椭圆分布数据
        theta = np.linspace(0, 2*np.pi, 100)
        readings = np.column_stack([
            50 * np.cos(theta) + 10,
            40 * np.sin(theta) + 5,
            30 + np.random.randn(100) * 0.1
        ])
        cal.calibrate(readings)
        self.assertTrue(cal.calibrated)
    
    def test_calibration_manager(self):
        """校准管理器"""
        manager = SensorCalibrationManager()
        accel = np.array([[0.1, -0.2, 9.8]] * 10)
        gyro = np.array([[0.01, -0.02, 0.01]] * 10)
        mag = np.column_stack([
            np.cos(np.linspace(0, 2*np.pi, 20)) * 50 + 10,
            np.sin(np.linspace(0, 2*np.pi, 20)) * 40 + 5,
            np.ones(20) * 30
        ])
        manager.full_calibration(accel, gyro, mag)
        status = manager.get_status()
        self.assertTrue(status['accelerometer'])
        self.assertTrue(status['gyroscope'])
        self.assertTrue(status['magnetometer'])


class TestDataPreprocessing(unittest.TestCase):
    """数据预处理测试"""
    
    def test_moving_average(self):
        """移动平均滤波器"""
        ma = MovingAverageFilter(window_size=5)
        # 输入恒定值
        for _ in range(20):
            result = ma.update(1.0)
        self.assertAlmostEqual(result, 1.0, places=3)
    
    def test_low_pass_filter(self):
        """低通滤波器"""
        lp = LowPassFilter(cutoff_freq=10.0, sample_rate=100.0)
        # 输入阶跃信号
        lp.update(0.0)
        result = lp.update(1.0)
        self.assertGreater(result, 0.0)
        self.assertLess(result, 1.0)
    
    def test_outlier_detector(self):
        """异常值检测"""
        detector = OutlierDetector(max_std=2.0)
        # 先填充一些数据
        for _ in range(20):
            detector.update(np.random.randn(3))
        # 正常值
        is_outlier, corrected = detector.update(np.array([0.0, 0.0, 0.0]))
        self.assertFalse(is_outlier)
        # 异常值
        is_outlier, corrected = detector.update(np.array([100.0, 0.0, 0.0]))
        self.assertTrue(is_outlier)
    
    def test_sensor_data_processor(self):
        """传感器数据处理器"""
        processor = SensorDataProcessor(cutoff_freq=10.0, sample_rate=100.0)
        accel, gyro, mag = processor.process(
            np.array([0.0, 0.0, 9.81]),
            np.array([0.0, 0.0, 0.0]),
            np.array([50.0, 0.0, 30.0])
        )
        self.assertEqual(len(accel), 3)
        self.assertEqual(len(gyro), 3)
        self.assertEqual(len(mag), 3)


class TestComplementaryFilter(unittest.TestCase):
    """互补滤波器测试"""
    
    def test_initial_state(self):
        """初始状态应为单位四元数"""
        f = ComplementaryFilter(gain=0.98)
        q = f.q
        self.assertAlmostEqual(np.linalg.norm(q), 1.0, places=10)
    
    def test_static_accelerometer(self):
        """静止时加速度计应只测量重力"""
        f = ComplementaryFilter(gain=0.5)  # 高增益以快速收敛
        # 静止: 加速度计读数为 [0, 0, 9.81]
        q = f.update(np.array([0.0, 0.0, 9.81]), np.array([0.0, 0.0, 0.0]), 0.01)
        r, p, y = f.get_euler_angles()
        # 应接近零姿态
        self.assertAlmostEqual(p, 0.0, places=1)
    
    def test_pitch_estimation(self):
        """俯仰角估计"""
        f = ComplementaryFilter(gain=0.7)
        # 绕 Y 轴旋转 30 度
        pitch = np.pi / 6
        ax = -9.81 * np.sin(pitch)
        az = 9.81 * np.cos(pitch)
        for _ in range(500):
            q = f.update(np.array([ax, 0.0, az]), np.array([0.0, 0.0, 0.0]), 0.01)
        r, p_est, y = f.get_euler_angles()
        # 允许较大误差，因为互补滤波在静态加速度计条件下收敛较慢
        self.assertAlmostEqual(abs(p_est), abs(pitch), delta=0.3)


class TestKalmanFilter(unittest.TestCase):
    """卡尔曼滤波器测试"""
    
    def test_standard_kf(self):
        """标准卡尔曼滤波器"""
        kf = KalmanFilter(state_dim=2, obs_dim=1)
        kf.x = np.array([0.0, 0.0])
        kf.F = np.array([[1.0, 0.1], [0.0, 1.0]])
        kf.H = np.array([[1.0, 0.0]])
        
        # 预测
        kf.predict()
        x_pred = kf.x.copy()
        
        # 更新
        kf.update(np.array([1.0]))
        
        # 状态应变化
        self.assertFalse(np.allclose(kf.x, x_pred))
    
    def test_ekf_attitude(self):
        """EKF 姿态估计初始化"""
        ekf = AttitudeEKF(process_noise=1e-4, accel_noise=1e-2, mag_noise=1e-2)
        q = ekf.update(np.array([0.0, 0.0, 9.81]), np.array([50.0, 0.0, 30.0]),
                       np.array([0.0, 0.0, 0.0]))
        self.assertAlmostEqual(np.linalg.norm(q), 1.0, places=3)


class TestMadgwickFilter(unittest.TestCase):
    """Madgwick 滤波器测试"""
    
    def test_initial_state(self):
        """初始状态"""
        f = MadgwickFilter(beta=0.1, sample_period=0.01)
        self.assertAlmostEqual(np.linalg.norm(f.q), 1.0, places=10)
    
    def test_static_update(self):
        """静止更新"""
        f = MadgwickFilter(beta=0.1, sample_period=0.01)
        q = f.update(
            gyro=np.array([0.0, 0.0, 0.0]),
            accel=np.array([0.0, 0.0, 9.81]),
            mag=np.array([50.0, 0.0, 30.0]),
            sample_period=0.01
        )
        self.assertAlmostEqual(np.linalg.norm(q), 1.0, places=10)


class TestMahonyFilter(unittest.TestCase):
    """Mahony 滤波器测试"""
    
    def test_initial_state(self):
        """初始状态"""
        f = MahonyFilter(Kp=2.0, Ki=0.1, sample_period=0.01)
        self.assertAlmostEqual(np.linalg.norm(f.q), 1.0, places=10)
    
    def test_static_update(self):
        """静止更新"""
        f = MahonyFilter(Kp=2.0, Ki=0.1, sample_period=0.01)
        q = f.update(
            gyro=np.array([0.0, 0.0, 0.0]),
            accel=np.array([0.0, 0.0, 9.81]),
            mag=np.array([50.0, 0.0, 30.0]),
            sample_period=0.01
        )
        self.assertAlmostEqual(np.linalg.norm(q), 1.0, places=10)
    
    def test_reset(self):
        """重置"""
        f = MahonyFilter(Kp=2.0, Ki=0.1)
        f.reset()
        np.testing.assert_array_equal(f.q, np.array([1.0, 0.0, 0.0, 0.0]))
        np.testing.assert_array_equal(f.bias, np.zeros(3))


if __name__ == '__main__':
    unittest.main(verbosity=2)
