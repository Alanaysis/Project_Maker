"""
布隆过滤器 (Bloom Filter) 实现库

提供标准布隆过滤器、计数布隆过滤器和可扩展布隆过滤器的实现。

模块:
    - bit_array: 位数组实现
    - hash_functions: 哈希函数实现
    - bloom_filter: 标准布隆过滤器
    - counting_bloom_filter: 计数布隆过滤器
    - scalable_bloom_filter: 可扩展布隆过滤器
    - analysis: 性能分析工具

快速开始:

    >>> from bloom_filter import BloomFilter
    >>> bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
    >>> bf.add("hello")
    >>> "hello" in bf
    True
    >>> "world" in bf
    False
"""

from .bit_array import BitArray
from .hash_functions import HashFunction, DoubleHashFunction
from .bloom_filter import BloomFilter
from .counting_bloom_filter import CountingBloomFilter
from .scalable_bloom_filter import ScalableBloomFilter
from .analysis import (
    optimal_size,
    optimal_hash_count,
    false_positive_rate,
    compare_filters,
)

__version__ = "1.0.0"
__author__ = "AI Analysis"

__all__ = [
    "BitArray",
    "HashFunction",
    "DoubleHashFunction",
    "BloomFilter",
    "CountingBloomFilter",
    "ScalableBloomFilter",
    "optimal_size",
    "optimal_hash_count",
    "false_positive_rate",
    "compare_filters",
]
