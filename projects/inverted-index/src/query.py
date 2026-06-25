"""查询处理模块 - Query Processing

实现布尔查询、短语查询、通配符查询和模糊查询。
"""

import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Set, Optional
from dataclasses import dataclass

from .index import InvertedIndex, PositionalIndex


class QueryType(Enum):
    """查询类型"""
    TERM = "term"
    AND = "and"
    OR = "or"
    NOT = "not"
    PHRASE = "phrase"
    WILDCARD = "wildcard"
    FUZZY = "fuzzy"


@dataclass
class QueryNode:
    """查询树节点"""
    query_type: QueryType
    value: Optional[str] = None
    children: Optional[List['QueryNode']] = None

    def __repr__(self):
        if self.children:
            return f"{self.query_type.value}({', '.join(str(c) for c in self.children)})"
        return f"{self.query_type.value}({self.value})"


class QueryParser:
    """查询解析器

    将查询字符串解析为查询树。
    """

    def parse(self, query_str: str) -> QueryNode:
        """解析查询字符串

        Args:
            query_str: 查询字符串

        Returns:
            查询树根节点
        """
        query_str = query_str.strip()

        # 短语查询 "..."
        if query_str.startswith('"') and query_str.endswith('"'):
            return QueryNode(QueryType.PHRASE, value=query_str[1:-1])

        # 通配符查询
        if '*' in query_str or '?' in query_str:
            return QueryNode(QueryType.WILDCARD, value=query_str)

        # 模糊查询 ~
        if query_str.endswith('~'):
            return QueryNode(QueryType.FUZZY, value=query_str[:-1])

        # 布尔查询
        if ' OR ' in query_str:
            parts = query_str.split(' OR ')
            return QueryNode(
                QueryType.OR,
                children=[self.parse(part.strip()) for part in parts]
            )

        if ' AND ' in query_str:
            parts = query_str.split(' AND ')
            return QueryNode(
                QueryType.AND,
                children=[self.parse(part.strip()) for part in parts]
            )

        # 处理NOT查询（支持 NOT 在开头或中间）
        if ' NOT ' in query_str:
            parts = query_str.split(' NOT ', 1)
            positive = self.parse(parts[0].strip())
            negative = self.parse(parts[1].strip())
            return QueryNode(
                QueryType.AND,
                children=[positive, QueryNode(QueryType.NOT, children=[negative])]
            )

        if query_str.startswith('NOT '):
            return QueryNode(
                QueryType.NOT,
                children=[self.parse(query_str[4:])]
            )

        # 多词默认AND查询
        terms = query_str.split()
        if len(terms) > 1:
            return QueryNode(
                QueryType.AND,
                children=[QueryNode(QueryType.TERM, value=term) for term in terms]
            )

        return QueryNode(QueryType.TERM, value=query_str)


class QueryExecutor:
    """查询执行器

    执行查询树并返回结果。
    """

    def __init__(self, index: InvertedIndex):
        self.index = index

    def execute(self, query: QueryNode) -> Set[str]:
        """执行查询

        Args:
            query: 查询树

        Returns:
            匹配的文档ID集合
        """
        if query.query_type == QueryType.TERM:
            return self._execute_term(query.value)
        elif query.query_type == QueryType.AND:
            return self._execute_and(query.children)
        elif query.query_type == QueryType.OR:
            return self._execute_or(query.children)
        elif query.query_type == QueryType.NOT:
            return self._execute_not(query.children)
        elif query.query_type == QueryType.PHRASE:
            return self._execute_phrase(query.value)
        elif query.query_type == QueryType.WILDCARD:
            return self._execute_wildcard(query.value)
        elif query.query_type == QueryType.FUZZY:
            return self._execute_fuzzy(query.value)
        return set()

    def _execute_term(self, term: str) -> Set[str]:
        """执行单词汇查询"""
        postings = self.index.get_postings(term)
        return {p.doc_id for p in postings}

    def _execute_and(self, children: List[QueryNode]) -> Set[str]:
        """执行AND查询"""
        if not children:
            return set()

        result = self.execute(children[0])
        for child in children[1:]:
            result &= self.execute(child)
        return result

    def _execute_or(self, children: List[QueryNode]) -> Set[str]:
        """执行OR查询"""
        result = set()
        for child in children:
            result |= self.execute(child)
        return result

    def _execute_not(self, children: List[QueryNode]) -> Set[str]:
        """执行NOT查询"""
        if not children:
            return set()

        all_docs = set(self.index.documents.keys())
        exclude = self.execute(children[0])
        return all_docs - exclude

    def _execute_phrase(self, phrase: str) -> Set[str]:
        """执行短语查询"""
        if isinstance(self.index, PositionalIndex):
            return set(self.index.search_phrase(phrase))

        # 降级处理：AND查询
        terms = phrase.split()
        return self._execute_and([
            QueryNode(QueryType.TERM, value=term) for term in terms
        ])

    def _execute_wildcard(self, pattern: str) -> Set[str]:
        """执行通配符查询

        支持 * (任意字符) 和 ? (单个字符)
        """
        import fnmatch

        result = set()
        regex_pattern = fnmatch.translate(pattern)

        for term in self.index.index.keys():
            if re.match(regex_pattern, term):
                postings = self.index.get_postings(term)
                result.update(p.doc_id for p in postings)

        return result

    def _execute_fuzzy(self, term: str) -> Set[str]:
        """执行模糊查询

        使用编辑距离查找相似词汇
        """
        result = set()
        max_distance = 1 if len(term) <= 4 else 2

        for index_term in self.index.index.keys():
            if self._edit_distance(term, index_term) <= max_distance:
                postings = self.index.get_postings(index_term)
                result.update(p.doc_id for p in postings)

        return result

    def _edit_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离

        Args:
            s1: 字符串1
            s2: 字符串2

        Returns:
            编辑距离
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

        return dp[m][n]


class Query:
    """查询接口

    提供简洁的查询API。
    """

    def __init__(self, index: InvertedIndex):
        self.parser = QueryParser()
        self.executor = QueryExecutor(index)
        self.index = index

    def search(self, query_str: str) -> Set[str]:
        """执行查询

        Args:
            query_str: 查询字符串

        Returns:
            匹配的文档ID集合
        """
        query_tree = self.parser.parse(query_str)
        return self.executor.execute(query_tree)

    def search_with_ranking(self, query_str: str, method: str = 'bm25',
                           top_k: int = 10) -> List[tuple]:
        """带排序的查询

        Args:
            query_str: 查询字符串
            method: 排序方法 ('tfidf' 或 'bm25')
            top_k: 返回前k个结果

        Returns:
            (doc_id, score)列表
        """
        from .ranking import TFIDFRanker, BM25Ranker

        doc_ids = self.search(query_str)

        if method == 'bm25':
            ranker = BM25Ranker(self.index)
        else:
            ranker = TFIDFRanker(self.index)

        query_terms = self.index._process_text(query_str)
        scores = []

        for doc_id in doc_ids:
            score = ranker.score(query_terms, doc_id)
            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
