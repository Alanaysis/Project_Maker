#!/usr/bin/env python3
"""
ViT 模型变体对比示例

对比不同大小的 ViT 模型的参数量和推理速度。
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
from src.vit import VisionTransformer


def compare_models():
    """对比不同 ViT 变体"""
    print("=" * 70)
    print("ViT Model Variants Comparison")
    print("=" * 70)

    configs = [
        ('ViT-Tiny',  {'embed_dim': 192,  'depth': 4,  'num_heads': 3}),
        ('ViT-Small', {'embed_dim': 384,  'depth': 8,  'num_heads': 6}),
        ('ViT-Base',  {'embed_dim': 768,  'depth': 12, 'num_heads': 12}),
    ]

    img_size = 224
    patch_size = 16
    num_classes = 1000
    batch_size = 1

    print(f"\nInput: {batch_size}x3x{img_size}x{img_size}, patch_size={patch_size}")
    print(f"Num patches: {(img_size // patch_size) ** 2}")
    print()

    print(f"{'Model':<12} {'Params':>12} {'Depth':>6} {'Dim':>5} {'Heads':>6} {'Time(ms)':>10}")
    print("-" * 60)

    for name, cfg in configs:
        model = VisionTransformer(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
            **cfg,
        )
        model.eval()

        # 参数量
        params = sum(p.numel() for p in model.parameters())

        # 推理时间
        x = torch.randn(batch_size, 3, img_size, img_size)

        # Warmup
        with torch.no_grad():
            for _ in range(3):
                model(x)

        # 计时
        start = time.time()
        with torch.no_grad():
            for _ in range(10):
                model(x)
        elapsed = (time.time() - start) / 10 * 1000  # ms

        print(f"{name:<12} {params:>12,} {cfg['depth']:>6} {cfg['embed_dim']:>5} "
              f"{cfg['num_heads']:>6} {elapsed:>10.1f}")

    print()


def compare_patch_sizes():
    """对比不同 patch 大小的影响"""
    print("=" * 70)
    print("Patch Size Comparison (ViT-Tiny, 224x224)")
    print("=" * 70)

    patch_sizes = [8, 14, 16, 28, 32]
    img_size = 224

    print(f"\n{'Patch':>6} {'NumPatches':>11} {'SeqLen':>7} {'Params':>12} {'Time(ms)':>10}")
    print("-" * 50)

    for ps in patch_sizes:
        if img_size % ps != 0:
            continue

        num_patches = (img_size // ps) ** 2

        model = VisionTransformer(
            img_size=img_size,
            patch_size=ps,
            num_classes=10,
            embed_dim=192,
            depth=4,
            num_heads=3,
        )
        model.eval()

        params = sum(p.numel() for p in model.parameters())

        x = torch.randn(1, 3, img_size, img_size)
        with torch.no_grad():
            # Warmup
            for _ in range(3):
                model(x)
            start = time.time()
            for _ in range(10):
                model(x)
            elapsed = (time.time() - start) / 10 * 1000

        print(f"{ps:>6} {num_patches:>11} {num_patches + 1:>7} {params:>12,} {elapsed:>10.1f}")

    print()


if __name__ == '__main__':
    compare_models()
    compare_patch_sizes()
    print("Done!")
