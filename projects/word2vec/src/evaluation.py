"""
词向量评估模块

提供词向量质量评估功能：
- 词相似度评估
- 词类比评估
- t-SNE 可视化
"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class WordSimilarityEvaluator:
    """词相似度评估器

    通过计算词对相似度与人工评分的相关性来评估词向量质量。
    常用数据集：WordSim-353, SimLex-999
    """

    def __init__(self, word_vectors: np.ndarray, word2idx: Dict[str, int]):
        """初始化

        Args:
            word_vectors: 词向量矩阵 (vocab_size, dim)
            word2idx: 词到索引的映射
        """
        self.word_vectors = word_vectors
        self.word2idx = word2idx

        # 预计算归一化向量
        norms = np.linalg.norm(word_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self.normalized = word_vectors / norms

    def cosine_similarity(self, word1: str, word2: str) -> float:
        """计算两个词的余弦相似度

        Args:
            word1: 第一个词
            word2: 第二个词

        Returns:
            余弦相似度
        """
        idx1 = self.word2idx.get(word1)
        idx2 = self.word2idx.get(word2)

        if idx1 is None or idx2 is None:
            return 0.0

        return float(np.dot(self.normalized[idx1], self.normalized[idx2]))

    def evaluate(self, word_pairs: List[Tuple[str, str, float]]) -> float:
        """评估词相似度

        使用 Spearman 等级相关系数。

        Args:
            word_pairs: [(word1, word2, human_score), ...]

        Returns:
            Spearman 相关系数
        """
        model_scores = []
        human_scores = []

        for word1, word2, score in word_pairs:
            sim = self.cosine_similarity(word1, word2)
            model_scores.append(sim)
            human_scores.append(score)

        if len(model_scores) < 2:
            return 0.0

        return self._spearman_correlation(model_scores, human_scores)

    @staticmethod
    def _spearman_correlation(x: List[float], y: List[float]) -> float:
        """计算 Spearman 等级相关系数

        Args:
            x: 第一个变量
            y: 第二个变量

        Returns:
            相关系数
        """
        n = len(x)

        # 计算等级
        def rank(arr):
            sorted_indices = np.argsort(arr)
            ranks = np.zeros(n)
            for i, idx in enumerate(sorted_indices):
                ranks[idx] = i + 1
            return ranks

        rank_x = rank(x)
        rank_y = rank(y)

        # 计算等级差的平方和
        d_squared = np.sum((rank_x - rank_y) ** 2)

        # Spearman 公式
        rho = 1 - (6 * d_squared) / (n * (n * n - 1))
        return rho


class AnalogyEvaluator:
    """词类比评估器

    评估词向量的类比能力，例如：
    king - man + woman = queen
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

        # 预计算归一化向量
        norms = np.linalg.norm(word_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self.normalized = word_vectors / norms

    def analogy(self, a: str, b: str, c: str, topn: int = 5) -> List[Tuple[str, float]]:
        """执行词类比

        a - b + c = ?  (例如: king - man + woman = queen)

        Args:
            a: 第一个词（如 king）
            b: 第二个词（如 man）
            c: 第三个词（如 woman）
            topn: 返回结果数量

        Returns:
            [(word, similarity), ...]
        """
        idx_a = self.word2idx.get(a)
        idx_b = self.word2idx.get(b)
        idx_c = self.word2idx.get(c)

        if idx_a is None or idx_b is None or idx_c is None:
            return []

        # 类比向量: a - b + c
        vec = self.word_vectors[idx_a] - self.word_vectors[idx_b] + self.word_vectors[idx_c]

        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        # 计算相似度
        similarities = np.dot(self.normalized, vec)

        # 排除输入词
        similarities[idx_a] = -1
        similarities[idx_b] = -1
        similarities[idx_c] = -1

        # 获取 topn
        top_indices = np.argsort(similarities)[::-1][:topn]

        results = []
        for idx in top_indices:
            word = self.idx2word.get(idx)
            if word is not None:
                results.append((word, float(similarities[idx])))

        return results

    def evaluate(self, analogy_pairs: List[Tuple[str, str, str, str]],
                 topn: int = 1) -> float:
        """评估类比准确率

        Args:
            analogy_pairs: [(a, b, c, expected_d), ...]
            topn: 考虑前 topn 个结果

        Returns:
            准确率
        """
        correct = 0
        total = 0

        for a, b, c, expected in analogy_pairs:
            idx_a = self.word2idx.get(a)
            idx_b = self.word2idx.get(b)
            idx_c = self.word2idx.get(c)
            idx_expected = self.word2idx.get(expected)

            if idx_a is None or idx_b is None or idx_c is None or idx_expected is None:
                continue

            results = self.analogy(a, b, c, topn=topn)
            predicted_words = [w for w, _ in results]

            total += 1
            if expected in predicted_words:
                correct += 1

        return correct / total if total > 0 else 0.0


class TSNEVisualizer:
    """t-SNE 可视化器

    将高维词向量降到 2D 进行可视化。
    使用简化版 t-SNE（Barnes-Hut 近似）或 PCA 作为备选。
    """

    @staticmethod
    def pca_reduce(vectors: np.ndarray, n_components: int = 2) -> np.ndarray:
        """PCA 降维

        比 t-SNE 快得多，适合快速预览。

        Args:
            vectors: 高维向量矩阵 (n, d)
            n_components: 目标维度

        Returns:
            降维后的向量矩阵 (n, n_components)
        """
        # 中心化
        mean = np.mean(vectors, axis=0)
        centered = vectors - mean

        # SVD
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)

        # 取前 n_components 个主成分
        return U[:, :n_components] * S[:n_components]

    @staticmethod
    def tsne_reduce(vectors: np.ndarray, n_components: int = 2,
                    perplexity: float = 30.0, n_iter: int = 1000,
                    learning_rate: float = 200.0) -> np.ndarray:
        """t-SNE 降维

        实现标准 t-SNE 算法。

        Args:
            vectors: 高维向量矩阵 (n, d)
            n_components: 目标维度
            perplexity: 困惑度
            n_iter: 迭代次数
            learning_rate: 学习率

        Returns:
            降维后的向量矩阵 (n, n_components)
        """
        n = vectors.shape[0]

        if n <= 1:
            return np.zeros((n, n_components))

        # 计算成对距离
        distances = TSNEVisualizer._compute_distances(vectors)

        # 计算高维空间的概率分布 P
        P = TSNEVisualizer._compute_p(distances, perplexity)
        P = (P + P.T) / (2 * n)  # 对称化
        P = np.maximum(P, 1e-12)

        # 初始化低维嵌入
        Y = np.random.randn(n, n_components) * 0.01

        # 训练
        momentum = 0.5
        for iteration in range(n_iter):
            # 计算低维空间的概率分布 Q
            Q, distances_Y = TSNEVisualizer._compute_q(Y)

            # 计算梯度
            grad = TSNEVisualizer._compute_gradient(P, Q, Y, distances_Y)

            # 更新
            if iteration < 250:
                momentum = 0.5
            else:
                momentum = 0.8

            Y = Y - learning_rate * grad + momentum * (Y - (Y - learning_rate * grad))

            # 裁剪以防止数值爆炸
            Y = np.clip(Y, -100, 100)

        return Y

    @staticmethod
    def _compute_distances(vectors: np.ndarray) -> np.ndarray:
        """计算欧氏距离矩阵"""
        n = vectors.shape[0]
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = np.sum((vectors[i] - vectors[j]) ** 2)
                distances[i, j] = d
                distances[j, i] = d
        return distances

    @staticmethod
    def _compute_p(distances: np.ndarray, perplexity: float) -> np.ndarray:
        """计算高维概率分布 P"""
        n = distances.shape[0]
        P = np.zeros((n, n))
        target_entropy = np.log(perplexity)

        for i in range(n):
            # 二分搜索找到合适的 sigma
            lo, hi = 1e-10, 1e4
            for _ in range(50):
                sigma = (lo + hi) / 2
                p = np.exp(-distances[i] / (2 * sigma ** 2))
                p[i] = 0
                p_sum = p.sum()

                if p_sum == 0:
                    p_sum = 1e-10

                p = p / p_sum
                entropy = -np.sum(p[p > 0] * np.log(p[p > 0]))

                if entropy > target_entropy:
                    hi = sigma
                else:
                    lo = sigma

            P[i] = p

        return P

    @staticmethod
    def _compute_q(Y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """计算低维概率分布 Q"""
        n = Y.shape[0]

        # 计算距离
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = np.sum((Y[i] - Y[j]) ** 2)
                distances[i, j] = d
                distances[j, i] = d

        # t 分布核
        Q = 1.0 / (1.0 + distances)
        np.fill_diagonal(Q, 0)
        Q = Q / Q.sum()
        Q = np.maximum(Q, 1e-12)

        return Q, distances

    @staticmethod
    def _compute_gradient(P: np.ndarray, Q: np.ndarray,
                          Y: np.ndarray, distances_Y: np.ndarray) -> np.ndarray:
        """计算 t-SNE 梯度"""
        n = Y.shape[0]
        d = Y.shape[1]
        grad = np.zeros_like(Y)

        for i in range(n):
            diff = Y[i] - Y  # (n, d)
            pq_diff = (P[i] - Q[i]) * (1.0 / (1.0 + distances_Y[i]))  # (n,)
            grad[i] = 4 * np.sum(pq_diff.reshape(-1, 1) * diff, axis=0)

        return grad

    def visualize(self, word_vectors: np.ndarray, words: List[str],
                  method: str = 'pca', figsize: Tuple[int, int] = (12, 8),
                  save_path: Optional[str] = None) -> None:
        """可视化词向量

        Args:
            word_vectors: 词向量矩阵
            words: 词列表
            method: 降维方法 'pca' 或 'tsne'
            figsize: 图片大小
            save_path: 保存路径
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
        except ImportError:
            print("matplotlib not installed. Install with: pip install matplotlib")
            return

        # 降维
        if method == 'pca':
            coords = self.pca_reduce(word_vectors, n_components=2)
        elif method == 'tsne':
            coords = self.tsne_reduce(word_vectors, n_components=2)
        else:
            raise ValueError(f"Unknown method: {method}")

        # 绘图
        plt.figure(figsize=figsize)
        plt.scatter(coords[:, 0], coords[:, 1], c='steelblue', alpha=0.6, s=50)

        # 标注词
        for i, word in enumerate(words):
            plt.annotate(word, (coords[i, 0], coords[i, 1]),
                         fontsize=9, alpha=0.8)

        plt.title(f"Word2Vec Visualization ({method.upper()})")
        plt.xlabel("Dimension 1")
        plt.ylabel("Dimension 2")
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved to {save_path}")

        plt.show()


class WordClustering:
    """词聚类

    使用 K-Means 对词向量进行聚类
    """

    @staticmethod
    def kmeans(vectors: np.ndarray, k: int, max_iter: int = 100,
               random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
        """K-Means 聚类

        Args:
            vectors: 词向量矩阵 (n, d)
            k: 聚类数
            max_iter: 最大迭代次数
            random_state: 随机种子

        Returns:
            (labels, centroids)
            labels: 每个点的聚类标签 (n,)
            centroids: 聚类中心 (k, d)
        """
        np.random.seed(random_state)
        n, d = vectors.shape

        # 随机初始化聚类中心
        indices = np.random.choice(n, k, replace=False)
        centroids = vectors[indices].copy()

        labels = np.zeros(n, dtype=int)

        for _ in range(max_iter):
            # 分配每个点到最近的聚类中心
            new_labels = np.zeros(n, dtype=int)
            for i in range(n):
                distances = np.sum((centroids - vectors[i]) ** 2, axis=1)
                new_labels[i] = np.argmin(distances)

            # 检查收敛
            if np.array_equal(labels, new_labels):
                break
            labels = new_labels

            # 更新聚类中心
            for j in range(k):
                members = vectors[labels == j]
                if len(members) > 0:
                    centroids[j] = members.mean(axis=0)

        return labels, centroids

    @staticmethod
    def get_clusters(words: List[str], labels: np.ndarray, k: int) -> Dict[int, List[str]]:
        """获取聚类结果

        Args:
            words: 词列表
            labels: 聚类标签
            k: 聚类数

        Returns:
            {cluster_id: [words]}
        """
        clusters: Dict[int, List[str]] = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(words[i])
        return clusters

    @staticmethod
    def evaluate_clustering(vectors: np.ndarray, labels: np.ndarray,
                            centroids: np.ndarray) -> float:
        """评估聚类质量（轮廓系数）

        Args:
            vectors: 词向量矩阵
            labels: 聚类标签
            centroids: 聚类中心

        Returns:
            平均轮廓系数
        """
        n = len(vectors)
        if n <= 1:
            return 0.0

        silhouette_scores = np.zeros(n)

        for i in range(n):
            # a(i): 同簇内的平均距离
            same_cluster = vectors[labels == labels[i]]
            if len(same_cluster) > 1:
                a_i = np.mean(np.sqrt(np.sum((same_cluster - vectors[i]) ** 2, axis=1)))
            else:
                a_i = 0

            # b(i): 最近其他簇的平均距离
            b_i = np.inf
            for c in range(len(centroids)):
                if c != labels[i]:
                    other_cluster = vectors[labels == c]
                    if len(other_cluster) > 0:
                        dist = np.mean(np.sqrt(np.sum((other_cluster - vectors[i]) ** 2, axis=1)))
                        b_i = min(b_i, dist)

            if b_i == np.inf:
                b_i = 0

            # 轮廓系数
            if max(a_i, b_i) > 0:
                silhouette_scores[i] = (b_i - a_i) / max(a_i, b_i)

        return float(np.mean(silhouette_scores))
