"""降采样测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.subsampling import SubSampler


class TestSubSampler:
    """降采样器测试类"""

    def test_init(self):
        """测试初始化"""
        word_freq = {"the": 1000, "cat": 100, "sat": 50}
        total_words = 1150
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        assert sampler.threshold == 1e-3
        assert len(sampler.keep_probs) == 3

    def test_keep_probabilities(self):
        """测试保留概率"""
        word_freq = {"the": 1000, "cat": 100, "sat": 50}
        total_words = 1150
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        # 高频词应该有更低的保留概率
        prob_high = sampler.get_keep_probability("the")
        prob_low = sampler.get_keep_probability("sat")
        assert prob_high <= prob_low

    def test_keep_prob_range(self):
        """测试保留概率范围"""
        word_freq = {"a": 100, "b": 50, "c": 10}
        total_words = 160
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        for word in word_freq:
            prob = sampler.get_keep_probability(word)
            assert 0 <= prob <= 1

    def test_should_keep(self):
        """测试是否保留"""
        word_freq = {"the": 1000, "cat": 100}
        total_words = 1100
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        # 应该总是返回布尔值（numpy bool 也是 bool 的子类）
        for _ in range(100):
            result_the = sampler.should_keep("the")
            result_cat = sampler.should_keep("cat")
            assert isinstance(result_the, (bool, np.bool_))
            assert isinstance(result_cat, (bool, np.bool_))

    def test_unknown_word_kept(self):
        """测试未知词保留"""
        word_freq = {"the": 1000}
        total_words = 1000
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        # 未知词应该保留
        for _ in range(100):
            assert sampler.should_keep("unknown") == True

    def test_subsample_sentence(self):
        """测试句子降采样"""
        word_freq = {"the": 1000, "cat": 100, "sat": 50, "on": 200, "mat": 30}
        total_words = 1380
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        sentence = ["the", "cat", "sat", "on", "the", "mat"]
        result = sampler.subsample_sentence(sentence)

        # 结果应该是原句子的子集
        assert len(result) <= len(sentence)
        assert all(w in sentence for w in result)

    def test_subsample_corpus(self):
        """测试语料降采样"""
        word_freq = {"the": 1000, "cat": 100, "dog": 100}
        total_words = 1200
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        corpus = [
            ["the", "cat"],
            ["the", "dog"],
            ["cat", "dog"]
        ]
        result = sampler.subsample_corpus(corpus)

        # 结果应该是非空句子的列表
        assert len(result) <= len(corpus)
        assert all(len(s) > 0 for s in result)

    def test_high_freq_dropped_more(self):
        """测试高频词被丢弃更多"""
        word_freq = {"the": 10000, "cat": 10, "sat": 5}
        total_words = 10015
        sampler = SubSampler(word_freq, total_words, threshold=1e-4)

        # 统计保留次数
        keep_count = {"the": 0, "cat": 0, "sat": 0}
        n_trials = 10000

        for _ in range(n_trials):
            for word in keep_count:
                if sampler.should_keep(word):
                    keep_count[word] += 1

        # 高频词应该被保留更少
        assert keep_count["the"] < keep_count["cat"]
        assert keep_count["cat"] < keep_count["sat"]

    def test_zero_threshold(self):
        """测试零阈值（不降采样）"""
        word_freq = {"the": 1000, "cat": 100}
        total_words = 1100
        sampler = SubSampler(word_freq, total_words, threshold=0)

        # 零阈值时保留概率应该是1
        for word in word_freq:
            assert sampler.get_keep_probability(word) == 1.0

    def test_empty_corpus(self):
        """测试空语料"""
        word_freq = {}
        total_words = 0
        sampler = SubSampler(word_freq, total_words, threshold=1e-3)

        result = sampler.subsample_corpus([])
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
