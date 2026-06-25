"""
布隆过滤器性能分析工具

提供误判率计算、最优参数计算、性能对比等功能。

数学公式:
    误判率: p ≈ (1 - e^(-kn/m))^k
    最优位数组大小: m = -(n * ln(p)) / (ln(2))^2
    最优哈希函数数量: k = (m/n) * ln(2)
"""

import math
import time
from typing import Any, Callable

from .bloom_filter import BloomFilter
from .counting_bloom_filter import CountingBloomFilter
from .scalable_bloom_filter import ScalableBloomFilter


LN2 = math.log(2)
LN2_SQUARED = LN2 ** 2


def optimal_size(n: int, p: float) -> int:
    """
    计算最优位数组大小

    公式: m = -(n * ln(p)) / (ln(2))^2

    Args:
        n: 预期元素数量
        p: 期望误判率

    Returns:
        最优位数组大小 (位)

    Examples:
        >>> optimal_size(10000, 0.01)
        95858
        >>> optimal_size(100000, 0.001)
        1437759
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not (0 < p < 1):
        raise ValueError(f"p must be in (0, 1), got {p}")

    m = -(n * math.log(p)) / LN2_SQUARED
    return math.ceil(m)


def optimal_hash_count(m: int, n: int) -> int:
    """
    计算最优哈希函数数量

    公式: k = (m/n) * ln(2)

    Args:
        m: 位数组大小
        n: 预期元素数量

    Returns:
        最优哈希函数数量 (至少为 1)

    Examples:
        >>> optimal_hash_count(95858, 10000)
        7
        >>> optimal_hash_count(1437759, 100000)
        10
    """
    if m <= 0:
        raise ValueError(f"m must be positive, got {m}")
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")

    k = (m / n) * LN2
    return max(1, round(k))


def false_positive_rate(m: int, k: int, n: int) -> float:
    """
    计算误判率

    公式: p = (1 - e^(-kn/m))^k

    Args:
        m: 位数组大小
        k: 哈希函数数量
        n: 已插入元素数量

    Returns:
        误判率

    Examples:
        >>> false_positive_rate(100000, 7, 10000)
        0.00818...
        >>> false_positive_rate(100000, 7, 0)
        0.0
    """
    if n == 0:
        return 0.0
    if m <= 0 or k <= 0:
        raise ValueError(f"m and k must be positive, got m={m}, k={k}")

    exponent = -k * n / m
    return (1 - math.exp(exponent)) ** k


def false_positive_rate_analysis(
    n: int, p: float, actual_n: int
) -> dict:
    """
    分析实际误判率

    比较理论最优误判率和实际误判率。

    Args:
        n: 设计容量
        p: 设计误判率
        actual_n: 实际插入元素数量

    Returns:
        包含分析结果的字典
    """
    m = optimal_size(n, p)
    k = optimal_hash_count(m, n)

    theoretical_fpr = false_positive_rate(m, k, actual_n)
    actual_fpr = false_positive_rate(m, k, actual_n)

    return {
        "design_capacity": n,
        "design_fpr": p,
        "actual_count": actual_n,
        "bit_array_size": m,
        "hash_count": k,
        "theoretical_fpr": theoretical_fpr,
        "actual_fpr": actual_fpr,
        "bits_per_element": m / actual_n if actual_n > 0 else float("inf"),
    }


def compare_filters(n: int, p: float) -> dict:
    """
    比较不同类型的布隆过滤器

    Args:
        n: 预期元素数量
        p: 期望误判率

    Returns:
        包含比较结果的字典
    """
    results = {}

    # 标准布隆过滤器
    bf = BloomFilter(expected_items=n, false_positive_rate=p)
    for i in range(n):
        bf.add(f"item_{i}")
    results["standard"] = {
        "size": bf.size,
        "hash_count": bf.hash_count,
        "memory_bytes": (bf.size + 7) // 8,
        "fill_ratio": bf.fill_ratio(),
        "estimated_fpr": bf.estimated_false_positive_rate(),
    }

    # 计数布隆过滤器
    cbf = CountingBloomFilter(expected_items=n, false_positive_rate=p)
    for i in range(n):
        cbf.add(f"item_{i}")
    results["counting"] = {
        "size": cbf.size,
        "hash_count": cbf.hash_count,
        "memory_bytes": cbf.size,
        "fill_ratio": cbf.fill_ratio(),
        "estimated_fpr": cbf.estimated_false_positive_rate(),
    }

    # 可扩展布隆过滤器
    sbf = ScalableBloomFilter(initial_capacity=n // 4, false_positive_rate=p)
    for i in range(n):
        sbf.add(f"item_{i}")
    mem = sbf.memory_usage()
    results["scalable"] = {
        "layers": sbf.layer_count,
        "total_count": sbf.count,
        "memory_bytes": mem["total_bytes"],
        "estimated_fpr": sbf.estimated_false_positive_rate(),
    }

    return results


def benchmark_insert(filter_factory: Callable, items: list[Any]) -> dict:
    """
    基准测试: 插入性能

    Args:
        filter_factory: 创建过滤器的函数
        items: 要插入的元素列表

    Returns:
        包含性能指标的字典
    """
    bf = filter_factory()

    start = time.perf_counter()
    for item in items:
        bf.add(item)
    end = time.perf_counter()

    elapsed = end - start
    count = len(items)

    return {
        "count": count,
        "total_time": elapsed,
        "items_per_second": count / elapsed,
        "ns_per_item": (elapsed * 1e9) / count,
    }


def benchmark_query(
    filter_factory: Callable,
    existing_items: list[Any],
    non_existing_items: list[Any],
) -> dict:
    """
    基准测试: 查询性能

    Args:
        filter_factory: 创建过滤器的函数
        existing_items: 存在的元素列表
        non_existing_items: 不存在的元素列表

    Returns:
        包含性能指标的字典
    """
    bf = filter_factory()
    for item in existing_items:
        bf.add(item)

    # 测试存在的元素查询
    start = time.perf_counter()
    for item in existing_items:
        _ = item in bf
    end = time.perf_counter()
    existing_time = end - start

    # 测试不存在的元素查询
    start = time.perf_counter()
    false_positives = 0
    for item in non_existing_items:
        if item in bf:
            false_positives += 1
    end = time.perf_counter()
    non_existing_time = end - start

    return {
        "existing_count": len(existing_items),
        "existing_time": existing_time,
        "existing_ns_per_query": (existing_time * 1e9) / len(existing_items),
        "non_existing_count": len(non_existing_items),
        "non_existing_time": non_existing_time,
        "non_existing_ns_per_query": (non_existing_time * 1e9) / len(non_existing_items),
        "false_positives": false_positives,
        "actual_fpr": false_positives / len(non_existing_items),
    }


def parameter_sweep(
    n: int,
    p_values: list[float] = None,
    k_values: list[int] = None,
) -> list[dict]:
    """
    参数扫描: 分析不同参数组合的性能

    Args:
        n: 预期元素数量
        p_values: 误判率列表
        k_values: 哈希函数数量列表

    Returns:
        包含各参数组合性能指标的字典列表
    """
    if p_values is None:
        p_values = [0.001, 0.005, 0.01, 0.05, 0.1]
    if k_values is None:
        k_values = [3, 5, 7, 10, 15]

    results = []

    for p in p_values:
        m = optimal_size(n, p)
        k_optimal = optimal_hash_count(m, n)

        for k in k_values:
            fpr = false_positive_rate(m, k, n)
            bits_per_elem = m / n

            results.append({
                "n": n,
                "p_design": p,
                "m": m,
                "k": k,
                "k_optimal": k_optimal,
                "fpr": fpr,
                "bits_per_element": bits_per_elem,
                "is_optimal": k == k_optimal,
            })

    return results


def optimal_parameters_table(
    n_values: list[int] = None,
    p_values: list[float] = None,
) -> list[dict]:
    """
    生成最优参数表

    Args:
        n_values: 元素数量列表
        p_values: 误判率列表

    Returns:
        包含最优参数的字典列表
    """
    if n_values is None:
        n_values = [1000, 10000, 100000, 1000000]
    if p_values is None:
        p_values = [0.001, 0.01, 0.1]

    results = []
    for n in n_values:
        for p in p_values:
            m = optimal_size(n, p)
            k = optimal_hash_count(m, n)
            fpr = false_positive_rate(m, k, n)
            bits_per = m / n
            bytes_per = bits_per / 8

            results.append({
                "n": n,
                "p": p,
                "m": m,
                "k": k,
                "fpr_actual": fpr,
                "bits_per_element": bits_per,
                "bytes_per_element": bytes_per,
                "total_kb": (m / 8) / 1024,
            })

    return results
