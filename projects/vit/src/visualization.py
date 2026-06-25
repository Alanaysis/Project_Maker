"""
ViT 可视化工具

提供注意力图可视化、训练曲线绘制等功能。
帮助理解 ViT 的内部工作机制。
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, List, Tuple


def attention_to_image(
    attn_weights: torch.Tensor,
    num_heads: int = 0,
    head_idx: int = 0,
) -> np.ndarray:
    """
    将注意力权重转换为可视化图像

    ViT 的注意力权重可以展示模型"看"图像的哪些区域。
    CLS token 对其他 patches 的注意力权重，可以生成注意力热力图。

    参数：
        attn_weights: 注意力权重 (B, H, N+1, N+1) 或 (H, N+1, N+1)
        num_heads: 注意力头数
        head_idx: 要可视化的头索引

    返回：
        注意力图 (N, N) 的 numpy 数组
    """
    if attn_weights.dim() == 4:
        # (B, H, N+1, N+1) -> 取第一个样本
        attn = attn_weights[0, head_idx].cpu().numpy()
    elif attn_weights.dim() == 3:
        # (H, N+1, N+1)
        attn = attn_weights[head_idx].cpu().numpy()
    else:
        attn = attn_weights.cpu().numpy()

    # 去掉 CLS token 的行和列，只保留 patch 之间的注意力
    # attn[0, 1:] 表示 CLS token 对所有 patches 的注意力
    return attn[0, 1:]


def create_attention_heatmap(
    attn_weights: torch.Tensor,
    img_size: int = 224,
    patch_size: int = 16,
    head_idx: int = 0,
) -> np.ndarray:
    """
    创建注意力热力图

    将注意力权重重塑为与原始图像相同的空间尺寸，用于叠加显示。

    参数：
        attn_weights: 注意力权重 (B, H, N+1, N+1) 或 (H, N+1, N+1)
        img_size: 原始图像尺寸
        patch_size: patch 大小
        head_idx: 注意力头索引

    返回：
        热力图 (grid_h, grid_w) 的 numpy 数组
    """
    # 处理带 batch 维度的情况
    if attn_weights.dim() == 4:
        attn_weights = attn_weights[0]  # 取第一个样本

    # 获取 CLS token 对 patches 的注意力
    attn = attn_weights[head_idx, 0, 1:].cpu().numpy()

    # 计算空间尺寸
    grid_size = img_size // patch_size

    # 重塑为空间维度
    attn_map = attn.reshape(grid_size, grid_size)

    # 归一化到 [0, 1]
    attn_map = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-8)

    return attn_map


def get_attention_rollout(
    all_attn_weights: List[torch.Tensor],
    head_fusion: str = 'mean',
) -> np.ndarray:
    """
    注意力 Rollout

    将所有层的注意力权重累积起来，得到一个全局的注意力图。
    这比单层注意力更能反映模型的完整注意力模式。

    方法：
        1. 对每层的多头注意力进行融合（取均值或最大值）
        2. 添加残差连接的影响：A_rollout = 0.5 * A + 0.5 * I
        3. 逐层相乘

    参数：
        all_attn_weights: 每层的注意力权重列表 [(H, N+1, N+1), ...]
        head_fusion: 多头融合方式 ('mean' 或 'max')

    返回：
        融合后的注意力图 (N+1, N+1)
    """
    # 添加单位矩阵（残差连接的影响）
    result = None

    for attn in all_attn_weights:
        if attn.dim() == 3:
            attn = attn.unsqueeze(0)  # 添加 batch 维度

        # 取第一个样本
        attn = attn[0]  # (H, N+1, N+1)

        # 多头融合
        if head_fusion == 'mean':
            attn_fused = attn.mean(dim=0)  # (N+1, N+1)
        elif head_fusion == 'max':
            attn_fused = attn.max(dim=0)[0]
        else:
            raise ValueError(f"Unknown head fusion: {head_fusion}")

        # 添加残差连接
        # A_rollout = 0.5 * A + 0.5 * I
        I = torch.eye(attn_fused.size(0), device=attn_fused.device)
        attn_fused = 0.5 * attn_fused + 0.5 * I

        # 归一化
        attn_fused = attn_fused / attn_fused.sum(dim=-1, keepdim=True)

        # 逐层累积
        if result is None:
            result = attn_fused
        else:
            result = attn_fused @ result

    return result.cpu().numpy()


def print_model_summary(model: nn.Module) -> None:
    """
    打印模型摘要

    显示模型的参数量、各层结构等信息。
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print("=" * 60)
    print("Model Summary")
    print("=" * 60)
    print(f"Total parameters:     {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Non-trainable:        {total_params - trainable_params:,}")
    print("=" * 60)
    print()
    print(model)
    print()
