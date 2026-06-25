"""
标准布隆过滤器实现

布隆过滤器是一种空间效率极高的概率型数据结构，用于判断元素是否属于集合。

特性:
    - 空间效率: O(m/8) 字节，m 为位数组大小
    - 插入时间: O(k)，k 为哈希函数数量
    - 查询时间: O(k)
    - 可能产生假阳性 (false positive)
    - 绝不会产生假阴性 (false negative)

数学原理:
    误判率: p ≈ (1 - e^(-kn/m))^k
    最优位数组大小: m = -(n * ln(p)) / (ln(2))^2
    最优哈希函数数量: k = (m/n) * ln(2)

参考:
    - Bloom, B. H. (1970). Space/time trade-offs in hash coding with allowable errors.
    - https://en.wikipedia.org/wiki/Bloom_filter
"""

import math
from typing import Any, Iterator

from .bit_array import BitArray
from .hash_functions import DoubleHashFunction


class BloomFilter:
    """
    标准布隆过滤器

    支持两种创建方式:
    1. 手动指定参数: BloomFilter(size=10000, hash_count=7)
    2. 自动计算最优参数: BloomFilter(expected_items=10000, false_positive_rate=0.01)

    Args:
        size: 位数组大小 (与 expected_items 二选一)
        hash_count: 哈希函数数量 (与 false_positive_rate 二选一)
        expected_items: 预期元素数量
        false_positive_rate: 期望误判率 (0, 1)

    Raises:
        ValueError: 参数无效时

    Examples:
        >>> # 方式 1: 手动指定参数
        >>> bf = BloomFilter(size=10000, hash_count=7)

        >>> # 方式 2: 自动计算最优参数
        >>> bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)

        >>> bf.add("hello")
        >>> "hello" in bf
        True
        >>> "world" in bf
        False
    """

    LN2 = math.log(2)
    LN2_SQUARED = LN2 ** 2

    def __init__(
        self,
        size: int = 0,
        hash_count: int = 0,
        expected_items: int = 0,
        false_positive_rate: float = 0.0,
    ):
        if expected_items > 0 and false_positive_rate > 0:
            # 自动计算最优参数
            if not (0 < false_positive_rate < 1):
                raise ValueError(
                    f"false_positive_rate must be in (0, 1), got {false_positive_rate}"
                )
            self._size = self._optimal_size(expected_items, false_positive_rate)
            self._hash_count = self._optimal_hash_count(self._size, expected_items)
        elif size > 0 and hash_count > 0:
            # 手动指定参数
            self._size = size
            self._hash_count = hash_count
        else:
            raise ValueError(
                "Either (size, hash_count) or (expected_items, false_positive_rate) must be provided"
            )

        self._bits = BitArray(self._size)
        self._hash_fn = DoubleHashFunction(self._hash_count)
        self._count = 0

    @property
    def size(self) -> int:
        """位数组大小"""
        return self._size

    @property
    def hash_count(self) -> int:
        """哈希函数数量"""
        return self._hash_count

    @property
    def count(self) -> int:
        """已插入元素数量"""
        return self._count

    def add(self, item: Any) -> None:
        """
        插入元素

        将元素通过所有哈希函数映射到位数组，并设置对应位为 1。

        Args:
            item: 要插入的元素

        Time Complexity: O(k)，k 为哈希函数数量
        """
        indices = self._hash_fn.hash_to_indices(item, self._size)
        for index in indices:
            self._bits.set(index)
        self._count += 1

    def add_many(self, items: Iterator[Any]) -> int:
        """
        批量插入元素

        Args:
            items: 元素迭代器

        Returns:
            成功插入的元素数量
        """
        count = 0
        for item in items:
            self.add(item)
            count += 1
        return count

    def __contains__(self, item: Any) -> bool:
        """
        检查元素是否可能存在

        通过所有哈希函数检查对应位是否都为 1。

        Returns:
            True: 元素可能存在 (可能有假阳性)
            False: 元素一定不存在 (无假阴性)

        Time Complexity: O(k)
        """
        indices = self._hash_fn.hash_to_indices(item, self._size)
        return all(self._bits.get(index) for index in indices)

    def might_contain(self, item: Any) -> bool:
        """
        检查元素是否可能存在 (与 __contains__ 相同)

        提供更明确的方法名。

        Args:
            item: 要查询的元素

        Returns:
            True 如果元素可能存在
        """
        return item in self

    def clear(self) -> None:
        """
        清空过滤器

        将所有位重置为 0，并重置元素计数。
        """
        self._bits.reset()
        self._count = 0

    def fill_ratio(self) -> float:
        """
        计算位数组填充率

        Returns:
            值为 1 的位数占总位数的比例 (0.0 ~ 1.0)
        """
        return self._bits.fill_ratio()

    def estimated_false_positive_rate(self) -> float:
        """
        估算当前误判率

        使用公式: p ≈ (1 - e^(-kn/m))^k

        Returns:
            估算的误判率
        """
        if self._count == 0:
            return 0.0
        return self._false_positive_rate(self._size, self._hash_count, self._count)

    def memory_usage(self) -> dict:
        """
        估算内存使用量

        Returns:
            包含内存使用信息的字典
        """
        bits_bytes = (self._size + 7) // 8
        return {
            "bit_array_size": self._size,
            "bit_array_bytes": bits_bytes,
            "bit_array_mb": bits_bytes / (1024 * 1024),
            "hash_count": self._hash_count,
            "element_count": self._count,
        }

    def __len__(self) -> int:
        return self._count

    def __repr__(self) -> str:
        return (
            f"BloomFilter(size={self._size}, hash_count={self._hash_count}, "
            f"count={self._count}, fill_ratio={self.fill_ratio():.4f})"
        )

    @classmethod
    def _optimal_size(cls, n: int, p: float) -> int:
        """
        计算最优位数组大小

        公式: m = -(n * ln(p)) / (ln(2))^2

        Args:
            n: 预期元素数量
            p: 期望误判率

        Returns:
            最优位数组大小
        """
        m = -(n * math.log(p)) / cls.LN2_SQUARED
        return math.ceil(m)

    @classmethod
    def _optimal_hash_count(cls, m: int, n: int) -> int:
        """
        计算最优哈希函数数量

        公式: k = (m/n) * ln(2)

        Args:
            m: 位数组大小
            n: 预期元素数量

        Returns:
            最优哈希函数数量 (至少为 1)
        """
        k = (m / n) * cls.LN2
        return max(1, round(k))

    @staticmethod
    def _false_positive_rate(m: int, k: int, n: int) -> float:
        """
        计算误判率

        公式: p = (1 - e^(-kn/m))^k

        Args:
            m: 位数组大小
            k: 哈希函数数量
            n: 已插入元素数量

        Returns:
            误判率
        """
        exponent = -k * n / m
        return (1 - math.exp(exponent)) ** k
