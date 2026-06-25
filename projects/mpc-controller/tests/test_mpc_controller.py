"""
MPC 控制器测试
"""

import pytest
import numpy as np
from src.plant_model import DoubleIntegrator, LinearPlantModel
from src.mpc_controller import MPCController, MPCConfig, MPCMode
from src.optimizer import MPCConstraints, MPCWeights


class TestMPCController:
    """MPC 控制器测试"""

    def setup_method(self):
        """测试前准备"""
        # 双积分器系统
        self.plant = DoubleIntegrator(dt=0.1)

        # MPC 配置
        self.config = MPCConfig(
            prediction_horizon=10,
            control_horizon=5,
            sample_time=0.1,
            mode=MPCMode.LINEAR
        )

        # 权重配置
        self.weights = MPCWeights(
            Q=np.diag([10.0, 1.0]),  # 状态权重
            R=np.array([[0.1]]),      # 输入权重
            Rd=np.array([[0.01]])     # 输入变化率权重
        )

        # 约束配置
        self.constraints = MPCConstraints(
            u_min=np.array([-2.0]),
            u_max=np.array([2.0])
        )

    def test_initialization(self):
        """测试初始化"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        assert controller.plant == self.plant
        assert controller.config == self.config
        assert controller.dt == 0.1

    def test_compute_control(self):
        """测试控制计算"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        # 初始状态
        x0 = np.array([1.0, 0.0])
        reference = np.array([0.0, 0.0])  # 目标：原点

        # 计算控制输入
        result = controller.compute_control(x0, reference)

        # 验证结果
        assert result.u_optimal.shape == (1,)
        assert result.u_sequence.shape == (5, 1)  # control_horizon x n_inputs
        assert result.x_predicted.shape == (11, 2)  # (Np+1) x n_states
        assert result.y_predicted.shape == (10, 2)  # Np x n_outputs
        assert isinstance(result.cost, float)

    def test_constraint_satisfaction(self):
        """测试约束满足"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        x0 = np.array([5.0, 0.0])  # 远离目标
        reference = np.array([0.0, 0.0])

        result = controller.compute_control(x0, reference)

        # 验证输入约束
        assert np.all(result.u_optimal >= self.constraints.u_min)
        assert np.all(result.u_optimal <= self.constraints.u_max)

        # 验证控制序列约束
        assert np.all(result.u_sequence >= self.constraints.u_min)
        assert np.all(result.u_sequence <= self.constraints.u_max)

    def test_tracking_performance(self):
        """测试跟踪性能"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        # 模拟多步控制
        x = np.array([0.0, 0.0])
        reference = np.array([1.0, 0.0])  # 目标位置

        for _ in range(50):
            result = controller.compute_control(x, reference)
            u = result.u_optimal
            x = self.plant.step(x, u, self.config.sample_time)

        # 应该接近目标位置
        assert abs(x[0] - 1.0) < 0.1

    def test_reset(self):
        """测试重置"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        x0 = np.array([1.0, 0.0])
        reference = np.array([0.0, 0.0])

        # 计算一次控制
        controller.compute_control(x0, reference)

        # 重置
        controller.reset()

        # 验证历史被清空
        assert len(controller.history['states']) == 0
        assert len(controller.history['inputs']) == 0

    def test_different_reference(self):
        """测试不同参考值"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        # 测试不同参考值
        references = [
            np.array([0.0, 0.0]),
            np.array([1.0, 0.0]),
            np.array([0.0, 1.0]),
            np.array([-1.0, -1.0])
        ]

        x0 = np.array([0.0, 0.0])

        for ref in references:
            result = controller.compute_control(x0, ref)
            assert result.u_optimal.shape == (1,)

    def test_operating_point(self):
        """测试工作点设置"""
        controller = MPCController(
            plant=self.plant,
            config=self.config,
            constraints=self.constraints,
            weights=self.weights
        )

        # 设置工作点
        state_op = np.array([0.0, 0.0])
        u_op = np.array([0.0])
        controller.set_operating_point(state_op, u_op)

        # 验证可以正常计算
        x0 = np.array([0.5, 0.0])
        reference = np.array([0.0, 0.0])
        result = controller.compute_control(x0, reference)

        assert result.u_optimal.shape == (1,)


class TestMPCWithLinearSystem:
    """线性系统 MPC 测试"""

    def test_siso_system(self):
        """测试单输入单输出系统"""
        # 一阶系统：x(k+1) = 0.9*x(k) + u(k)
        A = np.array([[0.9]])
        B = np.array([[1.0]])
        C = np.array([[1.0]])
        plant = LinearPlantModel(A, B, C)

        config = MPCConfig(
            prediction_horizon=10,
            control_horizon=5,
            sample_time=1.0
        )

        weights = MPCWeights(
            Q=np.array([[1.0]]),
            R=np.array([[0.1]])
        )

        controller = MPCController(plant, config, weights=weights)

        # 测试跟踪
        x = np.array([0.0])
        reference = np.array([1.0])

        for _ in range(20):
            result = controller.compute_control(x, reference)
            x = plant.step(x, result.u_optimal, 1.0)

        # 应该接近参考值
        assert abs(x[0] - 1.0) < 0.2

    def test_mimo_system(self):
        """测试多输入多输出系统"""
        # 2x2 系统
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0, 0.0], [0.0, 1.0]])
        C = np.eye(2)
        plant = LinearPlantModel(A, B, C)

        config = MPCConfig(
            prediction_horizon=10,
            control_horizon=5,
            sample_time=1.0
        )

        weights = MPCWeights(
            Q=np.eye(2),
            R=0.1 * np.eye(2)
        )

        controller = MPCController(plant, config, weights=weights)

        # 测试跟踪
        x = np.array([0.0, 0.0])
        reference = np.array([1.0, 0.5])

        for _ in range(30):
            result = controller.compute_control(x, reference)
            x = plant.step(x, result.u_optimal, 1.0)

        # 应该接近参考值
        assert abs(x[0] - 1.0) < 0.3
        assert abs(x[1] - 0.5) < 0.3


class TestMPCOptimizer:
    """MPC 优化器测试"""

    def test_unconstrained_optimization(self):
        """测试无约束优化"""
        from src.optimizer import MPCOptimizer

        n_states = 2
        n_inputs = 1
        Np = 10
        Nc = 5

        optimizer = MPCOptimizer(n_states, n_inputs, Np, Nc)

        # 简单的线性系统
        A = np.array([[1, 0.1], [0, 1]])
        B = np.array([[0.005], [0.1]])
        C = np.eye(2)

        A_list = [A] * Np
        B_list = [B] * Np
        C_list = [C] * Np

        x0 = np.array([1.0, 0.0])
        x_ref = np.zeros((Np, 2))

        U_opt, info = optimizer.solve(x0, A_list, B_list, C_list, x_ref)

        assert U_opt.shape == (Nc, n_inputs)
        assert info['success']

    def test_constrained_optimization(self):
        """测试有约束优化"""
        from src.optimizer import MPCOptimizer

        n_states = 2
        n_inputs = 1
        Np = 10
        Nc = 5

        constraints = MPCConstraints(
            u_min=np.array([-1.0]),
            u_max=np.array([1.0])
        )

        optimizer = MPCOptimizer(n_states, n_inputs, Np, Nc, constraints=constraints)

        A = np.array([[1, 0.1], [0, 1]])
        B = np.array([[0.005], [0.1]])
        C = np.eye(2)

        A_list = [A] * Np
        B_list = [B] * Np
        C_list = [C] * Np

        x0 = np.array([5.0, 0.0])  # 远离目标，需要大输入
        x_ref = np.zeros((Np, 2))

        U_opt, info = optimizer.solve(x0, A_list, B_list, C_list, x_ref)

        # 验证约束满足
        assert np.all(U_opt >= -1.0)
        assert np.all(U_opt <= 1.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
