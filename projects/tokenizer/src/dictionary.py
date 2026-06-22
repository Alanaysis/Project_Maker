"""
词典管理模块
"""

class Dictionary:
    """词典管理类"""

    def __init__(self):
        """初始化词典"""
        self.words = {}  # {word: freq}
        self.max_length = 0

    def load(self, filepath):
        """
        加载词典文件

        Args:
            filepath: 词典文件路径，每行格式为 "词语 频率"

        Raises:
            FileNotFoundError: 文件不存在
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        word = parts[0]
                        freq = int(parts[1])
                        self.add(word, freq)
        except FileNotFoundError:
            raise FileNotFoundError(f"词典文件不存在: {filepath}")

    def add(self, word, freq=1):
        """
        添加词条

        Args:
            word: 词语
            freq: 词频，默认为 1
        """
        self.words[word] = freq
        self.max_length = max(self.max_length, len(word))

    def remove(self, word):
        """
        删除词条

        Args:
            word: 要删除的词语

        Raises:
            KeyError: 词语不存在
        """
        if word in self.words:
            del self.words[word]
            # 重新计算最大长度
            if self.words:
                self.max_length = max(len(w) for w in self.words.keys())
            else:
                self.max_length = 0
        else:
            raise KeyError(f"词语不存在: {word}")

    def contains(self, word):
        """
        检查词语是否在词典中

        Args:
            word: 要检查的词语

        Returns:
            bool: 是否存在
        """
        return word in self.words

    def get_frequency(self, word):
        """
        获取词语频率

        Args:
            word: 词语

        Returns:
            int: 词频

        Raises:
            KeyError: 词语不存在
        """
        if word in self.words:
            return self.words[word]
        else:
            raise KeyError(f"词语不存在: {word}")

    def get_max_word_length(self):
        """
        获取词典中最长词的长度

        Returns:
            int: 最长词长度
        """
        return self.max_length

    def get_words(self):
        """
        获取所有词语

        Returns:
            list: 词语列表
        """
        return list(self.words.keys())

    def size(self):
        """
        获取词典大小

        Returns:
            int: 词条数量
        """
        return len(self.words)
