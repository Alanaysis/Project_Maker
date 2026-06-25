"""搜索引擎模块 - Search Engine

提供完整的搜索引擎功能，整合索引、查询和排序。
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .index import InvertedIndex, PositionalIndex, CompressedIndex, Document
from .query import Query, QueryParser, QueryExecutor
from .ranking import TFIDFRanker, BM25Ranker, QueryDocumentScorer


@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    title: str
    content: str
    score: float
    snippet: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SearchEngine:
    """搜索引擎

    提供完整的文档检索功能。
    """

    def __init__(self, index_type: str = 'positional'):
        """初始化搜索引擎

        Args:
            index_type: 索引类型 ('basic', 'positional', 'compressed')
        """
        if index_type == 'positional':
            self.index = PositionalIndex()
        elif index_type == 'compressed':
            self.index = CompressedIndex()
        else:
            self.index = InvertedIndex()

        self.query = Query(self.index)
        self.scorer = QueryDocumentScorer(self.index)

    def add_document(self, doc_id: str, title: str, content: str,
                    metadata: Dict = None) -> None:
        """添加文档

        Args:
            doc_id: 文档ID
            title: 文档标题
            content: 文档内容
            metadata: 元数据
        """
        doc = Document(
            doc_id=doc_id,
            title=title,
            content=content,
            metadata=metadata or {}
        )
        self.index.add_document(doc)

    def add_documents(self, documents: List[Dict]) -> None:
        """批量添加文档

        Args:
            documents: 文档字典列表，每个包含 doc_id, title, content
        """
        for doc_data in documents:
            self.add_document(
                doc_id=doc_data['doc_id'],
                title=doc_data.get('title', ''),
                content=doc_data.get('content', ''),
                metadata=doc_data.get('metadata', {})
            )

    def search(self, query_str: str, method: str = 'bm25',
              top_k: int = 10) -> List[SearchResult]:
        """执行搜索

        Args:
            query_str: 查询字符串
            method: 排序方法 ('tfidf' 或 'bm25')
            top_k: 返回前k个结果

        Returns:
            搜索结果列表
        """
        # 执行查询
        doc_ids = self.query.search(query_str)

        if not doc_ids:
            return []

        # 获取查询词汇
        query_terms = self.index._process_text(query_str)

        # 排序
        ranked = self.scorer.rank(query_terms, list(doc_ids), method, top_k)

        # 构建结果
        results = []
        for doc_id, score in ranked:
            doc = self.index.documents[doc_id]
            snippet = self._generate_snippet(doc.content, query_terms)
            results.append(SearchResult(
                doc_id=doc_id,
                title=doc.title,
                content=doc.content,
                score=score,
                snippet=snippet,
                metadata=doc.metadata
            ))

        return results

    def _generate_snippet(self, content: str, query_terms: List[str],
                         max_length: int = 200) -> str:
        """生成摘要片段

        Args:
            content: 文档内容
            query_terms: 查询词汇
            max_length: 最大长度

        Returns:
            摘要片段
        """
        content_lower = content.lower()

        # 查找第一个查询词出现的位置
        best_pos = len(content)
        for term in query_terms:
            pos = content_lower.find(term.lower())
            if 0 <= pos < best_pos:
                best_pos = pos

        if best_pos == len(content):
            return content[:max_length] + "..." if len(content) > max_length else content

        # 提取上下文
        start = max(0, best_pos - 50)
        end = min(len(content), best_pos + max_length - 50)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def get_statistics(self) -> Dict:
        """获取索引统计信息

        Returns:
            统计信息字典
        """
        return {
            'document_count': self.index.doc_count,
            'vocabulary_size': self.index.get_vocabulary_size(),
            'avg_document_length': self.index.avg_doc_length,
            'index_type': type(self.index).__name__
        }

    def save_index(self, filepath: str) -> None:
        """保存索引

        Args:
            filepath: 文件路径
        """
        if isinstance(self.index, CompressedIndex):
            self.index.save_compressed(filepath)
        else:
            self.index.save(filepath)

    def load_index(self, filepath: str) -> None:
        """加载索引

        Args:
            filepath: 文件路径
        """
        if isinstance(self.index, CompressedIndex):
            self.index.load_compressed(filepath)
        else:
            self.index.load(filepath)


class SimpleSearchEngine:
    """简单搜索引擎

    提供简化的API接口，适合快速使用。
    """

    def __init__(self):
        self.engine = SearchEngine('basic')

    def index_documents(self, documents: List[Dict[str, str]]) -> None:
        """索引文档

        Args:
            documents: 文档列表，每个包含 title 和 content
        """
        for i, doc in enumerate(documents):
            self.engine.add_document(
                doc_id=str(i),
                title=doc.get('title', f'Document {i}'),
                content=doc.get('content', '')
            )

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索

        Args:
            query: 查询字符串
            top_k: 返回结果数

        Returns:
            搜索结果列表
        """
        results = self.engine.search(query, top_k=top_k)
        return [
            {
                'title': r.title,
                'content': r.content[:200] + "..." if len(r.content) > 200 else r.content,
                'score': round(r.score, 4)
            }
            for r in results
        ]
