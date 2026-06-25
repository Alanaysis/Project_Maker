"""
测试注意力机制
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.attention import Attention, ScaledDotProductAttention


class TestAttention:
    """Bahdanau 注意力测试套件。"""

    def test_output_shape(self):
        """测试注意力输出形状。"""
        attention = Attention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(4, 49, 256)
        decoder_hidden = torch.randn(4, 512)
        context, weights = attention(encoder_out, decoder_hidden)
        assert context.shape == (4, 256)
        assert weights.shape == (4, 49)

    def test_attention_weights_sum_to_one(self):
        """测试注意力权重之和为1。"""
        attention = Attention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(4, 49, 256)
        decoder_hidden = torch.randn(4, 512)
        _, weights = attention(encoder_out, decoder_hidden)
        sums = weights.sum(dim=-1)
        assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5)

    def test_attention_weights_non_negative(self):
        """测试注意力权重非负。"""
        attention = Attention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(4, 49, 256)
        decoder_hidden = torch.randn(4, 512)
        _, weights = attention(encoder_out, decoder_hidden)
        assert (weights >= 0).all()

    def test_gradient_flow(self):
        """测试梯度反向传播。"""
        attention = Attention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(2, 49, 256, requires_grad=True)
        decoder_hidden = torch.randn(2, 512, requires_grad=True)
        context, _ = attention(encoder_out, decoder_hidden)
        loss = context.sum()
        loss.backward()
        assert encoder_out.grad is not None
        assert decoder_hidden.grad is not None

    def test_single_pixel(self):
        """测试单像素输入。"""
        attention = Attention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(2, 1, 256)
        decoder_hidden = torch.randn(2, 512)
        context, weights = attention(encoder_out, decoder_hidden)
        assert context.shape == (2, 256)
        assert weights.shape == (2, 1)
        assert torch.allclose(weights, torch.ones_like(weights), atol=1e-5)


class TestScaledDotProductAttention:
    """缩放点积注意力测试套件。"""

    def test_output_shape(self):
        """测试输出形状。"""
        attention = ScaledDotProductAttention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(4, 49, 256)
        decoder_hidden = torch.randn(4, 512)
        context, weights = attention(encoder_out, decoder_hidden)
        assert context.shape == (4, 256)
        assert weights.shape == (4, 49)

    def test_weights_sum_to_one(self):
        """测试权重之和为1。"""
        attention = ScaledDotProductAttention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(4, 49, 256)
        decoder_hidden = torch.randn(4, 512)
        _, weights = attention(encoder_out, decoder_hidden)
        sums = weights.sum(dim=-1)
        assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5)

    def test_gradient_flow(self):
        """测试梯度反向传播。"""
        attention = ScaledDotProductAttention(encoder_dim=256, decoder_dim=512, attention_dim=256)
        encoder_out = torch.randn(2, 49, 256, requires_grad=True)
        decoder_hidden = torch.randn(2, 512, requires_grad=True)
        context, _ = attention(encoder_out, decoder_hidden)
        loss = context.sum()
        loss.backward()
        assert encoder_out.grad is not None
        assert decoder_hidden.grad is not None


def run_tests():
    """运行所有测试。"""
    all_tests = []
    for cls in [TestAttention, TestScaledDotProductAttention]:
        test_instance = cls()
        for name in dir(test_instance):
            if name.startswith("test_"):
                all_tests.append((cls.__name__, getattr(test_instance, name)))

    passed = 0
    failed = 0
    for class_name, t in all_tests:
        try:
            t()
            print(f"  PASS: {class_name}.{t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {class_name}.{t.__name__} - {e}")
            failed += 1
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    print("注意力机制测试")
    print("-" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
