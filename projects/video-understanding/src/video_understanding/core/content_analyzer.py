"""内容理解分析模块

整合特征提取、分类和关键帧提取，提供统一的视频内容分析接口。
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

from video_understanding.core.keyframe_extractor import KeyframeExtractor
from video_understanding.data.frame_sampler import FrameSampler
from video_understanding.models.classifier import VideoContentClassifier
from video_understanding.models.feature_extractor import VideoFeatureExtractor
from video_understanding.models.summarizer import VideoSummarizer


class ContentAnalyzer:
    """视频内容分析器

    整合视频理解的各个组件，提供统一的分析接口。

    工作流程：
    1. 帧采样 - 从视频中采样代表性帧
    2. 特征提取 - 提取视觉特征
    3. 内容分类 - 识别视频内容类别
    4. 关键帧提取 - 选取最具代表性的帧
    5. 摘要生成 - 生成视频摘要

    Args:
        num_classes: 分类类别数
        num_frames: 采样帧数
        num_keyframes: 关键帧数
        backbone: 特征提取骨干网络
        feature_dim: 特征维度
    """

    def __init__(
        self,
        num_classes: int = 10,
        num_frames: int = 16,
        num_keyframes: int = 5,
        backbone: str = "resnet18",
        feature_dim: int = 512,
    ):
        self.num_frames = num_frames
        self.num_keyframes = num_keyframes

        # 组件
        self.sampler = FrameSampler(num_frames=num_frames, method="uniform")
        self.feature_extractor = VideoFeatureExtractor(
            backbone=backbone, feature_dim=feature_dim
        )
        self.classifier = VideoContentClassifier(
            num_classes=num_classes, backbone=backbone, feature_dim=feature_dim
        )
        self.keyframe_extractor = KeyframeExtractor(
            method="histogram", max_keyframes=num_keyframes
        )
        self.summarizer = VideoSummarizer(
            backbone=backbone, feature_dim=feature_dim, num_keyframes=num_keyframes
        )

    def analyze_frames(self, frames: torch.Tensor) -> Dict:
        """分析视频帧序列

        Args:
            frames: 视频帧张量，形状为 (T, C, H, W)

        Returns:
            分析结果字典
        """
        results = {}

        # 1. 特征提取
        frame_features = self.feature_extractor.extract_frame_features(frames)
        video_feature = self.feature_extractor.temporal_pool(frame_features)

        # 2. 内容分类
        frames_batch = frames.unsqueeze(0)  # 添加 batch 维度
        predictions = self.classifier.predict(frames_batch)

        # 3. 重要性评分
        importance_scores = self.summarizer.compute_importance_scores(frames)

        # 4. 关键帧选取
        k = min(self.num_keyframes, frames.shape[0])
        top_indices = torch.topk(importance_scores, k).indices
        keyframe_indices = top_indices.sort().values.tolist()

        # 5. 组装结果
        results["video_feature"] = video_feature.detach().numpy()
        results["frame_features"] = frame_features.detach().numpy()
        results["predictions"] = predictions[0]
        results["importance_scores"] = importance_scores.detach().numpy().tolist()
        results["keyframe_indices"] = keyframe_indices
        results["num_frames"] = frames.shape[0]
        results["feature_dim"] = video_feature.shape[-1]

        return results

    def analyze_numpy_frames(self, frames: List[np.ndarray]) -> Dict:
        """分析 numpy 格式的帧列表

        Args:
            frames: 帧列表

        Returns:
            分析结果字典
        """
        from video_understanding.utils.video_utils import frames_to_tensor

        tensor = frames_to_tensor(frames)
        return self.analyze_frames(tensor)

    def compute_frame_similarity(
        self, frames: torch.Tensor
    ) -> np.ndarray:
        """计算帧间相似度矩阵

        Args:
            frames: 视频帧，形状为 (T, C, H, W)

        Returns:
            相似度矩阵，形状为 (T, T)
        """
        features = self.feature_extractor.extract_frame_features(frames)
        # L2 归一化
        features_norm = torch.nn.functional.normalize(features, p=2, dim=-1)
        # 余弦相似度
        similarity = torch.mm(features_norm, features_norm.t())
        return similarity.detach().numpy()

    def detect_segments(
        self, frames: torch.Tensor, min_segment_length: int = 3
    ) -> List[Tuple[int, int]]:
        """检测视频片段（基于特征变化）

        Args:
            frames: 视频帧
            min_segment_length: 最小片段长度

        Returns:
            片段列表，每个元素为 (起始帧, 结束帧)
        """
        features = self.feature_extractor.extract_frame_features(frames)
        features_np = features.detach().numpy()

        # 计算帧间距离
        distances = []
        for i in range(1, len(features_np)):
            dist = np.linalg.norm(features_np[i] - features_np[i - 1])
            distances.append(dist)

        if not distances:
            return [(0, frames.shape[0] - 1)]

        # 基于阈值分割
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        threshold = mean_dist + std_dist

        segments = []
        start = 0
        for i, dist in enumerate(distances):
            if dist > threshold and (i - start + 1) >= min_segment_length:
                segments.append((start, i))
                start = i + 1

        # 添加最后一个片段
        if start < frames.shape[0]:
            segments.append((start, frames.shape[0] - 1))

        return segments

    def __repr__(self) -> str:
        return (
            f"ContentAnalyzer(num_frames={self.num_frames}, "
            f"num_keyframes={self.num_keyframes})"
        )
