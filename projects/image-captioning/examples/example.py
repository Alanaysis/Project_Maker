"""
图像描述生成示例

演示如何使用图像描述模型：
1. 创建合成数据集
2. 构建词汇表
3. 初始化模型
4. 训练模型
5. 生成图像描述
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from torch.utils.data import DataLoader

from src import (
    ImageCaptioningModel,
    Vocabulary,
    Trainer,
    SyntheticCaptionDataset,
    synthetic_collate_fn,
)


def main():
    """运行图像描述模型示例。"""
    print("=" * 60)
    print("图像描述生成 (Image Captioning) 示例")
    print("=" * 60)

    # 超参数
    VOCAB_SIZE = 100
    EMBED_DIM = 128
    HIDDEN_DIM = 256
    ATTENTION_DIM = 128
    BATCH_SIZE = 8
    NUM_SAMPLES = 64
    NUM_EPOCHS = 3
    IMAGE_SIZE = 128  # 使用较小的图像以加速

    # 设备选择
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n使用设备: {device}")

    # -------------------------------------------------------
    # 1. 创建合成数据集
    # -------------------------------------------------------
    print("\n[1/5] 创建合成数据集...")
    train_dataset = SyntheticCaptionDataset(
        vocab_size=VOCAB_SIZE,
        num_samples=NUM_SAMPLES,
        image_size=IMAGE_SIZE,
        max_caption_length=8,
    )
    val_dataset = SyntheticCaptionDataset(
        vocab_size=VOCAB_SIZE,
        num_samples=16,
        image_size=IMAGE_SIZE,
        max_caption_length=8,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=synthetic_collate_fn,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=synthetic_collate_fn,
        num_workers=0,
    )
    print(f"  训练集: {len(train_dataset)} 个样本")
    print(f"  验证集: {len(val_dataset)} 个样本")

    # -------------------------------------------------------
    # 2. 构建词汇表
    # -------------------------------------------------------
    print("\n[2/5] 构建词汇表...")
    # 使用简单词汇构建词汇表
    sample_captions = [
        "a dog is running",
        "a cat is sleeping",
        "a bird is flying",
        "a car is moving",
        "a person is walking",
    ]
    vocabulary = Vocabulary.from_captions(sample_captions, min_freq=1)
    # 为合成数据集手动扩展词汇表
    for i in range(4, VOCAB_SIZE):
        vocabulary.word2idx[f"word_{i}"] = i
        vocabulary.idx2word[i] = f"word_{i}"
    print(f"  词汇表大小: {len(vocabulary)}")

    # -------------------------------------------------------
    # 3. 初始化模型
    # -------------------------------------------------------
    print("\n[3/5] 初始化模型...")
    model = ImageCaptioningModel(
        vocab_size=VOCAB_SIZE,
        embed_dim=EMBED_DIM,
        hidden_dim=HIDDEN_DIM,
        attention_dim=ATTENTION_DIM,
        encoder_backbone="resnet18",  # 使用 ResNet-18 加速
        encoder_pretrained=True,
        dropout=0.3,
        attention_type="bahdanau",
    )

    # 统计参数量
    param_counts = model.count_parameters()
    print(f"  编码器参数量: {param_counts['encoder']:,}")
    print(f"  解码器参数量: {param_counts['decoder']:,}")
    print(f"  总参数量: {param_counts['total']:,}")

    # -------------------------------------------------------
    # 4. 训练模型
    # -------------------------------------------------------
    print("\n[4/5] 训练模型...")
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        learning_rate=1e-3,
        device=str(device),
        checkpoint_dir=os.path.join(os.path.dirname(__file__), "checkpoints"),
    )

    history = trainer.train(
        num_epochs=NUM_EPOCHS,
        print_every=1,
        save_every=0,  # 不保存检查点
    )

    # 打印训练摘要
    print(f"\n训练摘要:")
    print(f"  最终训练损失: {history['train_loss'][-1]:.4f}")
    if history['val_loss']:
        print(f"  最终验证损失: {history['val_loss'][-1]:.4f}")

    # -------------------------------------------------------
    # 5. 生成描述
    # -------------------------------------------------------
    print("\n[5/5] 生成图像描述...")
    # 创建测试图像
    test_images = torch.randn(3, 3, IMAGE_SIZE, IMAGE_SIZE).to(device)

    # 使用模型生成描述
    model.eval()
    with torch.no_grad():
        encoder_out = model.encoder(test_images)
        generated_indices = model.decoder.generate(
            encoder_out,
            max_length=10,
            start_idx=vocabulary.start_idx,
            end_idx=vocabulary.end_idx,
            temperature=0.8,
        )

    # 解码生成的描述
    for i, indices in enumerate(generated_indices):
        caption = vocabulary.decode(indices, skip_special=True)
        print(f"  图像 {i+1}: {caption if caption else '(空序列)'}")

    # 展示注意力权重可视化（获取注意力权重）
    print("\n[附加] 展示注意力机制...")
    with torch.no_grad():
        single_image = test_images[:1]
        encoder_out = model.encoder(single_image)
        # 使用 teacher forcing 获取注意力权重
        dummy_caption = torch.tensor([[vocabulary.start_idx, 5, 6]], device=device)
        dummy_length = torch.tensor([3], device=device)
        predictions, attn_weights = model.decoder(encoder_out, dummy_caption, dummy_length)
        print(f"  注意力权重形状: {attn_weights.shape}")
        print(f"  预测输出形状: {predictions.shape}")

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
