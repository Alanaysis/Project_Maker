"""
Object Tracking - 目标跟踪模块

实现视频中的目标跟踪，包括:
- 相关滤波跟踪 (MOSSE, KCF)
- 卡尔曼滤波
- 跟踪评估
- 视频跟踪演示
"""

from .kalman_filter import KalmanFilter, AdaptiveKalmanFilter
from .correlation_filter import MOSSETracker, KCFTracker, TrackingResult
from .evaluation import (
    TrackingEvaluator,
    OPEBenchmark,
    compute_iou,
    compute_center_error,
    compute_precision,
    compute_success_rate
)
from .video_tracker import VideoTracker, MultiObjectTracker

__all__ = [
    # 卡尔曼滤波
    'KalmanFilter',
    'AdaptiveKalmanFilter',
    # 相关滤波
    'MOSSETracker',
    'KCFTracker',
    'TrackingResult',
    # 评估
    'TrackingEvaluator',
    'OPEBenchmark',
    'compute_iou',
    'compute_center_error',
    'compute_precision',
    'compute_success_rate',
    # 视频跟踪
    'VideoTracker',
    'MultiObjectTracker',
]
