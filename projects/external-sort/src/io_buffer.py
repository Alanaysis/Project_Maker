"""
I/O 缓冲区管理

实现带缓冲的文件读写，支持:
- 读缓冲区 (BufferedReader)
- 写缓冲区 (BufferedWriter)
- 自动刷新机制
- 内存使用监控
"""

import os
from typing import Any, BinaryIO, List, Optional, TextIO, Union


class IOBuffer:
    """
    I/O 缓冲区基类

    管理内存缓冲区和文件句柄之间的数据传输。
    """

    def __init__(self, buffer_size: int = 1024 * 1024):
        """
        初始化 I/O 缓冲区。

        Args:
            buffer_size: 缓冲区大小（字节），默认 1MB
        """
        self._buffer_size = buffer_size
        self._buffer: List[Any] = []
        self._bytes_used = 0
        self._flush_count = 0

    @property
    def buffer_size(self) -> int:
        """缓冲区大小（字节）"""
        return self._buffer_size

    @property
    def bytes_used(self) -> int:
        """当前缓冲区使用的字节数"""
        return self._bytes_used

    @property
    def flush_count(self) -> int:
        """刷新次数"""
        return self._flush_count

    @property
    def is_full(self) -> bool:
        """缓冲区是否已满"""
        return self._bytes_used >= self._buffer_size

    def clear(self) -> None:
        """清空缓冲区"""
        self._buffer.clear()
        self._bytes_used = 0

    def _estimate_size(self, item: Any) -> int:
        """
        估算单个元素的字节大小。

        Args:
            item: 要估算的元素

        Returns:
            估算的字节数
        """
        if isinstance(item, (int, float)):
            return 8
        elif isinstance(item, str):
            return len(item.encode('utf-8')) + 4  # +4 for length prefix
        elif isinstance(item, bytes):
            return len(item) + 4
        elif isinstance(item, (list, tuple)):
            return sum(self._estimate_size(x) for x in item) + 8
        elif isinstance(item, dict):
            return sum(
                self._estimate_size(k) + self._estimate_size(v)
                for k, v in item.items()
            ) + 8
        else:
            return 64  # 默认估算


class BufferedWriter(IOBuffer):
    """
    写缓冲区

    将数据先写入内存缓冲区，当缓冲区满或手动刷新时
    才写入文件，减少 I/O 次数。
    """

    def __init__(self, filepath: str, buffer_size: int = 1024 * 1024,
                 append: bool = False):
        """
        初始化写缓冲区。

        Args:
            filepath: 输出文件路径
            buffer_size: 缓冲区大小（字节）
            append: 是否追加模式
        """
        super().__init__(buffer_size)
        self._filepath = filepath
        self._mode = 'ab' if append else 'wb'
        self._file: Optional[BinaryIO] = None
        self._total_written = 0
        self._record_count = 0

    def open(self) -> 'BufferedWriter':
        """打开文件"""
        self._file = open(self._filepath, self._mode)
        return self

    def close(self) -> None:
        """刷新缓冲区并关闭文件"""
        if self._file:
            self.flush()
            self._file.close()
            self._file = None

    def __enter__(self) -> 'BufferedWriter':
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def write(self, item: Any) -> None:
        """
        写入单个元素到缓冲区。

        当缓冲区满时自动刷新。

        Args:
            item: 要写入的元素
        """
        self._buffer.append(item)
        self._bytes_used += self._estimate_size(item)
        self._record_count += 1

        if self.is_full:
            self.flush()

    def write_batch(self, items: List[Any]) -> None:
        """
        批量写入元素。

        Args:
            items: 要写入的元素列表
        """
        for item in items:
            self.write(item)

    def flush(self) -> None:
        """
        将缓冲区内容写入文件。
        """
        if not self._buffer or not self._file:
            return

        # 将每个元素转换为一行文本写入
        for item in self._buffer:
            if isinstance(item, (int, float)):
                line = f"{item}\n"
            elif isinstance(item, str):
                line = item + "\n"
            elif isinstance(item, bytes):
                self._file.write(item + b"\n")
                self._total_written += len(item) + 1
                continue
            else:
                line = str(item) + "\n"

            encoded = line.encode('utf-8')
            self._file.write(encoded)
            self._total_written += len(encoded)

        self._flush_count += 1
        self.clear()

    @property
    def total_written(self) -> int:
        """总共写入的字节数"""
        return self._total_written

    @property
    def record_count(self) -> int:
        """总共写入的记录数"""
        return self._record_count

    def write_delimiter(self, delimiter: str = "---") -> None:
        """
        写入分隔符（用于分隔不同的 run）。

        Args:
            delimiter: 分隔符字符串
        """
        if self._file:
            self._file.write((delimiter + "\n").encode('utf-8'))


class BufferedReader(IOBuffer):
    """
    读缓冲区

    从文件批量读取数据到内存缓冲区，
    减少文件 I/O 次数。
    """

    def __init__(self, filepath: str, buffer_size: int = 1024 * 1024):
        """
        初始化读缓冲区。

        Args:
            filepath: 输入文件路径
            buffer_size: 缓冲区大小（字节）
        """
        super().__init__(buffer_size)
        self._filepath = filepath
        self._file: Optional[TextIO] = None
        self._eof = False
        self._position = 0
        self._total_read = 0
        self._record_count = 0

    def open(self) -> 'BufferedReader':
        """打开文件"""
        self._file = open(self._filepath, 'r', encoding='utf-8')
        self._eof = False
        self._position = 0
        return self

    def close(self) -> None:
        """关闭文件"""
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self) -> 'BufferedReader':
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _fill_buffer(self) -> None:
        """从文件读取数据填充缓冲区"""
        if self._eof or not self._file:
            return

        self.clear()
        bytes_read = 0

        while bytes_read < self._buffer_size:
            line = self._file.readline()
            if not line:
                self._eof = True
                break

            line = line.rstrip('\n')
            if line:
                self._buffer.append(line)
                bytes_read += len(line.encode('utf-8'))
                self._record_count += 1

        self._bytes_used = bytes_read
        self._total_read += bytes_read
        self._position = 0

    def read(self) -> Optional[Any]:
        """
        读取下一个元素。

        Returns:
            下一个元素，如果到达文件末尾返回 None
        """
        if not self._buffer or self._position >= len(self._buffer):
            self._fill_buffer()
            if not self._buffer:
                return None

        if self._position < len(self._buffer):
            item = self._buffer[self._position]
            self._position += 1
            return item

        return None

    def read_batch(self, count: int) -> List[Any]:
        """
        批量读取元素。

        Args:
            count: 要读取的元素数量

        Returns:
            读取到的元素列表
        """
        result = []
        for _ in range(count):
            item = self.read()
            if item is None:
                break
            result.append(item)
        return result

    def read_all(self) -> List[Any]:
        """
        读取所有剩余元素。

        Returns:
            所有剩余元素的列表
        """
        result = []
        while True:
            item = self.read()
            if item is None:
                break
            result.append(item)
        return result

    @property
    def eof(self) -> bool:
        """是否到达文件末尾"""
        return self._eof and (
            not self._buffer or self._position >= len(self._buffer)
        )

    @property
    def total_read(self) -> int:
        """总共读取的字节数"""
        return self._total_read

    @property
    def record_count(self) -> int:
        """总共读取的记录数"""
        return self._record_count


class RunBuffer:
    """
    归并段缓冲区

    专门用于管理归并段的读写操作。
    支持写入一个完整的归并段，以及读取多个归并段进行归并。
    """

    def __init__(self, max_memory: int = 1024 * 1024):
        """
        初始化归并段缓冲区。

        Args:
            max_memory: 最大可用内存（字节）
        """
        self._max_memory = max_memory
        self._run_buffer: List[Any] = []
        self._bytes_used = 0
        self._run_count = 0

    @property
    def max_memory(self) -> int:
        """最大可用内存"""
        return self._max_memory

    @property
    def available_memory(self) -> int:
        """可用内存"""
        return self._max_memory - self._bytes_used

    @property
    def is_full(self) -> bool:
        """缓冲区是否已满"""
        return self._bytes_used >= self._max_memory

    @property
    def bytes_used(self) -> int:
        """当前使用的字节数"""
        return self._bytes_used

    @property
    def run_count(self) -> int:
        """归并段数量"""
        return self._run_count

    def add(self, item: Any) -> bool:
        """
        添加元素到当前归并段。

        Args:
            item: 要添加的元素

        Returns:
            添加是否成功（缓冲区未满）
        """
        item_size = self._estimate_size(item)
        if self._bytes_used + item_size > self._max_memory:
            return False

        self._run_buffer.append(item)
        self._bytes_used += item_size
        return True

    def sort(self, key_func=None) -> None:
        """对当前归并段排序"""
        if key_func:
            self._run_buffer.sort(key=key_func)
        else:
            self._run_buffer.sort()

    def get_run(self) -> List[Any]:
        """
        获取排序后的归并段并重置缓冲区。

        Returns:
            排序后的归并段
        """
        run = self._run_buffer.copy()
        self._run_buffer.clear()
        self._bytes_used = 0
        self._run_count += 1
        return run

    def clear(self) -> None:
        """清空缓冲区"""
        self._run_buffer.clear()
        self._bytes_used = 0

    def _estimate_size(self, item: Any) -> int:
        """估算元素大小"""
        if isinstance(item, (int, float)):
            return 8
        elif isinstance(item, str):
            return len(item.encode('utf-8')) + 4
        else:
            return 64
