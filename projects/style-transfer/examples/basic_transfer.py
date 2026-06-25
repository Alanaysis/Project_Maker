"""基本风格迁移示例

演示如何使用风格迁移库进行基本的风格迁移。
"""

import torch
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import StyleTransfer, load_image, save_image


def main():
    """基本风格迁移示例"""
    print("=" * 60)
    print("风格迁移示例")
    print("=" * 60)

    # 1. 创建示例图像（如果需要真实图像，请替换为实际路径）
    print("\n1. 创建示例图像...")

    # 创建随机内容图像和风格图像（实际使用时应加载真实图像）
    content_image = torch.randn(1, 3, 256, 256)
    style_image = torch.randn(1, 3, 256, 256)

    print(f"   内容图像形状: {content_image.shape}")
    print(f"   风格图像形状: {style_image.shape}")

    # 2. 创建风格迁移器
    print("\n2. 创建风格迁移器...")

    transfer = StyleTransfer(
        content_layers=["conv4_2"],
        style_layers=["conv1_1", "conv2_1", "conv3_1", "conv4_1", "conv5_1"],
        content_weight=1.0,
        style_weight=1e6,
        tv_weight=1e-5,
        device="cpu",
    )

    print("   使用的层:")
    print(f"     内容层: {transfer.content_layers}")
    print(f"     风格层: {transfer.style_layers}")

    # 3. 定义回调函数
    print("\n3. 开始风格迁移...")

    def print_progress(step, loss_dict):
        if step % 50 == 0:
            print(f"   Step {step}: total_loss={loss_dict['total_loss']:.4f}, "
                  f"content_loss={loss_dict['content_loss']:.4f}, "
                  f"style_loss={loss_dict['style_loss']:.4f}")

    # 4. 执行风格迁移
    output = transfer.transfer(
        content_image=content_image,
        style_image=style_image,
        num_steps=200,
        optimizer_type="lbfgs",
        learning_rate=1.0,
        init_method="content",
        callback=print_progress,
    )

    print(f"\n4. 风格迁移完成!")
    print(f"   输出图像形状: {output.shape}")

    # 5. 保存结果
    print("\n5. 保存结果...")

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    save_image(output, output_dir / "basic_transfer_result.jpg")
    print(f"   结果已保存到: {output_dir / 'basic_transfer_result.jpg'}")

    # 6. 显示损失信息
    print("\n6. 损失信息:")
    loss_summary = transfer.get_loss_summary()
    for key, value in loss_summary.items():
        print(f"   {key}: {value:.4f}")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
