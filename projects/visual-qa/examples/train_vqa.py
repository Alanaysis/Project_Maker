"""
VQA 训练示例

演示如何训练 VQA 模型。
"""

import torch
from torch.utils.data import DataLoader

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import VQAModel, VQADataset, create_sample_data
from src.dataset import collate_fn
from src.trainer import VQATrainer


def main():
    """训练 VQA 模型"""
    print("=" * 60)
    print("VQA 模型训练示例")
    print("=" * 60)

    # 超参数
    vocab_size = 2000
    num_answers = 50
    embed_dim = 128
    image_feature_dim = 256
    text_feature_dim = 256
    fusion_dim = 512
    hidden_dim = 256
    batch_size = 16
    num_epochs = 5
    learning_rate = 1e-3

    # 创建示例数据
    print("\n1. 创建示例数据...")
    train_questions, train_image_ids, train_answers, vocab = create_sample_data(
        num_samples=200,
        num_images=40,
        num_answers=num_answers,
    )
    val_questions, val_image_ids, val_answers, _ = create_sample_data(
        num_samples=50,
        num_images=10,
        num_answers=num_answers,
    )

    print(f"   训练样本: {len(train_questions)}")
    print(f"   验证样本: {len(val_questions)}")
    print(f"   词汇表大小: {len(vocab)}")
    print(f"   答案数量: {num_answers}")

    # 创建数据集和数据加载器
    print("\n2. 创建数据加载器...")
    train_dataset = VQADataset(train_questions, train_image_ids, train_answers, vocab, feature_dim=image_feature_dim)
    val_dataset = VQADataset(val_questions, val_image_ids, val_answers, vocab, feature_dim=image_feature_dim)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_fn,
    )

    # 创建模型
    print("\n3. 创建 VQA 模型...")
    model = VQAModel(
        vocab_size=len(vocab),
        num_answers=num_answers,
        image_backbone='resnet18',
        text_encoder_type='lstm',
        fusion_type='concat',
        embed_dim=embed_dim,
        image_feature_dim=image_feature_dim,
        text_feature_dim=text_feature_dim,
        fusion_dim=fusion_dim,
        hidden_dim=hidden_dim,
        dropout=0.1,
        pretrained_image=False,
    )

    model_info = model.get_model_info()
    print(f"   模型参数量: {model_info['total_params']:,}")
    print(f"   可训练参数: {model_info['trainable_params']:,}")

    # 创建训练器
    print("\n4. 初始化训练器...")
    trainer = VQATrainer(
        model=model,
        learning_rate=learning_rate,
        weight_decay=1e-4,
    )

    # 训练
    print("\n5. 开始训练...")
    print("-" * 60)
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
    )

    # 打印训练结果
    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)
    print(f"最终训练损失: {history['train_loss'][-1]:.4f}")
    print(f"最终训练准确率: {history['train_acc'][-1]:.2%}")
    if history['val_loss']:
        print(f"最终验证损失: {history['val_loss'][-1]:.4f}")
        print(f"最终验证准确率: {history['val_acc'][-1]:.2%}")

    # 演示预测
    print("\n6. 预测示例...")
    model.eval()
    with torch.no_grad():
        sample = val_dataset[0]
        question_ids = sample['question_ids'].unsqueeze(0).to(trainer.device)
        image_features = sample['image_features'].unsqueeze(0).to(trainer.device)

        predictions, confidence = model.predict(
            image_features=image_features,
            question_ids=question_ids,
        )
        print(f"   预测答案索引: {predictions[0].item()}")
        print(f"   置信度: {confidence[0].item():.2%}")

    print("\n训练完成!")


if __name__ == '__main__':
    main()
