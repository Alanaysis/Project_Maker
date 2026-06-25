"""
布隆过滤器基本使用示例

展示标准布隆过滤器、计数布隆过滤器和可扩展布隆过滤器的基本用法。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import BloomFilter, CountingBloomFilter, ScalableBloomFilter


def example_standard_bloom_filter():
    """标准布隆过滤器示例"""
    print("=" * 60)
    print("标准布隆过滤器示例")
    print("=" * 60)

    # 方式 1: 自动计算最优参数
    bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
    print(f"\n创建布隆过滤器:")
    print(f"  位数组大小: {bf.size}")
    print(f"  哈希函数数量: {bf.hash_count}")

    # 插入元素
    words = ["apple", "banana", "cherry", "date", "elderberry"]
    for word in words:
        bf.add(word)

    # 查询元素
    print(f"\n查询结果:")
    for word in words:
        print(f"  '{word}' in filter: {word in bf}")

    print(f"  'fig' in filter: {'fig' in bf}")
    print(f"  'grape' in filter: {'grape' in bf}")

    # 统计信息
    print(f"\n统计信息:")
    print(f"  元素数量: {bf.count}")
    print(f"  填充率: {bf.fill_ratio():.4f}")
    print(f"  估算误判率: {bf.estimated_false_positive_rate():.6f}")


def example_counting_bloom_filter():
    """计数布隆过滤器示例"""
    print("\n" + "=" * 60)
    print("计数布隆过滤器示例")
    print("=" * 60)

    cbf = CountingBloomFilter(expected_items=10000, false_positive_rate=0.01)
    print(f"\n创建计数布隆过滤器:")
    print(f"  计数器数组大小: {cbf.size}")
    print(f"  哈希函数数量: {cbf.hash_count}")
    print(f"  最大计数值: {cbf.max_count}")

    # 插入元素
    items = ["user_1", "user_2", "user_3", "user_4", "user_5"]
    for item in items:
        cbf.add(item)

    print(f"\n插入 {len(items)} 个元素后:")
    print(f"  元素数量: {cbf.count}")

    # 删除元素
    print(f"\n删除 'user_1' 和 'user_3':")
    cbf.remove("user_1")
    cbf.remove("user_3")

    print(f"  元素数量: {cbf.count}")
    print(f"  'user_1' in filter: {'user_1' in cbf}")
    print(f"  'user_2' in filter: {'user_2' in cbf}")
    print(f"  'user_3' in filter: {'user_3' in cbf}")
    print(f"  'user_4' in filter: {'user_4' in cbf}")


def example_scalable_bloom_filter():
    """可扩展布隆过滤器示例"""
    print("\n" + "=" * 60)
    print("可扩展布隆过滤器示例")
    print("=" * 60)

    # 初始容量较小，会自动扩容
    sbf = ScalableBloomFilter(
        initial_capacity=100,
        false_positive_rate=0.01,
        scaling_factor=2.0,
        tightening_ratio=0.5,
    )

    print(f"\n创建可扩展布隆过滤器:")
    print(f"  初始容量: {sbf._initial_capacity}")
    print(f"  目标误判率: {sbf.false_positive_rate}")

    # 插入大量元素
    n = 1000
    for i in range(n):
        sbf.add(f"item_{i}")

    print(f"\n插入 {n} 个元素后:")
    print(f"  层数: {sbf.layer_count}")
    print(f"  总容量: {sbf.current_capacity}")
    print(f"  总元素数: {sbf.count}")
    print(f"  估算误判率: {sbf.estimated_false_positive_rate():.6f}")

    # 各层信息
    print(f"\n各层信息:")
    for info in sbf.layer_info():
        print(
            f"  层 {info['index']}: "
            f"容量={info['capacity']}, "
            f"元素数={info['count']}, "
            f"填充率={info['fill_ratio']:.4f}"
        )


def example_data_types():
    """支持不同数据类型"""
    print("\n" + "=" * 60)
    print("支持不同数据类型")
    print("=" * 60)

    bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

    # 字符串
    bf.add("hello")
    bf.add("world")

    # 整数
    bf.add(12345)
    bf.add(67890)

    # 浮点数
    bf.add(3.14)
    bf.add(2.718)

    # 字节串
    bf.add(b"bytes")

    print(f"\n查询不同类型的数据:")
    print(f"  'hello': {'hello' in bf}")
    print(f"  12345: {12345 in bf}")
    print(f"  3.14: {3.14 in bf}")
    print(f"  b'bytes': {b'bytes' in bf}")
    print(f"  'missing': {'missing' in bf}")
    print(f"  99999: {99999 in bf}")


def main():
    """主函数"""
    print("布隆过滤器基本使用示例")
    print("=" * 60)

    example_standard_bloom_filter()
    example_counting_bloom_filter()
    example_scalable_bloom_filter()
    example_data_types()

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
