"""
LoRA 模块测试

⭐ 测试重点:
1. LoRA 层的前向传播正确性
2. 低秩矩阵的初始化
3. 权重合并/取消合并
4. 参数量统计
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import torch
import torch.nn as nn

from src.lora.layer import LoRALinear, inject_lora_layers, count_lora_parameters


class TestLoRALinear:
    """LoRA 线性层测试"""

    def test_init(self):
        """测试 LoRA 层初始化"""
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
            alpha=16.0,
        )

        # 检查维度
        assert layer.in_features == 64
        assert layer.out_features == 32
        assert layer.rank == 8
        assert layer.alpha == 16.0

        # 检查参数形状
        assert layer.lora_A.shape == (64, 8)
        assert layer.lora_B.shape == (8, 32)

        # 检查缩放因子
        assert layer.scaling == 16.0 / 8

    def test_forward(self):
        """测试前向传播"""
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
        )

        # 创建输入
        x = torch.randn(2, 10, 64)  # (batch, seq_len, in_features)

        # 前向传播
        output = layer(x)

        # 检查输出形状
        assert output.shape == (2, 10, 32)

    def test_zero_init(self):
        """测试 B 矩阵零初始化

        ⭐ 训练开始时 ΔW = BA 应该为 0
        """
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
        )

        # B 应该是零
        assert torch.all(layer.lora_B == 0)

        # 计算 ΔW
        delta_w = layer.lora_B @ layer.lora_A.T

        # ΔW 应该为 0
        assert torch.allclose(delta_w, torch.zeros_like(delta_w))

    def test_gradient_flow(self):
        """测试梯度流

        ⭐ 只有 LoRA 参数应该有梯度
        """
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
        )

        # 前向传播
        x = torch.randn(2, 10, 64)
        output = layer(x)

        # 反向传播
        loss = output.sum()
        loss.backward()

        # 检查梯度
        assert layer.lora_A.grad is not None  # LoRA A 有梯度
        assert layer.lora_B.grad is not None  # LoRA B 有梯度
        assert layer.linear.weight.grad is None  # 基础权重没有梯度

    def test_merge_unmerge(self):
        """测试权重合并和取消合并"""
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
            merge_weights=True,
        )

        # 保存原始权重
        original_weight = layer.linear.weight.data.clone()

        # 计算预期的合并权重
        delta_w = (layer.lora_B @ layer.lora_A.T) * layer.scaling
        expected_weight = original_weight + delta_w.T

        # 合并
        layer.merge()

        # 检查合并后的权重
        assert torch.allclose(layer.linear.weight.data, expected_weight)

        # 取消合并
        layer.unmerge()

        # 检查恢复的权重
        assert torch.allclose(layer.linear.weight.data, original_weight)

    def test_scaling(self):
        """测试缩放因子的影响"""
        # 不同的 alpha 和 rank
        layer1 = LoRALinear(64, 32, rank=4, alpha=8.0)
        layer2 = LoRALinear(64, 32, rank=8, alpha=16.0)

        # 缩放因子应该相同
        assert layer1.scaling == 2.0  # 8/4
        assert layer2.scaling == 2.0  # 16/8

    def test_dropout(self):
        """测试 Dropout"""
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
            dropout=0.5,
        )

        # 训练模式
        layer.train()
        x = torch.randn(2, 10, 64)

        # 多次前向传播，结果应该不同（由于 Dropout）
        output1 = layer(x)
        output2 = layer(x)

        # 注意：由于概率性，这个测试可能偶尔失败
        # 但在大多数情况下应该不同
        assert not torch.allclose(output1, output2)

        # 评估模式
        layer.eval()
        output3 = layer(x)
        output4 = layer(x)

        # 评估模式下结果应该相同
        assert torch.allclose(output3, output4)


class TestInjectLoRALayers:
    """LoRA 注入测试"""

    def test_inject_to_linear(self):
        """测试将 LoRA 注入到线性层"""
        # 创建简单模型
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear1 = nn.Linear(64, 32)
                self.linear2 = nn.Linear(32, 16)

            def forward(self, x):
                x = self.linear1(x)
                x = self.linear2(x)
                return x

        model = SimpleModel()

        # 注入 LoRA 到 linear1
        model = inject_lora_layers(
            model,
            target_modules=["linear1"],
            rank=8,
        )

        # 检查 linear1 是否被替换
        assert isinstance(model.linear1, LoRALinear)

        # 检查 linear2 是否保持不变
        assert isinstance(model.linear2, nn.Linear)

    def test_inject_preserves_weights(self):
        """测试注入 LoRA 保持原始权重"""
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(64, 32)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()

        # 保存原始权重
        original_weight = model.linear.weight.data.clone()

        # 注入 LoRA
        model = inject_lora_layers(
            model,
            target_modules=["linear"],
            rank=8,
        )

        # 检查基础权重是否保持
        assert torch.allclose(
            model.linear.linear.weight.data,
            original_weight,
        )


class TestCountParameters:
    """参数量统计测试"""

    def test_count_lora_parameters(self):
        """测试 LoRA 参数量统计"""
        # 创建 LoRA 层
        layer = LoRALinear(
            in_features=64,
            out_features=32,
            rank=8,
        )

        # 创建简单模型
        model = nn.Sequential(layer)

        # 统计参数量
        lora_params, total_params = count_lora_parameters(model)

        # 检查
        expected_lora = 64 * 8 + 8 * 32  # lora_A + lora_B
        expected_total = 64 * 32 + 32 + expected_lora  # linear + bias + lora

        assert lora_params == expected_lora
        assert total_params == expected_total


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
