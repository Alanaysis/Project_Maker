"""
仿真引擎

提供自适应控制系统的仿真环境。

支持功能：
- 单次仿真运行
- 参数扫描
- 蒙特卡洛仿真
- 扰动测试
"""

import numpy as np
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .adaptive_controller import MRACController
from .reference_model import ReferenceModel, ModelOrder, ModelParameters
from .plant_model import PlantModel, PlantType, PlantParameters
from .analyzer import PerformanceAnalyzer


class ReferenceSignal(Enum):
    """参考信号类型"""
    STEP = "step"
    SINE = "sine"
    SQUARE = "square"
    RAMP = "ramp"
    CUSTOM = "custom"


@dataclass
class SimulationConfig:
    """仿真配置"""
    duration: float = 10.0  # 仿真时长 (秒)
    dt: float = 0.01  # 时间步长
    reference_type: ReferenceSignal = ReferenceSignal.STEP
    reference_amplitude: float = 1.0  # 参考信号幅度
    reference_frequency: float = 1.0  # 参考信号频率 (用于正弦)
    ramp_rate: float = 1.0  # 斜坡信号斜率
    custom_reference: Optional[Callable[[float], float]] = None


@dataclass
class SimulationResult:
    """仿真结果"""
    times: np.ndarray
    reference_signal: np.ndarray
    reference_model_output: np.ndarray
    plant_output: np.ndarray
    control_signal: np.ndarray
    tracking_error: np.ndarray
    parameter_history: Dict[str, np.ndarray]
    metrics: Dict[str, float]


class SimulationEngine:
    """
    仿真引擎

    运行自适应控制系统的仿真。

    参数：
        controller: 自适应控制器
        plant: 被控对象
        config: 仿真配置
    """

    def __init__(
        self,
        controller: MRACController,
        plant: PlantModel,
        config: Optional[SimulationConfig] = None,
    ):
        self.controller = controller
        self.plant = plant
        self.config = config or SimulationConfig()

    def run(self) -> SimulationResult:
        """
        运行仿真

        返回：
            仿真结果
        """
        dt = self.config.dt
        duration = self.config.duration
        n_steps = int(duration / dt)

        # 初始化记录数组
        times = np.zeros(n_steps)
        ref_signal = np.zeros(n_steps)
        ref_output = np.zeros(n_steps)
        plant_output = np.zeros(n_steps)
        control_signal = np.zeros(n_steps)
        tracking_error = np.zeros(n_steps)

        # 重置控制器和被控对象
        self.controller.reset()
        self.plant.reset()

        # 运行仿真循环
        for i in range(n_steps):
            t = i * dt

            # 生成参考信号
            r = self._generate_reference(t)

            # 获取当前被控对象输出
            y = self.plant.get_output()

            # 计算控制信号
            u = self.controller.compute_control(r, y, dt)

            # 更新被控对象
            y_new = self.plant.update(u, dt)

            # 获取参考模型输出
            y_m = self.controller.reference_model.get_output()

            # 记录数据
            times[i] = t
            ref_signal[i] = r
            ref_output[i] = y_m
            plant_output[i] = y_new
            control_signal[i] = u
            tracking_error[i] = y_new - y_m

        # 获取参数历史
        _, param_history = self.controller.get_parameter_history()

        # 计算性能指标
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.compute_metrics(
            times=times,
            reference=ref_output,
            actual=plant_output,
            control=control_signal,
        )

        return SimulationResult(
            times=times,
            reference_signal=ref_signal,
            reference_model_output=ref_output,
            plant_output=plant_output,
            control_signal=control_signal,
            tracking_error=tracking_error,
            parameter_history=param_history,
            metrics=metrics,
        )

    def _generate_reference(self, t: float) -> float:
        """
        生成参考信号

        参数：
            t: 当前时间

        返回：
            参考信号值
        """
        if self.config.reference_type == ReferenceSignal.STEP:
            return self.config.reference_amplitude if t > 0 else 0.0

        elif self.config.reference_type == ReferenceSignal.SINE:
            return self.config.reference_amplitude * np.sin(
                2 * np.pi * self.config.reference_frequency * t
            )

        elif self.config.reference_type == ReferenceSignal.SQUARE:
            return self.config.reference_amplitude * np.sign(
                np.sin(2 * np.pi * self.config.reference_frequency * t)
            )

        elif self.config.reference_type == ReferenceSignal.RAMP:
            return self.config.ramp_rate * t

        elif self.config.reference_type == ReferenceSignal.CUSTOM:
            if self.config.custom_reference:
                return self.config.custom_reference(t)
            return 0.0

        return 0.0


def run_parameter_sweep(
    controller_factory: Callable[[], MRACController],
    plant_factory: Callable[[], PlantModel],
    param_name: str,
    param_values: List[float],
    config: Optional[SimulationConfig] = None,
) -> Dict[float, SimulationResult]:
    """
    参数扫描仿真

    参数：
        controller_factory: 控制器工厂函数
        plant_factory: 被控对象工厂函数
        param_name: 扫描参数名称
        param_values: 参数值列表
        config: 仿真配置

    返回：
        参数值到仿真结果的映射
    """
    results = {}

    for value in param_values:
        # 创建控制器和被控对象
        controller = controller_factory()
        plant = plant_factory()

        # 设置参数 (这里简化处理，实际需要根据参数名设置)
        if param_name == "adaptation_gain":
            controller.gamma = value
        elif param_name == "noise_std":
            plant.params.noise_std = value

        # 运行仿真
        engine = SimulationEngine(controller, plant, config)
        results[value] = engine.run()

    return results


def run_monte_carlo(
    controller_factory: Callable[[], MRACController],
    plant_factory: Callable[[], PlantModel],
    n_runs: int = 100,
    config: Optional[SimulationConfig] = None,
) -> Dict[str, Any]:
    """
    蒙特卡洛仿真

    参数：
        controller_factory: 控制器工厂函数
        plant_factory: 被控对象工厂函数
        n_runs: 仿真次数
        config: 仿真配置

    返回：
        统计结果
    """
    metrics_list = []

    for i in range(n_runs):
        # 创建控制器和被控对象
        controller = controller_factory()
        plant = plant_factory()

        # 运行仿真
        engine = SimulationEngine(controller, plant, config)
        result = engine.run()
        metrics_list.append(result.metrics)

    # 计算统计量
    metric_keys = metrics_list[0].keys()
    statistics = {}

    for key in metric_keys:
        values = [m[key] for m in metrics_list]
        statistics[key] = {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "median": np.median(values),
        }

    return {
        "n_runs": n_runs,
        "statistics": statistics,
        "all_metrics": metrics_list,
    }


def create_step_response_test(
    controller: MRACController,
    plant: PlantModel,
    amplitude: float = 1.0,
    duration: float = 10.0,
) -> SimulationResult:
    """
    阶跃响应测试

    参数：
        controller: 自适应控制器
        plant: 被控对象
        amplitude: 阶跃幅度
        duration: 测试时长
    """
    config = SimulationConfig(
        duration=duration,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=amplitude,
    )
    engine = SimulationEngine(controller, plant, config)
    return engine.run()


def create_tracking_test(
    controller: MRACController,
    plant: PlantModel,
    frequency: float = 1.0,
    amplitude: float = 1.0,
    duration: float = 10.0,
) -> SimulationResult:
    """
    跟踪测试 (正弦信号)

    参数：
        controller: 自适应控制器
        plant: 被控对象
        frequency: 信号频率
        amplitude: 信号幅度
        duration: 测试时长
    """
    config = SimulationConfig(
        duration=duration,
        reference_type=ReferenceSignal.SINE,
        reference_amplitude=amplitude,
        reference_frequency=frequency,
    )
    engine = SimulationEngine(controller, plant, config)
    return engine.run()
