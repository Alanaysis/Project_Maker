"""
DETR (DEtection TRansformer) - 端到端目标检测模型
"""

from .backbone import Backbone, build_backbone
from .transformer import Transformer, build_transformer
from .matcher import HungarianMatcher
from .detr import DETR, build_detr
from .loss import SetCriterion
from .utils import nested_tensor_from_tensor_list
from .dataset import SimpleDetectionDataset, create_simple_dataset, collate_fn

__all__ = [
    'Backbone',
    'build_backbone',
    'Transformer',
    'build_transformer',
    'HungarianMatcher',
    'DETR',
    'build_detr',
    'SetCriterion',
    'nested_tensor_from_tensor_list',
    'SimpleDetectionDataset',
    'create_simple_dataset',
    'collate_fn',
]
