"""
I/O 缓冲优化模块 (I/O Buffering Optimization Module)

提供 I/O 优化技术，减少外部排序中的磁盘访问次数。
包括：缓冲读取、写合并、预读取等策略。

I/O Buffering Optimization Module:
Provides I/O optimization techniques to reduce disk accesses
during external sorting. Includes: buffered reading, write combining,
and read-ahead strategies.
"""

import os
import logging
import threading
from typing import List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class BufferedWriter:
    """
    缓冲写入器：将多次小写合并为少量大写。

    Buffered writer: combines many small writes into fewer large writes.

    减少 write() 系统调用次数，提高 I/O 效率。
    Reduces write() syscalls, improving I/O efficiency.
    """

    def __init__(self, filepath: str, buffer_size: int = 65536):
        self.filepath = filepath
        self.buffer_size = buffer_size
        self._buffer = []
        self._buffer_bytes = 0
        self._file = open(filepath, 'w')
        self._total_written = 0

    def write(self, line: str):
        """写入一行数据，缓冲不满时不刷盘。"""
        line_bytes = len(line.encode('utf-8'))

        # 如果当前缓冲 + 新行超过限制，先刷盘
        if self._buffer_bytes + line_bytes > self.buffer_size and self._buffer:
            self._flush()

        self._buffer.append(line)
        self._buffer_bytes += line_bytes
        self._total_written += line_bytes

    def _flush(self):
        """刷新缓冲到磁盘。"""
        if self._buffer:
            self._file.writelines(self._buffer)
            self._buffer.clear()
            self._buffer_bytes = 0

    def close(self):
        """关闭写入器，确保所有数据写入磁盘。"""
        self._flush()
        self._file.close()

    @property
    def total_written(self) -> int:
        return self._total_written

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class BufferedReader:
    """
    缓冲读取器：批量读取行，减少 read() 系统调用。

    Buffered reader: reads lines in batches, reducing read() syscalls.
    """

    def __init__(self, filepath: str, buffer_size: int = 65536):
        self.filepath = filepath
        self.buffer_size = buffer_size
        self._file = open(filepath, 'r')
        self._buffer = deque()
        self._exhausted = False
        self._total_read = 0

    def read_line(self) -> Optional[str]:
        """读取下一行。"""
        while not self._buffer:
            if self._exhausted:
                return None
            lines = self._file.readlines(self.buffer_size)
            if not lines:
                self._exhausted = True
                return None
            self._buffer = deque(line.strip() for line in lines if line.strip())

        self._total_read += 1
        return self._buffer.popleft()

    def close(self):
        """关闭读取器。"""
        if not self._file.closed:
            self._file.close()

    @property
    def total_read(self) -> int:
        return self._total_read

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class WriteCombiningSorter:
    """
    写合并排序器：将多个有序流的写入合并优化。

    Write-combining sorter: merges writes from multiple sorted streams.

    在 k 路归并中，交替写入不同 run 可能导致磁盘头频繁跳动。
    写合并策略减少这种 seek 开销。

    In k-way merge, alternating writes to different runs can cause
    frequent disk head seeks. Write combining reduces this overhead.
    """

    def __init__(self, output_path: str, write_buffer_size: int = 131072):
        self.output_path = output_path
        self.write_buffer_size = write_buffer_size
        self._results = []
        self._total_written = 0

    def add_result(self, value: int):
        """添加一个排序结果。"""
        self._results.append(f"{value}\n")
        self._total_written += 1

        # 缓冲满时写入
        if len(self._results) >= 10000:
            self._flush()

    def _flush(self):
        """批量写入结果。"""
        if self._results:
            with open(self.output_path, 'a') as f:
                f.writelines(self._results)
            self._results.clear()

    def finalize(self) -> int:
        """完成写入，返回总记录数。"""
        self._flush()
        return self._total_written


def optimize_io_for_merge(num_files: int,
                          file_size_mb: float,
                          available_memory_mb: float) -> dict:
    """
    为归并阶段优化 I/O 策略。

    Optimize I/O strategy for merge phase.

    根据文件数量和大小推荐最佳 I/O 参数。

    Recommends optimal I/O parameters based on file count and size.
    """
    # 缓冲大小建议
    if file_size_mb < 10:
        buffer_size = 8192  # 小文件用小缓冲
    elif file_size_mb < 100:
        buffer_size = 65536  # 中等文件用 64KB 缓冲
    else:
        buffer_size = 262144  # 大文件用 256KB 缓冲

    # 每路归并的文件数建议
    ideal_merge_k = min(num_files, int(available_memory_mb / 2))
    ideal_merge_k = max(2, ideal_merge_k)

    return {
        'recommended_buffer_size': buffer_size,
        'ideal_merge_degree': ideal_merge_k,
        'num_files': num_files,
        'file_size_mb': file_size_mb,
        'available_memory_mb': available_memory_mb,
    }
