"""
被控对象模型测试
"""

import pytest
import numpy as np
from src.plant_model import (
    LinearPlantModel,
    NonlinearPlantModel,
    DoubleIntegrator,
    PendulumModel,
    TankSystem
)


class TestLinearPlantModel:
    """线性系统模型测试"""

    def test_initialization(self):
        """测试初始化"""
        A = np.array([[1, 0.1], [0, 1]])
        B = np.array([[0.005], [0.1]])
        model = LinearPlantModel(A, B)

        assert model.n_states == 2
        assert model.n_inputs == 1
        assert model.n_outputs == 2
        np.testing.assert_array_equal(model.A, A)
        np.testing.assert_array_equal(model.B, B)

    def test_step(self):
        """测试状态更新"""
        A = np.array([[1, 0.1], [0, 1]])
        B = np.array([[0.005], [0.1]])
        model = LinearPlantModel(A, B)

        x = np.array([1.0, 0.5])
        u = np.array([1.0])
        x_next = model.step(x, u)

        expected = A @ x + B @ u
        np.testing.assert_array_almost_equal(x_next, expected)

    def test_output(self):
        """测试输出计算"""
        A = np.array([[1, 0.1], [0, 1]])
        B = np.array([[0.005], [0.1]])
        C = np.array([[1, 0]])
        model = LinearPlantModel(A, B, C)

        x = np.array([1.0, 0.5])
        y = model.output(x)

        expected = C @ x
        np.testing.assert_array_almost_equal(y, expected)

    def test_linearize(self):
        """测试线性化"""
        A = np.array([[1, 0.1], [0, 1]])
        B = np.array([[0.005], [0.1]])
        model = LinearPlantModel(A, B)

        x_op = np.array([0.0, 0.0])
        u_op = np.array([0.0])
        A_lin, B_lin, C_lin, D_lin = model.linearize(x_op, u_op)

        np.testing.assert_array_almost_equal(A_lin, A)
        np.testing.assert_array_almost_equal(B_lin, B)


class TestDoubleIntegrator:
    """双积分器测试"""

    def test_initialization(self):
        """测试初始化"""
        model = DoubleIntegrator(dt=0.1)

        assert model.n_states == 2
        assert model.n_inputs == 1
        assert model.dt == 0.1

    def test_dynamics(self):
        """测试动力学特性"""
        model = DoubleIntegrator(dt=0.1)

        # 初始状态：位置=1，速度=0
        x = np.array([1.0, 0.0])
        u = np.array([-1.0])  # 负加速度

        # 执行一步
        x_next = model.step(x, u)

        # 验证物理意义：位置应该减小，速度应该变为负
        assert x_next[0] < x[0]  # 位置减小
        assert x_next[1] < x[1]  # 速度变为负

    def test_stability(self):
        """测试稳定性（无控制时）"""
        model = DoubleIntegrator(dt=0.1)

        x = np.array([1.0, 0.0])
        u = np.array([0.0])

        # 无控制时，速度保持不变
        for _ in range(10):
            x = model.step(x, u)

        # 位置应该线性增长（因为速度为0）
        np.testing.assert_almost_equal(x[0], 1.0)
        np.testing.assert_almost_equal(x[1], 0.0)


class TestPendulumModel:
    """倒立摆模型测试"""

    def test_initialization(self):
        """测试初始化"""
        model = PendulumModel(m=1.0, L=1.0, b=0.1, g=9.81)

        assert model.n_states == 2
        assert model.n_inputs == 1
        assert model.n_outputs == 1

    def test_downward_equilibrium(self):
        """测试向下平衡点"""
        model = PendulumModel(m=1.0, L=1.0, b=0.1, g=9.81)

        # 向下平衡点：theta=pi, omega=0
        x = np.array([np.pi, 0.0])
        u = np.array([0.0])

        # 在平衡点附近，状态应该相对稳定
        x_next = model.step(x, u, dt=0.01)

        # 角度应该接近 pi
        assert abs(x_next[0] - np.pi) < 0.1

    def test_output(self):
        """测试输出"""
        model = PendulumModel()

        x = np.array([0.5, 0.1])
        y = model.output(x)

        # 输出应该是角度
        np.testing.assert_array_almost_equal(y, [0.5])


class TestTankSystem:
    """双水箱系统测试"""

    def test_initialization(self):
        """测试初始化"""
        model = TankSystem(A1=1.0, A2=1.0, k1=0.5, k2=0.5)

        assert model.n_states == 2
        assert model.n_inputs == 1
        assert model.n_outputs == 1

    def test_steady_state(self):
        """测试稳态"""
        model = TankSystem(A1=1.0, A2=1.0, k1=0.5, k2=0.5)

        # 稳态时：流入 = 流出
        # u = k1*sqrt(h1) = k2*sqrt(h2)
        # 设 u=0.5, 则 h1 = (u/k1)^2 = 1, h2 = (u/k2)^2 = 1
        x = np.array([1.0, 1.0])
        u = np.array([0.5])

        # 执行多步，应该接近稳态
        for _ in range(100):
            x = model.step(x, u, dt=0.1)

        # 液位应该非负
        assert x[0] >= 0
        assert x[1] >= 0

    def test_output(self):
        """测试输出"""
        model = TankSystem()

        x = np.array([0.5, 0.3])
        y = model.output(x)

        # 输出应该是第二个水箱的液位
        np.testing.assert_array_almost_equal(y, [0.3])


class TestNonlinearPlantModel:
    """非线性系统模型测试"""

    def test_custom_dynamics(self):
        """测试自定义动力学"""
        def dynamics(x, u):
            return np.array([-x[0] + u[0], -x[1]])

        model = NonlinearPlantModel(
            n_states=2,
            n_inputs=1,
            n_outputs=2,
            dynamics_fn=dynamics
        )

        x = np.array([1.0, 1.0])
        u = np.array([1.0])

        # 执行多步，应该收敛到 [1, 0]
        for _ in range(100):
            x = model.step(x, u, dt=0.1)

        np.testing.assert_almost_equal(x[0], 1.0, decimal=2)
        np.testing.assert_almost_equal(x[1], 0.0, decimal=2)

    def test_rk4_accuracy(self):
        """测试 RK4 积分精度"""
        # 简单的一阶系统：dx/dt = -x
        def dynamics(x, u):
            return -x

        model = NonlinearPlantModel(
            n_states=1,
            n_inputs=1,
            n_outputs=1,
            dynamics_fn=dynamics
        )

        x = np.array([1.0])
        u = np.array([0.0])
        dt = 0.01

        # 解析解：x(t) = exp(-t)
        for k in range(100):
            x = model.step(x, u, dt)

        # t=1 时，x = exp(-1) ≈ 0.3679
        expected = np.exp(-1.0)
        np.testing.assert_almost_equal(x[0], expected, decimal=4)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
