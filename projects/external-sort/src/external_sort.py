"""
外部排序主模块

将归并段生成和多路归并组合成完整的外部排序流程。
支持多种排序模式和优化策略。
"""

import os
import tempfile
import time
from typing import Any, Callable, Iterator, List, Optional, Tuple

from .run_generator import RunGenerator, ReplacementSelection, ReplacementSelectionV2
from .kway_merger import KWayMerger, NaturalMerge


class ExternalSorter:
    """
    外部排序器

    完整的外部排序实现，支持:
    1. 基本外部归并排序
    2. 置换选择排序优化
    3. 多趟归并
    4. 自定义解析和比较函数

    使用方法:
        sorter = ExternalSorter(memory_limit=10*1024*1024)
        sorter.sort_file("input.txt", "output.txt")
    """

    def __init__(self, memory_limit: int = 1024 * 1024,
                 max_merge_ways: int = 10,
                 buffer_size: int = 512 * 1024,
                 key_func: Optional[Callable] = None,
                 use_replacement_selection: bool = True,
                 temp_dir: Optional[str] = None):
        """
        初始化外部排序器。

        Args:
            memory_limit: 内存限制（字节）
            max_merge_ways: 最大归并路数
            buffer_size: I/O 缓冲区大小（字节）
            key_func: 排序键提取函数
            use_replacement_selection: 是否使用置换选择排序
            temp_dir: 临时文件目录
        """
        self._memory_limit = memory_limit
        self._max_merge_ways = max_merge_ways
        self._buffer_size = buffer_size
        self._key_func = key_func or (lambda x: x)
        self._use_replacement_selection = use_replacement_selection
        self._temp_dir = temp_dir

        # 统计信息
        self._stats = {
            'total_records': 0,
            'total_runs': 0,
            'merge_passes': 0,
            'run_generation_time': 0,
            'merge_time': 0,
            'total_time': 0,
            'io_reads': 0,
            'io_writes': 0,
        }

    @property
    def stats(self) -> dict:
        """排序统计信息"""
        return self._stats.copy()

    def sort_file(self, input_file: str, output_file: str,
                  parse_func: Optional[Callable] = None) -> int:
        """
        对文件进行外部排序。

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            parse_func: 行解析函数

        Returns:
            排序后的记录数
        """
        start_time = time.time()

        # 创建临时目录
        if self._temp_dir:
            temp_dir = self._temp_dir
        else:
            temp_dir = tempfile.mkdtemp(prefix="external_sort_")

        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 阶段 1: 生成初始归并段
            run_start = time.time()
            run_files = self._generate_runs(input_file, temp_dir, parse_func)
            self._stats['run_generation_time'] = time.time() - run_start
            self._stats['total_runs'] = len(run_files)

            if not run_files:
                # 空文件
                with open(output_file, 'w') as f:
                    pass
                self._stats['total_time'] = time.time() - start_time
                return 0

            # 阶段 2: 多路归并
            merge_start = time.time()
            total_records = self._merge_runs(
                run_files, output_file, parse_func
            )
            self._stats['merge_time'] = time.time() - merge_start
            self._stats['total_records'] = total_records

            self._stats['total_time'] = time.time() - start_time
            return total_records

        finally:
            # 清理临时文件
            self._cleanup_temp(temp_dir)

    def sort_iterator(self, data_iter: Iterator[Any],
                      output_file: str) -> int:
        """
        从迭代器读取数据进行排序。

        Args:
            data_iter: 数据迭代器
            output_file: 输出文件路径

        Returns:
            排序后的记录数
        """
        start_time = time.time()

        temp_dir = tempfile.mkdtemp(prefix="external_sort_")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 生成归并段
            run_start = time.time()
            if self._use_replacement_selection:
                generator = ReplacementSelectionV2(
                    self._memory_limit, self._key_func
                )
            else:
                generator = RunGenerator(
                    self._memory_limit, self._key_func
                )

            run_files = generator.generate_from_iterator(data_iter, temp_dir)
            self._stats['run_generation_time'] = time.time() - run_start
            self._stats['total_runs'] = len(run_files)
            self._stats['total_records'] = generator.total_records

            if not run_files:
                with open(output_file, 'w') as f:
                    pass
                self._stats['total_time'] = time.time() - start_time
                return 0

            # 归并
            merge_start = time.time()
            merger = KWayMerger(self._buffer_size, self._key_func)
            total_records = merger.multi_pass_merge(
                run_files, output_file, self._max_merge_ways, temp_dir
            )
            self._stats['merge_time'] = time.time() - merge_start

            self._stats['total_time'] = time.time() - start_time
            return total_records

        finally:
            self._cleanup_temp(temp_dir)

    def sort_data(self, data: List[Any]) -> List[Any]:
        """
        对内存中的数据进行外部排序风格的排序。

        当数据量不太大但想模拟外部排序流程时使用。

        Args:
            data: 输入数据列表

        Returns:
            排序后的数据列表
        """
        if not data:
            return []

        start_time = time.time()
        temp_dir = tempfile.mkdtemp(prefix="external_sort_")

        try:
            # 写入临时文件
            input_file = os.path.join(temp_dir, "input.txt")
            with open(input_file, 'w') as f:
                for item in data:
                    f.write(f"{item}\n")

            # 执行外部排序
            output_file = os.path.join(temp_dir, "output.txt")
            self.sort_file(input_file, output_file)

            # 读取结果
            result = []
            with open(output_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            result.append(int(line))
                        except ValueError:
                            try:
                                result.append(float(line))
                            except ValueError:
                                result.append(line)

            self._stats['total_time'] = time.time() - start_time
            return result

        finally:
            self._cleanup_temp(temp_dir)

    def _generate_runs(self, input_file: str, output_dir: str,
                       parse_func: Optional[Callable] = None) -> List[str]:
        """
        生成初始归并段。

        Args:
            input_file: 输入文件
            output_dir: 输出目录
            parse_func: 解析函数

        Returns:
            归并段文件列表
        """
        if self._use_replacement_selection:
            generator = ReplacementSelectionV2(
                self._memory_limit, self._key_func
            )
        else:
            generator = RunGenerator(
                self._memory_limit, self._key_func
            )

        run_files = generator.generate_from_file(
            input_file, output_dir, parse_func
        )

        self._stats['total_records'] = generator.total_records
        return run_files

    def _merge_runs(self, run_files: List[str], output_file: str,
                    parse_func: Optional[Callable] = None) -> int:
        """
        执行多路归并。

        Args:
            run_files: 归并段文件列表
            output_file: 输出文件
            parse_func: 解析函数

        Returns:
            合并后的记录数
        """
        merger = KWayMerger(self._buffer_size, self._key_func)

        if len(run_files) <= self._max_merge_ways:
            # 单趟归并
            total = merger.merge_files(run_files, output_file, parse_func)
            self._stats['merge_passes'] = 1
            return total
        else:
            # 多趟归并
            temp_dir = tempfile.mkdtemp(prefix="merge_pass_")
            try:
                total = merger.multi_pass_merge(
                    run_files, output_file,
                    self._max_merge_ways, temp_dir, parse_func
                )
                self._stats['merge_passes'] = (
                    (len(run_files) - 1) // self._max_merge_ways + 1
                )
                return total
            finally:
                self._cleanup_temp(temp_dir)

    def _cleanup_temp(self, temp_dir: str) -> None:
        """清理临时目录"""
        try:
            for f in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, f)
                if os.path.isfile(filepath):
                    os.remove(filepath)
            os.rmdir(temp_dir)
        except OSError:
            pass


class LargeFileSorter:
    """
    大文件排序器

    专门针对超大文件的排序优化:
    - 分块读取，避免内存溢出
    - 多趟归并，控制归并路数
    - 并行 I/O 优化
    """

    def __init__(self, memory_limit: int = 100 * 1024 * 1024,
                 max_merge_ways: int = 8,
                 chunk_size: int = 10 * 1024 * 1024):
        """
        初始化大文件排序器。

        Args:
            memory_limit: 总内存限制（字节），默认 100MB
            max_merge_ways: 最大归并路数
            chunk_size: 每个分块大小（字节）
        """
        self._memory_limit = memory_limit
        self._max_merge_ways = max_merge_ways
        self._chunk_size = chunk_size

    def sort(self, input_file: str, output_file: str,
             key_func: Optional[Callable] = None,
             parse_func: Optional[Callable] = None) -> int:
        """
        对大文件进行排序。

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            key_func: 排序键函数
            parse_func: 解析函数

        Returns:
            排序后的记录数
        """
        sorter = ExternalSorter(
            memory_limit=self._memory_limit,
            max_merge_ways=self._max_merge_ways,
            buffer_size=self._chunk_size,
            key_func=key_func,
            use_replacement_selection=True,
        )

        return sorter.sort_file(input_file, output_file, parse_func)


class LogSorter:
    """
    日志文件排序器

    按时间戳或特定字段对日志文件进行排序。
    支持自定义日志格式解析。
    """

    def __init__(self, memory_limit: int = 50 * 1024 * 1024,
                 timestamp_format: str = "%Y-%m-%d %H:%M:%S"):
        """
        初始化日志排序器。

        Args:
            memory_limit: 内存限制
            timestamp_format: 时间戳格式
        """
        self._memory_limit = memory_limit
        self._timestamp_format = timestamp_format

    def sort_by_timestamp(self, input_file: str, output_file: str,
                          timestamp_field: int = 0,
                          separator: str = " ") -> int:
        """
        按时间戳排序日志文件。

        支持标准日志格式: "2024-01-01 08:00:00 INFO Message"
        时间戳由日期和时间两部分组成，用空格分隔。

        Args:
            input_file: 输入日志文件
            output_file: 输出文件
            timestamp_field: 时间戳字段索引（0 表示从行首开始）
            separator: 字段分隔符

        Returns:
            排序后的记录数
        """
        from datetime import datetime

        # 检测时间戳格式中的字段数
        # 例如 "%Y-%m-%d %H:%M:%S" 包含空格，需要 2 个字段
        ts_field_count = self._timestamp_format.count(' ') + 1

        def key_func(line):
            """从日志行提取时间戳作为排序键"""
            if isinstance(line, str):
                parts = line.split(separator)
                # 提取时间戳部分（可能跨多个字段）
                if len(parts) >= timestamp_field + ts_field_count:
                    ts_str = separator.join(
                        parts[timestamp_field:timestamp_field + ts_field_count]
                    )
                    try:
                        return datetime.strptime(ts_str, self._timestamp_format)
                    except ValueError:
                        pass
            return datetime.min

        def parse_func(line):
            return line.strip()

        sorter = ExternalSorter(
            memory_limit=self._memory_limit,
            key_func=key_func,
        )

        return sorter.sort_file(input_file, output_file, parse_func)

    def sort_by_field(self, input_file: str, output_file: str,
                      field_index: int = 0,
                      separator: str = ",",
                      reverse: bool = False) -> int:
        """
        按指定字段排序日志文件。

        Args:
            input_file: 输入文件
            output_file: 输出文件
            field_index: 字段索引
            separator: 字段分隔符
            reverse: 是否降序

        Returns:
            排序后的记录数
        """
        def key_func(line):
            if isinstance(line, str):
                parts = line.split(separator)
                if len(parts) > field_index:
                    try:
                        return float(parts[field_index])
                    except ValueError:
                        return parts[field_index].strip()
            return ""

        def parse_func(line):
            return line.strip()

        sorter = ExternalSorter(
            memory_limit=self._memory_limit,
            key_func=key_func,
        )

        return sorter.sort_file(input_file, output_file, parse_func)


class DatabaseSorter:
    """
    数据库排序器

    模拟数据库的外部排序操作。
    支持:
    - 单列排序
    - 多列排序
    - 自定义数据类型
    """

    def __init__(self, memory_limit: int = 64 * 1024 * 1024,
                 max_merge_ways: int = 10):
        """
        初始化数据库排序器。

        Args:
            memory_limit: 内存限制
            max_merge_ways: 最大归并路数
        """
        self._memory_limit = memory_limit
        self._max_merge_ways = max_merge_ways

    def sort_by_columns(self, input_file: str, output_file: str,
                        sort_columns: List[int],
                        separator: str = ",",
                        reverse_flags: Optional[List[bool]] = None,
                        header: bool = True) -> int:
        """
        按多个列排序。

        Args:
            input_file: 输入 CSV 文件
            output_file: 输出文件
            sort_columns: 排序列索引列表
            separator: 字段分隔符
            reverse_flags: 每列是否降序的标志列表
            header: 是否有表头

        Returns:
            排序后的记录数
        """
        if reverse_flags is None:
            reverse_flags = [False] * len(sort_columns)

        # 读取表头
        header_line = None
        if header:
            with open(input_file, 'r', encoding='utf-8') as f:
                header_line = f.readline().strip()

        def key_func(line):
            """多列排序键"""
            if isinstance(line, str):
                parts = line.split(separator)
                key = []
                for col, rev in zip(sort_columns, reverse_flags):
                    if col < len(parts):
                        try:
                            val = float(parts[col])
                        except ValueError:
                            val = parts[col].strip()
                    else:
                        val = ""

                    # 处理降序: 对数值取反，对字符串使用特殊处理
                    if rev:
                        if isinstance(val, (int, float)):
                            val = -val
                        else:
                            # 字符串降序比较复杂，这里简化处理
                            val = tuple(
                                -ord(c) if isinstance(c, str) else c
                                for c in str(val)
                            )
                    key.append(val)
                return tuple(key)
            return ()

        def parse_func(line):
            return line.strip()

        # 跳过表头的文件处理
        if header:
            # 创建临时文件（不含表头）
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_input = os.path.join(temp_dir, "input_no_header.txt")

            with open(input_file, 'r', encoding='utf-8') as fin, \
                 open(temp_input, 'w', encoding='utf-8') as fout:
                next(fin)  # 跳过表头
                for line in fin:
                    fout.write(line)

            sorter = ExternalSorter(
                memory_limit=self._memory_limit,
                max_merge_ways=self._max_merge_ways,
                key_func=key_func,
            )

            count = sorter.sort_file(temp_input, output_file, parse_func)

            # 将表头插入输出文件
            if header_line:
                self._prepend_header(output_file, header_line)

            # 清理
            os.remove(temp_input)
            os.rmdir(temp_dir)

            return count
        else:
            sorter = ExternalSorter(
                memory_limit=self._memory_limit,
                max_merge_ways=self._max_merge_ways,
                key_func=key_func,
            )

            return sorter.sort_file(input_file, output_file, parse_func)

    def _prepend_header(self, filepath: str, header: str) -> None:
        """在文件开头插入表头"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header + '\n')
            f.write(content)
