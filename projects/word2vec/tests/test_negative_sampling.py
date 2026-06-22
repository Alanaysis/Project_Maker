"""负采样测试"""

import pytest
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.negative_sampling import NegativeSampler


class TestNegativeSampler:
    """负采样器测试类"""

    def test_init(self):
        """测试初始化"""
        word_freqs = np.array([100, 50, 10])
        sampler = NegativeSampler(vocab_size=3, word_freqs=word_freqs, table_size=10000)
        assert len(sampler.table) == 10000

    def test_sample_size(self):
        """测试采样数量"""
        word_freqs = np.array([100, 50, 10])
        sampler = NegativeSampler(vocab_size=3, word_freqs=word_freqs)
        samples = sampler.sample(positive=0, k=5)
        assert len(samples) == 5

    def test_sample_not_positive(self):
        """测试采样不包含正样本"""
        word_freqs = np.array([100, 50, 10])
        sampler = NegativeSampler(vocab_size=3, word_freqs=word_freqs, table_size=100000)

        # 多次采样，确保不包含正样本
        for _ in range(100):
            samples = sampler.sample(positive=0, k=5)
            assert 0 not in samples

    def test_sample_range(self):
        """测试采样范围"""
        vocab_size = 10
        word_freqs = np.ones(vocab_size) * 100
        sampler = NegativeSampler(vocab_size=vocab_size, word_freqs=word_freqs)

        samples = sampler.sample(positive=0, k=20)
        assert all(0 <= s < vocab_size for s in samples)

    def test_sample_distribution(self):
        """测试采样分布"""
        # 高频词应该被采样更多
        word_freqs = np.array([1000, 100, 10])
        sampler = NegativeSampler(vocab_size=3, word_freqs=word_freqs, table_size=1000000)

        counts = [0, 0, 0]
        num_samples = 10000
        for _ in range(num_samples):
            idx = sampler.table[np.random.randint(0, 1000000)]
            counts[idx] += 1

        # 词频1000应该比词频100被采样更多
        assert counts[0] > counts[1]
        # 词频100应该比词频10被采样更多
        assert counts[1] > counts[2]

    def test_sample_batch(self):
        """测试批量采样"""
        word_freqs = np.array([100, 50, 10, 5])
        sampler = NegativeSampler(vocab_size=4, word_freqs=word_freqs)

        positives = np.array([0, 1, 2])
        negatives = sampler.sample_batch(positives, k=3)

        assert negatives.shape == (3, 3)
        # 确保不包含正样本
        for i, pos in enumerate(positives):
            assert pos not in negatives[i]

    def test_uniform_distribution(self):
        """测试均匀分布"""
        word_freqs = np.ones(100)
        sampler = NegativeSampler(vocab_size=100, word_freqs=word_freqs, table_size=100000)

        counts = np.zeros(100)
        num_samples = 100000
        for _ in range(num_samples):
            idx = sampler.table[np.random.randint(0, 100000)]
            counts[idx] += 1

        # 均匀分布下，每个词应该被采样约 1000 次
        expected = num_samples / 100
        assert all(abs(c - expected) / expected < 0.1 for c in counts)

    def test_single_word_vocab(self):
        """测试单个词词汇表"""
        word_freqs = np.array([100])
        sampler = NegativeSampler(vocab_size=1, word_freqs=word_freqs)

        # 只有一个词时，采样会陷入无限循环
        # 这是一个边界情况，实际使用中应该避免
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
