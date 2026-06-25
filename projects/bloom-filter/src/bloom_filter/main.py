"""
布隆过滤器演示程序

展示标准布隆过滤器、计数布隆过滤器和可扩展布隆过滤器的使用。
"""

import random
import string
import time

from .bloom_filter import BloomFilter
from .counting_bloom_filter import CountingBloomFilter
from .scalable_bloom_filter import ScalableBloomFilter
from .analysis import (
    optimal_size,
    optimal_hash_count,
    false_positive_rate,
    optimal_parameters_table,
)


def demo_standard_bloom_filter():
    """标准布隆过滤器演示"""
    print("=" * 60)
    print("标准布隆过滤器演示")
    print("=" * 60)

    # 创建布隆过滤器
    n = 10000
    p = 0.01
    bf = BloomFilter(expected_items=n, false_positive_rate=p)

    print(f"\n配置:")
    print(f"  预期元素数量: {n}")
    print(f"  期望误判率: {p}")
    print(f"  位数组大小: {bf.size}")
    print(f"  哈希函数数量: {bf.hash_count}")

    # 插入元素
    words = [f"word_{i}" for i in range(n)]
    start = time.perf_counter()
    for word in words:
        bf.add(word)
    insert_time = time.perf_counter() - start

    print(f"\n插入 {n} 个元素:")
    print(f"  耗时: {insert_time:.4f} 秒")
    print(f"  速度: {n / insert_time:.0f} 元素/秒")
    print(f"  填充率: {bf.fill_ratio():.4f}")
    print(f"  估算误判率: {bf.estimated_false_positive_rate():.6f}")

    # 查询测试
    true_positives = sum(1 for w in words if w in bf)
    false_negatives = n - true_positives

    # 误判率测试
    test_size = 10000
    test_words = [f"test_{i}" for i in range(test_size)]
    false_positives = sum(1 for w in test_words if w in bf)
    actual_fpr = false_positives / test_size

    print(f"\n查询测试:")
    print(f"  已插入元素: {true_positives}/{n} 正确识别 (假阴性: {false_negatives})")
    print(f"  未插入元素: {false_positives}/{test_size} 误判 (实际误判率: {actual_fpr:.6f})")

    # 内存使用
    mem = bf.memory_usage()
    print(f"\n内存使用:")
    print(f"  位数组: {mem['bit_array_size']} 位 = {mem['bit_array_bytes']} 字节")
    print(f"  每元素: {mem['bit_array_bytes'] / n:.2f} 字节")


def demo_counting_bloom_filter():
    """计数布隆过滤器演示"""
    print("\n" + "=" * 60)
    print("计数布隆过滤器演示")
    print("=" * 60)

    n = 10000
    p = 0.01
    cbf = CountingBloomFilter(expected_items=n, false_positive_rate=p)

    print(f"\n配置:")
    print(f"  预期元素数量: {n}")
    print(f"  期望误判率: {p}")
    print(f"  计数器数组大小: {cbf.size}")
    print(f"  哈希函数数量: {cbf.hash_count}")
    print(f"  最大计数值: {cbf.max_count}")

    # 插入元素
    words = [f"word_{i}" for i in range(n)]
    for word in words:
        cbf.add(word)

    print(f"\n插入 {n} 个元素:")
    print(f"  填充率: {cbf.fill_ratio():.4f}")

    # 删除测试
    delete_count = n // 2
    deleted_words = words[:delete_count]
    for word in deleted_words:
        cbf.remove(word)

    # 验证删除
    still_present = sum(1 for w in deleted_words if w in cbf)
    remaining_present = sum(1 for w in words[delete_count:] if w in cbf)

    print(f"\n删除测试:")
    print(f"  删除 {delete_count} 个元素")
    print(f"  已删除元素仍存在: {still_present}/{delete_count}")
    print(f"  未删除元素仍存在: {remaining_present}/{n - delete_count}")

    # 内存使用
    mem = cbf.memory_usage()
    print(f"\n内存使用:")
    print(f"  计数器数组: {mem['counter_array_size']} × 8 位 = {mem['counter_array_bytes']} 字节")
    print(f"  每元素: {mem['counter_array_bytes'] / n:.2f} 字节")


def demo_scalable_bloom_filter():
    """可扩展布隆过滤器演示"""
    print("\n" + "=" * 60)
    print("可扩展布隆过滤器演示")
    print("=" * 60)

    initial_capacity = 1000
    p = 0.01
    sbf = ScalableBloomFilter(
        initial_capacity=initial_capacity,
        false_positive_rate=p,
        scaling_factor=2.0,
        tightening_ratio=0.5,
    )

    print(f"\n配置:")
    print(f"  初始容量: {initial_capacity}")
    print(f"  目标误判率: {p}")
    print(f"  扩容因子: {sbf._scaling_factor}")
    print(f"  收紧比例: {sbf._tightening_ratio}")

    # 插入大量元素
    n = 10000
    words = [f"word_{i}" for i in range(n)]
    start = time.perf_counter()
    for word in words:
        sbf.add(word)
    insert_time = time.perf_counter() - start

    print(f"\n插入 {n} 个元素:")
    print(f"  耗时: {insert_time:.4f} 秒")
    print(f"  速度: {n / insert_time:.0f} 元素/秒")
    print(f"  层数: {sbf.layer_count}")
    print(f"  总容量: {sbf.current_capacity}")

    # 各层信息
    print(f"\n各层信息:")
    for info in sbf.layer_info():
        print(
            f"  层 {info['index']}: "
            f"大小={info['size']}, "
            f"哈希数={info['hash_count']}, "
            f"容量={info['capacity']}, "
            f"元素数={info['count']}, "
            f"填充率={info['fill_ratio']:.4f}"
        )

    # 查询测试
    true_positives = sum(1 for w in words if w in bf for bf in [sbf])
    test_words = [f"test_{i}" for i in range(10000)]
    false_positives = sum(1 for w in test_words if w in sbf)

    print(f"\n查询测试:")
    print(f"  已插入元素正确识别: {true_positives}/{n}")
    print(f"  未插入元素误判: {false_positives}/10000")
    print(f"  估算总体误判率: {sbf.estimated_false_positive_rate():.6f}")

    # 内存使用
    mem = sbf.memory_usage()
    print(f"\n内存使用:")
    print(f"  层数: {mem['layer_count']}")
    print(f"  总内存: {mem['total_bytes']} 字节 = {mem['total_mb']:.2f} MB")


def demo_optimal_parameters():
    """最优参数分析演示"""
    print("\n" + "=" * 60)
    print("最优参数分析")
    print("=" * 60)

    table = optimal_parameters_table()

    print(f"\n{'n':>10} {'p':>8} {'m':>12} {'k':>4} {'fpr':>10} {'bits/elem':>10} {'bytes/elem':>10} {'total_kb':>10}")
    print("-" * 80)

    for row in table:
        print(
            f"{row['n']:>10,} "
            f"{row['p']:>8.3f} "
            f"{row['m']:>12,} "
            f"{row['k']:>4} "
            f"{row['fpr_actual']:>10.6f} "
            f"{row['bits_per_element']:>10.2f} "
            f"{row['bytes_per_element']:>10.2f} "
            f"{row['total_kb']:>10.2f}"
        )


def demo_practical_applications():
    """实际应用演示"""
    print("\n" + "=" * 60)
    print("实际应用演示")
    print("=" * 60)

    # 1. URL 去重
    print("\n1. URL 去重:")
    url_filter = BloomFilter(expected_items=1000000, false_positive_rate=0.01)
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
        "https://example.com/page1",  # 重复
    ]

    new_urls = []
    for url in urls:
        if url not in url_filter:
            url_filter.add(url)
            new_urls.append(url)

    print(f"  总 URL: {len(urls)}")
    print(f"  去重后: {len(new_urls)}")
    print(f"  新 URL: {new_urls}")

    # 2. 垃圾邮件过滤
    print("\n2. 垃圾邮件过滤:")
    spam_filter = BloomFilter(expected_items=100000, false_positive_rate=0.001)
    spam_keywords = ["viagra", "casino", "lottery", "winner", "click here"]

    for keyword in spam_keywords:
        spam_filter.add(keyword)

    test_emails = [
        "Win a free lottery ticket!",
        "Meeting tomorrow at 3pm",
        "Click here for viagra",
        "Project update",
    ]

    for email in test_emails:
        words = email.lower().split()
        is_spam = any(word in spam_filter for word in words)
        status = "SPAM" if is_spam else "CLEAN"
        print(f"  [{status}] {email}")

    # 3. 数据库查询优化
    print("\n3. 数据库查询优化:")
    db_filter = BloomFilter(expected_items=1000000, false_positive_rate=0.01)

    # 模拟数据库中的键
    db_keys = [f"user_{i}" for i in range(100000)]
    for key in db_keys:
        db_filter.add(key)

    # 模拟查询
    query_keys = ["user_1", "user_50000", "user_99999", "user_100001", "user_200000"]
    for key in query_keys:
        if key in db_filter:
            print(f"  {key}: 可能存在，查询数据库")
        else:
            print(f"  {key}: 一定不存在，跳过查询")


def main():
    """主函数"""
    print("布隆过滤器 (Bloom Filter) 演示程序")
    print("=" * 60)

    demo_standard_bloom_filter()
    demo_counting_bloom_filter()
    demo_scalable_bloom_filter()
    demo_optimal_parameters()
    demo_practical_applications()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
