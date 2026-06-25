"""
Word2Vec 应用模块

使用训练好的词向量解决实际 NLP 任务：
- 文本分类
- 情感分析
- 词聚类
"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class TextClassifier:
    """文本分类器

    使用词向量的平均作为文档表示，然后用简单的分类器进行分类。
    支持：
    - 最近邻分类
    - 逻辑回归分类
    """

    def __init__(self, word_vectors: np.ndarray, word2idx: Dict[str, int]):
        """初始化

        Args:
            word_vectors: 词向量矩阵 (vocab_size, dim)
            word2idx: 词到索引的映射
        """
        self.word_vectors = word_vectors
        self.word2idx = word2idx
        self.vector_size = word_vectors.shape[1]

        # 训练数据
        self.class_centroids: Dict[int, np.ndarray] = {}
        self.trained = False

    def _sentence_vector(self, words: List[str]) -> Optional[np.ndarray]:
        """计算句子向量（词向量的平均）

        Args:
            words: 分词后的句子

        Returns:
            句子向量，如果没有有效词返回 None
        """
        vectors = []
        for word in words:
            idx = self.word2idx.get(word)
            if idx is not None:
                vectors.append(self.word_vectors[idx])

        if not vectors:
            return None

        return np.mean(vectors, axis=0)

    def train(self, sentences: List[List[str]], labels: List[int]) -> None:
        """训练分类器（基于类别中心）

        Args:
            sentences: 分词后的句子列表
            labels: 类别标签列表
        """
        # 收集每个类别的句子向量
        class_vectors: Dict[int, List[np.ndarray]] = {}

        for sentence, label in zip(sentences, labels):
            vec = self._sentence_vector(sentence)
            if vec is not None:
                if label not in class_vectors:
                    class_vectors[label] = []
                class_vectors[label].append(vec)

        # 计算类别中心
        self.class_centroids = {}
        for label, vectors in class_vectors.items():
            self.class_centroids[label] = np.mean(vectors, axis=0)

        self.trained = True

    def predict(self, sentence: List[str]) -> Optional[int]:
        """预测句子类别

        Args:
            sentence: 分词后的句子

        Returns:
            预测的类别标签，如果无法预测返回 None
        """
        if not self.trained:
            return None

        vec = self._sentence_vector(sentence)
        if vec is None:
            return None

        # 最近邻分类
        best_label = None
        best_similarity = -np.inf

        for label, centroid in self.class_centroids.items():
            similarity = np.dot(vec, centroid) / (
                np.linalg.norm(vec) * np.linalg.norm(centroid) + 1e-10
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_label = label

        return best_label

    def predict_batch(self, sentences: List[List[str]]) -> List[Optional[int]]:
        """批量预测

        Args:
            sentences: 分词后的句子列表

        Returns:
            预测的类别标签列表
        """
        return [self.predict(s) for s in sentences]

    def evaluate(self, sentences: List[List[str]], labels: List[int]) -> Dict[str, float]:
        """评估分类器

        Args:
            sentences: 测试句子列表
            labels: 真实标签列表

        Returns:
            评估指标字典
        """
        predictions = self.predict_batch(sentences)

        correct = 0
        total = 0
        class_correct: Dict[int, int] = {}
        class_total: Dict[int, int] = {}

        for pred, true in zip(predictions, labels):
            if pred is None:
                continue

            total += 1
            class_total[true] = class_total.get(true, 0) + 1

            if pred == true:
                correct += 1
                class_correct[true] = class_correct.get(true, 0) + 1

        accuracy = correct / total if total > 0 else 0.0

        # 每类准确率
        class_accuracy = {}
        for label in class_total:
            c = class_correct.get(label, 0)
            t = class_total[label]
            class_accuracy[label] = c / t if t > 0 else 0.0

        return {
            'accuracy': accuracy,
            'total': total,
            'correct': correct,
            'class_accuracy': class_accuracy
        }


class SentimentAnalyzer:
    """情感分析器

    使用词向量进行情感分析。
    基于情感词典和词向量相似度。
    """

    def __init__(self, word_vectors: np.ndarray, word2idx: Dict[str, int]):
        """初始化

        Args:
            word_vectors: 词向量矩阵
            word2idx: 词到索引的映射
        """
        self.word_vectors = word_vectors
        self.word2idx = word2idx
        self.vector_size = word_vectors.shape[1]

        # 情感词典
        self.positive_words: List[str] = []
        self.negative_words: List[str] = []
        self.positive_centroid: Optional[np.ndarray] = None
        self.negative_centroid: Optional[np.ndarray] = None

    def build_sentiment_lexicon(self, positive_words: List[str],
                                 negative_words: List[str]) -> None:
        """构建情感词典

        Args:
            positive_words: 正面词列表
            negative_words: 负面词列表
        """
        self.positive_words = [w for w in positive_words if w in self.word2idx]
        self.negative_words = [w for w in negative_words if w in self.word2idx]

        # 计算情感中心向量
        pos_vectors = [self.word_vectors[self.word2idx[w]]
                       for w in self.positive_words]
        neg_vectors = [self.word_vectors[self.word2idx[w]]
                       for w in self.negative_words]

        if pos_vectors:
            self.positive_centroid = np.mean(pos_vectors, axis=0)
        if neg_vectors:
            self.negative_centroid = np.mean(neg_vectors, axis=0)

    def _sentence_vector(self, words: List[str]) -> Optional[np.ndarray]:
        """计算句子向量"""
        vectors = []
        for word in words:
            idx = self.word2idx.get(word)
            if idx is not None:
                vectors.append(self.word_vectors[idx])

        if not vectors:
            return None

        return np.mean(vectors, axis=0)

    def analyze(self, words: List[str]) -> Dict[str, float]:
        """分析句子情感

        Args:
            words: 分词后的句子

        Returns:
            {
                'sentiment': float (-1 to 1, 负面到正面),
                'positive_score': float,
                'negative_score': float
            }
        """
        vec = self._sentence_vector(words)
        if vec is None:
            return {'sentiment': 0.0, 'positive_score': 0.0, 'negative_score': 0.0}

        pos_score = 0.0
        neg_score = 0.0

        if self.positive_centroid is not None:
            pos_score = np.dot(vec, self.positive_centroid) / (
                np.linalg.norm(vec) * np.linalg.norm(self.positive_centroid) + 1e-10
            )

        if self.negative_centroid is not None:
            neg_score = np.dot(vec, self.negative_centroid) / (
                np.linalg.norm(vec) * np.linalg.norm(self.negative_centroid) + 1e-10
            )

        # 情感得分 = 正面相似度 - 负面相似度
        sentiment = pos_score - neg_score

        return {
            'sentiment': float(sentiment),
            'positive_score': float(pos_score),
            'negative_score': float(neg_score)
        }

    def analyze_batch(self, sentences: List[List[str]]) -> List[Dict[str, float]]:
        """批量分析情感

        Args:
            sentences: 分词后的句子列表

        Returns:
            情感分析结果列表
        """
        return [self.analyze(s) for s in sentences]

    def evaluate(self, sentences: List[List[str]],
                 labels: List[int]) -> Dict[str, float]:
        """评估情感分析器

        Args:
            sentences: 测试句子列表
            labels: 真实标签 (1=正面, -1=负面, 0=中性)

        Returns:
            评估指标
        """
        results = self.analyze_batch(sentences)

        correct = 0
        total = 0

        for result, label in zip(results, labels):
            # 将连续得分转为离散标签
            if result['sentiment'] > 0.05:
                pred = 1
            elif result['sentiment'] < -0.05:
                pred = -1
            else:
                pred = 0

            total += 1
            if pred == label:
                correct += 1

        accuracy = correct / total if total > 0 else 0.0

        return {
            'accuracy': accuracy,
            'total': total,
            'correct': correct
        }


class WordClusterer:
    """词聚类器

    使用词向量进行语义聚类
    """

    def __init__(self, word_vectors: np.ndarray, word2idx: Dict[str, int],
                 idx2word: Dict[int, str]):
        """初始化

        Args:
            word_vectors: 词向量矩阵
            word2idx: 词到索引的映射
            idx2word: 索引到词的映射
        """
        self.word_vectors = word_vectors
        self.word2idx = word2idx
        self.idx2word = idx2word

    def cluster(self, words: List[str], k: int,
                max_iter: int = 100) -> Dict[int, List[str]]:
        """对指定词进行聚类

        Args:
            words: 要聚类的词列表
            k: 聚类数
            max_iter: 最大迭代次数

        Returns:
            {cluster_id: [words]}
        """
        # 获取词向量
        valid_words = []
        vectors = []
        for word in words:
            idx = self.word2idx.get(word)
            if idx is not None:
                valid_words.append(word)
                vectors.append(self.word_vectors[idx])

        if not valid_words:
            return {}

        vectors = np.array(vectors)

        # K-Means 聚类
        labels, centroids = self._kmeans(vectors, k, max_iter)

        # 整理结果
        clusters: Dict[int, List[str]] = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(valid_words[i])

        return clusters

    @staticmethod
    def _kmeans(vectors: np.ndarray, k: int,
                max_iter: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """K-Means 聚类

        Args:
            vectors: 向量矩阵
            k: 聚类数
            max_iter: 最大迭代次数

        Returns:
            (labels, centroids)
        """
        n = vectors.shape[0]

        # 随机初始化
        indices = np.random.choice(n, min(k, n), replace=False)
        centroids = vectors[indices].copy()

        labels = np.zeros(n, dtype=int)

        for _ in range(max_iter):
            # 分配
            new_labels = np.zeros(n, dtype=int)
            for i in range(n):
                distances = np.sum((centroids - vectors[i]) ** 2, axis=1)
                new_labels[i] = np.argmin(distances)

            if np.array_equal(labels, new_labels):
                break
            labels = new_labels

            # 更新中心
            for j in range(k):
                members = vectors[labels == j]
                if len(members) > 0:
                    centroids[j] = members.mean(axis=0)

        return labels, centroids

    def get_cluster_summary(self, clusters: Dict[int, List[str]]) -> str:
        """获取聚类结果摘要

        Args:
            clusters: 聚类结果

        Returns:
            格式化的摘要字符串
        """
        lines = []
        for cluster_id in sorted(clusters.keys()):
            words = clusters[cluster_id]
            lines.append(f"Cluster {cluster_id}: {', '.join(words)}")
        return '\n'.join(lines)
