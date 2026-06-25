"""
超分辨率演示脚本

演示 SRCNN 和 ESPCN 模型的使用
"""

import os
import sys
import torch
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SRCNN, ESPCN, get_model
from src.dataset import create_synthetic_dataset
from src.evaluator import SREvaluator
from src.utils import set_seed, calculate_psnr


def demo_models():
    """演示模型创建和使用"""
    print("="*60)
    print("Super Resolution Models Demo")
    print("="*60)

    # 设置随机种子
    set_seed(42)

    # 创建模型
    print("\n1. Creating Models...")

    # SRCNN
    srcnn = get_model('srcnn', num_channels=3, num_features=64, hidden_features=32)
    print(f"SRCNN Parameters: {sum(p.numel() for p in srcnn.parameters()):,}")

    # ESPCN
    espcn = get_model('espcn', scale_factor=2, num_channels=3, num_features=64)
    print(f"ESPCN Parameters: {sum(p.numel() for p in espcn.parameters()):,}")

    # 测试前向传播
    print("\n2. Testing Forward Pass...")

    # 低分辨率输入
    lr_image = torch.randn(1, 3, 32, 32)

    # SRCNN 需要先上采样
    lr_upsampled = torch.nn.functional.interpolate(
        lr_image,
        size=(64, 64),
        mode='bicubic',
        align_corners=False
    )

    # SRCNN 前向传播
    srcnn.eval()
    with torch.no_grad():
        sr_srcnn = srcnn(lr_upsampled)
    print(f"SRCNN Input: {lr_upsampled.shape}")
    print(f"SRCNN Output: {sr_srcnn.shape}")

    # ESPCN 前向传播
    espcn.eval()
    with torch.no_grad():
        sr_espcn = espcn(lr_image)
    print(f"ESPCN Input: {lr_image.shape}")
    print(f"ESPCN Output: {sr_espcn.shape}")

    # 演示 Pixel Shuffle
    print("\n3. Demonstrating Pixel Shuffle...")

    # 创建输入张量
    features = torch.randn(1, 12, 4, 4)  # 3 * 2^2 = 12 channels

    # 使用 PyTorch 内置的 pixel_shuffle
    output = torch.nn.functional.pixel_shuffle(features, 2)
    print(f"PixelShuffle Input: {features.shape}")
    print(f"PixelShuffle Output: {output.shape}")

    # 解释 Pixel Shuffle
    print("\nPixel Shuffle Explanation:")
    print("Input: [B, C*r^2, H, W]")
    print("Output: [B, C, H*r, W*r]")
    print("Where r is the scale factor")


def demo_upscale():
    """演示图像超分辨率"""
    print("\n" + "="*60)
    print("Image Upscaling Demo")
    print("="*60)

    # 创建临时目录
    os.makedirs('demo_data', exist_ok=True)
    os.makedirs('demo_results', exist_ok=True)

    # 创建合成数据集
    print("\n1. Creating synthetic dataset...")
    create_synthetic_dataset('demo_data', num_images=3, image_size=64)

    # 创建模型
    print("\n2. Creating and training model...")
    model = get_model('espcn', scale_factor=2)

    # 模拟训练（实际应用中需要真正的训练）
    model.eval()

    # 加载图像
    image_files = os.listdir('demo_data')
    if image_files:
        image_path = os.path.join('demo_data', image_files[0])
        image = Image.open(image_path).convert('RGB')

        # 转换为张量
        from torchvision import transforms
        to_tensor = transforms.ToTensor()
        lr_tensor = to_tensor(image).unsqueeze(0)

        # 前向传播
        print("\n3. Performing super resolution...")
        with torch.no_grad():
            sr_tensor = model(lr_tensor)

        # 转换为图像
        sr_tensor = sr_tensor.squeeze(0).cpu().clamp(0, 1)
        to_pil = transforms.ToPILImage()
        sr_image = to_pil(sr_tensor)

        # 保存结果
        sr_image.save('demo_results/sr_output.png')
        print(f"Super-resolution image saved to: demo_results/sr_output.png")

        # 计算 PSNR（需要高分辨率参考图像）
        print("\n4. Calculating PSNR...")
        hr_tensor = to_tensor(image.resize((sr_image.width, sr_image.height), Image.BICUBIC))
        psnr = calculate_psnr(sr_tensor.numpy(), hr_tensor.numpy())
        print(f"PSNR: {psnr:.2f} dB")

    # 清理
    print("\n5. Cleaning up...")
    import shutil
    if os.path.exists('demo_data'):
        shutil.rmtree('demo_data')
    print("Demo complete!")


def demo_comparison():
    """演示模型对比"""
    print("\n" + "="*60)
    print("Model Comparison Demo")
    print("="*60)

    # 创建输入
    lr_image = torch.randn(1, 3, 16, 16)

    # SRCNN
    print("\n1. SRCNN Model:")
    srcnn = get_model('srcnn')
    srcnn_lr = torch.nn.functional.interpolate(
        lr_image,
        size=(32, 32),
        mode='bicubic',
        align_corners=False
    )

    srcnn.eval()
    with torch.no_grad():
        sr_srcnn = srcnn(srcnn_lr)

    print(f"   Input: {srcnn_lr.shape}")
    print(f"   Output: {sr_srcnn.shape}")
    print(f"   Parameters: {sum(p.numel() for p in srcnn.parameters()):,}")

    # ESPCN
    print("\n2. ESPCN Model:")
    espcn = get_model('espcn', scale_factor=2)

    espcn.eval()
    with torch.no_grad():
        sr_espcn = espcn(lr_image)

    print(f"   Input: {lr_image.shape}")
    print(f"   Output: {sr_espcn.shape}")
    print(f"   Parameters: {sum(p.numel() for p in espcn.parameters()):,}")

    # 对比
    print("\n3. Comparison:")
    print("   SRCNN: 先上采样，再CNN处理，参数较多")
    print("   ESPCN: 在低分辨率空间提取特征，使用PixelShuffle，参数较少")
    print("   ESPCN 计算效率更高，适合实时应用")


if __name__ == '__main__':
    # 运行所有演示
    demo_models()
    demo_upscale()
    demo_comparison()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
