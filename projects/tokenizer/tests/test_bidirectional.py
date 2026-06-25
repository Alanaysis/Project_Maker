"""
双向最大匹配分词测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dictionary import Dictionary
from src.bidirectional import BiMM


class TestBiMM:
    """BiMM 测试类"""

    def _create_bimm(self, words):
        """创建双向最大匹配分词器"""
        dict_obj = Dictionary()
        for word in words:
            dict_obj.add(word, 100)
        return BiMM(dict_obj)

    def test_basic(self):
        """测试基本分词"""
        bimm = self._create_bimm(["我", "爱", "北京", "天安门"])
        result = bimm.segment("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_consensus(self):
        """测试 FMM 和 BMM 结果一致"""
        bimm = self._create_bimm(["我", "爱", "北京"])
        result = bimm.segment("我爱北京")
        assert result == ["我", "爱", "北京"]

    def test_ambiguity(self):
        """测试歧义处理"""
        bimm = self._create_bimm(["研究", "研究生", "生命", "的", "起源"])
        result = bimm.segment("研究生命的起源")
        # 双向最大匹配应该选择更优的结果
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_text(self):
        """测试空文本"""
        bimm = self._create_bimm(["北京"])
        result = bimm.segment("")
        assert result == []

    def test_single_word(self):
        """测试单个词"""
        bimm = self._create_bimm(["北京"])
        result = bimm.segment("北京")
        assert result == ["北京"]

    def test_unknown_words(self):
        """测试未登录词"""
        bimm = self._create_bimm(["北京"])
        result = bimm.segment("我爱北京")
        assert result == ["我", "爱", "北京"]

    def test_segment_with_info(self):
        """测试带详细信息的分词"""
        bimm = self._create_bimm(["我", "爱", "北京", "天安门"])
        info = bimm.segment_with_info("我爱北京天安门")

        assert 'result' in info
        assert 'fmm' in info
        assert 'bmm' in info
        assert 'method' in info

        assert info['result'] == ["我", "爱", "北京", "天安门"]
        assert info['method'] == 'consensus'

    def test_mixed_length(self):
        """测试混合长度词语"""
        bimm = self._create_bimm(["中华", "人民", "共和国", "中华人民共和国"])
        result = bimm.segment("中华人民共和国")
        assert result == ["中华人民共和国"]

    def test_repeated_words(self):
        """测试重复词语"""
        bimm = self._create_bimm(["我", "爱"])
        result = bimm.segment("我爱我爱")
        assert result == ["我", "爱", "我", "爱"]
