"""
多路归并器

实现 K 路归并排序，将多个有序归并段合并为一个有序序列。

支持:
- 基于最小堆的多路归并
- 缓冲 I/O 优化
- 并行读取优化
"""

import heapq
import os
from typing import Any, Callable, List, Optional, Tuple

from .io_buffer import BufferedReader, BufferedWriter


class KWayMerger:
    """
    K 路归并器

    使用最小堆将多个有序文件合并为一个有序文件。
    时间复杂度: O(N log K)，其中 N 为总元素数，K 为归并路数。
    """

    def __init__(self, buffer_size: int = 1024 * 1024,
                 key_func: Optional[Callable] = None):
        """
        初始化 K 路归并器。

        Args:
            buffer_size: 每个输入文件的缓冲区大小（字节）
            key_func: 排序键提取函数
        """
        self._buffer_size = buffer_size
        self._key_func = key_func or (lambda x: x)
        self._readers: List[BufferedReader] = []
        self._heap: List[Tuple[Any, int, int]] = []  # (key, reader_idx, counter)
        self._counter = 0
        self._current_values: dict[int, Any] = {}  # reader_idx -> current value
        self._eof_flags: dict[int, bool] = {}  # reader_idx -> eof flag
        self._total_merged = 0

    @property
    def total_merged(self) -> int:
        """总共合并的记录数"""
        return self._total_merged

    def merge_files(self, input_files: List[str], output_file: str,
                    parse_func: Optional[Callable] = None) -> int:
        """
        合并多个有序文件到一个输出文件。

        Args:
            input_files: 输入文件路径列表
            output_file: 输出文件路径
            parse_func: 解析函数，None 则按数值解析

        Returns:
            合并后的记录总数
        """
        if not input_files:
            return 0

        if parse_func is None:
            def parse_func(line):
                line = line.strip()
                try:
                    return int(line)
                except ValueError:
                    try:
                        return float(line)
                    except ValueError:
                        return line

        # 打开所有输入文件
        self._readers.clear()
        self._heap.clear()
        self._current_values.clear()
        self._eof_flags.clear()
        self._counter = 0
        self._total_merged = 0

        for i, filepath in enumerate(input_files):
            reader = BufferedReader(filepath, self._buffer_size)
            reader.open()
            self._readers.append(reader)
            self._eof_flags[i] = False

            # 读取每个文件的第一个元素
            line = reader.read()
            if line is not None:
                value = parse_func(line)
                self._current_values[i] = value
                key = self._key_func(value)
                heapq.heappush(self._heap, (key, i, self._counter))
                self._counter += 1
            else:
                self._eof_flags[i] = True

        # 执行 K 路归并
        with BufferedWriter(output_file, self._buffer_size) as writer:
            while self._heap:
                # 弹出最小元素
                key, reader_idx, _ = heapq.heappop(self._heap)
                value = self._current_values[reader_idx]

                # 写入输出
                writer.write(value)
                self._total_merged += 1

                # 从对应的读取器读取下一个元素
                line = self._readers[reader_idx].read()
                if line is not None:
                    next_value = parse_func(line)
                    self._current_values[reader_idx] = next_value
                    next_key = self._key_func(next_value)
                    heapq.heappush(
                        self._heap, (next_key, reader_idx, self._counter)
                    )
                    self._counter += 1
                else:
                    self._eof_flags[reader_idx] = True

        # 关闭所有读取器
        for reader in self._readers:
            reader.close()
        self._readers.clear()

        return self._total_merged

    def merge_in_memory(self, sorted_lists: List[List[Any]]) -> List[Any]:
        """
        在内存中合并多个有序列表。

        Args:
            sorted_lists: 有序列表的列表

        Returns:
            合并后的有序列表
        """
        result = []
        heap = []

        # 初始化堆
        for i, lst in enumerate(sorted_lists):
            if lst:
                key = self._key_func(lst[0])
                heapq.heappush(heap, (key, i, 0, self._counter))
                self._counter += 1

        while heap:
            key, list_idx, elem_idx, _ = heapq.heappop(heap)
            result.append(sorted_lists[list_idx][elem_idx])

            # 移动到下一个元素
            next_idx = elem_idx + 1
            if next_idx < len(sorted_lists[list_idx]):
                next_elem = sorted_lists[list_idx][next_idx]
                next_key = self._key_func(next_elem)
                heapq.heappush(heap, (next_key, list_idx, next_idx, self._counter))
                self._counter += 1

        return result

    def merge_iterator(self, iterators: List[Any],
                       parse_func: Optional[Callable] = None) -> Any:
        """
        合并多个有序迭代器。

        Args:
            iterators: 迭代器列表
            parse_func: 解析函数

        Yields:
            合并后的有序元素
        """
        heap = []
        counter = 0

        # 初始化堆
        for i, it in enumerate(iterators):
            try:
                value = next(it)
                key = self._key_func(value)
                heapq.heappush(heap, (key, i, counter))
                counter += 1
            except StopIteration:
                pass

        # 创建值存储
        current_values = {}
        for _, i, _ in heap:
            current_values[i] = None

        # 重新初始化
        heap.clear()
        for i, it in enumerate(iterators):
            try:
                value = next(it)
                key = self._key_func(value)
                heapq.heappush(heap, (key, i, counter))
                current_values[i] = value
                counter += 1
            except StopIteration:
                pass

        while heap:
            key, iter_idx, _ = heapq.heappop(heap)
            yield current_values[iter_idx]

            # 从对应的迭代器读取下一个
            try:
                value = next(iterators[iter_idx])
                key = self._key_func(value)
                current_values[iter_idx] = value
                heapq.heappush(heap, (key, iter_idx, counter))
                counter += 1
            except StopIteration:
                pass

    def multi_pass_merge(self, input_files: List[str], output_file: str,
                         max_merge_ways: int = 10,
                         temp_dir: Optional[str] = None,
                         parse_func: Optional[Callable] = None) -> int:
        """
        多趟归并。

        当归并路数超过 max_merge_ways 时，分多趟进行。
        每趟最多合并 max_merge_ways 个文件。

        Args:
            input_files: 输入文件列表
            output_file: 最终输出文件
            max_merge_ways: 每趟最大归并路数
            temp_dir: 临时文件目录
            parse_func: 解析函数

        Returns:
            合并后的记录总数
        """
        if len(input_files) <= max_merge_ways:
            return self.merge_files(input_files, output_file, parse_func)

        if temp_dir is None:
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="merge_pass_")

        os.makedirs(temp_dir, exist_ok=True)

        current_files = input_files
        pass_num = 0

        while len(current_files) > max_merge_ways:
            next_files = []
            for i in range(0, len(current_files), max_merge_ways):
                batch = current_files[i:i + max_merge_ways]
                if len(batch) == 1:
                    next_files.append(batch[0])
                else:
                    temp_output = os.path.join(
                        temp_dir, f"pass_{pass_num:03d}_batch_{i // max_merge_ways:03d}.txt"
                    )
                    self.merge_files(batch, temp_output, parse_func)
                    next_files.append(temp_output)
            current_files = next_files
            pass_num += 1

        # 最终归并
        return self.merge_files(current_files, output_file, parse_func)


class NaturalMerge:
    """
    自然归并

    利用输入数据中已有的自然有序段进行归并，
    减少初始归并段的生成开销。
    """

    def __init__(self, buffer_size: int = 1024 * 1024,
                 key_func: Optional[Callable] = None):
        """
        初始化自然归并器。

        Args:
            buffer_size: 缓冲区大小
            key_func: 排序键提取函数
        """
        self._buffer_size = buffer_size
        self._key_func = key_func or (lambda x: x)

    def find_natural_runs(self, data: List[Any]) -> List[List[Any]]:
        """
        查找数据中的自然有序段。

        Args:
            data: 输入数据

        Returns:
            自然有序段列表
        """
        if not data:
            return []

        runs = []
        current_run = [data[0]]

        for i in range(1, len(data)):
            if self._key_func(data[i]) >= self._key_func(current_run[-1]):
                current_run.append(data[i])
            else:
                runs.append(current_run)
                current_run = [data[i]]

        if current_run:
            runs.append(current_run)

        return runs

    def merge_natural_runs(self, input_file: str, output_file: str,
                           parse_func: Optional[Callable] = None) -> int:
        """
        使用自然归并对文件排序。

        Args:
            input_file: 输入文件
            output_file: 输出文件
            parse_func: 解析函数

        Returns:
            排序后的记录数
        """
        if parse_func is None:
            def parse_func(line):
                line = line.strip()
                try:
                    return int(line)
                except ValueError:
                    try:
                        return float(line)
                    except ValueError:
                        return line

        # 读取所有数据
        data = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(parse_func(line))

        # 查找自然有序段
        runs = self.find_natural_runs(data)

        # 归并所有自然有序段
        merger = KWayMerger(self._buffer_size, self._key_func)
        result = merger.merge_in_memory(runs)

        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in result:
                f.write(f"{item}\n")

        return len(result)
