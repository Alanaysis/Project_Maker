"""
性能分析工具单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import (
    BloomFilter,
    CountingBloomFilter,
    ScalableBloomFilter,
    optimal_size,
    optimal_hash_count,
    false_positive_rate,
    compare_filters,
)
from bloom_filter.analysis import (
    false_positive_rate_analysis,
    benchmark_insert,
    benchmark_query,
    parameter_sweep,
    optimal_parameters_table,
)


class TestOptimalSize:
    """最优位数组大小测试"""

    def test_basic(self):
        """测试基本计算"""
        m = optimal_size(10000, 0.01)
        assert m > 0
        assert m > 10000  # 应该大于元素数量

    def test_smaller_fpr(self):
        """测试更小的误判率需要更大的数组"""
        m1 = optimal_size(10000, 0.01)
        m2 = optimal_size(10000, 0.001)
        assert m2 > m1

    def test_more_elements(self):
        """测试更多元素需要更大的数组"""
        m1 = optimal_size(10000, 0.01)
        m2 = optimal_size(100000, 0.01)
        assert m2 > m1

    def test_invalid_n(self):
        """测试无效 n"""
        with pytest.raises(ValueError):
            optimal_size(0, 0.01)

    def test_invalid_p(self):
        """测试无效 p"""
        with pytest.raises(ValueError):
            optimal_size(10000, 0.0)

        with pytest.raises(ValueError):
            optimal_size(10000, 1.0)


class TestOptimalHashCount:
    """最优哈希函数数量测试"""

    def test_basic(self):
        """测试基本计算"""
        k = optimal_hash_count(100000, 10000)
        assert k >= 1
        assert k <= 20

    def test_larger_array(self):
        """测试更大的数组需要更多哈希函数"""
        k1 = optimal_hash_count(100000, 10000)
        k2 = optimal_hash_count(200000, 10000)
        assert k2 >= k1

    def test_invalid_m(self):
        """测试无效 m"""
        with pytest.raises(ValueError):
            optimal_hash_count(0, 10000)

    def test_invalid_n(self):
        """测试无效 n"""
        with pytest.raises(ValueError):
            optimal_hash_count(100000, 0)


class TestFalsePositiveRate:
    """误判率测试"""

    def test_zero_elements(self):
        """测试零元素"""
        assert false_positive_rate(100000, 7, 0) == 0.0

    def test_basic(self):
        """测试基本计算"""
        fpr = false_positive_rate(100000, 7, 10000)
        assert 0.0 < fpr < 1.0

    def test_increases_with_n(self):
        """测试误判率随元素数量增加而增加"""
        fpr1 = false_positive_rate(100000, 7, 10000)
        fpr2 = false_positive_rate(100000, 7, 20000)
        assert fpr2 > fpr1

    def test_invalid_params(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            false_positive_rate(0, 7, 10000)

        with pytest.raises(ValueError):
            false_positive_rate(100000, 0, 10000)


class TestFalsePositiveRateAnalysis:
    """误判率分析测试"""

    def test_basic(self):
        """测试基本分析"""
        result = false_positive_rate_analysis(10000, 0.01, 10000)

        assert "design_capacity" in result
        assert "design_fpr" in result
        assert "actual_count" in result
        assert "bit_array_size" in result
        assert "hash_count" in result
        assert "theoretical_fpr" in result
        assert "actual_fpr" in result
        assert "bits_per_element" in result


class TestCompareFilters:
    """过滤器比较测试"""

    def test_basic(self):
        """测试基本比较"""
        results = compare_filters(1000, 0.01)

        assert "standard" in results
        assert "counting" in results
        assert "scalable" in results

        # 标准过滤器应该使用最少内存
        assert results["standard"]["memory_bytes"] < results["counting"]["memory_bytes"]


class TestBenchmarkInsert:
    """插入基准测试"""

    def test_basic(self):
        """测试基本基准"""
        items = [f"item_{i}" for i in range(1000)]

        result = benchmark_insert(
            lambda: BloomFilter(expected_items=10000, false_positive_rate=0.01),
            items,
        )

        assert result["count"] == 1000
        assert result["total_time"] > 0
        assert result["items_per_second"] > 0
        assert result["ns_per_item"] > 0


class TestBenchmarkQuery:
    """查询基准测试"""

    def test_basic(self):
        """测试基本基准"""
        existing = [f"item_{i}" for i in range(1000)]
        non_existing = [f"test_{i}" for i in range(1000)]

        result = benchmark_query(
            lambda: BloomFilter(expected_items=10000, false_positive_rate=0.01),
            existing,
            non_existing,
        )

        assert result["existing_count"] == 1000
        assert result["non_existing_count"] == 1000
        assert result["existing_time"] > 0
        assert result["non_existing_time"] > 0


class TestParameterSweep:
    """参数扫描测试"""

    def test_basic(self):
        """测试基本扫描"""
        results = parameter_sweep(10000)

        assert len(results) > 0
        for r in results:
            assert "n" in r
            assert "p_design" in r
            assert "m" in r
            assert "k" in r
            assert "fpr" in r
            assert "bits_per_element" in r


class TestOptimalParametersTable:
    """最优参数表测试"""

    def test_basic(self):
        """测试基本表格"""
        table = optimal_parameters_table()

        assert len(table) > 0
        for row in table:
            assert "n" in row
            assert "p" in row
            assert "m" in row
            assert "k" in row
            assert "fpr_actual" in row
            assert "bits_per_element" in row
            assert "bytes_per_element" in row
            assert "total_kb" in row
