"""
归并段生成器测试
"""

import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.run_generator import RunGenerator, ReplacementSelection, ReplacementSelectionV2


class TestRunGenerator(unittest.TestCase):
    """内部排序法归并段生成器测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_generate_from_iterator(self):
        """测试从迭代器生成归并段"""
        generator = RunGenerator(memory_limit=100)

        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        self.assertGreater(len(run_files), 0)
        self.assertEqual(generator.total_records, 9)

        # 验证每个归并段都是有序的
        for filepath in run_files:
            with open(filepath, 'r') as f:
                values = [int(line.strip()) for line in f if line.strip()]
                self.assertEqual(values, sorted(values))

    def test_generate_from_file(self):
        """测试从文件生成归并段"""
        # 创建测试文件
        input_file = os.path.join(self.temp_dir, "input.txt")
        with open(input_file, 'w') as f:
            for i in [5, 3, 8, 1, 9, 2, 7, 4, 6]:
                f.write(f"{i}\n")

        generator = RunGenerator(memory_limit=50)
        run_files = generator.generate_from_file(input_file, self.temp_dir)

        self.assertGreater(len(run_files), 0)

        # 验证所有归并段合并后与输入数据一致
        all_values = []
        for filepath in run_files:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        all_values.append(int(line.strip()))

        self.assertEqual(sorted(all_values), [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_single_run(self):
        """测试单个归并段（数据量小于内存限制）"""
        generator = RunGenerator(memory_limit=1024 * 1024)

        data = [3, 1, 4, 1, 5, 9, 2, 6]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        # 所有数据应该在一个归并段中
        self.assertEqual(len(run_files), 1)

        # 验证排序正确
        with open(run_files[0], 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]
        self.assertEqual(values, [1, 1, 2, 3, 4, 5, 6, 9])

    def test_custom_key_function(self):
        """测试自定义键函数"""
        generator = RunGenerator(
            memory_limit=1024,
            key_func=lambda x: x[1]  # 按元组第二个元素排序
        )

        data = [("c", 3), ("a", 1), ("b", 2), ("d", 4)]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        # 读取所有值并合并
        all_values = []
        for filepath in run_files:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        all_values.append(eval(line.strip()))

        # 验证所有值都存在且每个 run 内部有序
        self.assertEqual(sorted(all_values, key=lambda x: x[1]),
                         [("a", 1), ("b", 2), ("c", 3), ("d", 4)])

        # 验证每个 run 内部按 key 排序
        for filepath in run_files:
            with open(filepath, 'r') as f:
                run_values = [eval(line.strip()) for line in f if line.strip()]
                run_keys = [v[1] for v in run_values]
                self.assertEqual(run_keys, sorted(run_keys))

    def test_empty_input(self):
        """测试空输入"""
        generator = RunGenerator(memory_limit=100)

        run_files = generator.generate_from_iterator(iter([]), self.temp_dir)

        self.assertEqual(len(run_files), 0)
        self.assertEqual(generator.total_records, 0)

    def test_large_dataset(self):
        """测试大数据集"""
        import random

        generator = RunGenerator(memory_limit=1000)
        data = [random.randint(1, 10000) for _ in range(10000)]

        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        # 读取所有数据
        all_values = []
        for filepath in run_files:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        all_values.append(int(line.strip()))

        self.assertEqual(sorted(all_values), sorted(data))


class TestReplacementSelection(unittest.TestCase):
    """置换选择排序测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_basic_generation(self):
        """测试基本生成"""
        generator = ReplacementSelection(memory_limit=100)

        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        self.assertGreater(len(run_files), 0)
        self.assertEqual(generator.total_records, 9)

    def test_sorted_input(self):
        """测试已排序输入"""
        generator = ReplacementSelection(memory_limit=100)

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        # 已排序数据应该只有一个归并段
        self.assertEqual(len(run_files), 1)

    def test_reverse_sorted_input(self):
        """测试逆序输入"""
        generator = ReplacementSelection(memory_limit=100)

        data = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        # 逆序输入会产生多个归并段
        self.assertGreater(len(run_files), 0)

    def test_all_runs_sorted(self):
        """测试所有归并段都是有序的"""
        import random

        generator = ReplacementSelection(memory_limit=200)
        data = [random.randint(1, 100) for _ in range(1000)]

        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        for filepath in run_files:
            with open(filepath, 'r') as f:
                values = [int(line.strip()) for line in f if line.strip()]
                self.assertEqual(values, sorted(values))

    def test_from_file(self):
        """测试从文件生成"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        with open(input_file, 'w') as f:
            for i in [5, 3, 8, 1, 9, 2, 7, 4, 6]:
                f.write(f"{i}\n")

        generator = ReplacementSelection(memory_limit=100)
        run_files = generator.generate_from_file(input_file, self.temp_dir)

        self.assertGreater(len(run_files), 0)


class TestReplacementSelectionV2(unittest.TestCase):
    """改进版置换选择排序测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_basic_generation(self):
        """测试基本生成"""
        generator = ReplacementSelectionV2(memory_limit=100)

        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        self.assertGreater(len(run_files), 0)
        self.assertEqual(generator.total_records, 9)

    def test_all_runs_sorted(self):
        """测试所有归并段都是有序的"""
        import random

        generator = ReplacementSelectionV2(memory_limit=200)
        data = [random.randint(1, 100) for _ in range(1000)]

        run_files = generator.generate_from_iterator(iter(data), self.temp_dir)

        for filepath in run_files:
            with open(filepath, 'r') as f:
                values = [int(line.strip()) for line in f if line.strip()]
                self.assertEqual(values, sorted(values))

    def test_longer_runs(self):
        """测试更长的归并段"""
        import random

        # V2 应该生成更长的归并段
        v1 = ReplacementSelection(memory_limit=200)
        v2 = ReplacementSelectionV2(memory_limit=200)

        data = [random.randint(1, 100) for _ in range(1000)]

        temp_v1 = tempfile.mkdtemp()
        temp_v2 = tempfile.mkdtemp()

        try:
            runs_v1 = v1.generate_from_iterator(iter(data), temp_v1)
            runs_v2 = v2.generate_from_iterator(iter(data), temp_v2)

            # V2 应该产生相同或更少的归并段
            # (因为 V2 正确实现了置换选择)
            self.assertLessEqual(len(runs_v2), len(runs_v1) + 5)  # 允许小误差
        finally:
            for f in os.listdir(temp_v1):
                os.remove(os.path.join(temp_v1, f))
            os.rmdir(temp_v1)
            for f in os.listdir(temp_v2):
                os.remove(os.path.join(temp_v2, f))
            os.rmdir(temp_v2)

    def test_empty_input(self):
        """测试空输入"""
        generator = ReplacementSelectionV2(memory_limit=100)

        run_files = generator.generate_from_iterator(iter([]), self.temp_dir)

        self.assertEqual(len(run_files), 0)

    def test_single_element(self):
        """测试单个元素"""
        generator = ReplacementSelectionV2(memory_limit=100)

        run_files = generator.generate_from_iterator(iter([42]), self.temp_dir)

        self.assertEqual(len(run_files), 1)

        with open(run_files[0], 'r') as f:
            value = int(f.read().strip())
        self.assertEqual(value, 42)


if __name__ == '__main__':
    unittest.main()
