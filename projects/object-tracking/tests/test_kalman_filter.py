"""
卡尔曼滤波器测试

测试内容:
- 基本初始化和状态设置
- 预测和更新步骤
- 匀速运动跟踪
- 自适应滤波
"""

import pytest
import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kalman_filter import KalmanFilter, AdaptiveKalmanFilter


class TestKalmanFilter:
    """卡尔曼滤波器测试类"""

    def test_initialization(self):
        """测试初始化"""
        kf = KalmanFilter(dt=1.0)
        assert kf is not None
        assert kf.dt == 1.0
        assert len(kf.x) == 4
        assert kf.x[0] == 0
        assert kf.x[1] == 0

    def test_set_state(self):
        """测试状态设置"""
        kf = KalmanFilter()
        kf.set_state(100, 200, 5, 3)

        assert kf.x[0] == 100
        assert kf.x[1] == 200
        assert kf.x[2] == 5
        assert kf.x[3] == 3

    def test_get_state(self):
        """测试获取状态"""
        kf = KalmanFilter()
        kf.set_state(100, 200, 5, 3)

        state = kf.get_state()
        assert len(state) == 4
        assert state[0] == 100
        assert state[1] == 200
        assert state[2] == 5
        assert state[3] == 3

    def test_get_position(self):
        """测试获取位置"""
        kf = KalmanFilter()
        kf.set_state(100, 200, 5, 3)

        pos = kf.get_position()
        assert len(pos) == 2
        assert pos[0] == 100
        assert pos[1] == 200

    def test_get_velocity(self):
        """测试获取速度"""
        kf = KalmanFilter()
        kf.set_state(100, 200, 5, 3)

        vel = kf.get_velocity()
        assert len(vel) == 2
        assert vel[0] == 5
        assert vel[1] == 3

    def test_predict(self):
        """测试预测步骤"""
        kf = KalmanFilter(dt=1.0)
        kf.set_state(100, 200, 5, 3)

        # 预测
        predicted = kf.predict()

        # 匀速运动: x' = x + vx * dt
        assert abs(predicted[0] - 105) < 1e-6
        assert abs(predicted[1] - 203) < 1e-6
        assert abs(predicted[2] - 5) < 1e-6
        assert abs(predicted[3] - 3) < 1e-6

    def test_update(self):
        """测试更新步骤"""
        kf = KalmanFilter(dt=1.0, measurement_noise=0.1)
        kf.set_state(100, 200, 5, 3)

        # 预测
        kf.predict()

        # 更新
        measurement = np.array([106.0, 204.0])
        updated = kf.update(measurement)

        # 应该接近测量值和预测值的加权平均
        assert abs(updated[0] - 106) < 1.0
        assert abs(updated[1] - 204) < 1.0

    def test_constant_velocity_tracking(self):
        """测试匀速运动跟踪"""
        kf = KalmanFilter(dt=1.0, process_noise=1e-3, measurement_noise=1.0)

        # 初始状态
        kf.set_state(100, 200, 5, 3)

        # 模拟匀速运动
        true_positions = [(100 + 5*i, 200 + 3*i) for i in range(50)]

        # 添加测量噪声
        np.random.seed(42)
        measurements = [
            np.array([x + np.random.randn() * 2, y + np.random.randn() * 2])
            for x, y in true_positions
        ]

        errors = []
        for i, (true_pos, meas) in enumerate(zip(true_positions, measurements)):
            kf.predict()
            kf.update(meas)

            estimated = kf.get_position()
            error = np.sqrt((estimated[0] - true_pos[0])**2 +
                           (estimated[1] - true_pos[1])**2)
            errors.append(error)

        # 平均误差应该小于测量噪声
        avg_error = np.mean(errors)
        assert avg_error < 3.0, f"平均误差 {avg_error} 太大"

    def test_covariance_convergence(self):
        """测试协方差收敛"""
        kf = KalmanFilter(dt=1.0, process_noise=1e-3, measurement_noise=1.0)
        kf.set_state(0, 0)

        initial_uncertainty = kf.get_position_uncertainty()

        # 多次更新后不确定性应该减小
        for _ in range(50):
            kf.predict()
            kf.update(np.array([0.0, 0.0]))

        final_uncertainty = kf.get_position_uncertainty()

        assert final_uncertainty[0] < initial_uncertainty[0]
        assert final_uncertainty[1] < initial_uncertainty[1]

    def test_reset(self):
        """测试重置"""
        kf = KalmanFilter()
        kf.set_state(100, 200, 5, 3)
        kf.predict()
        kf.update(np.array([105.0, 203.0]))

        kf.reset(50, 60, 1, 2)

        assert kf.x[0] == 50
        assert kf.x[1] == 60
        assert kf.x[2] == 1
        assert kf.x[3] == 2


class TestAdaptiveKalmanFilter:
    """自适应卡尔曼滤波器测试类"""

    def test_initialization(self):
        """测试初始化"""
        akf = AdaptiveKalmanFilter(dt=1.0, window_size=10)
        assert akf is not None
        assert akf.window_size == 10

    def test_adaptive_update(self):
        """测试自适应更新"""
        akf = AdaptiveKalmanFilter(
            dt=1.0,
            window_size=5,
            adaptation_rate=0.1
        )
        akf.set_state(100, 200, 5, 3)

        # 添加多个更新
        for i in range(20):
            akf.predict()
            measurement = np.array([100 + 5*i, 200 + 3*i])
            akf.update(measurement)

        # 应该正常工作
        pos = akf.get_position()
        assert pos[0] > 100
        assert pos[1] > 200

    def test_residual_window(self):
        """测试残差窗口"""
        akf = AdaptiveKalmanFilter(dt=1.0, window_size=5)
        akf.set_state(0, 0)

        # 添加多个更新
        for i in range(20):
            akf.predict()
            akf.update(np.array([float(i), float(i)]))

        # 残差窗口大小应该不超过window_size
        assert len(akf.residuals) <= akf.window_size


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
