"""
邻域生成策略模块 (Neighborhood Generation Strategies)

邻域搜索是模拟退火的"探索"机制。好的邻域策略决定了算法能否
有效地在解空间中搜索。

邻域结构的选择取决于问题的性质：
- 离散问题：交换、插入、反转等排列操作
- 连续问题：高斯扰动、均匀扰动等
- 组合问题：多种策略组合（自适应）
"""

import random
import math
from typing import List, Callable, Any, Optional


def neighborhood_generator(
    solution: Any,
    strategy: str = "auto",
    **kwargs
) -> Any:
    """
    统一的邻域生成接口

    根据问题类型自动选择或手动指定邻域生成策略。

    Args:
        solution: 当前解
        strategy: 策略名称 ("swap", "insert", "reverse", "multi_switch",
                  "continuous", "adaptive", "auto")
        **kwargs: 策略参数

    Returns:
        新生成的解
    """
    if strategy == "auto":
        if isinstance(solution, list):
            return swap_neighbor(solution)
        elif isinstance(solution, (int, float)):
            return continuous_neighbor(solution)
        else:
            raise ValueError(f"无法自动推断解的类型: {type(solution)}")

    strategy_map = {
        "swap": swap_neighbor,
        "insert": insert_neighbor,
        "reverse": reverse_neighbor,
        "multi_switch": multi_switch_neighbor,
        "continuous": continuous_neighbor,
        "adaptive": adaptive_neighborhood,
    }

    if strategy not in strategy_map:
        raise ValueError(f"未知的邻域策略: {strategy}，可选: {list(strategy_map.keys())}")

    return strategy_map[strategy](solution, **kwargs)


def swap_neighbor(solution: List) -> List:
    """
    交换邻域 (Swap Neighborhood)

    随机选择两个位置并交换它们的值。

    适用于：排列问题（如 TSP）

    示例：
        [1, 2, 3, 4, 5] → [1, 4, 3, 2, 5]  (交换位置 1 和 3)
    """
    new_sol = solution.copy()
    i, j = random.sample(range(len(new_sol)), 2)
    new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol


def insert_neighbor(solution: List) -> List:
    """
    插入邻域 (Insert Neighborhood)

    随机选择一个元素，插入到另一个随机位置。

    适用于：排列问题（如 TSP）

    示例：
        [1, 2, 3, 4, 5] → [1, 3, 2, 4, 5]  (将 2 插入到位置 1)
    """
    new_sol = solution.copy()
    i = random.randint(0, len(new_sol) - 1)
    j = random.randint(0, len(new_sol) - 1)
    while j == i:
        j = random.randint(0, len(new_sol) - 1)
    value = new_sol.pop(i)
    new_sol.insert(j, value)
    return new_sol


def reverse_neighbor(solution: List) -> List:
    """
    反转邻域 (Reverse/Inversion Neighborhood)

    随机选择两个位置，反转它们之间的子序列。

    适用于：排列问题（如 TSP），2-opt 局部搜索的基础

    示例：
        [1, 2, 3, 4, 5] → [1, 4, 3, 2, 5]  (反转位置 1-3)
    """
    new_sol = solution.copy()
    i, j = sorted(random.sample(range(len(new_sol)), 2))
    new_sol[i:j+1] = reversed(new_sol[i:j+1])
    return new_sol


def multi_switch_neighbor(solution: List, num_switches: int = 2) -> List:
    """
    多交换邻域 (Multi-Switch Neighborhood)

    进行多次交换操作，扩大搜索范围。

    适用于：需要较大扰动的问题

    Args:
        solution: 当前解
        num_switches: 交换次数

    示例：
        [1, 2, 3, 4, 5] → [3, 1, 5, 4, 2]  (进行 3 次交换)
    """
    new_sol = solution.copy()
    for _ in range(num_switches):
        i, j = random.sample(range(len(new_sol)), 2)
        new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol


def continuous_neighbor(solution, magnitude: float = 1.0) -> Any:
    """
    连续邻域搜索 (Continuous Neighborhood)

    对连续变量施加高斯扰动。

    适用于：连续优化问题

    Args:
        solution: 当前解（标量或数组）
        magnitude: 扰动幅度（标准差）

    示例：
        x = 5.0 → x = 5.3  (高斯噪声 ±1.0)
    """
    if isinstance(solution, (int, float)):
        return solution + random.gauss(0, magnitude)
    elif isinstance(solution, list):
        return [x + random.gauss(0, magnitude) for x in solution]
    else:
        # 尝试转换为列表
        arr = list(solution)
        return [x + random.gauss(0, magnitude) for x in arr]


def adaptive_neighborhood(
    solution: List,
    strategies: Optional[List[str]] = None,
    weights: Optional[List[float]] = None
) -> List:
    """
    自适应邻域搜索 (Adaptive Neighborhood)

    根据当前状态动态选择邻域策略。
    - 高温时：倾向于大范围探索（如多交换）
    - 低温时：倾向于精细搜索（如单交换）

    Args:
        solution: 当前解
        strategies: 可选的策略列表
        weights: 可选的策略权重

    Returns:
        新解
    """
    if strategies is None:
        strategies = ["swap", "insert", "reverse"]
    if weights is None:
        weights = [0.4, 0.3, 0.3]

    # 根据温度调整权重（模拟：高温时更多探索）
    # 这里假设调用者会传入温度信息，简化版直接随机选择
    strategy = random.choices(strategies, weights=weights, k=1)[0]

    strategy_map = {
        "swap": swap_neighbor,
        "insert": insert_neighbor,
        "reverse": reverse_neighbor,
    }

    return strategy_map[strategy](solution)
