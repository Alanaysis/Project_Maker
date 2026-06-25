"""
高级 MRAC 示例

展示更复杂的自适应控制场景。
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
from src.reference_model import create_first_order_model, create_second_order_model
from src.plant_model import (
    PlantType, PlantParameters, PlantModel,
    create_first_order_plant, create_second_order_plant, create_nonlinear_plant
)
from src.simulation import SimulationConfig, ReferenceSignal, run_monte_carlo
from src.adaptive_controller import AdaptationLaw


def nonlinear_system_example():
    """
    非线性系统示例

    展示自适应控制器处理非线性系统的能力
    """
    print("=" * 60)
    print("非线性系统 MRAC 示例")
    print("=" * 60)

    # 创建参考模型
    ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

    # 创建非线性被控对象
    plant = create_nonlinear_plant(a=1.0, b=1.0, noise_std=0.05)

    # 创建自适应控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.5,
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
    plot_results(result, title="非线性系统 MRAC 示例")

    return result


def time_varying_system_example():
    """
    时变系统示例

    展示自适应控制器处理时变系统的能力
    """
    print("\n" + "=" * 60)
    print("时变系统 MRAC 示例")
    print("=" * 60)

    # 创建参考模型
    ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

    # 创建时变被控对象
    params = PlantParameters(a=1.0, b=1.0, noise_std=0.02)
    plant = PlantModel(PlantType.TIME_VARYING, params)

    # 创建自适应控制器
    controller = MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.8,
        initial_params={
            "theta_r": 0.5,
            "theta_x": np.array([0.5]),
            "theta_d": 0.0,
        }
    )

    # 配置仿真
    config = SimulationConfig(
        duration=30.0,
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
    plot_results(result, title="时变系统 MRAC 示例")

    return result


def sinusoidal_tracking_example():
    """
    正弦跟踪示例

    展示自适应控制器的正弦信号跟踪能力
    """
    print("\n" + "=" * 60)
    print("正弦跟踪 MRAC 示例")
    print("=" * 60)

    # 创建参考模型
    ref_model = create_first_order_model(time_constant=0.3, steady_state_gain=1.0)

    # 创建被控对象
    plant = create_first_order_plant(time_constant=1.0, gain=1.5)

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

    # 配置仿真 (正弦跟踪)
    config = SimulationConfig(
        duration=20.0,
        dt=0.01,
        reference_type=ReferenceSignal.SINE,
        reference_amplitude=1.0,
        reference_frequency=0.5,
    )

    # 运行仿真
    engine = SimulationEngine(controller, plant, config)
    result = engine.run()

    # 分析性能
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(result.metrics)
    print(report)

    # 绘制结果
    plot_results(result, title="正弦跟踪 MRAC 示例")

    return result


def monte_carlo_analysis():
    """
    蒙特卡洛分析

    通过多次仿真评估控制器的鲁棒性
    """
    print("\n" + "=" * 60)
    print("蒙特卡洛鲁棒性分析")
    print("=" * 60)

    def controller_factory():
        ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
        return MRACController(
            reference_model=ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=0.5,
        )

    def plant_factory():
        # 随机化系统参数
        a = np.random.uniform(0.5, 2.0)
        b = np.random.uniform(0.5, 2.0)
        noise = np.random.uniform(0, 0.1)
        return create_first_order_plant(time_constant=1.0/a, gain=b, noise_std=noise)

    # 运行蒙特卡洛仿真
    config = SimulationConfig(
        duration=10.0,
        dt=0.01,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=1.0,
    )

    mc_results = run_monte_carlo(
        controller_factory=controller_factory,
        plant_factory=plant_factory,
        n_runs=50,
        config=config,
    )

    # 打印统计结果
    print("\n蒙特卡洛统计结果 (50 次仿真):")
    print("-" * 40)
    for metric, stats in mc_results["statistics"].items():
        print(f"{metric}:")
        print(f"  均值: {stats['mean']:.4f}")
        print(f"  标准差: {stats['std']:.4f}")
        print(f"  范围: [{stats['min']:.4f}, {stats['max']:.4f}]")

    # 绘制统计图
    plot_monte_carlo_results(mc_results)

    return mc_results


def comparison_example():
    """
    对比示例

    对比 MIT 规则和 Lyapunov 方法
    """
    print("\n" + "=" * 60)
    print("MIT vs Lyapunov 对比示例")
    print("=" * 60)

    # 创建相同的初始条件
    ref_model_lyap = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
    ref_model_mit = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

    plant_lyap = create_first_order_plant(time_constant=2.0, gain=0.5)
    plant_mit = create_first_order_plant(time_constant=2.0, gain=0.5)

    # Lyapunov 控制器
    controller_lyap = MRACController(
        reference_model=ref_model_lyap,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.5,
        initial_params={
            "theta_r": 0.1,
            "theta_x": np.array([0.1]),
            "theta_d": 0.0,
        }
    )

    # MIT 控制器
    controller_mit = MRACController(
        reference_model=ref_model_mit,
        adaptation_law=AdaptationLaw.MIT,
        adaptation_gain=0.1,
        initial_params={
            "theta_r": 0.1,
            "theta_x": np.array([0.1]),
            "theta_d": 0.0,
        }
    )

    config = SimulationConfig(
        duration=20.0,
        dt=0.01,
        reference_type=ReferenceSignal.STEP,
        reference_amplitude=1.0,
    )

    # 运行仿真
    engine_lyap = SimulationEngine(controller_lyap, plant_lyap, config)
    result_lyap = engine_lyap.run()

    engine_mit = SimulationEngine(controller_mit, plant_mit, config)
    result_mit = engine_mit.run()

    # 绘制对比图
    plot_comparison(result_lyap, result_mit)

    # 打印性能对比
    print("\n性能对比:")
    print("-" * 40)
    print("Lyapunov 方法:")
    print(f"  MSE: {result_lyap.metrics['mse']:.6f}")
    print(f"  调节时间: {result_lyap.metrics['settling_time']:.4f} s")
    print(f"  超调量: {result_lyap.metrics['overshoot']:.2f}%")
    print("\nMIT 规则:")
    print(f"  MSE: {result_mit.metrics['mse']:.6f}")
    print(f"  调节时间: {result_mit.metrics['settling_time']:.4f} s")
    print(f"  超调量: {result_mit.metrics['overshoot']:.2f}%")

    return result_lyap, result_mit


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
    plt.savefig(f'{title.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_monte_carlo_results(mc_results):
    """绘制蒙特卡洛结果"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    metrics_to_plot = ['mse', 'settling_time', 'overshoot', 'control_energy']
    titles = ['均方误差', '调节时间', '超调量', '控制能量']

    for idx, (metric, title) in enumerate(zip(metrics_to_plot, titles)):
        ax = axes[idx // 2, idx % 2]
        values = [m[metric] for m in mc_results["all_metrics"]]
        ax.hist(values, bins=20, edgecolor='black', alpha=0.7)
        ax.set_xlabel(title)
        ax.set_ylabel('频数')
        ax.set_title(f'{title}分布')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('monte_carlo_results.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_comparison(result_lyap, result_mit):
    """绘制对比图"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # 输出对比
    axes[0].plot(result_lyap.times, result_lyap.reference_model_output, 'b--', label='参考模型', linewidth=2)
    axes[0].plot(result_lyap.times, result_lyap.plant_output, 'b-', label='Lyapunov', linewidth=1.5)
    axes[0].plot(result_mit.times, result_mit.plant_output, 'r-', label='MIT', linewidth=1.5)
    axes[0].set_ylabel('输出')
    axes[0].set_title('Lyapunov vs MIT 对比')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 误差对比
    axes[1].plot(result_lyap.times, np.abs(result_lyap.tracking_error), 'b-', label='Lyapunov', linewidth=1.5)
    axes[1].plot(result_mit.times, np.abs(result_mit.tracking_error), 'r-', label='MIT', linewidth=1.5)
    axes[1].set_xlabel('时间 (s)')
    axes[1].set_ylabel('绝对误差')
    axes[1].set_title('跟踪误差对比')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('comparison_lyapunov_mit.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    # 运行非线性系统示例
    nonlinear_system_example()

    # 运行时变系统示例
    time_varying_system_example()

    # 运行正弦跟踪示例
    sinusoidal_tracking_example()

    # 运行对比示例
    comparison_example()

    # 运行蒙特卡洛分析
    monte_carlo_analysis()
