"""
词典管理模块测试
"""

import pytest
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dictionary import Dictionary


class TestDictionary:
    """词典测试类"""

    def test_init(self):
        """测试初始化"""
        dict = Dictionary()
        assert dict.size() == 0
        assert dict.get_max_word_length() == 0

    def test_add(self):
        """测试添加词条"""
        dict = Dictionary()
        dict.add("北京", 100)
        assert dict.contains("北京")
        assert dict.get_frequency("北京") == 100
        assert dict.size() == 1

    def test_add_multiple(self):
        """测试添加多个词条"""
        dict = Dictionary()
        dict.add("我", 200)
        dict.add("北京", 100)
        dict.add("天安门", 50)
        assert dict.size() == 3
        assert dict.get_max_word_length() == 3

    def test_remove(self):
        """测试删除词条"""
        dict = Dictionary()
        dict.add("北京", 100)
        dict.remove("北京")
        assert not dict.contains("北京")
        assert dict.size() == 0

    def test_remove_nonexistent(self):
        """测试删除不存在的词条"""
        dict = Dictionary()
        with pytest.raises(KeyError):
            dict.remove("北京")

    def test_contains(self):
        """测试查询词条"""
        dict = Dictionary()
        dict.add("北京", 100)
        assert dict.contains("北京") is True
        assert dict.contains("上海") is False

    def test_get_frequency(self):
        """测试获取词频"""
        dict = Dictionary()
        dict.add("北京", 100)
        assert dict.get_frequency("北京") == 100

    def test_get_frequency_nonexistent(self):
        """测试获取不存在词的频率"""
        dict = Dictionary()
        with pytest.raises(KeyError):
            dict.get_frequency("北京")

    def test_get_max_word_length(self):
        """测试获取最大词长"""
        dict = Dictionary()
        dict.add("我", 200)
        dict.add("北京", 100)
        dict.add("天安门", 50)
        assert dict.get_max_word_length() == 3

    def test_get_words(self):
        """测试获取所有词语"""
        dict = Dictionary()
        dict.add("我", 200)
        dict.add("北京", 100)
        words = dict.get_words()
        assert "我" in words
        assert "北京" in words
        assert len(words) == 2

    def test_size(self):
        """测试词典大小"""
        dict = Dictionary()
        assert dict.size() == 0
        dict.add("我", 200)
        assert dict.size() == 1

    def test_load(self, tmp_path):
        """测试加载词典文件"""
        # 创建临时词典文件
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("北京 100\n天安门 50\n", encoding='utf-8')

        dict = Dictionary()
        dict.load(str(dict_file))

        assert dict.size() == 2
        assert dict.contains("北京")
        assert dict.contains("天安门")

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        dict = Dictionary()
        with pytest.raises(FileNotFoundError):
            dict.load("nonexistent.txt")
