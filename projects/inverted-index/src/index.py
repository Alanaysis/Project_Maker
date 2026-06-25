"""倒排索引模块 - Inverted Index

实现倒排索引、位置索引和压缩索引。
"""

import json
import gzip
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple

from .tokenizer import Tokenizer
from .stopwords import StopWordsFilter
from .stemmer import PorterStemmer
from .lemmatizer import Lemmatizer


@dataclass
class Document:
    """文档数据结构"""
    doc_id: str
    title: str
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class PostingEntry:
    """倒排列表条目"""
    doc_id: str
    term_frequency: int = 0
    positions: List[int] = field(default_factory=list)


class InvertedIndex:
    """倒排索引

    基本的倒排索引实现，支持文档索引和查询。
    """

    def __init__(self):
        self.index: Dict[str, List[PostingEntry]] = defaultdict(list)
        self.documents: Dict[str, Document] = {}
        self.doc_count: int = 0
        self.avg_doc_length: float = 0.0
        self.doc_lengths: Dict[str, int] = {}

        # 文档处理组件
        self.tokenizer = Tokenizer()
        self.stopwords_filter = StopWordsFilter()
        self.stemmer = PorterStemmer()
        self.lemmatizer = Lemmatizer()

    def add_document(self, doc: Document) -> None:
        """添加文档到索引

        Args:
            doc: 文档对象
        """
        if doc.doc_id in self.documents:
            self.remove_document(doc.doc_id)

        self.documents[doc.doc_id] = doc
        self.doc_count += 1

        # 处理文本
        full_text = f"{doc.title} {doc.content}"
        tokens = self._process_text(full_text)

        # 记录文档长度
        self.doc_lengths[doc.doc_id] = len(tokens)
        self._update_avg_doc_length()

        # 统计词频
        term_freq: Dict[str, int] = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1

        # 构建倒排列表
        for term, freq in term_freq.items():
            posting = PostingEntry(
                doc_id=doc.doc_id,
                term_frequency=freq
            )
            self.index[term].append(posting)

    def remove_document(self, doc_id: str) -> None:
        """从索引中移除文档

        Args:
            doc_id: 文档ID
        """
        if doc_id not in self.documents:
            return

        del self.documents[doc_id]
        self.doc_count -= 1

        # 更新倒排列表
        for term in list(self.index.keys()):
            self.index[term] = [p for p in self.index[term] if p.doc_id != doc_id]
            if not self.index[term]:
                del self.index[term]

        if doc_id in self.doc_lengths:
            del self.doc_lengths[doc_id]

        self._update_avg_doc_length()

    def get_postings(self, term: str) -> List[PostingEntry]:
        """获取词汇的倒排列表

        Args:
            term: 查询词汇

        Returns:
            倒排列表
        """
        processed = self._process_text(term)
        if not processed:
            return []
        return self.index.get(processed[0], [])

    def get_document_frequency(self, term: str) -> int:
        """获取文档频率

        Args:
            term: 词汇

        Returns:
            包含该词的文档数量
        """
        return len(self.get_postings(term))

    def get_vocabulary_size(self) -> int:
        """获取词汇表大小"""
        return len(self.index)

    def _process_text(self, text: str) -> List[str]:
        """处理文本：分词 -> 过滤停用词 -> 词干提取

        Args:
            text: 输入文本

        Returns:
            处理后的词汇列表
        """
        tokens = self.tokenizer.tokenize(text)
        tokens = self.stopwords_filter.filter(tokens)
        tokens = self.stemmer.stem_tokens(tokens)
        return [t for t in tokens if len(t) > 1]  # 过滤单字符

    def _update_avg_doc_length(self) -> None:
        """更新平均文档长度"""
        if self.doc_count > 0:
            total_length = sum(self.doc_lengths.values())
            self.avg_doc_length = total_length / self.doc_count

    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'doc_count': self.doc_count,
            'avg_doc_length': self.avg_doc_length,
            'documents': {k: {'doc_id': v.doc_id, 'title': v.title,
                             'content': v.content, 'metadata': v.metadata}
                         for k, v in self.documents.items()},
            'index': {term: [{'doc_id': p.doc_id, 'term_frequency': p.term_frequency,
                             'positions': p.positions} for p in postings]
                     for term, postings in self.index.items()},
            'doc_lengths': self.doc_lengths
        }

    def save(self, filepath: str) -> None:
        """保存索引到文件

        Args:
            filepath: 文件路径
        """
        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, filepath: str) -> None:
        """从文件加载索引

        Args:
            filepath: 文件路径
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.doc_count = data['doc_count']
        self.avg_doc_length = data['avg_doc_length']
        self.doc_lengths = data['doc_lengths']

        self.documents = {}
        for k, v in data['documents'].items():
            self.documents[k] = Document(**v)

        self.index = defaultdict(list)
        for term, postings in data['index'].items():
            for p in postings:
                self.index[term].append(PostingEntry(**p))


class PositionalIndex(InvertedIndex):
    """位置索引

    在倒排索引基础上记录词汇位置，支持短语查询。
    """

    def add_document(self, doc: Document) -> None:
        """添加文档到索引（记录位置信息）

        Args:
            doc: 文档对象
        """
        if doc.doc_id in self.documents:
            self.remove_document(doc.doc_id)

        self.documents[doc.doc_id] = doc
        self.doc_count += 1

        # 处理文本并记录位置
        full_text = f"{doc.title} {doc.content}"
        tokens_with_positions = self.tokenizer.tokenize_with_positions(full_text)

        # 过滤停用词并保持位置
        filtered_tokens = []
        for token, pos in tokens_with_positions:
            if not self.stopwords_filter.is_stop_word(token) and len(token) > 1:
                stemmed = self.stemmer.stem(token.lower())
                filtered_tokens.append((stemmed, pos))

        # 记录文档长度
        self.doc_lengths[doc.doc_id] = len(filtered_tokens)
        self._update_avg_doc_length()

        # 构建带位置的倒排列表
        term_positions: Dict[str, List[int]] = defaultdict(list)
        for token, pos in filtered_tokens:
            term_positions[token].append(pos)

        for term, positions in term_positions.items():
            posting = PostingEntry(
                doc_id=doc.doc_id,
                term_frequency=len(positions),
                positions=positions
            )
            self.index[term].append(posting)

    def search_phrase(self, phrase: str) -> List[str]:
        """短语查询

        Args:
            phrase: 查询短语

        Returns:
            匹配的文档ID列表
        """
        tokens = self._process_text(phrase)
        if not tokens:
            return []

        # 获取每个词汇的倒排列表
        postings_lists = [self.get_postings(token) for token in tokens]
        if not all(postings_lists):
            return []

        # 找出包含所有词汇的文档
        doc_sets = [set(p.doc_id for p in pl) for pl in postings_lists]
        common_docs = doc_sets[0].intersection(*doc_sets[1:])

        # 检查位置连续性
        result = []
        for doc_id in common_docs:
            if self._check_positions(doc_id, tokens):
                result.append(doc_id)

        return result

    def _check_positions(self, doc_id: str, tokens: List[str]) -> bool:
        """检查词汇位置是否连续

        Args:
            doc_id: 文档ID
            tokens: 词汇列表

        Returns:
            是否连续
        """
        # 获取每个词汇在文档中的位置
        positions_list = []
        for token in tokens:
            postings = self.index.get(token, [])
            for p in postings:
                if p.doc_id == doc_id:
                    positions_list.append(p.positions)
                    break

        if len(positions_list) != len(tokens):
            return False

        # 检查是否存在连续位置序列
        first_positions = positions_list[0]
        for start_pos in first_positions:
            match = True
            for i in range(1, len(tokens)):
                if (start_pos + i) not in positions_list[i]:
                    match = False
                    break
            if match:
                return True

        return False


class CompressedIndex(InvertedIndex):
    """压缩索引

    使用可变字节编码压缩倒排索引，减少存储空间。
    """

    def __init__(self):
        super().__init__()
        self.compressed_data: Dict[str, bytes] = {}

    def compress(self) -> None:
        """压缩索引"""
        for term, postings in self.index.items():
            # 对文档ID进行差分编码
            sorted_postings = sorted(postings, key=lambda p: p.doc_id)
            compressed = self._variable_byte_encode(sorted_postings)
            self.compressed_data[term] = compressed

    def decompress(self, term: str) -> List[PostingEntry]:
        """解压词汇的倒排列表

        Args:
            term: 词汇

        Returns:
            倒排列表
        """
        if term not in self.compressed_data:
            return self.index.get(term, [])
        return self._variable_byte_decode(self.compressed_data[term])

    def _variable_byte_encode(self, postings: List[PostingEntry]) -> bytes:
        """可变字节编码

        Args:
            postings: 倒排列表

        Returns:
            编码后的字节
        """
        result = bytearray()

        # 编码列表长度
        result.extend(self._encode_number(len(postings)))

        prev_doc_id = 0
        for posting in postings:
            # 差分编码文档ID
            doc_id_num = int(posting.doc_id) if posting.doc_id.isdigit() else hash(posting.doc_id) % (2**31)
            delta = doc_id_num - prev_doc_id
            prev_doc_id = doc_id_num

            result.extend(self._encode_number(delta))
            result.extend(self._encode_number(posting.term_frequency))

            # 编码位置信息
            result.extend(self._encode_number(len(posting.positions)))
            prev_pos = 0
            for pos in posting.positions:
                result.extend(self._encode_number(pos - prev_pos))
                prev_pos = pos

        return bytes(result)

    def _variable_byte_decode(self, data: bytes) -> List[PostingEntry]:
        """可变字节解码

        Args:
            data: 编码数据

        Returns:
            倒排列表
        """
        result = []
        pos = 0

        # 解码列表长度
        length, pos = self._decode_number(data, pos)

        prev_doc_id = 0
        for _ in range(length):
            # 解码文档ID差分值
            delta, pos = self._decode_number(data, pos)
            doc_id = str(prev_doc_id + delta)
            prev_doc_id = doc_id if isinstance(doc_id, int) else int(doc_id)

            # 解码词频
            tf, pos = self._decode_number(data, pos)

            # 解码位置信息
            positions = []
            num_positions, pos = self._decode_number(data, pos)
            prev_position = 0
            for _ in range(num_positions):
                pos_delta, pos = self._decode_number(data, pos)
                position = prev_position + pos_delta
                positions.append(position)
                prev_position = position

            result.append(PostingEntry(
                doc_id=doc_id,
                term_frequency=tf,
                positions=positions
            ))

        return result

    def _encode_number(self, n: int) -> bytes:
        """编码单个数字为可变字节

        Args:
            n: 数字

        Returns:
            编码字节
        """
        result = bytearray()
        while n >= 128:
            result.append((n & 0x7F) | 0x80)
            n >>= 7
        result.append(n & 0x7F)
        return bytes(result)

    def _decode_number(self, data: bytes, pos: int) -> Tuple[int, int]:
        """从可变字节解码数字

        Args:
            data: 字节数据
            pos: 起始位置

        Returns:
            (数字, 新位置)
        """
        n = 0
        shift = 0
        while pos < len(data):
            byte = data[pos]
            n |= (byte & 0x7F) << shift
            pos += 1
            shift += 7
            if byte < 128:
                break
        return n, pos

    def get_compression_ratio(self) -> float:
        """获取压缩比

        Returns:
            压缩比 (压缩后大小 / 原始大小)
        """
        if not self.compressed_data:
            return 1.0

        compressed_size = sum(len(v) for v in self.compressed_data.values())

        # 估算原始大小
        original_size = 0
        for postings in self.index.values():
            for p in postings:
                original_size += len(p.doc_id) + 8  # doc_id + term_frequency
                original_size += len(p.positions) * 4  # 每个位置4字节

        return compressed_size / original_size if original_size > 0 else 1.0

    def save_compressed(self, filepath: str) -> None:
        """保存压缩索引

        Args:
            filepath: 文件路径
        """
        self.compress()
        data = {
            'doc_count': self.doc_count,
            'avg_doc_length': self.avg_doc_length,
            'documents': {k: {'doc_id': v.doc_id, 'title': v.title,
                             'content': v.content, 'metadata': v.metadata}
                         for k, v in self.documents.items()},
            'compressed': {term: list(comp) for term, comp in self.compressed_data.items()},
            'doc_lengths': self.doc_lengths
        }

        # 使用gzip压缩存储
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(data, f)

    def load_compressed(self, filepath: str) -> None:
        """加载压缩索引

        Args:
            filepath: 文件路径
        """
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)

        self.doc_count = data['doc_count']
        self.avg_doc_length = data['avg_doc_length']
        self.doc_lengths = data['doc_lengths']

        self.documents = {}
        for k, v in data['documents'].items():
            self.documents[k] = Document(**v)

        self.compressed_data = {}
        for term, comp in data['compressed'].items():
            self.compressed_data[term] = bytes(comp)
