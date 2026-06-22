"""
Word2Vec 主模块

提供 Word2Vec 的高层接口，包括训练、查询、保存/加载功能
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from .vocabulary import Vocabulary
from .skipgram import SkipGramModel
from .negative_sampling import NegativeSampler
from .trainer import Trainer


class Word2Vec:
    """Word2Vec 主类

    提供完整的 Word2Vec 训练和查询功能

    Attributes:
        vector_size: 向量维度
        window: 上下文窗口大小
        min_count: 最小词频
        negative: 负样本数量
        learning_rate: 学习率
        vocab: 词汇表
        model: Skip-gram 模型
    """

    def __init__(self, vector_size: int = 100, window: int = 5,
                 min_count: int = 5, negative: int = 5,
                 learning_rate: float = 0.025):
        """初始化 Word2Vec

        Args:
            vector_size: 向量维度
            window: 上下文窗口大小
            min_count: 最小词频阈值
            negative: 负样本数量
            learning_rate: 学习率
        """
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.negative = negative
        self.learning_rate = learning_rate

        self.vocab: Optional[Vocabulary] = None
        self.model: Optional[SkipGramModel] = None
        self._is_trained = False

    def train(self, corpus: List[List[str]], epochs: int = 100,
              verbose: bool = True) -> List[float]:
        """训练模型

        Args:
            corpus: 分词后的语料，每个元素是一个句子的词列表
            epochs: 训练轮数
            verbose: 是否打印训练信息

        Returns:
            每个 epoch 的损失列表
        """
        # 构建词汇表
        self.vocab = Vocabulary(min_count=self.min_count)
        self.vocab.build(corpus)

        if verbose:
            print(f"Vocabulary size: {len(self.vocab)}")
            print(f"Total words: {self.vocab.total_words}")

        if len(self.vocab) == 0:
            raise ValueError("Vocabulary is empty. Check your corpus or reduce min_count.")

        # 初始化模型
        self.model = SkipGramModel(
            vocab_size=len(self.vocab),
            vector_size=self.vector_size
        )

        # 初始化负采样器
        word_freqs = self.vocab.get_word_freqs_array()
        neg_sampler = NegativeSampler(
            vocab_size=len(self.vocab),
            word_freqs=word_freqs
        )

        # 初始化训练器
        trainer = Trainer(
            model=self.model,
            vocabulary=self.vocab,
            neg_sampler=neg_sampler,
            window=self.window,
            learning_rate=self.learning_rate,
            negative=self.negative
        )

        # 训练
        losses = trainer.train(corpus, epochs=epochs, verbose=verbose)

        self._is_trained = True
        return losses

    def get_vector(self, word: str) -> Optional[np.ndarray]:
        """获取词向量

        Args:
            word: 输入词

        Returns:
            词向量，如果词不在词汇表中返回 None
        """
        if not self._is_trained or self.vocab is None or self.model is None:
            return None

        idx = self.vocab.get_idx(word)
        if idx is None:
            return None

        return self.model.get_vector(idx)

    def most_similar(self, word: str, topn: int = 10) -> List[Tuple[str, float]]:
        """查询相似词

        Args:
            word: 输入词
            topn: 返回的相似词数量

        Returns:
            相似词列表，每个元素是 (word, similarity)
        """
        if not self._is_trained or self.vocab is None or self.model is None:
            return []

        idx = self.vocab.get_idx(word)
        if idx is None:
            return []

        # 计算与所有词的相似度
        vector = self.model.W_in[idx]
        all_vectors = self.model.W_in

        # 余弦相似度
        dot_products = np.dot(all_vectors, vector)
        norms = np.linalg.norm(all_vectors, axis=1) * np.linalg.norm(vector)

        # 避免除以零
        norms = np.where(norms == 0, 1, norms)
        similarities = dot_products / norms

        # 排除自身
        similarities[idx] = -1

        # 获取 topn
        top_indices = np.argsort(similarities)[::-1][:topn]

        results = []
        for i in top_indices:
            word_i = self.vocab.get_word(i)
            if word_i is not None:
                results.append((word_i, float(similarities[i])))

        return results

    def similarity(self, word1: str, word2: str) -> float:
        """计算两个词的相似度

        Args:
            word1: 第一个词
            word2: 第二个词

        Returns:
            余弦相似度，如果任一词不在词汇表中返回 0.0
        """
        if not self._is_trained or self.vocab is None or self.model is None:
            return 0.0

        idx1 = self.vocab.get_idx(word1)
        idx2 = self.vocab.get_idx(word2)

        if idx1 is None or idx2 is None:
            return 0.0

        return self.model.get_similarity(idx1, idx2)

    def analogy(self, positive: str, negative: str, topn: int = 10) -> List[Tuple[str, float]]:
        """词类比

        例如: king - man + woman = queen

        Args:
            positive: 正面词（如 king, woman）
            negative: 负面词（如 man）
            topn: 返回结果数量

        Returns:
            类比结果列表
        """
        if not self._is_trained or self.vocab is None or self.model is None:
            return []

        idx_pos = self.vocab.get_idx(positive)
        idx_neg = self.vocab.get_idx(negative)

        if idx_pos is None or idx_neg is None:
            return []

        # 计算类比向量: positive - negative
        vec = self.model.W_in[idx_pos] - self.model.W_in[idx_neg]

        # 计算与所有词的相似度
        all_vectors = self.model.W_in
        dot_products = np.dot(all_vectors, vec)
        norms = np.linalg.norm(all_vectors, axis=1) * np.linalg.norm(vec)
        norms = np.where(norms == 0, 1, norms)
        similarities = dot_products / norms

        # 排除输入词
        similarities[idx_pos] = -1
        similarities[idx_neg] = -1

        # 获取 topn
        top_indices = np.argsort(similarities)[::-1][:topn]

        results = []
        for i in top_indices:
            word = self.vocab.get_word(i)
            if word is not None:
                results.append((word, float(similarities[i])))

        return results

    def save(self, filepath: str) -> None:
        """保存模型

        Args:
            filepath: 保存路径
        """
        if not self._is_trained:
            raise ValueError("Model not trained yet")

        np.savez(filepath,
                 W_in=self.model.W_in,
                 W_out=self.model.W_out,
                 vector_size=self.vector_size,
                 window=self.window,
                 min_count=self.min_count,
                 negative=self.negative)

        # 保存词汇表
        vocab_data = {
            'word2idx': self.vocab.word2idx,
            'word_freq': self.vocab.word_freq
        }
        np.save(filepath + '_vocab', vocab_data)

    @classmethod
    def load(cls, filepath: str) -> 'Word2Vec':
        """加载模型

        Args:
            filepath: 模型文件路径

        Returns:
            Word2Vec 实例
        """
        data = np.load(filepath + '.npz')

        model = cls(
            vector_size=int(data['vector_size']),
            window=int(data['window']),
            min_count=int(data['min_count']),
            negative=int(data['negative'])
        )

        # 加载词汇表
        vocab_data = np.load(filepath + '_vocab.npy', allow_pickle=True).item()
        model.vocab = Vocabulary(min_count=model.min_count)
        model.vocab.word2idx = vocab_data['word2idx']
        model.vocab.idx2word = {v: k for k, v in vocab_data['word2idx'].items()}
        model.vocab.word_freq = vocab_data['word_freq']

        # 加载模型参数
        model.model = SkipGramModel(len(model.vocab), model.vector_size)
        model.model.W_in = data['W_in']
        model.model.W_out = data['W_out']

        model._is_trained = True
        return model

    @property
    def is_trained(self) -> bool:
        """模型是否已训练"""
        return self._is_trained

    @property
    def vocab_size(self) -> int:
        """词汇表大小"""
        if self.vocab is None:
            return 0
        return len(self.vocab)
