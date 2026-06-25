"""
自校正控制器测试

测试自校正控制器 (STR) 的核心功能。
"""

import pytest
import numpy as np
from src.adaptive_controller import SelfTuningController
from src.plant_model import create_first_order_plant


class TestSelfTuningController:
    """自校正控制器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.controller = SelfTuningController(
            n_params=2,
            desired_poles=[0.5],
            estimation_method="rls",
            forgetting_factor=0.98,
            adaptation_gain=0.1,
        )

    def test_initialization(self):
        """测试初始化"""
        assert self.controller.n_params == 2
        assert len(self.controller.desired_poles) == 1
        assert self.controller.desired_poles[0] == 0.5
        assert len(self.controller.estimated_params) == 2
        assert len(self.controller.controller_gains) == 2

    def test_compute_control(self):
        """测试控制信号计算"""
        u = self.controller.compute_control(
            reference_input=1.0,
            plant_output=0.5,
            dt=0.01,
        )

        assert isinstance(u, float)
        assert len(self.controller.history) == 1

    def test_parameter_estimation(self):
        """测试参数估计"""
        # 创建被控对象
        plant = create_first_order_plant(time_constant=1.0, gain=1.0)

        # 运行仿真让参数估计收敛
        for _ in range(500):
            y = plant.get_output()
            phi = np.array([1.0, -y])
            u = self.controller.compute_control(1.0, y, 0.01, phi)
            plant.update(u, 0.01)

        # 检查参数估计不为零
        assert not np.all(self.controller.estimated_params == 0)

    def test_controller_gains_update(self):
        """测试控制器增益更新"""
        # 运行几步
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        # 检查增益已更新
        assert not np.all(self.controller.controller_gains == 0)

    def test_estimation_convergence(self):
        """测试参数估计收敛"""
        # 创建被控对象
        plant = create_first_order_plant(time_constant=1.0, gain=1.0)

        # 运行长时间仿真
        for _ in range(1000):
            y = plant.get_output()
            phi = np.array([1.0, -y])
            u = self.controller.compute_control(1.0, y, 0.01, phi)
            plant.update(u, 0.01)

        # 检查估计误差在减小
        _, errors = self.controller.get_estimation_errors()
        early_error = np.mean(np.abs(errors[:100]))
        late_error = np.mean(np.abs(errors[-100:]))

        # 后期误差应该更小或相近
        assert late_error <= early_error * 2  # 允许一定波动

    def test_history_recording(self):
        """测试历史记录"""
        n_steps = 50
        for i in range(n_steps):
            self.controller.compute_control(1.0, 0.5 * i / n_steps, 0.01)

        assert len(self.controller.history) == n_steps

        # 检查历史记录内容
        last_record = self.controller.history[-1]
        assert "time" in last_record
        assert "reference" in last_record
        assert "output" in last_record
        assert "control" in last_record
        assert "estimation_error" in last_record
        assert "estimated_params" in last_record
        assert "controller_gains" in last_record

    def test_get_parameter_estimates(self):
        """测试获取参数估计历史"""
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        times, params = self.controller.get_parameter_estimates()
        assert len(times) == 100
        assert params.shape == (100, 2)

    def test_get_controller_gains(self):
        """测试获取控制器增益历史"""
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        times, gains = self.controller.get_controller_gains()
        assert len(times) == 100
        assert gains.shape == (100, 2)

    def test_get_estimation_errors(self):
        """测试获取估计误差历史"""
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        times, errors = self.controller.get_estimation_errors()
        assert len(times) == 100
        assert len(errors) == 100

    def test_reset(self):
        """测试重置功能"""
        # 运行几步
        for _ in range(10):
            self.controller.compute_control(1.0, 0.5, 0.01)

        # 重置
        self.controller.reset()

        # 验证状态已重置
        assert len(self.controller.history) == 0
        assert np.all(self.controller.estimated_params == 0)
        assert np.all(self.controller.controller_gains == 0)
        assert self.controller._time == 0.0

    def test_different_estimation_methods(self):
        """测试不同的参数估计方法"""
        methods = ["rls", "gradient", "forgetting_factor"]

        for method in methods:
            controller = SelfTuningController(
                n_params=2,
                estimation_method=method,
                adaptation_gain=0.1,
            )

            # 运行几步
            for _ in range(50):
                controller.compute_control(1.0, 0.5, 0.01)

            # 验证正常工作
            assert len(controller.history) == 50

    def test_custom_regression_vector(self):
        """测试自定义回归向量"""
        for _ in range(100):
            phi = np.array([1.0, -0.5])
            self.controller.compute_control(1.0, 0.5, 0.01, phi)

        assert len(self.controller.history) == 100

    def test_pole_placement(self):
        """测试极点配置"""
        # 设置已知参数
        self.controller.estimated_params = np.array([-1.0, 2.0])
        self.controller._design_controller()

        # 验证增益计算
        # 对于 a=-1, b=2, pole=0.5
        # theta_r = (0.5 - (-1)) / 2 = 0.75
        # theta_x = -((-1) + 0.5) / 2 = 0.25
        assert abs(self.controller.controller_gains[0] - 0.75) < 0.01
        assert abs(self.controller.controller_gains[1] - 0.25) < 0.01


class TestSelfTuningIntegration:
    """自校正控制器集成测试"""

    def test_full_str_system(self):
        """测试完整的自校正控制系统"""
        controller = SelfTuningController(
            n_params=2,
            desired_poles=[0.6],
            estimation_method="forgetting_factor",
            forgetting_factor=0.98,
            adaptation_gain=0.05,
        )

        plant = create_first_order_plant(time_constant=1.0, gain=1.0)

        # 运行仿真
        for _ in range(2000):
            y = plant.get_output()
            phi = np.array([1.0, -y])
            u = controller.compute_control(1.0, y, 0.01, phi)
            plant.update(u, 0.01)

        # 验证系统正常运行
        assert len(controller.history) == 2000

        # 检查参数估计有变化
        _, params = controller.get_parameter_estimates()
        assert not np.all(params[-1] == 0)

    def test_str_with_disturbance(self):
        """测试自校正控制器的扰动抑制能力"""
        controller = SelfTuningController(
            n_params=2,
            desired_poles=[0.5],
            estimation_method="rls",
            forgetting_factor=0.98,
        )

        plant = create_first_order_plant(time_constant=1.0, gain=1.0)
        plant.params.disturbance_amplitude = 0.5
        plant.params.disturbance_frequency = 0.5

        # 运行仿真
        for _ in range(1000):
            y = plant.get_output()
            phi = np.array([1.0, -y])
            u = controller.compute_control(1.0, y, 0.01, phi)
            plant.update(u, 0.01)

        # 验证系统稳定
        outputs = [h["output"] for h in controller.history]
        assert not np.any(np.isnan(outputs))
        assert not np.any(np.isinf(outputs))

    def test_str_with_noisy_measurements(self):
        """测试自校正控制器对噪声的鲁棒性"""
        controller = SelfTuningController(
            n_params=2,
            desired_poles=[0.5],
            estimation_method="rls",
            forgetting_factor=0.99,
        )

        plant = create_first_order_plant(time_constant=1.0, gain=1.0, noise_std=0.1)

        # 运行仿真
        for _ in range(1000):
            y = plant.get_output()
            phi = np.array([1.0, -y])
            u = controller.compute_control(1.0, y, 0.01, phi)
            plant.update(u, 0.01)

        # 验证系统稳定
        outputs = [h["output"] for h in controller.history]
        assert not np.any(np.isnan(outputs))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
