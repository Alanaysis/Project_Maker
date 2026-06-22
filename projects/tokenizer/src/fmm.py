"""
正向最大匹配分词算法
Forward Maximum Matching (FMM)
"""

from .dictionary import Dictionary


class FMM:
    """正向最大匹配分词器"""

    def __init__(self, dictionary):
        """
        初始化 FMM 分词器

        Args:
            dictionary: Dictionary 词典对象
        """
        self.dictionary = dictionary
        self.max_len = dictionary.get_max_word_length()

    def segment(self, text):
        """
        对文本进行正向最大匹配分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Examples:
            >>> dict = Dictionary()
            >>> dict.add("我", 100)
            >>> dict.add("爱", 100)
            >>> dict.add("北京", 100)
            >>> fmm = FMM(dict)
            >>> fmm.segment("我爱北京")
            ['我', '爱', '北京']
        """
        if not text:
            return []

        result = []
        i = 0
        text_len = len(text)

        while i < text_len:
            matched = False

            # 从最长词开始匹配
            for length in range(self.max_len, 0, -1):
                # 边界检查
                if i + length > text_len:
                    continue

                # 取子串
                word = text[i:i + length]

                # 在词典中查找
                if self.dictionary.contains(word):
                    result.append(word)
                    i += length
                    matched = True
                    break

            # 未匹配则取单字
            if not matched:
                result.append(text[i])
                i += 1

        return result
