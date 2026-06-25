"""关键帧提取模块

实现多种关键帧提取策略，包括基于视觉差异、直方图变化和聚类的方法。
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np


class KeyframeExtractor:
    """关键帧提取器

    支持多种关键帧提取策略：
    - histogram: 基于颜色直方图差异
    - optical_flow: 基于光流幅度
    - clustering: 基于特征聚类
    - threshold: 基于固定阈值

    Args:
        method: 提取方法
        threshold: 差异阈值（histogram/threshold 方法使用）
        max_keyframes: 最大关键帧数
    """

    def __init__(
        self,
        method: str = "histogram",
        threshold: float = 0.5,
        max_keyframes: int = 20,
    ):
        self.method = method
        self.threshold = threshold
        self.max_keyframes = max_keyframes

    def extract(self, frames: List[np.ndarray]) -> Tuple[List[int], List[float]]:
        """提取关键帧

        Args:
            frames: 视频帧列表

        Returns:
            (关键帧索引列表, 对应分数列表)
        """
        if len(frames) == 0:
            return [], []

        if self.method == "histogram":
            return self._extract_by_histogram(frames)
        elif self.method == "optical_flow":
            return self._extract_by_optical_flow(frames)
        elif self.method == "threshold":
            return self._extract_by_threshold(frames)
        elif self.method == "clustering":
            return self._extract_by_clustering(frames)
        else:
            raise ValueError(f"未知关键帧提取方法: {self.method}")

    def _extract_by_histogram(
        self, frames: List[np.ndarray]
    ) -> Tuple[List[int], List[float]]:
        """基于颜色直方图差异的关键帧提取

        计算相邻帧的直方图差异，选取差异较大的帧作为关键帧。
        """
        if len(frames) == 1:
            return [0], [1.0]

        # 计算直方图
        histograms = []
        for frame in frames:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
            cv2.normalize(hist, hist)
            histograms.append(hist.flatten())

        # 计算帧间差异
        scores = [0.0]  # 第一帧分数为 0
        for i in range(1, len(histograms)):
            diff = cv2.compareHist(
                histograms[i - 1], histograms[i], cv2.HISTCMP_BHATTACHARYYA
            )
            scores.append(diff)

        # 选取关键帧
        keyframe_indices = self._select_keyframes_by_scores(scores)
        return keyframe_indices, [scores[i] for i in keyframe_indices]

    def _extract_by_optical_flow(
        self, frames: List[np.ndarray]
    ) -> Tuple[List[int], List[float]]:
        """基于光流幅度的关键帧提取

        计算相邻帧的光流幅度，选取运动变化大的帧。
        """
        if len(frames) <= 1:
            return list(range(len(frames))), [1.0] * len(frames)

        gray_prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        scores = [0.0]

        for i in range(1, len(frames)):
            gray_curr = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(
                gray_prev, gray_curr, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
            scores.append(magnitude.mean())
            gray_prev = gray_curr

        # 归一化分数
        max_score = max(scores) if max(scores) > 0 else 1.0
        scores = [s / max_score for s in scores]

        keyframe_indices = self._select_keyframes_by_scores(scores)
        return keyframe_indices, [scores[i] for i in keyframe_indices]

    def _extract_by_threshold(
        self, frames: List[np.ndarray]
    ) -> Tuple[List[int], List[float]]:
        """基于阈值的关键帧提取

        当帧间差异超过阈值时，选取该帧为关键帧。
        """
        if len(frames) <= 1:
            return list(range(len(frames))), [1.0]

        keyframe_indices = [0]
        prev_hist = self._compute_histogram(frames[0])

        for i in range(1, len(frames)):
            curr_hist = self._compute_histogram(frames[i])
            diff = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_BHATTACHARYYA)

            if diff > self.threshold:
                keyframe_indices.append(i)
                prev_hist = curr_hist

        scores = [1.0] * len(keyframe_indices)
        return keyframe_indices, scores

    def _extract_by_clustering(
        self, frames: List[np.ndarray]
    ) -> Tuple[List[int], List[float]]:
        """基于聚类的关键帧提取

        对帧的特征进行聚类，选取每个聚类的中心帧。
        """
        # 提取简化的特征（颜色直方图 + 纹理）
        features = []
        for frame in frames:
            feat = self._extract_simple_feature(frame)
            features.append(feat)

        features = np.array(features)

        # 简单的 K-Means 聚类
        n_clusters = min(self.max_keyframes, len(frames))
        centroids, labels = self._simple_kmeans(features, n_clusters)

        # 选取每个聚类中最接近中心的帧
        keyframe_indices = []
        for c in range(n_clusters):
            cluster_indices = np.where(labels == c)[0]
            if len(cluster_indices) == 0:
                continue
            # 找到最接近中心的帧
            distances = np.linalg.norm(features[cluster_indices] - centroids[c], axis=1)
            closest = cluster_indices[np.argmin(distances)]
            keyframe_indices.append(closest)

        keyframe_indices = sorted(keyframe_indices)
        scores = [1.0] * len(keyframe_indices)
        return keyframe_indices, scores

    def _select_keyframes_by_scores(self, scores: List[float]) -> List[int]:
        """基于分数选取关键帧"""
        indices = list(range(len(scores)))
        # 按分数降序排列
        sorted_pairs = sorted(zip(scores, indices), reverse=True)
        selected = sorted([pair[1] for pair in sorted_pairs[:self.max_keyframes]])
        return selected

    def _compute_histogram(self, frame: np.ndarray) -> np.ndarray:
        """计算帧的颜色直方图"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return hist.flatten()

    def _extract_simple_feature(self, frame: np.ndarray) -> np.ndarray:
        """提取简化的帧特征（颜色直方图 + 梯度）"""
        # 颜色直方图
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180]).flatten()
        hist_s = cv2.calcHist([hsv], [1], None, [16], [0, 256]).flatten()

        # 梯度特征
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_resized = cv2.resize(gray, (64, 64))
        gx = cv2.Sobel(gray_resized, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray_resized, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(gx ** 2 + gy ** 2)
        grad_hist = np.histogram(grad_mag, bins=16, range=(0, 255))[0].astype(float)

        # 归一化
        hist_h = hist_h / (hist_h.sum() + 1e-8)
        hist_s = hist_s / (hist_s.sum() + 1e-8)
        grad_hist = grad_hist / (grad_hist.sum() + 1e-8)

        return np.concatenate([hist_h, hist_s, grad_hist])

    def _simple_kmeans(
        self, data: np.ndarray, n_clusters: int, max_iter: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """简单的 K-Means 实现"""
        n_samples = data.shape[0]
        rng = np.random.RandomState(42)

        # 随机初始化中心
        indices = rng.choice(n_samples, size=n_clusters, replace=False)
        centroids = data[indices].copy()

        for _ in range(max_iter):
            # 计算距离并分配
            distances = np.linalg.norm(data[:, np.newaxis] - centroids, axis=2)
            labels = np.argmin(distances, axis=1)

            # 更新中心
            new_centroids = np.zeros_like(centroids)
            for c in range(n_clusters):
                mask = labels == c
                if mask.any():
                    new_centroids[c] = data[mask].mean(axis=0)
                else:
                    new_centroids[c] = centroids[c]

            # 检查收敛
            if np.allclose(centroids, new_centroids, atol=1e-6):
                break
            centroids = new_centroids

        return centroids, labels

    def __repr__(self) -> str:
        return (
            f"KeyframeExtractor(method='{self.method}', "
            f"threshold={self.threshold}, max_keyframes={self.max_keyframes})"
        )
