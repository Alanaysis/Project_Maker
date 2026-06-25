"""查询处理测试"""

import unittest
from src.index import InvertedIndex, PositionalIndex, Document
from src.query import Query, QueryParser, QueryType


class TestQueryParser(unittest.TestCase):
    """查询解析器测试类"""

    def setUp(self):
        self.parser = QueryParser()

    def test_term_query(self):
        """测试单词查询"""
        query = self.parser.parse("python")
        self.assertEqual(query.query_type, QueryType.TERM)
        self.assertEqual(query.value, "python")

    def test_and_query(self):
        """测试AND查询"""
        query = self.parser.parse("python AND programming")
        self.assertEqual(query.query_type, QueryType.AND)
        self.assertEqual(len(query.children), 2)

    def test_or_query(self):
        """测试OR查询"""
        query = self.parser.parse("python OR java")
        self.assertEqual(query.query_type, QueryType.OR)
        self.assertEqual(len(query.children), 2)

    def test_not_query(self):
        """测试NOT查询"""
        query = self.parser.parse("NOT java")
        self.assertEqual(query.query_type, QueryType.NOT)
        self.assertEqual(len(query.children), 1)

    def test_phrase_query(self):
        """测试短语查询"""
        query = self.parser.parse('"machine learning"')
        self.assertEqual(query.query_type, QueryType.PHRASE)
        self.assertEqual(query.value, "machine learning")

    def test_wildcard_query(self):
        """测试通配符查询"""
        query = self.parser.parse("py*")
        self.assertEqual(query.query_type, QueryType.WILDCARD)
        self.assertEqual(query.value, "py*")

    def test_fuzzy_query(self):
        """测试模糊查询"""
        query = self.parser.parse("pythn~")
        self.assertEqual(query.query_type, QueryType.FUZZY)
        self.assertEqual(query.value, "pythn")

    def test_multi_term_and(self):
        """测试多词默认AND"""
        query = self.parser.parse("python programming language")
        self.assertEqual(query.query_type, QueryType.AND)
        self.assertEqual(len(query.children), 3)


class TestQueryExecutor(unittest.TestCase):
    """查询执行器测试类"""

    def setUp(self):
        self.index = InvertedIndex()
        self.index.add_document(Document(
            doc_id="1",
            title="Python Programming",
            content="Python is a popular programming language for data science"
        ))
        self.index.add_document(Document(
            doc_id="2",
            title="Java Programming",
            content="Java is a programming language for enterprise applications"
        ))
        self.index.add_document(Document(
            doc_id="3",
            title="Data Science",
            content="Data science uses Python and R for analysis"
        ))
        self.query = Query(self.index)

    def test_term_search(self):
        """测试单词搜索"""
        results = self.query.search("python")
        self.assertIn("1", results)
        self.assertIn("3", results)
        self.assertNotIn("2", results)

    def test_and_search(self):
        """测试AND搜索"""
        results = self.query.search("python AND science")
        self.assertIn("1", results)
        self.assertIn("3", results)

    def test_or_search(self):
        """测试OR搜索"""
        results = self.query.search("python OR java")
        self.assertEqual(len(results), 3)

    def test_not_search(self):
        """测试NOT搜索"""
        results = self.query.search("python NOT java")
        self.assertIn("1", results)
        self.assertIn("3", results)
        self.assertNotIn("2", results)

    def test_wildcard_search(self):
        """测试通配符搜索"""
        results = self.query.search("prog*")
        self.assertIn("1", results)
        self.assertIn("2", results)

    def test_fuzzy_search(self):
        """测试模糊搜索"""
        results = self.query.search("pythn~")
        self.assertIn("1", results)

    def test_phrase_search(self):
        """测试短语查询（位置索引）"""
        positional_index = PositionalIndex()
        positional_index.add_document(Document(
            doc_id="1",
            title="Test",
            content="the quick brown fox"
        ))
        positional_index.add_document(Document(
            doc_id="2",
            title="Test2",
            content="the brown quick fox"
        ))
        query = Query(positional_index)
        results = query.search('"quick brown"')
        self.assertIn("1", results)
        self.assertNotIn("2", results)


if __name__ == '__main__':
    unittest.main()
