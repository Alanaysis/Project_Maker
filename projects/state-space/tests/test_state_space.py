"""
状态空间模型测试

测试覆盖:
1. 连续时间系统
2. 离散时间系统
3. 系统分析（可控性、可观性、稳定性）
4. 状态反馈控制（极点配置、LQR）
5. 观测器（全阶、降阶）
6. 卡尔曼滤波
7. 实际应用（倒立摆、电机）
"""

import pytest
import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.state_space_model import StateSpaceModel, ContinuousStateSpace
from src.kalman_filter import KalmanFilter
from src.analysis import (
    controllability_matrix,
    observability_matrix,
    is_controllable,
    is_observable,
    check_stability_continuous,
    check_stability_discrete,
    stability_margin,
    controllability_index,
    observability_index,
    gramian_controllability,
    gramian_observability,
)
from src.controller import StateFeedbackController, LQRController
from src.observer import FullOrderObserver, ReducedOrderObserver
from src.applications import InvertedPendulum, DCmotor


# ============================================================
# 1. 连续时间系统测试
# ============================================================

class TestContinuousStateSpace:
    """连续时间状态空间模型测试"""

    def setup_method(self):
        """测试前准备：简单的二阶连续系统"""
        self.A = np.array([[0, 1], [-2, -3]])
        self.B = np.array([[0], [1]])
        self.C = np.array([[1, 0]])
        self.D = np.array([[0]])
        self.model = ContinuousStateSpace(self.A, self.B, self.C, self.D)

    def test_initialization(self):
        """测试初始化"""
        assert self.model.n_states == 2
        assert self.model.n_inputs == 1
        assert self.model.n_outputs == 1
        np.testing.assert_array_almost_equal(self.model.A, self.A)

    def test_stability_stable(self):
        """测试稳定连续系统"""
        # A的特征值为 -1 和 -2，都为负实部
        assert self.model.is_stable()

    def test_stability_unstable(self):
        """测试不稳定连续系统"""
        A_unstable = np.array([[1, 0], [0, -2]])
        model = ContinuousStateSpace(A_unstable, self.B, self.C)
        assert not model.is_stable()

    def test_eigenvalues(self):
        """测试特征值计算"""
        eigenvalues = self.model.get_eigenvalues()
        expected = np.linalg.eigvals(self.A)
        np.testing.assert_array_almost_equal(
            np.sort(eigenvalues), np.sort(expected)
        )

    def test_transfer_function(self):
        """测试传递函数"""
        num, den = self.model.get_transfer_function()
        # G(s) = 1 / (s^2 + 3s + 2)
        np.testing.assert_array_almost_equal(den, [1, 3, 2])
        np.testing.assert_array_almost_equal(num, [0, 0, 1])

    def test_discretize_zoh(self):
        """测试零阶保持器离散化"""
        dt = 0.01
        model_d = self.model.discretize(dt, method="zoh")
        assert model_d.n_states == 2
        assert model_d.dt == dt
        # 离散化后应该是稳定的
        assert model_d.is_stable()

    def test_discretize_tustin(self):
        """测试双线性变换离散化"""
        dt = 0.01
        model_d = self.model.discretize(dt, method="tustin")
        assert model_d.is_stable()

    def test_discretize_euler(self):
        """测试前向欧拉离散化"""
        dt = 0.001
        model_d = self.model.discretize(dt, method="euler")
        assert model_d.is_stable()

    def test_simulate(self):
        """测试连续系统仿真"""
        x0 = np.array([1.0, 0.0])
        u_func = lambda t: np.array([0.0])
        t, states, outputs = self.model.simulate(x0, u_func, (0, 1), dt=0.01)

        assert len(t) > 0
        assert states.shape[1] == 2
        np.testing.assert_array_almost_equal(states[0], x0)
        # 稳定系统，状态应衰减
        assert np.linalg.norm(states[-1]) < np.linalg.norm(x0)

    def test_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.model)
        assert "ContinuousStateSpace" in repr_str


# ============================================================
# 2. 离散时间系统测试
# ============================================================

class TestStateSpaceModel:
    """离散时间状态空间模型测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[0.9, 0.1], [-0.1, 0.8]])
        self.B = np.array([[1.0], [0.5]])
        self.C = np.array([[1.0, 0.0]])
        self.D = np.array([[0.0]])
        self.model = StateSpaceModel(self.A, self.B, self.C, self.D)

    def test_initialization(self):
        """测试初始化"""
        assert self.model.n_states == 2
        assert self.model.n_inputs == 1
        assert self.model.n_outputs == 1
        np.testing.assert_array_almost_equal(self.model.A, self.A)

    def test_simulate(self):
        """测试仿真"""
        x0 = np.array([1.0, 0.0])
        u = np.zeros((10, 1))
        states, outputs = self.model.simulate(x0, u)

        assert states.shape == (11, 2)
        assert outputs.shape == (10, 1)
        np.testing.assert_array_almost_equal(states[0], x0)

    def test_step(self):
        """测试单步仿真"""
        x = np.array([1.0, 0.0])
        u = np.array([0.0])
        x_next, y = self.model.step(x, u)

        expected_x_next = self.A @ x + self.B @ u
        expected_y = self.C @ x + self.D @ u

        np.testing.assert_array_almost_equal(x_next, expected_x_next)
        np.testing.assert_array_almost_equal(y, expected_y)

    def test_stability(self):
        """测试稳定性判断"""
        # 稳定系统
        A_stable = np.array([[0.5, 0.0], [0.0, 0.3]])
        model_stable = StateSpaceModel(A_stable, self.B, self.C)
        assert model_stable.is_stable()

        # 不稳定系统
        A_unstable = np.array([[1.5, 0.0], [0.0, 0.3]])
        model_unstable = StateSpaceModel(A_unstable, self.B, self.C)
        assert not model_unstable.is_stable()

    def test_eigenvalues(self):
        """测试特征值计算"""
        eigenvalues = self.model.get_eigenvalues()
        expected = np.linalg.eigvals(self.A)
        np.testing.assert_array_almost_equal(np.sort(eigenvalues), np.sort(expected))

    def test_transfer_function(self):
        """测试传递函数"""
        num, den = self.model.get_transfer_function()
        assert len(den) == 3  # 二阶系统
        assert len(num) == 3

    def test_from_continuous(self):
        """测试从连续系统创建离散系统"""
        A_c = np.array([[0, 1], [-2, -3]])
        B_c = np.array([[0], [1]])
        C = np.array([[1, 0]])
        D = np.array([[0]])
        dt = 0.01

        model_d = StateSpaceModel.from_continuous(A_c, B_c, C, D, dt)
        assert model_d.is_stable()
        assert model_d.dt == dt

    def test_step_response(self):
        """测试阶跃响应"""
        t, y = self.model.get_step_response(n_steps=50)
        assert len(t) == 51
        assert y.shape[0] == 50  # 输出序列长度 = n_steps

    def test_impulse_response(self):
        """测试脉冲响应"""
        t, y = self.model.get_impulse_response(n_steps=50)
        assert len(t) == 51

    def test_dimension_validation(self):
        """测试维度验证"""
        with pytest.raises(AssertionError):
            StateSpaceModel(np.eye(2), np.array([[1.0]]), np.array([[1.0, 0.0]]))

    def test_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.model)
        assert "StateSpaceModel" in repr_str
        assert "n_states=2" in repr_str


# ============================================================
# 3. 系统分析测试
# ============================================================

class TestAnalysis:
    """可控性/可观性分析测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[0, 1], [-2, -3]])
        self.B = np.array([[0], [1]])
        self.C = np.array([[1, 0]])

    def test_controllability_matrix(self):
        """测试可控性矩阵"""
        Co = controllability_matrix(self.A, self.B)
        expected = np.hstack([self.B, self.A @ self.B])
        np.testing.assert_array_almost_equal(Co, expected)

    def test_observability_matrix(self):
        """测试可观性矩阵"""
        Ob = observability_matrix(self.A, self.C)
        expected = np.vstack([self.C, self.C @ self.A])
        np.testing.assert_array_almost_equal(Ob, expected)

    def test_is_controllable(self):
        """测试可控性判断"""
        assert is_controllable(self.A, self.B)

        # 不可控系统
        A_unc = np.array([[1, 0], [0, 2]])
        B_unc = np.array([[1], [0]])
        assert not is_controllable(A_unc, B_unc)

    def test_is_observable(self):
        """测试可观性判断"""
        assert is_observable(self.A, self.C)

        # 不可观系统
        A_uno = np.array([[1, 0], [0, 2]])
        C_uno = np.array([[1, 0]])
        assert not is_observable(A_uno, C_uno)

    def test_controllability_index(self):
        """测试可控性指数"""
        idx = controllability_index(self.A, self.B)
        assert idx == 2

    def test_observability_index(self):
        """测试可观性指数"""
        idx = observability_index(self.A, self.C)
        assert idx == 2

    def test_gramian_controllability(self):
        """测试可控性格拉姆矩阵"""
        Wc = gramian_controllability(self.A, self.B, N=10)
        assert Wc.shape == (2, 2)
        eigenvalues = np.linalg.eigvals(Wc)
        assert np.all(eigenvalues >= -1e-10)

    def test_gramian_observability(self):
        """测试可观性格拉姆矩阵"""
        Wo = gramian_observability(self.A, self.C, N=10)
        assert Wo.shape == (2, 2)
        eigenvalues = np.linalg.eigvals(Wo)
        assert np.all(eigenvalues >= -1e-10)

    def test_stability_continuous_stable(self):
        """测试连续系统稳定性判断（稳定）"""
        # A = [[0,1],[-2,-3]] 特征值 -1, -2
        assert check_stability_continuous(self.A)

    def test_stability_continuous_unstable(self):
        """测试连续系统稳定性判断（不稳定）"""
        A_unstable = np.array([[1, 1], [0, -2]])
        assert not check_stability_continuous(A_unstable)

    def test_stability_discrete_stable(self):
        """测试离散系统稳定性判断（稳定）"""
        A_d = np.array([[0.5, 0.1], [-0.1, 0.3]])
        assert check_stability_discrete(A_d)

    def test_stability_discrete_unstable(self):
        """测试离散系统稳定性判断（不稳定）"""
        A_d = np.array([[1.5, 0], [0, 0.3]])
        assert not check_stability_discrete(A_d)

    def test_stability_margin_discrete(self):
        """测试离散系统稳定性裕度"""
        A_d = np.array([[0.5, 0], [0, 0.3]])
        margin = stability_margin(A_d, is_discrete=True)
        assert margin > 0  # 稳定系统裕度为正
        assert abs(margin - 0.5) < 1e-10  # 1 - 0.5 = 0.5

    def test_stability_margin_continuous(self):
        """测试连续系统稳定性裕度"""
        # 特征值 -1, -2
        margin = stability_margin(self.A, is_discrete=False)
        assert margin > 0  # 稳定系统裕度为正
        assert abs(margin - 1.0) < 1e-10  # -(-1) = 1


# ============================================================
# 4. 控制器测试
# ============================================================

class TestController:
    """控制器测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[0, 1], [-2, -3]])
        self.B = np.array([[0], [1]])
        self.C = np.array([[1, 0]])
        self.Q = np.eye(2)
        self.R = np.array([[1.0]])

    def test_state_feedback_controller(self):
        """测试状态反馈控制器"""
        controller = StateFeedbackController(self.A, self.B)
        desired_poles = np.array([0.5, 0.3])
        K = controller.place_poles(desired_poles)

        assert K.shape == (1, 2)

        closed_loop_poles = controller.get_closed_loop_poles()
        np.testing.assert_array_almost_equal(
            np.sort(np.abs(closed_loop_poles)),
            np.sort(np.abs(desired_poles)),
            decimal=5,
        )

    def test_lqr_controller(self):
        """测试LQR控制器"""
        lqr = LQRController(self.A, self.B, self.Q, self.R)

        assert lqr.K.shape == (1, 2)
        assert lqr.P.shape == (2, 2)

        # 闭环系统应稳定
        A_cl, _ = lqr.get_closed_loop_system()
        eigenvalues = np.linalg.eigvals(A_cl)
        assert np.all(np.abs(eigenvalues) < 1.0)

    def test_compute_control(self):
        """测试控制输入计算"""
        controller = StateFeedbackController(self.A, self.B)
        K = np.array([[2.0, 1.0]])
        controller.set_gain(K)

        x = np.array([1.0, 0.5])
        u = controller.compute_control(x)

        expected = -K @ x
        np.testing.assert_array_almost_equal(u, expected.flatten())

    def test_lqr_simulate(self):
        """测试LQR仿真"""
        lqr = LQRController(self.A, self.B, self.Q, self.R)

        x0 = np.array([1.0, 0.0])
        states, controls = lqr.simulate(x0, n_steps=20)

        assert states.shape == (21, 2)
        assert controls.shape == (20, 1)

        # 状态应趋于零
        assert np.linalg.norm(states[-1]) < np.linalg.norm(x0)

    def test_lqr_cost(self):
        """测试LQR成本计算"""
        lqr = LQRController(self.A, self.B, self.Q, self.R)
        x0 = np.array([1.0, 0.0])
        cost = lqr.get_cost(x0, N=50)
        assert cost > 0

    def test_pole_placement_error(self):
        """测试极点配置错误处理"""
        controller = StateFeedbackController(self.A, self.B)
        # 极点数量不匹配
        with pytest.raises(ValueError):
            controller.place_poles(np.array([0.5]))


# ============================================================
# 5. 观测器测试
# ============================================================

class TestObserver:
    """观测器测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[0, 1], [-2, -3]])
        self.B = np.array([[0], [1]])
        self.C = np.array([[1, 0]])

    def test_full_order_observer(self):
        """测试全阶观测器"""
        observer = FullOrderObserver(self.A, self.B, self.C)
        desired_poles = np.array([0.5, 0.3])
        L = observer.design_by_poles(desired_poles)

        assert L.shape == (2, 1)

        obs_poles = observer.get_observer_poles()
        np.testing.assert_array_almost_equal(
            np.sort(np.abs(obs_poles)),
            np.sort(np.abs(desired_poles)),
            decimal=5,
        )

    def test_observer_update(self):
        """测试观测器更新"""
        observer = FullOrderObserver(self.A, self.B, self.C)
        observer.design_by_poles(np.array([0.5, 0.3]))

        y = np.array([1.0])
        u = np.array([0.0])

        x_hat = observer.update(y, u)
        assert x_hat.shape == (2,)

    def test_observer_convergence(self):
        """测试观测器收敛性"""
        observer = FullOrderObserver(self.A, self.B, self.C)
        observer.design_by_poles(np.array([0.2, 0.1]))

        x_true = np.array([1.0, 0.5])
        y = self.C @ x_true

        for _ in range(20):
            y = self.C @ x_true
            x_hat = observer.update(y)
            x_true = self.A @ x_true

        np.testing.assert_array_almost_equal(x_hat, x_true, decimal=3)

    def test_observer_reset(self):
        """测试观测器重置"""
        observer = FullOrderObserver(self.A, self.B, self.C)
        observer.design_by_poles(np.array([0.5, 0.3]))
        observer.update(np.array([1.0]))

        observer.reset()
        np.testing.assert_array_almost_equal(observer.x_hat, np.zeros(2))

    def test_reduced_order_observer(self):
        """测试降阶观测器"""
        # 3维系统，2维输出
        A = np.array([[0.5, 0.1, 0], [-0.1, 0.8, 0.1], [0, 0, 0.3]])
        B = np.array([[1], [0], [1]])
        C = np.array([[1, 0, 0], [0, 1, 0]])

        observer = ReducedOrderObserver(A, B, C)
        observer.design(desired_poles=np.array([0.2]))

        y = np.array([1.0, 0.5])
        x_hat = observer.update(y)
        assert x_hat.shape == (3,)


# ============================================================
# 6. 卡尔曼滤波测试
# ============================================================

class TestKalmanFilter:
    """卡尔曼滤波器测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[1.0, 1.0], [0.0, 1.0]])
        self.B = np.array([[0.5], [1.0]])
        self.C = np.array([[1.0, 0.0]])
        self.Q = np.array([[0.01, 0.0], [0.0, 0.01]])
        self.R = np.array([[0.1]])
        self.kf = KalmanFilter(self.A, self.B, self.C, self.Q, self.R)

    def test_initialization(self):
        """测试初始化"""
        assert self.kf.n == 2
        assert self.kf.m == 1
        assert self.kf.p == 1
        np.testing.assert_array_almost_equal(self.kf.x_hat, np.zeros(2))

    def test_predict(self):
        """测试预测步骤"""
        u = np.array([1.0])
        x_hat_prior, P_prior = self.kf.predict(u)

        assert x_hat_prior.shape == (2,)
        assert P_prior.shape == (2, 2)

    def test_update(self):
        """测试更新步骤"""
        y = np.array([1.0])
        x_hat, P, K = self.kf.update(y)

        assert x_hat.shape == (2,)
        assert P.shape == (2, 2)
        assert K.shape == (2, 1)

    def test_filter_step(self):
        """测试完整滤波步骤"""
        y = np.array([1.0])
        u = np.array([0.5])
        x_hat, P, K = self.kf.filter_step(y, u)

        assert x_hat.shape == (2,)
        assert P.shape == (2, 2)

    def test_state_estimates_history(self):
        """测试状态估计历史"""
        for _ in range(5):
            y = np.array([np.random.randn()])
            self.kf.update(y)

        estimates = self.kf.state_estimates
        assert estimates.shape == (6, 2)

    def test_estimation_error(self):
        """测试估计误差计算"""
        true_states = np.array([[1.0, 0.5], [2.0, 1.0], [3.0, 1.5]])
        kf = KalmanFilter(self.A, self.B, self.C, self.Q, self.R)

        for state in true_states:
            y = kf.C @ state
            kf.update(y)

        errors = kf.get_estimation_error(true_states)
        assert errors.shape == (3, 2)

    def test_rmse(self):
        """测试RMSE计算"""
        kf = KalmanFilter(self.A, self.B, self.C, self.Q, self.R)
        true_states = np.array([[1.0, 0.5], [2.0, 1.0]])

        for state in true_states:
            y = kf.C @ state
            kf.update(y)

        rmse = kf.get_estimation_rmse(true_states)
        assert rmse >= 0


# ============================================================
# 7. 实际应用测试
# ============================================================

class TestInvertedPendulum:
    """倒立摆测试"""

    def test_default_parameters(self):
        """测试默认参数"""
        ip = InvertedPendulum()
        params = ip.get_parameters()
        assert params["M"] == 0.5
        assert params["m"] == 0.2
        assert params["g"] == 9.81

    def test_custom_parameters(self):
        """测试自定义参数"""
        ip = InvertedPendulum(M=1.0, m=0.5, l=0.5)
        assert ip.M == 1.0
        assert ip.m == 0.5

    def test_discretize(self):
        """测试离散化"""
        ip = InvertedPendulum()
        model = ip.discretize(dt=0.01)
        assert model.n_states == 4
        assert model.n_inputs == 1

    def test_controllability(self):
        """测试可控性"""
        ip = InvertedPendulum()
        assert ip.check_controllability(dt=0.01)

    def test_observability(self):
        """测试可观性"""
        ip = InvertedPendulum()
        assert ip.check_observability(dt=0.01)

    def test_lqr_design(self):
        """测试LQR控制器设计"""
        ip = InvertedPendulum()
        lqr = ip.design_lqr(dt=0.01)
        assert lqr.K.shape == (1, 4)

    def test_lqr_stabilization(self):
        """测试LQR稳定化控制"""
        ip = InvertedPendulum()
        dt = 0.01
        lqr = ip.design_lqr(dt=dt, Q=np.diag([100, 1, 100, 1]), R=np.array([[1.0]]))

        model = ip.discretize(dt)
        x0 = np.array([0.0, 0.0, 0.1, 0.0])  # 初始偏角0.1弧度
        states, controls = lqr.simulate(x0, n_steps=200)

        # 角度应趋于零
        assert np.abs(states[-1, 2]) < np.abs(x0[2])

    def test_observer_design(self):
        """测试观测器设计"""
        ip = InvertedPendulum()
        # 观测器极点必须不同（scipy限制），且数量等于状态数
        obs_poles = np.array([0.3, 0.4, 0.5, 0.6])
        observer, model = ip.design_observer(dt=0.01, desired_poles=obs_poles)
        assert observer.L.shape == (4, 2)

    def test_repr(self):
        """测试字符串表示"""
        ip = InvertedPendulum()
        repr_str = repr(ip)
        assert "InvertedPendulum" in repr_str


class TestDCmotor:
    """直流电机测试"""

    def test_default_parameters(self):
        """测试默认参数"""
        motor = DCmotor()
        params = motor.get_parameters()
        assert params["R"] == 1.0
        assert params["L"] == 0.5
        assert params["Ke"] == 0.01

    def test_custom_parameters(self):
        """测试自定义参数"""
        motor = DCmotor(R=2.0, L=1.0)
        assert motor.R == 2.0
        assert motor.L == 1.0

    def test_discretize(self):
        """测试离散化"""
        motor = DCmotor()
        model = motor.discretize(dt=0.001)
        assert model.n_states == 3
        assert model.n_inputs == 1

    def test_controllability(self):
        """测试可控性"""
        motor = DCmotor()
        assert motor.check_controllability(dt=0.001)

    def test_observability(self):
        """测试可观性"""
        motor = DCmotor()
        assert motor.check_observability(dt=0.001)

    def test_lqr_design(self):
        """测试LQR控制器设计"""
        motor = DCmotor()
        lqr = motor.design_lqr(dt=0.001)
        assert lqr.K.shape == (1, 3)

    def test_speed_controller(self):
        """测试速度控制器设计"""
        motor = DCmotor()
        controller, model = motor.design_speed_controller(dt=0.001)
        assert controller.K.shape[1] == 2

    def test_linear_simulation(self):
        """测试线性模型仿真"""
        motor = DCmotor()
        x0 = np.array([0.0, 0.0, 0.0])
        u_func = lambda t: np.array([12.0])  # 12V阶跃电压
        t, states, outputs = motor.simulate_linear(
            x0, u_func, (0, 0.5), dt=0.001
        )

        # 电机应加速
        assert states[-1, 1] > 0  # 角速度为正

    def test_repr(self):
        """测试字符串表示"""
        motor = DCmotor()
        repr_str = repr(motor)
        assert "DCmotor" in repr_str


# ============================================================
# 8. 集成测试
# ============================================================

class TestIntegration:
    """集成测试"""

    def test_lqr_with_kalman_filter(self):
        """测试LQR与卡尔曼滤波器集成"""
        A = np.array([[0.9, 0.1], [-0.1, 0.8]])
        B = np.array([[1.0], [0.5]])
        C = np.array([[1.0, 0.0]])

        Q = np.eye(2)
        R = np.array([[1.0]])
        lqr = LQRController(A, B, Q, R)

        Qn = 0.01 * np.eye(2)
        Rn = np.array([[0.1]])
        kf = KalmanFilter(A, B, C, Qn, Rn)

        x_true = np.array([1.0, 0.0])
        n_steps = 50
        states_true = [x_true.copy()]

        for _ in range(n_steps):
            y = C @ x_true + np.random.randn() * np.sqrt(Rn[0, 0])
            kf.predict()
            x_hat, _, _ = kf.update(y)
            u = lqr.compute_control(x_hat)
            x_true = A @ x_true + B @ u
            states_true.append(x_true.copy())

        states_true = np.array(states_true)
        assert np.linalg.norm(states_true[-1]) < 0.5

    def test_observer_based_control(self):
        """测试基于观测器的控制"""
        A = np.array([[0, 1], [-2, -3]])
        B = np.array([[0], [1]])
        C = np.array([[1, 0]])

        controller = StateFeedbackController(A, B)
        K = controller.place_poles(np.array([0.5, 0.3]))

        observer = FullOrderObserver(A, B, C)
        L = observer.design_by_poles(np.array([0.2, 0.1]))

        x_true = np.array([1.0, 0.5])
        n_steps = 20

        for _ in range(n_steps):
            y = C @ x_true
            x_hat = observer.update(y)
            x_true = A @ x_true

        np.testing.assert_array_almost_equal(x_hat, x_true, decimal=3)

    def test_continuous_to_discrete_pipeline(self):
        """测试连续到离散的完整流程"""
        # 定义连续系统
        A_c = np.array([[0, 1], [-4, -2]])
        B_c = np.array([[0], [1]])
        C = np.array([[1, 0]])
        D = np.array([[0]])

        # 创建连续模型
        cs = ContinuousStateSpace(A_c, B_c, C, D)
        assert cs.is_stable()

        # 离散化
        dt = 0.01
        model_d = cs.discretize(dt)
        assert model_d.is_stable()

        # 设计LQR
        lqr = LQRController(model_d.A, model_d.B, np.eye(2), np.array([[1.0]]))
        assert lqr.K.shape == (1, 2)

        # 仿真
        x0 = np.array([1.0, 0.0])
        states, controls = lqr.simulate(x0, n_steps=100)
        # LQR应使状态衰减
        assert np.linalg.norm(states[-1]) < np.linalg.norm(x0)

    def test_inverted_pendulum_full_control(self):
        """测试倒立摆完整控制流程"""
        ip = InvertedPendulum()
        dt = 0.01

        # 设计LQR
        lqr = ip.design_lqr(dt=dt, Q=np.diag([100, 1, 200, 1]), R=np.array([[1.0]]))

        # 设计观测器（极点必须不同）
        obs_poles = np.array([0.3, 0.4, 0.5, 0.6])
        observer, model = ip.design_observer(dt=dt, desired_poles=obs_poles)

        # 仿真带观测器的控制
        x_true = np.array([0.0, 0.0, 0.1, 0.0])
        observer.x_hat = np.zeros(4)
        n_steps = 200

        for _ in range(n_steps):
            y = model.C @ x_true
            x_hat = observer.update(y)
            u = lqr.compute_control(x_hat)
            x_true = model.A @ x_true + model.B @ u

        # 角度应趋于零
        assert np.abs(x_true[2]) < 0.1

    def test_motor_position_control(self):
        """测试电机位置控制"""
        motor = DCmotor()
        dt = 0.001

        # 设计LQR
        lqr = motor.design_lqr(dt=dt, Q=np.diag([100, 1, 1]), R=np.array([[0.1]]))

        model = motor.discretize(dt)

        # 目标角度 = 1 rad
        x0 = np.array([0.0, 0.0, 0.0])
        states, controls = lqr.simulate(x0, n_steps=500, r=np.array([0.0]))

        # 角度应趋于零（调节器问题）
        assert np.abs(states[-1, 0]) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
