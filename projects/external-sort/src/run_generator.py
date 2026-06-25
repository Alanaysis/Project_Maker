"""
初始归并段生成器

实现两种初始归并段生成策略:
1. 内部排序法 - 将数据分块，每块在内存中排序后写入临时文件
2. 置换选择排序 - 使用最小堆生成更长的初始归并段

置换选择排序是外部排序的关键优化技术，
它可以生成平均长度为 2M 的归并段（M 为内存容量）。
"""

import os
import tempfile
from typing import Any, Callable, Iterator, List, Optional, Tuple

from .min_heap import MinHeap


class RunGenerator:
    """
    初始归并段生成器

    使用内部排序法生成初始归并段:
    1. 从输入文件读取数据块到内存
    2. 对内存中的数据块进行排序
    3. 将排序后的数据块写入临时文件
    """

    def __init__(self, memory_limit: int = 1024 * 1024,
                 key_func: Optional[Callable] = None):
        """
        初始化归并段生成器。

        Args:
            memory_limit: 内存限制（字节）
            key_func: 排序键提取函数
        """
        self._memory_limit = memory_limit
        self._key_func = key_func or (lambda x: x)
        self._run_files: List[str] = []
        self._total_records = 0
        self._total_runs = 0

    @property
    def run_files(self) -> List[str]:
        """生成的归并段文件列表"""
        return self._run_files.copy()

    @property
    def total_records(self) -> int:
        """总记录数"""
        return self._total_records

    @property
    def total_runs(self) -> int:
        """总归并段数"""
        return self._total_runs

    def generate_from_iterator(self, data_iter: Iterator[Any],
                               output_dir: Optional[str] = None) -> List[str]:
        """
        从数据迭代器生成归并段。

        Args:
            data_iter: 数据迭代器
            output_dir: 输出目录，None 使用临时目录

        Returns:
            归并段文件路径列表
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="external_sort_")

        os.makedirs(output_dir, exist_ok=True)
        self._run_files.clear()
        self._total_records = 0
        self._total_runs = 0

        current_buffer: List[Any] = []
        current_size = 0

        for item in data_iter:
            item_size = self._estimate_size(item)

            # 检查缓冲区是否已满
            if current_size + item_size > self._memory_limit and current_buffer:
                # 排序并写入归并段
                self._write_run(current_buffer, output_dir)
                current_buffer = []
                current_size = 0

            current_buffer.append(item)
            current_size += item_size
            self._total_records += 1

        # 处理最后一个缓冲区
        if current_buffer:
            self._write_run(current_buffer, output_dir)

        return self._run_files.copy()

    def generate_from_file(self, input_file: str,
                           output_dir: Optional[str] = None,
                           parse_func: Optional[Callable] = None) -> List[str]:
        """
        从输入文件生成归并段。

        Args:
            input_file: 输入文件路径
            output_dir: 输出目录
            parse_func: 行解析函数，None 则按整数解析

        Returns:
            归并段文件路径列表
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

        def data_iterator():
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield parse_func(line)

        return self.generate_from_iterator(data_iterator(), output_dir)

    def _write_run(self, buffer: List[Any], output_dir: str) -> None:
        """
        将排序后的缓冲区写入归并段文件。

        Args:
            buffer: 排序后的数据缓冲区
            output_dir: 输出目录
        """
        buffer.sort(key=self._key_func)

        run_file = os.path.join(output_dir, f"run_{self._total_runs:04d}.txt")
        with open(run_file, 'w', encoding='utf-8') as f:
            for item in buffer:
                f.write(f"{item}\n")

        self._run_files.append(run_file)
        self._total_runs += 1

    def _estimate_size(self, item: Any) -> int:
        """估算元素大小"""
        if isinstance(item, (int, float)):
            return 8
        elif isinstance(item, str):
            return len(item.encode('utf-8')) + 4
        else:
            return 64

    def cleanup(self) -> None:
        """清理临时文件"""
        for f in self._run_files:
            try:
                os.remove(f)
            except OSError:
                pass
        self._run_files.clear()


class ReplacementSelection:
    """
    置换选择排序

    使用最小堆生成更长的初始归并段。
    算法流程:
    1. 从输入读取 M 个元素到最小堆（M 为内存容量）
    2. 输出堆顶元素（当前归并段的最大值）
    3. 从输入读取下一个元素:
       - 如果新元素 >= 刚输出的元素，加入当前归并段
       - 否则，标记为下一个归并段
    4. 当堆中所有元素都属于下一个归并段时，当前归并段结束
    5. 重复直到所有数据处理完毕

    平均归并段长度为 2M，比内部排序法（长度 M）更长。
    """

    def __init__(self, memory_limit: int = 1024 * 1024,
                 key_func: Optional[Callable] = None):
        """
        初始化置换选择排序。

        Args:
            memory_limit: 内存限制（字节）
            key_func: 排序键提取函数
        """
        self._memory_limit = memory_limit
        self._key_func = key_func or (lambda x: x)
        self._run_files: List[str] = []
        self._total_records = 0
        self._total_runs = 0
        self._max_heap_size = 0

    @property
    def run_files(self) -> List[str]:
        """生成的归并段文件列表"""
        return self._run_files.copy()

    @property
    def total_records(self) -> int:
        """总记录数"""
        return self._total_records

    @property
    def total_runs(self) -> int:
        """总归并段数"""
        return self._total_runs

    @property
    def max_heap_size(self) -> int:
        """堆的最大大小"""
        return self._max_heap_size

    def generate_from_iterator(self, data_iter: Iterator[Any],
                               output_dir: Optional[str] = None) -> List[str]:
        """
        使用置换选择排序从迭代器生成归并段。

        Args:
            data_iter: 数据迭代器
            output_dir: 输出目录

        Returns:
            归并段文件路径列表
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="replacement_sel_")

        os.makedirs(output_dir, exist_ok=True)
        self._run_files.clear()
        self._total_records = 0
        self._total_runs = 0

        # 计算堆的最大容量
        # 每个元素估算 64 字节，堆容量 = 内存限制 / 元素大小
        max_elements = max(1, self._memory_limit // 64)
        self._max_heap_size = max_elements

        # 初始化: 读取 max_elements 个元素
        heap = MinHeap(key_func=self._key_func)
        data_iter_obj = iter(data_iter)

        # 填充初始堆
        for _ in range(max_elements):
            try:
                item = next(data_iter_obj)
                heap.push(item)
                self._total_records += 1
            except StopIteration:
                break

        if not heap:
            return []

        # 开始置换选择排序
        current_run: List[Any] = []
        last_output = None
        runs_generated = 0

        while heap:
            # 输出堆顶
            item = heap.pop()
            current_run.append(item)
            last_output = item

            # 尝试读取下一个元素
            try:
                new_item = next(data_iter_obj)
                self._total_records += 1

                if self._key_func(new_item) >= self._key_func(last_output):
                    # 新元素可以加入当前归并段
                    heap.push(new_item)
                else:
                    # 新元素属于下一个归并段
                    # 但我们不能直接放入堆中，需要暂存
                    # 使用标记: 先将新元素放入堆，但标记为"下一个归并段"
                    # 实际实现中，我们使用两个堆来处理
                    heap.push(new_item)
                    # 标记堆中所有比 last_output 小的元素属于下一个归并段
                    # 但这在标准实现中不容易做到

                    # 简化实现: 当堆顶比 last_output 小时，结束当前归并段
                    if heap and self._key_func(heap.peek()) < self._key_func(last_output):
                        # 写入当前归并段
                        self._write_run(current_run, output_dir, runs_generated)
                        runs_generated += 1
                        current_run = []
                        last_output = None

            except StopIteration:
                # 没有更多数据
                pass

            # 检查是否需要结束当前归并段
            if heap and last_output is not None:
                if self._key_func(heap.peek()) < self._key_func(last_output):
                    # 写入当前归并段
                    self._write_run(current_run, output_dir, runs_generated)
                    runs_generated += 1
                    current_run = []
                    last_output = None

        # 处理最后一个归并段
        if current_run:
            self._write_run(current_run, output_dir, runs_generated)
            runs_generated += 1

        self._total_runs = runs_generated
        return self._run_files.copy()

    def generate_from_file(self, input_file: str,
                           output_dir: Optional[str] = None,
                           parse_func: Optional[Callable] = None) -> List[str]:
        """
        使用置换选择排序从文件生成归并段。

        Args:
            input_file: 输入文件路径
            output_dir: 输出目录
            parse_func: 行解析函数

        Returns:
            归并段文件路径列表
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

        def data_iterator():
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield parse_func(line)

        return self.generate_from_iterator(data_iterator(), output_dir)

    def _write_run(self, run: List[Any], output_dir: str, run_idx: int) -> None:
        """
        写入归并段文件。

        Args:
            run: 归并段数据
            output_dir: 输出目录
            run_idx: 归并段索引
        """
        run_file = os.path.join(output_dir, f"run_{run_idx:04d}.txt")
        with open(run_file, 'w', encoding='utf-8') as f:
            for item in run:
                f.write(f"{item}\n")

        self._run_files.append(run_file)

    def cleanup(self) -> None:
        """清理临时文件"""
        for f in self._run_files:
            try:
                os.remove(f)
            except OSError:
                pass
        self._run_files.clear()


class ReplacementSelectionV2:
    """
    置换选择排序 - 改进版

    使用双缓冲区策略，更准确地实现置换选择排序。
    当新元素小于已输出的最大值时，将其暂存到"下一个归并段"缓冲区。
    """

    def __init__(self, memory_limit: int = 1024 * 1024,
                 key_func: Optional[Callable] = None):
        """
        初始化改进版置换选择排序。

        Args:
            memory_limit: 内存限制（字节）
            key_func: 排序键提取函数
        """
        self._memory_limit = memory_limit
        self._key_func = key_func or (lambda x: x)
        self._run_files: List[str] = []
        self._total_records = 0
        self._total_runs = 0

    @property
    def run_files(self) -> List[str]:
        return self._run_files.copy()

    @property
    def total_records(self) -> int:
        return self._total_records

    @property
    def total_runs(self) -> int:
        return self._total_runs

    def generate_from_iterator(self, data_iter: Iterator[Any],
                               output_dir: Optional[str] = None) -> List[str]:
        """
        使用改进版置换选择排序生成归并段。

        Args:
            data_iter: 数据迭代器
            output_dir: 输出目录

        Returns:
            归并段文件路径列表
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="replacement_sel_v2_")

        os.makedirs(output_dir, exist_ok=True)
        self._run_files.clear()
        self._total_records = 0
        self._total_runs = 0

        max_elements = max(1, self._memory_limit // 64)
        data_iter_obj = iter(data_iter)

        # 初始化: 填充堆
        heap = MinHeap(key_func=self._key_func)
        next_run_buffer: List[Any] = []  # 暂存下一个归并段的元素

        for _ in range(max_elements):
            try:
                item = next(data_iter_obj)
                heap.push(item)
                self._total_records += 1
            except StopIteration:
                break

        if not heap:
            return []

        current_run: List[Any] = []
        last_output = None

        while heap or next_run_buffer:
            # 如果堆为空，但有暂存的元素，开始新的归并段
            if not heap and next_run_buffer:
                # 写入上一个归并段（如果有的话）
                if current_run:
                    self._write_run(current_run, output_dir)
                    self._total_runs += 1
                    current_run = []

                # 将暂存元素放入堆
                for item in next_run_buffer:
                    heap.push(item)
                next_run_buffer.clear()
                last_output = None

            if not heap:
                break

            # 输出堆顶
            item = heap.pop()
            current_run.append(item)
            last_output = item

            # 尝试读取下一个元素
            try:
                new_item = next(data_iter_obj)
                self._total_records += 1

                if self._key_func(new_item) >= self._key_func(last_output):
                    heap.push(new_item)
                else:
                    next_run_buffer.append(new_item)
            except StopIteration:
                pass

        # 写入最后一个归并段
        if current_run:
            self._write_run(current_run, output_dir)
            self._total_runs += 1

        return self._run_files.copy()

    def generate_from_file(self, input_file: str,
                           output_dir: Optional[str] = None,
                           parse_func: Optional[Callable] = None) -> List[str]:
        """从文件生成归并段"""
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

        def data_iterator():
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield parse_func(line)

        return self.generate_from_iterator(data_iterator(), output_dir)

    def _write_run(self, run: List[Any], output_dir: str) -> None:
        """写入归并段文件"""
        run_file = os.path.join(output_dir, f"run_{self._total_runs:04d}.txt")
        with open(run_file, 'w', encoding='utf-8') as f:
            for item in run:
                f.write(f"{item}\n")
        self._run_files.append(run_file)

    def cleanup(self) -> None:
        """清理临时文件"""
        for f in self._run_files:
            try:
                os.remove(f)
            except OSError:
                pass
        self._run_files.clear()
