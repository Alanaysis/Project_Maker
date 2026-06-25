"""
测试图像描述模型
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.model import ImageCaptioningModel
from src.vocabulary import Vocabulary


class TestImageCaptioningModel:
    """图像描述模型测试套件。"""

    def _make_model(self, vocab_size=50, attention_type="bahdanau"):
        return ImageCaptioningModel(
            vocab_size=vocab_size,
            embed_dim=64,
            hidden_dim=128,
            attention_dim=64,
            encoder_backbone="resnet18",
            encoder_pretrained=False,
            dropout=0.0,
            attention_type=attention_type,
        )

    def test_forward_shape(self):
        """测试前向传播输出形状。"""
        model = self._make_model()
        images = torch.randn(2, 3, 224, 224)
        captions = torch.randint(0, 50, (2, 10))
        captions[:, 0] = 1
        lengths = torch.tensor([10, 8])

        predictions, attn_weights = model(images, captions, lengths)
        assert predictions.shape[0] == 2
        assert predictions.shape[2] == 50
        assert attn_weights.shape[0] == 2

    def test_generate(self):
        """测试描述生成。"""
        model = self._make_model()
        model.eval()

        # 构建简单词汇表
        vocab = Vocabulary()
        for i in range(50):
            if i < 4:
                continue
            vocab.word2idx[f"word_{i}"] = i
            vocab.idx2word[i] = f"word_{i}"

        images = torch.randn(2, 3, 224, 224)
        captions = model.generate(images, vocab, max_length=10)
        assert len(captions) == 2
        for caption in captions:
            assert isinstance(caption, str)

    def test_count_parameters(self):
        """测试参数量统计。"""
        model = self._make_model()
        params = model.count_parameters()
        assert "encoder" in params
        assert "decoder" in params
        assert "total" in params
        assert params["total"] > 0
        assert params["total"] == params["encoder"] + params["decoder"]

    def test_gradient_flow(self):
        """测试梯度反向传播。"""
        model = self._make_model()
        images = torch.randn(2, 3, 224, 224)
        captions = torch.randint(0, 50, (2, 8))
        captions[:, 0] = 1
        lengths = torch.tensor([8, 6])

        predictions, _ = model(images, captions, lengths)
        loss = predictions.sum()
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"参数 {name} 没有梯度"

    def test_scaled_dot_attention(self):
        """测试使用缩放点积注意力。"""
        model = self._make_model(attention_type="scaled_dot")
        images = torch.randn(2, 3, 224, 224)
        captions = torch.randint(0, 50, (2, 8))
        captions[:, 0] = 1
        lengths = torch.tensor([8, 8])

        predictions, attn_weights = model(images, captions, lengths)
        assert predictions.shape[0] == 2

    def test_single_image(self):
        """测试单张图像输入。"""
        model = self._make_model()
        model.eval()
        image = torch.randn(1, 3, 224, 224)
        caption = torch.randint(0, 50, (1, 6))
        caption[0, 0] = 1
        length = torch.tensor([6])

        predictions, attn_weights = model(image, caption, length)
        assert predictions.shape[0] == 1

    def test_generate_with_beam_search(self):
        """测试束搜索生成。"""
        model = self._make_model()
        model.eval()

        vocab = Vocabulary()
        for i in range(50):
            if i < 4:
                continue
            vocab.word2idx[f"word_{i}"] = i
            vocab.idx2word[i] = f"word_{i}"

        image = torch.randn(1, 3, 224, 224)
        captions = model.generate(image, vocab, max_length=10, beam_size=3)
        assert len(captions) == 1


def run_tests():
    """运行所有测试。"""
    test = TestImageCaptioningModel()
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
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    print("图像描述模型测试")
    print("-" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
