"""
内存排序模块 (In-Memory Sort Module)

负责在内存中对单个块进行排序。
这是外部排序的第一阶段：对每个块进行内部排序。

In-Memory Sort Module:
Responsible for sorting individual chunks in memory.
This is Phase 1 of external sorting: internal sort of each chunk.
"""

import logging
import time
from typing import List

logger = logging.getLogger(__name__)


def sort_chunk(chunk: List[int],
               algorithm: str = 'tim_sort') -> List[int]:
    """
    在内存中对一个块进行排序。

    Sort a chunk in memory.

    支持多种排序算法供学习和比较：
    - 'tim_sort': Python 内置 Timsort (推荐)
    - 'quick_sort': 快速排序 (教学用途)
    - 'merge_sort': 归并排序 (教学用途)

    Args:
        chunk: 待排序的整数列表
        algorithm: 排序算法名称

    Returns:
        排序后的整数列表
    """
    if algorithm == 'tim_sort':
        return _tim_sort(chunk)
    elif algorithm == 'quick_sort':
        return _quick_sort(chunk[:])
    elif algorithm == 'merge_sort':
        return _merge_sort(chunk[:])
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


def _tim_sort(chunk: List[int]) -> List[int]:
    """
    Timsort: Python 内置排序算法。
    混合归并排序和插入排序，时间复杂度 O(n log n)。
    对部分有序数据特别高效。

    Timsort: Python's built-in sorting algorithm.
    Hybrid of merge sort and insertion sort, O(n log n).
    Particularly efficient for partially sorted data.
    """
    return sorted(chunk)


def _quick_sort(arr: List[int]) -> List[int]:
    """
    快速排序 (Quick Sort) - 教学实现。

    Choose median-of-three pivot to avoid worst-case O(n^2).

    Time: O(n log n) average, O(n^2) worst
    Space: O(log n) recursion stack
    """
    if len(arr) <= 1:
        return arr

    # 三数取中法选择基准，避免最坏情况
    mid = len(arr) // 2
    candidates = [(arr[0], 0), (arr[mid], mid), (arr[-1], -1)]
    candidates.sort(key=lambda x: x[0])
    pivot = candidates[1][0]

    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return _quick_sort(left) + middle + _quick_sort(right)


def _merge_sort(arr: List[int]) -> List[int]:
    """
    归并排序 (Merge Sort) - 教学实现。

    分治策略：将数组递归分成两半，分别排序后合并。
    Divide and conquer: recursively split, sort, then merge.

    Time: O(n log n) always
    Space: O(n) for temporary arrays
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = _merge_sort(arr[:mid])
    right = _merge_sort(arr[mid:])

    return _merge(left, right)


def _merge(left: List[int], right: List[int]) -> List[int]:
    """
    合并两个有序数组。

    Merge two sorted arrays into one sorted array.
    """
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def benchmark_sort(chunk: List[int], algorithm: str = 'tim_sort') -> dict:
    """
    对排序算法进行基准测试。

    Benchmark a sorting algorithm.

    Returns timing and statistics info.
    """
    start = time.perf_counter()
    result = sort_chunk(chunk, algorithm)
    elapsed = time.perf_counter() - start

    return {
        'algorithm': algorithm,
        'input_size': len(chunk),
        'elapsed_seconds': elapsed,
        'is_sorted': all(result[i] <= result[i + 1]
                         for i in range(len(result) - 1)),
    }
