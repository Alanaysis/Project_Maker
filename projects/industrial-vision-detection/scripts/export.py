"""
导出脚本

使用方法:
    python scripts/export.py --model runs/best_model.pth --format onnx
    python scripts/export.py --model runs/best_model.pth --format onnx --simplify

⭐ 重点理解:
- 模型导出流程
- ONNX 格式
- 模型优化
"""

import argparse
import torch
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import YOLOModel
from src.deployment import export_to_onnx, validate_onnx_model, ONNXDetector


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='工业视觉检测 - 导出脚本')

    # 模型参数
    parser.add_argument('--model', type=str, required=True,
                        help='模型检查点路径')
    parser.add_argument('--num-classes', type=int, default=5,
                        help='类别数')

    # 导出参数
    parser.add_argument('--format', type=str, default='onnx',
                        choices=['onnx'],
                        help='导出格式')
    parser.add_argument('--output', type=str, default=None,
                        help='输出路径')
    parser.add_argument('--input-shape', type=int, nargs=4,
                        default=[1, 3, 640, 640],
                        help='输入形状 (batch, channels, height, width)')
    parser.add_argument('--opset-version', type=int, default=11,
                        help='ONNX 版本')
    parser.add_argument('--simplify', action='store_true',
                        help='简化模型')

    # 验证参数
    parser.add_argument('--validate', action='store_true',
                        help='验证导出的模型')
    parser.add_argument('--benchmark', action='store_true',
                        help='性能基准测试')

    return parser.parse_args()


def main():
    """主导出函数"""
    args = parse_args()

    print("=" * 60)
    print("工业视觉检测 - 导出脚本")
    print("=" * 60)

    # 加载模型
    print(f"\n加载模型: {args.model}")
    model = YOLOModel.load_pretrained(args.model)
    model.eval()

    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}")

    # 输出路径
    if args.output is None:
        model_name = Path(args.model).stem
        args.output = f'{model_name}.{args.format}'

    # 输入形状
    input_shape = tuple(args.input_shape)
    print(f"\n输入形状: {input_shape}")

    # 导出
    if args.format == 'onnx':
        print(f"\n导出 ONNX 模型到: {args.output}")

        onnx_path = export_to_onnx(
            model=model,
            output_path=args.output,
            input_shape=input_shape,
            opset_version=args.opset_version,
            simplify=args.simplify
        )

        print(f"ONNX 模型导出成功: {onnx_path}")

        # 验证
        if args.validate:
            print("\n验证 ONNX 模型...")
            is_valid = validate_onnx_model(
                onnx_path=onnx_path,
                pytorch_model=model,
                input_shape=input_shape
            )

            if is_valid:
                print("ONNX 模型验证通过!")
            else:
                print("ONNX 模型验证失败!")

        # 性能测试
        if args.benchmark:
            print("\n性能基准测试...")
            try:
                detector = ONNXDetector(onnx_path)
                results = detector.benchmark(
                    input_shape=input_shape,
                    num_iterations=100,
                    warmup_iterations=10
                )
            except Exception as e:
                print(f"性能测试失败: {e}")

    print("\n" + "=" * 60)
    print("导出完成!")
    print("=" * 60)

    # 部署建议
    print("\n💡 部署建议:")
    print("  1. 使用 ONNX Runtime 进行 CPU 推理")
    print("  2. 使用 TensorRT 进行 GPU 推理优化")
    print("  3. 使用 OpenVINO 进行 Intel 设备优化")
    print("  4. 使用量化技术减少模型大小")


if __name__ == '__main__':
    main()
