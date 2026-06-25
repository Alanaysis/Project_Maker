"""排序测试"""

import unittest
from src.index import InvertedIndex, Document
from src.ranking import TFIDFRanker, BM25Ranker, QueryDocumentScorer


class TestTFIDFRanker(unittest.TestCase):
    """TF-IDF排序器测试类"""

    def setUp(self):
        self.index = InvertedIndex()
        self.index.add_document(Document(
            doc_id="1",
            title="Python Programming",
            content="Python is a programming language for data science"
        ))
        self.index.add_document(Document(
            doc_id="2",
            title="Java Programming",
            content="Java is also a programming language"
        ))
        self.ranker = TFIDFRanker(self.index)

    def test_tf_idf_score(self):
        """测试TF-IDF得分"""
        query_terms = ["python"]
        score = self.ranker.score(query_terms, "1")
        self.assertGreater(score, 0)

    def test_idf_value(self):
        """测试IDF值"""
        # "programming" 出现在2个文档中，IDF应该较低
        idf_programming = self.ranker._compute_idf("programming")

        # "python" 只出现在1个文档中，IDF应该较高
        idf_python = self.ranker._compute_idf("python")
        self.assertGreater(idf_python, idf_programming)

    def test_ranking(self):
        """测试排序"""
        query_terms = ["python"]
        ranked = self.ranker.rank(query_terms, top_k=2)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0][0], "1")  # doc 1 should rank higher

    def test_no_match_score(self):
        """测试无匹配得分"""
        query_terms = ["javascript"]
        score = self.ranker.score(query_terms, "1")
        self.assertEqual(score, 0)


class TestBM25Ranker(unittest.TestCase):
    """BM25排序器测试类"""

    def setUp(self):
        self.index = InvertedIndex()
        self.index.add_document(Document(
            doc_id="1",
            title="Python Programming",
            content="Python is a programming language for data science"
        ))
        self.index.add_document(Document(
            doc_id="2",
            title="Java Programming",
            content="Java is also a programming language"
        ))
        self.ranker = BM25Ranker(self.index)

    def test_bm25_score(self):
        """测试BM25得分"""
        query_terms = ["python"]
        score = self.ranker.score(query_terms, "1")
        self.assertGreater(score, 0)

    def test_bm25_idf(self):
        """测试BM25 IDF公式"""
        idf = self.ranker._compute_idf("python")
        self.assertGreater(idf, 0)

    def test_bm25_ranking(self):
        """测试BM25排序"""
        query_terms = ["programming", "python"]
        ranked = self.ranker.rank(query_terms, top_k=2)
        self.assertEqual(len(ranked), 2)

    def test_parameter_customization(self):
        """测试参数自定义"""
        ranker = BM25Ranker(self.index, k1=2.0, b=0.5)
        self.assertEqual(ranker.k1, 2.0)
        self.assertEqual(ranker.b, 0.5)


class TestQueryDocumentScorer(unittest.TestCase):
    """查询文档评分器测试类"""

    def setUp(self):
        self.index = InvertedIndex()
        self.index.add_document(Document(
            doc_id="1",
            title="Python Programming",
            content="Python is a popular language"
        ))
        self.index.add_document(Document(
            doc_id="2",
            title="Java Programming",
            content="Java is also popular"
        ))
        self.scorer = QueryDocumentScorer(self.index)

    def test_tfidf_method(self):
        """测试TF-IDF方法"""
        score = self.scorer.score(["python"], "1", method="tfidf")
        self.assertGreater(score, 0)

    def test_bm25_method(self):
        """测试BM25方法"""
        score = self.scorer.score(["python"], "1", method="bm25")
        self.assertGreater(score, 0)

    def test_invalid_method(self):
        """测试无效方法"""
        with self.assertRaises(ValueError):
            self.scorer.score(["python"], "1", method="invalid")

    def test_rank_with_method(self):
        """测试排序方法选择"""
        ranked = self.scorer.rank(["python"], method="bm25")
        self.assertGreater(len(ranked), 0)


if __name__ == '__main__':
    unittest.main()
