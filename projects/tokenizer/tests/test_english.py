"""
英文分词器测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.english import EnglishTokenizer


class TestEnglishTokenizer:
    """英文分词器测试类"""

    def test_basic(self):
        """测试基本分词"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("Hello world")
        assert result == ["Hello", "world"]

    def test_punctuation(self):
        """测试标点处理"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("Hello, world!")
        assert "Hello" in result
        assert "," in result
        assert "world" in result
        assert "!" in result

    def test_contraction_expand(self):
        """测试缩写展开"""
        tokenizer = EnglishTokenizer(expand_contractions=True)
        result = tokenizer.tokenize("I can't believe it")
        assert "can" in result
        assert "not" in result

    def test_contraction_no_expand(self):
        """测试不展开缩写"""
        tokenizer = EnglishTokenizer(expand_contractions=False)
        result = tokenizer.tokenize("I can't believe it")
        assert "can't" in result

    def test_empty_text(self):
        """测试空文本"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("")
        assert result == []

    def test_numbers(self):
        """测试数字处理"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("I have 100 apples")
        assert "100" in result

    def test_decimal_numbers(self):
        """测试小数处理"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("The price is 3.14 dollars")
        assert "3.14" in result

    def test_abbreviation(self):
        """测试缩略词"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("Mr. Smith went to Washington")
        assert "Mr." in result

    def test_tokenize_words_only(self):
        """测试只返回单词"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize_words_only("Hello, world!")
        assert "Hello" in result
        assert "world" in result
        assert "," not in result
        assert "!" not in result

    def test_sentence_split(self):
        """测试分句"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.sentence_split("Hello world. How are you? I am fine!")
        assert len(result) == 3
        assert "Hello world." in result[0]

    def test_multiple_contractions(self):
        """测试多个缩写"""
        tokenizer = EnglishTokenizer(expand_contractions=True)
        result = tokenizer.tokenize("I'm happy and you're sad")
        assert "I" in result
        assert "am" in result
        assert "you" in result
        assert "are" in result

    def test_complex_sentence(self):
        """测试复杂句子"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("The U.S.A. is a country in North America.")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_url(self):
        """测试 URL 处理"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("Visit https://example.com for more info")
        assert "https://example.com" in result

    def test_percentage(self):
        """测试百分比"""
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("The growth rate is 15%")
        assert "15%" in result
