"""
正向最大匹配分词测试
"""

import pytest
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dictionary import Dictionary
from src.fmm import FMM


class TestFMM:
    """FMM 测试类"""

    def _create_fmm(self, words):
        """创建 FMM 分词器"""
        dict = Dictionary()
        for word in words:
            dict.add(word, 100)
        return FMM(dict)

    def test_basic(self):
        """测试基本分词"""
        fmm = self._create_fmm(["我", "爱", "北京", "天安门"])
        result = fmm.segment("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_single_word(self):
        """测试单个词"""
        fmm = self._create_fmm(["北京"])
        result = fmm.segment("北京")
        assert result == ["北京"]

    def test_single_char(self):
        """测试单个字符"""
        fmm = self._create_fmm(["我"])
        result = fmm.segment("我")
        assert result == ["我"]

    def test_empty_text(self):
        """测试空文本"""
        fmm = self._create_fmm(["北京"])
        result = fmm.segment("")
        assert result == []

    def test_unknown_words(self):
        """测试未登录词"""
        fmm = self._create_fmm(["北京"])
        result = fmm.segment("我爱北京")
        assert result == ["我", "爱", "北京"]

    def test_longest_match(self):
        """测试最长匹配"""
        fmm = self._create_fmm(["研究", "研究生", "生命", "的", "起源"])
        result = fmm.segment("研究生命的起源")
        # FMM 会选择最长匹配 "研究生"
        assert result == ["研究生", "命", "的", "起源"]

    def test_consecutive_chars(self):
        """测试连续单字"""
        fmm = self._create_fmm(["我", "爱", "你"])
        result = fmm.segment("我爱你")
        assert result == ["我", "爱", "你"]

    def test_mixed_length(self):
        """测试混合长度词语"""
        fmm = self._create_fmm(["中华", "人民", "共和国", "中华人民共和国"])
        result = fmm.segment("中华人民共和国")
        # FMM 会选择最长匹配
        assert result == ["中华人民共和国"]

    def test_with_dictionary(self):
        """测试使用词典文件"""
        dict = Dictionary()
        dict.add("我", 200)
        dict.add("爱", 150)
        dict.add("北京", 100)
        dict.add("天安门", 50)

        fmm = FMM(dict)
        result = fmm.segment("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_repeated_words(self):
        """测试重复词语"""
        fmm = self._create_fmm(["我", "爱"])
        result = fmm.segment("我爱我爱")
        assert result == ["我", "爱", "我", "爱"]
