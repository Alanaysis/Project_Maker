"""
调度问题示例

演示如何使用模拟退火算法求解调度问题：
- 作业车间调度（Job Shop）
- 流水车间调度（Flow Shop）
- 单机调度（Single Machine）
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule
from src.scheduling import JobShopScheduling, FlowShopScheduling, SingleMachineScheduling
from src.visualization import plot_convergence


def solve_job_shop():
    """求解作业车间调度问题"""
    print("=" * 60)
    print("调度问题示例 - 作业车间调度 (Job Shop)")
    print("=" * 60)

    # 创建实例
    np.random.seed(42)
    n_jobs = 8
    n_machines = 4
    jsp = JobShopScheduling.create_random_instance(n_jobs, n_machines, seed=42)

    print(f"\n问题规模: {n_jobs}个作业, {n_machines}台机器")

    # 生成初始解
    initial_solution = jsp.generate_random_solution()
    initial_makespan = jsp.evaluate(initial_solution)
    print(f"初始Makespan: {initial_makespan}")

    # 配置SA
    config = SAConfig(
        initial_temp=100.0,
        final_temp=0.01,
        cooling_rate=0.995,
        max_iterations=5000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    # 使用混合邻域
    def mixed_neighbor(solution):
        ops = [jsp.neighbor_swap, jsp.neighbor_insert, jsp.neighbor_reverse]
        idx = np.random.randint(0, len(ops))
        return ops[idx](solution)

    # 优化
    print("\n开始优化...")
    optimizer = SimulatedAnnealing(
        config, jsp.evaluate, mixed_neighbor, initial_solution
    )

    best_solution, best_makespan, history = optimizer.optimize()

    print(f"\n最优调度: {best_solution}")
    print(f"最优Makespan: {best_makespan}")
    print(f"改善: {(initial_makespan - best_makespan) / initial_makespan * 100:.1f}%")
    print(f"迭代次数: {optimizer.iteration}")

    # 绘制收敛曲线
    fig = plot_convergence(history, "作业车间调度优化收敛曲线")
    plt.savefig('jobshop_convergence.png', dpi=100, bbox_inches='tight')
    print("\n已保存: jobshop_convergence.png")

    return best_solution, best_makespan


def solve_flow_shop():
    """求解流水车间调度问题"""
    print("\n" + "=" * 60)
    print("调度问题示例 - 流水车间调度 (Flow Shop)")
    print("=" * 60)

    # 创建实例
    np.random.seed(42)
    n_jobs = 10
    n_machines = 5
    fsp = FlowShopScheduling.create_random_instance(n_jobs, n_machines, seed=42)

    print(f"\n问题规模: {n_jobs}个作业, {n_machines}台机器")

    # 生成初始解
    initial_solution = fsp.generate_random_solution()
    initial_makespan = fsp.evaluate(initial_solution)
    print(f"初始Makespan: {initial_makespan}")

    # 配置SA
    config = SAConfig(
        initial_temp=200.0,
        final_temp=0.01,
        cooling_rate=0.997,
        max_iterations=8000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    # 使用NEH启发式生成初始解（简化版）
    # NEH启发式：按总加工时间降序排列
    total_times = fsp.process_times.sum(axis=1)
    neh_order = np.argsort(-total_times).tolist()

    print(f"\n使用NEH启发式初始解...")
    neh_makespan = fsp.evaluate(neh_order)
    print(f"NEH初始Makespan: {neh_makespan}")

    # 优化
    print("\n开始SA优化...")
    optimizer = SimulatedAnnealing(
        config, fsp.evaluate, fsp.neighbor_insert, neh_order
    )

    best_solution, best_makespan, history = optimizer.optimize()

    print(f"\n最优调度: {best_solution}")
    print(f"最优Makespan: {best_makespan}")
    print(f"相对NEH改善: {(neh_makespan - best_makespan) / neh_makespan * 100:.1f}%")
    print(f"相对随机改善: {(initial_makespan - best_makespan) / initial_makespan * 100:.1f}%")

    # 绘制收敛曲线
    fig = plot_convergence(history, "流水车间调度优化收敛曲线")
    plt.savefig('flowshop_convergence.png', dpi=100, bbox_inches='tight')
    print("\n已保存: flowshop_convergence.png")

    return best_solution, best_makespan


def solve_single_machine():
    """求解单机调度问题"""
    print("\n" + "=" * 60)
    print("调度问题示例 - 单机调度 (Single Machine)")
    print("=" * 60)

    # 创建实例
    np.random.seed(42)
    n_jobs = 12
    sms = SingleMachineScheduling.create_random_instance(n_jobs, seed=42)

    print(f"\n问题规模: {n_jobs}个作业")
    print(f"目标: 最小化加权总延迟")

    # 生成初始解
    initial_solution = sms.generate_random_solution()
    initial_tardiness = sms.evaluate(initial_solution)
    print(f"\n初始加权延迟: {initial_tardiness:.2f}")

    # 使用WSPT启发式（加权最短加工时间优先）
    wspt_ratio = [(sms.weights[i] / sms.process_times[i], i) for i in range(n_jobs)]
    wspt_ratio.sort(reverse=True)
    wspt_order = [idx for _, idx in wspt_ratio]

    wspt_tardiness = sms.evaluate(wspt_order)
    print(f"WSPT启发式加权延迟: {wspt_tardiness:.2f}")

    # 配置SA
    config = SAConfig(
        initial_temp=50.0,
        final_temp=0.01,
        cooling_rate=0.995,
        max_iterations=5000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    # 优化
    print("\n开始SA优化...")
    optimizer = SimulatedAnnealing(
        config, sms.evaluate, sms.neighbor_insert, wspt_order
    )

    best_solution, best_tardiness, history = optimizer.optimize()

    print(f"\n最优调度: {best_solution}")
    print(f"最优加权延迟: {best_tardiness:.2f}")
    print(f"相对随机改善: {(initial_tardiness - best_tardiness) / initial_tardiness * 100:.1f}%")
    print(f"相对WSPT改善: {(wspt_tardiness - best_tardiness) / wspt_tardiness * 100:.1f}%")

    # 绘制收敛曲线
    fig = plot_convergence(history, "单机调度优化收敛曲线")
    plt.savefig('single_machine_convergence.png', dpi=100, bbox_inches='tight')
    print("\n已保存: single_machine_convergence.png")

    return best_solution, best_tardiness


def compare_cooling_schedules_scheduling():
    """对比不同冷却策略在调度问题上的效果"""
    print("\n" + "=" * 60)
    print("冷却策略对比 - 作业车间调度")
    print("=" * 60)

    np.random.seed(42)
    jsp = JobShopScheduling.create_random_instance(6, 3, seed=42)
    initial_solution = jsp.generate_random_solution()

    schedules = [
        ("指数冷却", CoolingSchedule.EXPONENTIAL),
        ("线性冷却", CoolingSchedule.LINEAR),
        ("对数冷却", CoolingSchedule.LOGARITHMIC),
    ]

    results = []

    for name, schedule in schedules:
        print(f"\n运行 {name}...")
        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.01,
            cooling_rate=0.995,
            max_iterations=3000,
            cooling_schedule=schedule
        )

        optimizer = SimulatedAnnealing(
            config, jsp.evaluate, jsp.neighbor_swap, initial_solution.copy()
        )

        best_solution, best_makespan, history = optimizer.optimize()
        results.append((name, best_makespan, history))
        print(f"  最优Makespan: {best_makespan}")

    # 绘制对比图
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for name, makespan, history in results:
        axes[0].plot(history['best_cost'], label=f'{name}: {makespan}')
    axes[0].set_xlabel('迭代次数')
    axes[0].set_ylabel('最优Makespan')
    axes[0].set_title('冷却策略对比 - 收敛曲线')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    for name, makespan, history in results:
        axes[1].plot(history['temperature'], label=name)
    axes[1].set_xlabel('迭代次数')
    axes[1].set_ylabel('温度')
    axes[1].set_title('冷却策略对比 - 温度变化')
    axes[1].set_yscale('log')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('scheduling_cooling_comparison.png', dpi=100, bbox_inches='tight')
    print("\n已保存: scheduling_cooling_comparison.png")

    return results


if __name__ == "__main__":
    # 求解作业车间调度
    solve_job_shop()

    # 求解流水车间调度
    solve_flow_shop()

    # 求解单机调度
    solve_single_machine()

    # 对比冷却策略
    compare_cooling_schedules_scheduling()
