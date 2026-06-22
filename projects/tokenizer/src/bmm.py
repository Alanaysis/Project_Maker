"""
逆向最大匹配分词算法
Backward Maximum Matching (BMM)
"""

from .dictionary import Dictionary


class BMM:
    """逆向最大匹配分词器"""

    def __init__(self, dictionary):
        """
        初始化 BMM 分词器

        Args:
            dictionary: Dictionary 词典对象
        """
        self.dictionary = dictionary
        self.max_len = dictionary.get_max_word_length()

    def segment(self, text):
        """
        对文本进行逆向最大匹配分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Examples:
            >>> dict = Dictionary()
            >>> dict.add("我", 100)
            >>> dict.add("爱", 100)
            >>> dict.add("北京", 100)
            >>> bmm = BMM(dict)
            >>> bmm.segment("我爱北京")
            ['我', '爱', '北京']
        """
        if not text:
            return []

        result = []
        i = len(text)

        while i > 0:
            matched = False

            # 从最长词开始匹配
            for length in range(self.max_len, 0, -1):
                # 边界检查
                if i - length < 0:
                    continue

                # 取子串
                word = text[i - length:i]

                # 在词典中查找
                if self.dictionary.contains(word):
                    result.append(word)
                    i -= length
                    matched = True
                    break

            # 未匹配则取单字
            if not matched:
                result.append(text[i - 1])
                i -= 1

        # 逆向结果需要反转
        return list(reversed(result))
