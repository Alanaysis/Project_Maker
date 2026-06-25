"""
Image Captioning - 图像描述生成

实现基于 CNN + LSTM + Attention 的图像描述生成模型。
"""

from .encoder import CNNEncoder
from .attention import Attention
from .decoder import LSTMDecoder
from .model import ImageCaptioningModel
from .vocabulary import Vocabulary
from .dataset import CaptionDataset, collate_fn, SyntheticCaptionDataset, synthetic_collate_fn
from .trainer import Trainer

__all__ = [
    "CNNEncoder",
    "Attention",
    "LSTMDecoder",
    "ImageCaptioningModel",
    "Vocabulary",
    "CaptionDataset",
    "collate_fn",
    "SyntheticCaptionDataset",
    "synthetic_collate_fn",
    "Trainer",
]
