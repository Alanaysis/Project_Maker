"""
位数组 (Bit Array) 实现

使用 Python 整数的位操作实现紧凑的位数组存储。
相比 list[bool] 节省约 8 倍内存。

时间复杂度:
    - get/set: O(1)
    - clear: O(n/64)
    - count_set_bits: O(n/64)

空间复杂度: O(n/8) 字节
"""

from typing import Optional


class BitArray:
    """
    紧凑位数组实现

    使用 Python 整数数组存储位，每个整数存储 64 位。

    Args:
        size: 位数组大小（位数）

    Examples:
        >>> bits = BitArray(100)
        >>> bits.set(42)
        >>> bits.get(42)
        True
        >>> bits.get(43)
        False
        >>> bits.count_set_bits()
        1
    """

    BITS_PER_WORD = 64

    def __init__(self, size: int):
        if size <= 0:
            raise ValueError(f"size must be positive, got {size}")

        self._size = size
        word_count = (size + self.BITS_PER_WORD - 1) // self.BITS_PER_WORD
        self._words = [0] * word_count

    @property
    def size(self) -> int:
        """返回位数组大小"""
        return self._size

    def get(self, index: int) -> bool:
        """
        获取指定位的值

        Args:
            index: 位索引 (0 <= index < size)

        Returns:
            该位的值 (True/False)

        Raises:
            IndexError: 索引超出范围
        """
        self._check_index(index)
        word_index = index // self.BITS_PER_WORD
        bit_offset = index % self.BITS_PER_WORD
        return bool(self._words[word_index] & (1 << bit_offset))

    def set(self, index: int) -> None:
        """
        将指定位设为 1

        Args:
            index: 位索引 (0 <= index < size)

        Raises:
            IndexError: 索引超出范围
        """
        self._check_index(index)
        word_index = index // self.BITS_PER_WORD
        bit_offset = index % self.BITS_PER_WORD
        self._words[word_index] |= (1 << bit_offset)

    def clear(self, index: int) -> None:
        """
        将指定位设为 0

        Args:
            index: 位索引 (0 <= index < size)

        Raises:
            IndexError: 索引超出范围
        """
        self._check_index(index)
        word_index = index // self.BITS_PER_WORD
        bit_offset = index % self.BITS_PER_WORD
        self._words[word_index] &= ~(1 << bit_offset)

    def reset(self) -> None:
        """将所有位重置为 0"""
        for i in range(len(self._words)):
            self._words[i] = 0

    def count_set_bits(self) -> int:
        """
        统计值为 1 的位数

        使用 popcount 算法计算。

        Returns:
            值为 1 的位数
        """
        count = 0
        for word in self._words:
            count += bin(word).count("1")
        return count

    def fill_ratio(self) -> float:
        """
        计算填充率

        Returns:
            值为 1 的位数占总位数的比例 (0.0 ~ 1.0)
        """
        if self._size == 0:
            return 0.0
        return self.count_set_bits() / self._size

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, index: int) -> bool:
        return self.get(index)

    def __setitem__(self, index: int, value: bool) -> None:
        if value:
            self.set(index)
        else:
            self.clear(index)

    def __repr__(self) -> str:
        set_count = self.count_set_bits()
        return f"BitArray(size={self._size}, set={set_count}, ratio={self.fill_ratio():.4f})"

    def _check_index(self, index: int) -> None:
        if not 0 <= index < self._size:
            raise IndexError(
                f"index {index} out of range [0, {self._size})"
            )


class CountingArray:
    """
    计数数组实现

    用于计数布隆过滤器，每个位置存储一个计数器而非单个位。

    Args:
        size: 数组大小
        max_count: 最大计数值 (默认 255，即 8 位计数器)

    Examples:
        >>> counters = CountingArray(100)
        >>> counters.increment(42)
        >>> counters.get(42)
        1
        >>> counters.increment(42)
        >>> counters.get(42)
        2
        >>> counters.decrement(42)
        >>> counters.get(42)
        1
    """

    def __init__(self, size: int, max_count: int = 255):
        if size <= 0:
            raise ValueError(f"size must be positive, got {size}")
        if max_count <= 0 or max_count > 255:
            raise ValueError(f"max_count must be in (0, 255], got {max_count}")

        self._size = size
        self._max_count = max_count
        self._counters = [0] * size

    @property
    def size(self) -> int:
        return self._size

    @property
    def max_count(self) -> int:
        return self._max_count

    def get(self, index: int) -> int:
        """获取指定位置的计数值"""
        self._check_index(index)
        return self._counters[index]

    def increment(self, index: int) -> bool:
        """
        增加指定位置的计数值

        Args:
            index: 数组索引

        Returns:
            True 如果成功增加，False 如果已达到最大值
        """
        self._check_index(index)
        if self._counters[index] >= self._max_count:
            return False
        self._counters[index] += 1
        return True

    def decrement(self, index: int) -> bool:
        """
        减少指定位置的计数值

        Args:
            index: 数组索引

        Returns:
            True 如果成功减少，False 如果已经为 0
        """
        self._check_index(index)
        if self._counters[index] <= 0:
            return False
        self._counters[index] -= 1
        return True

    def is_zero(self, index: int) -> bool:
        """检查指定位置的计数是否为 0"""
        return self.get(index) == 0

    def reset(self) -> None:
        """将所有计数器重置为 0"""
        for i in range(self._size):
            self._counters[i] = 0

    def count_nonzero(self) -> int:
        """统计非零计数器的数量"""
        return sum(1 for c in self._counters if c > 0)

    def fill_ratio(self) -> float:
        """计算非零计数器的比例"""
        if self._size == 0:
            return 0.0
        return self.count_nonzero() / self._size

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, index: int) -> int:
        return self.get(index)

    def __repr__(self) -> str:
        nonzero = self.count_nonzero()
        return f"CountingArray(size={self._size}, nonzero={nonzero})"

    def _check_index(self, index: int) -> None:
        if not 0 <= index < self._size:
            raise IndexError(
                f"index {index} out of range [0, {self._size})"
            )
