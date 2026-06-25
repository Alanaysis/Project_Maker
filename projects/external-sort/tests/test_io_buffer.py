"""
I/O 缓冲区测试
"""

import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.io_buffer import IOBuffer, BufferedWriter, BufferedReader, RunBuffer


class TestIOBuffer(unittest.TestCase):
    """I/O 缓冲区基类测试"""

    def test_initialization(self):
        """测试初始化"""
        buffer = IOBuffer(buffer_size=1024)
        self.assertEqual(buffer.buffer_size, 1024)
        self.assertEqual(buffer.bytes_used, 0)
        self.assertEqual(buffer.flush_count, 0)
        self.assertFalse(buffer.is_full)

    def test_estimate_size(self):
        """测试大小估算"""
        buffer = IOBuffer()

        # 整数
        self.assertEqual(buffer._estimate_size(42), 8)

        # 字符串
        self.assertGreater(buffer._estimate_size("hello"), 0)

        # 列表
        self.assertGreater(buffer._estimate_size([1, 2, 3]), 0)

    def test_clear(self):
        """测试清空"""
        buffer = IOBuffer()
        buffer._buffer = [1, 2, 3]
        buffer._bytes_used = 100

        buffer.clear()
        self.assertEqual(buffer.bytes_used, 0)
        self.assertEqual(len(buffer._buffer), 0)


class TestBufferedWriter(unittest.TestCase):
    """写缓冲区测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_write_and_flush(self):
        """测试写入和刷新"""
        filepath = os.path.join(self.temp_dir, "test.txt")

        with BufferedWriter(filepath, buffer_size=100) as writer:
            writer.write(1)
            writer.write(2)
            writer.write(3)

        # 验证文件内容
        with open(filepath, 'r') as f:
            lines = f.read().strip().split('\n')

        self.assertEqual(lines, ['1', '2', '3'])

    def test_auto_flush(self):
        """测试自动刷新"""
        filepath = os.path.join(self.temp_dir, "test.txt")

        # 使用很小的缓冲区
        with BufferedWriter(filepath, buffer_size=10) as writer:
            for i in range(100):
                writer.write(i)

        # 验证所有数据都写入了
        with open(filepath, 'r') as f:
            lines = f.read().strip().split('\n')

        self.assertEqual(len(lines), 100)

    def test_batch_write(self):
        """测试批量写入"""
        filepath = os.path.join(self.temp_dir, "test.txt")

        with BufferedWriter(filepath) as writer:
            writer.write_batch([1, 2, 3, 4, 5])

        with open(filepath, 'r') as f:
            lines = f.read().strip().split('\n')

        self.assertEqual(lines, ['1', '2', '3', '4', '5'])

    def test_statistics(self):
        """测试统计信息"""
        filepath = os.path.join(self.temp_dir, "test.txt")

        with BufferedWriter(filepath, buffer_size=50) as writer:
            for i in range(20):
                writer.write(i)

        self.assertGreater(writer.total_written, 0)
        self.assertEqual(writer.record_count, 20)
        self.assertGreater(writer.flush_count, 0)

    def test_write_delimiter(self):
        """测试写入分隔符"""
        filepath = os.path.join(self.temp_dir, "test.txt")

        with BufferedWriter(filepath) as writer:
            writer.write(1)
            writer.write(2)
            writer.write_delimiter("---")
            writer.write(3)
            writer.write(4)

        with open(filepath, 'r') as f:
            content = f.read()

        self.assertIn("---", content)


class TestBufferedReader(unittest.TestCase):
    """读缓冲区测试"""

    def setUp(self):
        """创建临时目录和测试文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")

        with open(self.test_file, 'w') as f:
            for i in range(10):
                f.write(f"{i}\n")

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_read_all(self):
        """测试读取所有数据"""
        with BufferedReader(self.test_file) as reader:
            data = reader.read_all()

        self.assertEqual(len(data), 10)
        self.assertEqual(data, [str(i) for i in range(10)])

    def test_read_one_by_one(self):
        """测试逐个读取"""
        with BufferedReader(self.test_file) as reader:
            for i in range(10):
                item = reader.read()
                self.assertEqual(item, str(i))

            # 文件结束
            self.assertIsNone(reader.read())

    def test_read_batch(self):
        """测试批量读取"""
        with BufferedReader(self.test_file) as reader:
            batch = reader.read_batch(5)

        self.assertEqual(len(batch), 5)
        self.assertEqual(batch, [str(i) for i in range(5)])

    def test_eof_detection(self):
        """测试文件结束检测"""
        with BufferedReader(self.test_file) as reader:
            for _ in range(10):
                reader.read()

            self.assertTrue(reader.eof)

    def test_statistics(self):
        """测试统计信息"""
        with BufferedReader(self.test_file) as reader:
            reader.read_all()

        self.assertGreater(reader.total_read, 0)
        self.assertEqual(reader.record_count, 10)

    def test_buffered_reading(self):
        """测试缓冲读取"""
        # 使用很小的缓冲区
        with BufferedReader(self.test_file, buffer_size=10) as reader:
            data = reader.read_all()

        self.assertEqual(len(data), 10)


class TestRunBuffer(unittest.TestCase):
    """归并段缓冲区测试"""

    def test_initialization(self):
        """测试初始化"""
        buffer = RunBuffer(max_memory=1024)

        self.assertEqual(buffer.max_memory, 1024)
        self.assertEqual(buffer.available_memory, 1024)
        self.assertFalse(buffer.is_full)
        self.assertEqual(buffer.run_count, 0)

    def test_add_and_sort(self):
        """测试添加和排序"""
        buffer = RunBuffer(max_memory=1024)

        buffer.add(3)
        buffer.add(1)
        buffer.add(4)
        buffer.add(1)
        buffer.add(5)

        buffer.sort()
        run = buffer.get_run()

        self.assertEqual(run, [1, 1, 3, 4, 5])
        self.assertEqual(buffer.run_count, 1)

    def test_custom_sort(self):
        """测试自定义排序"""
        buffer = RunBuffer(max_memory=1024)

        buffer.add(("c", 3))
        buffer.add(("a", 1))
        buffer.add(("b", 2))

        buffer.sort(key_func=lambda x: x[1])
        run = buffer.get_run()

        self.assertEqual(run, [("a", 1), ("b", 2), ("c", 3)])

    def test_memory_limit(self):
        """测试内存限制"""
        # 使用很小的内存限制
        buffer = RunBuffer(max_memory=50)

        # 添加一些元素
        for i in range(10):
            result = buffer.add(i)
            if not result:
                break

        # 应该有一些元素添加失败
        self.assertTrue(buffer.is_full or len(buffer._run_buffer) < 10)

    def test_clear(self):
        """测试清空"""
        buffer = RunBuffer()

        buffer.add(1)
        buffer.add(2)
        buffer.add(3)

        buffer.clear()

        self.assertEqual(len(buffer._run_buffer), 0)
        self.assertEqual(buffer.bytes_used, 0)

    def test_multiple_runs(self):
        """测试多个归并段"""
        buffer = RunBuffer(max_memory=1024)

        # 第一个归并段
        buffer.add(3)
        buffer.add(1)
        buffer.sort()
        run1 = buffer.get_run()

        # 第二个归并段
        buffer.add(2)
        buffer.add(4)
        buffer.sort()
        run2 = buffer.get_run()

        self.assertEqual(run1, [1, 3])
        self.assertEqual(run2, [2, 4])
        self.assertEqual(buffer.run_count, 2)


if __name__ == '__main__':
    unittest.main()
