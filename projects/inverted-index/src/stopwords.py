"""停用词过滤模块 - Stop Words Filter

提供停用词过滤功能，移除常见无意义词汇。
"""

from typing import List, Set


# 英文停用词列表
ENGLISH_STOP_WORDS: Set[str] = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that',
    'these', 'those', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he',
    'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
    'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all',
    'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
}

# 中文停用词列表
CHINESE_STOP_WORDS: Set[str] = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '被',
    '从', '把', '让', '用', '为', '以', '所', '而', '及', '与', '或',
    '但', '如', '若', '虽然', '因为', '所以', '可以', '这个', '那个',
}


class StopWordsFilter:
    """停用词过滤器"""

    def __init__(self, custom_stop_words: Set[str] = None, language: str = 'both'):
        """初始化停用词过滤器

        Args:
            custom_stop_words: 自定义停用词集合
            language: 语言选择 ('en', 'zh', 'both')
        """
        self.stop_words: Set[str] = set()

        if language in ('en', 'both'):
            self.stop_words.update(ENGLISH_STOP_WORDS)
        if language in ('zh', 'both'):
            self.stop_words.update(CHINESE_STOP_WORDS)
        if custom_stop_words:
            self.stop_words.update(custom_stop_words)

    def is_stop_word(self, token: str) -> bool:
        """判断是否为停用词

        Args:
            token: 待判断的词

        Returns:
            是否为停用词
        """
        return token.lower() in self.stop_words

    def filter(self, tokens: List[str]) -> List[str]:
        """过滤停用词

        Args:
            tokens: token列表

        Returns:
            过滤后的token列表
        """
        return [token for token in tokens if not self.is_stop_word(token)]

    def add_stop_words(self, words: Set[str]) -> None:
        """添加自定义停用词

        Args:
            words: 停用词集合
        """
        self.stop_words.update(words)

    def remove_stop_words(self, words: Set[str]) -> None:
        """从停用词列表中移除

        Args:
            words: 要移除的词集合
        """
        self.stop_words -= words
