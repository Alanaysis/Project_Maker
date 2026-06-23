# YOLO Object Detection Implementation
"""
YOLO (You Only Look Once) Object Detection
============================================

A minimal implementation of the YOLO v1 object detection algorithm.

Modules:
- model: YOLOv1 network architecture
- loss: YOLO loss function
- nms: Non-Maximum Suppression
- dataset: Dataset handling for object detection
- utils: Utility functions (IoU, bbox conversions, etc.)
"""

from .model import YOLOv1
from .loss import YOLOLoss
from .nms import non_max_suppression
from .utils import compute_iou, xywh_to_xyxy, xyxy_to_xywh

__version__ = "0.1.0"
__all__ = [
    "YOLOv1",
    "YOLOLoss",
    "non_max_suppression",
    "compute_iou",
    "xywh_to_xyxy",
    "xyxy_to_xywh",
]
