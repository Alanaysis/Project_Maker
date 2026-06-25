"""
基于词典的 NER
==============

使用词典匹配识别命名实体，支持正向最大匹配和逆向最大匹配。

适用场景:
- 已知实体集合明确: 人名库、地名库、机构名库
- 专业术语: 医学名词、法律术语
- 产品名称: 品牌名、商品名

优点:
- 速度快 (O(n*m)，n 为文本长度，m 为最长词长)
- 精确度高 (在词典覆盖范围内)
- 易于维护和更新

缺点:
- 召回率受词典覆盖限制
- 无法识别未登录实体
- 歧义切分问题
"""

from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class TrieNode:
    """Trie 树节点"""

    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end: bool = False
        self.entity_type: Optional[str] = None


class DictNER:
    """
    基于词典的命名实体识别器

    使用 Trie 树实现高效的词典匹配，支持:
    - 正向最大匹配 (Forward Maximum Matching)
    - 逆向最大匹配 (Backward Maximum Matching)
    - 双向匹配 (结合两种方法)

    用法:
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        ner.add_entity("上海市", "LOC")
        ner.add_entity("清华大学", "ORG")
        entities = ner.recognize("我去了北京市清华大学")
    """

    def __init__(self):
        """初始化词典 NER"""
        self.trie = TrieNode()
        self.entity_count: Dict[str, int] = defaultdict(int)
        self.total_entities = 0

    def add_entity(self, entity: str, entity_type: str):
        """
        添加实体到词典

        参数:
            entity: 实体文本
            entity_type: 实体类型 (如 PER, LOC, ORG)
        """
        node = self.trie
        for char in entity:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        node.is_end = True
        node.entity_type = entity_type
        self.entity_count[entity_type] += 1
        self.total_entities += 1

    def add_entities(self, entities: Dict[str, str]):
        """
        批量添加实体

        参数:
            entities: {实体文本: 实体类型} 字典
        """
        for entity, entity_type in entities.items():
            self.add_entity(entity, entity_type)

    def add_entity_list(self, entity_list: List[str], entity_type: str):
        """
        添加同类型的实体列表

        参数:
            entity_list: 实体文本列表
            entity_type: 实体类型
        """
        for entity in entity_list:
            self.add_entity(entity, entity_type)

    def load_from_file(self, filepath: str, entity_type: str,
                       encoding: str = 'utf-8'):
        """
        从文件加载实体词典

        文件格式: 每行一个实体

        参数:
            filepath: 文件路径
            entity_type: 实体类型
            encoding: 文件编码
        """
        with open(filepath, 'r', encoding=encoding) as f:
            for line in f:
                entity = line.strip()
                if entity:
                    self.add_entity(entity, entity_type)

    def recognize(self, text: str,
                  method: str = "forward") -> List[Tuple[str, str, int, int]]:
        """
        识别文本中的命名实体

        参数:
            text: 输入文本
            method: 匹配方法
                - "forward": 正向最大匹配
                - "backward": 逆向最大匹配
                - "bidirectional": 双向匹配 (取切分数量少的结果)

        返回:
            entities: 实体列表 [(类型, 文本, 开始位置, 结束位置), ...]
        """
        if method == "forward":
            return self._forward_match(text)
        elif method == "backward":
            return self._backward_match(text)
        elif method == "bidirectional":
            return self._bidirectional_match(text)
        else:
            raise ValueError(f"Unknown method: {method}")

    def recognize_tokens(self, tokens: List[str],
                         method: str = "forward") -> List[str]:
        """
        对 token 序列进行标注

        参数:
            tokens: token 列表
            method: 匹配方法

        返回:
            tags: BIO 标签列表
        """
        # 将 token 序列还原为文本
        text = "".join(tokens)
        entities = self.recognize(text, method)

        # 初始化为 O 标签
        tags = ["O"] * len(tokens)

        # 计算每个 token 在文本中的位置
        token_positions = []
        pos = 0
        for token in tokens:
            start = pos
            end = pos + len(token)
            token_positions.append((start, end))
            pos = end

        # 标注实体
        for entity_type, entity_text, start, end in entities:
            first = True
            for i, (tok_start, tok_end) in enumerate(token_positions):
                if tok_start >= start and tok_end <= end:
                    if first:
                        tags[i] = f"B-{entity_type}"
                        first = False
                    else:
                        tags[i] = f"I-{entity_type}"

        return tags

    def _forward_match(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        正向最大匹配

        从左到右扫描文本，每次尝试匹配最长的实体。

        时间复杂度: O(n * L)，其中 n 为文本长度，L 为最长实体长度
        """
        entities = []
        i = 0
        text_len = len(text)

        while i < text_len:
            # 尝试从当前位置匹配最长的实体
            best_match = None
            best_type = None

            node = self.trie
            j = i

            while j < text_len and text[j] in node.children:
                node = node.children[text[j]]
                j += 1
                if node.is_end:
                    best_match = text[i:j]
                    best_type = node.entity_type

            if best_match is not None:
                entities.append((best_type, best_match, i, i + len(best_match)))
                i += len(best_match)
            else:
                i += 1

        return entities

    def _backward_match(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        逆向最大匹配

        从右到左扫描文本，每次尝试匹配最长的实体。
        """
        entities = []
        text_len = len(text)
        i = text_len

        while i > 0:
            # 尝试从当前位置向左匹配最长的实体
            best_match = None
            best_type = None
            best_start = None

            # 限制最大匹配长度
            max_len = min(i, 20)  # 假设最长实体不超过 20 字符

            for length in range(max_len, 0, -1):
                start = i - length
                substr = text[start:i]

                if self._search(substr):
                    best_match = substr
                    best_type = self._get_type(substr)
                    best_start = start
                    break

            if best_match is not None:
                entities.append((best_type, best_match, best_start, i))
                i = best_start
            else:
                i -= 1

        entities.reverse()
        return entities

    def _bidirectional_match(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        双向匹配

        同时使用正向和逆向匹配，选择切分数量较少的结果。
        如果数量相同，选择单个实体更长的结果。
        """
        forward_entities = self._forward_match(text)
        backward_entities = self._backward_match(text)

        # 比较两种方法的结果
        if len(forward_entities) < len(backward_entities):
            return forward_entities
        elif len(backward_entities) < len(forward_entities):
            return backward_entities
        else:
            # 数量相同，比较平均实体长度
            forward_avg = (sum(len(e[1]) for e in forward_entities) /
                           len(forward_entities) if forward_entities else 0)
            backward_avg = (sum(len(e[1]) for e in backward_entities) /
                            len(backward_entities) if backward_entities else 0)

            return forward_entities if forward_avg >= backward_avg else backward_entities

    def _search(self, word: str) -> bool:
        """在 Trie 树中搜索词语"""
        node = self.trie
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def _get_type(self, word: str) -> Optional[str]:
        """获取词语的实体类型"""
        node = self.trie
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        return node.entity_type if node.is_end else None

    def get_statistics(self) -> Dict:
        """获取词典统计信息"""
        return {
            "total_entities": self.total_entities,
            "entity_types": dict(self.entity_count),
            "trie_nodes": self._count_nodes(self.trie)
        }

    def _count_nodes(self, node: TrieNode) -> int:
        """递归计算 Trie 节点数"""
        count = 1
        for child in node.children.values():
            count += self._count_nodes(child)
        return count

    def __len__(self) -> int:
        return self.total_entities

    def __repr__(self) -> str:
        return (f"DictNER(entities={self.total_entities}, "
                f"types={list(self.entity_count.keys())})")
