"""
预测模型测试 - 状态空间模型和脉冲响应模型
"""

import pytest
import numpy as np
from src.models import (
    StateSpaceModel,
    ImpulseResponseModel,
    DiscreteTransferFunction,
)


class TestStateSpaceModel:
    """状态空间模型测试"""

    def test_initialization(self):
        """测试初始化"""
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        model = StateSpaceModel(A, B)

        assert model.n_states == 2
        assert model.n_inputs == 1
        assert model.n_outputs == 2  # 默认 C = I
        np.testing.assert_array_equal(model.A, A)
        np.testing.assert_array_equal(model.B, B)

    def test_predict(self):
        """测试状态预测"""
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        model = StateSpaceModel(A, B)

        x = np.array([1.0, 2.0])
        u = np.array([0.5])

        x_next = model.predict(x, u)
        expected = A @ x + B @ u
        np.testing.assert_array_almost_equal(x_next, expected)

    def test_output(self):
        """测试输出计算"""
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        C = np.array([[1.0, 0.0]])
        model = StateSpaceModel(A, B, C)

        x = np.array([1.0, 2.0])
        y = model.output(x)
        np.testing.assert_array_almost_equal(y, [1.0])

    def test_predict_sequence(self):
        """测试序列预测"""
        A = np.array([[0.9, 0.0], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        model = StateSpaceModel(A, B)

        x0 = np.array([0.0, 0.0])
        U = np.array([[1.0], [1.0], [1.0]])

        X, Y = model.predict_sequence(x0, U)

        assert X.shape == (4, 2)  # N+1 x n
        assert Y.shape == (3, 2)  # N x n (default C = I)

    def test_stability_check(self):
        """测试稳定性检查"""
        # 稳定系统
        A_stable = np.array([[0.5, 0.0], [0.0, 0.3]])
        B = np.array([[1.0], [0.5]])
        model_stable = StateSpaceModel(A_stable, B)
        assert model_stable.is_stable()

        # 不稳定系统
        A_unstable = np.array([[1.5, 0.0], [0.0, 0.3]])
        model_unstable = StateSpaceModel(A_unstable, B)
        assert not model_unstable.is_stable()

    def test_controllability(self):
        """测试可控性检查"""
        # 可控系统
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        model = StateSpaceModel(A, B)
        assert model.is_controllable()

    def test_observability(self):
        """测试可观性检查"""
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        C = np.array([[1.0, 0.0]])
        model = StateSpaceModel(A, B, C)
        assert model.is_observable()

    def test_prediction_matrices(self):
        """测试预测矩阵计算"""
        A = np.array([[0.9, 0.1], [0.0, 0.8]])
        B = np.array([[1.0], [0.5]])
        C = np.array([[1.0, 0.0]])
        model = StateSpaceModel(A, B, C)

        Np = 5
        Psi, Theta = model.compute_prediction_matrices(Np)

        # Psi: Np*p x n
        assert Psi.shape == (Np * 1, 2)
        # Theta: Np*p x Np*m
        assert Theta.shape == (Np * 1, Np * 1)


class TestImpulseResponseModel:
    """脉冲响应模型测试"""

    def test_initialization_siso(self):
        """测试 SISO 系统初始化"""
        h = np.array([1.0, 0.5, 0.25, 0.125])
        model = ImpulseResponseModel(h)

        assert model.N == 4
        assert model.n_inputs == 1
        assert model.n_outputs == 1

    def test_initialization_mimo(self):
        """测试 MIMO 系统初始化"""
        N, p, m = 5, 2, 1
        h = np.random.randn(N, p, m)
        model = ImpulseResponseModel(h)

        assert model.N == N
        assert model.n_inputs == m
        assert model.n_outputs == p

    def test_predict_siso(self):
        """测试 SISO 系统预测"""
        # 简单的一阶系统脉冲响应
        h = np.array([1.0, 0.5, 0.25])
        model = ImpulseResponseModel(h)

        # 阶跃输入
        outputs = []
        for i in range(5):
            y = model.predict(np.array([1.0]))
            outputs.append(y[0])

        # 验证输出
        expected = [1.0, 1.5, 1.75, 1.75, 1.75]
        np.testing.assert_array_almost_equal(outputs, expected)

    def test_from_step_response(self):
        """测试从阶跃响应创建"""
        # 阶跃响应
        step = np.array([0.0, 0.5, 0.75, 0.875, 0.9375])
        model = ImpulseResponseModel.from_step_response(step)

        # 脉冲响应应该是阶跃响应的差分
        expected_h = np.array([0.0, 0.5, 0.25, 0.125, 0.0625])
        np.testing.assert_array_almost_equal(model.h.flatten(), expected_h)

    def test_from_state_space(self):
        """测试从状态空间模型计算脉冲响应"""
        # 一阶系统: x(k+1) = 0.9*x(k) + u(k), y(k) = x(k)
        A = np.array([[0.9]])
        B = np.array([[1.0]])
        C = np.array([[1.0]])
        N = 10

        model = ImpulseResponseModel.from_state_space(A, B, C, N)

        # 脉冲响应: h(k) = C * A^k * B
        for k in range(N):
            expected = 0.9 ** k
            np.testing.assert_almost_equal(model.h[k, 0, 0], expected, decimal=10)

    def test_prediction_matrix(self):
        """测试预测矩阵计算"""
        h = np.array([1.0, 0.5, 0.25])
        model = ImpulseResponseModel(h)

        Np = 5
        S = model.compute_prediction_matrix(Np)

        # 验证下三角结构
        assert S.shape == (Np, Np)
        # 第一列应该是 [h0, h1, h2, 0, 0]
        np.testing.assert_almost_equal(S[:, 0], [1.0, 0.5, 0.25, 0.0, 0.0])

    def test_reset(self):
        """测试重置"""
        h = np.array([1.0, 0.5, 0.25])
        model = ImpulseResponseModel(h)

        # 执行一些预测
        model.predict(np.array([1.0]))
        model.predict(np.array([2.0]))

        # 重置
        model.reset()

        # 内部历史应该清零
        np.testing.assert_array_equal(model._u_history, np.zeros((3, 1)))

    def test_predict_sequence(self):
        """测试序列预测"""
        h = np.array([1.0, 0.5, 0.25])
        model = ImpulseResponseModel(h)

        # 历史输入
        u_history = np.array([[1.0], [0.5]])
        # 未来输入
        U_future = np.array([[0.0], [0.0]])

        Y = model.predict_sequence(u_history, U_future)
        assert Y.shape == (2, 1)


class TestDiscreteTransferFunction:
    """离散传递函数测试"""

    def test_initialization(self):
        """测试初始化"""
        num = np.array([1.0, 0.5])
        den = np.array([1.0, -0.8])
        model = DiscreteTransferFunction(num, den)

        # 分母应该归一化
        np.testing.assert_almost_equal(model.den[0], 1.0)

    def test_step_response(self):
        """测试阶跃响应"""
        # 一阶系统: H(z) = 1 / (1 - 0.9*z^-1)
        num = np.array([1.0])
        den = np.array([1.0, -0.9])
        model = DiscreteTransferFunction(num, den)

        # 阶跃响应应该收敛到 1/(1-0.9) = 10
        outputs = []
        for _ in range(50):
            y = model.step(1.0)
            outputs.append(y)

        # 最终输出应该接近 10
        np.testing.assert_almost_equal(outputs[-1], 10.0, decimal=1)

    def test_impulse_response(self):
        """测试脉冲响应"""
        # H(z) = 1 / (1 - 0.5*z^-1)
        num = np.array([1.0])
        den = np.array([1.0, -0.5])
        model = DiscreteTransferFunction(num, den)

        h = model.impulse_response(5)
        expected = [1.0, 0.5, 0.25, 0.125, 0.0625]
        np.testing.assert_array_almost_equal(h, expected, decimal=10)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
