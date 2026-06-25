"""词形还原测试"""

import unittest
from src.lemmatizer import Lemmatizer


class TestLemmatizer(unittest.TestCase):
    """词形还原测试类"""

    def setUp(self):
        self.lemmatizer = Lemmatizer()

    def test_irregular_verbs(self):
        """测试不规则动词"""
        self.assertEqual(self.lemmatizer.lemmatize('is', 'v'), 'be')
        self.assertEqual(self.lemmatizer.lemmatize('was', 'v'), 'be')
        self.assertEqual(self.lemmatizer.lemmatize('has', 'v'), 'have')
        self.assertEqual(self.lemmatizer.lemmatize('did', 'v'), 'do')

    def test_irregular_nouns(self):
        """测试不规则名词"""
        self.assertEqual(self.lemmatizer.lemmatize('men', 'n'), 'man')
        self.assertEqual(self.lemmatizer.lemmatize('children', 'n'), 'child')
        self.assertEqual(self.lemmatizer.lemmatize('teeth', 'n'), 'tooth')

    def test_verb_forms(self):
        """测试动词形式"""
        self.assertEqual(self.lemmatizer.lemmatize('running', 'v'), 'run')
        self.assertEqual(self.lemmatizer.lemmatize('walking', 'v'), 'walk')
        self.assertEqual(self.lemmatizer.lemmatize('played', 'v'), 'play')

    def test_noun_plurals(self):
        """测试名词复数"""
        self.assertEqual(self.lemmatizer.lemmatize('cats', 'n'), 'cat')
        self.assertEqual(self.lemmatizer.lemmatize('buses', 'n'), 'bus')
        self.assertEqual(self.lemmatizer.lemmatize('stories', 'n'), 'story')

    def test_adjective_forms(self):
        """测试形容词形式"""
        self.assertEqual(self.lemmatizer.lemmatize('better', 'a'), 'good')
        self.assertEqual(self.lemmatizer.lemmatize('worse', 'a'), 'bad')

    def test_comparative_forms(self):
        """测试比较级"""
        self.assertEqual(self.lemmatizer.lemmatize('better'), 'good')
        self.assertEqual(self.lemmatizer.lemmatize('best'), 'good')

    def test_batch_lemmatization(self):
        """测试批量词形还原"""
        words = ['running', 'cats', 'better']
        lemmas = self.lemmatizer.lemmatize_tokens(words)
        self.assertEqual(len(lemmas), 3)


if __name__ == '__main__':
    unittest.main()
