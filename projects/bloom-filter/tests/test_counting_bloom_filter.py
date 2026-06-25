"""
计数布隆过滤器单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import CountingBloomFilter


class TestCountingBloomFilter:
    """计数布隆过滤器测试"""

    def test_create_with_params(self):
        """测试通过参数创建"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        assert cbf.size > 0
        assert cbf.hash_count > 0
        assert cbf.count == 0

    def test_create_manual(self):
        """测试手动指定参数创建"""
        cbf = CountingBloomFilter(size=10000, hash_count=7)
        assert cbf.size == 10000
        assert cbf.hash_count == 7

    def test_invalid_params(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            CountingBloomFilter()

        with pytest.raises(ValueError):
            CountingBloomFilter(expected_items=1000, false_positive_rate=0.0)

    def test_add_and_contains(self):
        """测试添加和查询"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        cbf.add("hello")
        cbf.add("world")

        assert "hello" in cbf
        assert "world" in cbf
        assert "rust" not in cbf

    def test_add_many(self):
        """测试批量添加"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(100)]
        count = cbf.add_many(iter(items))

        assert count == 100
        assert cbf.count == 100

    def test_remove(self):
        """测试删除"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        cbf.add("hello")
        cbf.add("world")

        assert "hello" in cbf
        assert cbf.remove("hello") is True
        # 删除后可能仍存在 (假阳性)，但应该减少误判概率
        assert cbf.count == 1

    def test_remove_nonexistent(self):
        """测试删除不存在的元素"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        cbf.add("hello")

        # 删除不存在的元素应该返回 False
        assert cbf.remove("nonexistent") is False
        assert cbf.count == 1

    def test_remove_preserves_others(self):
        """测试删除不影响其他元素"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(100)]
        for item in items:
            cbf.add(item)

        # 删除一半
        for item in items[:50]:
            cbf.remove(item)

        # 剩余元素应该仍然存在
        for item in items[50:]:
            assert item in cbf

    def test_clear(self):
        """测试清空"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        cbf.add("hello")
        assert "hello" in cbf

        cbf.clear()
        assert "hello" not in cbf
        assert cbf.count == 0

    def test_fill_ratio(self):
        """测试填充率"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert cbf.fill_ratio() == 0.0

        cbf.add("hello")
        assert 0.0 < cbf.fill_ratio() < 1.0

    def test_estimated_fpr(self):
        """测试估算误判率"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert cbf.estimated_false_positive_rate() == 0.0

        for i in range(100):
            cbf.add(f"item_{i}")

        fpr = cbf.estimated_false_positive_rate()
        assert 0.0 < fpr < 1.0

    def test_memory_usage(self):
        """测试内存使用统计"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        mem = cbf.memory_usage()

        assert "counter_array_size" in mem
        assert "counter_array_bytes" in mem
        assert "counter_array_mb" in mem
        assert "max_count" in mem

    def test_max_count(self):
        """测试最大计数值"""
        cbf = CountingBloomFilter(
            expected_items=1000, false_positive_rate=0.01, max_count=100
        )
        assert cbf.max_count == 100

    def test_len(self):
        """测试 len()"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert len(cbf) == 0

        cbf.add("hello")
        assert len(cbf) == 1

    def test_repr(self):
        """测试 __repr__"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        r = repr(cbf)

        assert "CountingBloomFilter" in r
        assert "size=" in r

    def test_duplicate_add_and_remove(self):
        """测试重复添加和删除"""
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

        # 添加两次
        cbf.add("hello")
        cbf.add("hello")
        assert cbf.count == 2

        # 删除一次
        cbf.remove("hello")
        assert cbf.count == 1

        # 仍然存在
        assert "hello" in cbf

    def test_no_false_negatives(self):
        """测试无假阴性"""
        cbf = CountingBloomFilter(expected_items=10000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(1000)]
        for item in items:
            cbf.add(item)

        for item in items:
            assert item in cbf, f"False negative for {item}"
