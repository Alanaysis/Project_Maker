"""
调度问题模块

实现常见的调度优化问题：
- 作业车间调度（Job Shop Scheduling）
- 流水车间调度（Flow Shop Scheduling）
- 单机调度（Single Machine Scheduling）
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass, field
from enum import Enum


class ObjectiveType(Enum):
    """调度目标类型"""
    MAKESPAN = "makespan"          # 最大完工时间
    TOTAL_FLOW_TIME = "flow_time"  # 总流程时间
    TOTAL_TARDINESS = "tardiness"  # 总延迟时间


@dataclass
class Job:
    """作业"""
    id: int
    operations: List[Tuple[int, int]]  # (机器ID, 加工时间) 列表
    due_date: float = float('inf')     # 截止时间
    weight: float = 1.0                # 权重


@dataclass
class Schedule:
    """调度方案"""
    job_sequence: List[int]           # 作业顺序
    machine_assignments: Dict = field(default_factory=dict)  # 机器分配
    completion_times: Dict = field(default_factory=dict)     # 完成时间


class JobShopScheduling:
    """
    作业车间调度问题

    n个作业在m台机器上加工，每个作业有特定的加工顺序。
    目标是最小化最大完工时间（makespan）。

    参数:
        jobs: 作业列表
        n_machines: 机器数量
    """

    def __init__(self, jobs: List[Job], n_machines: int):
        self.jobs = jobs
        self.n_jobs = len(jobs)
        self.n_machines = n_machines
        self.objective_type = ObjectiveType.MAKESPAN

    def evaluate(self, permutation: List[int]) -> float:
        """
        评估调度方案

        参数:
            permutation: 作业排列顺序

        返回:
            目标函数值（makespan）
        """
        # 初始化机器可用时间
        machine_available = [0.0] * self.n_machines
        # 初始化作业完成时间
        job_completion = [0.0] * self.n_jobs

        # 按顺序处理每个作业
        for job_idx in permutation:
            job = self.jobs[job_idx]
            current_time = 0.0

            for machine_id, process_time in job.operations:
                # 等待机器可用
                start_time = max(current_time, machine_available[machine_id])
                # 更新机器可用时间
                machine_available[machine_id] = start_time + process_time
                # 更新当前时间
                current_time = start_time + process_time

            job_completion[job_idx] = current_time

        # 计算目标函数值
        if self.objective_type == ObjectiveType.MAKESPAN:
            return max(job_completion)
        elif self.objective_type == ObjectiveType.TOTAL_FLOW_TIME:
            return sum(job_completion)
        elif self.objective_type == ObjectiveType.TOTAL_TARDINESS:
            tardiness = sum(
                max(0, job_completion[i] - self.jobs[i].due_date)
                for i in range(self.n_jobs)
            )
            return tardiness

        return max(job_completion)

    def generate_random_solution(self) -> List[int]:
        """生成随机调度方案"""
        solution = list(range(self.n_jobs))
        np.random.shuffle(solution)
        return solution

    def neighbor_swap(self, solution: List[int]) -> List[int]:
        """交换邻域：交换两个作业的位置"""
        new_solution = solution.copy()
        i, j = np.random.choice(self.n_jobs, 2, replace=False)
        new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
        return new_solution

    def neighbor_insert(self, solution: List[int]) -> List[int]:
        """插入邻域：将一个作业移动到另一个位置"""
        new_solution = solution.copy()
        i = np.random.randint(0, self.n_jobs)
        positions = list(range(self.n_jobs))
        positions.remove(i)
        j = np.random.choice(positions)

        job = new_solution.pop(i)
        new_solution.insert(j, job)
        return new_solution

    def neighbor_reverse(self, solution: List[int]) -> List[int]:
        """逆序邻域：反转一段子序列"""
        new_solution = solution.copy()
        i, j = sorted(np.random.choice(self.n_jobs, 2, replace=False))
        new_solution[i:j + 1] = reversed(new_solution[i:j + 1])
        return new_solution

    @staticmethod
    def create_random_instance(
        n_jobs: int,
        n_machines: int,
        max_process_time: int = 10,
        seed: int = None
    ) -> 'JobShopScheduling':
        """
        创建随机作业车间调度实例

        参数:
            n_jobs: 作业数量
            n_machines: 机器数量
            max_process_time: 最大加工时间
            seed: 随机种子

        返回:
            JobShopScheduling实例
        """
        if seed is not None:
            np.random.seed(seed)

        jobs = []
        for job_id in range(n_jobs):
            # 每个作业在每台机器上加工一次，顺序随机
            machines = list(range(n_machines))
            np.random.shuffle(machines)
            operations = [
                (m, np.random.randint(1, max_process_time + 1))
                for m in machines
            ]
            jobs.append(Job(id=job_id, operations=operations))

        return JobShopScheduling(jobs, n_machines)


class FlowShopScheduling:
    """
    流水车间调度问题

    n个作业依次通过m台机器，所有作业的加工顺序相同。
    目标是最小化最大完工时间。

    参数:
        process_times: 加工时间矩阵 [n_jobs x n_machines]
    """

    def __init__(self, process_times: np.ndarray):
        self.process_times = process_times
        self.n_jobs, self.n_machines = process_times.shape

    def evaluate(self, permutation: List[int]) -> float:
        """
        评估调度方案

        参数:
            permutation: 作业排列顺序

        返回:
            makespan
        """
        n = len(permutation)
        m = self.n_machines

        # 完成时间矩阵
        completion = np.zeros((n, m))

        for i, job_idx in enumerate(permutation):
            for j in range(m):
                if i == 0 and j == 0:
                    completion[i][j] = self.process_times[job_idx][j]
                elif i == 0:
                    completion[i][j] = completion[i][j - 1] + self.process_times[job_idx][j]
                elif j == 0:
                    completion[i][j] = completion[i - 1][j] + self.process_times[job_idx][j]
                else:
                    completion[i][j] = max(
                        completion[i - 1][j],
                        completion[i][j - 1]
                    ) + self.process_times[job_idx][j]

        return completion[-1][-1]

    def generate_random_solution(self) -> List[int]:
        """生成随机调度方案"""
        solution = list(range(self.n_jobs))
        np.random.shuffle(solution)
        return solution

    def neighbor_swap(self, solution: List[int]) -> List[int]:
        """交换邻域"""
        new_solution = solution.copy()
        i, j = np.random.choice(self.n_jobs, 2, replace=False)
        new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
        return new_solution

    def neighbor_insert(self, solution: List[int]) -> List[int]:
        """插入邻域"""
        new_solution = solution.copy()
        i = np.random.randint(0, self.n_jobs)
        positions = list(range(self.n_jobs))
        positions.remove(i)
        j = np.random.choice(positions)

        job = new_solution.pop(i)
        new_solution.insert(j, job)
        return new_solution

    def neighbor_reverse(self, solution: List[int]) -> List[int]:
        """逆序邻域"""
        new_solution = solution.copy()
        i, j = sorted(np.random.choice(self.n_jobs, 2, replace=False))
        new_solution[i:j + 1] = reversed(new_solution[i:j + 1])
        return new_solution

    @staticmethod
    def create_random_instance(
        n_jobs: int,
        n_machines: int,
        max_process_time: int = 10,
        seed: int = None
    ) -> 'FlowShopScheduling':
        """
        创建随机流水车间调度实例

        参数:
            n_jobs: 作业数量
            n_machines: 机器数量
            max_process_time: 最大加工时间
            seed: 随机种子

        返回:
            FlowShopScheduling实例
        """
        if seed is not None:
            np.random.seed(seed)

        process_times = np.random.randint(1, max_process_time + 1, size=(n_jobs, n_machines))
        return FlowShopScheduling(process_times)


class SingleMachineScheduling:
    """
    单机调度问题

    n个作业在一台机器上加工，目标是最小化加权总延迟。

    参数:
        process_times: 加工时间列表
        due_dates: 截止时间列表
        weights: 权重列表
    """

    def __init__(
        self,
        process_times: List[float],
        due_dates: List[float],
        weights: List[float] = None
    ):
        self.process_times = process_times
        self.due_dates = due_dates
        self.n_jobs = len(process_times)

        if weights is None:
            self.weights = [1.0] * self.n_jobs
        else:
            self.weights = weights

    def evaluate(self, permutation: List[int]) -> float:
        """
        评估调度方案（加权总延迟）

        参数:
            permutation: 作业排列顺序

        返回:
            加权总延迟
        """
        current_time = 0.0
        total_tardiness = 0.0

        for job_idx in permutation:
            current_time += self.process_times[job_idx]
            tardiness = max(0, current_time - self.due_dates[job_idx])
            total_tardiness += self.weights[job_idx] * tardiness

        return total_tardiness

    def generate_random_solution(self) -> List[int]:
        """生成随机调度方案"""
        solution = list(range(self.n_jobs))
        np.random.shuffle(solution)
        return solution

    def neighbor_swap(self, solution: List[int]) -> List[int]:
        """交换邻域"""
        new_solution = solution.copy()
        i, j = np.random.choice(self.n_jobs, 2, replace=False)
        new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
        return new_solution

    def neighbor_insert(self, solution: List[int]) -> List[int]:
        """插入邻域"""
        new_solution = solution.copy()
        i = np.random.randint(0, self.n_jobs)
        positions = list(range(self.n_jobs))
        positions.remove(i)
        j = np.random.choice(positions)

        job = new_solution.pop(i)
        new_solution.insert(j, job)
        return new_solution

    @staticmethod
    def create_random_instance(
        n_jobs: int,
        max_process_time: int = 10,
        seed: int = None
    ) -> 'SingleMachineScheduling':
        """
        创建随机单机调度实例

        参数:
            n_jobs: 作业数量
            max_process_time: 最大加工时间
            seed: 随机种子

        返回:
            SingleMachineScheduling实例
        """
        if seed is not None:
            np.random.seed(seed)

        process_times = np.random.randint(1, max_process_time + 1, n_jobs).tolist()
        # 截止时间：总加工时间的一定比例
        total_time = sum(process_times)
        due_dates = np.random.uniform(
            total_time * 0.5 / n_jobs,
            total_time * 1.5 / n_jobs,
            n_jobs
        ).tolist()
        weights = np.random.uniform(0.5, 2.0, n_jobs).tolist()

        return SingleMachineScheduling(process_times, due_dates, weights)


def demo_scheduling():
    """演示调度问题求解"""
    print("调度问题演示")
    print("=" * 50)

    from .simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule

    # 1. 作业车间调度
    print("\n[1] 作业车间调度 (Job Shop)")
    print("-" * 40)

    np.random.seed(42)
    jsp = JobShopScheduling.create_random_instance(5, 3, seed=42)
    initial_solution = jsp.generate_random_solution()
    initial_makespan = jsp.evaluate(initial_solution)

    config = SAConfig(
        initial_temp=100.0,
        final_temp=0.01,
        cooling_rate=0.995,
        max_iterations=3000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    optimizer = SimulatedAnnealing(
        config,
        jsp.evaluate,
        jsp.neighbor_swap,
        initial_solution
    )

    best_solution, best_makespan, history = optimizer.optimize()

    print(f"  作业数量: {jsp.n_jobs}")
    print(f"  机器数量: {jsp.n_machines}")
    print(f"  初始Makespan: {initial_makespan}")
    print(f"  最优Makespan: {best_makespan}")
    print(f"  改善: {(initial_makespan - best_makespan) / initial_makespan * 100:.1f}%")

    # 2. 流水车间调度
    print("\n[2] 流水车间调度 (Flow Shop)")
    print("-" * 40)

    np.random.seed(42)
    fsp = FlowShopScheduling.create_random_instance(6, 4, seed=42)
    initial_solution = fsp.generate_random_solution()
    initial_makespan = fsp.evaluate(initial_solution)

    optimizer = SimulatedAnnealing(
        config,
        fsp.evaluate,
        fsp.neighbor_insert,
        initial_solution
    )

    best_solution, best_makespan, history = optimizer.optimize()

    print(f"  作业数量: {fsp.n_jobs}")
    print(f"  机器数量: {fsp.n_machines}")
    print(f"  初始Makespan: {initial_makespan}")
    print(f"  最优Makespan: {best_makespan}")
    print(f"  改善: {(initial_makespan - best_makespan) / initial_makespan * 100:.1f}%")

    # 3. 单机调度
    print("\n[3] 单机调度 (Single Machine)")
    print("-" * 40)

    np.random.seed(42)
    sms = SingleMachineScheduling.create_random_instance(8, seed=42)
    initial_solution = sms.generate_random_solution()
    initial_tardiness = sms.evaluate(initial_solution)

    optimizer = SimulatedAnnealing(
        config,
        sms.evaluate,
        sms.neighbor_swap,
        initial_solution
    )

    best_solution, best_tardiness, history = optimizer.optimize()

    print(f"  作业数量: {sms.n_jobs}")
    print(f"  初始加权延迟: {initial_tardiness:.2f}")
    print(f"  最优加权延迟: {best_tardiness:.2f}")
    print(f"  改善: {(initial_tardiness - best_tardiness) / initial_tardiness * 100:.1f}%")

    print("\n演示完成!")


if __name__ == "__main__":
    demo_scheduling()
