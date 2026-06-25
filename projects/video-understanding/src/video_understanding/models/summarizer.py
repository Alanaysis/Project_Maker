"""视频摘要生成器模块

基于关键帧选择和特征聚合，生成视频的文字摘要和关键帧摘要。
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from video_understanding.models.feature_extractor import VideoFeatureExtractor


class VideoSummarizer(nn.Module):
    """视频摘要生成器

    通过分析帧特征的重要性，选取关键帧并生成摘要。

    工作流程：
    1. 提取所有帧的特征
    2. 计算每帧的重要性分数
    3. 选取 top-k 关键帧
    4. 生成文本摘要

    Args:
        backbone: 特征提取骨干网络
        feature_dim: 特征维度
        num_keyframes: 关键帧数量
    """

    def __init__(
        self,
        backbone: str = "resnet18",
        feature_dim: int = 512,
        num_keyframes: int = 5,
    ):
        super().__init__()
        self.num_keyframes = num_keyframes
        self.feature_dim = feature_dim

        # 特征提取器
        self.feature_extractor = VideoFeatureExtractor(
            backbone=backbone,
            pretrained=True,
            feature_dim=feature_dim,
            pooling="mean",
        )

        # 重要性评分网络
        self.importance_net = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 2),
            nn.ReLU(inplace=True),
            nn.Linear(feature_dim // 2, 1),
            nn.Sigmoid(),
        )

        # 场景变化检测网络
        self.change_net = nn.Sequential(
            nn.Linear(feature_dim * 2, feature_dim),
            nn.ReLU(inplace=True),
            nn.Linear(feature_dim, 1),
            nn.Sigmoid(),
        )

    def compute_importance_scores(self, frames: torch.Tensor) -> torch.Tensor:
        """计算每帧的重要性分数

        Args:
            frames: 视频帧，形状为 (T, C, H, W)

        Returns:
            重要性分数，形状为 (T,)
        """
        self.eval()
        with torch.no_grad():
            features = self.feature_extractor.extract_frame_features(frames)
            scores = self.importance_net(features).squeeze(-1)
        return scores

    def detect_scene_changes(self, frames: torch.Tensor, threshold: float = 0.5) -> List[int]:
        """检测场景变化点

        Args:
            frames: 视频帧，形状为 (T, C, H, W)
            threshold: 变化阈值

        Returns:
            场景变化帧索引列表
        """
        self.eval()
        with torch.no_grad():
            features = self.feature_extractor.extract_frame_features(frames)
            T = features.shape[0]
            change_scores = []

            for i in range(1, T):
                pair = torch.cat([features[i - 1], features[i]], dim=-1).unsqueeze(0)
                score = self.change_net(pair).item()
                change_scores.append(score)

            change_indices = [
                i + 1 for i, score in enumerate(change_scores) if score > threshold
            ]

        return change_indices

    def extract_keyframes(self, frames: torch.Tensor) -> Tuple[List[int], np.ndarray]:
        """提取关键帧

        Args:
            frames: 视频帧，形状为 (T, C, H, W)

        Returns:
            (关键帧索引列表, 重要性分数数组)
        """
        scores = self.compute_importance_scores(frames)
        k = min(self.num_keyframes, frames.shape[0])
        top_indices = torch.topk(scores, k).indices
        top_indices = top_indices.sort().values

        return top_indices.tolist(), scores[top_indices].detach().numpy()

    def generate_summary(self, frames: torch.Tensor) -> Dict:
        """生成视频摘要

        Args:
            frames: 视频帧，形状为 (T, C, H, W)

        Returns:
            摘要信息字典
        """
        # 提取特征
        features = self.feature_extractor.extract_frame_features(frames)
        video_feature = self.feature_extractor.temporal_pool(features)

        # 计算重要性分数
        scores = self.importance_net(features).squeeze(-1)

        # 选取关键帧
        k = min(self.num_keyframes, frames.shape[0])
        top_indices = torch.topk(scores, k).indices
        top_indices = top_indices.sort().values

        # 检测场景变化
        scene_changes = self.detect_scene_changes(frames)

        summary = {
            "num_frames": frames.shape[0],
            "num_keyframes": k,
            "keyframe_indices": top_indices.tolist(),
            "keyframe_scores": scores[top_indices].tolist(),
            "scene_changes": scene_changes,
            "video_feature": video_feature.detach().numpy(),
            "average_importance": scores.mean().item(),
            "max_importance": scores.max().item(),
        }

        return summary

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        """前向传播，返回视频特征"""
        return self.feature_extractor(frames)

    def __repr__(self) -> str:
        return (
            f"VideoSummarizer(feature_dim={self.feature_dim}, "
            f"num_keyframes={self.num_keyframes})"
        )
