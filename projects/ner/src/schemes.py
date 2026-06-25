"""
标注方案模块
============

支持两种主流的序列标注方案:
1. BIO: Begin, Inside, Outside
2. BIOES: Begin, Inside, Outside, End, Single

BIO 标注:
  B-XXX: 实体 XXX 的开始
  I-XXX: 实体 XXX 的内部
  O:     非实体

BIOES 标注:
  B-XXX: 多 token 实体的开始
  I-XXX: 多 token 实体的内部
  O:     非实体
  E-XXX: 多 token 实体的结束
  S-XXX: 单 token 实体

BIOES 比 BIO 提供更丰富的边界信息，通常效果更好。
"""

from typing import List, Tuple, Optional


class BIOEncoder:
    """
    BIO 标注方案编解码器

    标注规则:
    - 实体的第一个 token: B-XXX
    - 实体的后续 token: I-XXX
    - 非实体 token: O
    - 相邻同类实体: 用 B- 分隔
    """

    @staticmethod
    def encode(entities: List[Tuple[str, int, int]],
               seq_len: int) -> List[str]:
        """
        将实体列表编码为 BIO 标签序列

        参数:
            entities: [(实体类型, 开始位置, 结束位置), ...]
            seq_len: 序列长度

        返回:
            tags: BIO 标签序列
        """
        tags = ["O"] * seq_len

        for entity_type, start, end in entities:
            for i in range(start, end + 1):
                if i >= seq_len:
                    break
                if i == start:
                    tags[i] = f"B-{entity_type}"
                else:
                    tags[i] = f"I-{entity_type}"

        return tags

    @staticmethod
    def decode(tags: List[str]) -> List[Tuple[str, int, int]]:
        """
        将 BIO 标签序列解码为实体列表

        参数:
            tags: BIO 标签序列

        返回:
            entities: [(实体类型, 开始位置, 结束位置), ...]
        """
        entities = []
        current_type = None
        current_start = None

        for i, tag in enumerate(tags):
            if tag.startswith("B-"):
                # 保存之前的实体
                if current_type is not None:
                    entities.append((current_type, current_start, i - 1))
                # 开始新实体
                current_type = tag[2:]
                current_start = i

            elif tag.startswith("I-"):
                entity_type = tag[2:]
                if current_type == entity_type:
                    # 继续当前实体
                    continue
                else:
                    # 类型不匹配，结束之前的实体
                    if current_type is not None:
                        entities.append(
                            (current_type, current_start, i - 1)
                        )
                    current_type = None
                    current_start = None

            else:  # O 标签
                if current_type is not None:
                    entities.append(
                        (current_type, current_start, i - 1)
                    )
                    current_type = None
                    current_start = None

        # 最后一个实体
        if current_type is not None:
            entities.append(
                (current_type, current_start, len(tags) - 1)
            )

        return entities

    @staticmethod
    def get_tag_set(entity_types: List[str]) -> List[str]:
        """
        获取完整的标签集合

        参数:
            entity_types: 实体类型列表

        返回:
            tags: 所有可能的标签
        """
        tags = ["O"]
        for entity_type in entity_types:
            tags.append(f"B-{entity_type}")
            tags.append(f"I-{entity_type}")
        return tags


class BIOESEncoder:
    """
    BIOES 标注方案编解码器

    标注规则:
    - 多 token 实体的第一个 token: B-XXX
    - 多 token 实体的内部 token: I-XXX
    - 多 token 实体的最后一个 token: E-XXX
    - 单 token 实体: S-XXX
    - 非实体 token: O

    相比 BIO 的优势:
    - 明确标记实体结束位置
    - 区分单 token 实体和多 token 实体
    - 提供更丰富的边界信息
    """

    @staticmethod
    def encode(entities: List[Tuple[str, int, int]],
               seq_len: int) -> List[str]:
        """
        将实体列表编码为 BIOES 标签序列

        参数:
            entities: [(实体类型, 开始位置, 结束位置), ...]
            seq_len: 序列长度

        返回:
            tags: BIOES 标签序列
        """
        tags = ["O"] * seq_len

        for entity_type, start, end in entities:
            if start >= seq_len:
                continue

            entity_len = end - start + 1

            if entity_len == 1:
                # 单 token 实体
                tags[start] = f"S-{entity_type}"
            else:
                # 多 token 实体
                for i in range(start, min(end + 1, seq_len)):
                    if i == start:
                        tags[i] = f"B-{entity_type}"
                    elif i == end:
                        tags[i] = f"E-{entity_type}"
                    else:
                        tags[i] = f"I-{entity_type}"

        return tags

    @staticmethod
    def decode(tags: List[str]) -> List[Tuple[str, int, int]]:
        """
        将 BIOES 标签序列解码为实体列表

        参数:
            tags: BIOES 标签序列

        返回:
            entities: [(实体类型, 开始位置, 结束位置), ...]
        """
        entities = []
        current_type = None
        current_start = None

        for i, tag in enumerate(tags):
            if tag.startswith("S-"):
                # 保存之前的实体
                if current_type is not None:
                    entities.append((current_type, current_start, i - 1))
                # 单 token 实体
                entities.append((tag[2:], i, i))
                current_type = None
                current_start = None

            elif tag.startswith("B-"):
                # 保存之前的实体
                if current_type is not None:
                    entities.append((current_type, current_start, i - 1))
                # 开始新实体
                current_type = tag[2:]
                current_start = i

            elif tag.startswith("I-"):
                entity_type = tag[2:]
                if current_type != entity_type:
                    # 类型不匹配
                    if current_type is not None:
                        entities.append(
                            (current_type, current_start, i - 1)
                        )
                    current_type = None
                    current_start = None

            elif tag.startswith("E-"):
                entity_type = tag[2:]
                if current_type == entity_type:
                    # 结束当前实体
                    entities.append((current_type, current_start, i))
                    current_type = None
                    current_start = None
                else:
                    # 类型不匹配
                    if current_type is not None:
                        entities.append(
                            (current_type, current_start, i - 1)
                        )
                    current_type = None
                    current_start = None

            else:  # O 标签
                if current_type is not None:
                    entities.append(
                        (current_type, current_start, i - 1)
                    )
                    current_type = None
                    current_start = None

        # 最后一个实体
        if current_type is not None:
            entities.append(
                (current_type, current_start, len(tags) - 1)
            )

        return entities

    @staticmethod
    def get_tag_set(entity_types: List[str]) -> List[str]:
        """
        获取完整的标签集合

        参数:
            entity_types: 实体类型列表

        返回:
            tags: 所有可能的标签
        """
        tags = ["O"]
        for entity_type in entity_types:
            tags.append(f"B-{entity_type}")
            tags.append(f"I-{entity_type}")
            tags.append(f"E-{entity_type}")
            tags.append(f"S-{entity_type}")
        return tags


def bio_to_bioes(bio_tags: List[str]) -> List[str]:
    """
    将 BIO 标签转换为 BIOES 标签

    参数:
        bio_tags: BIO 标签序列

    返回:
        bioes_tags: BIOES 标签序列
    """
    # 先解码为实体
    entities = BIOEncoder.decode(bio_tags)
    # 再编码为 BIOES
    return BIOESEncoder.encode(entities, len(bio_tags))


def bioes_to_bio(bioes_tags: List[str]) -> List[str]:
    """
    将 BIOES 标签转换为 BIO 标签

    参数:
        bioes_tags: BIOES 标签序列

    返回:
        bio_tags: BIO 标签序列
    """
    # 先解码为实体
    entities = BIOESEncoder.decode(bioes_tags)
    # 再编码为 BIO
    return BIOEncoder.encode(entities, len(bioes_tags))
