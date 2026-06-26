"""
多路归并模块 (K-Way Merge Module)

实现 k 路归并算法，用于合并多个有序文件。
这是外部排序的第二阶段：将多个有序段合并为一个有序文件。

K-Way Merge Module:
Implements k-way merge algorithm to merge multiple sorted files.
This is Phase 2 of external sorting: merge sorted runs into one.
"""

import heapq
import os
import logging
from typing import List, Iterator, Tuple, Optional

logger = logging.getLogger(__name__)


class FileIterator:
    """
    封装文件行的迭代器，支持缓冲读取。

    Wrap file line iteration with buffering support.

    使用缓冲读取减少 I/O 系统调用次数。
    Uses buffered reading to reduce I/O syscalls.
    """

    def __init__(self, filepath: str, buffer_size: int = 8192):
        self.filepath = filepath
        self.buffer_size = buffer_size
        self.file = open(filepath, 'r')
        self._buffer = []
        self._pos = 0
        self._exhausted = False

    def __iter__(self):
        return self

    def __next__(self) -> int:
        while True:
            if self._pos < len(self._buffer):
                val = int(self._buffer[self._pos])
                self._pos += 1
                return val
            else:
                # 缓冲耗尽，重新读取
                lines = self.file.readlines(self.buffer_size)
                if not lines:
                    self._exhausted = True
                    raise StopIteration
                self._buffer = [line.strip() for line in lines
                                if line.strip()]
                self._pos = 0

    def close(self):
        """关闭文件资源。"""
        if not self.file.closed:
            self.file.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class HeapEntry:
    """
    优先队列中的堆条目。

    Heap entry for the priority queue.

    使用 (value, file_id, value_id) 三元组避免比较整数时的冲突。
    Uses (value, file_id, value_id) tuple to avoid comparison issues.
    """

    def __init__(self, value: int, file_id: int, value_id: int):
        self.value = value
        self.file_id = file_id
        self.value_id = value_id

    def __lt__(self, other):
        return self.value < other.value


def k_way_merge(filepaths: List[str],
                output_path: str,
                k: Optional[int] = None,
                buffer_size: int = 8192) -> dict:
    """
    k 路归并：将 k 个有序文件合并为一个有序文件。

    K-way merge: merge k sorted files into one sorted file.

    使用最小堆维护 k 个文件当前最小值的关系。
    Uses a min-heap to maintain relationships among current minimums
    of k files.

    算法步骤：
    1. 从每个文件读取第一个值，放入最小堆
    2. 弹出堆最小值，写入输出文件
    3. 从弹出值对应文件读取下一个值，放入堆
    4. 重复直到所有文件耗尽

    Algorithm steps:
    1. Read first value from each file, push to min-heap
    2. Pop min from heap, write to output
    3. Read next value from the popped file, push to heap
    4. Repeat until all files exhausted

    Args:
        filepaths: 有序文件路径列表 (sorted file paths)
        output_path: 输出文件路径 (output file path)
        k: 归并路数，默认等于文件数 (merge degree, defaults to num files)
        buffer_size: 读取缓冲大小 (read buffer size)

    Returns:
        归并统计信息 (merge statistics)
    """
    if not filepaths:
        raise ValueError("No input files provided")

    # k 不能超过文件数
    k = k or len(filepaths)
    k = min(k, len(filepaths))

    # 创建每个文件的迭代器
    iterators = []
    for fp in filepaths:
        if not os.path.exists(fp):
            raise FileNotFoundError(f"File not found: {fp}")
        iterators.append(FileIterator(fp, buffer_size))

    # 初始化最小堆：(值, 文件ID, 值ID)
    heap = []
    for i, it in enumerate(iterators):
        try:
            val = next(it)
            heapq.heappush(heap, HeapEntry(val, i, 0))
        except StopIteration:
            pass  # 空文件跳过

    # 归并过程
    merged_count = 0
    output_file = open(output_path, 'w')
    start_time = __import__('time').perf_counter()

    try:
        while heap:
            entry = heapq.heappop(heap)
            output_file.write(f"{entry.value}\n")
            merged_count += 1

            # 从对应文件读取下一个值
            try:
                next_val = next(iterators[entry.file_id])
                heapq.heappush(heap,
                               HeapEntry(next_val, entry.file_id,
                                         entry.value_id + 1))
            except StopIteration:
                pass  # 该文件已耗尽
    finally:
        output_file.close()
        for it in iterators:
            it.close()

    elapsed = __import__('time').perf_counter() - start_time

    return {
        'merged_records': merged_count,
        'input_files': len(filepaths),
        'merge_degree': k,
        'elapsed_seconds': elapsed,
        'output_size_bytes': os.path.getsize(output_path),
    }


def multi_stage_merge(filepaths: List[str],
                      output_path: str,
                      max_k: int = 100,
                      buffer_size: int = 8192) -> List[dict]:
    """
    多阶段归并：当文件数超过 max_k 时，分多轮归并。

    Multi-stage merge: when num files exceeds max_k, merge in rounds.

    例如：有 1000 个文件，max_k=100，则：
    - 第一轮：1000 个文件合并为 10 个中间文件
    - 第二轮：10 个中间文件合并为 1 个最终文件

    Example with 1000 files, max_k=100:
    - Round 1: 1000 -> 10 intermediate files
    - Round 2: 10 -> 1 final file
    """
    stages = []
    current_files = list(filepaths)

    while len(current_files) > 1:
        # 将文件分组，每组最多 max_k 个
        groups = []
        for i in range(0, len(current_files), max_k):
            groups.append(current_files[i:i + max_k])

        next_files = []
        for group in groups:
            if len(group) == 1:
                next_files.append(group[0])
            else:
                # 对该组进行 k 路归并
                temp_output = f"{output_path}.stage_{len(stages)}_tmp"
                stats = k_way_merge(group, temp_output,
                                    k=len(group),
                                    buffer_size=buffer_size)
                stats['output_file'] = temp_output
                stats['input_files'] = [os.path.basename(f) for f in group]
                stages.append(stats)
                next_files.append(temp_output)

        current_files = next_files

    # 如果最终只有一个文件，重命名为输出路径
    if len(current_files) == 1 and current_files[0] != output_path:
        os.rename(current_files[0], output_path)

    return stages
