"""
可扩展布隆过滤器 (Scalable Bloom Filter) 实现

可扩展布隆过滤器能够动态扩容，当元素数量超过预期时自动创建新的布隆过滤器。

参考论文:
    Almeida, P. S., Baquero, C., Preguica, N., & Hutchison, D. (2007).
    Scalable Bloom Filters.

特性:
    - 动态扩容: 当误判率超过阈值时自动创建新过滤器
    - 渐进式收紧: 每层的误判率递减，保证总体误判率不超过目标
    - 空间效率: 仅在需要时分配新空间
    - 不支持删除 (标准布隆过滤器的限制)

扩容策略:
    - 初始过滤器使用目标误判率 p
    - 每次扩容，新过滤器的误判率为 p * r^i (r < 1，如 0.5)
    - 总体误判率不超过 p / (1 - r)

时间复杂度:
    - 插入: O(k * L)，L 为过滤器层数
    - 查询: O(k * L)

空间复杂度: 动态增长
"""

import math
from typing import Any, Iterator

from .bloom_filter import BloomFilter


class ScalableBloomFilter:
    """
    可扩展布隆过滤器

    当元素数量超过当前容量时，自动创建新的布隆过滤器层。

    Args:
        initial_capacity: 初始容量 (每层的预期元素数量)
        false_positive_rate: 目标误判率
        scaling_factor: 扩容因子 (默认 2.0，每层容量翻倍)
        tightening_ratio: 误判率收紧比例 (默认 0.5)

    Examples:
        >>> sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)
        >>> for i in range(10000):
        ...     sbf.add(f"item_{i}")
        >>> f"item_0" in sbf
        True
        >>> f"nonexistent" in sbf
        False
        >>> sbf.layer_count
        5  # 自动创建了多层
    """

    def __init__(
        self,
        initial_capacity: int = 10000,
        false_positive_rate: float = 0.01,
        scaling_factor: float = 2.0,
        tightening_ratio: float = 0.5,
    ):
        if initial_capacity <= 0:
            raise ValueError(f"initial_capacity must be positive, got {initial_capacity}")
        if not (0 < false_positive_rate < 1):
            raise ValueError(f"false_positive_rate must be in (0, 1), got {false_positive_rate}")
        if scaling_factor <= 1.0:
            raise ValueError(f"scaling_factor must be > 1.0, got {scaling_factor}")
        if not (0 < tightening_ratio < 1):
            raise ValueError(f"tightening_ratio must be in (0, 1), got {tightening_ratio}")

        self._initial_capacity = initial_capacity
        self._false_positive_rate = false_positive_rate
        self._scaling_factor = scaling_factor
        self._tightening_ratio = tightening_ratio

        self._layers: list[_FilterLayer] = []
        self._total_count = 0

        # 创建初始层
        self._add_layer()

    @property
    def layer_count(self) -> int:
        """过滤器层数"""
        return len(self._layers)

    @property
    def count(self) -> int:
        """总元素数量"""
        return self._total_count

    @property
    def current_capacity(self) -> int:
        """当前总容量"""
        return sum(layer.capacity for layer in self._layers)

    @property
    def false_positive_rate(self) -> float:
        """目标误判率"""
        return self._false_positive_rate

    def add(self, item: Any) -> None:
        """
        插入元素

        如果当前层已满，自动创建新层。

        Args:
            item: 要插入的元素

        Time Complexity: O(k * L)
        """
        # 检查当前层是否已满
        current_layer = self._layers[-1]
        if current_layer.is_full():
            self._add_layer()
            current_layer = self._layers[-1]

        # 检查是否已存在于任何层
        if item not in self:
            current_layer.filter.add(item)
            self._total_count += 1
        else:
            # 元素已存在，仍然插入当前层以保持一致性
            current_layer.filter.add(item)
            self._total_count += 1

    def add_many(self, items: Iterator[Any]) -> int:
        """
        批量插入元素

        Args:
            items: 元素迭代器

        Returns:
            插入的元素数量
        """
        count = 0
        for item in items:
            self.add(item)
            count += 1
        return count

    def __contains__(self, item: Any) -> bool:
        """
        检查元素是否可能存在

        检查所有层中是否存在。

        Returns:
            True: 元素可能存在
            False: 元素一定不存在
        """
        return any(item in layer.filter for layer in self._layers)

    def might_contain(self, item: Any) -> bool:
        """检查元素是否可能存在"""
        return item in self

    def clear(self) -> None:
        """
        清空所有层

        保留第一层，删除其他层。
        """
        while len(self._layers) > 1:
            self._layers.pop()
        self._layers[0].filter.clear()
        self._total_count = 0

    def estimated_false_positive_rate(self) -> float:
        """
        估算当前总体误判率

        总体误判率 = 1 - ∏(1 - p_i)

        Returns:
            估算的总体误判率
        """
        if self._total_count == 0:
            return 0.0

        # 计算所有层的误判率
        p_no_fp = 1.0
        for layer in self._layers:
            p_layer = layer.filter.estimated_false_positive_rate()
            p_no_fp *= (1 - p_layer)

        return 1 - p_no_fp

    def layer_info(self) -> list[dict]:
        """
        获取各层信息

        Returns:
            包含各层信息的字典列表
        """
        return [
            {
                "index": i,
                "size": layer.filter.size,
                "hash_count": layer.filter.hash_count,
                "capacity": layer.capacity,
                "count": layer.filter.count,
                "fill_ratio": layer.filter.fill_ratio(),
                "estimated_fpr": layer.filter.estimated_false_positive_rate(),
            }
            for i, layer in enumerate(self._layers)
        ]

    def memory_usage(self) -> dict:
        """
        估算内存使用量

        Returns:
            包含内存使用信息的字典
        """
        total_bytes = 0
        for layer in self._layers:
            total_bytes += (layer.filter.size + 7) // 8

        return {
            "layer_count": self.layer_count,
            "total_bytes": total_bytes,
            "total_mb": total_bytes / (1024 * 1024),
            "total_count": self._total_count,
        }

    def __len__(self) -> int:
        return self._total_count

    def __repr__(self) -> str:
        return (
            f"ScalableBloomFilter(layers={self.layer_count}, count={self._total_count}, "
            f"capacity={self.current_capacity}, fpr={self.estimated_false_positive_rate():.6f})"
        )

    def _add_layer(self) -> None:
        """添加新的一层"""
        layer_index = len(self._layers)

        # 计算新层的容量
        capacity = int(self._initial_capacity * (self._scaling_factor ** layer_index))

        # 计算新层的误判率 (渐进式收紧)
        layer_fpr = self._false_positive_rate * (self._tightening_ratio ** layer_index)

        # 确保误判率不会太小
        layer_fpr = max(layer_fpr, 1e-10)

        # 创建新层
        bloom = BloomFilter(expected_items=capacity, false_positive_rate=layer_fpr)
        layer = _FilterLayer(filter=bloom, capacity=capacity)
        self._layers.append(layer)


class _FilterLayer:
    """过滤器层"""

    def __init__(self, filter: BloomFilter, capacity: int):
        self.filter = filter
        self.capacity = capacity

    def is_full(self) -> bool:
        """检查是否已满"""
        return self.filter.count >= self.capacity

    def __repr__(self) -> str:
        return f"FilterLayer(capacity={self.capacity}, count={self.filter.count})"
