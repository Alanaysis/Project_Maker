"""
中文分词器
支持正向最大匹配、逆向最大匹配、HMM 分词
"""

from .dictionary import Dictionary
from .fmm import FMM
from .bmm import BMM
from .hmm import HMM
from .tokenizer import Tokenizer

__all__ = ['Dictionary', 'FMM', 'BMM', 'HMM', 'Tokenizer']
