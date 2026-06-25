"""
Image Captioning Model - 图像描述模型

将 CNN 编码器和 LSTM 解码器整合为完整的图像描述模型。

架构概览：
    图像 -> CNN编码器 -> 特征序列 -> LSTM解码器(带注意力) -> 词序列

前向传播流程：
    1. CNN 编码器提取图像特征 (batch, num_pixels, encoder_dim)
    2. LSTM 解码器在注意力机制辅助下逐词生成描述
    3. 输出每个时间步的词概率分布

推理流程：
    1. CNN 编码器提取图像特征
    2. LSTM 解码器使用贪心搜索或束搜索生成描述
"""

import torch
import torch.nn as nn

from .encoder import CNNEncoder
from .decoder import LSTMDecoder


class ImageCaptioningModel(nn.Module):
    """图像描述生成模型。

    整合 CNN 编码器和 LSTM 解码器，实现端到端的图像描述生成。
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 256,
        hidden_dim: int = 512,
        attention_dim: int = 256,
        encoder_backbone: str = "resnet50",
        encoder_pretrained: bool = True,
        num_decoder_layers: int = 1,
        dropout: float = 0.5,
        attention_type: str = "bahdanau",
    ):
        """初始化图像描述模型。

        Args:
            vocab_size: 词汇表大小
            embed_dim: 嵌入维度（编码器和解码器共享）
            hidden_dim: LSTM 隐藏状态维度
            attention_dim: 注意力计算维度
            encoder_backbone: 编码器骨干网络
            encoder_pretrained: 是否使用预训练编码器
            num_decoder_layers: 解码器 LSTM 层数
            dropout: Dropout 比率
            attention_type: 注意力类型
        """
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim

        # CNN 编码器
        self.encoder = CNNEncoder(
            embed_dim=embed_dim,
            backbone=encoder_backbone,
            pretrained=encoder_pretrained,
        )

        # LSTM 解码器
        self.decoder = LSTMDecoder(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            encoder_dim=embed_dim,  # 编码器输出维度等于 embed_dim
            attention_dim=attention_dim,
            num_layers=num_decoder_layers,
            dropout=dropout,
            attention_type=attention_type,
        )

    def forward(
        self,
        images: torch.Tensor,
        captions: torch.Tensor,
        caption_lengths: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """训练阶段前向传播。

        Args:
            images: 输入图像 (batch_size, 3, H, W)
            captions: 目标描述序列 (batch_size, max_length)
            caption_lengths: 描述长度 (batch_size,)

        Returns:
            predictions: 词预测 (batch_size, max_length-1, vocab_size)
            attention_weights: 注意力权重 (batch_size, max_length-1, num_pixels)
        """
        # 编码器提取特征
        encoder_out = self.encoder(images)

        # 解码器生成预测
        predictions, attention_weights = self.decoder(
            encoder_out, captions, caption_lengths
        )

        return predictions, attention_weights

    def generate(
        self,
        images: torch.Tensor,
        vocabulary,
        max_length: int = 50,
        temperature: float = 1.0,
        beam_size: int = 1,
    ) -> list[str]:
        """推理阶段生成图像描述。

        Args:
            images: 输入图像 (batch_size, 3, H, W)
            vocabulary: 词汇表实例
            max_length: 最大生成长度
            temperature: 采样温度
            beam_size: 束搜索宽度

        Returns:
            生成的描述文本列表
        """
        self.eval()
        with torch.no_grad():
            # 编码器提取特征
            encoder_out = self.encoder(images)

            # 解码器生成词索引
            generated_indices = self.decoder.generate(
                encoder_out,
                max_length=max_length,
                start_idx=vocabulary.start_idx,
                end_idx=vocabulary.end_idx,
                temperature=temperature,
                beam_size=beam_size,
            )

            # 解码为文本
            captions = []
            for indices in generated_indices:
                caption = vocabulary.decode(indices, skip_special=True)
                captions.append(caption)

        return captions

    def count_parameters(self) -> dict[str, int]:
        """统计模型参数量。

        Returns:
            各模块参数量字典
        """
        encoder_params = sum(p.numel() for p in self.encoder.parameters())
        decoder_params = sum(p.numel() for p in self.decoder.parameters())
        total_params = sum(p.numel() for p in self.parameters())

        return {
            "encoder": encoder_params,
            "decoder": decoder_params,
            "total": total_params,
        }
