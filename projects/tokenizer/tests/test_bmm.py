"""
逆向最大匹配分词测试
"""

import pytest
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dictionary import Dictionary
from src.bmm import BMM


class TestBMM:
    """BMM 测试类"""

    def _create_bmm(self, words):
        """创建 BMM 分词器"""
        dict = Dictionary()
        for word in words:
            dict.add(word, 100)
        return BMM(dict)

    def test_basic(self):
        """测试基本分词"""
        bmm = self._create_bmm(["我", "爱", "北京", "天安门"])
        result = bmm.segment("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_single_word(self):
        """测试单个词"""
        bmm = self._create_bmm(["北京"])
        result = bmm.segment("北京")
        assert result == ["北京"]

    def test_single_char(self):
        """测试单个字符"""
        bmm = self._create_bmm(["我"])
        result = bmm.segment("我")
        assert result == ["我"]

    def test_empty_text(self):
        """测试空文本"""
        bmm = self._create_bmm(["北京"])
        result = bmm.segment("")
        assert result == []

    def test_unknown_words(self):
        """测试未登录词"""
        bmm = self._create_bmm(["北京"])
        result = bmm.segment("我爱北京")
        assert result == ["我", "爱", "北京"]

    def test_ambiguity(self):
        """测试歧义处理"""
        bmm = self._create_bmm(["研究", "研究生", "生命", "的", "起源"])
        result = bmm.segment("研究生命的起源")
        # BMM 可能与 FMM 结果不同
        assert result == ["研究", "生命", "的", "起源"]

    def test_consecutive_chars(self):
        """测试连续单字"""
        bmm = self._create_bmm(["我", "爱", "你"])
        result = bmm.segment("我爱你")
        assert result == ["我", "爱", "你"]

    def test_mixed_length(self):
        """测试混合长度词语"""
        bmm = self._create_bmm(["中华", "人民", "共和国", "中华人民共和国"])
        result = bmm.segment("中华人民共和国")
        # BMM 从右向左匹配
        assert result == ["中华人民共和国"]

    def test_with_dictionary(self):
        """测试使用词典"""
        dict = Dictionary()
        dict.add("我", 200)
        dict.add("爱", 150)
        dict.add("北京", 100)
        dict.add("天安门", 50)

        bmm = BMM(dict)
        result = bmm.segment("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_reversed_result(self):
        """测试结果顺序"""
        bmm = self._create_bmm(["我", "爱", "北京"])
        result = bmm.segment("我爱北京")
        # BMM 从右向左扫描，但结果应该是正序
        assert result == ["我", "爱", "北京"]
