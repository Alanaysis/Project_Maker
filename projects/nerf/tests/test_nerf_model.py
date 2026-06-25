"""
NeRF 模型测试
============

测试 NeRFModel 和 TinyNeRF 模块的功能。
"""

import pytest
import torch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.nerf_model import NeRFModel, TinyNeRF


class TestNeRFModel:
    """NeRF 模型测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        model = NeRFModel(
            pos_encoding_dim=63,
            dir_encoding_dim=27,
            hidden_dim=256,
            num_layers=8,
        )

        # 单点输入
        positions = torch.randn(10, 63)
        directions = torch.randn(10, 27)
        density, color = model(positions, directions)

        assert density.shape == (10, 1)
        assert color.shape == (10, 3)

    def test_batch_processing(self):
        """测试批量处理"""
        model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)

        # 不同批量大小
        for batch_size in [1, 16, 64, 256]:
            positions = torch.randn(batch_size, 63)
            directions = torch.randn(batch_size, 27)
            density, color = model(positions, directions)

            assert density.shape == (batch_size, 1)
            assert color.shape == (batch_size, 3)

    def test_density_non_negative(self):
        """测试密度非负"""
        model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)

        positions = torch.randn(100, 63)
        directions = torch.randn(100, 27)
        density, _ = model(positions, directions)

        # Softplus 确保非负
        assert (density >= 0).all()

    def test_color_range(self):
        """测试颜色范围 [0, 1]"""
        model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)

        positions = torch.randn(100, 63)
        directions = torch.randn(100, 27)
        _, color = model(positions, directions)

        # Sigmoid 确保在 [0, 1]
        assert (color >= 0).all()
        assert (color <= 1).all()

    def test_skip_connection(self):
        """测试跳跃连接"""
        model = NeRFModel(
            pos_encoding_dim=63,
            dir_encoding_dim=27,
            hidden_dim=128,
            num_layers=8,
            skip_layer=4,
        )

        positions = torch.randn(10, 63)
        directions = torch.randn(10, 27)
        density, color = model(positions, directions)

        assert density.shape == (10, 1)
        assert color.shape == (10, 3)

    def test_without_viewdirs(self):
        """测试不使用观察方向"""
        model = NeRFModel(
            pos_encoding_dim=63,
            dir_encoding_dim=27,
            use_viewdirs=False,
        )

        positions = torch.randn(10, 63)
        density, color = model(positions)

        assert density.shape == (10, 1)
        assert color.shape == (10, 3)

    def test_gradient_flow(self):
        """测试梯度流"""
        model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)

        positions = torch.randn(10, 63, requires_grad=True)
        directions = torch.randn(10, 27, requires_grad=True)

        density, color = model(positions, directions)
        loss = density.sum() + color.sum()
        loss.backward()

        assert positions.grad is not None
        assert directions.grad is not None

    def test_parameter_count(self):
        """测试参数数量"""
        model = NeRFModel(
            pos_encoding_dim=63,
            dir_encoding_dim=27,
            hidden_dim=256,
            num_layers=8,
        )

        total_params = sum(p.numel() for p in model.parameters())
        # 应该有合理的参数数量
        assert total_params > 100000
        assert total_params < 1000000

    def test_device_compatibility(self):
        """测试设备兼容性"""
        if torch.cuda.is_available():
            model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27).cuda()
            positions = torch.randn(10, 63).cuda()
            directions = torch.randn(10, 27).cuda()
            density, color = model(positions, directions)

            assert density.is_cuda
            assert color.is_cuda


class TestTinyNeRF:
    """TinyNeRF 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        model = TinyNeRF(pos_encoding_dim=63, hidden_dim=128, num_layers=4)

        positions = torch.randn(10, 63)
        density, color = model(positions)

        assert density.shape == (10, 1)
        assert color.shape == (10, 3)

    def test_simpler_than_full(self):
        """测试参数比完整模型少"""
        full_model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
        tiny_model = TinyNeRF(pos_encoding_dim=63)

        full_params = sum(p.numel() for p in full_model.parameters())
        tiny_params = sum(p.numel() for p in tiny_model.parameters())

        assert tiny_params < full_params

    def test_density_non_negative(self):
        """测试密度非负"""
        model = TinyNeRF(pos_encoding_dim=63)

        positions = torch.randn(100, 63)
        density, _ = model(positions)

        assert (density >= 0).all()

    def test_color_range(self):
        """测试颜色范围"""
        model = TinyNeRF(pos_encoding_dim=63)

        positions = torch.randn(100, 63)
        _, color = model(positions)

        assert (color >= 0).all()
        assert (color <= 1).all()

    def test_gradient_flow(self):
        """测试梯度流"""
        model = TinyNeRF(pos_encoding_dim=63)

        positions = torch.randn(10, 63, requires_grad=True)
        density, color = model(positions)
        loss = density.sum() + color.sum()
        loss.backward()

        assert positions.grad is not None

    def test_batch_independence(self):
        """测试批次独立性"""
        model = TinyNeRF(pos_encoding_dim=63)

        positions = torch.randn(5, 63)
        density, color = model(positions)

        # 单独处理应该得到相同结果
        for i in range(5):
            d, c = model(positions[i:i+1])
            assert torch.allclose(density[i:i+1], d, atol=1e-5)
            assert torch.allclose(color[i:i+1], c, atol=1e-5)

    def test_different_configs(self):
        """测试不同配置"""
        configs = [
            {"pos_encoding_dim": 39, "hidden_dim": 64, "num_layers": 3},
            {"pos_encoding_dim": 63, "hidden_dim": 128, "num_layers": 4},
            {"pos_encoding_dim": 93, "hidden_dim": 256, "num_layers": 6},
        ]

        for config in configs:
            model = TinyNeRF(**config)
            positions = torch.randn(10, config["pos_encoding_dim"])
            density, color = model(positions)

            assert density.shape == (10, 1)
            assert color.shape == (10, 3)


class TestModelIntegration:
    """模型集成测试"""

    def test_with_positional_encoding(self):
        """测试与位置编码的集成"""
        from src.positional_encoding import PositionalEncoding

        pos_enc = PositionalEncoding(input_dim=3, num_freqs=10)
        dir_enc = PositionalEncoding(input_dim=3, num_freqs=6)
        model = NeRFModel(
            pos_encoding_dim=pos_enc.output_dim,
            dir_encoding_dim=dir_enc.output_dim,
        )

        # 原始坐标
        positions = torch.randn(10, 3)
        directions = torch.randn(10, 3)

        # 编码
        pos_encoded = pos_enc(positions)
        dir_encoded = dir_enc(directions)

        # 模型预测
        density, color = model(pos_encoded, dir_encoded)

        assert density.shape == (10, 1)
        assert color.shape == (10, 3)

    def test_consistency(self):
        """测试一致性"""
        model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
        model.eval()

        positions = torch.randn(10, 63)
        directions = torch.randn(10, 27)

        # 多次前向传播应该得到相同结果
        density1, color1 = model(positions, directions)
        density2, color2 = model(positions, directions)

        assert torch.allclose(density1, density2, atol=1e-6)
        assert torch.allclose(color1, color2, atol=1e-6)

    def test_train_eval_mode(self):
        """测试训练和评估模式"""
        model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)

        positions = torch.randn(10, 63)
        directions = torch.randn(10, 27)

        # 训练模式
        model.train()
        density_train, color_train = model(positions, directions)

        # 评估模式
        model.eval()
        density_eval, color_eval = model(positions, directions)

        # 结果应该相同（没有 dropout 等）
        assert torch.allclose(density_train, density_eval, atol=1e-6)
        assert torch.allclose(color_train, color_eval, atol=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
