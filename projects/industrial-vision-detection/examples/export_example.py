"""
导出示例

演示如何将模型导出为 ONNX 格式。

使用方法:
    python examples/export_example.py

⭐ 重点理解:
- ONNX 导出流程
- 模型验证
- 部署优化
"""

import torch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import YOLOv8Tiny
from src.deployment import export_to_onnx, validate_onnx_model, ONNXDetector


def main():
    """主导出函数"""
    print("=" * 60)
    print("工业视觉检测 - ONNX 导出示例")
    print("=" * 60)

    # 配置
    num_classes = 5
    input_shape = (1, 3, 640, 640)

    # 创建模型
    print("\n创建模型...")
    model = YOLOv8Tiny(num_classes=num_classes)
    model.eval()

    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}")

    # 导出路径
    onnx_path = 'yolov8_tiny.onnx'

    # 导出 ONNX
    print("\n导出 ONNX 模型...")
    export_to_onnx(
        model=model,
        output_path=onnx_path,
        input_shape=input_shape,
        opset_version=11,
        simplify=True
    )

    # 验证模型
    print("\n验证 ONNX 模型...")
    is_valid = validate_onnx_model(
        onnx_path=onnx_path,
        pytorch_model=model,
        input_shape=input_shape,
        rtol=1e-3,
        atol=1e-5
    )

    if is_valid:
        print("ONNX 模型验证通过!")
    else:
        print("ONNX 模型验证失败!")

    # 测试 ONNX 推理
    print("\n测试 ONNX 推理...")
    try:
        detector = ONNXDetector(onnx_path)

        # 创建测试输入
        import numpy as np
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # ONNX 推理
        result = detector.predict(test_image, conf_threshold=0.1)

        print(f"ONNX 推理结果:")
        print(f"  检测到 {len(result['boxes'])} 个目标")
        print(f"  推理时间: {result['inference_time']*1000:.2f} ms")

        # 性能基准测试
        print("\n性能基准测试...")
        benchmark_results = detector.benchmark(
            input_shape=input_shape,
            num_iterations=50,
            warmup_iterations=10
        )

    except Exception as e:
        print(f"ONNX 推理测试失败: {e}")

    # 清理
    print("\n清理临时文件...")
    if os.path.exists(onnx_path):
        os.remove(onnx_path)
        print(f"已删除: {onnx_path}")

    print("\n" + "=" * 60)
    print("导出完成!")
    print("=" * 60)

    print("\n💡 部署建议:")
    print("  1. 使用 TensorRT 进一步优化 GPU 推理")
    print("  2. 使用 ONNX Runtime 进行 CPU 推理")
    print("  3. 使用 OpenVINO 进行 Intel 设备优化")
    print("  4. 使用量化技术减少模型大小")


if __name__ == '__main__':
    main()
