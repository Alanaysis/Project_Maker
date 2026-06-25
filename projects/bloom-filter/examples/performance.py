"""
布隆过滤器性能分析示例

展示不同参数配置下的性能表现。
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import BloomFilter, CountingBloomFilter, ScalableBloomFilter
from bloom_filter.analysis import (
    optimal_size,
    optimal_hash_count,
    false_positive_rate,
    optimal_parameters_table,
    parameter_sweep,
    benchmark_insert,
    benchmark_query,
)


def demo_optimal_parameters():
    """最优参数分析"""
    print("=" * 60)
    print("最优参数分析")
    print("=" * 60)

    table = optimal_parameters_table(
        n_values=[1000, 10000, 100000, 1000000],
        p_values=[0.001, 0.01, 0.1],
    )

    print(f"\n{'n':>10} {'p':>8} {'m':>12} {'k':>4} {'bits/elem':>10} {'bytes/elem':>10} {'total_kb':>10}")
    print("-" * 70)

    for row in table:
        print(
            f"{row['n']:>10,} "
            f"{row['p']:>8.3f} "
            f"{row['m']:>12,} "
            f"{row['k']:>4} "
            f"{row['bits_per_element']:>10.2f} "
            f"{row['bytes_per_element']:>10.2f} "
            f"{row['total_kb']:>10.2f}"
        )


def demo_false_positive_rate():
    """误判率分析"""
    print("\n" + "=" * 60)
    print("误判率分析")
    print("=" * 60)

    n = 10000
    p = 0.01
    m = optimal_size(n, p)
    k = optimal_hash_count(m, n)

    print(f"\n配置: n={n}, p={p}, m={m}, k={k}")

    # 不同元素数量下的误判率
    print(f"\n{'实际元素数':>12} {'理论误判率':>12} {'实际误判率':>12}")
    print("-" * 40)

    bf = BloomFilter(size=m, hash_count=k)
    test_size = 100000

    for actual_n in [0, 1000, 2000, 5000, 8000, 10000, 12000, 15000]:
        # 插入元素
        while bf.count < actual_n:
            bf.add(f"item_{bf.count}")

        # 计算理论误判率
        theoretical = false_positive_rate(m, k, actual_n)

        # 测量实际误判率
        false_positives = sum(
            1 for i in range(test_size) if f"test_{i}" in bf
        )
        actual = false_positives / test_size

        print(f"{actual_n:>12,} {theoretical:>12.6f} {actual:>12.6f}")


def demo_insert_benchmark():
    """插入性能基准测试"""
    print("\n" + "=" * 60)
    print("插入性能基准测试")
    print("=" * 60)

    sizes = [1000, 10000, 100000]

    print(f"\n{'过滤器类型':>20} {'元素数':>10} {'时间(秒)':>10} {'速度(元素/秒)':>15}")
    print("-" * 60)

    for n in sizes:
        items = [f"item_{i}" for i in range(n)]

        # 标准布隆过滤器
        result = benchmark_insert(
            lambda: BloomFilter(expected_items=n, false_positive_rate=0.01),
            items,
        )
        print(
            f"{'标准布隆过滤器':>20} {n:>10,} "
            f"{result['total_time']:>10.4f} "
            f"{result['items_per_second']:>15,.0f}"
        )

        # 计数布隆过滤器
        result = benchmark_insert(
            lambda: CountingBloomFilter(expected_items=n, false_positive_rate=0.01),
            items,
        )
        print(
            f"{'计数布隆过滤器':>20} {n:>10,} "
            f"{result['total_time']:>10.4f} "
            f"{result['items_per_second']:>15,.0f}"
        )

        # 可扩展布隆过滤器
        result = benchmark_insert(
            lambda: ScalableBloomFilter(initial_capacity=n // 4, false_positive_rate=0.01),
            items,
        )
        print(
            f"{'可扩展布隆过滤器':>20} {n:>10,} "
            f"{result['total_time']:>10.4f} "
            f"{result['items_per_second']:>15,.0f}"
        )


def demo_query_benchmark():
    """查询性能基准测试"""
    print("\n" + "=" * 60)
    print("查询性能基准测试")
    print("=" * 60)

    n = 100000
    existing = [f"item_{i}" for i in range(n)]
    non_existing = [f"test_{i}" for i in range(n)]

    print(f"\n{'过滤器类型':>20} {'查询类型':>12} {'时间(秒)':>10} {'速度(ns/query)':>15}")
    print("-" * 60)

    # 标准布隆过滤器
    result = benchmark_query(
        lambda: BloomFilter(expected_items=n, false_positive_rate=0.01),
        existing,
        non_existing,
    )
    print(
        f"{'标准布隆过滤器':>20} {'存在':>12} "
        f"{result['existing_time']:>10.4f} "
        f"{result['existing_ns_per_query']:>15,.0f}"
    )
    print(
        f"{'':>20} {'不存在':>12} "
        f"{result['non_existing_time']:>10.4f} "
        f"{result['non_existing_ns_per_query']:>15,.0f}"
    )

    # 计数布隆过滤器
    result = benchmark_query(
        lambda: CountingBloomFilter(expected_items=n, false_positive_rate=0.01),
        existing,
        non_existing,
    )
    print(
        f"{'计数布隆过滤器':>20} {'存在':>12} "
        f"{result['existing_time']:>10.4f} "
        f"{result['existing_ns_per_query']:>15,.0f}"
    )
    print(
        f"{'':>20} {'不存在':>12} "
        f"{result['non_existing_time']:>10.4f} "
        f"{result['non_existing_ns_per_query']:>15,.0f}"
    )


def demo_memory_usage():
    """内存使用分析"""
    print("\n" + "=" * 60)
    print("内存使用分析")
    print("=" * 60)

    n = 100000
    p = 0.01

    print(f"\n配置: n={n}, p={p}")

    # 标准布隆过滤器
    bf = BloomFilter(expected_items=n, false_positive_rate=p)
    mem = bf.memory_usage()
    print(f"\n标准布隆过滤器:")
    print(f"  位数组大小: {mem['bit_array_size']:,} 位")
    print(f"  内存使用: {mem['bit_array_bytes']:,} 字节 = {mem['bit_array_mb']:.2f} MB")
    print(f"  每元素: {mem['bit_array_bytes'] / n:.2f} 字节")

    # 计数布隆过滤器
    cbf = CountingBloomFilter(expected_items=n, false_positive_rate=p)
    mem = cbf.memory_usage()
    print(f"\n计数布隆过滤器:")
    print(f"  计数器数组大小: {mem['counter_array_size']:,}")
    print(f"  内存使用: {mem['counter_array_bytes']:,} 字节 = {mem['counter_array_mb']:.2f} MB")
    print(f"  每元素: {mem['counter_array_bytes'] / n:.2f} 字节")

    # 可扩展布隆过滤器
    sbf = ScalableBloomFilter(initial_capacity=n // 4, false_positive_rate=p)
    for i in range(n):
        sbf.add(f"item_{i}")
    mem = sbf.memory_usage()
    print(f"\n可扩展布隆过滤器:")
    print(f"  层数: {mem['layer_count']}")
    print(f"  内存使用: {mem['total_bytes']:,} 字节 = {mem['total_mb']:.2f} MB")
    print(f"  每元素: {mem['total_bytes'] / n:.2f} 字节")


def demo_parameter_sweep():
    """参数扫描分析"""
    print("\n" + "=" * 60)
    print("参数扫描分析")
    print("=" * 60)

    n = 10000
    results = parameter_sweep(n, p_values=[0.001, 0.01, 0.1], k_values=[3, 5, 7, 10])

    print(f"\nn = {n}")
    print(f"\n{'p':>8} {'k':>4} {'m':>10} {'fpr':>10} {'bits/elem':>10} {'最优':>6}")
    print("-" * 50)

    for r in results:
        optimal = "✓" if r["is_optimal"] else ""
        print(
            f"{r['p_design']:>8.3f} "
            f"{r['k']:>4} "
            f"{r['m']:>10,} "
            f"{r['fpr']:>10.6f} "
            f"{r['bits_per_element']:>10.2f} "
            f"{optimal:>6}"
        )


def main():
    """主函数"""
    print("布隆过滤器性能分析示例")
    print("=" * 60)

    demo_optimal_parameters()
    demo_false_positive_rate()
    demo_insert_benchmark()
    demo_query_benchmark()
    demo_memory_usage()
    demo_parameter_sweep()

    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
