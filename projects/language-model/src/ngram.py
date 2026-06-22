"""N-gram 模型模块 - 核心统计模型"""

import math
import random
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict


class NGramModel:
    """
    N-gram 语言模型

    实现 N-gram 统计、概率计算和文本生成。
    支持 1-gram (unigram) 到任意 N 的 N-gram 模型。
    """

    def __init__(self, n: int = 3, smoothing: str = "add_k", k: float = 1.0):
        """
        初始化 N-gram 模型

        Args:
            n: N-gram 的 N 值
            smoothing: 平滑方法 ("add_k", "kneser_ney_simple", "none")
            k: Add-k 平滑的 k 值
        """
        if n < 1:
            raise ValueError("n 必须为正整数")

        self.n = n
        self.smoothing = smoothing
        self.k = k

        # N-gram 计数: {ngram_tuple: count}
        self._ngram_counts: Dict[Tuple[str, ...], int] = Counter()

        # (N-1)-gram 计数（用于计算条件概率）
        self._context_counts: Dict[Tuple[str, ...], int] = Counter()

        # 词汇表
        self._vocab: Set[str] = set()

        # 是否已训练
        self._trained = False

    @property
    def vocab_size(self) -> int:
        """词汇表大小"""
        return len(self._vocab)

    def train(self, corpus: List[List[str]]) -> "NGramModel":
        """
        训练 N-gram 模型

        Args:
            corpus: 分词后的语料库，每个元素是一个词列表（句子）

        Returns:
            self，支持链式调用
        """
        self._ngram_counts = Counter()
        self._context_counts = Counter()
        self._vocab = set()

        for sentence in corpus:
            # 收集词汇
            self._vocab.update(sentence)

            # 添加开始和结束标记
            padded = ["<BOS>"] * (self.n - 1) + sentence + ["<EOS>"]

            # 统计 N-gram
            for i in range(len(padded) - self.n + 1):
                ngram = tuple(padded[i:i + self.n])
                context = ngram[:-1]
                self._ngram_counts[ngram] += 1
                self._context_counts[context] += 1

        self._trained = True
        return self

    def probability(self, ngram: Tuple[str, ...]) -> float:
        """
        计算 N-gram 的条件概率 P(w_n | w_1, ..., w_{n-1})

        Args:
            ngram: N-gram 元组

        Returns:
            条件概率
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练，请先调用 train() 方法")

        context = ngram[:-1]
        ngram_count = self._ngram_counts.get(ngram, 0)
        context_count = self._context_counts.get(context, 0)

        if self.smoothing == "none":
            if context_count == 0:
                return 0.0
            return ngram_count / context_count

        elif self.smoothing == "add_k":
            # Add-k 平滑
            denominator = context_count + self.k * self.vocab_size
            if denominator == 0:
                return 0.0
            return (ngram_count + self.k) / denominator

        else:
            raise ValueError(f"未知的平滑方法: {self.smoothing}")

    def sentence_probability(self, sentence: List[str]) -> float:
        """
        计算整个句子的概率（对数空间）

        P(sentence) = P(w1) * P(w2|w1) * ... * P(wn|w1,...,w_{n-1})

        Args:
            sentence: 分词后的句子

        Returns:
            句子的对数概率
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练")

        padded = ["<BOS>"] * (self.n - 1) + sentence + ["<EOS>"]
        log_prob = 0.0

        for i in range(self.n - 1, len(padded)):
            ngram = tuple(padded[i - self.n + 1:i + 1])
            prob = self.probability(ngram)

            if prob <= 0:
                return float('-inf')

            log_prob += math.log(prob)

        return log_prob

    def perplexity(self, corpus: List[List[str]]) -> float:
        """
        计算困惑度 (Perplexity)

        PPL = exp(-1/N * sum(log P(w_i | context)))

        Args:
            corpus: 分词后的语料库

        Returns:
            困惑度
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练")

        total_log_prob = 0.0
        total_words = 0

        for sentence in corpus:
            padded = ["<BOS>"] * (self.n - 1) + sentence + ["<EOS>"]

            for i in range(self.n - 1, len(padded)):
                ngram = tuple(padded[i - self.n + 1:i + 1])
                prob = self.probability(ngram)

                if prob <= 0:
                    return float('inf')

                total_log_prob += math.log(prob)
                total_words += 1

        if total_words == 0:
            return float('inf')

        avg_log_prob = total_log_prob / total_words
        return math.exp(-avg_log_prob)

    def generate(
        self,
        max_length: int = 50,
        temperature: float = 1.0,
        seed: Optional[str] = None,
    ) -> List[str]:
        """
        生成文本

        Args:
            max_length: 最大生成长度
            temperature: 温度参数，控制随机性
                - temperature < 1.0: 更确定性
                - temperature = 1.0: 标准采样
                - temperature > 1.0: 更随机
            seed: 可选的起始词

        Returns:
            生成的词列表
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练")

        if temperature <= 0:
            raise ValueError("temperature 必须为正数")

        # 初始化上下文和生成结果
        if seed is not None:
            seed_lower = seed.lower()
            context = ["<BOS>"] * (self.n - 2) + [seed_lower]
            generated = [seed_lower]
        else:
            context = ["<BOS>"] * (self.n - 1)
            generated = []

        for _ in range(max_length):
            # 获取可能的下一个词及其概率
            candidates = self._get_next_word_probs(tuple(context[-(self.n - 1):]))

            if not candidates:
                break

            # 应用温度
            if temperature != 1.0:
                candidates = self._apply_temperature(candidates, temperature)

            # 采样
            next_word = self._sample(candidates)

            if next_word == "<EOS>":
                break

            generated.append(next_word)
            context.append(next_word)

        return generated

    def generate_greedy(
        self,
        max_length: int = 50,
        seed: Optional[str] = None,
    ) -> List[str]:
        """
        贪婪生成（总是选择概率最高的词）

        Args:
            max_length: 最大生成长度
            seed: 可选的起始词

        Returns:
            生成的词列表
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练")

        # 初始化上下文和生成结果
        if seed is not None:
            seed_lower = seed.lower()
            context = ["<BOS>"] * (self.n - 2) + [seed_lower]
            generated = [seed_lower]
        else:
            context = ["<BOS>"] * (self.n - 1)
            generated = []

        for _ in range(max_length):
            candidates = self._get_next_word_probs(tuple(context[-(self.n - 1):]))

            if not candidates:
                break

            # 选择概率最高的词
            next_word = max(candidates, key=candidates.get)

            if next_word == "<EOS>":
                break

            generated.append(next_word)
            context.append(next_word)

        return generated

    def _get_next_word_probs(self, context: Tuple[str, ...]) -> Dict[str, float]:
        """
        获取给定上下文下所有可能下一个词的概率

        Args:
            context: 上下文元组

        Returns:
            {word: probability} 字典
        """
        probs = {}
        for word in self._vocab:
            ngram = context + (word,)
            prob = self.probability(ngram)
            if prob > 0:
                probs[word] = prob

        # 也考虑 <EOS>
        eos_ngram = context + ("<EOS>",)
        eos_prob = self.probability(eos_ngram)
        if eos_prob > 0:
            probs["<EOS>"] = eos_prob

        return probs

    @staticmethod
    def _apply_temperature(
        probs: Dict[str, float], temperature: float
    ) -> Dict[str, float]:
        """
        应用温度参数

        Args:
            probs: 原始概率字典
            temperature: 温度参数

        Returns:
            温度调整后的概率字典
        """
        # 在对数空间中应用温度
        import math
        adjusted = {}
        for word, prob in probs.items():
            adjusted[word] = math.log(prob) / temperature

        # 转换回概率空间并归一化
        max_log = max(adjusted.values())
        total = 0.0
        for word in adjusted:
            adjusted[word] = math.exp(adjusted[word] - max_log)
            total += adjusted[word]

        for word in adjusted:
            adjusted[word] /= total

        return adjusted

    @staticmethod
    def _sample(probs: Dict[str, float]) -> str:
        """
        根据概率分布采样

        Args:
            probs: {word: probability} 字典

        Returns:
            采样结果
        """
        words = list(probs.keys())
        weights = list(probs.values())

        # 归一化
        total = sum(weights)
        weights = [w / total for w in weights]

        # 累积分布采样
        r = random.random()
        cumulative = 0.0
        for word, weight in zip(words, weights):
            cumulative += weight
            if r <= cumulative:
                return word

        return words[-1]

    def get_ngram_count(self, ngram: Tuple[str, ...]) -> int:
        """获取 N-gram 的计数"""
        return self._ngram_counts.get(ngram, 0)

    def get_context_count(self, context: Tuple[str, ...]) -> int:
        """获取上下文的计数"""
        return self._context_counts.get(context, 0)

    def get_vocab(self) -> Set[str]:
        """获取词汇表"""
        return self._vocab.copy()

    def top_ngrams(self, n: int = 10) -> List[Tuple[Tuple[str, ...], int]]:
        """
        获取最常见的 N-gram

        Args:
            n: 返回数量

        Returns:
            [(ngram, count), ...] 列表
        """
        return self._ngram_counts.most_common(n)

    def __repr__(self) -> str:
        return (
            f"NGramModel(n={self.n}, smoothing='{self.smoothing}', "
            f"k={self.k}, vocab_size={self.vocab_size}, "
            f"trained={self._trained})"
        )
