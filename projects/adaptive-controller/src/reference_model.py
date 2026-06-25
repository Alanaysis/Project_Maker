"""
参考模型

定义自适应控制系统中期望的闭环行为。
参考模型描述了理想的系统响应特性。

常见参考模型：
- 一阶系统: y_m = (a_m * y_m + b_m * r) / (s + a_m)
- 二阶系统: y_m = ω_n^2 / (s^2 + 2ζω_n*s + ω_n^2) * r
"""

import numpy as np
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ModelOrder(Enum):
    """模型阶次"""
    FIRST_ORDER = 1
    SECOND_ORDER = 2


@dataclass
class ModelParameters:
    """模型参数"""
    # 一阶模型: ẏ_m = -a_m * y_m + b_m * r
    a_m: float = 1.0  # 闭环极点位置 (应为负值以保证稳定)
    b_m: float = 1.0  # 前馈增益

    # 二阶模型参数
    omega_n: float = 1.0  # 自然频率
    zeta: float = 0.7  # 阻尼比


class ReferenceModel:
    """
    参考模型

    定义期望的闭环系统行为，用于自适应控制器。

    参数：
        model_order: 模型阶次 (一阶或二阶)
        params: 模型参数
        initial_output: 初始输出值
    """

    def __init__(
        self,
        model_order: ModelOrder = ModelOrder.FIRST_ORDER,
        params: Optional[ModelParameters] = None,
        initial_output: float = 0.0,
    ):
        self.model_order = model_order
        self.params = params or ModelParameters()
        self.y_m = initial_output  # 参考模型输出
        self.dy_m = 0.0  # 输出导数
        self.time = 0.0

        # 状态历史
        self._history: List[dict] = []

        # 二阶模型需要额外状态
        if model_order == ModelOrder.SECOND_ORDER:
            self._prev_y_m = initial_output
            self._prev_dy_m = 0.0

    def update(self, reference_input: float, dt: float) -> float:
        """
        更新参考模型输出

        参数：
            reference_input: 参考输入 r(t)
            dt: 时间步长

        返回：
            参考模型输出 y_m(t)
        """
        if self.model_order == ModelOrder.FIRST_ORDER:
            self._update_first_order(reference_input, dt)
        else:
            self._update_second_order(reference_input, dt)

        self.time += dt

        # 记录历史
        self._history.append({
            "time": self.time,
            "output": self.y_m,
            "derivative": self.dy_m,
            "input": reference_input,
        })

        return self.y_m

    def _update_first_order(self, r: float, dt: float):
        """
        一阶参考模型: ẏ_m = -a_m * y_m + b_m * r

        解析解: y_m(t) = (b_m/a_m) * r + (y_m(0) - b_m/a_m * r) * exp(-a_m * t)
        """
        a_m = self.params.a_m
        b_m = self.params.b_m

        # 使用欧拉法更新
        self.dy_m = -a_m * self.y_m + b_m * r
        self.y_m += self.dy_m * dt

    def _update_second_order(self, r: float, dt: float):
        """
        二阶参考模型: ÿ_m + 2ζω_n * ẏ_m + ω_n^2 * y_m = ω_n^2 * r

        转换为状态空间:
        x1 = y_m
        x2 = ẏ_m
        ẋ1 = x2
        ẋ2 = -ω_n^2 * x1 - 2ζω_n * x2 + ω_n^2 * r
        """
        omega_n = self.params.omega_n
        zeta = self.params.zeta

        # 状态空间更新 (RK4 方法)
        x1 = self.y_m
        x2 = self.dy_m

        # RK4 积分
        k1_x1 = x2
        k1_x2 = -omega_n**2 * x1 - 2 * zeta * omega_n * x2 + omega_n**2 * r

        k2_x1 = x2 + 0.5 * dt * k1_x2
        k2_x2 = -omega_n**2 * (x1 + 0.5 * dt * k1_x1) - 2 * zeta * omega_n * (x2 + 0.5 * dt * k1_x2) + omega_n**2 * r

        k3_x1 = x2 + 0.5 * dt * k2_x2
        k3_x2 = -omega_n**2 * (x1 + 0.5 * dt * k2_x1) - 2 * zeta * omega_n * (x2 + 0.5 * dt * k2_x2) + omega_n**2 * r

        k4_x1 = x2 + dt * k3_x2
        k4_x2 = -omega_n**2 * (x1 + dt * k3_x1) - 2 * zeta * omega_n * (x2 + dt * k3_x2) + omega_n**2 * r

        # 更新状态
        self.y_m += (dt / 6.0) * (k1_x1 + 2 * k2_x1 + 2 * k3_x1 + k4_x1)
        self.dy_m += (dt / 6.0) * (k1_x2 + 2 * k2_x2 + 2 * k3_x2 + k4_x2)

    def get_output(self) -> float:
        """获取当前输出"""
        return self.y_m

    def get_derivative(self) -> float:
        """获取输出导数"""
        return self.dy_m

    def get_history(self) -> List[dict]:
        """获取历史记录"""
        return self._history.copy()

    def get_state(self) -> dict:
        """获取当前状态"""
        return {
            "time": self.time,
            "output": self.y_m,
            "derivative": self.dy_m,
        }

    def reset(self):
        """重置模型状态"""
        self.y_m = 0.0
        self.dy_m = 0.0
        self.time = 0.0
        self._history.clear()


def create_first_order_model(
    time_constant: float = 1.0,
    steady_state_gain: float = 1.0,
) -> ReferenceModel:
    """
    创建一阶参考模型

    参数：
        time_constant: 时间常数 (越大响应越慢)
        steady_state_gain: 稳态增益

    返回：
        一阶参考模型实例
    """
    a_m = 1.0 / time_constant
    b_m = steady_state_gain * a_m
    params = ModelParameters(a_m=a_m, b_m=b_m)
    return ReferenceModel(ModelOrder.FIRST_ORDER, params)


def create_second_order_model(
    natural_frequency: float = 1.0,
    damping_ratio: float = 0.7,
) -> ReferenceModel:
    """
    创建二阶参考模型

    参数：
        natural_frequency: 自然频率 (越大响应越快)
        damping_ratio: 阻尼比 (0.7 左右为临界阻尼)

    返回：
        二阶参考模型实例
    """
    params = ModelParameters(omega_n=natural_frequency, zeta=damping_ratio)
    return ReferenceModel(ModelOrder.SECOND_ORDER, params)
