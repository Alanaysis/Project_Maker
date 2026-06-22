"""Vocabulary 测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vocabulary import Vocabulary


class TestVocabulary:
    """词汇表测试"""

    def test_init(self):
        """测试初始化"""
        vocab = Vocabulary()
        assert vocab.size == len(Vocabulary.SPECIAL_TOKENS)
        assert vocab.pad_id == 0
        assert vocab.unk_id == 1
        assert vocab.bos_id == 2
        assert vocab.eos_id == 3

    def test_build(self):
        """测试构建词汇表"""
        corpus = [
            ["hello", "world"],
            ["hello", "there"],
            ["world", "peace"],
        ]
        vocab = Vocabulary().build(corpus)

        assert vocab.size > len(Vocabulary.SPECIAL_TOKENS)
        assert vocab.get_id("hello") != vocab.unk_id
        assert vocab.get_id("world") != vocab.unk_id
        assert vocab.get_id("there") != vocab.unk_id

    def test_min_freq(self):
        """测试最小词频过滤"""
        corpus = [
            ["hello", "world"],
            ["hello", "there"],
            ["world", "peace"],
        ]
        vocab = Vocabulary(min_freq=2).build(corpus)

        # "hello" 和 "world" 出现 2 次
        assert vocab.get_id("hello") != vocab.unk_id
        assert vocab.get_id("world") != vocab.unk_id

        # "there" 和 "peace" 只出现 1 次
        assert vocab.get_id("there") == vocab.unk_id
        assert vocab.get_id("peace") == vocab.unk_id

    def test_encode_decode(self):
        """测试编码和解码"""
        corpus = [["hello", "world", "foo"]]
        vocab = Vocabulary().build(corpus)

        tokens = ["hello", "world", "foo"]
        ids = vocab.encode(tokens)
        decoded = vocab.decode(ids)

        assert decoded == tokens

    def test_encode_unknown(self):
        """测试未知词编码"""
        corpus = [["hello"]]
        vocab = Vocabulary().build(corpus)

        ids = vocab.encode(["hello", "unknown"])
        assert ids[0] != vocab.unk_id
        assert ids[1] == vocab.unk_id

    def test_tokenize(self):
        """测试分词"""
        tokens = Vocabulary.tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_tokenize_empty(self):
        """测试空文本分词"""
        tokens = Vocabulary.tokenize("")
        assert tokens == []

    def test_get_freq(self):
        """测试获取词频"""
        corpus = [["hello", "hello", "world"]]
        vocab = Vocabulary().build(corpus)

        assert vocab.get_freq("hello") == 2
        assert vocab.get_freq("world") == 1
        assert vocab.get_freq("unknown") == 0

    def test_chain_build(self):
        """测试链式调用"""
        corpus = [["hello"]]
        vocab = Vocabulary()
        result = vocab.build(corpus)
        assert result is vocab


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
