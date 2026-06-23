"""
NER 测试套件
============

测试内容:
1. CRF 层测试
2. BiLSTM-CRF 模型测试
3. 数据处理测试
4. 评估器测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import torch
import tempfile

from src.crf import CRF
from src.model import BiLSTM_CRF
from src.dataset import (Vocabulary, TagVocabulary, NERDataset,
                          read_conll_file, save_conll_file, create_sample_data)
from src.evaluator import Evaluator
from src.trainer import Trainer


class TestCRF:
    """CRF 层测试"""

    def setup_method(self):
        """测试前准备"""
        self.num_tags = 5
        self.batch_size = 2
        self.seq_len = 4
        self.crf = CRF(self.num_tags)

    def test_initialization(self):
        """测试初始化"""
        assert self.crf.num_tags == self.num_tags
        assert self.crf.transitions.shape == (self.num_tags, self.num_tags)
        assert self.crf.start_transitions.shape == (self.num_tags,)
        assert self.crf.end_transitions.shape == (self.num_tags,)

    def test_forward(self):
        """测试前向传播（损失计算）"""
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)
        tags = torch.randint(0, self.num_tags, (self.batch_size, self.seq_len))

        loss = self.crf(emissions, tags)
        assert loss.dim() == 0  # 标量
        assert loss.item() > 0  # 损失应该为正数

    def test_forward_with_mask(self):
        """测试带掩码的前向传播"""
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)
        tags = torch.randint(0, self.num_tags, (self.batch_size, self.seq_len))
        mask = torch.tensor([
            [1, 1, 1, 0],
            [1, 1, 0, 0]
        ], dtype=torch.float32)

        loss = self.crf(emissions, tags, mask)
        assert loss.dim() == 0
        assert loss.item() > 0

    def test_decode(self):
        """测试维特比解码"""
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)

        best_tags = self.crf.decode(emissions)
        assert len(best_tags) == self.batch_size
        for tags in best_tags:
            assert len(tags) == self.seq_len
            for tag in tags:
                assert 0 <= tag < self.num_tags

    def test_decode_with_mask(self):
        """测试带掩码的解码"""
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)
        mask = torch.tensor([
            [1, 1, 1, 0],
            [1, 1, 0, 0]
        ], dtype=torch.float32)

        best_tags = self.crf.decode(emissions, mask)
        assert len(best_tags) == self.batch_size
        assert len(best_tags[0]) == 3  # 第一个序列长度为 3
        assert len(best_tags[1]) == 2  # 第二个序列长度为 2

    def test_score_consistency(self):
        """测试分数一致性：最优路径分数应该 <= 配分函数"""
        emissions = torch.randn(1, 5, self.num_tags)
        tags = torch.randint(0, self.num_tags, (1, 5))
        mask = torch.ones(1, 5)

        score = self.crf._compute_score(emissions, tags, mask)
        log_z = self.crf._compute_log_partition(emissions, mask)

        # 最优路径分数应该 <= 配分函数
        assert score.item() <= log_z.item() + 1e-5

    def test_gradient_flow(self):
        """测试梯度流动"""
        emissions = torch.randn(2, 4, self.num_tags, requires_grad=True)
        tags = torch.randint(0, self.num_tags, (2, 4))

        loss = self.crf(emissions, tags)
        loss.backward()

        assert emissions.grad is not None
        assert not torch.isnan(emissions.grad).any()


class TestBiLSTMCRF:
    """BiLSTM-CRF 模型测试"""

    def setup_method(self):
        """测试前准备"""
        self.vocab_size = 100
        self.num_tags = 5
        self.embedding_dim = 32
        self.hidden_dim = 64
        self.batch_size = 2
        self.seq_len = 8

        self.model = BiLSTM_CRF(
            vocab_size=self.vocab_size,
            num_tags=self.num_tags,
            embedding_dim=self.embedding_dim,
            hidden_dim=self.hidden_dim
        )

    def test_initialization(self):
        """测试模型初始化"""
        assert self.model.embedding.num_embeddings == self.vocab_size
        assert self.model.embedding.embedding_dim == self.embedding_dim
        assert self.model.lstm.hidden_size == self.hidden_dim
        assert self.model.lstm.bidirectional
        assert self.model.hidden2tag.out_features == self.num_tags

    def test_forward(self):
        """测试前向传播"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))
        tags = torch.randint(0, self.num_tags, (self.batch_size, self.seq_len))

        loss = self.model(tokens, tags)
        assert loss.dim() == 0
        assert loss.item() > 0

    def test_decode(self):
        """测试解码"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))

        best_tags = self.model.decode(tokens)
        assert len(best_tags) == self.batch_size
        for tags in best_tags:
            assert len(tags) == self.seq_len

    def test_gradient_flow(self):
        """测试梯度流动"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))
        tags = torch.randint(0, self.num_tags, (self.batch_size, self.seq_len))

        loss = self.model(tokens, tags)
        loss.backward()

        # 检查所有参数都有梯度
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"

    def test_mask_handling(self):
        """测试掩码处理"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))
        tags = torch.randint(0, self.num_tags, (self.batch_size, self.seq_len))
        mask = torch.ones(self.batch_size, self.seq_len)
        mask[0, 5:] = 0  # 第一个序列长度为 5
        mask[1, 3:] = 0  # 第二个序列长度为 3

        loss = self.model(tokens, tags, mask)
        assert loss.dim() == 0

        best_tags = self.model.decode(tokens, mask)
        assert len(best_tags[0]) == 5
        assert len(best_tags[1]) == 3


class TestVocabulary:
    """词表测试"""

    def test_basic_operations(self):
        """测试基本操作"""
        vocab = Vocabulary()
        assert len(vocab) == 2  # PAD 和 UNK
        assert vocab.pad_idx == 0
        assert vocab.unk_idx == 1

        # 未知词
        assert vocab["unknown"] == vocab.unk_idx
        assert vocab.get_token(999) == Vocabulary.UNK

    def test_build(self):
        """测试构建词表"""
        vocab = Vocabulary()
        sentences = [
            ["hello", "world"],
            ["hello", "python"],
            ["foo", "bar", "baz"]
        ]
        vocab.build(sentences)

        assert "hello" in vocab
        assert "world" in vocab
        assert "python" in vocab
        assert vocab["hello"] >= 2  # 不是特殊标记
        assert len(vocab) > 2

    def test_min_freq(self):
        """测试最小频率过滤"""
        vocab = Vocabulary(min_freq=2)
        sentences = [
            ["hello", "world"],
            ["hello", "python"],
            ["foo", "bar"]
        ]
        vocab.build(sentences)

        # "hello" 出现 2 次
        assert "hello" in vocab
        # "world" 只出现 1 次
        assert "world" not in vocab


class TestTagVocabulary:
    """标签表测试"""

    def test_basic_operations(self):
        """测试基本操作"""
        tag_vocab = TagVocabulary()
        assert len(tag_vocab) == 1  # O
        assert tag_vocab["O"] == 0

    def test_build(self):
        """测试构建标签表"""
        tag_vocab = TagVocabulary()
        tags = [
            ["O", "B-PER", "I-PER", "O"],
            ["B-LOC", "I-LOC", "O"]
        ]
        tag_vocab.build(tags)

        assert "B-PER" in tag_vocab
        assert "I-PER" in tag_vocab
        assert "B-LOC" in tag_vocab
        assert "I-LOC" in tag_vocab
        assert tag_vocab["O"] == 0

    def test_get_tag(self):
        """测试获取标签"""
        tag_vocab = TagVocabulary()
        tags = [["O", "B-PER", "I-PER"]]
        tag_vocab.build(tags)

        for idx in range(len(tag_vocab)):
            tag = tag_vocab.get_tag(idx)
            assert tag in tag_vocab


class TestNERDataset:
    """数据集测试"""

    def setup_method(self):
        """测试前准备"""
        self.sentences, self.tags = create_sample_data()
        self.vocab = Vocabulary()
        self.vocab.build(self.sentences)
        self.tag_vocab = TagVocabulary()
        self.tag_vocab.build(self.tags)

    def test_dataset_creation(self):
        """测试数据集创建"""
        dataset = NERDataset(
            self.sentences, self.tags,
            self.vocab, self.tag_vocab,
            max_len=20
        )
        assert len(dataset) == len(self.sentences)

    def test_getitem(self):
        """测试获取数据"""
        dataset = NERDataset(
            self.sentences, self.tags,
            self.vocab, self.tag_vocab,
            max_len=20
        )
        tokens, tag_ids, mask = dataset[0]

        assert tokens.shape == (20,)
        assert tag_ids.shape == (20,)
        assert mask.shape == (20,)
        assert mask.sum().item() == len(self.sentences[0])


class TestCoNLLIO:
    """CoNLL 文件 I/O 测试"""

    def test_save_and_read(self):
        """测试保存和读取"""
        sentences = [
            ["John", "lives", "in", "New", "York"],
            ["Mary", "works", "at", "Google"]
        ]
        tags = [
            ["B-PER", "O", "O", "B-LOC", "I-LOC"],
            ["B-PER", "O", "O", "B-ORG"]
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.conll',
                                          delete=False) as f:
            filepath = f.name

        try:
            save_conll_file(filepath, sentences, tags)
            read_sentences, read_tags = read_conll_file(filepath)

            assert len(read_sentences) == 2
            assert len(read_tags) == 2
            assert read_sentences[0] == ["John", "lives", "in", "New", "York"]
            assert read_tags[0] == ["B-PER", "O", "O", "B-LOC", "I-LOC"]
        finally:
            os.unlink(filepath)


class TestEvaluator:
    """评估器测试"""

    def setup_method(self):
        """测试前准备"""
        self.tag_vocab = TagVocabulary()
        self.tag_vocab.build([
            ["O", "B-PER", "I-PER", "B-LOC", "I-LOC"]
        ])
        self.evaluator = Evaluator(self.tag_vocab)

    def test_perfect_prediction(self):
        """测试完美预测"""
        true_tags = [
            ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        ]
        pred_tags = [
            ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        ]

        results = self.evaluator.evaluate(true_tags, pred_tags)
        assert results["overall"]["precision"] == 1.0
        assert results["overall"]["recall"] == 1.0
        assert results["overall"]["f1"] == 1.0

    def test_partial_prediction(self):
        """测试部分正确预测"""
        true_tags = [
            ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        ]
        pred_tags = [
            ["B-PER", "O", "O", "B-LOC", "O"]
        ]

        results = self.evaluator.evaluate(true_tags, pred_tags)
        # PER: 预测了 B-PER 但没有 I-PER，边界错误
        # LOC: 预测了 B-LOC 但没有 I-LOC，边界错误
        assert results["overall"]["f1"] < 1.0

    def test_no_entities(self):
        """测试无实体情况"""
        true_tags = [["O", "O", "O"]]
        pred_tags = [["O", "O", "O"]]

        results = self.evaluator.evaluate(true_tags, pred_tags)
        # 没有实体时，P/R/F1 都应该是 0
        assert results["overall"]["f1"] == 0.0

    def test_extract_entities(self):
        """测试实体提取"""
        tags = ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        entities = self.evaluator._extract_entities([tags])[0]

        assert len(entities) == 2
        assert entities[0] == ("PER", 0, 1)
        assert entities[1] == ("LOC", 3, 4)


class TestTrainer:
    """训练器测试"""

    def setup_method(self):
        """测试前准备"""
        self.model = BiLSTM_CRF(
            vocab_size=50,
            num_tags=5,
            embedding_dim=16,
            hidden_dim=32
        )
        self.tag_vocab = TagVocabulary()
        self.tag_vocab.build([["O", "B-PER", "I-PER"]])
        self.trainer = Trainer(self.model, tag_vocab=self.tag_vocab, learning_rate=0.01)

    def test_train_epoch(self):
        """测试训练一个 epoch"""
        # 创建简单数据集
        sentences = [["hello", "world"]] * 10
        tags = [["B-PER", "O"]] * 10

        vocab = Vocabulary()
        vocab.build(sentences)
        tag_vocab = TagVocabulary()
        tag_vocab.build(tags)

        dataset = NERDataset(sentences, tags, vocab, tag_vocab, max_len=4)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=4)

        loss = self.trainer.train_epoch(dataloader)
        assert loss > 0
        assert len(self.trainer.train_losses) == 1


class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整流程"""
        # 准备数据
        sentences, tags = create_sample_data()

        vocab = Vocabulary()
        vocab.build(sentences)
        tag_vocab = TagVocabulary()
        tag_vocab.build(tags)

        # 创建数据集
        max_len = 10
        dataset = NERDataset(sentences, tags, vocab, tag_vocab, max_len=max_len)

        # 分割训练/验证
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size]
        )

        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=4, shuffle=True
        )
        val_loader = torch.utils.data.DataLoader(
            val_dataset, batch_size=4
        )

        # 创建模型
        model = BiLSTM_CRF(
            vocab_size=len(vocab),
            num_tags=len(tag_vocab),
            embedding_dim=32,
            hidden_dim=64,
            dropout=0.1
        )

        # 训练
        trainer = Trainer(model, tag_vocab=tag_vocab, learning_rate=0.01)
        history = trainer.train(
            train_loader, val_loader,
            num_epochs=3,
            early_stopping=2,
            verbose=False
        )

        assert "train_losses" in history
        assert "val_f1_scores" in history
        assert len(history["train_losses"]) > 0

    def test_prediction(self):
        """测试预测功能"""
        sentences, tags = create_sample_data()

        vocab = Vocabulary()
        vocab.build(sentences)
        tag_vocab = TagVocabulary()
        tag_vocab.build(tags)

        model = BiLSTM_CRF(
            vocab_size=len(vocab),
            num_tags=len(tag_vocab),
            embedding_dim=32,
            hidden_dim=64
        )

        trainer = Trainer(model, tag_vocab=tag_vocab)

        # 准备输入
        test_sentence = ["John", "lives", "in", "New", "York"]
        token_ids = [vocab[token] for token in test_sentence]
        max_len = 10
        token_ids = token_ids + [vocab.pad_idx] * (max_len - len(token_ids))
        mask = [1] * 5 + [0] * 5

        tokens = torch.tensor([token_ids], dtype=torch.long)
        mask_tensor = torch.tensor([mask], dtype=torch.float32)

        # 预测
        pred_tags = trainer.predict(tokens, mask_tensor)
        assert len(pred_tags) == 1
        assert len(pred_tags[0]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
