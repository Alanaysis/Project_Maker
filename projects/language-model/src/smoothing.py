"""平滑技术模块 - 实现多种 N-gram 平滑方法"""

import math
from typing import Dict, Tuple, Set
from collections import Counter


class LaplaceSmoothing:
    """
    拉普拉斯平滑 (Add-k Smoothing)

    最简单的平滑方法，给每个 N-gram 计数加上常数 k。

    公式: P(w|c) = (C(c,w) + k) / (C(c) + k * V)

    当 k=1 时即为拉普拉斯平滑。
    """

    def __init__(self, k: float = 1.0):
        """
        Args:
            k: 平滑参数，k=1 为标准拉普拉斯平滑
        """
        if k <= 0:
            raise ValueError("k 必须为正数")
        self.k = k

    def probability(
        self,
        ngram_count: int,
        context_count: int,
        vocab_size: int,
    ) -> float:
        """
        计算平滑后的条件概率

        Args:
            ngram_count: N-gram 出现次数
            context_count: 上下文出现次数
            vocab_size: 词汇表大小

        Returns:
            平滑后的概率
        """
        denominator = context_count + self.k * vocab_size
        if denominator == 0:
            return 0.0
        return (ngram_count + self.k) / denominator

    def __repr__(self) -> str:
        return f"LaplaceSmoothing(k={self.k})"


class GoodTuringSmoothing:
    """
    Good-Turing 平滑

    核心思想：用出现 r+1 次的 N-gram 数量来重新估计出现 r 次的 N-gram 概率。

    调整后的计数: r* = (r+1) * N_{r+1} / N_r

    其中 N_r 是出现恰好 r 次的 N-gram 的数量。

    对于高频计数 (r > k_threshold)，不做调整以避免数据稀疏导致的不稳定。
    """

    def __init__(self, k_threshold: int = 5):
        """
        Args:
            k_threshold: 高频阈值，计数超过此值的 N-gram 不做 Good-Turing 调整
        """
        if k_threshold < 1:
            raise ValueError("k_threshold 必须为正整数")
        self.k_threshold = k_threshold

    def fit(self, ngram_counts: Dict[Tuple[str, ...], int]) -> None:
        """
        从 N-gram 计数中学习频率分布

        Args:
            ngram_counts: N-gram 计数字典
        """
        # N_r: 出现恰好 r 次的 N-gram 数量
        self._freq_of_freq: Counter = Counter()
        for count in ngram_counts.values():
            self._freq_of_freq[count] += 1

        # 总 N-gram 数量
        self._total_ngrams = sum(ngram_counts.values())

        # 计算调整后的计数 r*
        self._adjusted_counts: Dict[int, float] = {}
        for r in range(0, self.k_threshold + 1):
            n_r = self._freq_of_freq.get(r, 0)
            n_r_plus_1 = self._freq_of_freq.get(r + 1, 0)

            if n_r == 0:
                self._adjusted_counts[r] = 0.0
            else:
                # r* = (r+1) * N_{r+1} / N_r
                self._adjusted_counts[r] = (r + 1) * n_r_plus_1 / n_r

    def probability(
        self,
        ngram_count: int,
        context_count: int,
        vocab_size: int,
    ) -> float:
        """
        计算 Good-Turing 调整后的条件概率

        对于 P(w|c) = C*(c,w) / C(c)

        Args:
            ngram_count: N-gram 出现次数
            context_count: 上下文出现次数
            vocab_size: 词汇表大小 (未使用，保持接口一致)

        Returns:
            调整后的概率
        """
        if not hasattr(self, '_adjusted_counts'):
            raise RuntimeError("请先调用 fit() 方法")

        if context_count == 0:
            return 0.0

        if ngram_count <= self.k_threshold:
            adjusted = self._adjusted_counts.get(ngram_count, 0.0)
        else:
            adjusted = ngram_count

        return adjusted / context_count

    def get_adjusted_count(self, r: int) -> float:
        """获取原始计数 r 的调整后计数 r*"""
        if not hasattr(self, '_adjusted_counts'):
            raise RuntimeError("请先调用 fit() 方法")
        if r <= self.k_threshold:
            return self._adjusted_counts.get(r, 0.0)
        return r

    @property
    def freq_of_freq(self) -> Counter:
        """获取频率分布 N_r"""
        if not hasattr(self, '_freq_of_freq'):
            raise RuntimeError("请先调用 fit() 方法")
        return self._freq_of_freq.copy()

    def __repr__(self) -> str:
        return f"GoodTuringSmoothing(k_threshold={self.k_threshold})"


class KneserNeySmoothing:
    """
    Kneser-Ney 平滑

    目前 N-gram 模型中最有效的平滑方法之一。

    核心思想：低阶分布不是基于词频，而是基于词的"续接能力"——
    一个词的低阶概率正比于它能跟在多少种不同上下文后面。

    公式（以 Bigram 为例）:
    P_KN(w|w_{i-1}) = max(C(w_{i-1}, w) - d, 0) / C(w_{i-1}) + lambda(w_{i-1}) * P_KN(w)

    其中:
    - d 是折扣值 (通常 0.75)
    - lambda(w_{i-1}) 是归一化常数
    - P_KN(w) 是低阶（续接）概率: |{v: C(v,w)>0}| / |{(v',w'): C(v',w')>0}|
    """

    def __init__(self, discount: float = 0.75):
        """
        Args:
            discount: 折扣值 d，通常取 0.75
        """
        if not (0 < discount < 1):
            raise ValueError("discount 必须在 (0, 1) 之间")
        self.discount = discount

    def fit(
        self,
        ngram_counts: Dict[Tuple[str, ...], int],
        context_counts: Dict[Tuple[str, ...], int],
        vocab: Set[str],
    ) -> None:
        """
        从 N-gram 计数中学习参数

        Args:
            ngram_counts: N-gram 计数 {(w1,...,wn): count}
            context_counts: 上下文计数 {(w1,...,w_{n-1}): count}
            vocab: 词汇表
        """
        self._ngram_counts = ngram_counts
        self._context_counts = context_counts
        self._vocab = vocab

        # 计算每个上下文有多少种不同的后续词 |{w: C(context, w) > 0}|
        self._continuation_counts: Counter = Counter()
        for ngram in ngram_counts:
            context = ngram[:-1]
            self._continuation_counts[context] += 1

        # 计算低阶分布的分子和分母
        # 分子: |{v: C(v, w) > 0}| 对每个 w
        self._word_predecessor_count: Counter = Counter()
        # 同时按 w 统计 {w: {v1, v2, ...}}
        word_predecessors: Dict[str, set] = {}
        for ngram in ngram_counts:
            if len(ngram) >= 2:
                w = ngram[-1]
                v = ngram[-2]
                if w not in word_predecessors:
                    word_predecessors[w] = set()
                word_predecessors[w].add(v)

        for w, predecessors in word_predecessors.items():
            self._word_predecessor_count[w] = len(predecessors)

        # 分母: |{(v', w'): C(v', w') > 0}|
        self._total_continuations = len(ngram_counts)

    def probability(
        self,
        ngram: Tuple[str, ...],
    ) -> float:
        """
        计算 Kneser-Ney 平滑后的条件概率

        Args:
            ngram: N-gram 元组 (w1, ..., wN)

        Returns:
            平滑后的条件概率 P(wN | w1, ..., w_{N-1})
        """
        if not hasattr(self, '_ngram_counts'):
            raise RuntimeError("请先调用 fit() 方法")

        context = ngram[:-1]
        word = ngram[-1]

        ngram_count = self._ngram_counts.get(ngram, 0)
        context_count = self._context_counts.get(context, 0)

        if context_count == 0:
            # 上下文未见过，使用低阶分布
            return self._lower_order_prob(word)

        # 折扣后的概率
        discounted_count = max(ngram_count - self.discount, 0)
        first_term = discounted_count / context_count

        # 归一化常数 lambda
        num_continuations = self._continuation_counts.get(context, 0)
        lambda_weight = (self.discount / context_count) * num_continuations

        # 低阶概率（续接概率）
        lower_prob = self._lower_order_prob(word)

        return first_term + lambda_weight * lower_prob

    def _lower_order_prob(self, word: str) -> float:
        """
        计算低阶（续接）概率

        P_KN(w) = |{v: C(v,w)>0}| / |{(v',w'): C(v',w')>0}|

        Args:
            word: 目标词

        Returns:
            续接概率
        """
        if self._total_continuations == 0:
            return 0.0
        return self._word_predecessor_count.get(word, 0) / self._total_continuations

    def __repr__(self) -> str:
        return f"KneserNeySmoothing(discount={self.discount})"
