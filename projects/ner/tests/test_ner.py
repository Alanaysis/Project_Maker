"""
NER 测试套件
============

测试内容:
1. 标注方案测试 (BIO / BIOES)
2. 基于规则的 NER 测试 (正则匹配、词典匹配)
3. HMM 模型测试
4. CRF 模型测试
5. BiLSTM 模型测试
6. BiLSTM-CRF 模型测试
7. 数据处理测试
8. 评估器测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import torch
import tempfile
import numpy as np

from src.schemes import (
    BIOEncoder, BIOESEncoder, bio_to_bioes, bioes_to_bio
)
from src.rules.regex_ner import RegexNER
from src.rules.dict_ner import DictNER
from src.hmm import HMM
from src.standalone_crf import StandaloneCRF, FeatureExtractor
from src.bilstm import BiLSTM, BiLSTMWithSoftmax
from src.crf import CRF
from src.model import BiLSTM_CRF
from src.dataset import (Vocabulary, TagVocabulary, NERDataset,
                          read_conll_file, save_conll_file, create_sample_data)
from src.evaluator import Evaluator
from src.trainer import Trainer


# ============================================================
# 标注方案测试
# ============================================================

class TestBIOEncoder:
    """BIO 编码器测试"""

    def test_encode(self):
        """测试编码"""
        entities = [("PER", 0, 1), ("LOC", 3, 4)]
        tags = BIOEncoder.encode(entities, 5)
        assert tags == ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]

    def test_decode(self):
        """测试解码"""
        tags = ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        entities = BIOEncoder.decode(tags)
        assert len(entities) == 2
        assert entities[0] == ("PER", 0, 1)
        assert entities[1] == ("LOC", 3, 4)

    def test_roundtrip(self):
        """测试编解码往返"""
        entities = [("PER", 0, 1), ("ORG", 5, 7)]
        tags = BIOEncoder.encode(entities, 8)
        decoded = BIOEncoder.decode(tags)
        assert decoded == entities

    def test_get_tag_set(self):
        """测试获取标签集合"""
        tags = BIOEncoder.get_tag_set(["PER", "LOC"])
        assert "O" in tags
        assert "B-PER" in tags
        assert "I-PER" in tags
        assert "B-LOC" in tags
        assert "I-LOC" in tags

    def test_single_token_entity(self):
        """测试单 token 实体"""
        entities = [("PER", 0, 0)]
        tags = BIOEncoder.encode(entities, 3)
        assert tags == ["B-PER", "O", "O"]


class TestBIOESEncoder:
    """BIOES 编码器测试"""

    def test_encode_multi_token(self):
        """测试多 token 实体编码"""
        entities = [("PER", 0, 1), ("LOC", 3, 4)]
        tags = BIOESEncoder.encode(entities, 5)
        assert tags == ["B-PER", "E-PER", "O", "B-LOC", "E-LOC"]

    def test_encode_single_token(self):
        """测试单 token 实体编码"""
        entities = [("PER", 0, 0)]
        tags = BIOESEncoder.encode(entities, 3)
        assert tags == ["S-PER", "O", "O"]

    def test_decode(self):
        """测试解码"""
        tags = ["B-PER", "E-PER", "O", "S-LOC"]
        entities = BIOESEncoder.decode(tags)
        assert len(entities) == 2
        assert entities[0] == ("PER", 0, 1)
        assert entities[1] == ("LOC", 3, 3)

    def test_roundtrip(self):
        """测试编解码往返"""
        entities = [("PER", 0, 0), ("LOC", 2, 3)]
        tags = BIOESEncoder.encode(entities, 4)
        decoded = BIOESEncoder.decode(tags)
        assert decoded == entities

    def test_get_tag_set(self):
        """测试获取标签集合"""
        tags = BIOESEncoder.get_tag_set(["PER"])
        assert "O" in tags
        assert "B-PER" in tags
        assert "I-PER" in tags
        assert "E-PER" in tags
        assert "S-PER" in tags


class TestSchemeConversion:
    """标注方案转换测试"""

    def test_bio_to_bioes(self):
        """测试 BIO 转 BIOES"""
        bio = ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        bioes = bio_to_bioes(bio)
        assert bioes == ["B-PER", "E-PER", "O", "B-LOC", "E-LOC"]

    def test_bioes_to_bio(self):
        """测试 BIOES 转 BIO"""
        bioes = ["B-PER", "E-PER", "O", "S-LOC"]
        bio = bioes_to_bio(bioes)
        assert bio == ["B-PER", "I-PER", "O", "B-LOC"]

    def test_roundtrip(self):
        """测试往返转换"""
        bio = ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        bioes = bio_to_bioes(bio)
        bio_back = bioes_to_bio(bioes)
        # 注意: BIOES -> BIO 可能会改变单 token 实体的标签
        entities_orig = BIOEncoder.decode(bio)
        entities_back = BIOEncoder.decode(bio_back)
        assert entities_orig == entities_back


# ============================================================
# 基于规则的 NER 测试
# ============================================================

class TestRegexNER:
    """正则匹配 NER 测试"""

    def test_default_patterns(self):
        """测试默认模式"""
        ner = RegexNER()
        types = ner.get_supported_types()
        assert "DATE" in types
        assert "PHONE" in types
        assert "EMAIL" in types
        assert "URL" in types

    def test_phone_recognition(self):
        """测试电话号码识别"""
        ner = RegexNER()
        entities = ner.recognize("请拨打 13812345678 联系我")
        phone_entities = [e for e in entities if e[0] == "PHONE"]
        assert len(phone_entities) > 0
        assert "13812345678" in phone_entities[0][1]

    def test_email_recognition(self):
        """测试邮箱识别"""
        ner = RegexNER()
        entities = ner.recognize("发送到 test@example.com")
        email_entities = [e for e in entities if e[0] == "EMAIL"]
        assert len(email_entities) > 0
        assert "test@example.com" in email_entities[0][1]

    def test_custom_pattern(self):
        """测试自定义模式"""
        ner = RegexNER(patterns={})
        ner.add_pattern("ID", r'\b\d{6}\b')
        entities = ner.recognize("编号 123456 有效")
        assert len(entities) > 0
        assert entities[0][0] == "ID"

    def test_no_match(self):
        """测试无匹配"""
        ner = RegexNER()
        entities = ner.recognize("普通文本没有实体")
        assert len(entities) == 0

    def test_multiple_entities(self):
        """测试多个实体"""
        ner = RegexNER()
        text = "电话 13812345678 邮箱 test@example.com"
        entities = ner.recognize(text)
        assert len(entities) >= 2


class TestDictNER:
    """词典匹配 NER 测试"""

    def test_add_entity(self):
        """测试添加实体"""
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        assert len(ner) == 1

    def test_add_entities(self):
        """测试批量添加"""
        ner = DictNER()
        ner.add_entities({"北京": "LOC", "上海": "LOC", "清华大学": "ORG"})
        assert len(ner) == 3

    def test_forward_match(self):
        """测试正向最大匹配"""
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        ner.add_entity("北京市", "LOC")
        ner.add_entity("清华大学", "ORG")

        entities = ner.recognize("我去了北京市清华大学", method="forward")
        # 正向最大匹配应该匹配 "北京市"
        assert any(e[1] == "北京市" for e in entities)

    def test_backward_match(self):
        """测试逆向最大匹配"""
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        ner.add_entity("北京市", "LOC")

        entities = ner.recognize("北京市", method="backward")
        assert len(entities) > 0

    def test_recognize_tokens(self):
        """测试 token 标注"""
        ner = DictNER()
        ner.add_entity("清华大学", "ORG")

        tokens = ["我", "去", "了", "清", "华", "大", "学"]
        tags = ner.recognize_tokens(tokens)
        assert len(tags) == len(tokens)

    def test_empty_text(self):
        """测试空文本"""
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        entities = ner.recognize("")
        assert len(entities) == 0

    def test_statistics(self):
        """测试统计信息"""
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        ner.add_entity("清华大学", "ORG")
        stats = ner.get_statistics()
        assert stats["total_entities"] == 2


# ============================================================
# HMM 测试
# ============================================================

class TestHMM:
    """HMM 模型测试"""

    def setup_method(self):
        """测试前准备"""
        self.sentences, self.tags = create_sample_data()

    def test_fit(self):
        """测试训练"""
        hmm = HMM()
        hmm.fit(self.sentences, self.tags)

        assert hmm.num_tags > 0
        assert hmm.vocab_size > 0
        assert hmm.pi is not None
        assert hmm.A is not None
        assert hmm.B is not None

    def test_predict(self):
        """测试预测"""
        hmm = HMM()
        hmm.fit(self.sentences, self.tags)

        predicted = hmm.predict(["John", "works", "at", "Google"])
        assert len(predicted) == 4
        assert all(isinstance(t, str) for t in predicted)

    def test_predict_batch(self):
        """测试批量预测"""
        hmm = HMM()
        hmm.fit(self.sentences, self.tags)

        sentences = [
            ["John", "works", "at", "Google"],
            ["Mary", "lives", "in", "Beijing"]
        ]
        predicted = hmm.predict_batch(sentences)
        assert len(predicted) == 2

    def test_transition_matrix(self):
        """测试转移矩阵"""
        hmm = HMM()
        hmm.fit(self.sentences, self.tags)

        A = hmm.get_transition_matrix()
        assert A.shape == (hmm.num_tags, hmm.num_tags)
        # 每行应该近似和为 1
        assert np.allclose(A.sum(axis=1), 1.0, atol=1e-5)

    def test_emission_matrix(self):
        """测试发射矩阵"""
        hmm = HMM()
        hmm.fit(self.sentences, self.tags)

        B = hmm.get_emission_matrix()
        assert B.shape == (hmm.num_tags, hmm.vocab_size)
        assert np.allclose(B.sum(axis=1), 1.0, atol=1e-5)

    def test_empty_sentence(self):
        """测试空句子"""
        hmm = HMM()
        hmm.fit(self.sentences, self.tags)

        predicted = hmm.predict([])
        assert predicted == []


# ============================================================
# CRF 测试
# ============================================================

class TestStandaloneCRF:
    """独立 CRF 模型测试"""

    def setup_method(self):
        """测试前准备"""
        self.sentences = [
            ["John", "works", "at", "Google"],
            ["Mary", "lives", "in", "Beijing"],
        ]
        self.tags = [
            ["B-PER", "O", "O", "B-ORG"],
            ["B-PER", "O", "O", "B-LOC"],
        ]

    def test_feature_extractor(self):
        """测试特征提取器"""
        fe = FeatureExtractor()
        features = fe.extract(["John", "works"], 0, "B-PER")
        assert len(features) > 0
        assert any("word=" in f for f in features)
        assert any("tag=" in f for f in features)

    def test_fit(self):
        """测试训练"""
        crf = StandaloneCRF(max_iterations=5)
        crf.fit(self.sentences, self.tags)

        assert crf.num_tags > 0
        assert crf.weights is not None
        assert crf.transitions is not None

    def test_predict(self):
        """测试预测"""
        crf = StandaloneCRF(max_iterations=5)
        crf.fit(self.sentences, self.tags)

        predicted = crf.predict(["John", "works", "at", "Google"])
        assert len(predicted) == 4
        assert all(isinstance(t, str) for t in predicted)

    def test_train_losses(self):
        """测试训练损失"""
        crf = StandaloneCRF(max_iterations=5)
        crf.fit(self.sentences, self.tags)

        assert len(crf.train_losses) > 0


# ============================================================
# BiLSTM 测试
# ============================================================

class TestBiLSTM:
    """独立 BiLSTM 模型测试"""

    def setup_method(self):
        self.vocab_size = 100
        self.num_tags = 5
        self.batch_size = 2
        self.seq_len = 8
        self.model = BiLSTM(
            vocab_size=self.vocab_size,
            num_tags=self.num_tags,
            embedding_dim=32,
            hidden_dim=64
        )

    def test_initialization(self):
        """测试初始化"""
        assert self.model.embedding.num_embeddings == self.vocab_size
        assert self.model.lstm.bidirectional
        assert self.model.hidden2tag.out_features == self.num_tags

    def test_forward(self):
        """测试前向传播"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))
        emissions = self.model(tokens)
        assert emissions.shape == (self.batch_size, self.seq_len, self.num_tags)

    def test_decode(self):
        """测试解码"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))
        best_tags = self.model.decode(tokens)
        assert len(best_tags) == self.batch_size
        for tags in best_tags:
            assert len(tags) == self.seq_len

    def test_decode_with_mask(self):
        """测试带掩码的解码"""
        tokens = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))
        mask = torch.ones(self.batch_size, self.seq_len)
        mask[0, 5:] = 0
        mask[1, 3:] = 0

        best_tags = self.model.decode(tokens, mask)
        assert len(best_tags[0]) == 5
        assert len(best_tags[1]) == 3


class TestBiLSTMWithSoftmax:
    """带 Softmax 的 BiLSTM 测试"""

    def setup_method(self):
        self.model = BiLSTMWithSoftmax(
            vocab_size=100, num_tags=5,
            embedding_dim=32, hidden_dim=64
        )

    def test_forward(self):
        """测试前向传播"""
        tokens = torch.randint(0, 100, (2, 8))
        tags = torch.randint(0, 5, (2, 8))
        loss = self.model(tokens, tags)
        assert loss.dim() == 0
        assert loss.item() > 0

    def test_decode(self):
        """测试解码"""
        tokens = torch.randint(0, 100, (2, 8))
        best_tags = self.model.decode(tokens)
        assert len(best_tags) == 2


# ============================================================
# CRF 层测试
# ============================================================

class TestCRF:
    """CRF 层测试"""

    def setup_method(self):
        self.num_tags = 5
        self.batch_size = 2
        self.seq_len = 4
        self.crf = CRF(self.num_tags)

    def test_initialization(self):
        assert self.crf.num_tags == self.num_tags
        assert self.crf.transitions.shape == (self.num_tags, self.num_tags)

    def test_forward(self):
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)
        tags = torch.randint(0, self.num_tags, (self.batch_size, self.seq_len))
        loss = self.crf(emissions, tags)
        assert loss.dim() == 0
        assert loss.item() > 0

    def test_decode(self):
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)
        best_tags = self.crf.decode(emissions)
        assert len(best_tags) == self.batch_size

    def test_decode_with_mask(self):
        emissions = torch.randn(self.batch_size, self.seq_len, self.num_tags)
        mask = torch.tensor([[1, 1, 1, 0], [1, 1, 0, 0]], dtype=torch.float32)
        best_tags = self.crf.decode(emissions, mask)
        assert len(best_tags[0]) == 3
        assert len(best_tags[1]) == 2

    def test_score_consistency(self):
        emissions = torch.randn(1, 5, self.num_tags)
        tags = torch.randint(0, self.num_tags, (1, 5))
        mask = torch.ones(1, 5)
        score = self.crf._compute_score(emissions, tags, mask)
        log_z = self.crf._compute_log_partition(emissions, mask)
        assert score.item() <= log_z.item() + 1e-5

    def test_gradient_flow(self):
        emissions = torch.randn(2, 4, self.num_tags, requires_grad=True)
        tags = torch.randint(0, self.num_tags, (2, 4))
        loss = self.crf(emissions, tags)
        loss.backward()
        assert emissions.grad is not None
        assert not torch.isnan(emissions.grad).any()


# ============================================================
# BiLSTM-CRF 模型测试
# ============================================================

class TestBiLSTMCRF:
    """BiLSTM-CRF 模型测试"""

    def setup_method(self):
        self.model = BiLSTM_CRF(
            vocab_size=100, num_tags=5,
            embedding_dim=32, hidden_dim=64
        )

    def test_initialization(self):
        assert self.model.embedding.num_embeddings == 100
        assert self.model.lstm.bidirectional
        assert self.model.hidden2tag.out_features == 5

    def test_forward(self):
        tokens = torch.randint(0, 100, (2, 8))
        tags = torch.randint(0, 5, (2, 8))
        loss = self.model(tokens, tags)
        assert loss.dim() == 0
        assert loss.item() > 0

    def test_decode(self):
        tokens = torch.randint(0, 100, (2, 8))
        best_tags = self.model.decode(tokens)
        assert len(best_tags) == 2

    def test_gradient_flow(self):
        tokens = torch.randint(0, 100, (2, 8))
        tags = torch.randint(0, 5, (2, 8))
        loss = self.model(tokens, tags)
        loss.backward()
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"

    def test_mask_handling(self):
        tokens = torch.randint(0, 100, (2, 8))
        tags = torch.randint(0, 5, (2, 8))
        mask = torch.ones(2, 8)
        mask[0, 5:] = 0
        mask[1, 3:] = 0
        loss = self.model(tokens, tags, mask)
        assert loss.dim() == 0
        best_tags = self.model.decode(tokens, mask)
        assert len(best_tags[0]) == 5
        assert len(best_tags[1]) == 3


# ============================================================
# 数据处理测试
# ============================================================

class TestVocabulary:
    def test_basic_operations(self):
        vocab = Vocabulary()
        assert len(vocab) == 2
        assert vocab.pad_idx == 0
        assert vocab.unk_idx == 1
        assert vocab["unknown"] == vocab.unk_idx

    def test_build(self):
        vocab = Vocabulary()
        vocab.build([["hello", "world"], ["hello", "python"]])
        assert "hello" in vocab
        assert "world" in vocab
        assert len(vocab) > 2

    def test_min_freq(self):
        vocab = Vocabulary(min_freq=2)
        vocab.build([["hello", "world"], ["hello", "python"]])
        assert "hello" in vocab
        assert "world" not in vocab


class TestTagVocabulary:
    def test_basic_operations(self):
        tag_vocab = TagVocabulary()
        assert len(tag_vocab) == 1
        assert tag_vocab["O"] == 0

    def test_build(self):
        tag_vocab = TagVocabulary()
        tag_vocab.build([["O", "B-PER", "I-PER", "O"], ["B-LOC", "I-LOC"]])
        assert "B-PER" in tag_vocab
        assert "I-PER" in tag_vocab
        assert "B-LOC" in tag_vocab


class TestNERDataset:
    def setup_method(self):
        self.sentences, self.tags = create_sample_data()
        self.vocab = Vocabulary()
        self.vocab.build(self.sentences)
        self.tag_vocab = TagVocabulary()
        self.tag_vocab.build(self.tags)

    def test_dataset_creation(self):
        dataset = NERDataset(self.sentences, self.tags, self.vocab, self.tag_vocab, max_len=20)
        assert len(dataset) == len(self.sentences)

    def test_getitem(self):
        dataset = NERDataset(self.sentences, self.tags, self.vocab, self.tag_vocab, max_len=20)
        tokens, tag_ids, mask = dataset[0]
        assert tokens.shape == (20,)
        assert tag_ids.shape == (20,)
        assert mask.shape == (20,)


class TestCoNLLIO:
    def test_save_and_read(self):
        sentences = [["John", "lives", "in", "New", "York"]]
        tags = [["B-PER", "O", "O", "B-LOC", "I-LOC"]]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conll', delete=False) as f:
            filepath = f.name
        try:
            save_conll_file(filepath, sentences, tags)
            read_sentences, read_tags = read_conll_file(filepath)
            assert read_sentences[0] == ["John", "lives", "in", "New", "York"]
            assert read_tags[0] == ["B-PER", "O", "O", "B-LOC", "I-LOC"]
        finally:
            os.unlink(filepath)


# ============================================================
# 评估器测试
# ============================================================

class TestEvaluator:
    def setup_method(self):
        self.tag_vocab = TagVocabulary()
        self.tag_vocab.build([["O", "B-PER", "I-PER", "B-LOC", "I-LOC"]])
        self.evaluator = Evaluator(self.tag_vocab)

    def test_perfect_prediction(self):
        true_tags = [["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]]
        pred_tags = [["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]]
        results = self.evaluator.evaluate(true_tags, pred_tags)
        assert results["overall"]["precision"] == 1.0
        assert results["overall"]["recall"] == 1.0
        assert results["overall"]["f1"] == 1.0
        assert results["overall"]["accuracy"] == 1.0

    def test_partial_prediction(self):
        true_tags = [["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]]
        pred_tags = [["B-PER", "O", "O", "B-LOC", "O"]]
        results = self.evaluator.evaluate(true_tags, pred_tags)
        assert results["overall"]["f1"] < 1.0

    def test_accuracy(self):
        """测试准确率计算"""
        true_tags = [["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]]
        pred_tags = [["B-PER", "I-PER", "O", "B-LOC", "O"]]
        results = self.evaluator.evaluate(true_tags, pred_tags)
        # 4/5 = 0.8
        assert results["overall"]["accuracy"] == 0.8

    def test_no_entities(self):
        true_tags = [["O", "O", "O"]]
        pred_tags = [["O", "O", "O"]]
        results = self.evaluator.evaluate(true_tags, pred_tags)
        assert results["overall"]["f1"] == 0.0
        assert results["overall"]["accuracy"] == 1.0

    def test_extract_entities(self):
        tags = ["B-PER", "I-PER", "O", "B-LOC", "I-LOC"]
        entities = self.evaluator._extract_entities([tags])[0]
        assert len(entities) == 2
        assert entities[0] == ("PER", 0, 1)
        assert entities[1] == ("LOC", 3, 4)


# ============================================================
# 训练器测试
# ============================================================

class TestTrainer:
    def setup_method(self):
        self.model = BiLSTM_CRF(vocab_size=50, num_tags=5, embedding_dim=16, hidden_dim=32)
        self.tag_vocab = TagVocabulary()
        self.tag_vocab.build([["O", "B-PER", "I-PER"]])
        self.trainer = Trainer(self.model, tag_vocab=self.tag_vocab, learning_rate=0.01)

    def test_train_epoch(self):
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


# ============================================================
# 集成测试
# ============================================================

class TestIntegration:
    def test_full_pipeline(self):
        sentences, tags = create_sample_data()
        vocab = Vocabulary()
        vocab.build(sentences)
        tag_vocab = TagVocabulary()
        tag_vocab.build(tags)

        max_len = 10
        dataset = NERDataset(sentences, tags, vocab, tag_vocab, max_len=max_len)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=4, shuffle=True)
        val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=4)

        model = BiLSTM_CRF(vocab_size=len(vocab), num_tags=len(tag_vocab),
                           embedding_dim=32, hidden_dim=64, dropout=0.1)

        trainer = Trainer(model, tag_vocab=tag_vocab, learning_rate=0.01)
        history = trainer.train(train_loader, val_loader, num_epochs=3, early_stopping=2, verbose=False)

        assert "train_losses" in history
        assert "val_f1_scores" in history
        assert len(history["train_losses"]) > 0

    def test_hmm_pipeline(self):
        """测试 HMM 完整流程"""
        sentences, tags = create_sample_data()
        hmm = HMM()
        hmm.fit(sentences, tags)
        predicted = hmm.predict(["John", "works", "at", "Google"])
        assert len(predicted) == 4

    def test_dict_ner_pipeline(self):
        """测试词典 NER 完整流程"""
        ner = DictNER()
        ner.add_entity("北京", "LOC")
        ner.add_entity("清华大学", "ORG")
        entities = ner.recognize("我去了北京市清华大学")
        assert len(entities) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
