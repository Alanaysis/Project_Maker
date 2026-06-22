"""语言模型模块 - 提供完整的语言模型接口"""

import math
from typing import List, Dict, Optional, Tuple
from .vocabulary import Vocabulary
from .ngram import NGramModel


class LanguageModel:
    """
    完整的语言模型

    整合词汇表、N-gram 模型，提供统一的训练、评估和生成接口。

    使用示例:

        lm = LanguageModel(n=3)
        lm.train(["hello world", "hello there"])
        text = lm.generate("hello")
        ppl = lm.perplexity(["hello world"])
    """

    def __init__(
        self,
        n: int = 3,
        smoothing: str = "add_k",
        k: float = 1.0,
        min_freq: int = 1,
    ):
        """
        初始化语言模型

        Args:
            n: N-gram 的 N 值
            smoothing: 平滑方法
            k: Add-k 平滑的 k 值
            min_freq: 最小词频
        """
        self.n = n
        self.vocabulary = Vocabulary(min_freq=min_freq)
        self.ngram_model = NGramModel(n=n, smoothing=smoothing, k=k)
        self._corpus_raw: List[str] = []

    def train(self, texts: List[str]) -> "LanguageModel":
        """
        训练语言模型

        Args:
            texts: 原始文本列表

        Returns:
            self，支持链式调用
        """
        self._corpus_raw = texts

        # 分词
        tokenized = [Vocabulary.tokenize(text) for text in texts]

        # 构建词汇表
        self.vocabulary.build(tokenized)

        # 训练 N-gram 模型
        self.ngram_model.train(tokenized)

        return self

    def probability(self, text: str) -> float:
        """
        计算文本的对数概率

        Args:
            text: 输入文本

        Returns:
            对数概率
        """
        tokens = Vocabulary.tokenize(text)
        return self.ngram_model.sentence_probability(tokens)

    def perplexity(self, texts: List[str]) -> float:
        """
        计算困惑度

        Args:
            texts: 文本列表

        Returns:
            困惑度
        """
        tokenized = [Vocabulary.tokenize(text) for text in texts]
        return self.ngram_model.perplexity(tokenized)

    def generate(
        self,
        seed: Optional[str] = None,
        max_length: int = 50,
        temperature: float = 1.0,
    ) -> str:
        """
        生成文本

        Args:
            seed: 起始词
            max_length: 最大长度
            temperature: 温度参数

        Returns:
            生成的文本
        """
        tokens = self.ngram_model.generate(
            max_length=max_length,
            temperature=temperature,
            seed=seed,
        )
        return " ".join(tokens)

    def generate_greedy(
        self,
        seed: Optional[str] = None,
        max_length: int = 50,
    ) -> str:
        """
        贪婪生成文本

        Args:
            seed: 起始词
            max_length: 最大长度

        Returns:
            生成的文本
        """
        tokens = self.ngram_model.generate_greedy(
            max_length=max_length,
            seed=seed,
        )
        return " ".join(tokens)

    def top_words(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        获取最常见的词

        Args:
            n: 返回数量

        Returns:
            [(word, count), ...] 列表
        """
        freqs = self.vocabulary._token_freq
        return freqs.most_common(n)

    def top_ngrams(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        获取最常见的 N-gram

        Args:
            n: 返回数量

        Returns:
            [(ngram_str, count), ...] 列表
        """
        raw = self.ngram_model.top_ngrams(n)
        return [(" ".join(gram), count) for gram, count in raw]

    def evaluate(self, test_texts: List[str]) -> Dict[str, float]:
        """
        全面评估模型

        Args:
            test_texts: 测试文本列表

        Returns:
            评估指标字典
        """
        ppl = self.perplexity(test_texts)

        # 计算平均句子长度
        total_words = 0
        for text in test_texts:
            total_words += len(Vocabulary.tokenize(text))
        avg_len = total_words / len(test_texts) if test_texts else 0

        # 计算词汇覆盖率
        test_tokens = set()
        for text in test_texts:
            test_tokens.update(Vocabulary.tokenize(text))
        train_vocab = self.ngram_model.get_vocab()
        covered = test_tokens & train_vocab
        coverage = len(covered) / len(test_tokens) if test_tokens else 0

        return {
            "perplexity": ppl,
            "avg_sentence_length": avg_len,
            "vocab_coverage": coverage,
            "test_vocab_size": len(test_tokens),
            "train_vocab_size": len(train_vocab),
        }

    def __repr__(self) -> str:
        return (
            f"LanguageModel(n={self.n}, "
            f"vocab_size={self.vocabulary.size}, "
            f"ngram_model={self.ngram_model})"
        )
