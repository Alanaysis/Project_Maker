"""
Visual Question Answering (VQA) 实现

基于 PyTorch 的视觉问答系统，实现图像和文本的多模态融合。
"""

from .vqa_model import VQAModel
from .image_encoder import ImageEncoder
from .text_encoder import TextEncoder
from .fusion import FusionModule
from .answer_predictor import AnswerPredictor
from .dataset import VQADataset, create_sample_data

__all__ = [
    'VQAModel',
    'ImageEncoder',
    'TextEncoder',
    'FusionModule',
    'AnswerPredictor',
    'VQADataset',
    'create_sample_data',
]
