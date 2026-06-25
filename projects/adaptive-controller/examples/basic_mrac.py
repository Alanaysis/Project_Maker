"""
基本 MRAC 示例

演示模型参考自适应控制器的基本使用方法。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from src import (
    MRACController,
    ReferenceModel,
    PlantModel,
    SimulationEngine,
    PerformanceAnalyzer,
)
from src.reference_model import create_first_order_model, create_second_order_model, ModelOrder, ModelParameters
from src.plant_model import create_first_order_plant, create_second_order_plant
from src.simulation import SimulationConfig, ReferenceSignal
from src.adaptive_controller import AdaptationLaw


def basic_mrac_example():
    """
    基本 MRAC 示例

    展示一阶系统的模型参考自适应控制
    """
    print("=" * 60)
    print("基本 MRAC 示例 - 一阶系统")
    print("=" * 60)

    # 创建参考模型 (期望的闭环行为)
    # 一阶系统，时间常数 0.5s，稳态增益 1.0
    ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

    # 创建被控对象 (实际系统)
    # 一阶系统，时间常数 1.0s，增益 2.0 (与参考模型不同)
    plant = create_first_order_plant(time_constant=1.0, gain=2.0)

    # 创建自适应控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.5,
        initial_params={
            "theta_r": 0.5,  # 初始前馈增益
            "theta_x": np.array([0.5]),  # 初始反馈增益
            "theta_d": 0.0,  # 初始扰动补偿
        }
    )

    # 配置仿真
    config = SimulationConfig(
        duration=10.0,
        dt=0.01,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=1.0,
    )

    # 运行仿真
    engine = SimulationEngine(controller, plant, config)
    result = engine.run()

    # 分析性能
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(result.metrics)
    print(report)

    # 绘制结果
    plot_results(result, title="基本 MRAC 示例 - 一阶系统")

    return result


def second_order_mrac_example():
    """
    二阶系统 MRAC 示例

    展示二阶系统的模型参考自适应控制
    """
    print("\n" + "=" * 60)
    print("MRAC 示例 - 二阶系统")
    print("=" * 60)

    # 创建参考模型 (二阶临界阻尼系统)
    ref_model = create_second_order_model(
        natural_frequency=2.0,
        damping_ratio=0.7
    )

    # 创建被控对象 (欠阻尼二阶系统)
    plant = create_second_order_plant(
        natural_frequency=1.0,
        damping_ratio=0.3
    )

    # 创建自适应控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=1.0,
        initial_params={
            "theta_r": 0.5,
            "theta_x": np.array([0.5]),
            "theta_d": 0.0,
        }
    )

    # 配置仿真
    config = SimulationConfig(
        duration=15.0,
        dt=0.01,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=1.0,
    )

    # 运行仿真
    engine = SimulationEngine(controller, plant, config)
    result = engine.run()

    # 分析性能
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(result.metrics)
    print(report)

    # 绘制结果
    plot_results(result, title="MRAC 示例 - 二阶系统")

    return result


def parameter_adaptation_example():
    """
    参数自适应示例

    展示控制器参数的自适应调整过程
    """
    print("\n" + "=" * 60)
    print("参数自适应示例")
    print("=" * 60)

    # 创建参考模型
    ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

    # 创建被控对象 (参数与参考模型不同)
    plant = create_first_order_plant(time_constant=2.0, gain=0.5)

    # 创建自适应控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.3,
        initial_params={
            "theta_r": 0.1,  # 故意设置不准确的初始值
            "theta_x": np.array([0.1]),
            "theta_d": 0.0,
        }
    )

    # 配置仿真
    config = SimulationConfig(
        duration=20.0,
        dt=0.01,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=1.0,
    )

    # 运行仿真
    engine = SimulationEngine(controller, plant, config)
    result = engine.run()

    # 绘制参数变化
    plot_parameter_adaptation(result)

    # 计算参数收敛性
    analyzer = PerformanceAnalyzer()
    convergence = analyzer.compute_parameter_convergence(result.parameter_history)

    print("\n参数收敛性分析:")
    for key, info in convergence.items():
        print(f"  {key}:")
        print(f"    初始值: {info['initial_value']:.4f}")
        print(f"    最终值: {info['final_value']:.4f}")
        print(f"    变化量: {info['variation']:.4f}")
        print(f"    收敛: {'是' if info['converged'] else '否'}")

    return result


def disturbance_rejection_example():
    """
    扰动抑制示例

    展示自适应控制器的扰动抑制能力
    """
    print("\n" + "=" * 60)
    print("扰动抑制示例")
    print("=" * 60)

    # 创建参考模型
    ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

    # 创建带扰动的被控对象
    plant = create_first_order_plant(time_constant=1.0, gain=1.0)
    plant.params.disturbance_amplitude = 0.3  # 扰动幅度
    plant.params.disturbance_frequency = 0.5  # 扰动频率

    # 创建自适应控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=1.0,
        initial_params={
            "theta_r": 0.5,
            "theta_x": np.array([0.5]),
            "theta_d": 0.0,  # 初始扰动补偿为 0
        }
    )

    # 配置仿真
    config = SimulationConfig(
        duration=20.0,
        dt=0.01,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=1.0,
    )

    # 运行仿真
    engine = SimulationEngine(controller, plant, config)
    result = engine.run()

    # 分析性能
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(result.metrics)
    print(report)

    # 绘制结果
    plot_results(result, title="扰动抑制示例")

    return result


def plot_results(result, title="仿真结果"):
    """绘制仿真结果"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # 绘制输出跟踪
    axes[0].plot(result.times, result.reference_signal, 'k--', label='参考输入', linewidth=2)
    axes[0].plot(result.times, result.reference_model_output, 'b-', label='参考模型输出', linewidth=2)
    axes[0].plot(result.times, result.plant_output, 'r-', label='实际输出', linewidth=1.5)
    axes[0].set_ylabel('输出')
    axes[0].set_title(title)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 绘制跟踪误差
    axes[1].plot(result.times, result.tracking_error, 'g-', linewidth=1.5)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_ylabel('跟踪误差')
    axes[1].set_title('跟踪误差')
    axes[1].grid(True, alpha=0.3)

    # 绘制控制信号
    axes[2].plot(result.times, result.control_signal, 'm-', linewidth=1.5)
    axes[2].set_xlabel('时间 (s)')
    axes[2].set_ylabel('控制信号')
    axes[2].set_title('控制信号')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('mrac_results.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n结果已保存到 mrac_results.png")


def plot_parameter_adaptation(result):
    """绘制参数自适应过程"""
    fig, axes = plt.subplots(len(result.parameter_history), 1, figsize=(12, 4 * len(result.parameter_history)))

    if len(result.parameter_history) == 1:
        axes = [axes]

    for idx, (key, values) in enumerate(result.parameter_history.items()):
        axes[idx].plot(result.times, values, 'b-', linewidth=1.5)
        axes[idx].set_ylabel(f'{key}')
        axes[idx].set_title(f'参数 {key} 的自适应过程')
        axes[idx].grid(True, alpha=0.3)

    axes[-1].set_xlabel('时间 (s)')
    plt.tight_layout()
    plt.savefig('parameter_adaptation.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("参数自适应图已保存到 parameter_adaptation.png")


if __name__ == "__main__":
    # 运行基本示例
    basic_mrac_example()

    # 运行二阶系统示例
    second_order_mrac_example()

    # 运行参数自适应示例
    parameter_adaptation_example()

    # 运行扰动抑制示例
    disturbance_rejection_example()
