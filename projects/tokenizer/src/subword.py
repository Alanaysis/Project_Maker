"""
子词分词器
支持 BPE（字节对编码）、WordPiece、Unigram
"""

import re
from collections import Counter, defaultdict


class BPETokenizer:
    """BPE（字节对编码）分词器"""

    def __init__(self, vocab_size=1000):
        """
        初始化 BPE 分词器

        Args:
            vocab_size: 词表大小
        """
        self.vocab_size = vocab_size
        self.merges = []  # 合并规则
        self.vocab = {}   # 词表
        self.inverse_vocab = {}

    def train(self, corpus):
        """
        训练 BPE 模型

        Args:
            corpus: 训练语料（字符串列表）

        Examples:
            >>> bpe = BPETokenizer(vocab_size=100)
            >>> bpe.train(["low lower newest wide", "low low low"])
        """
        # 统计词频
        word_freq = Counter()
        for text in corpus:
            words = text.strip().split()
            for word in words:
                word_freq[word] += 1

        # 初始化词表（字符级）
        self.vocab = {}
        char_set = set()
        for word in word_freq:
            for char in word:
                char_set.add(char)

        # 添加基础字符到词表
        for char in sorted(char_set):
            self.vocab[char] = len(self.vocab)

        # 将词分割为字符序列
        splits = {}
        for word in word_freq:
            splits[word] = list(word)

        # 迭代合并
        num_merges = self.vocab_size - len(self.vocab)
        for i in range(num_merges):
            # 统计相邻对的频率
            pair_freq = Counter()
            for word, freq in word_freq.items():
                chars = splits[word]
                for j in range(len(chars) - 1):
                    pair = (chars[j], chars[j + 1])
                    pair_freq[pair] += freq

            if not pair_freq:
                break

            # 找到最频繁的对
            best_pair = max(pair_freq, key=pair_freq.get)
            best_freq = pair_freq[best_pair]

            if best_freq < 2:
                break

            # 合并
            new_token = best_pair[0] + best_pair[1]
            self.merges.append(best_pair)
            self.vocab[new_token] = len(self.vocab)

            # 更新分割
            for word in splits:
                chars = splits[word]
                new_chars = []
                j = 0
                while j < len(chars):
                    if j < len(chars) - 1 and chars[j] == best_pair[0] and chars[j + 1] == best_pair[1]:
                        new_chars.append(new_token)
                        j += 2
                    else:
                        new_chars.append(chars[j])
                        j += 1
                splits[word] = new_chars

        # 构建反向词表
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}

    def tokenize(self, text):
        """
        使用 BPE 进行分词

        Args:
            text: 待分词的文本

        Returns:
            list: 子词列表

        Examples:
            >>> bpe = BPETokenizer(vocab_size=100)
            >>> bpe.train(["low lower newest wide"])
            >>> bpe.tokenize("lower")
            ['low', 'er']
        """
        if not text:
            return []

        words = text.strip().split()
        tokens = []

        for word in words:
            word_tokens = self._tokenize_word(word)
            tokens.extend(word_tokens)

        return tokens

    def _tokenize_word(self, word):
        """对单个词进行 BPE 分词"""
        # 初始化为字符序列
        chars = list(word)

        # 应用合并规则
        for left, right in self.merges:
            new_chars = []
            i = 0
            while i < len(chars):
                if i < len(chars) - 1 and chars[i] == left and chars[i + 1] == right:
                    new_chars.append(left + right)
                    i += 2
                else:
                    new_chars.append(chars[i])
                    i += 1
            chars = new_chars

        return chars

    def save(self, filepath):
        """保存模型"""
        import json
        model = {
            'vocab_size': self.vocab_size,
            'merges': self.merges,
            'vocab': self.vocab
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)

    def load(self, filepath):
        """加载模型"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            model = json.load(f)

        self.vocab_size = model['vocab_size']
        self.merges = [tuple(m) for m in model['merges']]
        self.vocab = model['vocab']
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}


class WordPieceTokenizer:
    """WordPiece 分词器"""

    def __init__(self, vocab_size=1000, unk_token="[UNK]", prefix="##"):
        """
        初始化 WordPiece 分词器

        Args:
            vocab_size: 词表大小
            unk_token: 未知词标记
            prefix: 子词前缀标记
        """
        self.vocab_size = vocab_size
        self.unk_token = unk_token
        self.prefix = prefix
        self.vocab = {}
        self.inverse_vocab = {}

    def train(self, corpus):
        """
        训练 WordPiece 模型

        Args:
            corpus: 训练语料（字符串列表）
        """
        # 统计词频
        word_freq = Counter()
        for text in corpus:
            words = text.strip().split()
            for word in words:
                word_freq[word] += 1

        # 初始化词表（字符级）
        char_set = set()
        for word in word_freq:
            for char in word:
                char_set.add(char)

        # 添加特殊标记和基础字符
        self.vocab[self.unk_token] = len(self.vocab)
        for char in sorted(char_set):
            self.vocab[char] = len(self.vocab)

        # 添加子词前缀字符
        for char in sorted(char_set):
            self.vocab[self.prefix + char] = len(self.vocab)

        # 迭代添加最长子串
        while len(self.vocab) < self.vocab_size:
            # 统计子串频率
            substr_freq = Counter()
            for word, freq in word_freq.items():
                substrings = self._get_substrings(word)
                for substr in substrings:
                    substr_freq[substr] += freq

            if not substr_freq:
                break

            # 找到最高增益的子串
            best_substr = None
            best_gain = -1

            for substr, freq in substr_freq.items():
                if substr not in self.vocab:
                    # 计算增益
                    gain = freq * len(substr)
                    if gain > best_gain:
                        best_gain = gain
                        best_substr = substr

            if best_substr is None:
                break

            self.vocab[best_substr] = len(self.vocab)

        # 构建反向词表
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}

    def _get_substrings(self, word):
        """获取词的所有子串"""
        substrings = []
        n = len(word)

        for length in range(2, n + 1):
            for start in range(n - length + 1):
                substr = word[start:start + length]
                if start > 0:
                    substr = self.prefix + substr
                substrings.append(substr)

        return substrings

    def _tokenize_word(self, word):
        """对单个词进行 WordPiece 分词"""
        n = len(word)
        tokens = []
        start = 0

        while start < n:
            end = n
            found = False

            while start < end:
                substr = word[start:end]
                if start > 0:
                    substr = self.prefix + substr

                if substr in self.vocab:
                    tokens.append(substr)
                    start = end
                    found = True
                    break

                end -= 1

            if not found:
                tokens.append(self.unk_token)
                start += 1

        return tokens

    def tokenize(self, text):
        """
        使用 WordPiece 进行分词

        Args:
            text: 待分词的文本

        Returns:
            list: 子词列表

        Examples:
            >>> wp = WordPieceTokenizer(vocab_size=100)
            >>> wp.train(["unaffable"])
            >>> wp.tokenize("unaffable")
            ['un', '##aff', '##able']
        """
        if not text:
            return []

        words = text.strip().split()
        tokens = []

        for word in words:
            word_tokens = self._tokenize_word(word)
            tokens.extend(word_tokens)

        return tokens

    def _tokenize_word(self, word):
        """对单个词进行 WordPiece 分词"""
        n = len(word)
        tokens = []
        start = 0

        while start < n:
            end = n
            found = False

            while start < end:
                substr = word[start:end]
                if start > 0:
                    substr = self.prefix + substr

                if substr in self.vocab:
                    tokens.append(substr)
                    start = end
                    found = True
                    break

                end -= 1

            if not found:
                tokens.append(self.unk_token)
                start += 1

        return tokens

    def save(self, filepath):
        """保存模型"""
        import json
        model = {
            'vocab_size': self.vocab_size,
            'unk_token': self.unk_token,
            'prefix': self.prefix,
            'vocab': self.vocab
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)

    def load(self, filepath):
        """加载模型"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            model = json.load(f)

        self.vocab_size = model['vocab_size']
        self.unk_token = model['unk_token']
        self.prefix = model['prefix']
        self.vocab = model['vocab']
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}


class UnigramTokenizer:
    """Unigram 语言模型分词器"""

    def __init__(self, vocab_size=1000):
        """
        初始化 Unigram 分词器

        Args:
            vocab_size: 词表大小
        """
        self.vocab_size = vocab_size
        self.vocab = {}  # {token: log_prob}
        self.inverse_vocab = {}

    def train(self, corpus, num_iterations=10):
        """
        训练 Unigram 模型

        Args:
            corpus: 训练语料（字符串列表）
            num_iterations: 迭代次数
        """
        # 统计词频
        word_freq = Counter()
        for text in corpus:
            words = text.strip().split()
            for word in words:
                word_freq[word] += 1

        # 初始化候选词表（所有子串）
        candidate_vocab = Counter()
        for word, freq in word_freq.items():
            n = len(word)
            for length in range(1, n + 1):
                for start in range(n - length + 1):
                    substr = word[start:start + length]
                    candidate_vocab[substr] += freq

        # 保留高频词
        total_freq = sum(candidate_vocab.values())
        self.vocab = {}
        for token, freq in candidate_vocab.most_common(self.vocab_size * 2):
            self.vocab[token] = freq / total_freq

        # EM 算法迭代
        for iteration in range(num_iterations):
            # E 步：计算每个词的最优分割
            segment_counts = Counter()
            for word, freq in word_freq.items():
                best_segment = self._viterbi_segment(word)
                for token in best_segment:
                    segment_counts[token] += freq

            # M 步：更新概率
            total_count = sum(segment_counts.values())
            if total_count == 0:
                break

            new_vocab = {}
            for token, count in segment_counts.items():
                new_vocab[token] = count / total_count

            # 修剪低概率词
            if len(new_vocab) > self.vocab_size:
                sorted_vocab = sorted(new_vocab.items(), key=lambda x: x[1], reverse=True)
                new_vocab = dict(sorted_vocab[:self.vocab_size])

            self.vocab = new_vocab

        # 转换为对数概率
        import math
        for token in self.vocab:
            self.vocab[token] = math.log(self.vocab[token])

        # 构建反向词表
        self.inverse_vocab = {i: token for i, token in enumerate(self.vocab.keys())}

    def _viterbi_segment(self, word):
        """维特比算法找到最优分割"""
        n = len(word)
        # dp[i] = (最佳概率, 最佳分割)
        dp = [(-float('inf'), []) for _ in range(n + 1)]
        dp[0] = (0.0, [])

        import math
        for i in range(1, n + 1):
            for j in range(i):
                substr = word[j:i]
                if substr in self.vocab:
                    prob = dp[j][0] + self.vocab[substr]
                    if prob > dp[i][0]:
                        dp[i] = (prob, dp[j][1] + [substr])

        return dp[n][1] if dp[n][1] else [word]

    def tokenize(self, text):
        """
        使用 Unigram 进行分词

        Args:
            text: 待分词的文本

        Returns:
            list: 子词列表

        Examples:
            >>> uni = UnigramTokenizer(vocab_size=100)
            >>> uni.train(["low lower newest wide"])
            >>> uni.tokenize("lower")
            ['low', 'er']
        """
        if not text:
            return []

        words = text.strip().split()
        tokens = []

        for word in words:
            word_tokens = self._viterbi_segment(word)
            tokens.extend(word_tokens)

        return tokens

    def save(self, filepath):
        """保存模型"""
        import json
        model = {
            'vocab_size': self.vocab_size,
            'vocab': self.vocab
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)

    def load(self, filepath):
        """加载模型"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            model = json.load(f)

        self.vocab_size = model['vocab_size']
        self.vocab = model['vocab']
        self.inverse_vocab = {i: token for i, token in enumerate(self.vocab.keys())}
