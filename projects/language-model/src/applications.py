"""应用模块 - 基于语言模型的实际应用"""

import math
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict


class TextGenerator:
    """
    文本生成器

    基于语言模型生成文本，支持多种生成策略。
    """

    def __init__(self, lm):
        """
        Args:
            lm: 语言模型实例 (需要有 generate 和 probability 方法)
        """
        self.lm = lm

    def generate(self, seed: Optional[str] = None, max_length: int = 50,
                 temperature: float = 1.0) -> str:
        """
        生成文本

        Args:
            seed: 起始词
            max_length: 最大长度
            temperature: 温度参数

        Returns:
            生成的文本
        """
        return self.lm.generate(seed=seed, max_length=max_length,
                                temperature=temperature)

    def generate_diverse(self, seed: Optional[str] = None,
                         num_samples: int = 5, max_length: int = 20,
                         temperature: float = 1.0) -> List[str]:
        """
        生成多个不同的文本样本

        Args:
            seed: 起始词
            num_samples: 生成数量
            max_length: 最大长度
            temperature: 温度

        Returns:
            生成的文本列表
        """
        results = []
        for _ in range(num_samples):
            text = self.lm.generate(seed=seed, max_length=max_length,
                                    temperature=temperature)
            results.append(text)
        return results

    def generate_with_prefix(self, prefix: str, max_length: int = 50,
                             temperature: float = 1.0) -> str:
        """
        给定前缀，续写文本

        Args:
            prefix: 前缀文本
            max_length: 最大续写长度
            temperature: 温度

        Returns:
            完整文本（前缀 + 续写）
        """
        tokens = prefix.lower().split()
        if not tokens:
            return self.lm.generate(max_length=max_length,
                                    temperature=temperature)

        # 使用最后一个词作为种子
        seed = tokens[-1]
        generated = self.lm.generate(seed=seed, max_length=max_length,
                                     temperature=temperature)

        # 拼接前缀（去掉最后一个词，因为它是种子）
        prefix_str = " ".join(tokens[:-1])
        if prefix_str:
            return f"{prefix_str} {generated}"
        return generated


class SpellingCorrector:
    """
    拼写纠错器

    基于语言模型和编辑距离的拼写纠错。

    算法:
    1. 生成候选词（编辑距离为 1 或 2 的词）
    2. 使用语言模型对候选词排序
    3. 选择概率最高的候选词
    """

    def __init__(self, lm, vocab: Optional[Set[str]] = None):
        """
        Args:
            lm: 语言模型实例
            vocab: 词汇表集合，如果为 None 则从模型中获取
        """
        self.lm = lm
        if vocab is not None:
            self._vocab = vocab
        elif hasattr(lm, 'ngram_model'):
            self._vocab = lm.ngram_model.get_vocab()
        elif hasattr(lm, 'vocabulary'):
            self._vocab = set()
            for i in range(lm.vocabulary.size):
                token = lm.vocabulary.get_token(i)
                if token not in ('<PAD>', '<UNK>', '<BOS>', '<EOS>'):
                    self._vocab.add(token)
        else:
            self._vocab = set()

    @staticmethod
    def _edits1(word: str) -> Set[str]:
        """
        生成编辑距离为 1 的候选词

        操作: 删除、交换、替换、插入

        Args:
            word: 输入词

        Returns:
            编辑距离为 1 的候选词集合
        """
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]

        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]

        return set(deletes + transposes + replaces + inserts)

    @staticmethod
    def _edits2(word: str) -> Set[str]:
        """
        生成编辑距离为 2 的候选词

        Args:
            word: 输入词

        Returns:
            编辑距离为 2 的候选词集合
        """
        return set(
            e2 for e1 in SpellingCorrector._edits1(word)
            for e2 in SpellingCorrector._edits1(e1)
        )

    def _candidates(self, word: str) -> Set[str]:
        """
        生成候选词

        优先返回已知词，然后是编辑距离 1，最后是编辑距离 2。

        Args:
            word: 输入词

        Returns:
            候选词集合
        """
        known = {w for w in [word] if w in self._vocab}
        edits1 = {w for w in self._edits1(word) if w in self._vocab}
        edits2 = {w for w in self._edits2(word) if w in self._vocab}

        if known:
            return known
        elif edits1:
            return edits1
        elif edits2:
            return edits2
        else:
            return {word}  # 没有候选词，返回原词

    def correct_word(self, word: str, context: Optional[str] = None) -> str:
        """
        纠正单个词

        Args:
            word: 待纠正的词
            context: 上下文文本（可选，用于利用语言模型）

        Returns:
            纠正后的词
        """
        word_lower = word.lower()
        candidates = self._candidates(word_lower)

        if len(candidates) == 1:
            return list(candidates)[0]

        if context and hasattr(self.lm, 'probability'):
            # 使用语言模型对候选词排序
            best_word = word_lower
            best_score = float('-inf')

            for candidate in candidates:
                test_text = f"{context} {candidate}"
                try:
                    score = self.lm.probability(test_text)
                    if score > best_score:
                        best_score = score
                        best_word = candidate
                except Exception:
                    continue

            return best_word
        else:
            # 没有上下文时，返回编辑距离最小的已知词
            return min(candidates, key=lambda w: (
                0 if w == word_lower else
                1 if w in self._edits1(word_lower) else 2
            ))

    def correct_text(self, text: str) -> str:
        """
        纠正整段文本

        Args:
            text: 待纠正的文本

        Returns:
            纠正后的文本
        """
        words = text.lower().split()
        corrected = []

        for i, word in enumerate(words):
            # 使用前面的词作为上下文
            context = " ".join(corrected[-3:]) if corrected else None
            corrected_word = self.correct_word(word, context)
            corrected.append(corrected_word)

        return " ".join(corrected)

    def suggest(self, word: str, n: int = 5) -> List[str]:
        """
        提供拼写建议

        Args:
            word: 输入词
            n: 返回建议数量

        Returns:
            建议列表（按概率排序）
        """
        candidates = self._candidates(word.lower())
        scored = []

        for candidate in candidates:
            if hasattr(self.lm, 'probability'):
                try:
                    score = self.lm.probability(candidate)
                except Exception:
                    score = float('-inf')
            else:
                # 按编辑距离排序
                if candidate == word.lower():
                    score = 0
                elif candidate in self._edits1(word.lower()):
                    score = -1
                else:
                    score = -2

            scored.append((candidate, score))

        scored.sort(key=lambda x: -x[1])
        return [w for w, _ in scored[:n]]


class InputMethod:
    """
    输入法

    基于语言模型的拼音/字母输入法。
    给定输入序列，预测最可能的下一个词或完成当前词。

    工作流程:
    1. 用户输入前缀
    2. 系统基于语言模型预测候选词
    3. 返回按概率排序的候选列表
    """

    def __init__(self, lm, vocab: Optional[Set[str]] = None):
        """
        Args:
            lm: 语言模型实例
            vocab: 词汇表集合
        """
        self.lm = lm
        if vocab is not None:
            self._vocab = vocab
        elif hasattr(lm, 'ngram_model'):
            self._vocab = lm.ngram_model.get_vocab()
        elif hasattr(lm, 'vocabulary'):
            self._vocab = set()
            for i in range(lm.vocabulary.size):
                token = lm.vocabulary.get_token(i)
                if token not in ('<PAD>', '<UNK>', '<BOS>', '<EOS>'):
                    self._vocab.add(token)
        else:
            self._vocab = set()

    def complete_prefix(self, prefix: str, context: Optional[str] = None,
                        n: int = 10) -> List[Tuple[str, float]]:
        """
        前缀补全

        给定前缀，返回以该前缀开头的候选词，按概率排序。

        Args:
            prefix: 输入前缀
            context: 上下文文本
            n: 返回候选数量

        Returns:
            [(候选词, 概率), ...] 列表
        """
        prefix_lower = prefix.lower()

        # 找到所有以 prefix 开头的词
        candidates = [w for w in self._vocab if w.startswith(prefix_lower)]

        if not candidates:
            return []

        # 使用语言模型对候选词评分
        scored = []
        for candidate in candidates:
            if context and hasattr(self.lm, 'probability'):
                try:
                    test_text = f"{context} {candidate}"
                    score = self.lm.probability(test_text)
                except Exception:
                    score = float('-inf')
            elif hasattr(self.lm, 'probability'):
                try:
                    score = self.lm.probability(candidate)
                except Exception:
                    score = float('-inf')
            else:
                score = 0.0

            scored.append((candidate, score))

        # 按概率排序
        scored.sort(key=lambda x: -x[1])

        return scored[:n]

    def predict_next_words(self, context: str, n: int = 10) -> List[Tuple[str, float]]:
        """
        预测下一个词

        给定上下文，预测最可能出现的下一个词。

        Args:
            context: 上下文文本
            n: 返回候选数量

        Returns:
            [(候选词, 概率), ...] 列表
        """
        if not hasattr(self.lm, 'ngram_model'):
            return []

        ngram_model = self.lm.ngram_model
        context_tokens = context.lower().split()

        # 获取最近的上下文
        ctx_len = ngram_model.n - 1
        if len(context_tokens) >= ctx_len:
            recent_context = tuple(context_tokens[-ctx_len:])
        else:
            padding = ["<BOS>"] * (ctx_len - len(context_tokens))
            recent_context = tuple(padding + context_tokens)

        # 计算所有词的条件概率
        scored = []
        for word in self._vocab:
            ngram = recent_context + (word,)
            try:
                prob = ngram_model.probability(ngram)
                if prob > 0:
                    scored.append((word, prob))
            except Exception:
                continue

        # 按概率排序
        scored.sort(key=lambda x: -x[1])

        return scored[:n]

    def get_candidates(self, input_text: str, context: Optional[str] = None,
                       n: int = 10) -> List[Tuple[str, float]]:
        """
        获取输入法候选词

        综合考虑前缀匹配和语言模型概率。

        Args:
            input_text: 用户输入
            context: 上下文
            n: 候选数量

        Returns:
            [(候选词, 分数), ...] 列表
        """
        # 前缀补全
        prefix_candidates = self.complete_prefix(input_text, context, n=n * 2)

        if prefix_candidates:
            return prefix_candidates[:n]

        # 如果没有前缀匹配，尝试预测下一个词
        if context:
            return self.predict_next_words(context, n=n)

        return []
