"""
测试 CNN 编码器
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.encoder import CNNEncoder


class TestCNNEncoder:
    """CNNEncoder 测试套件。"""

    def test_output_shape_resnet18(self):
        """测试 ResNet-18 编码器输出形状。"""
        encoder = CNNEncoder(embed_dim=256, backbone="resnet18", pretrained=False)
        images = torch.randn(2, 3, 224, 224)
        output = encoder(images)
        assert output.shape[0] == 2
        assert output.shape[2] == 256

    def test_output_shape_resnet50(self):
        """测试 ResNet-50 编码器输出形状。"""
        encoder = CNNEncoder(embed_dim=512, backbone="resnet50", pretrained=False)
        images = torch.randn(4, 3, 224, 224)
        output = encoder(images)
        assert output.shape[0] == 4
        assert output.shape[2] == 512

    def test_output_shape_resnet34(self):
        """测试 ResNet-34 编码器输出形状。"""
        encoder = CNNEncoder(embed_dim=128, backbone="resnet34", pretrained=False)
        images = torch.randn(1, 3, 224, 224)
        output = encoder(images)
        assert output.shape[0] == 1
        assert output.shape[2] == 128

    def test_num_pixels(self):
        """测试特征图像素数量。"""
        encoder = CNNEncoder(embed_dim=256, backbone="resnet18", pretrained=False)
        assert encoder.num_pixels == 49

    def test_unsupported_backbone(self):
        """测试不支持的骨干网络抛出异常。"""
        try:
            CNNEncoder(embed_dim=256, backbone="unsupported", pretrained=False)
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass

    def test_gradient_flow(self):
        """测试梯度可以正常反向传播。"""
        encoder = CNNEncoder(embed_dim=256, backbone="resnet18", pretrained=False)
        images = torch.randn(2, 3, 224, 224)
        output = encoder(images)
        loss = output.sum()
        loss.backward()
        # 检查所有参数都有梯度
        for name, param in encoder.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"参数 {name} 没有梯度"

    def test_single_image(self):
        """测试单张图像输入。"""
        encoder = CNNEncoder(embed_dim=256, backbone="resnet18", pretrained=False)
        image = torch.randn(1, 3, 224, 224)
        output = encoder(image)
        assert output.shape[0] == 1
        assert output.dim() == 3

    def test_batch_consistency(self):
        """测试批量处理的一致性（同一图像在不同 batch 中输出应相同）。"""
        encoder = CNNEncoder(embed_dim=256, backbone="resnet18", pretrained=False)
        encoder.eval()
        image = torch.randn(1, 3, 224, 224)

        # 单独处理
        with torch.no_grad():
            out1 = encoder(image)

        # 与另一个图像一起处理
        other_image = torch.randn(1, 3, 224, 224)
        batch = torch.cat([image, other_image], dim=0)
        with torch.no_grad():
            out2_batch = encoder(batch)
            out2 = out2_batch[:1]

        assert torch.allclose(out1, out2, atol=1e-5), "批量处理结果不一致"


def run_tests():
    """运行所有测试。"""
    test = TestCNNEncoder()
    tests = [
        test.test_output_shape_resnet18,
        test.test_output_shape_resnet50,
        test.test_output_shape_resnet34,
        test.test_num_pixels,
        test.test_unsupported_backbone,
        test.test_gradient_flow,
        test.test_single_image,
        test.test_batch_consistency,
    ]
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
    print("CNN 编码器测试")
    print("-" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
