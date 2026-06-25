"""排序模块 - Ranking

实现 TF-IDF 和 BM25 相关性排序算法。
"""

import math
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from .index import InvertedIndex


class Ranker(ABC):
    """排序器基类"""

    def __init__(self, index: InvertedIndex):
        self.index = index

    def _process_query_terms(self, query_terms: List[str]) -> List[str]:
        """处理查询词汇（与索引构建时相同的处理流程）"""
        return self.index._process_text(' '.join(query_terms))

    @abstractmethod
    def score(self, query_terms: List[str], doc_id: str) -> float:
        """计算文档得分

        Args:
            query_terms: 查询词汇列表（原始词汇，会自动处理）
            doc_id: 文档ID

        Returns:
            相关性得分
        """
        pass

    def rank(self, query_terms: List[str], doc_ids: Optional[List[str]] = None,
             top_k: int = 10) -> List[tuple]:
        """对文档排序

        Args:
            query_terms: 查询词汇列表
            doc_ids: 候选文档ID列表，None表示所有文档
            top_k: 返回前k个结果

        Returns:
            (doc_id, score)列表
        """
        if doc_ids is None:
            doc_ids = list(self.index.documents.keys())

        scores = []
        for doc_id in doc_ids:
            score = self.score(query_terms, doc_id)
            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class TFIDFRanker(Ranker):
    """TF-IDF 排序器

    TF(t,d) = 词t在文档d中出现的次数 / 文档d的总词数
    IDF(t) = log(N / df(t))
    Score = TF * IDF
    """

    def score(self, query_terms: List[str], doc_id: str) -> float:
        """计算TF-IDF得分

        Args:
            query_terms: 查询词汇列表（原始词汇，会自动处理）
            doc_id: 文档ID

        Returns:
            TF-IDF得分
        """
        # 处理查询词汇（与索引构建时相同的处理流程）
        processed_terms = self._process_query_terms(query_terms)

        total_score = 0.0
        for term in processed_terms:
            tf = self._compute_tf(term, doc_id)
            idf = self._compute_idf(term)
            total_score += tf * idf

        return total_score

    def _compute_tf(self, term: str, doc_id: str) -> float:
        """计算词频

        Args:
            term: 词汇
            doc_id: 文档ID

        Returns:
            词频
        """
        postings = self.index.get_postings(term)
        for posting in postings:
            if posting.doc_id == doc_id:
                doc_length = self.index.doc_lengths.get(doc_id, 1)
                return posting.term_frequency / doc_length
        return 0.0

    def _compute_idf(self, term: str) -> float:
        """计算逆文档频率

        Args:
            term: 词汇（原始词汇，会自动处理）

        Returns:
            逆文档频率
        """
        # 处理词汇（与索引构建时相同的处理流程）
        processed_terms = self.index._process_text(term)
        if not processed_terms:
            return 0.0

        df = self.index.get_document_frequency(processed_terms[0])
        if df == 0:
            return 0.0
        n = self.index.doc_count
        return math.log(n / df)


class BM25Ranker(Ranker):
    """BM25 排序器

    BM25 是 TF-IDF 的改进版本，考虑了文档长度和词频饱和度。

    Score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1+1)) / (f(qi,D) + k1*(1-b+b*|D|/avgdl))

    参数:
        k1: 词频饱和参数 (默认 1.2)
        b: 文档长度归一化参数 (默认 0.75)
    """

    def __init__(self, index: InvertedIndex, k1: float = 1.2, b: float = 0.75):
        super().__init__(index)
        self.k1 = k1
        self.b = b

    def score(self, query_terms: List[str], doc_id: str) -> float:
        """计算BM25得分

        Args:
            query_terms: 查询词汇列表（原始词汇，会自动处理）
            doc_id: 文档ID

        Returns:
            BM25得分
        """
        # 处理查询词汇（与索引构建时相同的处理流程）
        processed_terms = self._process_query_terms(query_terms)

        total_score = 0.0
        for term in processed_terms:
            tf = self._get_term_frequency(term, doc_id)
            idf = self._compute_idf(term)
            doc_length = self.index.doc_lengths.get(doc_id, 0)
            avg_dl = self.index.avg_doc_length

            # BM25公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / avg_dl)

            total_score += idf * (numerator / denominator)

        return total_score

    def _get_term_frequency(self, term: str, doc_id: str) -> int:
        """获取词频

        Args:
            term: 词汇
            doc_id: 文档ID

        Returns:
            词频
        """
        postings = self.index.get_postings(term)
        for posting in postings:
            if posting.doc_id == doc_id:
                return posting.term_frequency
        return 0

    def _compute_idf(self, term: str) -> float:
        """计算逆文档频率

        使用BM25的IDF公式:
        IDF(t) = log((N - n(t) + 0.5) / (n(t) + 0.5) + 1)

        Args:
            term: 词汇（原始词汇，会自动处理）

        Returns:
            逆文档频率
        """
        # 处理词汇（与索引构建时相同的处理流程）
        processed_terms = self.index._process_text(term)
        if not processed_terms:
            return 0.0

        n = self.index.doc_count
        df = self.index.get_document_frequency(processed_terms[0])

        # BM25 IDF公式（带平滑）
        return math.log((n - df + 0.5) / (df + 0.5) + 1)


class QueryDocumentScorer:
    """查询-文档评分器

    综合评分器，支持多种排序方法。
    """

    def __init__(self, index: InvertedIndex):
        self.index = index
        self.rankers = {
            'tfidf': TFIDFRanker(index),
            'bm25': BM25Ranker(index),
        }

    def score(self, query_terms: List[str], doc_id: str,
              method: str = 'bm25') -> float:
        """计算文档得分

        Args:
            query_terms: 查询词汇列表
            doc_id: 文档ID
            method: 排序方法

        Returns:
            得分
        """
        ranker = self.rankers.get(method)
        if ranker is None:
            raise ValueError(f"Unknown ranking method: {method}")
        return ranker.score(query_terms, doc_id)

    def rank(self, query_terms: List[str], doc_ids: Optional[List[str]] = None,
             method: str = 'bm25', top_k: int = 10) -> List[tuple]:
        """对文档排序

        Args:
            query_terms: 查询词汇列表
            doc_ids: 候选文档ID列表
            method: 排序方法
            top_k: 返回前k个结果

        Returns:
            (doc_id, score)列表
        """
        ranker = self.rankers.get(method)
        if ranker is None:
            raise ValueError(f"Unknown ranking method: {method}")
        return ranker.rank(query_terms, doc_ids, top_k)
