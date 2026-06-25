"""
Vision Transformer (ViT) 实现

从零实现 Vision Transformer，理解视觉 Transformer 的核心原理：
- Patch Embedding：将图像分割为 patches 并线性嵌入
- Multi-Head Self-Attention：多头自注意力机制
- Transformer Encoder：Transformer 编码器
- ViT 模型：完整的 Vision Transformer 架构
"""

from .patch_embedding import PatchEmbedding
from .attention import MultiHeadSelfAttention
from .transformer import TransformerBlock, TransformerEncoder
from .vit import VisionTransformer

__all__ = [
    "PatchEmbedding",
    "MultiHeadSelfAttention",
    "TransformerBlock",
    "TransformerEncoder",
    "VisionTransformer",
]
