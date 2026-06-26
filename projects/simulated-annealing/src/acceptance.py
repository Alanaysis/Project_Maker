"""
接受准则模块 (Acceptance Criterion)

模拟退火的关键创新：以一定概率接受差解，从而跳出局部最优。

Metropolis 准则 (Metropolis Criterion):
- 如果新解更好 (ΔE < 0)，总是接受
- 如果新解更差 (ΔE > 0)，以概率 P = exp(-ΔE / T) 接受

其中：
- ΔE = E_new - E_old (能量差，越大表示新解越差)
- T 是当前温度

概率解释：
- 高温时：exp(-ΔE/T) 接近 1，几乎接受所有解（广泛探索）
- 低温时：exp(-ΔE/T) 接近 0，只接受好解（精细利用）
- T → 0 时：算法退化为贪心算法
"""

import random
import math


def metropolis_criterion(delta_e: float, temperature: float) -> bool:
    """
    Metropolis 接受准则

    判断是否接受一个新解。

    Args:
        delta_e: 能量差 = E_new - E_old。负值表示新解更好。
        temperature: 当前温度。必须 > 0。

    Returns:
        bool: True 表示接受新解，False 表示拒绝

    原理：
        ΔE < 0: 新解更优，直接接受
        ΔE >= 0: 按概率 exp(-ΔE/T) 接受

        例如：T=100, ΔE=10 时，接受概率 ≈ exp(-0.1) ≈ 0.905
             T=1, ΔE=10 时，接受概率 ≈ exp(-10) ≈ 0.000045
    """
    if temperature <= 0:
        temperature = 1e-10

    if delta_e < 0:
        return True

    # 新解更差，以概率 exp(-ΔE/T) 接受
    try:
        acceptance_prob = math.exp(-delta_e / temperature)
    except OverflowError:
        # 防止 exp 溢出
        acceptance_prob = 0.0

    return random.random() < acceptance_prob


def boltzmann_acceptance(delta_e: float, temperature: float) -> float:
    """
    Boltzmann 接受概率计算

    返回接受差解的概率值，用于需要概率值的场景（如加权选择）。

    Args:
        delta_e: 能量差 = E_new - E_old
        temperature: 当前温度

    Returns:
        float: 接受概率 [0, 1]

    注意：
        当 ΔE 很大或 T 很小时，exp(-ΔE/T) 可能下溢为 0。
        此时函数返回 0，表示几乎不可能接受该解。
    """
    if temperature <= 0:
        return 0.0

    if delta_e < 0:
        return 1.0

    try:
        prob = math.exp(-delta_e / temperature)
        return min(prob, 1.0)  # 确保不超过 1
    except OverflowError:
        return 0.0
    except ValueError:
        # exp 参数过大导致溢出
        return 0.0


def simulated_annealing_acceptance(
    delta_e: float, temperature: float, temperature_range: float = 1.0
) -> bool:
    """
    带温度范围归一化的接受准则

    当能量值的范围已知时，可以用温度范围归一化能量差，
    使接受概率在不同问题间可比。

    P = exp(-ΔE / (T * T_range))

    Args:
        delta_e: 能量差
        temperature: 当前温度
        temperature_range: 温度范围，用于归一化

    Returns:
        bool: 是否接受
    """
    effective_temp = temperature * temperature_range
    if effective_temp <= 0:
        effective_temp = 1e-10

    if delta_e < 0:
        return True

    try:
        acceptance_prob = math.exp(-delta_e / effective_temp)
    except OverflowError:
        acceptance_prob = 0.0

    return random.random() < acceptance_prob
