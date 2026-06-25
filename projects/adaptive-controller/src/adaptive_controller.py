"""
模型参考自适应控制器 (MRAC) 和自校正控制器 (STR)

实现 MIT 规则、Lyapunov 方法和自校正控制算法。

核心思想：
- 定义参考模型描述期望的闭环行为
- 通过自适应律调整控制器参数
- 使被控对象输出跟踪参考模型输出
- 在线估计系统参数并设计控制器
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .reference_model import ReferenceModel
from .parameter_estimator import ParameterEstimator


class AdaptationLaw(Enum):
    """自适应律类型"""
    MIT = "mit"  # MIT 规则
    LYAPUNOV = "lyapunov"  # Lyapunov 方法


@dataclass
class ControllerState:
    """控制器状态"""
    time: float = 0.0
    reference_output: float = 0.0
    plant_output: float = 0.0
    control_signal: float = 0.0
    tracking_error: float = 0.0
    parameters: dict = field(default_factory=dict)


class MRACController:
    """
    模型参考自适应控制器

    实现自适应控制律，使被控对象输出跟踪参考模型输出。

    参数：
        reference_model: 参考模型
        adaptation_law: 自适应律类型 (MIT 或 Lyapunov)
        adaptation_gain: 自适应增益 (影响参数调整速度)
        initial_params: 初始控制器参数
    """

    def __init__(
        self,
        reference_model: ReferenceModel,
        adaptation_law: AdaptationLaw = AdaptationLaw.LYAPUNOV,
        adaptation_gain: float = 0.1,
        initial_params: Optional[dict] = None,
    ):
        self.reference_model = reference_model
        self.adaptation_law = adaptation_law
        self.gamma = adaptation_gain  # 自适应增益

        # 控制器参数 (可调整)
        default_params = {
            "theta_r": 0.0,  # 前馈增益
            "theta_x": np.array([0.0]),  # 状态反馈增益
            "theta_d": 0.0,  # 扰动补偿
        }
        self.params = initial_params or default_params

        # 参数估计器
        self.estimator = ParameterEstimator(
            n_params=len(self._flatten_params()),
            adaptation_gain=adaptation_gain
        )

        # 状态历史
        self.history: list[ControllerState] = []

        # 内部状态
        self._integral_error = 0.0

    def _flatten_params(self) -> np.ndarray:
        """将参数展平为向量"""
        result = []
        for v in self.params.values():
            if isinstance(v, np.ndarray):
                result.extend(v.tolist())
            else:
                result.append(v)
        return np.array(result)

    def _unflatten_params(self, flat: np.ndarray) -> dict:
        """将向量恢复为参数字典"""
        idx = 0
        result = {}
        for k, v in self.params.items():
            if isinstance(v, np.ndarray):
                n = len(v)
                result[k] = flat[idx:idx + n]
                idx += n
            else:
                result[k] = flat[idx]
                idx += 1
        return result

    def compute_control(
        self,
        reference_input: float,
        plant_output: float,
        dt: float,
    ) -> float:
        """
        计算控制信号

        参数：
            reference_input: 参考输入 r(t)
            plant_output: 被控对象输出 y(t)
            dt: 时间步长

        返回：
            控制信号 u(t)
        """
        # 计算参考模型输出
        y_m = self.reference_model.update(reference_input, dt)

        # 计算跟踪误差
        e = plant_output - y_m

        # 更新积分误差
        self._integral_error += e * dt

        # 根据自适应律更新参数
        if self.adaptation_law == AdaptationLaw.MIT:
            self._mit_update(e, reference_input, plant_output, dt)
        else:  # Lyapunov
            self._lyapunov_update(e, reference_input, plant_output, dt)

        # 计算控制信号
        u = self._compute_control_signal(reference_input, plant_output, e)

        # 记录状态
        state = ControllerState(
            time=self.reference_model.time,
            reference_output=y_m,
            plant_output=plant_output,
            control_signal=u,
            tracking_error=e,
            parameters=dict(self.params),
        )
        self.history.append(state)

        return u

    def _compute_control_signal(
        self,
        r: float,
        y: float,
        e: float,
    ) -> float:
        """
        计算控制律 u = theta_r * r - theta_x * y + theta_d

        参数：
            r: 参考输入
            y: 被控对象输出
            e: 跟踪误差
        """
        theta_r = self.params.get("theta_r", 0.0)
        theta_x = self.params.get("theta_x", np.array([0.0]))
        theta_d = self.params.get("theta_d", 0.0)

        # 前馈 + 反馈 + 扰动补偿
        u = theta_r * r - np.sum(theta_x * y) + theta_d

        return u

    def _mit_update(
        self,
        e: float,
        r: float,
        y: float,
        dt: float,
    ):
        """
        MIT 规则自适应律

        基于梯度下降最小化误差平方:
        J = 0.5 * e^2
        dθ/dt = -γ * ∂J/∂θ = -γ * e * ∂e/∂θ

        使用灵敏度导数计算梯度：
        对于 u = θ_r * r - θ_x * y + θ_d
        ∂u/∂θ_r = r,  ∂u/∂θ_x = -y,  ∂u/∂θ_d = 1
        通过被控对象传递函数近似: ∂e/∂θ ≈ b * ∂u/∂θ

        参数：
            e: 跟踪误差
            r: 参考输入
            y: 被控对象输出
            dt: 时间步长
        """
        # 灵敏度导数: ∂e/∂θ
        # 对于 u = θ_r * r - θ_x * y + θ_d
        # ∂e/∂θ_r ≈ -r, ∂e/∂θ_x ≈ y, ∂e/∂θ_d ≈ -1
        grad_r = e * (-r)
        grad_x = e * y
        grad_d = e * (-1.0)

        # 梯度下降更新: θ = θ - γ * ∂J/∂θ = θ - γ * e * ∂e/∂θ
        self.params["theta_r"] -= self.gamma * grad_r * dt
        if isinstance(self.params["theta_x"], np.ndarray):
            self.params["theta_x"] -= self.gamma * grad_x * dt
        else:
            self.params["theta_x"] -= self.gamma * grad_x * dt
        self.params["theta_d"] -= self.gamma * grad_d * dt

    def _lyapunov_update(
        self,
        e: float,
        r: float,
        y: float,
        dt: float,
    ):
        """
        Lyapunov 方法自适应律

        基于 Lyapunov 稳定性理论:
        V = 0.5 * e^2 + 0.5 * (θ - θ*)^T * Γ^{-1} * (θ - θ*)
        dθ/dt = -Γ * e * φ(x)

        参数：
            e: 跟踪误差
            r: 参考输入
            y: 被控对象输出
            dt: 时间步长
        """
        # 回归向量 φ(x) = [r, -y, 1]^T
        phi = np.array([r, -y, 1.0])

        # Lyapunov 自适应律: dθ/dt = -Γ * e * φ
        grad = self.gamma * e * phi

        # 更新参数
        self.params["theta_r"] -= grad[0] * dt
        if isinstance(self.params["theta_x"], np.ndarray):
            self.params["theta_x"] -= grad[1] * dt
        else:
            self.params["theta_x"] -= grad[1] * dt
        self.params["theta_d"] -= grad[2] * dt

    def get_tracking_error_history(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取跟踪误差历史"""
        times = np.array([s.time for s in self.history])
        errors = np.array([s.tracking_error for s in self.history])
        return times, errors

    def get_parameter_history(self) -> Tuple[np.ndarray, dict]:
        """获取参数历史"""
        times = np.array([s.time for s in self.history])
        param_history = {}
        for key in self.params.keys():
            if isinstance(self.params[key], np.ndarray):
                param_history[key] = np.array([s.parameters[key] for s in self.history])
            else:
                param_history[key] = np.array([s.parameters[key] for s in self.history])
        return times, param_history

    def reset(self):
        """重置控制器状态"""
        self.history.clear()
        self._integral_error = 0.0
        self.reference_model.reset()


class SelfTuningController:
    """
    自校正控制器 (Self-Tuning Regulator, STR)

    结合在线参数估计和控制器设计，实现自校正控制。

    工作原理：
    1. 使用参数估计器在线估计被控对象参数
    2. 根据估计参数设计控制器 (极点配置)
    3. 应用控制信号
    4. 重复以上步骤

    参数：
        n_params: 系统参数数量
        desired_poles: 期望闭环极点
        estimation_method: 参数估计方法 ("rls", "gradient", "forgetting_factor")
        forgetting_factor: 遗忘因子
        adaptation_gain: 自适应增益
    """

    def __init__(
        self,
        n_params: int = 2,
        desired_poles: Optional[list] = None,
        estimation_method: str = "rls",
        forgetting_factor: float = 0.98,
        adaptation_gain: float = 0.1,
    ):
        self.n_params = n_params

        # 期望闭环极点
        self.desired_poles = desired_poles or [0.5]

        # 参数估计器
        from .parameter_estimator import EstimationMethod
        method_map = {
            "rls": EstimationMethod.RLS,
            "gradient": EstimationMethod.GRADIENT,
            "forgetting_factor": EstimationMethod.FORGETTING_FACTOR,
        }
        self.estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=method_map.get(estimation_method, EstimationMethod.RLS),
            adaptation_gain=adaptation_gain,
            forgetting_factor=forgetting_factor,
        )

        # 估计的系统参数
        self.estimated_params = np.zeros(n_params)

        # 控制器增益
        self.controller_gains = np.zeros(n_params)

        # 状态历史
        self.history: list[dict] = []
        self._time = 0.0

    def compute_control(
        self,
        reference_input: float,
        plant_output: float,
        dt: float,
        regression_vector: Optional[np.ndarray] = None,
    ) -> float:
        """
        计算控制信号

        参数：
            reference_input: 参考输入 r(t)
            plant_output: 被控对象输出 y(t)
            dt: 时间步长
            regression_vector: 回归向量 (如果为 None，使用默认构造)

        返回：
            控制信号 u(t)
        """
        # 构造回归向量
        if regression_vector is None:
            regression_vector = np.array([reference_input, -plant_output])
            if len(regression_vector) < self.n_params:
                regression_vector = np.pad(
                    regression_vector,
                    (0, self.n_params - len(regression_vector))
                )

        # 更新参数估计
        self.estimated_params, estimation_error = self.estimator.update(
            regression_vector, plant_output, dt
        )

        # 根据估计参数设计控制器增益 (极点配置)
        self._design_controller()

        # 计算控制信号
        u = self._compute_control_signal(reference_input, plant_output)

        self._time += dt

        # 记录历史
        self.history.append({
            "time": self._time,
            "reference": reference_input,
            "output": plant_output,
            "control": u,
            "estimation_error": estimation_error,
            "estimated_params": self.estimated_params.copy(),
            "controller_gains": self.controller_gains.copy(),
        })

        return u

    def _design_controller(self):
        """
        根据估计参数设计控制器

        使用极点配置方法：
        对于一阶系统 y = a*y + b*u
        期望闭环极点为 p
        控制律: u = (p - a_hat) / b_hat * r - (a_hat + p) / b_hat * y

        对于高阶系统，使用 Ackermann 公式
        """
        params = self.estimated_params

        if len(params) >= 2:
            # 假设参数为 [a, b] (系统矩阵和输入增益)
            a_hat = params[0]
            b_hat = params[1]

            # 避免除零
            if abs(b_hat) < 1e-6:
                b_hat = 0.1

            # 极点配置
            p = self.desired_poles[0] if self.desired_poles else 0.5

            # 前馈增益: theta_r = (p - a_hat) / b_hat
            self.controller_gains[0] = (p - a_hat) / b_hat

            # 反馈增益: theta_x = -(a_hat + p) / b_hat
            if len(self.controller_gains) > 1:
                self.controller_gains[1] = -(a_hat + p) / b_hat

    def _compute_control_signal(
        self,
        r: float,
        y: float,
    ) -> float:
        """
        计算控制信号

        u = theta_r * r + theta_x * y

        参数：
            r: 参考输入
            y: 被控对象输出
        """
        u = 0.0

        # 前馈
        if len(self.controller_gains) > 0:
            u += self.controller_gains[0] * r

        # 反馈
        if len(self.controller_gains) > 1:
            u += self.controller_gains[1] * y

        return u

    def get_parameter_estimates(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取参数估计历史

        返回：
            时间数组和参数估计数组
        """
        times = np.array([h["time"] for h in self.history])
        params = np.array([h["estimated_params"] for h in self.history])
        return times, params

    def get_controller_gains(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取控制器增益历史

        返回：
            时间数组和增益数组
        """
        times = np.array([h["time"] for h in self.history])
        gains = np.array([h["controller_gains"] for h in self.history])
        return times, gains

    def get_estimation_errors(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取估计误差历史

        返回：
            时间数组和误差数组
        """
        times = np.array([h["time"] for h in self.history])
        errors = np.array([h["estimation_error"] for h in self.history])
        return times, errors

    def reset(self):
        """重置控制器状态"""
        self.estimator.reset()
        self.estimated_params = np.zeros(self.n_params)
        self.controller_gains = np.zeros(self.n_params)
        self.history.clear()
        self._time = 0.0
