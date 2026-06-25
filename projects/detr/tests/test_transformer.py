"""
Transformer测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.transformer import (
    Transformer, build_transformer,
    TransformerEncoder, TransformerDecoder,
    TransformerEncoderLayer, TransformerDecoderLayer
)


class TestTransformer:
    """Transformer测试类"""

    def test_transformer_forward(self):
        """测试Transformer前向传播"""
        model = Transformer(d_model=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2)

        batch_size = 2
        src = torch.randn(batch_size, 64, 10, 10)
        mask = torch.zeros(batch_size, 10, 10, dtype=torch.bool)
        query_embed = torch.randn(100, 64)
        pos_embed = torch.randn(batch_size, 64, 10, 10)

        hs, memory = model(src, mask, query_embed, pos_embed)

        # 检查输出形状
        assert hs.shape == (batch_size, 100, 64)  # (batch, num_queries, d_model)
        assert memory.shape == (batch_size, 64, 10, 10)  # (batch, d_model, h, w)

    def test_encoder_layer(self):
        """测试编码器层"""
        layer = TransformerEncoderLayer(d_model=64, nhead=4, dim_feedforward=128)
        src = torch.randn(10, 2, 64)  # (seq_len, batch, d_model)
        out = layer(src)
        assert out.shape == src.shape

    def test_decoder_layer(self):
        """测试解码器层"""
        layer = TransformerDecoderLayer(d_model=64, nhead=4, dim_feedforward=128)
        tgt = torch.randn(100, 2, 64)  # (num_queries, batch, d_model)
        memory = torch.randn(10, 2, 64)  # (seq_len, batch, d_model)
        out = layer(tgt, memory)
        assert out.shape == tgt.shape

    def test_build_transformer(self):
        """测试构建Transformer"""
        model = build_transformer(
            hidden_dim=128,
            nhead=4,
            num_encoder_layers=3,
            num_decoder_layers=3,
            dim_feedforward=256
        )
        assert model.d_model == 128
        assert model.nhead == 4

    def test_transformer_with_different_sizes(self):
        """测试不同尺寸的输入"""
        model = Transformer(d_model=64, nhead=4, num_encoder_layers=1, num_decoder_layers=1)

        for h, w in [(5, 5), (10, 10), (8, 12)]:
            src = torch.randn(1, 64, h, w)
            mask = torch.zeros(1, h, w, dtype=torch.bool)
            query_embed = torch.randn(50, 64)
            pos_embed = torch.randn(1, 64, h, w)

            hs, memory = model(src, mask, query_embed, pos_embed)
            assert hs.shape == (1, 50, 64)
            assert memory.shape == (1, 64, h, w)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
