"""
NER 序列标注 - 命名实体识别系统
================================

提供多种 NER 方法:
- 基于规则: RegexNER, DictNER
- 统计模型: HMM, StandaloneCRF
- 深度学习: BiLSTM, BiLSTM_CRF

支持的标注方案:
- BIO: Begin, Inside, Outside
- BIOES: Begin, Inside, Outside, End, Single

评估指标:
- Accuracy: token 级别准确率
- Precision: 实体级别精确率
- Recall: 实体级别召回率
- F1: 精确率和召回率的调和平均
"""

# 标注方案
from .schemes import (
    BIOEncoder, BIOESEncoder, bio_to_bioes, bioes_to_bio
)

# 数据处理
from .dataset import NERDataset, Vocabulary, TagVocabulary

# 统计模型
from .hmm import HMM
from .standalone_crf import StandaloneCRF

# 深度学习模型
from .bilstm import BiLSTM, BiLSTMWithSoftmax
from .crf import CRF
from .model import BiLSTM_CRF

# 训练和评估
from .trainer import Trainer
from .evaluator import Evaluator

# 基于规则的 NER (需要单独导入)
# from .rules import RegexNER, DictNER

__version__ = "2.0.0"
__all__ = [
    # 标注方案
    "BIOEncoder", "BIOESEncoder", "bio_to_bioes", "bioes_to_bio",
    # 数据处理
    "NERDataset", "Vocabulary", "TagVocabulary",
    # 统计模型
    "HMM", "StandaloneCRF",
    # 深度学习模型
    "BiLSTM", "BiLSTMWithSoftmax", "CRF", "BiLSTM_CRF",
    # 训练和评估
    "Trainer", "Evaluator",
]
