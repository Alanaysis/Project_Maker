"""词汇表测试"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.vocabulary import Vocabulary


class TestVocabulary:
    """词汇表测试类"""

    def test_init(self):
        """测试初始化"""
        vocab = Vocabulary(min_count=2)
        assert vocab.min_count == 2
        assert len(vocab) == 0

    def test_build_basic(self):
        """测试基本构建"""
        corpus = [
            ["the", "cat", "sat"],
            ["the", "dog", "ran"]
        ]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        assert len(vocab) == 5
        assert "the" in vocab
        assert "cat" in vocab
        assert "dog" in vocab

    def test_build_min_count(self):
        """测试最小词频过滤"""
        corpus = [
            ["a", "b", "c"],
            ["a", "b", "d"]
        ]
        vocab = Vocabulary(min_count=2)
        vocab.build(corpus)

        assert "a" in vocab  # freq=2
        assert "b" in vocab  # freq=2
        assert "c" not in vocab  # freq=1
        assert "d" not in vocab  # freq=1

    def test_word_freq(self):
        """测试词频统计"""
        corpus = [
            ["a", "a", "b"],
            ["a", "c"]
        ]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        assert vocab.get_freq("a") == 3
        assert vocab.get_freq("b") == 1
        assert vocab.get_freq("c") == 1
        assert vocab.get_freq("d") == 0

    def test_word_idx_mapping(self):
        """测试词索引映射"""
        corpus = [["hello", "world"]]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        # 测试 get_idx
        idx_hello = vocab.get_idx("hello")
        idx_world = vocab.get_idx("world")
        assert idx_hello is not None
        assert idx_world is not None
        assert idx_hello != idx_world

        # 测试 get_word
        assert vocab.get_word(idx_hello) == "hello"
        assert vocab.get_word(idx_world) == "world"

    def test_unknown_word(self):
        """测试未知词处理"""
        corpus = [["hello", "world"]]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        assert "unknown" not in vocab
        assert vocab.get_idx("unknown") is None
        assert vocab.get_freq("unknown") == 0

    def test_total_words(self):
        """测试总词数统计"""
        corpus = [
            ["a", "b"],
            ["a", "c"]
        ]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        assert vocab.total_words == 4

    def test_empty_corpus(self):
        """测试空语料"""
        corpus = []
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        assert len(vocab) == 0

    def test_neg_table(self):
        """测试负采样表"""
        corpus = [["a", "b", "c"]] * 10
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        table = vocab.get_neg_table(table_size=1000)
        assert len(table) == 1000
        assert all(0 <= idx < len(vocab) for idx in table)

    def test_word_freqs_array(self):
        """测试词频数组"""
        corpus = [["a", "a", "b"]]
        vocab = Vocabulary(min_count=1)
        vocab.build(corpus)

        freqs = vocab.get_word_freqs_array()
        assert len(freqs) == len(vocab)
        assert sum(freqs) == vocab.total_words


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
