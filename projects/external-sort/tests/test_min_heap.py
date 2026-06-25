"""
最小堆测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.min_heap import MinHeap, KWayMergeHeap


class TestMinHeap(unittest.TestCase):
    """最小堆测试"""

    def test_basic_operations(self):
        """测试基本操作"""
        heap = MinHeap()

        # 空堆操作
        self.assertEqual(len(heap), 0)
        self.assertFalse(bool(heap))

        # push 和 pop
        heap.push(5)
        heap.push(3)
        heap.push(7)
        heap.push(1)

        self.assertEqual(len(heap), 4)
        self.assertTrue(bool(heap))

        # pop 应该返回最小元素
        self.assertEqual(heap.pop(), 1)
        self.assertEqual(heap.pop(), 3)
        self.assertEqual(heap.pop(), 5)
        self.assertEqual(heap.pop(), 7)

    def test_peek(self):
        """测试 peek 操作"""
        heap = MinHeap()

        heap.push(5)
        heap.push(3)
        heap.push(7)

        # peek 不应该移除元素
        self.assertEqual(heap.peek(), 3)
        self.assertEqual(heap.peek(), 3)
        self.assertEqual(len(heap), 3)

    def test_push_pop(self):
        """测试 push_pop 操作"""
        heap = MinHeap()

        heap.push(5)
        heap.push(3)
        heap.push(7)

        # push_pop 应该添加新元素并返回最小元素
        result = heap.push_pop(1)
        self.assertEqual(result, 1)  # 1 是最小的

        result = heap.push_pop(10)
        self.assertEqual(result, 3)  # 3 是最小的（5, 7, 10 中）

    def test_replace(self):
        """测试 replace 操作"""
        heap = MinHeap()

        heap.push(5)
        heap.push(3)
        heap.push(7)

        # replace 应该替换堆顶并返回旧的堆顶
        result = heap.replace(1)
        self.assertEqual(result, 3)
        self.assertEqual(heap.peek(), 1)

    def test_custom_key_function(self):
        """测试自定义键函数"""
        # 使用元组 (name, value)，按 value 排序
        heap = MinHeap(key_func=lambda x: x[1])

        heap.push(("c", 3))
        heap.push(("a", 1))
        heap.push(("b", 2))

        self.assertEqual(heap.pop(), ("a", 1))
        self.assertEqual(heap.pop(), ("b", 2))
        self.assertEqual(heap.pop(), ("c", 3))

    def test_stability(self):
        """测试稳定性（相同键的元素保持插入顺序）"""
        heap = MinHeap()

        heap.push((1, "first"))
        heap.push((1, "second"))
        heap.push((1, "third"))

        # 相同键的元素应该按插入顺序返回
        self.assertEqual(heap.pop(), (1, "first"))
        self.assertEqual(heap.pop(), (1, "second"))
        self.assertEqual(heap.pop(), (1, "third"))

    def test_large_dataset(self):
        """测试大数据集"""
        import random

        heap = MinHeap()
        data = [random.randint(1, 10000) for _ in range(1000)]

        for item in data:
            heap.push(item)

        # pop 应该按升序返回
        result = []
        while heap:
            result.append(heap.pop())

        self.assertEqual(result, sorted(data))

    def test_empty_heap_operations(self):
        """测试空堆操作"""
        heap = MinHeap()

        with self.assertRaises(IndexError):
            heap.pop()

        with self.assertRaises(IndexError):
            heap.peek()

    def test_repr(self):
        """测试字符串表示"""
        heap = MinHeap()
        self.assertIn("MinHeap", repr(heap))
        self.assertIn("0", repr(heap))

        heap.push(1)
        self.assertIn("1", repr(heap))


class TestKWayMergeHeap(unittest.TestCase):
    """多路归并堆测试"""

    def test_basic_operations(self):
        """测试基本操作"""
        heap = KWayMergeHeap()

        # 添加多个 run 的元素
        heap.add_run(0, 5)
        heap.add_run(1, 3)
        heap.add_run(2, 7)

        # pop 应该返回最小元素的 run_id
        run_id, key = heap.pop()
        self.assertEqual(run_id, 1)
        self.assertEqual(key, 3)

    def test_replace(self):
        """测试 replace 操作"""
        heap = KWayMergeHeap()

        heap.add_run(0, 5)
        heap.add_run(1, 3)
        heap.add_run(2, 7)

        # 弹出最小元素
        run_id, key = heap.pop()
        self.assertEqual(run_id, 1)

        # 替换 run 1 的元素
        heap.replace(1, 10)

        # 下一个最小应该是 5 (run 0)
        run_id, key = heap.pop()
        self.assertEqual(run_id, 0)
        self.assertEqual(key, 5)

    def test_multiple_replacements(self):
        """测试多次替换"""
        heap = KWayMergeHeap()

        # 模拟 3 路归并
        heap.add_run(0, 1)
        heap.add_run(1, 4)
        heap.add_run(2, 7)

        results = []

        # 第一轮
        run_id, key = heap.pop()
        results.append(key)
        heap.replace(run_id, 2)  # run 0 的下一个元素

        # 第二轮
        run_id, key = heap.pop()
        results.append(key)
        heap.replace(run_id, 5)  # run 1 的下一个元素

        # 第三轮
        run_id, key = heap.pop()
        results.append(key)
        heap.replace(run_id, 8)  # run 2 的下一个元素

        # 继续直到堆为空
        while heap:
            run_id, key = heap.pop()
            results.append(key)

        # 验证结果是有序的
        self.assertEqual(results, sorted(results))

    def test_empty_heap(self):
        """测试空堆操作"""
        heap = KWayMergeHeap()

        self.assertEqual(len(heap), 0)
        self.assertFalse(bool(heap))

        with self.assertRaises(IndexError):
            heap.pop()

    def test_single_run(self):
        """测试单个 run"""
        heap = KWayMergeHeap()

        heap.add_run(0, 5)
        self.assertEqual(len(heap), 1)

        run_id, key = heap.pop()
        self.assertEqual(run_id, 0)
        self.assertEqual(key, 5)

    def test_simulate_merge(self):
        """测试模拟完整归并过程"""
        heap = KWayMergeHeap()

        # 3 个有序序列
        runs = [
            [1, 4, 7, 10],
            [2, 5, 8, 11],
            [3, 6, 9, 12],
        ]

        # 初始化: 添加每个 run 的第一个元素
        for i, run in enumerate(runs):
            heap.add_run(i, run[0])

        # 归并
        result = []
        run_positions = [0] * len(runs)

        while heap:
            run_id, key = heap.pop()
            result.append(key)

            # 移动到下一个元素
            run_positions[run_id] += 1
            if run_positions[run_id] < len(runs[run_id]):
                next_key = runs[run_id][run_positions[run_id]]
                heap.replace(run_id, next_key)

        # 验证结果
        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])


if __name__ == '__main__':
    unittest.main()
