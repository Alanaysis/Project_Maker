"""视频内容分类器模块

基于特征提取器和分类头，实现端到端的视频内容分类。
"""

from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from video_understanding.models.feature_extractor import VideoFeatureExtractor


class VideoContentClassifier(nn.Module):
    """视频内容分类器

    组合特征提取器和分类头，实现视频内容分类。

    Args:
        num_classes: 类别数
        backbone: 骨干网络名称
        pretrained: 是否使用预训练权重
        feature_dim: 特征维度
        pooling: 时序池化方式
        dropout: Dropout 比率
    """

    def __init__(
        self,
        num_classes: int,
        backbone: str = "resnet18",
        pretrained: bool = True,
        feature_dim: int = 512,
        pooling: str = "mean",
        dropout: float = 0.3,
    ):
        super().__init__()
        self.num_classes = num_classes

        # 特征提取器
        self.feature_extractor = VideoFeatureExtractor(
            backbone=backbone,
            pretrained=pretrained,
            feature_dim=feature_dim,
            pooling=pooling,
        )

        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(feature_dim // 2, num_classes),
        )

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        """前向传播

        Args:
            frames: 视频帧，形状为 (B, T, C, H, W)

        Returns:
            分类 logits，形状为 (B, num_classes)
        """
        features = self.feature_extractor(frames)
        logits = self.classifier(features)
        return logits

    def predict(self, frames: torch.Tensor, top_k: int = 5) -> List[Dict]:
        """预测视频类别

        Args:
            frames: 视频帧，形状为 (B, T, C, H, W) 或 (T, C, H, W)
            top_k: 返回前 k 个预测结果

        Returns:
            预测结果列表
        """
        self.eval()
        with torch.no_grad():
            if frames.dim() == 4:
                frames = frames.unsqueeze(0)

            logits = self.forward(frames)
            probs = F.softmax(logits, dim=-1)

            results = []
            for b in range(probs.shape[0]):
                top_probs, top_indices = probs[b].topk(min(top_k, self.num_classes))
                result = {
                    "top_classes": top_indices.tolist(),
                    "top_probs": top_probs.tolist(),
                    "predicted_class": top_indices[0].item(),
                    "confidence": top_probs[0].item(),
                }
                results.append(result)

        return results

    def get_features(self, frames: torch.Tensor) -> torch.Tensor:
        """提取视频特征（不含分类）

        Args:
            frames: 视频帧

        Returns:
            视频特征向量
        """
        return self.feature_extractor(frames)

    def __repr__(self) -> str:
        return (
            f"VideoContentClassifier(num_classes={self.num_classes}, "
            f"backbone='{self.feature_extractor.backbone_name}')"
        )
