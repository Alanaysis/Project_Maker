"""
最小堆实现 - 用于多路归并排序

支持自定义比较函数，可以处理 (key, value) 对，
其中 key 用于排序，value 是实际数据。
"""

import heapq
from typing import Any, Callable, List, Optional, Tuple


class MinHeap:
    """
    最小堆，用于多路归并。

    支持两种模式:
    1. 简单模式: 直接存储可比较的元素
    2. 键值模式: 存储 (key, value) 对，按 key 排序
    """

    def __init__(self, key_func: Optional[Callable] = None):
        """
        初始化最小堆。

        Args:
            key_func: 可选的键提取函数，用于自定义排序
        """
        self._heap: List = []
        self._key_func = key_func or (lambda x: x)
        self._counter = 0  # 用于稳定排序的计数器

    def push(self, item: Any) -> None:
        """
        向堆中添加元素。

        Args:
            item: 要添加的元素
        """
        key = self._key_func(item)
        # 使用 (key, counter, item) 保证稳定性
        heapq.heappush(self._heap, (key, self._counter, item))
        self._counter += 1

    def pop(self) -> Any:
        """
        弹出堆中最小元素。

        Returns:
            最小元素

        Raises:
            IndexError: 堆为空时
        """
        if not self._heap:
            IndexError("pop from empty heap")
        key, _, item = heapq.heappop(self._heap)
        return item

    def peek(self) -> Any:
        """
        查看堆中最小元素但不弹出。

        Returns:
            最小元素

        Raises:
            IndexError: 堆为空时
        """
        if not self._heap:
            raise IndexError("peek from empty heap")
        key, _, item = self._heap[0]
        return item

    def push_pop(self, item: Any) -> Any:
        """
        添加元素并弹出最小元素。

        比分别调用 push 和 pop 更高效。

        Args:
            item: 要添加的元素

        Returns:
            弹出的最小元素
        """
        key = self._key_func(item)
        entry = (key, self._counter, item)
        self._counter += 1
        _, _, result = heapq.heappushpop(self._heap, entry)
        return result

    def replace(self, item: Any) -> Any:
        """
        替换堆顶元素并返回旧的堆顶。

        等同于 pop + push，但更高效。
        与 push_pop 不同，replace 总是将新元素留在堆中。

        Args:
            item: 新元素

        Returns:
            旧的堆顶元素
        """
        key = self._key_func(item)
        entry = (key, self._counter, item)
        self._counter += 1
        _, _, result = heapq.heapreplace(self._heap, entry)
        return result

    @property
    def size(self) -> int:
        """返回堆中元素数量"""
        return len(self._heap)

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    def __repr__(self) -> str:
        return f"MinHeap(size={self.size})"


class KWayMergeHeap:
    """
    专用的多路归并堆。

    管理多个有序序列的归并，每个序列用 (key, run_id) 表示。
    支持从指定 run 中获取下一个元素。

    典型用法:
        # 初始化: 添加每个 run 的第一个元素
        for i, run in enumerate(runs):
            heap.add_run(i, run[0])

        # 归并循环
        while heap:
            run_id, key = heap.pop()
            process(key)
            if has_next(run_id):
                heap.replace(run_id, next_key)
    """

    def __init__(self):
        """初始化多路归并堆"""
        self._heap: List[Tuple[Any, int, int]] = []  # (key, run_id, counter)
        self._counter = 0

    def add_run(self, run_id: int, key: Any) -> None:
        """
        添加一个 run 的当前元素到堆中。

        Args:
            run_id: run 的标识符
            key: 当前元素的排序键
        """
        heapq.heappush(self._heap, (key, run_id, self._counter))
        self._counter += 1

    def pop(self) -> Tuple[int, Any]:
        """
        弹出最小元素所在的 run。

        Returns:
            (run_id, key) 元组

        Raises:
            IndexError: 堆为空时
        """
        if not self._heap:
            raise IndexError("pop from empty heap")
        key, run_id, _ = heapq.heappop(self._heap)
        return run_id, key

    def replace(self, run_id: int, new_key: Any) -> None:
        """
        为指定 run 添加新的当前元素。

        通常在 pop 之后调用，将该 run 的下一个元素加入堆。
        等同于 add_run，但语义更清晰。

        Args:
            run_id: run 的标识符
            new_key: 新的排序键
        """
        self.add_run(run_id, new_key)

    @property
    def size(self) -> int:
        """返回堆中元素数量"""
        return len(self._heap)

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    def __repr__(self) -> str:
        return f"KWayMergeHeap(runs={self.size})"
