"""
Word2Vec 词向量训练实现

使用 Skip-gram 模型和负采样优化
"""

from .vocabulary import Vocabulary
from .skipgram import SkipGramModel
from .negative_sampling import NegativeSampler
from .trainer import Trainer
from .word2vec import Word2Vec

__version__ = "1.0.0"
__all__ = ["Vocabulary", "SkipGramModel", "NegativeSampler", "Trainer", "Word2Vec"]
