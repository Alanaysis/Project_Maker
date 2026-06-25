"""
被控对象模型

实现用于仿真测试的被控对象模型。

支持的模型类型：
- 一阶惯性环节
- 二阶系统
- 非线性系统
- 带扰动的系统
"""

import numpy as np
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum


class PlantType(Enum):
    """被控对象类型"""
    FIRST_ORDER = "first_order"
    SECOND_ORDER = "second_order"
    NONLINEAR = "nonlinear"
    TIME_VARYING = "time_varying"


@dataclass
class PlantParameters:
    """被控对象参数"""
    # 一阶系统: ẏ = -a * y + b * u
    a: float = 2.0  # 系统极点 (正数表示稳定系统)
    b: float = 1.0  # 系统增益

    # 二阶系统: ÿ + 2ζω_n * ẏ + ω_n^2 * y = ω_n^2 * u
    omega_n: float = 1.0  # 自然频率
    zeta: float = 0.5  # 阻尼比

    # 扰动
    disturbance_amplitude: float = 0.0
    disturbance_frequency: float = 0.0

    # 噪声
    noise_std: float = 0.0


class PlantModel:
    """
    被控对象模型

    模拟被控系统的动态行为。

    参数：
        plant_type: 系统类型
        params: 系统参数
        initial_output: 初始输出
    """

    def __init__(
        self,
        plant_type: PlantType = PlantType.FIRST_ORDER,
        params: Optional[PlantParameters] = None,
        initial_output: float = 0.0,
    ):
        self.plant_type = plant_type
        self.params = params or PlantParameters()
        self.y = initial_output  # 输出
        self.dy = 0.0  # 输出导数
        self.time = 0.0

        # 状态历史
        self._history: List[dict] = []

        # 二阶系统需要额外状态
        if plant_type == PlantType.SECOND_ORDER:
            self._prev_y = initial_output
            self._prev_dy = 0.0

    def update(self, control_input: float, dt: float) -> float:
        """
        更新被控对象状态

        参数：
            control_input: 控制输入 u(t)
            dt: 时间步长

        返回：
            系统输出 y(t)
        """
        # 添加扰动
        disturbance = self._compute_disturbance()

        # 添加噪声
        noise = np.random.normal(0, self.params.noise_std) if self.params.noise_std > 0 else 0

        if self.plant_type == PlantType.FIRST_ORDER:
            self._update_first_order(control_input, disturbance, dt)
        elif self.plant_type == PlantType.SECOND_ORDER:
            self._update_second_order(control_input, disturbance, dt)
        elif self.plant_type == PlantType.NONLINEAR:
            self._update_nonlinear(control_input, disturbance, dt)
        elif self.plant_type == PlantType.TIME_VARYING:
            self._update_time_varying(control_input, disturbance, dt)

        # 添加噪声到输出
        measured_output = self.y + noise

        self.time += dt

        # 记录历史
        self._history.append({
            "time": self.time,
            "output": self.y,
            "measured_output": measured_output,
            "derivative": self.dy,
            "input": control_input,
            "disturbance": disturbance,
        })

        return measured_output

    def _update_first_order(self, u: float, d: float, dt: float):
        """
        一阶系统: ẏ = -a * y + b * u + d

        解析解: y(t) = (b/a) * u + (y(0) - b/a * u) * exp(-a * t)
        """
        a = self.params.a
        b = self.params.b

        self.dy = -a * self.y + b * u + d
        self.y += self.dy * dt

    def _update_second_order(self, u: float, d: float, dt: float):
        """
        二阶系统: ÿ + 2ζω_n * ẏ + ω_n^2 * y = ω_n^2 * u + d

        状态空间:
        x1 = y
        x2 = ẏ
        ẋ1 = x2
        ẋ2 = -ω_n^2 * x1 - 2ζω_n * x2 + ω_n^2 * u + d
        """
        omega_n = self.params.omega_n
        zeta = self.params.zeta

        x1 = self.y
        x2 = self.dy

        # RK4 积分
        k1_x1 = x2
        k1_x2 = -omega_n**2 * x1 - 2 * zeta * omega_n * x2 + omega_n**2 * u + d

        k2_x1 = x2 + 0.5 * dt * k1_x2
        k2_x2 = -omega_n**2 * (x1 + 0.5 * dt * k1_x1) - 2 * zeta * omega_n * (x2 + 0.5 * dt * k1_x2) + omega_n**2 * u + d

        k3_x1 = x2 + 0.5 * dt * k2_x2
        k3_x2 = -omega_n**2 * (x1 + 0.5 * dt * k2_x1) - 2 * zeta * omega_n * (x2 + 0.5 * dt * k2_x2) + omega_n**2 * u + d

        k4_x1 = x2 + dt * k3_x2
        k4_x2 = -omega_n**2 * (x1 + dt * k3_x1) - 2 * zeta * omega_n * (x2 + dt * k3_x2) + omega_n**2 * u + d

        self.y += (dt / 6.0) * (k1_x1 + 2 * k2_x1 + 2 * k3_x1 + k4_x1)
        self.dy += (dt / 6.0) * (k1_x2 + 2 * k2_x2 + 2 * k3_x2 + k4_x2)

    def _update_nonlinear(self, u: float, d: float, dt: float):
        """
        非线性系统: ẏ = -a * y + b * tanh(u) + c * y^2 * sin(t) + d
        """
        a = self.params.a
        b = self.params.b
        c = 0.1  # 非线性系数

        # 添加非线性项
        nonlinear_term = c * self.y**2 * np.sin(self.time)

        self.dy = -a * self.y + b * np.tanh(u) + nonlinear_term + d
        self.y += self.dy * dt

    def _update_time_varying(self, u: float, d: float, dt: float):
        """
        时变系统: ẏ = -a(t) * y + b(t) * u + d

        参数随时间缓慢变化
        """
        # 参数随时间变化
        a_t = self.params.a * (1 + 0.2 * np.sin(0.5 * self.time))
        b_t = self.params.b * (1 + 0.1 * np.cos(0.3 * self.time))

        self.dy = -a_t * self.y + b_t * u + d
        self.y += self.dy * dt

    def _compute_disturbance(self) -> float:
        """计算扰动"""
        amp = self.params.disturbance_amplitude
        freq = self.params.disturbance_frequency

        if amp > 0 and freq > 0:
            return amp * np.sin(2 * np.pi * freq * self.time)
        return 0.0

    def get_output(self) -> float:
        """获取当前输出"""
        return self.y

    def get_history(self) -> List[dict]:
        """获取历史记录"""
        return self._history.copy()

    def reset(self):
        """重置系统状态"""
        self.y = 0.0
        self.dy = 0.0
        self.time = 0.0
        self._history.clear()


def create_first_order_plant(
    time_constant: float = 0.5,
    gain: float = 1.0,
    noise_std: float = 0.0,
) -> PlantModel:
    """
    创建一阶被控对象

    参数：
        time_constant: 时间常数
        gain: 系统增益
        noise_std: 测量噪声标准差
    """
    a = 1.0 / time_constant
    b = gain * a
    params = PlantParameters(a=a, b=b, noise_std=noise_std)
    return PlantModel(PlantType.FIRST_ORDER, params)


def create_second_order_plant(
    natural_frequency: float = 1.0,
    damping_ratio: float = 0.5,
    noise_std: float = 0.0,
) -> PlantModel:
    """
    创建二阶被控对象

    参数：
        natural_frequency: 自然频率
        damping_ratio: 阻尼比
        noise_std: 测量噪声标准差
    """
    params = PlantParameters(
        omega_n=natural_frequency,
        zeta=damping_ratio,
        noise_std=noise_std
    )
    return PlantModel(PlantType.SECOND_ORDER, params)


def create_nonlinear_plant(
    a: float = 1.0,
    b: float = 1.0,
    noise_std: float = 0.0,
) -> PlantModel:
    """
    创建非线性被控对象

    参数：
        a: 线性项系数
        b: 非线性增益
        noise_std: 测量噪声标准差
    """
    params = PlantParameters(a=a, b=b, noise_std=noise_std)
    return PlantModel(PlantType.NONLINEAR, params)
