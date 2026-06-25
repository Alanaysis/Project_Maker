#!/usr/bin/env python3
"""
Vision Transformer 演示脚本

展示 ViT 的核心功能：
1. 模型构建和参数统计
2. 前向传播
3. 注意力可视化
4. 快速训练演示

用法：
    python demo.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from src.vit import VisionTransformer
from src.patch_embedding import PatchEmbedding
from src.attention import MultiHeadSelfAttention
from src.transformer import TransformerEncoder
from src.visualization import print_model_summary


def demo_patch_embedding():
    """演示 Patch Embedding"""
    print("=" * 60)
    print("Demo 1: Patch Embedding")
    print("=" * 60)

    # 创建 Patch Embedding 层
    patch_embed = PatchEmbedding(
        img_size=32,
        patch_size=4,
        in_channels=3,
        embed_dim=128,
    )

    # 创建一个随机图像
    img = torch.randn(1, 3, 32, 32)
    print(f"Input image shape:  {img.shape}")

    # 通过 Patch Embedding
    output = patch_embed(img)
    print(f"Output shape:       {output.shape}")
    print(f"  -> {patch_embed.num_patches} patches + 1 CLS token = {output.shape[1]} tokens")
    print(f"  -> Each token is {output.shape[2]}-dimensional")
    print()

    # 展示各组件
    print(f"Projection (Conv2d): {patch_embed.projection}")
    print(f"CLS token shape:    {patch_embed.cls_token.shape}")
    print(f"Position embed:     {patch_embed.position_embedding.shape}")
    print()


def demo_attention():
    """演示 Multi-Head Self-Attention"""
    print("=" * 60)
    print("Demo 2: Multi-Head Self-Attention")
    print("=" * 60)

    # 创建注意力层
    attn = MultiHeadSelfAttention(embed_dim=128, num_heads=4)

    # 输入序列
    x = torch.randn(1, 10, 128)  # 1 个样本，10 个 token，128 维
    print(f"Input shape:   {x.shape}")

    # 计算注意力
    output, attn_weights = attn(x)
    print(f"Output shape:  {output.shape}")
    print(f"Attn weights:  {attn_weights.shape}")
    print(f"  -> 4 heads, 10x10 attention matrix")
    print()

    # 展示注意力权重
    print("Attention weights (head 0, sample 0):")
    print(f"  Row sums (should be ~1.0): {attn_weights[0, 0].sum(dim=-1)[:3].tolist()}")
    print()


def demo_transformer_encoder():
    """演示 Transformer Encoder"""
    print("=" * 60)
    print("Demo 3: Transformer Encoder")
    print("=" * 60)

    encoder = TransformerEncoder(embed_dim=128, depth=4, num_heads=4)

    x = torch.randn(1, 10, 128)
    print(f"Input shape:  {x.shape}")

    output, all_attn = encoder(x)
    print(f"Output shape: {output.shape}")
    print(f"Num layers:   {len(all_attn)}")
    print(f"Attn shape per layer: {all_attn[0].shape}")
    print()


def demo_vit_model():
    """演示完整的 ViT 模型"""
    print("=" * 60)
    print("Demo 4: Vision Transformer (Complete Model)")
    print("=" * 60)

    # 创建不同大小的模型
    configs = {
        'ViT-Tiny': {'embed_dim': 192, 'depth': 4, 'heads': 3},
        'ViT-Small': {'embed_dim': 384, 'depth': 8, 'heads': 6},
    }

    for name, cfg in configs.items():
        model = VisionTransformer(
            img_size=32, patch_size=4, in_channels=3, num_classes=10,
            embed_dim=cfg['embed_dim'], depth=cfg['depth'], num_heads=cfg['heads'],
        )
        total_params = sum(p.numel() for p in model.parameters())

        x = torch.randn(1, 3, 32, 32)
        logits, attn_weights = model(x, return_attention=True)

        print(f"{name}:")
        print(f"  Parameters:  {total_params:,}")
        print(f"  Input:       {x.shape}")
        print(f"  Output:      {logits.shape}")
        print(f"  Predicted:   {logits.argmax(dim=-1).item()}")
        print()


def demo_end_to_end():
    """演示端到端训练"""
    print("=" * 60)
    print("Demo 5: End-to-End Training (2 batches)")
    print("=" * 60)

    # 创建小模型
    model = VisionTransformer(
        img_size=8, patch_size=4, in_channels=3, num_classes=5,
        embed_dim=32, depth=2, num_heads=2,
    )

    # 创建虚拟数据
    images = torch.randn(4, 3, 8, 8)
    labels = torch.tensor([0, 1, 2, 3])

    # 前向传播
    logits, _ = model(images)
    loss = torch.nn.functional.cross_entropy(logits, labels)

    print(f"Logits: {logits.shape}")
    print(f"Loss:   {loss.item():.4f}")

    # 反向传播
    loss.backward()

    # 检查梯度
    grad_norms = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norms.append(param.grad.norm().item())

    print(f"Gradient norms: min={min(grad_norms):.6f}, max={max(grad_norms):.6f}")
    print(f"All parameters have gradients: {len(grad_norms) == sum(1 for _ in model.parameters())}")
    print()


def main():
    print("Vision Transformer (ViT) Demo")
    print("Understanding the architecture step by step")
    print()

    demo_patch_embedding()
    demo_attention()
    demo_transformer_encoder()
    demo_vit_model()
    demo_end_to_end()

    print("=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
