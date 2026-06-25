"""评估模块 - 提供语言模型的评估指标"""

import math
from typing import List, Dict, Optional


class EvaluationMetrics:
    """
    语言模型评估指标

    提供困惑度 (Perplexity)、交叉熵 (Cross-Entropy) 等评估指标的计算。
    """

    @staticmethod
    def perplexity(log_probs: List[float]) -> float:
        """
        计算困惑度 (Perplexity)

        PPL = exp(-1/N * sum(log P(w_i | context)))

        困惑度表示模型在每个位置上平均有多少个等可能的选择。
        值越低表示模型越好。

        Args:
            log_probs: 每个词的对数概率列表

        Returns:
            困惑度
        """
        if not log_probs:
            return float('inf')

        avg_log_prob = sum(log_probs) / len(log_probs)
        return math.exp(-avg_log_prob)

    @staticmethod
    def cross_entropy(log_probs: List[float], base: float = 2.0) -> float:
        """
        计算交叉熵 (Cross-Entropy)

        H = -1/N * sum(log_b P(w_i | context))

        交叉熵是困惑度的对数形式，更便于比较不同模型。

        Args:
            log_probs: 每个词的对数概率列表 (自然对数)
            base: 对数底数，默认为 2（单位为 bit），math.e 则为 nat

        Returns:
            交叉熵
        """
        if not log_probs:
            return float('inf')

        if base == math.e:
            avg_log_prob = sum(log_probs) / len(log_probs)
            return -avg_log_prob
        else:
            # 转换底数: log_b(x) = ln(x) / ln(b)
            log_base = math.log(base)
            avg_log_prob = sum(log_probs) / len(log_probs)
            return -avg_log_prob / log_base

    @staticmethod
    def bits_per_character(log_probs: List[float]) -> float:
        """
        计算每字符比特数 (Bits Per Character, BPC)

        BPC = H / log(2) = -1/N * sum(log2 P(w_i | context))

        常用于字符级语言模型评估。

        Args:
            log_probs: 每个字符的自然对数概率列表

        Returns:
            BPC
        """
        return EvaluationMetrics.cross_entropy(log_probs, base=2.0)

    @staticmethod
    def entropy(log_probs: List[float]) -> float:
        """
        计算熵 (Entropy)

        H = -1/N * sum(P(w_i) * log P(w_i))

        在语言模型评估中，通常使用经验熵（即交叉熵的估计）。

        Args:
            log_probs: 每个词的对数概率列表

        Returns:
            熵 (nats)
        """
        if not log_probs:
            return float('inf')

        return -sum(log_probs) / len(log_probs)

    @staticmethod
    def cross_entropy_from_probs(probs: List[float]) -> float:
        """
        从概率值计算交叉熵

        H = -1/N * sum(log P(w_i))

        Args:
            probs: 每个词的概率列表

        Returns:
            交叉熵 (nats)
        """
        if not probs:
            return float('inf')

        eps = 1e-10
        log_probs = [math.log(max(p, eps)) for p in probs]
        return -sum(log_probs) / len(log_probs)

    @staticmethod
    def perplexity_from_probs(probs: List[float]) -> float:
        """
        从概率值计算困惑度

        Args:
            probs: 每个词的概率列表

        Returns:
            困惑度
        """
        if not probs:
            return float('inf')

        eps = 1e-10
        log_probs = [math.log(max(p, eps)) for p in probs]
        avg_log_prob = sum(log_probs) / len(log_probs)
        return math.exp(-avg_log_prob)

    @staticmethod
    def word_error_rate(predicted: List[str], reference: List[str]) -> float:
        """
        计算词错误率 (Word Error Rate, WER)

        WER = (S + D + I) / N

        其中:
        - S: 替换数
        - D: 删除数
        - I: 插入数
        - N: 参考序列长度

        使用编辑距离计算。

        Args:
            predicted: 预测词序列
            reference: 参考词序列

        Returns:
            词错误率
        """
        n = len(reference)
        m = len(predicted)

        if n == 0:
            return 0.0 if m == 0 else 1.0

        # 动态规划计算编辑距离
        dp = [[0] * (m + 1) for _ in range(n + 1)]

        for i in range(n + 1):
            dp[i][0] = i
        for j in range(m + 1):
            dp[0][j] = j

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if reference[i - 1] == predicted[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j] + 1,     # 删除
                        dp[i][j - 1] + 1,     # 插入
                        dp[i - 1][j - 1] + 1, # 替换
                    )

        return dp[n][m] / n

    @staticmethod
    def bleu_score(
        predicted: List[str],
        references: List[List[str]],
        max_n: int = 4,
    ) -> float:
        """
        计算 BLEU 分数

        BLEU = BP * exp(sum(w_n * log p_n))

        Args:
            predicted: 预测词序列
            references: 参考词序列列表
            max_n: 最大 N-gram 阶数

        Returns:
            BLEU 分数
        """
        if not predicted or not references:
            return 0.0

        # 计算 brevity penalty
        pred_len = len(predicted)
        closest_ref_len = min(
            references,
            key=lambda r: abs(len(r) - pred_len)
        )
        ref_len = len(closest_ref_len)

        if pred_len >= ref_len:
            bp = 1.0
        else:
            bp = math.exp(1 - ref_len / pred_len)

        # 计算 N-gram 精度
        precisions = []
        for n in range(1, max_n + 1):
            # 跳过无法提取的 n-gram 阶数
            if len(predicted) < n:
                break

            pred_ngrams = {}
            for i in range(len(predicted) - n + 1):
                gram = tuple(predicted[i:i + n])
                pred_ngrams[gram] = pred_ngrams.get(gram, 0) + 1

            max_ref_counts = {}
            for ref in references:
                ref_ngrams = {}
                for i in range(len(ref) - n + 1):
                    gram = tuple(ref[i:i + n])
                    ref_ngrams[gram] = ref_ngrams.get(gram, 0) + 1

                for gram, count in ref_ngrams.items():
                    max_ref_counts[gram] = max(
                        max_ref_counts.get(gram, 0), count
                    )

            clipped = 0
            total = 0
            for gram, count in pred_ngrams.items():
                clipped += min(count, max_ref_counts.get(gram, 0))
                total += count

            if total == 0:
                precisions.append(0.0)
            else:
                precisions.append(clipped / total)

        if not precisions:
            return 0.0

        # 几何平均
        if any(p == 0 for p in precisions):
            return 0.0

        actual_n = len(precisions)
        avg_log = sum(
            (1.0 / actual_n) * math.log(p) for p in precisions
        )

        return bp * math.exp(avg_log)

    @staticmethod
    def compare_models(
        results: Dict[str, Dict[str, float]],
    ) -> Dict[str, str]:
        """
        比较多个模型的评估结果

        Args:
            results: {模型名: {指标名: 值}}

        Returns:
            {指标名: 最佳模型名}
        """
        best = {}

        for metric in ['perplexity', 'cross_entropy', 'bits_per_character']:
            values = {}
            for model_name, model_results in results.items():
                if metric in model_results:
                    values[model_name] = model_results[metric]

            if values:
                # 这些指标越低越好
                best_model = min(values, key=values.get)
                best[metric] = best_model

        return best
