"""高级风格迁移示例

演示高级风格迁移技术，包括：
1. 多风格迁移
2. 不同层的权重调整
3. 不同优化器的比较
"""

import torch
from pathlib import Path
import matplotlib.pyplot as plt

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import StyleTransfer


def compare_optimizers():
    """比较不同优化器的效果"""
    print("=" * 60)
    print("比较不同优化器")
    print("=" * 60)

    # 创建图像
    content_image = torch.randn(1, 3, 128, 128)
    style_image = torch.randn(1, 3, 128, 128)

    results = {}

    # L-BFGS 优化器
    print("\n1. 使用 L-BFGS 优化器...")
    transfer_lbfgs = StyleTransfer(
        content_layers=["conv4_2"],
        style_layers=["conv1_1", "conv2_1", "conv3_1"],
        device="cpu",
    )

    output_lbfgs = transfer_lbfgs.transfer(
        content_image=content_image,
        style_image=style_image,
        num_steps=100,
        optimizer_type="lbfgs",
        learning_rate=1.0,
    )
    results["L-BFGS"] = output_lbfgs

    # Adam 优化器
    print("\n2. 使用 Adam 优化器...")
    transfer_adam = StyleTransfer(
        content_layers=["conv4_2"],
        style_layers=["conv1_1", "conv2_1", "conv3_1"],
        device="cpu",
    )

    output_adam = transfer_adam.transfer(
        content_image=content_image,
        style_image=style_image,
        num_steps=100,
        optimizer_type="adam",
        learning_rate=0.01,
    )
    results["Adam"] = output_adam

    print("\n比较完成!")
    return results


def compare_content_layers():
    """比较不同内容层的效果"""
    print("=" * 60)
    print("比较不同内容层")
    print("=" * 60)

    content_image = torch.randn(1, 3, 128, 128)
    style_image = torch.randn(1, 3, 128, 128)

    content_layers_options = [
        ["conv2_2"],
        ["conv3_2"],
        ["conv4_2"],
        ["conv5_2"],
    ]

    results = {}

    for layers in content_layers_options:
        layer_name = layers[0]
        print(f"\n使用内容层: {layer_name}")

        transfer = StyleTransfer(
            content_layers=layers,
            style_layers=["conv1_1", "conv2_1", "conv3_1"],
            device="cpu",
        )

        output = transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=100,
        )

        results[layer_name] = output

    print("\n比较完成!")
    return results


def compare_style_weights():
    """比较不同风格权重的效果"""
    print("=" * 60)
    print("比较不同风格权重")
    print("=" * 60)

    content_image = torch.randn(1, 3, 128, 128)
    style_image = torch.randn(1, 3, 128, 128)

    style_weights = [1e4, 1e5, 1e6, 1e7]
    results = {}

    for weight in style_weights:
        print(f"\n使用风格权重: {weight:.0e}")

        transfer = StyleTransfer(
            content_layers=["conv4_2"],
            style_layers=["conv1_1", "conv2_1", "conv3_1"],
            style_weight=weight,
            device="cpu",
        )

        output = transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=100,
        )

        results[f"weight={weight:.0e}"] = output

    print("\n比较完成!")
    return results


def multi_style_transfer():
    """多风格迁移示例

    将多个风格图像的特征组合在一起。
    """
    print("=" * 60)
    print("多风格迁移")
    print("=" * 60)

    content_image = torch.randn(1, 3, 128, 128)
    style_images = [
        torch.randn(1, 3, 128, 128),
        torch.randn(1, 3, 128, 128),
    ]

    # 方法：对每个风格图像分别计算 Gram 矩阵，然后平均
    print("\n方法：分别计算每个风格的损失，然后加权组合")

    transfer = StyleTransfer(
        content_layers=["conv4_2"],
        style_layers=["conv1_1", "conv2_1", "conv3_1"],
        style_weight=1e6,
        device="cpu",
    )

    # 设置内容目标
    transfer._set_targets(content_image, style_images[0])

    # 对每个风格图像设置目标
    # 这里简化处理，实际应用中可以更复杂地组合多个风格
    output = transfer.transfer(
        content_image=content_image,
        style_image=style_images[0],
        num_steps=200,
    )

    print("\n多风格迁移完成!")
    return output


def main():
    """主函数"""
    print("神经风格迁移 - 高级示例")
    print("=" * 60)

    # 比较不同优化器
    optimizer_results = compare_optimizers()

    # 比较不同内容层
    layer_results = compare_content_layers()

    # 比较不同风格权重
    weight_results = compare_style_weights()

    # 多风格迁移
    multi_result = multi_style_transfer()

    print("\n" + "=" * 60)
    print("所有高级示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
