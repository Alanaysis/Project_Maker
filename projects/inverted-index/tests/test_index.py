"""索引测试"""

import unittest
from src.index import InvertedIndex, PositionalIndex, CompressedIndex, Document


class TestInvertedIndex(unittest.TestCase):
    """倒排索引测试类"""

    def setUp(self):
        self.index = InvertedIndex()
        self.doc1 = Document(
            doc_id="1",
            title="Python Programming",
            content="Python is a popular programming language"
        )
        self.doc2 = Document(
            doc_id="2",
            title="Java Programming",
            content="Java is also a programming language"
        )
        self.doc3 = Document(
            doc_id="3",
            title="Python Data Science",
            content="Python is used for data science and machine learning"
        )

    def test_add_document(self):
        """测试添加文档"""
        self.index.add_document(self.doc1)
        self.assertEqual(self.index.doc_count, 1)
        self.assertIn("1", self.index.documents)

    def test_remove_document(self):
        """测试移除文档"""
        self.index.add_document(self.doc1)
        self.index.remove_document("1")
        self.assertEqual(self.index.doc_count, 0)
        self.assertNotIn("1", self.index.documents)

    def test_get_postings(self):
        """测试获取倒排列表"""
        self.index.add_document(self.doc1)
        self.index.add_document(self.doc2)

        postings = self.index.get_postings("python")
        self.assertEqual(len(postings), 1)
        self.assertEqual(postings[0].doc_id, "1")

    def test_get_document_frequency(self):
        """测试文档频率"""
        self.index.add_document(self.doc1)
        self.index.add_document(self.doc2)

        df = self.index.get_document_frequency("programming")
        self.assertEqual(df, 2)

    def test_vocabulary_size(self):
        """测试词汇表大小"""
        self.index.add_document(self.doc1)
        self.index.add_document(self.doc2)

        vocab_size = self.index.get_vocabulary_size()
        self.assertGreater(vocab_size, 0)

    def test_save_load(self):
        """测试保存和加载"""
        self.index.add_document(self.doc1)
        self.index.add_document(self.doc2)

        filepath = "/tmp/test_index.json"
        self.index.save(filepath)

        new_index = InvertedIndex()
        new_index.load(filepath)

        self.assertEqual(new_index.doc_count, 2)
        self.assertIn("1", new_index.documents)


class TestPositionalIndex(unittest.TestCase):
    """位置索引测试类"""

    def setUp(self):
        self.index = PositionalIndex()
        self.index.add_document(Document(
            doc_id="1",
            title="Test Document",
            content="the quick brown fox jumps over the lazy dog"
        ))

    def test_phrase_query(self):
        """测试短语查询"""
        results = self.index.search_phrase("quick brown")
        self.assertIn("1", results)

    def test_phrase_query_no_match(self):
        """测试短语查询无匹配"""
        results = self.index.search_phrase("brown quick")
        self.assertNotIn("1", results)

    def test_positions_recorded(self):
        """测试位置记录"""
        postings = self.index.get_postings("quick")
        self.assertTrue(len(postings) > 0)
        self.assertTrue(len(postings[0].positions) > 0)


class TestCompressedIndex(unittest.TestCase):
    """压缩索引测试类"""

    def setUp(self):
        self.index = CompressedIndex()
        self.index.add_document(Document(
            doc_id="1",
            title="Test",
            content="hello world"
        ))

    def test_compress_decompress(self):
        """测试压缩和解压"""
        self.index.compress()
        self.assertGreater(len(self.index.compressed_data), 0)

        postings = self.index.decompress("hello")
        self.assertEqual(len(postings), 1)

    def test_compression_ratio(self):
        """测试压缩比"""
        self.index.compress()
        ratio = self.index.get_compression_ratio()
        self.assertGreater(ratio, 0)
        self.assertLessEqual(ratio, 1.0)


if __name__ == '__main__':
    unittest.main()
