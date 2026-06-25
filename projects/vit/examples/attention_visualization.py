#!/usr/bin/env python3
"""
注意力可视化示例

展示 ViT 如何"看"图像，通过注意力权重热力图理解模型的注意力模式。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
from src.vit import VisionTransformer
from src.visualization import (
    attention_to_image,
    create_attention_heatmap,
    get_attention_rollout,
    print_model_summary,
)


def visualize_attention():
    """可视化注意力权重"""
    print("=" * 60)
    print("ViT Attention Visualization Demo")
    print("=" * 60)
    print()

    # 创建模型
    model = VisionTransformer(
        img_size=32, patch_size=4, in_channels=3, num_classes=10,
        embed_dim=128, depth=4, num_heads=4,
    )
    model.eval()

    # 打印模型摘要
    print_model_summary(model)

    # 创建一个随机输入图像
    img = torch.randn(1, 3, 32, 32)
    print(f"Input image shape: {img.shape}")

    # 获取注意力权重
    logits, all_attn = model(img, return_attention=True)

    print(f"Output logits shape: {logits.shape}")
    print(f"Number of attention layers: {len(all_attn)}")
    print()

    # 分析每一层的注意力
    for layer_idx, attn in enumerate(all_attn):
        print(f"Layer {layer_idx + 1}:")
        print(f"  Shape: {attn.shape}")
        print(f"  Attention range: [{attn.min():.4f}, {attn.max():.4f}]")

        # CLS token 对其他 patches 的注意力
        cls_attn = attn[0, :, 0, 1:]  # (H, N)
        print(f"  CLS -> patches attention (head 0): {cls_attn[0, :5].tolist()}")
        print()

    # 注意力 Rollout
    print("=" * 60)
    print("Attention Rollout")
    print("=" * 60)

    rollout = get_attention_rollout(all_attn, head_fusion='mean')
    print(f"Rollout shape: {rollout.shape}")
    print(f"CLS -> patches rollout: {rollout[0, 1:6]}")

    # 创建热力图
    print()
    print("=" * 60)
    print("Attention Heatmap (Layer 4, Head 0)")
    print("=" * 60)

    heatmap = create_attention_heatmap(
        all_attn[-1], img_size=32, patch_size=4, head_idx=0
    )
    print(f"Heatmap shape: {heatmap.shape}")
    print(f"Heatmap values range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")

    # 以文本形式展示热力图
    print()
    print("Attention heatmap (higher = brighter):")
    for row in heatmap:
        line = ""
        for val in row:
            if val > 0.8:
                line += "##"
            elif val > 0.6:
                line += "@@"
            elif val > 0.4:
                line += "++"
            elif val > 0.2:
                line += ".."
            else:
                line += "  "
        print(f"  {line}")

    print()
    print("Legend: ## = high attention, @@ = medium-high, ++ = medium, .. = low")


if __name__ == '__main__':
    visualize_attention()
