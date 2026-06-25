"""
基于正则表达式的 NER
====================

使用正则表达式模式匹配识别命名实体。

适用场景:
- 格式化实体: 日期、电话号码、邮箱、网址等
- 特定模式的实体: 身份证号、IP 地址等
- 规则明确的实体: 货币金额、百分比等

优点:
- 无需训练数据
- 精确度高 (在规则覆盖范围内)
- 可解释性强

缺点:
- 召回率低 (无法覆盖所有情况)
- 需要人工编写规则
- 难以处理歧义
"""

import re
from typing import List, Dict, Tuple, Optional


class RegexNER:
    """
    基于正则表达式的命名实体识别器

    内置模式:
    - DATE: 日期 (2024-01-15, 2024年1月15日)
    - PHONE: 电话号码 (13812345678, 010-12345678)
    - EMAIL: 邮箱地址
    - URL: 网址
    - ID_CARD: 身份证号
    - IP: IP 地址
    - MONEY: 货币金额

    用法:
        ner = RegexNER()
        entities = ner.recognize("请拨打 13812345678 联系我")
        # [('PHONE', '13812345678', 4, 15)]
    """

    # 预定义的正则模式
    DEFAULT_PATTERNS = {
        "DATE": [
            # 2024-01-15
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            # 2024年1月15日
            r'\d{4}年\d{1,2}月\d{1,2}日',
            # 01/15/2024
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        ],
        "PHONE": [
            # 中国手机号: 13812345678
            r'\b1[3-9]\d{9}\b',
            # 带区号座机: 010-12345678
            r'\b0\d{2,3}[-\s]?\d{7,8}\b',
            # 国际格式: +86 13812345678
            r'\+\d{1,3}\s?\d{10,}',
        ],
        "EMAIL": [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        "URL": [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
        ],
        "ID_CARD": [
            # 18位身份证号
            r'\b\d{17}[\dXx]\b',
        ],
        "IP": [
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        ],
        "MONEY": [
            # ￥100, $50, €30
            r'[￥$€£]\s?\d+(?:,\d{3})*(?:\.\d{1,2})?',
            # 100元, 50美元
            r'\d+(?:,\d{3})*(?:\.\d{1,2})?\s?(?:元|美元|欧元|英镑|日元)',
        ],
    }

    def __init__(self, patterns: Optional[Dict[str, List[str]]] = None):
        """
        参数:
            patterns: 自定义模式字典 {实体类型: [正则表达式, ...]}
                      如果为 None，使用默认模式
        """
        if patterns is None:
            patterns = self.DEFAULT_PATTERNS

        self.patterns: Dict[str, List[re.Pattern]] = {}
        for entity_type, regex_list in patterns.items():
            self.patterns[entity_type] = [
                re.compile(pattern) for pattern in regex_list
            ]

    def add_pattern(self, entity_type: str, pattern: str):
        """
        添加新的匹配模式

        参数:
            entity_type: 实体类型
            pattern: 正则表达式
        """
        if entity_type not in self.patterns:
            self.patterns[entity_type] = []
        self.patterns[entity_type].append(re.compile(pattern))

    def recognize(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        识别文本中的命名实体

        参数:
            text: 输入文本

        返回:
            entities: 实体列表 [(类型, 文本, 开始位置, 结束位置), ...]
            按照在文本中出现的顺序排列
        """
        all_matches = []

        for entity_type, compiled_patterns in self.patterns.items():
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    all_matches.append((
                        entity_type,
                        match.group(),
                        match.start(),
                        match.end()
                    ))

        # 按位置排序
        all_matches.sort(key=lambda x: x[2])

        # 去除重叠 (保留较长的匹配)
        return self._remove_overlaps(all_matches)

    def recognize_tokens(self, tokens: List[str]) -> List[str]:
        """
        对 token 序列进行标注

        参数:
            tokens: token 列表

        返回:
            tags: BIO 标签列表
        """
        # 将 token 序列还原为文本
        text = " ".join(tokens)
        entities = self.recognize(text)

        # 初始化为 O 标签
        tags = ["O"] * len(tokens)

        # 计算每个 token 在文本中的位置
        token_positions = []
        pos = 0
        for token in tokens:
            start = text.find(token, pos)
            if start == -1:
                token_positions.append((pos, pos + len(token)))
            else:
                token_positions.append((start, start + len(token)))
            pos = token_positions[-1][1] + 1  # +1 for space

        # 标注实体
        for entity_type, entity_text, start, end in entities:
            for i, (tok_start, tok_end) in enumerate(token_positions):
                if tok_start >= start and tok_end <= end:
                    if tok_start == start:
                        tags[i] = f"B-{entity_type}"
                    else:
                        tags[i] = f"I-{entity_type}"

        return tags

    def _remove_overlaps(self, matches: List[Tuple]) -> List[Tuple]:
        """
        去除重叠的匹配结果

        策略: 保留较长的匹配，如果长度相同则保留前面的

        参数:
            matches: 匹配结果列表

        返回:
            去重后的结果
        """
        if not matches:
            return []

        result = [matches[0]]

        for current in matches[1:]:
            prev = result[-1]
            # 检查是否重叠
            if current[2] >= prev[3]:
                # 不重叠
                result.append(current)
            elif len(current[1]) > len(prev[1]):
                # 当前匹配更长，替换前一个
                result[-1] = current
            # 否则保留前一个

        return result

    def get_supported_types(self) -> List[str]:
        """获取支持的实体类型"""
        return list(self.patterns.keys())

    def __repr__(self) -> str:
        types = ", ".join(self.patterns.keys())
        return f"RegexNER(types=[{types}])"
