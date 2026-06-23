"""
NER 序列标注 - BiLSTM-CRF 命名实体识别
======================================

核心组件:
- crf: 条件随机场 (CRF) 层
- model: BiLSTM-CRF 模型
- dataset: 数据处理
- trainer: 训练器
- evaluator: 评估器
"""

from .crf import CRF
from .model import BiLSTM_CRF
from .dataset import NERDataset, Vocabulary, TagVocabulary
from .trainer import Trainer
from .evaluator import Evaluator

__version__ = "1.0.0"
__all__ = ["CRF", "BiLSTM_CRF", "NERDataset", "Vocabulary", "TagVocabulary",
           "Trainer", "Evaluator"]
