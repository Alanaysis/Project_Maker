"""
哈希函数实现

提供布隆过滤器所需的多个独立哈希函数。

实现策略:
    1. DoubleHash: 使用双重哈希技术，从两个基础哈希函数生成 k 个哈希值
       h_i(x) = (h1(x) + i * h2(x)) mod m
       这种方法在实践中效果良好，且计算效率高。

    2. 基于 Python 内置 hash() 和 hashlib 的组合实现。

时间复杂度: O(1) 每个哈希值
"""

import hashlib
import struct
from typing import Any


class HashFunction:
    """
    单个哈希函数

    使用种子值生成不同的哈希函数。

    Args:
        seed: 哈希函数种子值

    Examples:
        >>> hf = HashFunction(seed=42)
        >>> hf.hash("hello") != hf.hash("world")
        True
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def hash(self, item: Any) -> int:
        """
        计算哈希值

        Args:
            item: 要哈希的对象

        Returns:
            64 位无符号整数哈希值
        """
        data = self._to_bytes(item)
        # 使用 SHA-256 的前 8 字节作为哈希值
        seed_bytes = struct.pack(">Q", self._seed & 0xFFFFFFFFFFFFFFFF)
        h = hashlib.sha256(seed_bytes + data).digest()
        return struct.unpack(">Q", h[:8])[0]

    def hash_to_index(self, item: Any, size: int) -> int:
        """
        计算哈希值并映射到 [0, size) 范围

        Args:
            item: 要哈希的对象
            size: 位数组大小

        Returns:
            [0, size) 范围内的索引
        """
        return self.hash(item) % size

    @staticmethod
    def _to_bytes(item: Any) -> bytes:
        """将对象转换为字节串"""
        if isinstance(item, bytes):
            return item
        if isinstance(item, str):
            return item.encode("utf-8")
        if isinstance(item, (int, float)):
            return str(item).encode("utf-8")
        return str(item).encode("utf-8")

    def __repr__(self) -> str:
        return f"HashFunction(seed={self._seed})"


class DoubleHashFunction:
    """
    双重哈希函数

    使用双重哈希技术从两个基础哈希函数生成 k 个哈希值。
    公式: h_i(x) = (h1(x) + i * h2(x)) mod m

    这种方法的优势:
    1. 只需计算两个哈希值，即可生成任意多个哈希值
    2. 计算效率高
    3. 哈希值之间具有良好的独立性

    Args:
        hash_count: 需要生成的哈希函数数量

    Examples:
        >>> dhf = DoubleHashFunction(hash_count=5)
        >>> indices = dhf.hash_to_indices("hello", 1000)
        >>> len(indices)
        5
        >>> all(0 <= i < 1000 for i in indices)
        True
    """

    def __init__(self, hash_count: int):
        if hash_count <= 0:
            raise ValueError(f"hash_count must be positive, got {hash_count}")

        self._hash_count = hash_count
        self._h1 = HashFunction(seed=0x5BD1E995)
        self._h2 = HashFunction(seed=0x1B873593)

    @property
    def hash_count(self) -> int:
        return self._hash_count

    def hash(self, item: Any, index: int) -> int:
        """
        计算第 i 个哈希值

        Args:
            item: 要哈希的对象
            index: 哈希函数索引 (0 <= index < hash_count)

        Returns:
            64 位无符号整数哈希值
        """
        if not 0 <= index < self._hash_count:
            raise IndexError(
                f"index {index} out of range [0, {self._hash_count})"
            )

        h1 = self._h1.hash(item)
        h2 = self._h2.hash(item)

        # 双重哈希: h_i = h1 + i * h2
        # 使用大质数模运算避免溢出
        MOD = (1 << 64) - 1  # 2^64 - 1，大质数
        return (h1 + index * h2) % MOD

    def hash_to_index(self, item: Any, size: int, index: int) -> int:
        """
        计算第 i 个哈希值并映射到 [0, size) 范围

        Args:
            item: 要哈希的对象
            size: 位数组大小
            index: 哈希函数索引

        Returns:
            [0, size) 范围内的索引
        """
        return self.hash(item, index) % size

    def hash_to_indices(self, item: Any, size: int) -> list[int]:
        """
        计算所有 k 个哈希值并映射到位数组索引

        Args:
            item: 要哈希的对象
            size: 位数组大小

        Returns:
            k 个索引的列表
        """
        return [self.hash_to_index(item, size, i) for i in range(self._hash_count)]

    def __repr__(self) -> str:
        return f"DoubleHashFunction(hash_count={self._hash_count})"


def create_hash_functions(count: int) -> list[HashFunction]:
    """
    创建多个独立的哈希函数

    Args:
        count: 需要创建的哈希函数数量

    Returns:
        HashFunction 对象列表

    Examples:
        >>> fns = create_hash_functions(5)
        >>> len(fns)
        5
    """
    return [HashFunction(seed=i * 31 + 7) for i in range(count)]


def mmh3_hash(item: Any, seed: int = 0) -> int:
    """
    MurmurHash3 32-bit 哈希函数的纯 Python 实现

    这是一个简单但高效的哈希函数，适用于非密码学场景。

    Args:
        item: 要哈希的对象
        seed: 种子值

    Returns:
        32 位哈希值
    """
    data = HashFunction._to_bytes(item)

    c1 = 0xCC9E2D51
    c2 = 0x1B873593
    r1 = 15
    r2 = 13
    m = 5
    n = 0xE6546B64

    hash_val = seed & 0xFFFFFFFF
    length = len(data)

    # 处理 4 字节块
    nblocks = length // 4
    for i in range(nblocks):
        k = struct.unpack("<I", data[i * 4 : (i + 1) * 4])[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        hash_val ^= k
        hash_val = ((hash_val << r2) | (hash_val >> (32 - r2))) & 0xFFFFFFFF
        hash_val = (hash_val * m + n) & 0xFFFFFFFF

    # 处理尾部
    tail = data[nblocks * 4 :]
    k = 0
    if len(tail) >= 3:
        k ^= tail[2] << 16
    if len(tail) >= 2:
        k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        hash_val ^= k

    # 最终混合
    hash_val ^= length
    hash_val ^= hash_val >> 16
    hash_val = (hash_val * 0x85EBCA6B) & 0xFFFFFFFF
    hash_val ^= hash_val >> 13
    hash_val = (hash_val * 0xC2B2AE35) & 0xFFFFFFFF
    hash_val ^= hash_val >> 16

    return hash_val
