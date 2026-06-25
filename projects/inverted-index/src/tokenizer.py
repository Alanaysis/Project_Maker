"""分词器模块 - Tokenizer

提供文本分词功能，支持中英文分词。
"""

import re
from typing import List


class Tokenizer:
    """文本分词器"""

    def __init__(self, lowercase: bool = True, remove_punctuation: bool = True):
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self._punctuation_pattern = re.compile(r'[^\w\s一-鿿]')

    def tokenize(self, text: str) -> List[str]:
        """将文本分词为token列表

        Args:
            text: 输入文本

        Returns:
            token列表
        """
        if not text:
            return []

        if self.lowercase:
            text = text.lower()

        if self.remove_punctuation:
            text = self._punctuation_pattern.sub(' ', text)

        tokens = []
        # 处理中文和英文混合文本
        segments = re.findall(r'[一-鿿]+|[a-zA-Z]+|\d+', text)

        for segment in segments:
            if re.match(r'[一-鿿]', segment):
                # 中文按字符分词（简单实现）
                tokens.extend(list(segment))
            else:
                # 英文和数字作为整体
                tokens.append(segment)

        return tokens

    def tokenize_with_positions(self, text: str) -> List[tuple]:
        """分词并记录位置

        Args:
            text: 输入文本

        Returns:
            (token, position)列表
        """
        tokens = self.tokenize(text)
        return [(token, i) for i, token in enumerate(tokens)]
