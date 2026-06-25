"""
超分辨率模型评估脚本

使用方法：
    python evaluate.py --model srcnn --checkpoint checkpoints/best.pth
"""

import argparse
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.evaluator import SREvaluator
from src.dataset import create_synthetic_dataset


def main():
    parser = argparse.ArgumentParser(description='Evaluate Super Resolution Model')

    # 模型参数
    parser.add_argument('--model', type=str, default='srcnn',
                        choices=['srcnn', 'espcn', 'edsr'],
                        help='Model name (default: srcnn)')
    parser.add_argument('--scale_factor', type=int, default=2,
                        help='Scale factor (default: 2)')

    # 评估参数
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Model checkpoint path')
    parser.add_argument('--test_dir', type=str, default='data/test',
                        help='Test data directory')
    parser.add_argument('--output_dir', type=str, default='results',
                        help='Output directory for results')

    # 其他参数
    parser.add_argument('--batch_size', type=int, default=1,
                        help='Batch size (default: 1)')
    parser.add_argument('--num_workers', type=int, default=4,
                        help='Number of data loading workers')
    parser.add_argument('--create_synthetic', action='store_true',
                        help='Create synthetic dataset for testing')

    args = parser.parse_args()

    # 创建合成数据集（用于测试）
    if args.create_synthetic:
        print("Creating synthetic dataset...")
        create_synthetic_dataset(args.test_dir, num_images=10, image_size=256)

    # 检查数据目录
    if not os.path.exists(args.test_dir):
        print(f"Error: Test directory {args.test_dir} does not exist")
        print("Use --create_synthetic to create a synthetic dataset")
        sys.exit(1)

    # 检查检查点文件
    if not os.path.exists(args.checkpoint):
        print(f"Error: Checkpoint file {args.checkpoint} does not exist")
        sys.exit(1)

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 创建评估器
    evaluator = SREvaluator(
        model_name=args.model,
        scale_factor=args.scale_factor
    )

    # 加载检查点
    evaluator.load_checkpoint(args.checkpoint)

    # 评估模型
    print("\n" + "="*50)
    print("Evaluating Model")
    print("="*50)

    results = evaluator.evaluate(
        test_dir=args.test_dir,
        batch_size=args.batch_size,
        num_workers=args.num_workers
    )

    # 打印结果
    print("\n" + "="*50)
    print("Evaluation Results")
    print("="*50)
    print(f"Number of images: {results['num_images']}")
    print(f"Average PSNR: {results['psnr']:.2f} dB")
    print(f"Average SSIM: {results['ssim']:.4f}")

    # 保存结果
    results_file = os.path.join(args.output_dir, 'evaluation_results.txt')
    with open(results_file, 'w') as f:
        f.write(f"Model: {args.model}\n")
        f.write(f"Scale Factor: {args.scale_factor}x\n")
        f.write(f"Checkpoint: {args.checkpoint}\n")
        f.write(f"Number of images: {results['num_images']}\n")
        f.write(f"Average PSNR: {results['psnr']:.2f} dB\n")
        f.write(f"Average SSIM: {results['ssim']:.4f}\n")

    print(f"\nResults saved to: {results_file}")

    print("\n" + "="*50)
    print("Evaluation Complete!")
    print("="*50)


if __name__ == '__main__':
    main()
