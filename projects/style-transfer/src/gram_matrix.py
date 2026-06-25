"""Gram 矩阵计算模块

Gram 矩阵是风格迁移的核心概念，用于捕捉图像的风格信息。

数学定义：
    给定特征图 F，其 Gram 矩阵 G 定义为：
    G[i,j] = Σ_k F[i,k] * F[j,k]

    其中：
    - F 是 shape 为 (C, H*W) 的特征矩阵
    - G 是 shape 为 (C, C) 的 Gram 矩阵
    - C 是通道数
    - H, W 是特征图的高度和宽度

直觉理解：
    - Gram 矩阵计算了不同特征通道之间的相关性
    - 对角线元素表示每个通道的"能量"（方差）
    - 非对角线元素表示通道间的"协方差"
    - 这种相关性编码了图像的纹理和风格信息
"""

import torch
import torch.nn as nn


def gram_matrix(features: torch.Tensor, normalize: bool = True) -> torch.Tensor:
    """计算特征图的 Gram 矩阵

    Args:
        features: 特征图，shape 为 (batch_size, channels, height, width)
        normalize: 是否对 Gram 矩阵进行归一化

    Returns:
        Gram 矩阵，shape 为 (batch_size, channels, channels)

    示例：
        >>> import torch
        >>> from src import gram_matrix
        >>> features = torch.randn(1, 64, 32, 32)
        >>> gram = gram_matrix(features)
        >>> print(gram.shape)
        torch.Size([1, 64, 64])
    """
    batch_size, channels, height, width = features.shape

    # 重塑特征图：(batch_size, channels, height*width)
    # 这样每个通道的特征被展平为一维向量
    features_reshaped = features.view(batch_size, channels, -1)

    # 计算 Gram 矩阵：G = F * F^T
    # 对于每个 batch，计算 (C, H*W) @ (H*W, C) = (C, C)
    gram = torch.bmm(features_reshaped, features_reshaped.transpose(1, 2))

    if normalize:
        # 归一化：除以特征图的元素总数
        # 这样不同大小的特征图可以进行公平比较
        num_elements = height * width
        gram = gram / num_elements

    return gram


class GramMatrix(nn.Module):
    """Gram 矩阵计算层

    将 Gram 矩阵计算封装为 PyTorch 模块，方便集成到计算图中。

    示例：
        >>> import torch
        >>> from src import GramMatrix
        >>> gram_layer = GramMatrix(normalize=True)
        >>> features = torch.randn(1, 64, 32, 32)
        >>> gram = gram_layer(features)
        >>> print(gram.shape)
        torch.Size([1, 64, 64])
    """

    def __init__(self, normalize: bool = True):
        """初始化 Gram 矩阵层

        Args:
            normalize: 是否对 Gram 矩阵进行归一化
        """
        super().__init__()
        self.normalize = normalize

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """前向传播

        Args:
            features: 特征图

        Returns:
            Gram 矩阵
        """
        return gram_matrix(features, self.normalize)


def gram_loss(features1: torch.Tensor, features2: torch.Tensor) -> torch.Tensor:
    """计算两个特征图之间的 Gram 矩阵损失

    这个损失衡量了两张图像在风格上的差异。
    最小化这个损失意味着让两张图像具有相似的纹理和风格。

    Args:
        features1: 第一个特征图
        features2: 第二个特征图

    Returns:
        均方误差损失（MSE Loss）
    """
    gram1 = gram_matrix(features1, normalize=True)
    gram2 = gram_matrix(features2, normalize=True)
    return torch.mean((gram1 - gram2) ** 2)
