"""
外部排序主模块 (External Sort Main Module)

实现完整的外部排序算法流程：
1. 将大文件分块
2. 每块在内存中排序
3. 将排序后的块写入临时文件 (runs)
4. 多路归并所有 runs

External Sort Main Module:
Implements the complete external sorting algorithm:
1. Split large file into chunks
2. Sort each chunk in memory
3. Write sorted chunks to temp files (runs)
4. Multi-way merge all runs
"""

import os
import logging
import time
import shutil
from typing import List, Optional, Dict

from .chunk import (
    split_file_into_chunks,
    create_temp_file,
    compute_chunk_size,
    get_available_memory,
)
from .in_memory_sort import sort_chunk, benchmark_sort
from .k_way_merge import k_way_merge, multi_stage_merge
from .memory_management import (
    compute_memory_profile,
    adaptive_k_selection,
    estimate_io_cost,
)

logger = logging.getLogger(__name__)


class ExternalSortResult:
    """外部排序结果。

    Result of external sorting.
    """

    def __init__(self):
        self.input_file: str = ""
        self.output_file: str = ""
        self.input_size_bytes: int = 0
        self.output_size_bytes: int = 0
        self.record_count: int = 0
        self.num_runs: int = 0
        self.merge_degree: int = 0
        self.memory_profile: Dict = {}
        self.io_cost_estimate: Dict = {}
        self.timings: Dict[str, float] = {}
        self.temp_files: List[str] = []
        self.is_valid: bool = False

    def validate(self, input_path: str) -> bool:
        """验证排序结果是否正确。

        Validate that the sorted output is correct.
        """
        with open(input_path, 'r') as f:
            input_vals = [int(line.strip()) for line in f if line.strip()]

        with open(self.output_file, 'r') as f:
            output_vals = [int(line.strip()) for line in f if line.strip()]

        # 检查记录数是否一致
        if len(input_vals) != len(output_vals):
            logger.error("Record count mismatch: %d vs %d",
                         len(input_vals), len(output_vals))
            return False

        # 检查输出是否有序
        for i in range(len(output_vals) - 1):
            if output_vals[i] > output_vals[i + 1]:
                logger.error("Output not sorted at index %d: %d > %d",
                             i, output_vals[i], output_vals[i + 1])
                return False

        self.is_valid = True
        logger.info("Validation passed: %d records sorted correctly",
                    len(output_vals))
        return True

    def summary(self) -> str:
        """生成排序结果摘要。

        Generate a summary of the sorting result.
        """
        lines = [
            "=" * 60,
            "外部排序结果摘要 / External Sort Summary",
            "=" * 60,
            f"输入文件: {self.input_file}",
            f"输出文件: {self.output_file}",
            f"记录数量: {self.record_count:,}",
            f"输入大小: {self.input_size_bytes:,} bytes",
            f"输出大小: {self.output_size_bytes:,} bytes",
            f"生成 runs 数: {self.num_runs}",
            f"归并路数: {self.merge_degree}",
            "-" * 60,
            "耗时 / Timings:",
        ]
        for stage, elapsed in self.timings.items():
            lines.append(f"  {stage}: {elapsed:.4f}s")

        lines.append("-" * 60)
        lines.append("内存配置 / Memory Profile:")
        for key, val in self.memory_profile.items():
            lines.append(f"  {key}: {val}")

        lines.append("-" * 60)
        lines.append("I/O 成本估算 / I/O Cost Estimate:")
        for key, val in self.io_cost_estimate.items():
            lines.append(f"  {key}: {val}")

        lines.append("-" * 60)
        lines.append(f"验证结果: {'通过 ✓' if self.is_valid else '失败 ✗'}")
        lines.append("=" * 60)
        return "\n".join(lines)


class ExternalSort:
    """
    外部排序器。

    External Sorter.

    使用示例:
        sorter = ExternalSort(temp_dir='/tmp/ext-sort')
        result = sorter.sort('large_file.txt', 'sorted_output.txt')
        print(result.summary())

    Usage example:
        sorter = ExternalSort(temp_dir='/tmp/ext-sort')
        result = sorter.sort('large_file.txt', 'sorted_output.txt')
        print(result.summary())
    """

    def __init__(self,
                 temp_dir: str = '/tmp/external-sort',
                 chunk_size_mb: float = 1.0,
                 sort_algorithm: str = 'tim_sort',
                 buffer_size: int = 8192):
        """
        初始化外部排序器。

        Args:
            temp_dir: 临时文件目录 (temp file directory)
            chunk_size_mb: 每块大小 (MB) (chunk size in MB)
            sort_algorithm: 内存排序算法 (in-memory sort algorithm)
            buffer_size: I/O 缓冲大小 (I/O buffer size)
        """
        self.temp_dir = temp_dir
        self.chunk_size_bytes = int(chunk_size_mb * 1024 * 1024)
        self.sort_algorithm = sort_algorithm
        self.buffer_size = buffer_size
        self.temp_files = []

        # 确保临时目录存在
        os.makedirs(temp_dir, exist_ok=True)

        # 内存配置
        self.memory_profile = compute_memory_profile(
            target_chunk_records=int(self.chunk_size_bytes / 10),
            record_size_bytes=10,
        )

    def sort(self,
             input_path: str,
             output_path: str,
             max_merge_degree: Optional[int] = None) -> ExternalSortResult:
        """
        执行外部排序。

        Execute external sort.

        算法流程:
        Phase 1 (生成 runs):
            1. 将文件分块
            2. 每块在内存中排序
            3. 将排序后的块写入临时文件

        Phase 2 (多路归并):
            4. 对所有 runs 进行 k 路归并

        Algorithm flow:
        Phase 1 (Run generation):
            1. Split file into chunks
            2. Sort each chunk in memory
            3. Write sorted chunks to temp files

        Phase 2 (Multi-way merge):
            4. k-way merge all runs
        """
        result = ExternalSortResult()
        result.input_file = input_path
        result.input_size_bytes = os.path.getsize(input_path)

        start_total = time.perf_counter()

        # ========== Phase 1: 生成 runs ==========
        logger.info("Phase 1: Generating sorted runs...")
        start_phase1 = time.perf_counter()

        runs = self._generate_runs(input_path)
        result.num_runs = len(runs)

        timings_phase1 = time.perf_counter() - start_phase1
        result.timings['phase1_run_generation'] = timings_phase1
        logger.info("Phase 1 complete: %d runs generated in %.4fs",
                    len(runs), timings_phase1)

        # ========== Phase 2: 多路归并 ==========
        logger.info("Phase 2: Multi-way merging %d runs...", len(runs))
        start_phase2 = time.perf_counter()

        if len(runs) == 1:
            # 只有一个 run，直接复制
            shutil.copy2(runs[0].filepath, output_path)
            result.temp_files = runs
        else:
            run_paths = [r.filepath for r in runs]

            # 自适应选择归并路数
            k = max_merge_degree or adaptive_k_selection(
                num_runs=len(runs),
                max_merge_degree=self.memory_profile.max_merge_degree,
                buffer_overhead_bytes=int(
                    self.memory_profile.buffer_overhead_mb * 1024 * 1024),
            )

            result.merge_degree = k

            # 如果 run 数太多，使用多阶段归并
            if len(runs) > k:
                stages = multi_stage_merge(
                    run_paths, output_path,
                    max_k=k,
                    buffer_size=self.buffer_size,
                )
                result.timings['phase2_multi_stage_merge'] = (
                    time.perf_counter() - start_phase2
                )
                # 清理中间文件
                for stage in stages:
                    if stage['output_file'] != output_path:
                        if os.path.exists(stage['output_file']):
                            os.remove(stage['output_file'])
            else:
                stats = k_way_merge(
                    run_paths, output_path,
                    k=min(k, len(runs)),
                    buffer_size=self.buffer_size,
                )
                result.timings['phase2_k_way_merge'] = stats['elapsed_seconds']

        result.output_file = output_path
        result.output_size_bytes = os.path.getsize(output_path)
        result.record_count = sum(r.record_count for r in runs)
        result.temp_files = runs

        total_time = time.perf_counter() - start_total
        result.timings['total'] = total_time

        # 内存配置和 I/O 成本估算
        result.memory_profile = {
            'chunk_size_mb': self.memory_profile.chunk_size_mb,
            'max_merge_degree': self.memory_profile.max_merge_degree,
            'available_memory_mb': self.memory_profile.available_memory_mb,
        }

        result.io_cost_estimate = estimate_io_cost(
            num_records=result.record_count,
            chunk_size=self.chunk_size_bytes,
            num_runs=result.num_runs,
            merge_degree=result.merge_degree,
        )

        logger.info("External sort complete in %.4fs", total_time)

        # 验证排序结果
        result.validate(input_path)

        return result

    def _generate_runs(self, input_path: str) -> List:
        """
        生成有序 runs。

        Generate sorted runs.

        对每个分块：
        1. 在内存中排序
        2. 写入临时文件
        """
        runs = []
        run_index = 0

        for chunk in split_file_into_chunks(
                input_path,
                max_chunk_size=self.chunk_size_bytes,
        ):
            # 在内存中排序
            sorted_chunk = sort_chunk(chunk, self.sort_algorithm)

            # 写入临时文件
            temp_path = create_temp_file(
                suffix='.txt',
                prefix='ext-sort-run-',
                temp_dir=self.temp_dir,
            )
            with open(temp_path, 'w') as f:
                for val in sorted_chunk:
                    f.write(f"{val}\n")

            run = type('Run', (), {
                'filepath': temp_path,
                'size_bytes': len(sorted_chunk) * 10,
                'record_count': len(sorted_chunk),
            })()
            runs.append(run)
            run_index += 1

        return runs

    def _get_run_paths(self, runs) -> List[str]:
        """从 runs 列表获取文件路径。

        Extract file paths from runs list.
        """
        return [r.filepath if hasattr(r, 'filepath') else r for r in runs]

    def cleanup(self):
        """清理临时文件。

        Clean up temporary files.
        """
        for f in self.temp_files:
            if os.path.exists(f):
                os.remove(f)
        logger.info("Cleaned up %d temporary files", len(self.temp_files))
        self.temp_files.clear()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
