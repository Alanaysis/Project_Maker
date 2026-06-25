"""
仿真环境测试
"""

import pytest
import numpy as np
from src.plant_model import DoubleIntegrator
from src.mpc_controller import MPCController, MPCConfig
from src.optimizer import MPCConstraints, MPCWeights
from src.simulation import MPCSimulation, SimulationConfig


class TestMPCSimulation:
    """MPC 仿真测试"""

    def setup_method(self):
        """测试前准备"""
        # 双积分器系统
        self.plant = DoubleIntegrator(dt=0.1)

        # MPC 配置
        self.config = MPCConfig(
            prediction_horizon=10,
            control_horizon=5,
            sample_time=0.1
        )

        # 权重配置
        self.weights = MPCWeights(
            Q=np.diag([10.0, 1.0]),
            R=np.array([[0.1]])
        )

        # 约束配置
        self.constraints = MPCConstraints(
            u_min=np.array([-2.0]),
            u_max=np.array([2.0])
        )

        # 创建控制器
        self.controller = MPCController(
            self.plant, self.config, self.constraints, self.weights
        )

    def test_simulation_initialization(self):
        """测试仿真初始化"""
        sim = MPCSimulation(self.plant, self.controller)

        assert sim.plant == self.plant
        assert sim.controller == self.controller

    def test_step_response(self):
        """测试阶跃响应"""
        sim = MPCSimulation(self.plant, self.controller)

        x0 = np.array([0.0, 0.0])
        step_value = np.array([1.0, 0.0])

        result = sim.run_step_response(x0, step_value, step_time=0.5)

        # 验证结果
        assert result.time.shape[0] > 0
        assert result.states.shape[0] > 0
        assert result.inputs.shape[0] > 0
        assert result.outputs.shape[0] > 0

        # 验证阶跃响应特性
        # 最终应该接近参考值
        final_output = result.outputs[-1, 0]
        assert abs(final_output - 1.0) < 0.5  # 允许一定误差

    def test_sinusoidal_response(self):
        """测试正弦响应"""
        sim = MPCSimulation(self.plant, self.controller)

        x0 = np.array([0.0, 0.0])
        amplitude = np.array([1.0, 0.0])
        frequency = 0.1  # Hz

        result = sim.run_sinusoidal_response(x0, amplitude, frequency)

        # 验证结果
        assert result.time.shape[0] > 0
        assert result.outputs.shape[0] > 0

    def test_simulation_config(self):
        """测试仿真配置"""
        sim_config = SimulationConfig(
            total_time=5.0,
            sample_time=0.05,
            noise_std=0.01,
            measurement_noise_std=0.001
        )

        sim = MPCSimulation(self.plant, self.controller, sim_config)

        x0 = np.array([0.0, 0.0])
        step_value = np.array([1.0, 0.0])

        result = sim.run_step_response(x0, step_value)

        # 验证时间长度
        assert result.time[-1] <= 5.0 + 0.1

    def test_custom_reference(self):
        """测试自定义参考信号"""
        sim = MPCSimulation(self.plant, self.controller)

        x0 = np.array([0.0, 0.0])

        # 自定义参考：分段常数
        def custom_reference(t):
            if t < 2.0:
                return np.array([1.0, 0.0])
            elif t < 4.0:
                return np.array([0.0, 1.0])
            else:
                return np.array([0.5, 0.5])

        result = sim.run(x0, custom_reference)

        # 验证结果
        assert result.time.shape[0] > 0
        assert result.outputs.shape[0] > 0

    def test_random_reference(self):
        """测试随机参考"""
        sim = MPCSimulation(self.plant, self.controller)

        x0 = np.array([0.0, 0.0])

        result = sim.run_random_reference(
            x0, ref_range=(-1.0, 1.0), change_interval=2.0
        )

        # 验证结果
        assert result.time.shape[0] > 0
        assert result.outputs.shape[0] > 0

    def test_noisy_simulation(self):
        """测试带噪声的仿真"""
        sim_config = SimulationConfig(
            total_time=5.0,
            sample_time=0.1,
            noise_std=0.05,
            measurement_noise_std=0.02
        )

        sim = MPCSimulation(self.plant, self.controller, sim_config)

        x0 = np.array([0.0, 0.0])
        step_value = np.array([1.0, 0.0])

        result = sim.run_step_response(x0, step_value)

        # 验证结果
        assert result.time.shape[0] > 0

        # 带噪声时跟踪误差应该更大
        tracking_error = np.abs(result.outputs[:, 0] - result.references[:, 0])
        mean_error = np.mean(tracking_error)
        assert mean_error > 0  # 应该有一些误差

    def test_simulation_result_attributes(self):
        """测试仿真结果属性"""
        sim = MPCSimulation(self.plant, self.controller)

        x0 = np.array([0.0, 0.0])
        step_value = np.array([1.0, 0.0])

        result = sim.run_step_response(x0, step_value)

        # 验证所有属性
        assert hasattr(result, 'time')
        assert hasattr(result, 'states')
        assert hasattr(result, 'inputs')
        assert hasattr(result, 'outputs')
        assert hasattr(result, 'references')
        assert hasattr(result, 'costs')
        assert hasattr(result, 'info')

        # 验证形状一致性
        N = result.info['n_steps']
        assert result.time.shape == (N + 1,)
        assert result.states.shape == (N + 1, 2)
        assert result.inputs.shape == (N, 1)
        assert result.outputs.shape == (N, 2)
        assert result.references.shape == (N, 2)
        assert result.costs.shape == (N,)


class TestSimulationEdgeCases:
    """仿真边界情况测试"""

    def test_zero_initial_state(self):
        """测试零初始状态"""
        plant = DoubleIntegrator(dt=0.1)
        config = MPCConfig(prediction_horizon=5, control_horizon=3)
        weights = MPCWeights(Q=np.eye(2), R=0.1*np.eye(1))
        controller = MPCController(plant, config, weights=weights)

        sim = MPCSimulation(plant, controller)

        x0 = np.array([0.0, 0.0])
        ref = np.array([0.0, 0.0])

        result = sim.run_step_response(x0, ref)

        # 零初始状态，零参考，控制输入应该很小
        assert np.all(np.abs(result.inputs) < 0.1)

    def test_large_initial_error(self):
        """测试大初始误差"""
        plant = DoubleIntegrator(dt=0.1)
        config = MPCConfig(prediction_horizon=10, control_horizon=5)
        weights = MPCWeights(Q=np.diag([1.0, 0.1]), R=0.01*np.eye(1))
        constraints = MPCConstraints(u_min=np.array([-5.0]), u_max=np.array([5.0]))
        controller = MPCController(plant, config, constraints, weights)

        sim = MPCSimulation(plant, controller)

        x0 = np.array([10.0, 0.0])  # 远离目标
        ref = np.array([0.0, 0.0])

        result = sim.run_step_response(x0, ref)

        # 应该有较大的控制输入
        assert np.max(np.abs(result.inputs)) > 1.0

    def test_short_simulation(self):
        """测试短仿真"""
        plant = DoubleIntegrator(dt=0.1)
        config = MPCConfig(prediction_horizon=5, control_horizon=3)
        weights = MPCWeights(Q=np.eye(2), R=0.1*np.eye(1))
        controller = MPCController(plant, config, weights=weights)

        sim_config = SimulationConfig(total_time=0.5, sample_time=0.1)
        sim = MPCSimulation(plant, controller, sim_config)

        x0 = np.array([0.0, 0.0])
        ref = np.array([1.0, 0.0])

        result = sim.run_step_response(x0, ref)

        # 短仿真应该有少量步骤
        assert result.info['n_steps'] <= 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
