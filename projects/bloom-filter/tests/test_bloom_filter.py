"""
标准布隆过滤器单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import BloomFilter


class TestBloomFilter:
    """标准布隆过滤器测试"""

    def test_create_with_params(self):
        """测试通过参数创建"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        assert bf.size > 0
        assert bf.hash_count > 0
        assert bf.count == 0

    def test_create_manual(self):
        """测试手动指定参数创建"""
        bf = BloomFilter(size=10000, hash_count=7)
        assert bf.size == 10000
        assert bf.hash_count == 7

    def test_invalid_params(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            BloomFilter()

        with pytest.raises(ValueError):
            BloomFilter(expected_items=1000, false_positive_rate=0.0)

        with pytest.raises(ValueError):
            BloomFilter(expected_items=1000, false_positive_rate=1.0)

    def test_add_and_contains(self):
        """测试添加和查询"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        bf.add("hello")
        bf.add("world")

        assert "hello" in bf
        assert "world" in bf
        assert "rust" not in bf

    def test_add_many(self):
        """测试批量添加"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(100)]
        count = bf.add_many(iter(items))

        assert count == 100
        assert bf.count == 100

        for item in items:
            assert item in bf

    def test_contains_nonexistent(self):
        """测试查询不存在的元素"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        for i in range(100):
            bf.add(f"item_{i}")

        # 不存在的元素应该返回 False
        assert "nonexistent" not in bf

    def test_no_false_negatives(self):
        """测试无假阴性"""
        bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(1000)]
        for item in items:
            bf.add(item)

        # 所有插入的元素都应该存在
        for item in items:
            assert item in bf, f"False negative for {item}"

    def test_false_positive_rate(self):
        """测试误判率在合理范围内"""
        n = 10000
        p = 0.01
        bf = BloomFilter(expected_items=n, false_positive_rate=p)

        for i in range(n):
            bf.add(f"item_{i}")

        # 测试误判率
        test_size = 100000
        false_positives = sum(
            1 for i in range(test_size) if f"test_{i}" in bf
        )
        actual_fpr = false_positives / test_size

        # 误判率应该接近设计值 (允许 2 倍误差)
        assert actual_fpr < p * 2, f"False positive rate too high: {actual_fpr}"

    def test_clear(self):
        """测试清空"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        bf.add("hello")
        assert "hello" in bf

        bf.clear()
        assert "hello" not in bf
        assert bf.count == 0

    def test_fill_ratio(self):
        """测试填充率"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert bf.fill_ratio() == 0.0

        bf.add("hello")
        assert 0.0 < bf.fill_ratio() < 1.0

    def test_estimated_fpr(self):
        """测试估算误判率"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert bf.estimated_false_positive_rate() == 0.0

        for i in range(100):
            bf.add(f"item_{i}")

        fpr = bf.estimated_false_positive_rate()
        assert 0.0 < fpr < 1.0

    def test_memory_usage(self):
        """测试内存使用统计"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        mem = bf.memory_usage()

        assert "bit_array_size" in mem
        assert "bit_array_bytes" in mem
        assert "bit_array_mb" in mem
        assert "hash_count" in mem
        assert "element_count" in mem

    def test_len(self):
        """测试 len()"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert len(bf) == 0

        bf.add("hello")
        assert len(bf) == 1

    def test_repr(self):
        """测试 __repr__"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        r = repr(bf)

        assert "BloomFilter" in r
        assert "size=" in r
        assert "hash_count=" in r

    def test_different_types(self):
        """测试不同类型的数据"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        bf.add("string")
        bf.add(12345)
        bf.add(3.14)
        bf.add(b"bytes")

        assert "string" in bf
        assert 12345 in bf
        assert 3.14 in bf
        assert b"bytes" in bf

    def test_duplicate_add(self):
        """测试重复添加"""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

        bf.add("hello")
        bf.add("hello")

        assert bf.count == 2
        assert "hello" in bf
