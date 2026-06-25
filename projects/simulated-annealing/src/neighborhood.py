"""
邻域操作模块

实现组合优化问题中常用的邻域操作：
- 交换（Swap）：随机交换两个元素的位置
- 逆序（Reverse/2-opt）：反转子序列
- 插入（Insert）：将一个元素移动到另一个位置
"""

import numpy as np
from typing import List, Callable


class NeighborhoodOps:
    """
    邻域操作集合

    提供多种邻域操作函数，用于生成候选解。
    所有操作都不修改原始解，而是返回新解。
    """

    @staticmethod
    def swap(solution: List[int]) -> List[int]:
        """
        交换操作：随机选择两个位置并交换

        适用于：排列问题（TSP、调度等）

        参数:
            solution: 当前解（排列）

        返回:
            新解
        """
        new_solution = solution.copy()
        n = len(new_solution)
        i, j = np.random.choice(n, 2, replace=False)
        new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
        return new_solution

    @staticmethod
    def reverse(solution: List[int]) -> List[int]:
        """
        逆序操作（2-opt）：随机选择子序列并反转

        适用于：TSP等路径优化问题

        参数:
            solution: 当前解（排列）

        返回:
            新解
        """
        new_solution = solution.copy()
        n = len(new_solution)
        i, j = sorted(np.random.choice(n, 2, replace=False))
        new_solution[i:j + 1] = reversed(new_solution[i:j + 1])
        return new_solution

    @staticmethod
    def insert(solution: List[int]) -> List[int]:
        """
        插入操作：随机选择一个元素并插入到另一个位置

        适用于：调度问题、排列问题

        参数:
            solution: 当前解（排列）

        返回:
            新解
        """
        new_solution = solution.copy()
        n = len(new_solution)

        # 选择要移动的元素
        i = np.random.randint(0, n)
        # 选择插入位置（不能是原位置）
        positions = list(range(n))
        positions.remove(i)
        j = np.random.choice(positions)

        # 执行插入
        element = new_solution.pop(i)
        new_solution.insert(j, element)
        return new_solution

    @staticmethod
    def or_opt(solution: List[int], max_segment: int = 3) -> List[int]:
        """
        Or-opt操作：移动一段连续元素到另一个位置

        适用于：TSP等路径优化问题

        参数:
            solution: 当前解（排列）
            max_segment: 最大片段长度

        返回:
            新解
        """
        new_solution = solution.copy()
        n = len(new_solution)

        # 随机选择片段长度
        seg_len = np.random.randint(1, min(max_segment + 1, n))
        seg_start = np.random.randint(0, n - seg_len + 1)

        # 提取片段
        segment = new_solution[seg_start:seg_start + seg_len]
        remaining = new_solution[:seg_start] + new_solution[seg_start + seg_len:]

        # 选择插入位置
        insert_pos = np.random.randint(0, len(remaining) + 1)

        # 插入片段
        new_solution = remaining[:insert_pos] + segment + remaining[insert_pos:]
        return new_solution

    @staticmethod
    def two_opt_swap(solution: List[int]) -> List[int]:
        """
        2-opt交换：交换两段不相邻的子序列

        适用于：TSP等路径优化问题

        参数:
            solution: 当前解（排列）

        返回:
            新解
        """
        new_solution = solution.copy()
        n = len(new_solution)

        # 选择两个不相邻的断点
        i = np.random.randint(0, n - 2)
        j = np.random.randint(i + 2, n)

        # 交换两段
        new_solution[i + 1:j + 1] = reversed(new_solution[i + 1:j + 1])
        return new_solution

    @staticmethod
    def create_mixed_neighbor(ops: List[Callable] = None, weights: List[float] = None) -> Callable:
        """
        创建混合邻域函数

        随机选择多种邻域操作中的一种，可用于提高搜索多样性。

        参数:
            ops: 邻域操作列表
            weights: 各操作的选择权重

        返回:
            混合邻域函数
        """
        if ops is None:
            ops = [
                NeighborhoodOps.swap,
                NeighborhoodOps.reverse,
                NeighborhoodOps.insert,
                NeighborhoodOps.or_opt,
            ]

        if weights is None:
            weights = [1.0 / len(ops)] * len(ops)

        weights = np.array(weights)
        weights = weights / weights.sum()

        def mixed_neighbor(solution: List[int]) -> List[int]:
            op_idx = np.random.choice(len(ops), p=weights)
            return ops[op_idx](solution)

        return mixed_neighbor


def demo_neighborhood_ops():
    """演示邻域操作"""
    print("邻域操作演示")
    print("=" * 50)

    # 创建示例解
    solution = list(range(10))
    print(f"原始解: {solution}")
    print()

    ops = NeighborhoodOps()

    # 交换操作
    new_sol = ops.swap(solution)
    print(f"交换操作: {new_sol}")

    # 逆序操作
    new_sol = ops.reverse(solution)
    print(f"逆序操作: {new_sol}")

    # 插入操作
    new_sol = ops.insert(solution)
    print(f"插入操作: {new_sol}")

    # Or-opt操作
    new_sol = ops.or_opt(solution)
    print(f"Or-opt操作: {new_sol}")

    # 2-opt交换
    new_sol = ops.two_opt_swap(solution)
    print(f"2-opt交换: {new_sol}")

    # 混合邻域
    mixed = ops.create_mixed_neighbor()
    new_sol = mixed(solution)
    print(f"混合邻域: {new_sol}")

    print()
    print("所有操作保持排列的完整性:")
    for name, op in [
        ("swap", ops.swap),
        ("reverse", ops.reverse),
        ("insert", ops.insert),
        ("or_opt", ops.or_opt),
        ("two_opt_swap", ops.two_opt_swap),
    ]:
        new_sol = op(solution)
        assert sorted(new_sol) == sorted(solution), f"{name} 操作破坏了排列"
        print(f"  {name}: OK")

    print("\n演示完成!")


if __name__ == "__main__":
    demo_neighborhood_ops()
