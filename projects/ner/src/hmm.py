"""
隐马尔可夫模型 (HMM) 序列标注
=============================

实现基于 HMM 的命名实体识别。

HMM 是生成式概率图模型，建模联合概率 P(X, Y)。

三个核心参数:
- 初始概率 π: P(y_1)
- 转移概率 A: P(y_t | y_{t-1})
- 发射概率 B: P(x_t | y_t)

解码算法: 维特比算法 (Viterbi Algorithm)

与 CRF 的对比:
- HMM 是生成式模型，CRF 是判别式模型
- HMM 需要建模 P(X)，CRF 直接建模 P(Y|X)
- HMM 特征工程受限，CRF 可以使用任意特征
- HMM 训练更快，CRF 通常更准确
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class HMM:
    """
    隐马尔可夫模型

    用于序列标注任务 (NER, POS Tagging 等)

    参数:
        smooth: 平滑系数 (Laplace 平滑)
    """

    def __init__(self, smooth: float = 1e-6):
        self.smooth = smooth

        # 模型参数
        self.pi: Optional[np.ndarray] = None       # 初始概率 (num_tags,)
        self.A: Optional[np.ndarray] = None         # 转移概率 (num_tags, num_tags)
        self.B: Optional[np.ndarray] = None         # 发射概率 (num_tags, vocab_size)

        # 词表和标签表
        self.tag2idx: Dict[str, int] = {}
        self.idx2tag: Dict[int, str] = {}
        self.word2idx: Dict[str, int] = {}
        self.idx2word: Dict[int, str] = {}

        self.num_tags = 0
        self.vocab_size = 0

    def fit(self, sentences: List[List[str]], tags: List[List[str]]):
        """
        训练 HMM 模型 (监督学习)

        使用极大似然估计 (MLE) + Laplace 平滑。

        参数:
            sentences: token 序列列表
            tags: 标签序列列表
        """
        # 构建词表和标签表
        self._build_vocabularies(sentences, tags)

        # 初始化计数矩阵
        pi_counts = np.zeros(self.num_tags)
        A_counts = np.zeros((self.num_tags, self.num_tags))
        B_counts = np.zeros((self.num_tags, self.vocab_size))

        # 统计计数
        for sentence, tag_seq in zip(sentences, tags):
            if not sentence:
                continue

            # 初始概率计数
            tag_idx = self.tag2idx[tag_seq[0]]
            pi_counts[tag_idx] += 1

            for t in range(len(sentence)):
                tag_idx = self.tag2idx[tag_seq[t]]
                word_idx = self.word2idx.get(sentence[t], 0)  # 0 for UNK

                # 发射概率计数
                B_counts[tag_idx][word_idx] += 1

                # 转移概率计数
                if t > 0:
                    prev_tag_idx = self.tag2idx[tag_seq[t - 1]]
                    A_counts[prev_tag_idx][tag_idx] += 1

        # 归一化 (带 Laplace 平滑)
        self.pi = (pi_counts + self.smooth) / (pi_counts.sum() +
                                                self.smooth * self.num_tags)

        # 转移概率: A[i][j] = P(y_t = j | y_{t-1} = i)
        row_sums = A_counts.sum(axis=1, keepdims=True) + self.smooth * self.num_tags
        self.A = (A_counts + self.smooth) / row_sums

        # 发射概率: B[i][j] = P(x_t = j | y_t = i)
        row_sums = B_counts.sum(axis=1, keepdims=True) + self.smooth * self.vocab_size
        self.B = (B_counts + self.smooth) / row_sums

    def predict(self, sentence: List[str]) -> List[str]:
        """
        预测单个句子的标签序列 (维特比算法)

        参数:
            sentence: token 列表

        返回:
            tags: 预测的标签序列
        """
        if self.pi is None:
            raise ValueError("Model not trained. Call fit() first.")

        n = len(sentence)
        if n == 0:
            return []

        # 转换为索引
        word_indices = [self.word2idx.get(w, 0) for w in sentence]

        # 维特比算法
        # delta[t][j] = 到达位置 t 标签 j 的最优路径对数概率
        # psi[t][j] = 位置 t 标签 j 的最优前驱标签
        log_pi = np.log(self.pi + 1e-10)
        log_A = np.log(self.A + 1e-10)
        log_B = np.log(self.B + 1e-10)

        delta = np.zeros((n, self.num_tags))
        psi = np.zeros((n, self.num_tags), dtype=int)

        # 初始化
        delta[0] = log_pi + log_B[:, word_indices[0]]

        # 递推
        for t in range(1, n):
            for j in range(self.num_tags):
                # delta[t-1][i] + log_A[i][j]
                scores = delta[t - 1] + log_A[:, j]
                psi[t][j] = np.argmax(scores)
                delta[t][j] = scores[psi[t][j]] + log_B[j, word_indices[t]]

        # 回溯
        tags = [0] * n
        tags[n - 1] = np.argmax(delta[n - 1])

        for t in range(n - 2, -1, -1):
            tags[t] = psi[t + 1][tags[t + 1]]

        # 转换为标签字符串
        return [self.idx2tag[idx] for idx in tags]

    def predict_batch(self, sentences: List[List[str]]) -> List[List[str]]:
        """
        批量预测

        参数:
            sentences: token 序列列表

        返回:
            tags_list: 预测的标签序列列表
        """
        return [self.predict(sentence) for sentence in sentences]

    def _build_vocabularies(self, sentences: List[List[str]],
                            tags: List[List[str]]):
        """构建词表和标签表"""
        # 标签表
        tag_set = set()
        for tag_seq in tags:
            tag_set.update(tag_seq)

        for idx, tag in enumerate(sorted(tag_set)):
            self.tag2idx[tag] = idx
            self.idx2tag[idx] = tag

        self.num_tags = len(self.tag2idx)

        # 词表 (包含 UNK)
        word_set = set()
        for sentence in sentences:
            word_set.update(sentence)

        self.word2idx["<UNK>"] = 0
        self.idx2word[0] = "<UNK>"

        for idx, word in enumerate(sorted(word_set), start=1):
            self.word2idx[word] = idx
            self.idx2word[idx] = word

        self.vocab_size = len(self.word2idx)

    def get_transition_matrix(self) -> np.ndarray:
        """获取转移概率矩阵"""
        return self.A.copy() if self.A is not None else None

    def get_emission_matrix(self) -> np.ndarray:
        """获取发射概率矩阵"""
        return self.B.copy() if self.B is not None else None

    def get_initial_probs(self) -> np.ndarray:
        """获取初始概率"""
        return self.pi.copy() if self.pi is not None else None

    def __repr__(self) -> str:
        return (f"HMM(num_tags={self.num_tags}, "
                f"vocab_size={self.vocab_size}, "
                f"smooth={self.smooth})")
