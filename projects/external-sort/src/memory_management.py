"""
内存管理模块 (Memory Management Module)

负责管理外部排序过程中的内存使用。
根据可用内存动态调整块大小和归并路数。

Memory Management Module:
Manages memory usage during external sorting.
Dynamically adjusts chunk size and merge degree based on available memory.
"""

import os
import logging
from typing import NamedTuple

logger = logging.getLogger(__name__)


class MemoryProfile(NamedTuple):
    """内存配置概要。

    Memory configuration profile.
    """
    total_memory_mb: float
    available_memory_mb: float
    chunk_size_mb: float
    max_merge_degree: int
    buffer_overhead_mb: float


def compute_memory_profile(
    target_chunk_records: int = 100000,
    record_size_bytes: int = 10,
    memory_safety_factor: float = 0.5,
    records_per_merge_slot: int = 100,
) -> MemoryProfile:
    """
    根据系统内存计算外部排序的内存配置。

    Compute external sorting memory configuration based on system memory.

    计算逻辑：
    1. 获取系统可用内存
    2. 取一半作为安全可用内存
    3. 根据每条记录大小计算每块可容纳的记录数
    4. 根据剩余内存计算最大归并路数

    Calculation logic:
    1. Get system available memory
    2. Use half as safe available memory
    3. Compute records per chunk based on record size
    4. Compute max merge degree from remaining memory
    """
    # 获取可用内存
    try:
        import resource
        avail_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        avail_bytes = avail_kb * 1024
    except ImportError:
        avail_bytes = _fallback_memory_estimate()

    safe_memory = int(avail_bytes * memory_safety_factor)
    total_bytes = avail_bytes * 2  # 估算总量

    # 内存配置
    chunk_size_bytes = target_chunk_records * record_size_bytes
    chunk_size_mb = chunk_size_bytes / (1024 * 1024)

    # 归并路数：每条记录需要一个文件描述符和一小块缓冲
    buffer_overhead_bytes = safe_memory - chunk_size_bytes
    buffer_overhead_mb = buffer_overhead_bytes / (1024 * 1024)
    max_merge_degree = max(2, buffer_overhead_bytes // records_per_merge_slot)

    profile = MemoryProfile(
        total_memory_mb=total_bytes / (1024 * 1024),
        available_memory_mb=safe_memory / (1024 * 1024),
        chunk_size_mb=chunk_size_mb,
        max_merge_degree=max_merge_degree,
        buffer_overhead_mb=buffer_overhead_mb,
    )

    logger.info("Memory profile: %s", profile)
    return profile


def _fallback_memory_estimate() -> int:
    """
    回退的内存估计方法。

    Fallback memory estimation.
    """
    try:
        import psutil
        return psutil.virtual_memory().available
    except ImportError:
        # 保守估计：使用 64MB 作为可用内存
        return 64 * 1024 * 1024


def adaptive_k_selection(
    num_runs: int,
    max_merge_degree: int,
    buffer_overhead_bytes: int,
    records_per_slot: int = 100,
) -> int:
    """
    自适应选择归并路数 k。

    Adaptive selection of merge degree k.

    当可用内存不足以支持 num_runs 路归并时，
    选择最大的可行 k 值。

    When available memory cannot support num_runs-way merge,
    choose the largest feasible k.
    """
    max_feasible = buffer_overhead_bytes // records_per_slot
    return min(num_runs, max_merge_degree, max_feasible)


def estimate_io_cost(num_records: int,
                     chunk_size: int,
                     num_runs: int,
                     merge_degree: int) -> dict:
    """
    估算外部排序的 I/O 成本。

    Estimate I/O cost of external sorting.

    外部排序的 I/O 成本：
    - 初始分块阶段：2 * num_records (读一次，写一次)
    - 归并阶段：num_records * log_k(num_runs) * 2
      (每轮归并所有记录读/写一次，共 log_k(num_runs) 轮)

    I/O cost of external sorting:
    - Initial phase: 2 * num_records (read once, write once)
    - Merge phase: num_records * log_k(num_runs) * 2
      (all records read/written per round, log_k(num_runs) rounds)
    """
    import math

    pass_through_cost = 2 * num_records
    merge_rounds = math.ceil(math.log(max(num_runs, 2)) /
                             math.log(max(merge_degree, 2)))
    merge_cost = num_records * merge_rounds * 2

    return {
        'pass_through_io': pass_through_cost,
        'merge_io': merge_cost,
        'total_io': pass_through_cost + merge_cost,
        'merge_rounds': merge_rounds,
        'num_runs': num_runs,
        'merge_degree': merge_degree,
    }
