"""
独立 CRF 序列标注
=================

不依赖深度学习框架，使用纯 NumPy 实现 CRF。

与 src/crf.py (PyTorch CRF 层) 的区别:
- src/crf.py: PyTorch nn.Module，用于 BiLSTM-CRF 模型
- standalone_crf.py: 独立的 CRF 分类器，可直接用于序列标注

CRF 核心思想:
- 给定输入序列 X，建模条件概率 P(Y|X)
- 使用特征函数描述 (标签, 输入) 之间的关系
- 使用转移矩阵建模标签之间的依赖关系

训练方法:
- 梯度下降优化对数似然

解码方法:
- 维特比算法
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class FeatureExtractor:
    """
    特征提取器

    将 (token, tag, 位置) 映射为特征索引。

    常用特征:
    - 当前词
    - 当前词的小写形式
    - 当前词的前缀/后缀
    - 当前词是否大写
    - 当前词是否为数字
    - 前一个词/后一个词
    """

    def __init__(self):
        self.feature2idx: Dict[str, int] = {}
        self.num_features = 0

    def extract(self, sentence: List[str], position: int,
                tag: str) -> List[str]:
        """
        提取特征

        参数:
            sentence: token 序列
            position: 当前位置
            tag: 当前标签

        返回:
            features: 特征名列表
        """
        features = []
        word = sentence[position]
        word_lower = word.lower()

        # 当前词特征
        features.append(f"word={word_lower}")
        features.append(f"tag={tag}")

        # 词形特征
        if word[0].isupper():
            features.append(f"cap_tag={tag}")
        if word.isdigit():
            features.append(f"digit_tag={tag}")
        if '-' in word:
            features.append(f"hyphen_tag={tag}")

        # 前缀和后缀
        if len(word) >= 3:
            features.append(f"prefix3={word_lower[:3]}_tag={tag}")
            features.append(f"suffix3={word_lower[-3:]}_tag={tag}")

        # 上下文特征
        if position > 0:
            prev_word = sentence[position - 1].lower()
            features.append(f"prev_word={prev_word}_tag={tag}")
        else:
            features.append(f"BOS_tag={tag}")

        if position < len(sentence) - 1:
            next_word = sentence[position + 1].lower()
            features.append(f"next_word={next_word}_tag={tag}")
        else:
            features.append(f"EOS_tag={tag}")

        return features

    def build(self, sentences: List[List[str]], tags: List[List[str]]):
        """
        构建特征索引

        参数:
            sentences: token 序列列表
            tags: 标签序列列表
        """
        feature_set = set()
        for sentence, tag_seq in zip(sentences, tags):
            for t in range(len(sentence)):
                features = self.extract(sentence, t, tag_seq[t])
                feature_set.update(features)

        for idx, feature in enumerate(sorted(feature_set)):
            self.feature2idx[feature] = idx

        self.num_features = len(self.feature2idx)

    def get_indices(self, sentence: List[str], position: int,
                    tag: str) -> List[int]:
        """获取特征索引列表"""
        features = self.extract(sentence, position, tag)
        return [self.feature2idx[f] for f in features if f in self.feature2idx]


class StandaloneCRF:
    """
    独立 CRF 分类器 (纯 NumPy 实现)

    使用梯度下降训练，维特比算法解码。

    参数:
        learning_rate: 学习率
        max_iterations: 最大迭代次数
        regularization: L2 正则化系数
        tolerance: 收敛阈值
    """

    def __init__(self, learning_rate: float = 0.01,
                 max_iterations: int = 100,
                 regularization: float = 0.01,
                 tolerance: float = 1e-4):
        self.lr = learning_rate
        self.max_iter = max_iterations
        self.reg = regularization
        self.tol = tolerance

        self.feature_extractor = FeatureExtractor()

        # 模型参数
        self.tag2idx: Dict[str, int] = {}
        self.idx2tag: Dict[int, str] = {}
        self.num_tags = 0

        # 转移矩阵
        self.transitions: Optional[np.ndarray] = None

        # 特征权重
        self.weights: Optional[np.ndarray] = None

        self.train_losses: List[float] = []

    def fit(self, sentences: List[List[str]], tags: List[List[str]]):
        """
        训练 CRF 模型

        参数:
            sentences: token 序列列表
            tags: 标签序列列表
        """
        # 构建标签表
        self._build_tag_vocab(tags)

        # 构建特征
        self.feature_extractor.build(sentences, tags)

        # 初始化参数
        self.transitions = np.random.randn(self.num_tags, self.num_tags) * 0.01
        self.weights = np.zeros(self.feature_extractor.num_features)

        # 训练循环
        for iteration in range(self.max_iter):
            total_loss = 0.0
            grad_transitions = np.zeros_like(self.transitions)
            grad_weights = np.zeros_like(self.weights)

            for sentence, tag_seq in zip(sentences, tags):
                # 计算梯度和损失
                loss, gt, gw = self._compute_gradient(sentence, tag_seq)
                total_loss += loss
                grad_transitions += gt
                grad_weights += gw

            # L2 正则化
            total_loss += 0.5 * self.reg * np.sum(self.weights ** 2)
            grad_weights += self.reg * self.weights

            # 更新参数
            self.transitions -= self.lr * grad_transitions
            self.weights -= self.lr * grad_weights

            avg_loss = total_loss / len(sentences)
            self.train_losses.append(avg_loss)

            # 收敛检查
            if (iteration > 0 and
                    abs(self.train_losses[-2] - self.train_losses[-1]) < self.tol):
                break

    def predict(self, sentence: List[str]) -> List[str]:
        """
        预测标签序列

        参数:
            sentence: token 序列

        返回:
            tags: 预测的标签序列
        """
        n = len(sentence)
        if n == 0:
            return []

        # 计算发射分数
        emissions = self._compute_emissions(sentence)

        # 维特比解码
        best_tags = self._viterbi(emissions)

        return [self.idx2tag[idx] for idx in best_tags]

    def predict_batch(self, sentences: List[List[str]]) -> List[List[str]]:
        """批量预测"""
        return [self.predict(s) for s in sentences]

    def _build_tag_vocab(self, tags: List[List[str]]):
        """构建标签表"""
        tag_set = set()
        for tag_seq in tags:
            tag_set.update(tag_seq)

        for idx, tag in enumerate(sorted(tag_set)):
            self.tag2idx[tag] = idx
            self.idx2tag[idx] = tag

        self.num_tags = len(self.tag2idx)

    def _compute_emissions(self, sentence: List[str]) -> np.ndarray:
        """
        计算发射分数

        返回:
            emissions: (seq_len, num_tags) 发射分数矩阵
        """
        n = len(sentence)
        emissions = np.zeros((n, self.num_tags))

        for t in range(n):
            for tag_idx in range(self.num_tags):
                tag = self.idx2tag[tag_idx]
                feature_indices = self.feature_extractor.get_indices(
                    sentence, t, tag
                )
                emissions[t][tag_idx] = sum(
                    self.weights[i] for i in feature_indices
                )

        return emissions

    def _viterbi(self, emissions: np.ndarray) -> List[int]:
        """
        维特比算法

        参数:
            emissions: (seq_len, num_tags) 发射分数

        返回:
            best_path: 最优标签索引序列
        """
        n, num_tags = emissions.shape

        # 初始化
        score = emissions[0]
        history = []

        # 递推
        for t in range(1, n):
            # score[i] + transitions[j][i] + emissions[t][j]
            scores = (score[:, np.newaxis] +
                      self.transitions +
                      emissions[t][np.newaxis, :])

            # 取最优前驱
            best_prev = np.argmax(scores, axis=0)
            score = np.max(scores, axis=0)

            history.append(best_prev)

        # 回溯
        best_path = [0] * n
        best_path[n - 1] = np.argmax(score)

        for t in range(n - 2, -1, -1):
            best_path[t] = history[t][best_path[t + 1]]

        return best_path

    def _compute_gradient(self, sentence: List[str],
                          tag_seq: List[str]) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        计算单个样本的梯度

        返回:
            loss: 负对数似然损失
            grad_transitions: 转移矩阵梯度
            grad_weights: 特征权重梯度
        """
        n = len(sentence)
        tag_indices = [self.tag2idx[tag] for tag in tag_seq]

        # 计算发射分数
        emissions = self._compute_emissions(sentence)

        # 真实路径分数
        real_score = self._path_score(emissions, tag_indices)

        # 配分函数 (前向算法)
        log_z = self._forward_algorithm(emissions)

        # 损失
        loss = log_z - real_score

        # 转移矩阵梯度
        grad_transitions = np.zeros_like(self.transitions)
        for t in range(1, n):
            grad_transitions[tag_indices[t]][tag_indices[t - 1]] -= 1

        # 特征权重梯度
        grad_weights = np.zeros_like(self.weights)

        # 真实路径的特征梯度 (负号因为是减去)
        for t in range(n):
            feature_indices = self.feature_extractor.get_indices(
                sentence, t, tag_seq[t]
            )
            for idx in feature_indices:
                grad_weights[idx] -= 1

        # 期望特征 (简化: 使用模型预测的路径近似)
        predicted = self._viterbi(emissions)
        for t in range(n):
            tag = self.idx2tag[predicted[t]]
            feature_indices = self.feature_extractor.get_indices(
                sentence, t, tag
            )
            for idx in feature_indices:
                grad_weights[idx] += 1

        return loss, grad_transitions, grad_weights

    def _path_score(self, emissions: np.ndarray,
                    tag_indices: List[int]) -> float:
        """计算路径分数"""
        score = emissions[0][tag_indices[0]]
        for t in range(1, len(tag_indices)):
            score += self.transitions[tag_indices[t]][tag_indices[t - 1]]
            score += emissions[t][tag_indices[t]]
        return score

    def _forward_algorithm(self, emissions: np.ndarray) -> float:
        """
        前向算法计算配分函数

        使用 log-sum-exp 保证数值稳定
        """
        n = emissions.shape[0]

        # 初始化
        alpha = emissions[0]

        # 递推
        for t in range(1, n):
            # alpha[i] + transitions[j][i]
            scores = alpha[:, np.newaxis] + self.transitions
            # log-sum-exp
            new_alpha = self._logsumexp(scores, axis=0)
            alpha = new_alpha + emissions[t]

        # 配分函数
        return self._logsumexp(alpha)

    def _logsumexp(self, x: np.ndarray, axis: int = None) -> np.ndarray:
        """数值稳定的 log-sum-exp"""
        x_max = np.max(x, axis=axis, keepdims=True)
        return np.squeeze(x_max) + np.log(
            np.sum(np.exp(x - x_max), axis=axis, keepdims=True)
        ).squeeze()
