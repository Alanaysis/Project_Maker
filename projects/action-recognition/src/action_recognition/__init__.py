"""
Action Recognition - Video-based action recognition using deep learning.

Core pipeline: 视频输入 → 帧采样 → 特征提取 → 时序建模 → 动作分类
"""

__version__ = "1.0.0"

from action_recognition.models.action_classifier import ActionClassifier
from action_recognition.models.temporal_model import TemporalModel
from action_recognition.models.spatial_model import SpatialModel
from action_recognition.data.frame_sampler import FrameSampler
from action_recognition.data.video_dataset import VideoDataset
from action_recognition.features.extractor import FeatureExtractor

__all__ = [
    "ActionClassifier",
    "TemporalModel",
    "SpatialModel",
    "FrameSampler",
    "VideoDataset",
    "FeatureExtractor",
]
