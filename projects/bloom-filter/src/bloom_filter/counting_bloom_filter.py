"""
计数布隆过滤器 (Counting Bloom Filter) 实现

计数布隆过滤器是标准布隆过滤器的扩展，使用计数器替代位数组，
从而支持删除操作。

参考论文:
    Fan, L., Cao, P., Almeida, J., & Broder, A. Z. (2000).
    Summary Cache: A Scalable Wide-Area Web Cache Sharing Protocol.

特性:
    - 支持插入、查询和删除操作
    - 每个位置使用 8 位计数器 (最大计数 255)
    - 空间开销约为标准布隆过滤器的 8 倍
    - 删除操作存在假阴性风险 (哈希冲突导致计数器下溢)

时间复杂度:
    - 插入: O(k)
    - 查询: O(k)
    - 删除: O(k)

空间复杂度: O(m) 字节，m 为计数器数组大小
"""

import math
from typing import Any, Iterator

from .bit_array import CountingArray
from .hash_functions import DoubleHashFunction


class CountingBloomFilter:
    """
    计数布隆过滤器

    支持删除操作的布隆过滤器变体。

    Args:
        size: 计数器数组大小 (与 expected_items 二选一)
        hash_count: 哈希函数数量 (与 false_positive_rate 二选一)
        expected_items: 预期元素数量
        false_positive_rate: 期望误判率 (0, 1)
        max_count: 最大计数值 (默认 255)

    Examples:
        >>> cbf = CountingBloomFilter(expected_items=10000, false_positive_rate=0.01)
        >>> cbf.add("hello")
        >>> cbf.add("world")
        >>> "hello" in cbf
        True
        >>> cbf.remove("hello")
        True
        >>> "hello" in cbf
        False
        >>> "world" in cbf
        True
    """

    LN2 = math.log(2)
    LN2_SQUARED = LN2 ** 2

    def __init__(
        self,
        size: int = 0,
        hash_count: int = 0,
        expected_items: int = 0,
        false_positive_rate: float = 0.0,
        max_count: int = 255,
    ):
        if expected_items > 0 and false_positive_rate > 0:
            if not (0 < false_positive_rate < 1):
                raise ValueError(
                    f"false_positive_rate must be in (0, 1), got {false_positive_rate}"
                )
            self._size = self._optimal_size(expected_items, false_positive_rate)
            self._hash_count = self._optimal_hash_count(self._size, expected_items)
        elif size > 0 and hash_count > 0:
            self._size = size
            self._hash_count = hash_count
        else:
            raise ValueError(
                "Either (size, hash_count) or (expected_items, false_positive_rate) must be provided"
            )

        self._counters = CountingArray(self._size, max_count)
        self._hash_fn = DoubleHashFunction(self._hash_count)
        self._count = 0

    @property
    def size(self) -> int:
        """计数器数组大小"""
        return self._size

    @property
    def hash_count(self) -> int:
        """哈希函数数量"""
        return self._hash_count

    @property
    def count(self) -> int:
        """已插入元素数量 (包括重复插入)"""
        return self._count

    @property
    def max_count(self) -> int:
        """最大计数值"""
        return self._counters.max_count

    def add(self, item: Any) -> bool:
        """
        插入元素

        将元素通过所有哈希函数映射，并增加对应位置的计数器。

        Args:
            item: 要插入的元素

        Returns:
            True 如果成功插入，False 如果某个计数器已满

        Time Complexity: O(k)
        """
        indices = self._hash_fn.hash_to_indices(item, self._size)
        success = True
        for index in indices:
            if not self._counters.increment(index):
                success = False
        self._count += 1
        return success

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

        检查所有哈希函数映射的位置计数器是否都大于 0。

        Returns:
            True: 元素可能存在
            False: 元素一定不存在
        """
        indices = self._hash_fn.hash_to_indices(item, self._size)
        return all(self._counters.get(index) > 0 for index in indices)

    def might_contain(self, item: Any) -> bool:
        """检查元素是否可能存在"""
        return item in self

    def remove(self, item: Any) -> bool:
        """
        删除元素

        减少所有哈希函数映射位置的计数器。

        注意: 如果元素不存在，此操作可能导致计数器下溢，
        从而产生假阴性。建议只删除已知存在的元素。

        Args:
            item: 要删除的元素

        Returns:
            True 如果成功删除 (所有计数器都大于 0)
            False 如果元素可能不存在 (某个计数器为 0)

        Time Complexity: O(k)
        """
        # 先检查元素是否存在
        indices = self._hash_fn.hash_to_indices(item, self._size)

        # 如果任何位置计数为 0，元素不存在
        if any(self._counters.get(index) == 0 for index in indices):
            return False

        # 减少所有位置的计数器
        for index in indices:
            self._counters.decrement(index)

        self._count -= 1
        return True

    def clear(self) -> None:
        """
        清空过滤器

        将所有计数器重置为 0。
        """
        self._counters.reset()
        self._count = 0

    def fill_ratio(self) -> float:
        """
        计算非零计数器的比例

        Returns:
            非零计数器占总计数器的比例 (0.0 ~ 1.0)
        """
        return self._counters.fill_ratio()

    def estimated_false_positive_rate(self) -> float:
        """
        估算当前误判率

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
        counter_bytes = self._size  # 每个计数器 1 字节
        return {
            "counter_array_size": self._size,
            "counter_array_bytes": counter_bytes,
            "counter_array_mb": counter_bytes / (1024 * 1024),
            "hash_count": self._hash_count,
            "element_count": self._count,
            "max_count": self._counters.max_count,
        }

    def __len__(self) -> int:
        return self._count

    def __repr__(self) -> str:
        return (
            f"CountingBloomFilter(size={self._size}, hash_count={self._hash_count}, "
            f"count={self._count}, fill_ratio={self.fill_ratio():.4f})"
        )

    @classmethod
    def _optimal_size(cls, n: int, p: float) -> int:
        """计算最优计数器数组大小"""
        m = -(n * math.log(p)) / cls.LN2_SQUARED
        return math.ceil(m)

    @classmethod
    def _optimal_hash_count(cls, m: int, n: int) -> int:
        """计算最优哈希函数数量"""
        k = (m / n) * cls.LN2
        return max(1, round(k))

    @staticmethod
    def _false_positive_rate(m: int, k: int, n: int) -> float:
        """计算误判率"""
        exponent = -k * n / m
        return (1 - math.exp(exponent)) ** k
