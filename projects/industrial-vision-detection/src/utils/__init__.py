"""
工具函数模块

包含:
- metrics: 评估指标
- visualization: 可视化工具
- boxes: 边界框操作
- general: 通用工具
"""

from .boxes import (
    box_iou,
    box_nms,
    xywh_to_xyxy,
    xyxy_to_xywh
)
from .metrics import (
    compute_iou,
    compute_ap,
    compute_map
)
from .visualization import (
    plot_detections,
    plot_training_curves
)

__all__ = [
    # Boxes
    'box_iou',
    'box_nms',
    'xywh_to_xyxy',
    'xyxy_to_xywh',

    # Metrics
    'compute_iou',
    'compute_ap',
    'compute_map',

    # Visualization
    'plot_detections',
    'plot_training_curves',
]
