"""
主分词器测试
"""

import pytest
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tokenizer import Tokenizer


class TestTokenizer:
    """主分词器测试类"""

    def _create_tokenizer(self, dict_path):
        """创建分词器"""
        tokenizer = Tokenizer()
        tokenizer.load_dictionary(dict_path)
        return tokenizer

    def test_load_dictionary(self, tmp_path):
        """测试加载词典"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        assert tokenizer.dictionary.size() == 2

    def test_load_nonexistent_dictionary(self):
        """测试加载不存在的词典"""
        tokenizer = Tokenizer()
        with pytest.raises(FileNotFoundError):
            tokenizer.load_dictionary("nonexistent.txt")

    def test_fmm(self, tmp_path):
        """测试正向最大匹配"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = self._create_tokenizer(str(dict_file))
        result = tokenizer.fmm("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_bmm(self, tmp_path):
        """测试逆向最大匹配"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = self._create_tokenizer(str(dict_file))
        result = tokenizer.bmm("我爱北京天安门")
        assert result == ["我", "爱", "北京", "天安门"]

    def test_hmm(self):
        """测试 HMM 分词"""
        tokenizer = Tokenizer()
        corpus = [
            "我/S 爱/S 北京/B 天安门/E"
        ]
        tokenizer.train_hmm(corpus)

        result = tokenizer.hmm("我爱北京天安门")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_segment_fmm(self, tmp_path):
        """测试统一分词接口 - FMM"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = self._create_tokenizer(str(dict_file))
        result = tokenizer.segment("我爱北京天安门", method='fmm')
        assert result == ["我", "爱", "北京", "天安门"]

    def test_segment_bmm(self, tmp_path):
        """测试统一分词接口 - BMM"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = self._create_tokenizer(str(dict_file))
        result = tokenizer.segment("我爱北京天安门", method='bmm')
        assert result == ["我", "爱", "北京", "天安门"]

    def test_segment_hmm(self):
        """测试统一分词接口 - HMM"""
        tokenizer = Tokenizer()
        corpus = [
            "我/S 爱/S 北京/B 天安门/E"
        ]
        tokenizer.train_hmm(corpus)

        result = tokenizer.segment("我爱北京天安门", method='hmm')
        assert isinstance(result, list)

    def test_segment_invalid_method(self, tmp_path):
        """测试无效分词方法"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("北京 100\n", encoding='utf-8')

        tokenizer = self._create_tokenizer(str(dict_file))
        with pytest.raises(ValueError):
            tokenizer.segment("北京", method='invalid')

    def test_fmm_without_dictionary(self):
        """测试未加载词典时使用 FMM"""
        tokenizer = Tokenizer()
        with pytest.raises(RuntimeError):
            tokenizer.fmm("北京")

    def test_bmm_without_dictionary(self):
        """测试未加载词典时使用 BMM"""
        tokenizer = Tokenizer()
        with pytest.raises(RuntimeError):
            tokenizer.bmm("北京")

    def test_integration(self, tmp_path):
        """集成测试"""
        # 创建词典
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n中华人民共和国 80\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        # 测试 FMM
        fmm_result = tokenizer.fmm("我爱北京天安门")
        assert fmm_result == ["我", "爱", "北京", "天安门"]

        # 测试 BMM
        bmm_result = tokenizer.bmm("我爱北京天安门")
        assert bmm_result == ["我", "爱", "北京", "天安门"]

        # 测试长文本
        long_text = "中华人民共和国我爱北京天安门"
        fmm_long = tokenizer.fmm(long_text)
        bmm_long = tokenizer.bmm(long_text)
        assert isinstance(fmm_long, list)
        assert isinstance(bmm_long, list)
