#!/usr/bin/env python3
"""
NER 训练示例
============

演示所有 NER 方法:
1. 基于规则: 正则匹配、词典匹配
2. 统计模型: HMM
3. 深度学习: BiLSTM-CRF
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
from torch.utils.data import DataLoader

from src.rules.regex_ner import RegexNER
from src.rules.dict_ner import DictNER
from src.hmm import HMM
from src.model import BiLSTM_CRF
from src.dataset import (Vocabulary, TagVocabulary, NERDataset,
                          create_sample_data)
from src.schemes import BIOEncoder, BIOESEncoder, bio_to_bioes
from src.trainer import Trainer
from src.evaluator import Evaluator


def demo_rule_based():
    """演示基于规则的 NER"""
    print("\n" + "=" * 60)
    print("[1] 基于规则的 NER")
    print("=" * 60)

    # 正则匹配
    print("\n--- 正则匹配 ---")
    regex_ner = RegexNER()

    test_texts = [
        "请拨打 13812345678 联系我",
        "发送邮件到 test@example.com",
        "访问 https://www.example.com 获取详情",
        "日期 2024-01-15 有会议",
    ]

    for text in test_texts:
        entities = regex_ner.recognize(text)
        print(f"  输入: {text}")
        print(f"  实体: {entities}")

    # 词典匹配
    print("\n--- 词典匹配 ---")
    dict_ner = DictNER()
    dict_ner.add_entities({
        "北京": "LOC",
        "北京市": "LOC",
        "上海": "LOC",
        "清华大学": "ORG",
        "北京大学": "ORG",
        "谷歌": "ORG",
        "百度": "ORG",
    })

    test_texts = [
        "我去了北京市清华大学",
        "上海和北京都是大城市",
        "谷歌和百度是科技公司",
    ]

    for text in test_texts:
        entities = dict_ner.recognize(text, method="forward")
        print(f"  输入: {text}")
        print(f"  实体: {entities}")


def demo_hmm():
    """演示 HMM NER"""
    print("\n" + "=" * 60)
    print("[2] HMM NER")
    print("=" * 60)

    sentences, tags = create_sample_data()

    # 训练
    print("\n--- 训练 HMM ---")
    hmm = HMM(smooth=1e-6)
    hmm.fit(sentences, tags)
    print(f"  标签数量: {hmm.num_tags}")
    print(f"  词表大小: {hmm.vocab_size}")

    # 预测
    print("\n--- 预测 ---")
    test_sentences = [
        ["John", "works", "at", "Google"],
        ["Mary", "lives", "in", "Beijing"],
        ["Apple", "is", "in", "Cupertino"],
    ]

    for tokens in test_sentences:
        predicted = hmm.predict(tokens)
        print(f"  输入: {' '.join(tokens)}")
        print(f"  预测: {' '.join(predicted)}")

        # 提取实体
        entities = BIOEncoder.decode(predicted)
        print(f"  实体: {entities}")


def demo_bilstm_crf():
    """演示 BiLSTM-CRF NER"""
    print("\n" + "=" * 60)
    print("[3] BiLSTM-CRF NER")
    print("=" * 60)

    torch.manual_seed(42)

    # 准备数据
    sentences, tags = create_sample_data()
    print(f"\n  样本数量: {len(sentences)}")

    vocab = Vocabulary(min_freq=1)
    vocab.build(sentences)
    tag_vocab = TagVocabulary()
    tag_vocab.build(tags)
    print(f"  词表大小: {len(vocab)}")
    print(f"  标签数量: {len(tag_vocab)}")

    # 创建数据集
    max_len = 15
    dataset = NERDataset(sentences, tags, vocab, tag_vocab, max_len=max_len)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    batch_size = 4
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    # 创建模型
    model = BiLSTM_CRF(
        vocab_size=len(vocab),
        num_tags=len(tag_vocab),
        embedding_dim=64,
        hidden_dim=128,
        num_layers=1,
        dropout=0.3
    )
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  模型参数量: {total_params:,}")

    # 训练
    print("\n--- 训练 ---")
    trainer = Trainer(model, tag_vocab=tag_vocab, learning_rate=0.005)
    history = trainer.train(
        train_loader, val_loader,
        num_epochs=30,
        early_stopping=5,
        verbose=True
    )
    print(f"\n  最佳验证 F1: {history['best_f1']:.4f}")

    # 最终评估
    print("\n--- 最终评估 ---")
    final_results = trainer.evaluate(val_loader)
    evaluator = Evaluator(tag_vocab)
    evaluator.print_results(final_results)

    # 预测示例
    print("\n--- 预测示例 ---")
    test_sentences = [
        ["John", "works", "at", "Google"],
        ["Mary", "lives", "in", "Beijing"],
        ["Elon", "Musk", "founded", "Tesla"],
    ]

    for test_tokens in test_sentences:
        token_ids = [vocab[token] for token in test_tokens]
        seq_len = len(token_ids)
        pad_len = max_len - seq_len
        token_ids_padded = token_ids + [vocab.pad_idx] * pad_len
        mask = [1] * seq_len + [0] * pad_len

        tokens_tensor = torch.tensor([token_ids_padded], dtype=torch.long)
        mask_tensor = torch.tensor([mask], dtype=torch.float32)

        pred_tags = trainer.predict(tokens_tensor, mask_tensor)[0]

        print(f"\n  输入: {' '.join(test_tokens)}")
        print(f"  预测: {' '.join(pred_tags)}")

        entities = BIOEncoder.decode(pred_tags)
        if entities:
            entity_strs = []
            for etype, start, end in entities:
                entity_text = " ".join(test_tokens[start:end+1])
                entity_strs.append(f"{entity_text}({etype})")
            print(f"  实体: {', '.join(entity_strs)}")


def demo_schemes():
    """演示标注方案"""
    print("\n" + "=" * 60)
    print("[4] 标注方案演示")
    print("=" * 60)

    entities = [("PER", 0, 1), ("LOC", 3, 4)]

    # BIO
    bio_tags = BIOEncoder.encode(entities, 5)
    print(f"\n  BIO 编码: {bio_tags}")

    # BIOES
    bioes_tags = BIOESEncoder.encode(entities, 5)
    print(f"  BIOES 编码: {bioes_tags}")

    # 转换
    bioes_from_bio = bio_to_bioes(bio_tags)
    print(f"  BIO -> BIOES: {bioes_from_bio}")


def main():
    print("=" * 60)
    print("NER 序列标注 - 命名实体识别系统演示")
    print("=" * 60)

    # 标注方案演示
    demo_schemes()

    # 基于规则的 NER
    demo_rule_based()

    # HMM NER
    demo_hmm()

    # BiLSTM-CRF NER
    demo_bilstm_crf()

    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
