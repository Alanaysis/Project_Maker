"""
Video Understanding - 视频内容理解与摘要系统

核心流程:
视频输入 → 帧采样 → 特征提取 → 内容理解 → 摘要生成
"""

__version__ = "0.1.0"

from video_understanding.models.feature_extractor import VideoFeatureExtractor
from video_understanding.models.classifier import VideoContentClassifier
from video_understanding.models.summarizer import VideoSummarizer
from video_understanding.data.frame_sampler import FrameSampler
from video_understanding.data.video_dataset import VideoDataset
from video_understanding.core.keyframe_extractor import KeyframeExtractor
from video_understanding.core.content_analyzer import ContentAnalyzer

__all__ = [
    "VideoFeatureExtractor",
    "VideoContentClassifier",
    "VideoSummarizer",
    "FrameSampler",
    "VideoDataset",
    "KeyframeExtractor",
    "ContentAnalyzer",
]
