"""
主分词器模块
提供统一的分词接口
"""

from .dictionary import Dictionary
from .fmm import FMM
from .bmm import BMM
from .bidirectional import BiMM
from .hmm import HMM
from .english import EnglishTokenizer
from .subword import BPETokenizer, WordPieceTokenizer, UnigramTokenizer
from .pos_tagger import POSTagger


class Tokenizer:
    """主分词器类"""

    def __init__(self):
        """初始化分词器"""
        self.dictionary = Dictionary()
        self._fmm = None
        self._bmm = None
        self._bimm = None
        self._hmm = HMM()
        self._english = EnglishTokenizer()
        self._bpe = BPETokenizer()
        self._wordpiece = WordPieceTokenizer()
        self._unigram = UnigramTokenizer()
        self._pos_tagger = POSTagger(method='rule')

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
        self._bimm = BiMM(self.dictionary)

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

    def bimm(self, text):
        """
        双向最大匹配分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Raises:
            RuntimeError: 词典未加载
        """
        if self._bimm is None:
            raise RuntimeError("请先加载词典")
        return self._bimm.segment(text)

    def hmm(self, text):
        """
        HMM 分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表
        """
        return self._hmm.segment(text)

    def english(self, text):
        """
        英文分词

        Args:
            text: 待分词的英文文本

        Returns:
            list: 分词结果列表
        """
        return self._english.tokenize(text)

    def bpe(self, text):
        """
        BPE 子词分词

        Args:
            text: 待分词的文本

        Returns:
            list: 子词列表
        """
        return self._bpe.tokenize(text)

    def wordpiece(self, text):
        """
        WordPiece 子词分词

        Args:
            text: 待分词的文本

        Returns:
            list: 子词列表
        """
        return self._wordpiece.tokenize(text)

    def unigram(self, text):
        """
        Unigram 子词分词

        Args:
            text: 待分词的文本

        Returns:
            list: 子词列表
        """
        return self._unigram.tokenize(text)

    def pos_tag(self, words, method='rule'):
        """
        词性标注

        Args:
            words: 词语列表
            method: 标注方法，'hmm' 或 'rule'

        Returns:
            list: [(word, tag), ...] 标注结果
        """
        return self._pos_tagger.tag(words, method=method)

    def segment(self, text, method='fmm'):
        """
        统一分词接口

        Args:
            text: 待分词的文本
            method: 分词方法，可选 'fmm', 'bmm', 'bimm', 'hmm', 'english',
                    'bpe', 'wordpiece', 'unigram'

        Returns:
            list: 分词结果列表

        Raises:
            ValueError: 不支持的分词方法
        """
        if method == 'fmm':
            return self.fmm(text)
        elif method == 'bmm':
            return self.bmm(text)
        elif method == 'bimm':
            return self.bimm(text)
        elif method == 'hmm':
            return self.hmm(text)
        elif method == 'english':
            return self.english(text)
        elif method == 'bpe':
            return self.bpe(text)
        elif method == 'wordpiece':
            return self.wordpiece(text)
        elif method == 'unigram':
            return self.unigram(text)
        else:
            raise ValueError(f"不支持的分词方法: {method}")

    def train_bpe(self, corpus, vocab_size=1000):
        """
        训练 BPE 模型

        Args:
            corpus: 训练语料（字符串列表）
            vocab_size: 词表大小
        """
        self._bpe = BPETokenizer(vocab_size=vocab_size)
        self._bpe.train(corpus)

    def train_wordpiece(self, corpus, vocab_size=1000):
        """
        训练 WordPiece 模型

        Args:
            corpus: 训练语料（字符串列表）
            vocab_size: 词表大小
        """
        self._wordpiece = WordPieceTokenizer(vocab_size=vocab_size)
        self._wordpiece.train(corpus)

    def train_unigram(self, corpus, vocab_size=1000):
        """
        训练 Unigram 模型

        Args:
            corpus: 训练语料（字符串列表）
            vocab_size: 词表大小
        """
        self._unigram = UnigramTokenizer(vocab_size=vocab_size)
        self._unigram.train(corpus)
