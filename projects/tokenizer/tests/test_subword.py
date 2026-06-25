"""
子词分词器测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.subword import BPETokenizer, WordPieceTokenizer, UnigramTokenizer


class TestBPETokenizer:
    """BPE 分词器测试类"""

    def test_init(self):
        """测试初始化"""
        bpe = BPETokenizer(vocab_size=100)
        assert bpe.vocab_size == 100
        assert len(bpe.merges) == 0

    def test_train(self):
        """测试训练"""
        bpe = BPETokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        bpe.train(corpus)
        assert len(bpe.vocab) > 0

    def test_tokenize(self):
        """测试分词"""
        bpe = BPETokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        bpe.train(corpus)
        tokens = bpe.tokenize("lower")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_tokenize_empty(self):
        """测试空文本"""
        bpe = BPETokenizer(vocab_size=50)
        tokens = bpe.tokenize("")
        assert tokens == []

    def test_tokenize_single_word(self):
        """测试单个词"""
        bpe = BPETokenizer(vocab_size=50)
        corpus = ["hello world", "hello hello"]
        bpe.train(corpus)
        tokens = bpe.tokenize("hello")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        bpe = BPETokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        bpe.train(corpus)

        # 保存
        model_path = str(tmp_path / "bpe_model.json")
        bpe.save(model_path)

        # 加载
        bpe2 = BPETokenizer()
        bpe2.load(model_path)

        # 验证
        assert bpe.vocab_size == bpe2.vocab_size
        assert len(bpe.merges) == len(bpe2.merges)

    def test_multiple_words(self):
        """测试多个词"""
        bpe = BPETokenizer(vocab_size=100)
        corpus = ["the cat sat on the mat", "the dog ran in the park"]
        bpe.train(corpus)
        tokens = bpe.tokenize("the cat")
        assert isinstance(tokens, list)


class TestWordPieceTokenizer:
    """WordPiece 分词器测试类"""

    def test_init(self):
        """测试初始化"""
        wp = WordPieceTokenizer(vocab_size=100)
        assert wp.vocab_size == 100
        assert wp.unk_token == "[UNK]"
        assert wp.prefix == "##"

    def test_train(self):
        """测试训练"""
        wp = WordPieceTokenizer(vocab_size=50)
        corpus = ["unaffable", "unlikely", "unhappy"]
        wp.train(corpus)
        assert len(wp.vocab) > 0

    def test_tokenize(self):
        """测试分词"""
        wp = WordPieceTokenizer(vocab_size=100)
        corpus = ["unaffable", "unlikely", "unhappy"]
        wp.train(corpus)
        tokens = wp.tokenize("unaffable")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_tokenize_empty(self):
        """测试空文本"""
        wp = WordPieceTokenizer(vocab_size=100)
        tokens = wp.tokenize("")
        assert tokens == []

    def test_tokenize_unknown(self):
        """测试未知词"""
        wp = WordPieceTokenizer(vocab_size=50)
        corpus = ["hello world"]
        wp.train(corpus)
        tokens = wp.tokenize("xyz")
        assert isinstance(tokens, list)

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        wp = WordPieceTokenizer(vocab_size=50)
        corpus = ["unaffable", "unlikely"]
        wp.train(corpus)

        # 保存
        model_path = str(tmp_path / "wp_model.json")
        wp.save(model_path)

        # 加载
        wp2 = WordPieceTokenizer()
        wp2.load(model_path)

        # 验证
        assert wp.vocab_size == wp2.vocab_size
        assert wp.unk_token == wp2.unk_token
        assert wp.prefix == wp2.prefix

    def test_prefix(self):
        """测试子词前缀"""
        wp = WordPieceTokenizer(vocab_size=20)
        corpus = ["unaffable", "unlikely", "unhappy"]
        wp.train(corpus)
        tokens = wp.tokenize("unaffable")
        # 子词应该有前缀
        has_prefix = any(t.startswith(wp.prefix) for t in tokens)
        assert has_prefix


class TestUnigramTokenizer:
    """Unigram 分词器测试类"""

    def test_init(self):
        """测试初始化"""
        uni = UnigramTokenizer(vocab_size=100)
        assert uni.vocab_size == 100

    def test_train(self):
        """测试训练"""
        uni = UnigramTokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        uni.train(corpus)
        assert len(uni.vocab) > 0

    def test_tokenize(self):
        """测试分词"""
        uni = UnigramTokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        uni.train(corpus)
        tokens = uni.tokenize("lower")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_tokenize_empty(self):
        """测试空文本"""
        uni = UnigramTokenizer(vocab_size=50)
        tokens = uni.tokenize("")
        assert tokens == []

    def test_tokenize_single_word(self):
        """测试单个词"""
        uni = UnigramTokenizer(vocab_size=50)
        corpus = ["hello world", "hello hello"]
        uni.train(corpus)
        tokens = uni.tokenize("hello")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        uni = UnigramTokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        uni.train(corpus)

        # 保存
        model_path = str(tmp_path / "unigram_model.json")
        uni.save(model_path)

        # 加载
        uni2 = UnigramTokenizer()
        uni2.load(model_path)

        # 验证
        assert uni.vocab_size == uni2.vocab_size

    def test_viterbi_segment(self):
        """测试维特比分割"""
        uni = UnigramTokenizer(vocab_size=50)
        corpus = ["low lower newest wide", "low low low"]
        uni.train(corpus)
        tokens = uni._viterbi_segment("lower")
        assert isinstance(tokens, list)
        assert len(tokens) > 0
