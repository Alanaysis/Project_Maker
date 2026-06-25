"""
Vision Transformer 完整模型测试

测试 ViT 模型的正确性：
1. 输出形状
2. 模型配置
3. 注意力可视化
4. 端到端训练
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.vit import VisionTransformer, MLPHead


class TestMLPHead:
    """MLPHead 测试类"""

    def test_simple_linear_head(self):
        """测试简单线性头"""
        head = MLPHead(in_features=768, out_features=10)
        x = torch.randn(2, 768)
        out = head(x)

        assert out.shape == (2, 10)

    def test_mlp_head_with_hidden(self):
        """测试带隐藏层的 MLP 头"""
        head = MLPHead(in_features=768, hidden_features=512, out_features=10)
        x = torch.randn(2, 768)
        out = head(x)

        assert out.shape == (2, 10)


class TestVisionTransformer:
    """VisionTransformer 测试类"""

    def test_output_shape_default(self):
        """测试默认配置的输出形状"""
        model = VisionTransformer(
            img_size=224, patch_size=16, num_classes=1000,
            embed_dim=768, depth=12, num_heads=12,
        )
        x = torch.randn(2, 3, 224, 224)
        logits, _ = model(x)

        assert logits.shape == (2, 1000)

    def test_output_shape_small(self):
        """测试小模型的输出形状"""
        model = VisionTransformer(
            img_size=28, patch_size=7, in_channels=1, num_classes=10,
            embed_dim=64, depth=2, num_heads=4,
        )
        x = torch.randn(4, 1, 28, 28)
        logits, _ = model(x)

        assert logits.shape == (4, 10)

    def test_vit_tiny_factory(self):
        """测试 ViT-Tiny 工厂方法"""
        model = VisionTransformer.vit_tiny(num_classes=10)
        x = torch.randn(1, 3, 224, 224)
        logits, _ = model(x)

        assert logits.shape == (1, 10)
        assert model.embed_dim == 192

    def test_vit_small_factory(self):
        """测试 ViT-Small 工厂方法"""
        model = VisionTransformer.vit_small(num_classes=10)
        x = torch.randn(1, 3, 224, 224)
        logits, _ = model(x)

        assert logits.shape == (1, 10)
        assert model.embed_dim == 384

    def test_attention_weights_return(self):
        """测试返回注意力权重"""
        # 8x8 图像，4x4 patch -> 2x2 = 4 patches + 1 CLS = 5 tokens
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
        )
        x = torch.randn(1, 3, 8, 8)
        logits, attn_weights = model(x, return_attention=True)

        assert logits.shape == (1, 5)
        assert len(attn_weights) == 2  # 2 层
        assert attn_weights[0].shape == (1, 2, 5, 5)  # (B, H, N+1, N+1)

    def test_get_attention_maps(self):
        """测试 get_attention_maps 方法"""
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
        )
        x = torch.randn(1, 3, 8, 8)
        attn_maps = model.get_attention_maps(x)

        assert len(attn_maps) == 2

    def test_gradient_flow(self):
        """测试梯度传播"""
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
        )
        x = torch.randn(1, 3, 8, 8)
        logits, _ = model(x)
        loss = logits.sum()
        loss.backward()

        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient"

    def test_parameter_count(self):
        """测试参数量是否合理"""
        model = VisionTransformer(
            img_size=224, patch_size=16, num_classes=1000,
            embed_dim=768, depth=12, num_heads=12,
        )
        total_params = sum(p.numel() for p in model.parameters())

        # ViT-Base 应该有约 86M 参数
        assert total_params > 50_000_000
        assert total_params < 150_000_000

    def test_tiny_model_parameter_count(self):
        """测试 Tiny 模型的参数量"""
        model = VisionTransformer.vit_tiny(num_classes=10)
        total_params = sum(p.numel() for p in model.parameters())

        # ViT-Tiny 应该参数量较少
        assert total_params < 10_000_000

    def test_batch_independence(self):
        """测试批次中的样本独立"""
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
        )
        x = torch.randn(2, 3, 8, 8)
        logits, _ = model(x)

        assert not torch.allclose(logits[0], logits[1])

    def test_training_mode(self):
        """测试训练模式切换"""
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
        )

        model.train()
        assert model.training

        model.eval()
        assert not model.training

    def test_end_to_end_backward(self):
        """测试端到端反向传播"""
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
        )
        x = torch.randn(2, 3, 8, 8)
        target = torch.tensor([0, 3])

        logits, _ = model(x)
        loss = torch.nn.functional.cross_entropy(logits, target)
        loss.backward()

        # 验证损失值合理
        assert loss.item() > 0

    def test_representation_size(self):
        """测试带隐藏层的分类头"""
        model = VisionTransformer(
            img_size=8, patch_size=4, num_classes=5,
            embed_dim=32, depth=2, num_heads=2,
            representation_size=256,
        )
        x = torch.randn(1, 3, 8, 8)
        logits, _ = model(x)

        assert logits.shape == (1, 5)

    def test_different_num_classes(self):
        """测试不同的类别数"""
        for num_classes in [2, 10, 100, 1000]:
            model = VisionTransformer(
                img_size=8, patch_size=4, num_classes=num_classes,
                embed_dim=32, depth=1, num_heads=2,
            )
            x = torch.randn(1, 3, 8, 8)
            logits, _ = model(x)

            assert logits.shape == (1, num_classes)
