"""
英文分词器
支持空格分词、标点处理、缩写处理
"""

import re


class EnglishTokenizer:
    """英文分词器"""

    # 常见缩写（完整词形式）
    CONTRACTIONS = {
        "can't": ["can", "not"],
        "won't": ["will", "not"],
        "let's": ["let", "us"],
        "he's": ["he", "is"],
        "she's": ["she", "is"],
        "it's": ["it", "is"],
        "that's": ["that", "is"],
        "there's": ["there", "is"],
        "here's": ["here", "is"],
        "what's": ["what", "is"],
        "who's": ["who", "is"],
        "how's": ["how", "is"],
        "i'm": ["I", "am"],
        "you're": ["you", "are"],
        "we're": ["we", "are"],
        "they're": ["they", "are"],
        "i've": ["I", "have"],
        "you've": ["you", "have"],
        "we've": ["we", "have"],
        "they've": ["they", "have"],
        "i'll": ["I", "will"],
        "you'll": ["you", "will"],
        "we'll": ["we", "will"],
        "they'll": ["they", "will"],
        "i'd": ["I", "would"],
        "you'd": ["you", "would"],
        "we'd": ["we", "would"],
        "they'd": ["they", "would"],
        "isn't": ["is", "not"],
        "aren't": ["are", "not"],
        "wasn't": ["was", "not"],
        "weren't": ["were", "not"],
        "hasn't": ["has", "not"],
        "haven't": ["have", "not"],
        "hadn't": ["had", "not"],
        "doesn't": ["does", "not"],
        "don't": ["do", "not"],
        "didn't": ["did", "not"],
        "shouldn't": ["should", "not"],
        "wouldn't": ["would", "not"],
        "couldn't": ["could", "not"],
        "mustn't": ["must", "not"],
    }

    # 后缀缩写（如 n't, 're, 've, 'll, 'd, 'm）
    SUFFIX_CONTRACTIONS = {
        "n't": ["not"],
        "'re": ["are"],
        "'ve": ["have"],
        "'ll": ["will"],
        "'d": ["would"],
        "'m": ["am"],
    }

    # 常见缩略词（不展开）
    ABBREVIATIONS = {
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.",
        "etc.", "i.e.", "e.g.", "vs.", "approx.",
        "dept.", "univ.", "govt.", "est.",
        "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.",
        "sep.", "oct.", "nov.", "dec.",
        "mon.", "tue.", "wed.", "thu.", "fri.", "sat.", "sun.",
    }

    def __init__(self, expand_contractions=True, keep_abbreviations=True):
        """
        初始化英文分词器

        Args:
            expand_contractions: 是否展开缩写（如 don't -> do not）
            keep_abbreviations: 是否保留缩略词（如 Mr.）
        """
        self.expand_contractions = expand_contractions
        self.keep_abbreviations = keep_abbreviations

    def tokenize(self, text):
        """
        对英文文本进行分词

        Args:
            text: 待分词的英文文本

        Returns:
            list: 分词结果列表

        Examples:
            >>> tokenizer = EnglishTokenizer()
            >>> tokenizer.tokenize("Hello, world!")
            ['Hello', ',', 'world', '!']
            >>> tokenizer.tokenize("I can't believe it.")
            ['I', 'can', 'not', 'believe', 'it', '.']
        """
        if not text:
            return []

        # 预处理
        text = text.strip()
        if not text:
            return []

        # 处理缩写
        if self.expand_contractions:
            text = self._expand_contractions(text)

        # 分词
        tokens = self._tokenize(text)

        # 后处理
        tokens = self._post_process(tokens)

        return tokens

    def _expand_contractions(self, text):
        """展开缩写"""
        # 按长度排序，先处理长的缩写
        sorted_contractions = sorted(self.CONTRACTIONS.items(), key=lambda x: len(x[0]), reverse=True)

        for contraction, expansion in sorted_contractions:
            # 使用正则匹配，确保是完整词
            pattern = re.compile(r'\b' + re.escape(contraction) + r'\b', re.IGNORECASE)
            replacement = ' '.join(expansion)
            text = pattern.sub(replacement, text)

        return text

    def _tokenize(self, text):
        """基础分词"""
        tokens = []
        i = 0
        n = len(text)

        while i < n:
            # 跳过空白
            if text[i].isspace():
                i += 1
                continue

            # 处理缩略词（如 Mr.）
            if self.keep_abbreviations:
                abbr_match = self._match_abbreviation(text, i)
                if abbr_match:
                    tokens.append(abbr_match)
                    i += len(abbr_match)
                    continue

            # 处理缩写（如 don't, can't）
            if not self.expand_contractions:
                contraction_match = self._match_contraction(text, i)
                if contraction_match:
                    tokens.append(contraction_match)
                    i += len(contraction_match)
                    continue

            # 处理 URL 和邮箱
            if text[i:i+5].lower() in ('http:', 'https') or text[i:i+4].lower() == 'www.':
                url, end = self._extract_url(text, i)
                tokens.append(url)
                i = end
                continue

            # 处理数字（包括小数、百分比）
            if text[i].isdigit() or (text[i] == '.' and i + 1 < n and text[i + 1].isdigit()):
                num_token, end = self._extract_number(text, i)
                tokens.append(num_token)
                i = end
                continue

            # 处理单词
            if text[i].isalpha() or text[i] == '_':
                word, end = self._extract_word(text, i)
                tokens.append(word)
                i = end
                continue

            # 处理标点和特殊字符
            tokens.append(text[i])
            i += 1

        return tokens

    def _match_contraction(self, text, start):
        """匹配缩写（如 don't, can't）"""
        lower_text = text[start:].lower()

        # 先匹配完整缩写
        for contraction in sorted(self.CONTRACTIONS.keys(), key=len, reverse=True):
            if lower_text.startswith(contraction):
                return text[start:start + len(contraction)]

        return None

    def _match_abbreviation(self, text, start):
        """匹配缩略词"""
        # 尝试匹配已知缩略词
        lower_text = text[start:].lower()
        for abbr in sorted(self.ABBREVIATIONS, key=len, reverse=True):
            if lower_text.startswith(abbr):
                return text[start:start + len(abbr)]

        # 匹配 U.S.A. 类型的缩写
        match = re.match(r'[A-Z]\.(?:[A-Z]\.)*', text[start:])
        if match:
            return match.group()

        return None

    def _extract_number(self, text, start):
        """提取数字"""
        i = start
        n = len(text)

        # 整数部分
        while i < n and text[i].isdigit():
            i += 1

        # 小数部分
        if i < n and text[i] == '.':
            i += 1
            while i < n and text[i].isdigit():
                i += 1

        # 百分比
        if i < n and text[i] == '%':
            i += 1

        # 逗号分隔的数字（如 1,000,000）
        while i < n and text[i] == ',' and i + 1 < n and text[i + 1].isdigit():
            i += 1  # 跳过逗号
            while i < n and text[i].isdigit():
                i += 1

        return text[start:i], i

    def _extract_word(self, text, start):
        """提取单词"""
        i = start
        n = len(text)

        while i < n and (text[i].isalnum() or text[i] in '_-'):
            i += 1

        return text[start:i], i

    def _extract_url(self, text, start):
        """提取 URL"""
        i = start
        n = len(text)

        # URL 字符集
        url_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~:/?#[]@!$&\'()*+,;=%')

        while i < n and not text[i].isspace():
            if text[i] in url_chars:
                i += 1
            else:
                break

        return text[start:i], i

    def _post_process(self, tokens):
        """后处理"""
        result = []

        for token in tokens:
            # 分离末尾标点（但保留缩略词如 Mr.）
            if len(token) > 1 and token[-1] in '.,;:!?':
                # 检查是否是缩略词
                if token.lower() in self.ABBREVIATIONS:
                    result.append(token)
                else:
                    word = token[:-1]
                    punct = token[-1]
                    if word:
                        result.append(word)
                    result.append(punct)
            else:
                result.append(token)

        return result

    def tokenize_words_only(self, text):
        """只返回单词，不包含标点"""
        tokens = self.tokenize(text)
        return [t for t in tokens if any(c.isalnum() for c in t)]

    def sentence_split(self, text):
        """
        分句

        Args:
            text: 待分句的文本

        Returns:
            list: 句子列表
        """
        if not text:
            return []

        # 按句号、问号、感叹号分句
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # 清理空句子
        return [s.strip() for s in sentences if s.strip()]
