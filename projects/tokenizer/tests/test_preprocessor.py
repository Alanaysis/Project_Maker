"""
文本预处理器测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tokenizer import Tokenizer
from src.preprocessor import TextPreprocessor, SearchTokenizer, MachineTranslationTokenizer


class TestTextPreprocessor:
    """文本预处理器测试类"""

    def test_init(self):
        """测试初始化"""
        preprocessor = TextPreprocessor()
        assert preprocessor.tokenizer is None

    def test_preprocess_basic(self):
        """测试基本预处理"""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess("  Hello   World  ")
        assert result == "Hello World"

    def test_preprocess_lowercase(self):
        """测试转小写"""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess("Hello World", {'lowercase': True})
        assert result == "hello world"

    def test_preprocess_remove_punctuation(self):
        """测试移除标点"""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess("Hello, World!", {'remove_punctuation': True})
        assert result == "Hello World"

    def test_preprocess_remove_numbers(self):
        """测试移除数字"""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess("I have 100 apples", {'remove_numbers': True})
        assert "100" not in result

    def test_preprocess_normalize_unicode(self):
        """测试 Unicode 标准化"""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess("Ｈｅｌｌｏ", {'normalize_unicode': True})
        assert result == "Hello"

    def test_tokenize_and_clean(self, tmp_path):
        """测试分词并清洗"""
        # 创建词典
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        preprocessor = TextPreprocessor(tokenizer=tokenizer)
        result = preprocessor.tokenize_and_clean("我爱北京")
        assert "我" in result
        assert "爱" in result
        assert "北京" in result

    def test_tokenize_and_clean_no_tokenizer(self):
        """测试未设置分词器时分词并清洗"""
        preprocessor = TextPreprocessor()
        with pytest.raises(RuntimeError):
            preprocessor.tokenize_and_clean("我爱北京")

    def test_extract_keywords(self, tmp_path):
        """测试提取关键词"""
        # 创建词典
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        preprocessor = TextPreprocessor(tokenizer=tokenizer)
        result = preprocessor.extract_keywords("我爱北京天安门", top_k=3)
        assert len(result) <= 3
        assert all(isinstance(pair, tuple) for pair in result)


class TestSearchTokenizer:
    """搜索引擎分词器测试类"""

    def test_init(self, tmp_path):
        """测试初始化"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        search_tokenizer = SearchTokenizer(tokenizer)
        assert search_tokenizer.tokenizer is not None

    def test_tokenize(self, tmp_path):
        """测试搜索分词"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n天安门 50\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        search_tokenizer = SearchTokenizer(tokenizer)
        result = search_tokenizer.tokenize("我爱北京天安门")
        assert isinstance(result, list)
        assert "北京" in result

    def test_tokenize_empty(self, tmp_path):
        """测试空文本"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        search_tokenizer = SearchTokenizer(tokenizer)
        result = search_tokenizer.tokenize("")
        assert result == []

    def test_tokenize_remove_stopwords(self, tmp_path):
        """测试移除停用词"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("的 300\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        search_tokenizer = SearchTokenizer(tokenizer, remove_stopwords=True)
        result = search_tokenizer.tokenize("北京的天安门")
        assert "的" not in result

    def test_build_index(self, tmp_path):
        """测试构建倒排索引"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("北京 100\n天安门 50\n上海 80\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        search_tokenizer = SearchTokenizer(tokenizer)
        documents = [
            (1, "北京天安门"),
            (2, "上海外滩"),
            (3, "北京故宫")
        ]
        index = search_tokenizer.build_index(documents)
        assert isinstance(index, dict)
        assert "北京" in index

    def test_search(self, tmp_path):
        """测试搜索"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("北京 100\n天安门 50\n上海 80\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        search_tokenizer = SearchTokenizer(tokenizer)
        documents = [
            (1, "北京天安门"),
            (2, "上海外滩"),
            (3, "北京故宫")
        ]
        index = search_tokenizer.build_index(documents)
        results = search_tokenizer.search("北京", index)
        assert len(results) > 0
        # 北京应该出现在文档 1 和 3 中
        doc_ids = [r[0] for r in results]
        assert 1 in doc_ids or 3 in doc_ids


class TestMachineTranslationTokenizer:
    """机器翻译分词器测试类"""

    def test_init(self, tmp_path):
        """测试初始化"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        mt_tokenizer = MachineTranslationTokenizer(tokenizer)
        assert mt_tokenizer.tokenizer is not None

    def test_tokenize_for_translation(self, tmp_path):
        """测试翻译分词"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        mt_tokenizer = MachineTranslationTokenizer(tokenizer)
        result = mt_tokenizer.tokenize_for_translation("我爱北京")
        assert 'tokens' in result
        assert 'pos_tags' in result
        assert 'length' in result

    def test_prepare_parallel_corpus(self, tmp_path):
        """测试准备平行语料"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        mt_tokenizer = MachineTranslationTokenizer(tokenizer)
        source = ["我爱北京", "你好世界"]
        target = ["I love Beijing", "Hello world"]
        result = mt_tokenizer.prepare_parallel_corpus(source, target)
        assert len(result) == 2
        assert all(isinstance(pair, tuple) for pair in result)

    def test_align_tokens(self, tmp_path):
        """测试词对齐"""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("我 200\n爱 150\n北京 100\n", encoding='utf-8')

        tokenizer = Tokenizer()
        tokenizer.load_dictionary(str(dict_file))

        mt_tokenizer = MachineTranslationTokenizer(tokenizer)
        alignments = mt_tokenizer.align_tokens(["我", "爱", "北京"], ["I", "love", "Beijing"])
        assert len(alignments) == 3
        assert all(isinstance(pair, tuple) for pair in alignments)
