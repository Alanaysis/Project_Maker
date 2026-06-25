"""
多路归并器测试
"""

import os
import random
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kway_merger import KWayMerger, NaturalMerge


class TestKWayMerger(unittest.TestCase):
    """K 路归并器测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def _create_sorted_file(self, values, filename):
        """创建排序文件"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            for v in values:
                f.write(f"{v}\n")
        return filepath

    def test_merge_two_files(self):
        """测试合并两个文件"""
        file1 = self._create_sorted_file([1, 3, 5, 7], "run1.txt")
        file2 = self._create_sorted_file([2, 4, 6, 8], "run2.txt")
        output = os.path.join(self.temp_dir, "output.txt")

        merger = KWayMerger()
        total = merger.merge_files([file1, file2], output)

        self.assertEqual(total, 8)

        with open(output, 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(values, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_merge_three_files(self):
        """测试合并三个文件"""
        file1 = self._create_sorted_file([1, 4, 7], "run1.txt")
        file2 = self._create_sorted_file([2, 5, 8], "run2.txt")
        file3 = self._create_sorted_file([3, 6, 9], "run3.txt")
        output = os.path.join(self.temp_dir, "output.txt")

        merger = KWayMerger()
        total = merger.merge_files([file1, file2, file3], output)

        self.assertEqual(total, 9)

        with open(output, 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(values, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_merge_empty_files(self):
        """测试合并空文件"""
        merger = KWayMerger()
        total = merger.merge_files([], "dummy.txt")

        self.assertEqual(total, 0)

    def test_merge_single_file(self):
        """测试合并单个文件"""
        file1 = self._create_sorted_file([3, 1, 4, 1, 5], "run1.txt")
        output = os.path.join(self.temp_dir, "output.txt")

        merger = KWayMerger()
        total = merger.merge_files([file1], output)

        self.assertEqual(total, 5)

    def test_merge_with_duplicates(self):
        """测试合并有重复元素的文件"""
        file1 = self._create_sorted_file([1, 2, 2, 3], "run1.txt")
        file2 = self._create_sorted_file([2, 3, 4, 4], "run2.txt")
        output = os.path.join(self.temp_dir, "output.txt")

        merger = KWayMerger()
        total = merger.merge_files([file1, file2], output)

        self.assertEqual(total, 8)

        with open(output, 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(values, [1, 2, 2, 2, 3, 3, 4, 4])

    def test_merge_in_memory(self):
        """测试内存中合并"""
        merger = KWayMerger()

        lists = [
            [1, 4, 7],
            [2, 5, 8],
            [3, 6, 9],
        ]

        result = merger.merge_in_memory(lists)

        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_merge_in_memory_single_list(self):
        """测试合并单个列表"""
        merger = KWayMerger()

        lists = [[3, 1, 4, 1, 5]]
        result = merger.merge_in_memory(lists)

        self.assertEqual(result, [3, 1, 4, 1, 5])

    def test_merge_in_memory_empty(self):
        """测试合并空列表"""
        merger = KWayMerger()

        result = merger.merge_in_memory([])

        self.assertEqual(result, [])

    def test_custom_key_function(self):
        """测试自定义键函数"""
        # 按元组第二个元素排序
        merger = KWayMerger(key_func=lambda x: x[1])

        lists = [
            [("a", 3), ("b", 6)],
            [("c", 1), ("d", 4)],
            [("e", 2), ("f", 5)],
        ]

        result = merger.merge_in_memory(lists)

        self.assertEqual(result, [
            ("c", 1), ("e", 2), ("a", 3),
            ("d", 4), ("f", 5), ("b", 6),
        ])

    def test_large_dataset(self):
        """测试大数据集"""
        import random

        # 创建 5 个有序文件
        files = []
        all_values = []
        for i in range(5):
            values = sorted([random.randint(1, 1000) for _ in range(1000)])
            all_values.extend(values)
            filepath = self._create_sorted_file(values, f"run{i}.txt")
            files.append(filepath)

        output = os.path.join(self.temp_dir, "output.txt")

        merger = KWayMerger()
        total = merger.merge_files(files, output)

        self.assertEqual(total, 5000)

        with open(output, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(all_values))

    def test_multi_pass_merge(self):
        """测试多趟归并"""
        # 创建 15 个文件，每趟最多合并 5 个
        files = []
        all_values = []
        for i in range(15):
            values = sorted([random.randint(1, 100) for _ in range(100)])
            all_values.extend(values)
            filepath = self._create_sorted_file(values, f"run{i}.txt")
            files.append(filepath)

        output = os.path.join(self.temp_dir, "output.txt")

        merger = KWayMerger()
        total = merger.multi_pass_merge(files, output, max_merge_ways=5)

        self.assertEqual(total, 1500)

        with open(output, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(all_values))


class TestNaturalMerge(unittest.TestCase):
    """自然归并测试"""

    def test_find_natural_runs(self):
        """测试查找自然有序段"""
        merger = NaturalMerge()

        data = [1, 3, 5, 2, 4, 6, 1, 7, 8]
        runs = merger.find_natural_runs(data)

        self.assertEqual(len(runs), 3)
        self.assertEqual(runs[0], [1, 3, 5])
        self.assertEqual(runs[1], [2, 4, 6])
        self.assertEqual(runs[2], [1, 7, 8])

    def test_find_natural_runs_sorted(self):
        """测试已排序数据"""
        merger = NaturalMerge()

        data = [1, 2, 3, 4, 5]
        runs = merger.find_natural_runs(data)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0], [1, 2, 3, 4, 5])

    def test_find_natural_runs_reverse(self):
        """测试逆序数据"""
        merger = NaturalMerge()

        data = [5, 4, 3, 2, 1]
        runs = merger.find_natural_runs(data)

        self.assertEqual(len(runs), 5)

    def test_find_natural_runs_empty(self):
        """测试空数据"""
        merger = NaturalMerge()

        runs = merger.find_natural_runs([])

        self.assertEqual(len(runs), 0)

    def test_merge_natural_runs(self):
        """测试自然归并排序"""
        import tempfile

        temp_dir = tempfile.mkdtemp()
        input_file = os.path.join(temp_dir, "input.txt")
        output_file = os.path.join(temp_dir, "output.txt")

        # 写入测试数据
        with open(input_file, 'w') as f:
            for v in [5, 3, 8, 1, 9, 2, 7, 4, 6]:
                f.write(f"{v}\n")

        merger = NaturalMerge()
        total = merger.merge_natural_runs(input_file, output_file)

        self.assertEqual(total, 9)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9])

        # 清理
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


if __name__ == '__main__':
    unittest.main()
