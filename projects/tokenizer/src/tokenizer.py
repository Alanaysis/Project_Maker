"""
主分词器模块
提供统一的分词接口
"""

from .dictionary import Dictionary
from .fmm import FMM
from .bmm import BMM
from .hmm import HMM


class Tokenizer:
    """主分词器类"""

    def __init__(self):
        """初始化分词器"""
        self.dictionary = Dictionary()
        self._fmm = None
        self._bmm = None
        self._hmm = HMM()

    def load_dictionary(self, filepath):
        """
        加载词典文件

        Args:
            filepath: 词典文件路径

        Raises:
            FileNotFoundError: 文件不存在
        """
        self.dictionary.load(filepath)
        self._fmm = FMM(self.dictionary)
        self._bmm = BMM(self.dictionary)

    def load_hmm_model(self, filepath):
        """
        加载 HMM 模型

        Args:
            filepath: HMM 模型文件路径

        Raises:
            FileNotFoundError: 文件不存在
        """
        self._hmm.load_model(filepath)

    def train_hmm(self, corpus):
        """
        训练 HMM 模型

        Args:
            corpus: 标注语料列表
        """
        self._hmm.train(corpus)

    def fmm(self, text):
        """
        正向最大匹配分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Raises:
            RuntimeError: 词典未加载
        """
        if self._fmm is None:
            raise RuntimeError("请先加载词典")
        return self._fmm.segment(text)

    def bmm(self, text):
        """
        逆向最大匹配分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Raises:
            RuntimeError: 词典未加载
        """
        if self._bmm is None:
            raise RuntimeError("请先加载词典")
        return self._bmm.segment(text)

    def hmm(self, text):
        """
        HMM 分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表
        """
        return self._hmm.segment(text)

    def segment(self, text, method='fmm'):
        """
        统一分词接口

        Args:
            text: 待分词的文本
            method: 分词方法，可选 'fmm', 'bmm', 'hmm'

        Returns:
            list: 分词结果列表

        Raises:
            ValueError: 不支持的分词方法
        """
        if method == 'fmm':
            return self.fmm(text)
        elif method == 'bmm':
            return self.bmm(text)
        elif method == 'hmm':
            return self.hmm(text)
        else:
            raise ValueError(f"不支持的分词方法: {method}")
