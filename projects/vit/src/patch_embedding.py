"""
Patch Embedding 模块

将图像分割为固定大小的 patches，并通过线性投影映射到嵌入空间。

核心思想：
    原始图像 (B, C, H, W) -> 分割为 N 个 patches -> 每个 patch 线性投影为 D 维向量
    其中 N = (H / patch_size) * (W / patch_size)

论文公式：
    z_0 = [x_cls; x_1^p E; x_2^p E; ...; x_N^p E] + E_pos
    其中 E 为 patch 嵌入投影矩阵，E_pos 为位置嵌入
"""

import torch
import torch.nn as nn
from typing import Tuple


class PatchEmbedding(nn.Module):
    """
    Patch Embedding 层

    将图像转换为 patch 序列的嵌入表示。

    实现方式：
    1. 使用 Conv2d 实现 patch 分割 + 线性投影（等价于手动分割后做矩阵乘法）
    2. 添加可学习的 [CLS] token
    3. 添加可学习的位置编码

    参数：
        img_size: 输入图像尺寸（假设正方形）
        patch_size: patch 大小（假设正方形）
        in_channels: 输入图像通道数
        embed_dim: 嵌入维度
    """

    def __init__(
        self,
        img_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        embed_dim: int = 768,
    ):
        super().__init__()

        self.img_size = img_size
        self.patch_size = patch_size
        self.in_channels = in_channels
        self.embed_dim = embed_dim

        # 计算 patch 数量
        # 对于 224x224 图像，16x16 patch -> 14x14 = 196 个 patches
        assert img_size % patch_size == 0, \
            f"图像尺寸 {img_size} 必须能被 patch_size {patch_size} 整除"
        self.num_patches = (img_size // patch_size) ** 2

        # ★ 核心：使用 Conv2d 实现 patch 分割 + 线性投影
        # kernel_size = patch_size, stride = patch_size -> 不重叠地提取 patches
        # out_channels = embed_dim -> 每个 patch 投影为 embed_dim 维向量
        # 这等价于：将每个 patch 展平后乘以一个 (patch_size^2 * C, embed_dim) 的权重矩阵
        self.projection = nn.Conv2d(
            in_channels=in_channels,
            out_channels=embed_dim,
            kernel_size=patch_size,
            stride=patch_size,
        )

        # ★ [CLS] token：用于分类的特殊 token
        # 在序列开头添加一个可学习的分类 token，最终用它的表示做分类
        # 形状：(1, 1, embed_dim)，会在 batch 维度上广播
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))

        # ★ 位置编码：为每个 patch 位置添加可学习的位置信息
        # +1 是因为还有 [CLS] token
        # 形状：(1, num_patches + 1, embed_dim)
        self.position_embedding = nn.Parameter(
            torch.zeros(1, self.num_patches + 1, embed_dim)
        )

        # LayerNorm 用于稳定训练
        self.norm = nn.LayerNorm(embed_dim)

        # 初始化参数
        self._init_weights()

    def _init_weights(self):
        """
        参数初始化

        - Conv2d 权重使用 Xavier 均匀分布
        - CLS token 和位置编码使用正态分布
        """
        # 初始化投影层
        nn.init.xavier_uniform_(self.projection.weight.view(
            self.embed_dim, -1
        ))
        nn.init.zeros_(self.projection.bias)

        # 初始化 CLS token 和位置编码
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.position_embedding, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        流程：
            1. 输入图像通过 Conv2d 进行 patch 分割 + 线性投影
            2. 将空间维度展平为序列维度
            3. 转置为 (B, N, D) 格式
            4. 拼接 [CLS] token
            5. 添加位置编码

        参数：
            x: 输入图像张量，形状 (B, C, H, W)

        返回：
            嵌入序列，形状 (B, N+1, D)
            其中 N = num_patches, D = embed_dim
        """
        B = x.shape[0]

        # Step 1: Patch 分割 + 线性投影
        # (B, C, H, W) -> (B, D, H/P, W/P)
        x = self.projection(x)

        # Step 2: 展平空间维度
        # (B, D, H/P, W/P) -> (B, D, N)  其中 N = (H/P) * (W/P)
        x = x.flatten(2)

        # Step 3: 转置为 (B, N, D) 格式
        # (B, D, N) -> (B, N, D)
        x = x.transpose(1, 2)

        # Step 4: 拼接 [CLS] token
        # CLS token: (1, 1, D) -> 扩展为 (B, 1, D)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        # 拼接: (B, N, D) + (B, 1, D) -> (B, N+1, D)
        x = torch.cat([cls_tokens, x], dim=1)

        # Step 5: 添加位置编码
        # (B, N+1, D) + (1, N+1, D) -> (B, N+1, D)
        x = x + self.position_embedding

        # LayerNorm
        x = self.norm(x)

        return x

    def extra_repr(self) -> str:
        return (
            f'img_size={self.img_size}, patch_size={self.patch_size}, '
            f'in_channels={self.in_channels}, embed_dim={self.embed_dim}, '
            f'num_patches={self.num_patches}'
        )
