"""
分块模块 (Chunk Module)

负责将大文件分割成适合内存处理的块。
每个块在内存中排序后写入临时文件，形成有序段 (run)。

Chunk Module:
Responsible for splitting large files into chunks that fit in memory.
Each chunk is sorted in memory and written to a temporary file, forming
an ordered run.
"""

import os
import tempfile
import logging
from typing import List, Generator, Tuple

logger = logging.getLogger(__name__)


class Chunk:
    """
    表示一个已排序的数据块 (run)。

    A sorted data block (run).
    """

    def __init__(self, filepath: str, size_bytes: int, record_count: int):
        self.filepath = filepath
        self.size_bytes = size_bytes
        self.record_count = record_count

    def __repr__(self):
        return (f"Chunk(path='{os.path.basename(self.filepath)}', "
                f"records={self.record_count}, "
                f"size={self.size_bytes} bytes)")


def split_file_into_chunks(filepath: str,
                           max_chunk_size: int = 1024 * 1024,
                           temp_dir: str = None) -> Generator[List[int], None, None]:
    """
    将文件按行分割成块，每块最多 max_chunk_size 字节。

    Split a file into chunks by lines, each chunk at most max_chunk_size bytes.

    外部排序的第一步：将大文件分块。
    Step 1 of external sorting: split large file into chunks.

    Args:
        filepath: 输入文件路径 (input file path)
        max_chunk_size: 每块的最大字节数 (max bytes per chunk)
        temp_dir: 临时目录 (temp directory)

    Yields:
        每块的内容作为整数列表 (content of each chunk as list of integers)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    chunk_size = 0
    current_chunk = []

    with open(filepath, 'r') as f:
        for line in f:
            line_bytes = len(line.encode('utf-8'))
            # 如果当前块为空或添加当前行不会超过限制，则添加
            if not current_chunk or chunk_size + line_bytes <= max_chunk_size:
                current_chunk.append(int(line.strip()))
                chunk_size += line_bytes
            else:
                # 当前块已满，yield 并重置
                yield current_chunk
                current_chunk = [int(line.strip())]
                chunk_size = line_bytes

    # yield 最后一个块
    if current_chunk:
        yield current_chunk


def create_temp_file(suffix: str = '.txt',
                     prefix='external-sort-chunk-',
                     temp_dir: str = None) -> str:
    """
    创建临时文件并返回其路径。

    Create a temp file and return its path.
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=temp_dir)
    os.close(fd)
    return path


def compute_chunk_size(available_memory_bytes: int,
                       safety_factor: float = 0.5) -> int:
    """
    根据可用内存计算安全的块大小。

    Compute safe chunk size based on available memory.

    使用安全系数确保不会耗尽内存。
    Uses a safety factor to avoid exhausting memory.

    Args:
        available_memory_bytes: 可用内存字节数
        safety_factor: 安全系数 (0.0-1.0)，越低越保守
    """
    return int(available_memory_bytes * safety_factor)


def get_available_memory() -> int:
    """
    获取系统可用内存字节数。

    Get available system memory in bytes.
    """
    try:
        import resource
        # Linux/macOS
        avail = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        # 使用一半作为安全限制
        return avail // 2
    except ImportError:
        # Windows fallback
        import psutil
        avail = psutil.virtual_memory().available
        return avail // 2
