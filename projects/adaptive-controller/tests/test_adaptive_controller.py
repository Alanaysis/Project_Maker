"""
自适应控制器测试

测试 MRAC 控制器的核心功能。
"""

import pytest
import numpy as np
from src.adaptive_controller import MRACController, AdaptationLaw, ControllerState
from src.reference_model import ReferenceModel, create_first_order_model, create_second_order_model
from src.plant_model import PlantModel, create_first_order_plant
from src.simulation import SimulationEngine, SimulationConfig, ReferenceSignal


class TestMRACController:
    """MRAC 控制器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
        self.controller = MRACController(
            reference_model=self.ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=0.5,
        )

    def test_initialization(self):
        """测试初始化"""
        assert self.controller.adaptation_law == AdaptationLaw.LYAPUNOV
        assert self.controller.gamma == 0.5
        assert "theta_r" in self.controller.params
        assert "theta_x" in self.controller.params
        assert "theta_d" in self.controller.params

    def test_compute_control(self):
        """测试控制信号计算"""
        # 设置初始状态
        self.controller.reference_model.update(1.0, 0.01)

        # 计算控制信号
        u = self.controller.compute_control(
            reference_input=1.0,
            plant_output=0.5,
            dt=0.01,
        )

        # 验证返回值
        assert isinstance(u, float)
        assert len(self.controller.history) == 1

    def test_parameter_update(self):
        """测试参数更新"""
        # 记录初始参数
        initial_theta_r = self.controller.params["theta_r"]

        # 运行几步
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        # 验证参数已更新
        assert self.controller.params["theta_r"] != initial_theta_r

    def test_lyapunov_adaptation(self):
        """测试 Lyapunov 自适应律"""
        controller = MRACController(
            reference_model=create_first_order_model(),
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=1.0,
            initial_params={
                "theta_r": 0.1,
                "theta_x": np.array([0.1]),
                "theta_d": 0.0,
            }
        )

        # 运行仿真
        plant = create_first_order_plant(time_constant=1.0, gain=2.0)
        for _ in range(1000):
            y = plant.get_output()
            u = controller.compute_control(1.0, y, 0.01)
            plant.update(u, 0.01)

        # 验证参数有变化
        assert controller.params["theta_r"] != 0.1

    def test_mit_adaptation(self):
        """测试 MIT 规则自适应律"""
        controller = MRACController(
            reference_model=create_first_order_model(),
            adaptation_law=AdaptationLaw.MIT,
            adaptation_gain=0.1,
            initial_params={
                "theta_r": 0.5,
                "theta_x": np.array([0.5]),
                "theta_d": 0.0,
            }
        )

        # 运行仿真
        plant = create_first_order_plant(time_constant=1.0, gain=1.0)
        for _ in range(500):
            y = plant.get_output()
            u = controller.compute_control(1.0, y, 0.01)
            plant.update(u, 0.01)

        # 验证控制器正常工作
        assert len(controller.history) == 500

    def test_history_recording(self):
        """测试历史记录"""
        n_steps = 50
        for i in range(n_steps):
            self.controller.compute_control(1.0, 0.5 * i / n_steps, 0.01)

        assert len(self.controller.history) == n_steps

        # 检查历史记录内容
        last_state = self.controller.history[-1]
        assert isinstance(last_state, ControllerState)
        assert last_state.time > 0

    def test_reset(self):
        """测试重置功能"""
        # 运行几步
        for _ in range(10):
            self.controller.compute_control(1.0, 0.5, 0.01)

        # 重置
        self.controller.reset()

        # 验证状态已重置
        assert len(self.controller.history) == 0
        assert self.controller._integral_error == 0.0

    def test_tracking_error_history(self):
        """测试跟踪误差历史"""
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        times, errors = self.controller.get_tracking_error_history()
        assert len(times) == 100
        assert len(errors) == 100

    def test_parameter_history(self):
        """测试参数历史"""
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        times, params = self.controller.get_parameter_history()
        assert len(times) == 100
        assert "theta_r" in params
        assert "theta_x" in params


class TestReferenceModel:
    """参考模型测试类"""

    def test_first_order_model(self):
        """测试一阶参考模型"""
        model = create_first_order_model(time_constant=1.0, steady_state_gain=1.0)

        # 阶跃响应
        outputs = []
        for _ in range(1000):
            y = model.update(1.0, 0.01)
            outputs.append(y)

        # 验证稳态值接近 1.0
        assert abs(outputs[-1] - 1.0) < 0.1

    def test_second_order_model(self):
        """测试二阶参考模型"""
        model = create_second_order_model(natural_frequency=2.0, damping_ratio=0.7)

        # 阶跃响应
        outputs = []
        for _ in range(2000):
            y = model.update(1.0, 0.005)
            outputs.append(y)

        # 验证稳态值接近 1.0
        assert abs(outputs[-1] - 1.0) < 0.1

    def test_model_reset(self):
        """测试模型重置"""
        model = create_first_order_model()

        # 运行几步
        for _ in range(10):
            model.update(1.0, 0.01)

        # 重置
        model.reset()

        # 验证状态已重置
        assert model.time == 0.0
        assert model.y_m == 0.0
        assert len(model._history) == 0


class TestPlantModel:
    """被控对象测试类"""

    def test_first_order_plant(self):
        """测试一阶被控对象"""
        plant = create_first_order_plant(time_constant=1.0, gain=1.0)

        # 阶跃响应
        outputs = []
        for _ in range(1000):
            y = plant.update(1.0, 0.01)
            outputs.append(y)

        # 验证稳态值接近 1.0
        assert abs(outputs[-1] - 1.0) < 0.2

    def test_plant_with_noise(self):
        """测试带噪声的被控对象"""
        plant = create_first_order_plant(noise_std=0.1)

        # 运行多次
        outputs = []
        for _ in range(100):
            y = plant.update(1.0, 0.01)
            outputs.append(y)

        # 验证有噪声
        assert np.std(outputs) > 0

    def test_plant_reset(self):
        """测试被控对象重置"""
        plant = create_first_order_plant()

        # 运行几步
        for _ in range(10):
            plant.update(1.0, 0.01)

        # 重置
        plant.reset()

        # 验证状态已重置
        assert plant.time == 0.0
        assert plant.y == 0.0


class TestSimulationEngine:
    """仿真引擎测试类"""

    def test_step_response(self):
        """测试阶跃响应仿真"""
        ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
        plant = create_first_order_plant(time_constant=1.0, gain=2.0)
        controller = MRACController(
            reference_model=ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=0.5,
        )

        config = SimulationConfig(
            duration=5.0,
            dt=0.01,
            reference_type=ReferenceSignal.STEP,
            reference_amplitude=1.0,
        )

        engine = SimulationEngine(controller, plant, config)
        result = engine.run()

        # 验证结果
        assert len(result.times) == 500
        assert result.metrics["mse"] >= 0
        assert result.metrics["rise_time"] > 0

    def test_sine_tracking(self):
        """测试正弦跟踪仿真"""
        ref_model = create_first_order_model(time_constant=0.3, steady_state_gain=1.0)
        plant = create_first_order_plant(time_constant=1.0, gain=1.0)
        controller = MRACController(
            reference_model=ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=1.0,
        )

        config = SimulationConfig(
            duration=10.0,
            dt=0.01,
            reference_type=ReferenceSignal.SINE,
            reference_amplitude=1.0,
            reference_frequency=0.5,
        )

        engine = SimulationEngine(controller, plant, config)
        result = engine.run()

        # 验证结果
        assert len(result.times) == 1000
        assert "mse" in result.metrics

    def test_simulation_result(self):
        """测试仿真结果结构"""
        ref_model = create_first_order_model()
        plant = create_first_order_plant()
        controller = MRACController(reference_model=ref_model)

        config = SimulationConfig(duration=1.0, dt=0.1)
        engine = SimulationEngine(controller, plant, config)
        result = engine.run()

        # 验证结果包含所有必要字段
        assert hasattr(result, 'times')
        assert hasattr(result, 'reference_signal')
        assert hasattr(result, 'reference_model_output')
        assert hasattr(result, 'plant_output')
        assert hasattr(result, 'control_signal')
        assert hasattr(result, 'tracking_error')
        assert hasattr(result, 'parameter_history')
        assert hasattr(result, 'metrics')


class TestIntegration:
    """集成测试"""

    def test_full_mrac_system(self):
        """测试完整的 MRAC 系统"""
        # 创建参考模型
        ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

        # 创建被控对象 (与参考模型参数不同)
        plant = create_first_order_plant(time_constant=2.0, gain=0.5)

        # 创建自适应控制器
        controller = MRACController(
            reference_model=ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=0.3,
            initial_params={
                "theta_r": 0.1,
                "theta_x": np.array([0.1]),
                "theta_d": 0.0,
            }
        )

        # 运行长时间仿真
        for _ in range(2000):
            y = plant.get_output()
            u = controller.compute_control(1.0, y, 0.01)
            plant.update(u, 0.01)

        # 验证跟踪误差在减小
        errors = [s.tracking_error for s in controller.history]
        early_error = np.mean(np.abs(errors[:100]))
        late_error = np.mean(np.abs(errors[-100:]))

        # 后期误差应该更小
        assert late_error < early_error

    def test_adaptation_convergence(self):
        """测试参数自适应收敛"""
        ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
        plant = create_first_order_plant(time_constant=1.0, gain=2.0)

        controller = MRACController(
            reference_model=ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=0.5,
            initial_params={
                "theta_r": 0.1,
                "theta_x": np.array([0.1]),
                "theta_d": 0.0,
            }
        )

        # 运行仿真
        for _ in range(3000):
            y = plant.get_output()
            u = controller.compute_control(1.0, y, 0.01)
            plant.update(u, 0.01)

        # 获取参数历史
        times, params = controller.get_parameter_history()

        # 验证参数在收敛 (后期变化减小)
        theta_r = params["theta_r"]
        early_change = np.std(theta_r[:100])
        late_change = np.std(theta_r[-100:])

        # 后期变化应该更小
        assert late_change < early_change


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
