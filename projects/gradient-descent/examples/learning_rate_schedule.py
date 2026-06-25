"""学习率调度示例 - 展示不同的学习率调度策略"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.optimizers import SGD, Adam
from src.schedulers import StepLR, ExponentialLR, CosineAnnealingLR, WarmupScheduler
from src.functions import QuadraticFunction
from src.optimizer import optimize


def demonstrate_step_lr():
    """展示阶梯学习率衰减"""
    print("\n" + "=" * 60)
    print("阶梯学习率衰减 (StepLR)")
    print("=" * 60)

    optimizer = SGD(learning_rate=0.1)
    scheduler = StepLR(optimizer, step_size=100, gamma=0.5)

    learning_rates = []
    for i in range(500):
        learning_rates.append(optimizer.learning_rate)
        scheduler.step()

    print(f"初始学习率: 0.1")
    print(f"衰减周期: 100")
    print(f"衰减因子: 0.5")
    print(f"最终学习率: {learning_rates[-1]:.6f}")

    return learning_rates


def demonstrate_exponential_lr():
    """展示指数学习率衰减"""
    print("\n" + "=" * 60)
    print("指数学习率衰减 (ExponentialLR)")
    print("=" * 60)

    optimizer = SGD(learning_rate=0.1)
    scheduler = ExponentialLR(optimizer, gamma=0.99)

    learning_rates = []
    for i in range(500):
        learning_rates.append(optimizer.learning_rate)
        scheduler.step()

    print(f"初始学习率: 0.1")
    print(f"衰减因子: 0.99")
    print(f"最终学习率: {learning_rates[-1]:.6f}")

    return learning_rates


def demonstrate_cosine_annealing():
    """展示余弦退火学习率"""
    print("\n" + "=" * 60)
    print("余弦退火学习率 (CosineAnnealingLR)")
    print("=" * 60)

    optimizer = SGD(learning_rate=0.1)
    scheduler = CosineAnnealingLR(optimizer, T_max=500, eta_min=0.001)

    learning_rates = []
    for i in range(500):
        learning_rates.append(optimizer.learning_rate)
        scheduler.step()

    print(f"初始学习率: 0.1")
    print(f"最小学习率: 0.001")
    print(f"周期: 500")
    print(f"最终学习率: {learning_rates[-1]:.6f}")

    return learning_rates


def demonstrate_warmup():
    """展示 Warmup 学习率"""
    print("\n" + "=" * 60)
    print("Warmup 学习率 (WarmupScheduler)")
    print("=" * 60)

    optimizer = SGD(learning_rate=0.0)
    scheduler = WarmupScheduler(optimizer, warmup_epochs=50, target_lr=0.1)

    learning_rates = []
    for i in range(500):
        learning_rates.append(optimizer.learning_rate)
        scheduler.step()

    print(f"预热前学习率: 0.0")
    print(f"目标学习率: 0.1")
    print(f"预热轮数: 50")
    print(f"最终学习率: {learning_rates[-1]:.6f}")

    return learning_rates


def demonstrate_warmup_with_cosine():
    """展示 Warmup + 余弦退火"""
    print("\n" + "=" * 60)
    print("Warmup + 余弦退火")
    print("=" * 60)

    optimizer = Adam(learning_rate=0.0)
    cosine_scheduler = CosineAnnealingLR(optimizer, T_max=450, eta_min=0.001)
    scheduler = WarmupScheduler(
        optimizer, warmup_epochs=50, target_lr=0.01, scheduler=cosine_scheduler
    )

    learning_rates = []
    for i in range(500):
        learning_rates.append(optimizer.learning_rate)
        scheduler.step()

    print(f"预热前学习率: 0.0")
    print(f"目标学习率: 0.01")
    print(f"预热轮数: 50")
    print(f"最小学习率: 0.001")
    print(f"最终学习率: {learning_rates[-1]:.6f}")

    return learning_rates


def compare_schedules_on_optimization():
    """在优化问题上对比不同调度策略"""
    print("\n" + "=" * 60)
    print("在优化问题上对比不同调度策略")
    print("=" * 60)

    func = QuadraticFunction(a=1.0, b=1.0)
    x0 = np.array([3.0, 3.0])

    # 不同调度策略
    schedules = {
        'No Schedule': lambda opt: None,
        'StepLR': lambda opt: StepLR(opt, step_size=100, gamma=0.5),
        'ExponentialLR': lambda opt: ExponentialLR(opt, gamma=0.99),
        'CosineAnnealing': lambda opt: CosineAnnealingLR(opt, T_max=500, eta_min=0.001),
    }

    results = {}
    for name, scheduler_fn in schedules.items():
        optimizer = Adam(learning_rate=0.01)
        scheduler = scheduler_fn(optimizer)

        # 运行优化
        x = x0.copy()
        values = [func(x)]
        learning_rates = [optimizer.learning_rate]

        for i in range(500):
            grad = func.gradient(x)
            x = optimizer.step(x, grad)
            if scheduler:
                scheduler.step()
            values.append(func(x))
            learning_rates.append(optimizer.learning_rate)

        results[name] = {
            'values': np.array(values),
            'learning_rates': np.array(learning_rates),
            'final_value': func(x),
            'iterations': 500
        }

        print(f"{name:<20} 最终函数值: {func(x):.6e}")

    return results


def plot_learning_rate_schedules(all_schedules):
    """绘制学习率调度曲线"""
    fig, ax = plt.subplots(figsize=(12, 6))

    for name, lr in all_schedules.items():
        ax.plot(lr, '-', linewidth=2, label=name)

    ax.set_xlabel('Iteration')
    ax.set_ylabel('Learning Rate')
    ax.set_title('学习率调度策略对比')
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.savefig('examples/learning_rate_schedules.png', dpi=150, bbox_inches='tight')
    return fig


def plot_optimization_comparison(results):
    """绘制优化对比图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 收敛曲线
    for name, result in results.items():
        ax1.plot(result['values'], '-', linewidth=2, label=name)

    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Function Value')
    ax1.set_title('收敛曲线对比')
    ax1.set_yscale('log')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 学习率曲线
    for name, result in results.items():
        ax2.plot(result['learning_rates'], '-', linewidth=2, label=name)

    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Learning Rate')
    ax2.set_title('学习率变化对比')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig('examples/schedule_optimization_comparison.png', dpi=150, bbox_inches='tight')
    return fig


def main():
    """运行学习率调度示例"""
    print("=" * 60)
    print("学习率调度示例 - 梯度下降家族")
    print("=" * 60)

    # 展示不同的调度策略
    all_schedules = {}
    all_schedules['StepLR'] = demonstrate_step_lr()
    all_schedules['ExponentialLR'] = demonstrate_exponential_lr()
    all_schedules['CosineAnnealing'] = demonstrate_cosine_annealing()
    all_schedules['Warmup'] = demonstrate_warmup()
    all_schedules['Warmup + Cosine'] = demonstrate_warmup_with_cosine()

    # 绘制学习率调度曲线
    print("\n生成学习率调度曲线...")
    plot_learning_rate_schedules(all_schedules)

    # 在优化问题上对比
    print("\n在优化问题上对比不同调度策略...")
    results = compare_schedules_on_optimization()

    # 绘制优化对比图
    print("生成优化对比图...")
    plot_optimization_comparison(results)

    # 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("\n学习率调度策略:")
    print("1. StepLR: 简单有效，适合已知衰减点的情况")
    print("2. ExponentialLR: 平滑衰减，适合连续下降的需求")
    print("3. CosineAnnealing: 平滑周期性衰减，有助于跳出局部最优")
    print("4. Warmup: 稳定训练初期，防止梯度爆炸")
    print("5. Warmup + Cosine: 结合两者优点，现代深度学习常用")

    print("\n示例完成!")


if __name__ == '__main__':
    main()
