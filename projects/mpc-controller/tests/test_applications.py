"""
应用测试 - 温度控制和轨迹跟踪
"""

import pytest
import numpy as np
from src.applications import (
    ThermalPlant,
    DubinsCar,
    TemperatureController,
    TemperatureControllerConfig,
    TrajectoryTracker,
    TrajectoryTrackerConfig,
    create_temperature_controller,
    create_trajectory_tracker,
)


class TestThermalPlant:
    """热力学系统测试"""

    def test_initialization(self):
        """测试初始化"""
        plant = ThermalPlant()
        assert plant.n_states == 1
        assert plant.n_inputs == 1
        assert plant.n_outputs == 1

    def test_dynamics(self):
        """测试动力学"""
        plant = ThermalPlant(T_env=293.15)

        # 初始温度 = 环境温度，无加热
        x = np.array([293.15])
        u = np.array([0.0])
        x_next = plant.step(x, u, dt=1.0)

        # 温度应该保持不变
        np.testing.assert_almost_equal(x_next[0], 293.15, decimal=2)

    def test_heating(self):
        """测试加热"""
        plant = ThermalPlant(T_env=293.15)

        # 初始温度 = 环境温度，全功率加热
        x = np.array([293.15])
        u = np.array([1.0])

        # 多步加热
        for _ in range(100):
            x = plant.step(x, u, dt=1.0)

        # 温度应该升高
        assert x[0] > 293.15

    def test_steady_state(self):
        """测试稳态"""
        plant = ThermalPlant(T_env=293.15)

        # 计算稳态工作点
        T_set = 353.15  # 80°C
        state_op, u_op = plant.get_operating_point(T_set)

        # 在工作点处，温度应该保持稳定
        x = state_op.copy()
        for _ in range(100):
            x = plant.step(x, u_op, dt=1.0)

        np.testing.assert_almost_equal(x[0], T_set, decimal=1)

    def test_output(self):
        """测试输出"""
        plant = ThermalPlant()
        x = np.array([350.0])
        y = plant.output(x)
        np.testing.assert_array_almost_equal(y, [350.0])

    def test_operating_point(self):
        """测试工作点计算"""
        plant = ThermalPlant(T_env=293.15)

        T_set = 353.15
        state_op, u_op = plant.get_operating_point(T_set)

        assert state_op[0] == T_set
        assert 0 <= u_op[0] <= 1


class TestDubinsCar:
    """Dubins 车模型测试"""

    def test_initialization(self):
        """测试初始化"""
        car = DubinsCar()
        assert car.n_states == 3
        assert car.n_inputs == 2
        assert car.n_outputs == 2

    def test_straight_line(self):
        """测试直线运动"""
        car = DubinsCar()

        # 初始状态: x=0, y=0, theta=0
        x = np.array([0.0, 0.0, 0.0])
        # 输入: v=1, omega=0 (直行)
        u = np.array([1.0, 0.0])

        # 多步前进
        for _ in range(10):
            x = car.step(x, u, dt=0.1)

        # 应该沿 x 轴前进
        assert x[0] > 0
        np.testing.assert_almost_equal(x[1], 0.0, decimal=5)
        np.testing.assert_almost_equal(x[2], 0.0, decimal=5)

    def test_circular_motion(self):
        """测试圆周运动"""
        car = DubinsCar()

        # 初始状态
        x = np.array([0.0, 0.0, 0.0])
        # 输入: v=1, omega=1 (转弯)
        u = np.array([1.0, 1.0])

        # 运行一段
        for _ in range(63):  # 约一圈 (2*pi/1.0 ≈ 6.28s)
            x = car.step(x, u, dt=0.1)

        # 应该接近回到原点附近
        assert abs(x[0]) < 2.0
        assert abs(x[1]) < 2.0

    def test_output(self):
        """测试输出"""
        car = DubinsCar()
        x = np.array([1.0, 2.0, 0.5])
        y = car.output(x)
        np.testing.assert_array_almost_equal(y, [1.0, 2.0])


class TestTemperatureController:
    """温度控制器测试"""

    def test_initialization(self):
        """测试初始化"""
        controller = TemperatureController()
        assert controller.config.T_setpoint == 353.15

    def test_compute_control(self):
        """测试控制计算"""
        controller = TemperatureController()

        T_current = 293.15  # 20°C
        result = controller.compute_control(T_current)

        # 应该给出正的加热功率
        assert result.u_optimal[0] > 0

    def test_at_setpoint(self):
        """测试在设定点处"""
        config = TemperatureControllerConfig(T_setpoint=353.15)
        controller = TemperatureController(config)

        # 在设定点处
        result = controller.compute_control(353.15)

        # 控制输入应该很小
        assert abs(result.u_optimal[0]) < 0.5

    def test_custom_config(self):
        """测试自定义配置"""
        config = TemperatureControllerConfig(
            T_setpoint=373.15,  # 100°C
            T_initial=293.15,
            prediction_horizon=15,
            control_horizon=8
        )
        controller = TemperatureController(config)

        result = controller.compute_control(293.15)
        assert result.u_optimal[0] > 0

    def test_reset(self):
        """测试重置"""
        controller = TemperatureController()

        controller.compute_control(293.15)
        controller.reset()

        assert len(controller.controller.history['states']) == 0


class TestTrajectoryTracker:
    """轨迹跟踪器测试"""

    def test_initialization(self):
        """测试初始化"""
        tracker = TrajectoryTracker()
        assert tracker.config.trajectory_type == "circle"

    def test_get_reference_circle(self):
        """测试圆形参考轨迹"""
        config = TrajectoryTrackerConfig(
            trajectory_type="circle",
            radius=5.0,
            speed=1.0,
            center_x=0.0,
            center_y=5.0
        )
        tracker = TrajectoryTracker(config)

        ref = tracker.get_reference_trajectory(0.0)
        assert len(ref) == 2

        # 在 t=0 时，应该在圆的最右端
        np.testing.assert_almost_equal(ref[0], 5.0)
        np.testing.assert_almost_equal(ref[1], 5.0)

    def test_get_reference_figure8(self):
        """测试 8 字形参考轨迹"""
        config = TrajectoryTrackerConfig(
            trajectory_type="figure8",
            radius=5.0,
            speed=1.0
        )
        tracker = TrajectoryTracker(config)

        ref = tracker.get_reference_trajectory(0.0)
        assert len(ref) == 2

    def test_get_reference_line(self):
        """测试直线参考轨迹"""
        config = TrajectoryTrackerConfig(
            trajectory_type="line",
            speed=1.0,
            center_y=5.0
        )
        tracker = TrajectoryTracker(config)

        ref_0 = tracker.get_reference_trajectory(0.0)
        ref_1 = tracker.get_reference_trajectory(1.0)

        # x 应该增长
        assert ref_1[0] > ref_0[0]
        # y 应该保持不变
        np.testing.assert_almost_equal(ref_0[1], 5.0)

    def test_get_reference_sequence(self):
        """测试参考序列"""
        tracker = TrajectoryTracker()

        ref_seq = tracker.get_reference_sequence(0.0, 10)
        assert ref_seq.shape == (10, 2)

    def test_compute_control(self):
        """测试控制计算"""
        tracker = TrajectoryTracker()

        state = np.array([0.0, 0.0, 0.0])
        result = tracker.compute_control(state, 0.0)

        assert result.u_optimal.shape == (2,)
        assert len(result.u_sequence) > 0

    def test_custom_config(self):
        """测试自定义配置"""
        config = TrajectoryTrackerConfig(
            trajectory_type="circle",
            radius=3.0,
            speed=0.5,
            prediction_horizon=10,
            control_horizon=5
        )
        tracker = TrajectoryTracker(config)

        state = np.array([0.0, 0.0, 0.0])
        result = tracker.compute_control(state, 0.0)

        assert result.u_optimal.shape == (2,)

    def test_reset(self):
        """测试重置"""
        tracker = TrajectoryTracker()

        state = np.array([0.0, 0.0, 0.0])
        tracker.compute_control(state, 0.0)

        tracker.reset()
        assert len(tracker.controller.history['states']) == 0


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_create_temperature_controller(self):
        """测试创建温度控制器"""
        controller = create_temperature_controller(
            T_setpoint=373.15,
            T_initial=293.15
        )

        assert isinstance(controller, TemperatureController)
        assert controller.config.T_setpoint == 373.15

    def test_create_trajectory_tracker(self):
        """测试创建轨迹跟踪器"""
        tracker = create_trajectory_tracker(
            trajectory_type="circle",
            radius=10.0
        )

        assert isinstance(tracker, TrajectoryTracker)
        assert tracker.config.radius == 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
