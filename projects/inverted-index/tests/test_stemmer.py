"""词干提取测试"""

import unittest
from src.stemmer import PorterStemmer


class TestPorterStemmer(unittest.TestCase):
    """词干提取测试类"""

    def setUp(self):
        self.stemmer = PorterStemmer()

    def test_basic_stemming(self):
        """测试基本词干提取"""
        self.assertEqual(self.stemmer.stem('running'), 'run')
        self.assertEqual(self.stemmer.stem('cats'), 'cat')
        self.assertEqual(self.stemmer.stem('dogs'), 'dog')

    def test_past_tense(self):
        """测试过去式"""
        self.assertEqual(self.stemmer.stem('walked'), 'walk')
        self.assertEqual(self.stemmer.stem('played'), 'play')

    def test_ing_suffix(self):
        """测试-ing后缀"""
        self.assertEqual(self.stemmer.stem('running'), 'run')
        self.assertEqual(self.stemmer.stem('walking'), 'walk')

    def test_tion_suffix(self):
        """测试-tion后缀"""
        result = self.stemmer.stem('national')
        self.assertTrue(result.endswith('tion') or result.endswith('ate'))

    def test_ful_suffix(self):
        """测试-ful后缀"""
        result = self.stemmer.stem('beautiful')
        self.assertTrue(result.endswith('beauti'))

    def test_short_words(self):
        """测试短词不处理"""
        self.assertEqual(self.stemmer.stem('is'), 'is')
        self.assertEqual(self.stemmer.stem('at'), 'at')

    def test_batch_stemming(self):
        """测试批量词干提取"""
        words = ['running', 'cats', 'walking']
        stems = self.stemmer.stem_tokens(words)
        self.assertEqual(len(stems), 3)
        self.assertEqual(stems[0], 'run')


if __name__ == '__main__':
    unittest.main()
