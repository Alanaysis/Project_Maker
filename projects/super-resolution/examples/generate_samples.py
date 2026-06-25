"""
生成示例图像

用于演示超分辨率效果
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dataset import create_synthetic_dataset


def main():
    """生成示例图像"""
    # 创建示例图像目录
    sample_dir = os.path.join(os.path.dirname(__file__), 'sample_images')
    os.makedirs(sample_dir, exist_ok=True)

    # 生成合成图像
    print("Generating sample images...")
    create_synthetic_dataset(sample_dir, num_images=5, image_size=256)

    print(f"Generated 5 sample images in {sample_dir}")
    print("You can use these images to test the super-resolution models.")


if __name__ == '__main__':
    main()
