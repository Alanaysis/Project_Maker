"""
测试 LSTM 解码器
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.decoder import LSTMDecoder


class TestLSTMDecoder:
    """LSTM 解码器测试套件。"""

    def _make_decoder(self, attention_type="bahdanau"):
        return LSTMDecoder(
            vocab_size=100,
            embed_dim=64,
            hidden_dim=128,
            encoder_dim=64,
            attention_dim=64,
            dropout=0.0,
            attention_type=attention_type,
        )

    def test_training_forward_shape(self):
        """测试训练阶段前向传播输出形状。"""
        decoder = self._make_decoder()
        batch_size = 4
        num_pixels = 49
        encoder_dim = 64
        caption_length = 10

        encoder_out = torch.randn(batch_size, num_pixels, encoder_dim)
        captions = torch.randint(0, 100, (batch_size, caption_length))
        captions[:, 0] = 1  # <start>
        lengths = torch.tensor([caption_length] * batch_size)

        predictions, attn_weights = decoder(encoder_out, captions, lengths)
        assert predictions.shape[0] == batch_size
        assert predictions.shape[2] == 100
        assert attn_weights.shape[0] == batch_size
        assert attn_weights.shape[2] == num_pixels

    def test_generate_greedy(self):
        """测试贪心生成。"""
        decoder = self._make_decoder()
        encoder_out = torch.randn(2, 49, 64)

        generated = decoder.generate(
            encoder_out,
            max_length=10,
            start_idx=1,
            end_idx=2,
            beam_size=1,
        )
        assert len(generated) == 2
        for seq in generated:
            assert len(seq) <= 10
            # 生成的序列不应包含 start 或 end 标记
            assert 1 not in seq
            assert 2 not in seq

    def test_generate_beam_search(self):
        """测试束搜索生成。"""
        decoder = self._make_decoder()
        encoder_out = torch.randn(1, 49, 64)

        generated = decoder.generate(
            encoder_out,
            max_length=10,
            start_idx=1,
            end_idx=2,
            beam_size=3,
        )
        assert len(generated) == 1
        for seq in generated:
            assert isinstance(seq, list)

    def test_init_hidden_state(self):
        """测试隐藏状态初始化。"""
        decoder = self._make_decoder()
        encoder_out = torch.randn(4, 49, 64)
        h, c = decoder.init_hidden_state(encoder_out)
        assert h.shape == (4, 128)
        assert c.shape == (4, 128)

    def test_gradient_flow(self):
        """测试梯度反向传播。"""
        decoder = self._make_decoder()
        encoder_out = torch.randn(2, 49, 64)
        captions = torch.randint(0, 100, (2, 8))
        captions[:, 0] = 1
        lengths = torch.tensor([8, 6])

        predictions, _ = decoder(encoder_out, captions, lengths)
        loss = predictions.sum()
        loss.backward()

        for name, param in decoder.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"参数 {name} 没有梯度"

    def test_scaled_dot_attention(self):
        """测试使用缩放点积注意力。"""
        decoder = self._make_decoder(attention_type="scaled_dot")
        encoder_out = torch.randn(2, 49, 64)
        captions = torch.randint(0, 100, (2, 8))
        captions[:, 0] = 1
        lengths = torch.tensor([8, 8])

        predictions, attn_weights = decoder(encoder_out, captions, lengths)
        assert predictions.shape == (2, 7, 100)

    def test_generate_with_temperature(self):
        """测试温度参数对生成的影响。"""
        decoder = self._make_decoder()
        decoder.eval()
        encoder_out = torch.randn(1, 49, 64)

        with torch.no_grad():
            gen_low_temp = decoder.generate(
                encoder_out, max_length=5, start_idx=1, end_idx=2, temperature=0.1
            )
            gen_high_temp = decoder.generate(
                encoder_out, max_length=5, start_idx=1, end_idx=2, temperature=2.0
            )

        # 两者都应生成有效序列
        assert len(gen_low_temp) == 1
        assert len(gen_high_temp) == 1


def run_tests():
    """运行所有测试。"""
    test = TestLSTMDecoder()
    tests = [getattr(test, name) for name in dir(test) if name.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__} - {e}")
            failed += 1
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    print("LSTM 解码器测试")
    print("-" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
