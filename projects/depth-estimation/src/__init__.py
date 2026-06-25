"""
深度估计 (Depth Estimation) - 从单张图像预测深度图

核心模块:
- model: 编码器-解码器深度估计网络
- loss: 深度估计损失函数
- dataset: 数据集处理
- train: 训练脚本
- utils: 可视化与工具函数
"""

from .model import (
    DepthEncoder,
    DepthDecoder,
    DepthEstimationNet,
    SimpleDepthNet,
)
from .loss import (
    DepthMSELoss,
    DepthMAELoss,
    SILogLoss,
    GradientLoss,
    CombinedDepthLoss,
)
from .dataset import (
    SyntheticDepthDataset,
    create_dataloader,
)
from .utils import (
    normalize_depth,
    colorize_depth,
    visualize_depth,
    compute_depth_metrics,
)

__version__ = "1.0.0"
__all__ = [
    # 模型
    "DepthEncoder",
    "DepthDecoder",
    "DepthEstimationNet",
    "SimpleDepthNet",
    # 损失函数
    "DepthMSELoss",
    "DepthMAELoss",
    "SILogLoss",
    "GradientLoss",
    "CombinedDepthLoss",
    # 数据集
    "SyntheticDepthDataset",
    "create_dataloader",
    # 工具
    "normalize_depth",
    "colorize_depth",
    "visualize_depth",
    "compute_depth_metrics",
]
