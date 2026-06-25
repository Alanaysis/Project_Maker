"""可视化演示示例 - 展示各种可视化功能"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.optimizers import SGD, Momentum, Adam
from src.functions import QuadraticFunction, RosenbrockFunction, HimmelblauFunction
from src.optimizer import optimize
from src.visualizer import ContourPlotter, TrajectoryPlotter, ComparisonPlotter


def demo_contour_plot():
    """演示等高线图"""
    print("\n" + "=" * 60)
    print("等高线图演示")
    print("=" * 60)

    # 二次函数
    func1 = QuadraticFunction(a=1.0, b=1.0)
    plotter1 = ContourPlotter(func1, x_range=(-4, 4), y_range=(-4, 4))
    fig1 = plotter1.plot(title="二次函数等高线图")
    fig1.savefig('examples/contour_quadratic.png', dpi=150, bbox_inches='tight')
    print("二次函数等高线图已保存")

    # Rosenbrock 函数
    func2 = RosenbrockFunction(a=1.0, b=100.0)
    plotter2 = ContourPlotter(func2, x_range=(-2, 2), y_range=(-1, 3))
    fig2 = plotter2.plot(title="Rosenbrock 函数等高线图")
    fig2.savefig('examples/contour_rosenbrock.png', dpi=150, bbox_inches='tight')
    print("Rosenbrock 函数等高线图已保存")

    # Himmelblau 函数
    func3 = HimmelblauFunction()
    plotter3 = ContourPlotter(func3, x_range=(-5, 5), y_range=(-5, 5))
    fig3 = plotter3.plot(title="Himmelblau 函数等高线图")
    fig3.savefig('examples/contour_himmelblau.png', dpi=150, bbox_inches='tight')
    print("Himmelblau 函数等高线图已保存")

    return [fig1, fig2, fig3]


def demo_3d_surface():
    """演示 3D 表面图"""
    print("\n" + "=" * 60)
    print("3D 表面图演示")
    print("=" * 60)

    # 二次函数
    func1 = QuadraticFunction(a=1.0, b=1.0)
    plotter1 = ContourPlotter(func1, x_range=(-4, 4), y_range=(-4, 4))
    fig1 = plotter1.plot_3d()
    fig1.savefig('examples/3d_quadratic.png', dpi=150, bbox_inches='tight')
    print("二次函数 3D 表面图已保存")

    # Rosenbrock 函数
    func2 = RosenbrockFunction(a=1.0, b=100.0)
    plotter2 = ContourPlotter(func2, x_range=(-2, 2), y_range=(-1, 3))
    fig2 = plotter2.plot_3d()
    fig2.savefig('examples/3d_rosenbrock.png', dpi=150, bbox_inches='tight')
    print("Rosenbrock 函数 3D 表面图已保存")

    return [fig1, fig2]


def demo_trajectory_plot():
    """演示轨迹图"""
    print("\n" + "=" * 60)
    print("轨迹图演示")
    print("=" * 60)

    # 在二次函数上运行优化
    func = QuadraticFunction(a=1.0, b=1.0)
    x0 = np.array([3.0, 3.0])

    optimizers = {
        'SGD': SGD(learning_rate=0.1),
        'Momentum': Momentum(learning_rate=0.01, momentum=0.9),
        'Adam': Adam(learning_rate=0.01)
    }

    results = {}
    for name, optimizer in optimizers.items():
        result = optimize(func, optimizer, x0.copy(), max_iter=100, tol=1e-6)
        results[name] = result

    # 创建轨迹可视化器
    plotter = TrajectoryPlotter()

    # 绘制单个轨迹
    fig1 = plotter.plot_trajectory(
        results['Adam']['trajectory'],
        label='Adam',
        color='blue'
    )
    fig1.figure.savefig('examples/trajectory_single.png', dpi=150, bbox_inches='tight')
    print("单个轨迹图已保存")

    # 对比多个轨迹
    trajectories = {name: result['trajectory'] for name, result in results.items()}
    fig2 = plotter.compare_trajectories(
        trajectories,
        title="优化轨迹对比"
    )
    fig2.savefig('examples/trajectory_comparison.png', dpi=150, bbox_inches='tight')
    print("轨迹对比图已保存")

    # 绘制收敛曲线
    values = {name: result['values'] for name, result in results.items()}
    fig3 = plotter.plot_convergence(
        values,
        title="收敛曲线对比"
    )
    fig3.savefig('examples/convergence_curves.png', dpi=150, bbox_inches='tight')
    print("收敛曲线已保存")

    # 绘制梯度范数曲线
    grad_norms = {name: result['grad_norms'] for name, result in results.items()}
    fig4 = plotter.plot_gradient_norm(
        grad_norms,
        title="梯度范数对比"
    )
    fig4.savefig('examples/gradient_norms.png', dpi=150, bbox_inches='tight')
    print("梯度范数曲线已保存")

    # 绘制学习率曲线
    learning_rates = {name: result['learning_rates'] for name, result in results.items()}
    fig5 = plotter.plot_learning_rate(
        learning_rates,
        title="学习率变化"
    )
    fig5.savefig('examples/learning_rates.png', dpi=150, bbox_inches='tight')
    print("学习率曲线已保存")

    return [fig1.figure, fig2, fig3, fig4, fig5]


def demo_comparison_plot():
    """演示对比图"""
    print("\n" + "=" * 60)
    print("对比图演示")
    print("=" * 60)

    # 在 Rosenbrock 函数上运行优化
    func = RosenbrockFunction(a=1.0, b=100.0)
    x0 = np.array([-1.0, 1.0])

    optimizers = {
        'SGD': SGD(learning_rate=0.0001),
        'Momentum': Momentum(learning_rate=0.0001, momentum=0.9),
        'Adam': Adam(learning_rate=0.001)
    }

    results = {}
    for name, optimizer in optimizers.items():
        result = optimize(func, optimizer, x0.copy(), max_iter=2000, tol=1e-4)
        results[name] = result

    # 创建对比可视化器
    plotter = ComparisonPlotter()

    # 绘制综合对比图
    comparison_results = {}
    for name, result in results.items():
        comparison_results[name] = {
            'trajectory': result['trajectory'],
            'values': result['values'],
            'grad_norms': result['grad_norms'],
            'iterations': result['niter'],
            'final_value': result['fun'],
            'final_grad_norm': result['grad_norms'][-1]
        }

    fig1 = plotter.plot_optimization_comparison(
        comparison_results,
        title="Rosenbrock 函数 - 优化器对比"
    )
    fig1.savefig('examples/comparison_full.png', dpi=150, bbox_inches='tight')
    print("综合对比图已保存")

    # 创建性能表
    table = plotter.create_performance_table(comparison_results)
    print("\n性能对比表:")
    print(table)

    # 绘制收敛速度对比
    fig2 = plotter.plot_convergence_speed(
        comparison_results,
        target_value=0.01,
        title="收敛速度对比 (目标值: 0.01)"
    )
    fig2.savefig('examples/convergence_speed.png', dpi=150, bbox_inches='tight')
    print("收敛速度对比图已保存")

    return [fig1, fig2]


def demo_advanced_visualization():
    """演示高级可视化"""
    print("\n" + "=" * 60)
    print("高级可视化演示")
    print("=" * 60)

    # 创建自定义对比图
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # 不同函数
    functions = [
        ('Quadratic', QuadraticFunction(a=1.0, b=1.0), (-4, 4), (-4, 4)),
        ('Rosenbrock', RosenbrockFunction(a=1.0, b=100.0), (-2, 2), (-1, 3)),
        ('Himmelblau', HimmelblauFunction(), (-5, 5), (-5, 5))
    ]

    for idx, (name, func, x_range, y_range) in enumerate(functions):
        # 等高线图
        plotter = ContourPlotter(func, x_range=x_range, y_range=y_range)
        X, Y, Z = plotter._create_meshgrid()

        ax = axes[0, idx]
        contour = ax.contourf(X, Y, Z, levels=20, cmap='viridis', alpha=0.8)
        ax.contour(X, Y, Z, levels=20, colors='black', linewidths=0.5, alpha=0.3)
        plt.colorbar(contour, ax=ax)
        ax.set_title(f'{name} Function')
        ax.set_xlabel('x')
        ax.set_ylabel('y')

        # 运行 Adam 优化
        optimizer = Adam(learning_rate=0.01)
        x0 = func.initial_point()
        result = optimize(func, optimizer, x0, max_iter=200, tol=1e-4)

        # 绘制轨迹
        ax = axes[1, idx]
        traj = result['trajectory']
        ax.plot(traj[:, 0], traj[:, 1], 'r-', linewidth=2, label='Adam')
        ax.plot(traj[0, 0], traj[0, 1], 'go', markersize=10, label='Start')
        ax.plot(traj[-1, 0], traj[-1, 1], 'r*', markersize=15, label='End')

        # 绘制等高线背景
        ax.contour(X, Y, Z, levels=20, colors='gray', linewidths=0.5, alpha=0.3)
        ax.set_title(f'{name} - Adam Trajectory')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig('examples/advanced_visualization.png', dpi=150, bbox_inches='tight')
    print("高级可视化图已保存")

    return fig


def main():
    """运行可视化演示示例"""
    print("=" * 60)
    print("可视化演示示例 - 梯度下降家族")
    print("=" * 60)

    # 确保 examples 目录存在
    import os
    os.makedirs('examples', exist_ok=True)

    # 演示各种可视化
    demo_contour_plot()
    demo_3d_surface()
    demo_trajectory_plot()
    demo_comparison_plot()
    demo_advanced_visualization()

    # 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("\n可视化类型:")
    print("1. 等高线图: 展示函数地形和优化轨迹")
    print("2. 3D 表面图: 直观展示函数形状")
    print("3. 轨迹图: 对比不同优化器的路径")
    print("4. 收敛曲线: 展示优化过程的收敛情况")
    print("5. 梯度范数: 展示梯度的变化趋势")
    print("6. 学习率曲线: 展示学习率调度的效果")
    print("7. 综合对比图: 全面对比不同优化器的性能")

    print("\n示例完成!")


if __name__ == '__main__':
    main()
