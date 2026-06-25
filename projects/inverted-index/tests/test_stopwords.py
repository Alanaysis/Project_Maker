"""停用词过滤测试"""

import unittest
from src.stopwords import StopWordsFilter


class TestStopWordsFilter(unittest.TestCase):
    """停用词过滤测试类"""

    def setUp(self):
        self.filter = StopWordsFilter()

    def test_english_stop_words(self):
        """测试英文停用词过滤"""
        tokens = ['the', 'quick', 'brown', 'fox', 'is', 'running']
        filtered = self.filter.filter(tokens)
        self.assertNotIn('the', filtered)
        self.assertNotIn('is', filtered)
        self.assertIn('quick', filtered)
        self.assertIn('brown', filtered)

    def test_chinese_stop_words(self):
        """测试中文停用词过滤"""
        tokens = ['的', '是', '搜索', '引擎']
        filtered = self.filter.filter(tokens)
        self.assertNotIn('的', filtered)
        self.assertNotIn('是', filtered)
        self.assertIn('搜索', filtered)

    def test_is_stop_word(self):
        """测试停用词判断"""
        self.assertTrue(self.filter.is_stop_word('the'))
        self.assertTrue(self.filter.is_stop_word('的'))
        self.assertFalse(self.filter.is_stop_word('search'))

    def test_custom_stop_words(self):
        """测试自定义停用词"""
        custom = {'foo', 'bar'}
        f = StopWordsFilter(custom_stop_words=custom)
        self.assertTrue(f.is_stop_word('foo'))
        self.assertTrue(f.is_stop_word('bar'))

    def test_add_stop_words(self):
        """测试添加停用词"""
        self.filter.add_stop_words({'custom', 'words'})
        self.assertTrue(self.filter.is_stop_word('custom'))

    def test_remove_stop_words(self):
        """测试移除停用词"""
        self.filter.remove_stop_words({'the', 'is'})
        self.assertFalse(self.filter.is_stop_word('the'))


if __name__ == '__main__':
    unittest.main()
