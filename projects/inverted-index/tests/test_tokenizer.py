"""分词器测试"""

import unittest
from src.tokenizer import Tokenizer


class TestTokenizer(unittest.TestCase):
    """分词器测试类"""

    def setUp(self):
        self.tokenizer = Tokenizer()

    def test_basic_tokenization(self):
        """测试基本分词"""
        text = "Hello World"
        tokens = self.tokenizer.tokenize(text)
        self.assertEqual(tokens, ['hello', 'world'])

    def test_chinese_tokenization(self):
        """测试中文分词"""
        text = "搜索引擎"
        tokens = self.tokenizer.tokenize(text)
        self.assertEqual(tokens, ['搜', '索', '引', '擎'])

    def test_mixed_tokenization(self):
        """测试中英文混合分词"""
        text = "Python编程"
        tokens = self.tokenizer.tokenize(text)
        self.assertEqual(tokens, ['python', '编', '程'])

    def test_punctuation_removal(self):
        """测试标点移除"""
        text = "Hello, World!"
        tokens = self.tokenizer.tokenize(text)
        self.assertEqual(tokens, ['hello', 'world'])

    def test_empty_text(self):
        """测试空文本"""
        tokens = self.tokenizer.tokenize("")
        self.assertEqual(tokens, [])

    def test_tokenize_with_positions(self):
        """测试带位置分词"""
        text = "Hello World"
        result = self.tokenizer.tokenize_with_positions(text)
        self.assertEqual(result, [('hello', 0), ('world', 1)])

    def test_number_handling(self):
        """测试数字处理"""
        text = "Version 2.0"
        tokens = self.tokenizer.tokenize(text)
        self.assertIn('2', tokens)
        self.assertIn('0', tokens)


if __name__ == '__main__':
    unittest.main()
