"""
中文分词器
支持正向最大匹配、逆向最大匹配、双向最大匹配、HMM 分词
支持英文分词、子词分词、词性标注
"""

from .dictionary import Dictionary
from .fmm import FMM
from .bmm import BMM
from .bidirectional import BiMM
from .hmm import HMM
from .tokenizer import Tokenizer
from .english import EnglishTokenizer
from .subword import BPETokenizer, WordPieceTokenizer, UnigramTokenizer
from .pos_tagger import HMMPOSTagger, RuleBasedPOSTagger, POSTagger
from .preprocessor import TextPreprocessor, SearchTokenizer, MachineTranslationTokenizer

__all__ = [
    # 核心分词
    'Dictionary', 'FMM', 'BMM', 'BiMM', 'HMM', 'Tokenizer',
    # 英文分词
    'EnglishTokenizer',
    # 子词分词
    'BPETokenizer', 'WordPieceTokenizer', 'UnigramTokenizer',
    # 词性标注
    'HMMPOSTagger', 'RuleBasedPOSTagger', 'POSTagger',
    # 实际应用
    'TextPreprocessor', 'SearchTokenizer', 'MachineTranslationTokenizer',
]
