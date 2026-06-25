"""
可扩展布隆过滤器单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import ScalableBloomFilter


class TestScalableBloomFilter:
    """可扩展布隆过滤器测试"""

    def test_create(self):
        """测试创建"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)
        assert sbf.layer_count == 1
        assert sbf.count == 0

    def test_invalid_params(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            ScalableBloomFilter(initial_capacity=0)

        with pytest.raises(ValueError):
            ScalableBloomFilter(false_positive_rate=0.0)

        with pytest.raises(ValueError):
            ScalableBloomFilter(scaling_factor=1.0)

        with pytest.raises(ValueError):
            ScalableBloomFilter(tightening_ratio=0.0)

    def test_add_and_contains(self):
        """测试添加和查询"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)

        sbf.add("hello")
        sbf.add("world")

        assert "hello" in sbf
        assert "world" in sbf
        assert "rust" not in sbf

    def test_add_many(self):
        """测试批量添加"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(100)]
        count = sbf.add_many(iter(items))

        assert count == 100
        assert sbf.count == 100

    def test_scaling(self):
        """测试自动扩容"""
        initial_capacity = 100
        sbf = ScalableBloomFilter(
            initial_capacity=initial_capacity,
            false_positive_rate=0.01,
            scaling_factor=2.0,
        )

        # 插入超过初始容量的元素
        n = 1000
        for i in range(n):
            sbf.add(f"item_{i}")

        # 应该创建了多层
        assert sbf.layer_count > 1
        assert sbf.count == n

    def test_no_false_negatives(self):
        """测试无假阴性"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)

        items = [f"item_{i}" for i in range(5000)]
        for item in items:
            sbf.add(item)

        for item in items:
            assert item in sbf, f"False negative for {item}"

    def test_false_positive_rate(self):
        """测试误判率在合理范围内"""
        n = 5000
        p = 0.01
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=p)

        for i in range(n):
            sbf.add(f"item_{i}")

        # 测试误判率
        test_size = 10000
        false_positives = sum(
            1 for i in range(test_size) if f"test_{i}" in sbf
        )
        actual_fpr = false_positives / test_size

        # 误判率应该接近设计值
        assert actual_fpr < p * 3, f"False positive rate too high: {actual_fpr}"

    def test_layer_info(self):
        """测试层信息"""
        sbf = ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)

        for i in range(500):
            sbf.add(f"item_{i}")

        info = sbf.layer_info()
        assert len(info) == sbf.layer_count

        for layer in info:
            assert "index" in layer
            assert "size" in layer
            assert "hash_count" in layer
            assert "capacity" in layer
            assert "count" in layer
            assert "fill_ratio" in layer

    def test_memory_usage(self):
        """测试内存使用统计"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)
        mem = sbf.memory_usage()

        assert "layer_count" in mem
        assert "total_bytes" in mem
        assert "total_mb" in mem
        assert "total_count" in mem

    def test_current_capacity(self):
        """测试总容量"""
        sbf = ScalableBloomFilter(
            initial_capacity=100,
            false_positive_rate=0.01,
            scaling_factor=2.0,
        )

        # 初始容量
        initial = sbf.current_capacity
        assert initial >= 100

        # 扩容后
        for i in range(500):
            sbf.add(f"item_{i}")

        assert sbf.current_capacity > initial

    def test_clear(self):
        """测试清空"""
        sbf = ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)

        for i in range(500):
            sbf.add(f"item_{i}")

        assert sbf.layer_count > 1

        sbf.clear()
        assert sbf.layer_count == 1
        assert sbf.count == 0

    def test_len(self):
        """测试 len()"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)

        assert len(sbf) == 0

        sbf.add("hello")
        assert len(sbf) == 1

    def test_repr(self):
        """测试 __repr__"""
        sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)
        r = repr(sbf)

        assert "ScalableBloomFilter" in r
        assert "layers=" in r
        assert "count=" in r

    def test_scaling_factor(self):
        """测试不同扩容因子"""
        sbf1 = ScalableBloomFilter(
            initial_capacity=100, false_positive_rate=0.01, scaling_factor=2.0
        )
        sbf2 = ScalableBloomFilter(
            initial_capacity=100, false_positive_rate=0.01, scaling_factor=3.0
        )

        for i in range(1000):
            sbf1.add(f"item_{i}")
            sbf2.add(f"item_{i}")

        # 更大的扩容因子应该产生更少的层
        assert sbf2.layer_count <= sbf1.layer_count

    def test_tightening_ratio(self):
        """测试不同收紧比例"""
        sbf1 = ScalableBloomFilter(
            initial_capacity=100, false_positive_rate=0.01, tightening_ratio=0.5
        )
        sbf2 = ScalableBloomFilter(
            initial_capacity=100, false_positive_rate=0.01, tightening_ratio=0.9
        )

        for i in range(500):
            sbf1.add(f"item_{i}")
            sbf2.add(f"item_{i}")

        # 收紧比例越小，误判率应该越低
        assert sbf1.estimated_false_positive_rate() <= sbf2.estimated_false_positive_rate() * 1.5
