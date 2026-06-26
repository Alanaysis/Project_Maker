"""
测试模块 (Test Module)

外部排序算法的单元测试。
Unit tests for external sorting algorithm.
"""

import os
import tempfile
import pytest
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.chunk import split_file_into_chunks, create_temp_file, compute_chunk_size
from src.in_memory_sort import sort_chunk, _quick_sort, _merge_sort, benchmark_sort
from src.k_way_merge import k_way_merge, multi_stage_merge, FileIterator
from src.external_sort import ExternalSort, ExternalSortResult
from src.memory_management import (
    compute_memory_profile,
    adaptive_k_selection,
    estimate_io_cost,
)
from src.io_optimization import BufferedWriter, BufferedReader, optimize_io_for_merge


# ========== Chunk Module Tests ==========

class TestChunk:
    def test_split_file_into_chunks(self, tmp_path):
        """测试文件分块。"""
        test_file = tmp_path / "test_input.txt"
        # 创建包含 100 行的测试文件
        with open(test_file, 'w') as f:
            for i in range(100):
                f.write(f"{i}\n" * 25)

        chunks = list(split_file_into_chunks(str(test_file), max_chunk_size=500))
        assert len(chunks) > 0
        # 验证每块都是列表
        for chunk in chunks:
            assert isinstance(chunk, list)

    def test_split_file_empty(self, tmp_path):
        """测试空文件分块。"""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        chunks = list(split_file_into_chunks(str(test_file), max_chunk_size=100))
        assert len(chunks) == 0

    def test_create_temp_file(self):
        """测试临时文件创建。"""
        path = create_temp_file(suffix='.test', prefix='test-')
        assert os.path.exists(path)
        assert path.endswith('.test')
        os.remove(path)

    def test_compute_chunk_size(self):
        """测试块大小计算。"""
        size = compute_chunk_size(1024 * 1024 * 100, safety_factor=0.5)
        assert size == 50 * 1024 * 1024


# ========== In-Memory Sort Tests ==========

class TestInMemorySort:
    def test_sort_chunk_tim_sort(self):
        """测试 Timsort。"""
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        result = sort_chunk(data, 'tim_sort')
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_sort_chunk_quick_sort(self):
        """测试快速排序。"""
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        result = sort_chunk(data, 'quick_sort')
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_sort_chunk_merge_sort(self):
        """测试归并排序。"""
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        result = sort_chunk(data, 'merge_sort')
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_sort_chunk_already_sorted(self):
        """测试已排序数据。"""
        data = list(range(100))
        for algo in ['tim_sort', 'quick_sort', 'merge_sort']:
            result = sort_chunk(data, algo)
            assert result == data

    def test_sort_chunk_reverse_sorted(self):
        """测试逆序数据。"""
        data = list(range(100, 0, -1))
        for algo in ['tim_sort', 'quick_sort', 'merge_sort']:
            result = sort_chunk(data, algo)
            assert result == list(range(1, 101))

    def test_sort_chunk_duplicates(self):
        """测试含重复元素的数据。"""
        data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        result = sort_chunk(data, 'tim_sort')
        assert result == [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9]

    def test_sort_chunk_single_element(self):
        """测试单元素。"""
        result = sort_chunk([42], 'tim_sort')
        assert result == [42]

    def test_sort_chunk_empty(self):
        """测试空列表。"""
        result = sort_chunk([], 'tim_sort')
        assert result == []

    def test_benchmark_sort(self):
        """测试基准测试功能。"""
        data = list(range(1000))
        import random
        random.shuffle(data)
        stats = benchmark_sort(data, 'tim_sort')
        assert stats['algorithm'] == 'tim_sort'
        assert stats['input_size'] == 1000
        assert stats['is_sorted'] is True
        assert stats['elapsed_seconds'] >= 0


# ========== K-Way Merge Tests ==========

class TestKWayMerge:
    def test_k_way_merge_two_files(self, tmp_path):
        """测试两文件归并。"""
        f1 = tmp_path / "sorted1.txt"
        f2 = tmp_path / "sorted2.txt"
        output = tmp_path / "merged.txt"

        f1.write_text("1\n3\n5\n7\n")
        f2.write_text("2\n4\n6\n8\n")

        stats = k_way_merge([str(f1), str(f2)], str(output))
        assert stats['merged_records'] == 8

        result = output.read_text().strip().split('\n')
        assert [int(x) for x in result] == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_k_way_merge_multiple_files(self, tmp_path):
        """测试多文件归并。"""
        outputs = []
        for i in range(5):
            f = tmp_path / f"sorted{i}.txt"
            f.write_text("".join(f"{i * 10 + j}\n" for j in range(1, 11)))
            outputs.append(str(f))

        output = tmp_path / "merged_all.txt"
        stats = k_way_merge(outputs, str(output))
        assert stats['merged_records'] == 50

        result = output.read_text().strip().split('\n')
        values = [int(x) for x in result]
        assert values == sorted(values)

    def test_k_way_merge_single_file(self, tmp_path):
        """测试单文件归并。"""
        f = tmp_path / "sorted.txt"
        f.write_text("1\n1\n3\n4\n5\n")
        output = tmp_path / "merged.txt"

        stats = k_way_merge([str(f)], str(output))
        assert stats['merged_records'] == 5

        result = output.read_text().strip().split('\n')
        assert [int(x) for x in result] == [1, 1, 3, 4, 5]

    def test_k_way_merge_empty_file(self, tmp_path):
        """测试含空文件的归并。"""
        f1 = tmp_path / "non_empty.txt"
        f2 = tmp_path / "empty.txt"
        output = tmp_path / "merged.txt"

        f1.write_text("2\n4\n6\n")
        f2.write_text("")

        stats = k_way_merge([str(f1), str(f2)], str(output))
        assert stats['merged_records'] == 3

    def test_multi_stage_merge(self, tmp_path):
        """测试多阶段归并。"""
        outputs = []
        for i in range(10):
            f = tmp_path / f"run{i}.txt"
            f.write_text("".join(f"{i * 100 + j}\n" for j in range(1, 11)))
            outputs.append(str(f))

        output = tmp_path / "final.txt"
        stages = multi_stage_merge(outputs, str(output), max_k=3)

        result = output.read_text().strip().split('\n')
        values = [int(x) for x in result]
        assert values == sorted(values)
        assert len(values) == 100


# ========== External Sort Tests ==========

class TestExternalSort:
    def test_full_external_sort(self, tmp_path):
        """测试完整外部排序流程。"""
        input_file = tmp_path / "large_input.txt"
        output_file = tmp_path / "large_output.txt"

        # 生成测试数据：500 个随机整数
        import random
        random.seed(42)
        data = [random.randint(1, 10000) for _ in range(500)]
        with open(input_file, 'w') as f:
            for val in data:
                f.write(f"{val}\n")

        temp_dir = str(tmp_path / "temp")
        sorter = ExternalSort(temp_dir=temp_dir, chunk_size_mb=0.01)
        result = sorter.sort(str(input_file), str(output_file))

        # 验证结果
        assert result.record_count == 500
        assert result.is_valid is True

        # 验证输出有序
        with open(output_file, 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]
        assert values == sorted(data)

    def test_external_sort_validation(self, tmp_path):
        """测试排序结果验证。"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        for i in range(100, 0, -1):
            with open(input_file, 'w') as f:
                f.write(f"{i}\n")

        sorter = ExternalSort(temp_dir=str(tmp_path / "temp"),
                              chunk_size_mb=0.001)
        result = sorter.sort(str(input_file), str(output_file))

        assert result.validate(str(input_file)) is True

    def test_external_sort_with_context_manager(self, tmp_path):
        """测试上下文管理器。"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        with open(input_file, 'w') as f:
            for i in range(50):
                f.write(f"{i * 2}\n")

        with ExternalSort(temp_dir=str(tmp_path / "temp"),
                          chunk_size_mb=0.001) as sorter:
            result = sorter.sort(str(input_file), str(output_file))

        assert result.record_count == 50

    def test_external_sort_summary(self, tmp_path):
        """测试摘要输出。"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        with open(input_file, 'w') as f:
            for i in range(10):
                f.write(f"{i}\n")

        sorter = ExternalSort(temp_dir=str(tmp_path / "temp"),
                              chunk_size_mb=0.001)
        result = sorter.sort(str(input_file), str(output_file))

        summary = result.summary()
        assert "外部排序结果摘要" in summary
        assert "记录数量: 10" in summary

    def test_external_sort_already_sorted(self, tmp_path):
        """测试已排序输入。"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        with open(input_file, 'w') as f:
            for i in range(100):
                f.write(f"{i}\n")

        sorter = ExternalSort(temp_dir=str(tmp_path / "temp"),
                              chunk_size_mb=0.001)
        result = sorter.sort(str(input_file), str(output_file))

        assert result.is_valid is True


# ========== Memory Management Tests ==========

class TestMemoryManagement:
    def test_compute_memory_profile(self):
        """测试内存配置计算。"""
        profile = compute_memory_profile(
            target_chunk_records=10000,
            record_size_bytes=10,
        )
        assert profile.chunk_size_mb > 0
        assert profile.max_merge_degree >= 2

    def test_adaptive_k_selection(self):
        """测试自适应 k 选择。"""
        k = adaptive_k_selection(
            num_runs=50,
            max_merge_degree=100,
            buffer_overhead_bytes=1024 * 1024 * 10,
        )
        assert k <= 50
        assert k >= 2

    def test_estimate_io_cost(self):
        """测试 I/O 成本估算。"""
        cost = estimate_io_cost(
            num_records=1000000,
            chunk_size=1024 * 1024,
            num_runs=10,
            merge_degree=5,
        )
        assert cost['total_io'] > 0
        assert cost['merge_rounds'] >= 1


# ========== I/O Optimization Tests ==========

class TestIOOptimization:
    def test_buffered_writer(self, tmp_path):
        """测试缓冲写入器。"""
        output = tmp_path / "buffered.txt"
        writer = BufferedWriter(str(output), buffer_size=1024)

        for i in range(100):
            writer.write(f"{i}\n")
        writer.close()

        result = output.read_text().strip().split('\n')
        assert len(result) == 100

    def test_buffered_reader(self, tmp_path):
        """测试缓冲读取器。"""
        input_file = tmp_path / "input.txt"
        input_file.write_text("".join(f"{i}\n" for i in range(50)))

        reader = BufferedReader(str(input_file))
        values = []
        while True:
            line = reader.read_line()
            if line is None:
                break
            values.append(int(line))
        reader.close()

        assert values == list(range(50))

    def test_optimize_io_for_merge(self):
        """测试 I/O 优化建议。"""
        config = optimize_io_for_merge(
            num_files=20,
            file_size_mb=50,
            available_memory_mb=512,
        )
        assert config['recommended_buffer_size'] > 0
        assert config['ideal_merge_degree'] == 20


# ========== Edge Case Tests ==========

class TestEdgeCases:
    def test_single_element_file(self, tmp_path):
        """测试单元素文件。"""
        input_file = tmp_path / "single.txt"
        output_file = tmp_path / "output.txt"
        with open(input_file, 'w') as f:
            f.write("42\n")

        sorter = ExternalSort(temp_dir=str(tmp_path / "temp"),
                              chunk_size_mb=0.001)
        result = sorter.sort(str(input_file), str(output_file))
        assert result.record_count == 1

        with open(output_file) as f:
            assert int(f.read().strip()) == 42

    def test_negative_numbers(self, tmp_path):
        """测试负数。"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        with open(input_file, 'w') as f:
            for val in [-5, -1, -3, 0, 2, -2, 1]:
                f.write(f"{val}\n")

        sorter = ExternalSort(temp_dir=str(tmp_path / "temp"),
                              chunk_size_mb=0.001)
        result = sorter.sort(str(input_file), str(output_file))

        with open(output_file) as f:
            values = [int(line.strip()) for line in f if line.strip()]
        assert values == [-5, -3, -2, -1, 0, 1, 2]

    def test_large_values(self, tmp_path):
        """测试大数值。"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        large_vals = [10**9, 10**18, 10**5, 10**12, 10**3]
        with open(input_file, 'w') as f:
            for val in large_vals:
                f.write(f"{val}\n")

        sorter = ExternalSort(temp_dir=str(tmp_path / "temp"),
                              chunk_size_mb=0.001)
        result = sorter.sort(str(input_file), str(output_file))

        with open(output_file) as f:
            values = [int(line.strip()) for line in f if line.strip()]
        assert values == sorted(large_vals)
