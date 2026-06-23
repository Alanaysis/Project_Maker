#!/usr/bin/env python3
"""
NER 训练示例
============

演示如何使用 BiLSTM-CRF 进行命名实体识别
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
from torch.utils.data import DataLoader

from src.model import BiLSTM_CRF
from src.dataset import (Vocabulary, TagVocabulary, NERDataset,
                          create_sample_data)
from src.trainer import Trainer
from src.evaluator import Evaluator


def main():
    print("=" * 60)
    print("NER - BiLSTM-CRF 命名实体识别训练")
    print("=" * 60)

    # 设置随机种子
    torch.manual_seed(42)

    # 1. 准备数据
    print("\n[1] 准备数据...")
    sentences, tags = create_sample_data()
    print(f"  样本数量: {len(sentences)}")

    # 2. 构建词表
    print("\n[2] 构建词表...")
    vocab = Vocabulary(min_freq=1)
    vocab.build(sentences)
    tag_vocab = TagVocabulary()
    tag_vocab.build(tags)
    print(f"  词表大小: {len(vocab)}")
    print(f"  标签数量: {len(tag_vocab)}")
    print(f"  标签: {tag_vocab.tag2idx}")

    # 3. 创建数据集
    print("\n[3] 创建数据集...")
    max_len = 15
    dataset = NERDataset(sentences, tags, vocab, tag_vocab, max_len=max_len)

    # 分割训练/验证集
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )
    print(f"  训练集: {train_size} 样本")
    print(f"  验证集: {val_size} 样本")

    # 创建数据加载器
    batch_size = 4
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    # 4. 创建模型
    print("\n[4] 创建模型...")
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

    # 5. 训练
    print("\n[5] 开始训练...")
    trainer = Trainer(model, tag_vocab=tag_vocab, learning_rate=0.005)
    history = trainer.train(
        train_loader, val_loader,
        num_epochs=30,
        early_stopping=5,
        verbose=True
    )

    print(f"\n  最佳验证 F1: {history['best_f1']:.4f}")

    # 6. 最终评估
    print("\n[6] 最终评估...")
    final_results = trainer.evaluate(val_loader)
    evaluator = Evaluator(tag_vocab)
    evaluator.print_results(final_results)

    # 7. 预测示例
    print("\n[7] 预测示例...")
    test_sentences = [
        ["John", "works", "at", "Google"],
        ["Mary", "lives", "in", "Beijing"],
        ["Apple", "is", "in", "Cupertino"],
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

        # 提取实体
        entities = []
        current_entity = None
        current_tokens = []
        for token, tag in zip(test_tokens, pred_tags):
            if tag.startswith("B-"):
                if current_entity:
                    entities.append((current_entity, ' '.join(current_tokens)))
                current_entity = tag[2:]
                current_tokens = [token]
            elif tag.startswith("I-") and current_entity:
                current_tokens.append(token)
            else:
                if current_entity:
                    entities.append((current_entity, ' '.join(current_tokens)))
                    current_entity = None
                    current_tokens = []
        if current_entity:
            entities.append((current_entity, ' '.join(current_tokens)))

        if entities:
            print(f"  实体: {entities}")
        else:
            print(f"  实体: 无")

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
