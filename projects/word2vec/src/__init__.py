"""
Word2Vec 词向量训练实现

支持 Skip-gram 和 CBOW 模型，使用负采样和层次 Softmax 优化
"""

from .vocabulary import Vocabulary
from .skipgram import SkipGramModel
from .cbow import CBOWModel
from .negative_sampling import NegativeSampler
from .hierarchical_softmax import HierarchicalSoftmax
from .subsampling import SubSampler
from .trainer import Trainer
from .word2vec import Word2Vec
from .evaluation import WordSimilarityEvaluator, AnalogyEvaluator, TSNEVisualizer, WordClustering
from .applications import TextClassifier, SentimentAnalyzer, WordClusterer

__version__ = "2.0.0"
__all__ = [
    "Vocabulary",
    "SkipGramModel",
    "CBOWModel",
    "NegativeSampler",
    "HierarchicalSoftmax",
    "SubSampler",
    "Trainer",
    "Word2Vec",
    "WordSimilarityEvaluator",
    "AnalogyEvaluator",
    "TSNEVisualizer",
    "WordClustering",
    "TextClassifier",
    "SentimentAnalyzer",
    "WordClusterer",
]
