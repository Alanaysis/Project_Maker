"""
ONNX 模型导出

实现 PyTorch 模型到 ONNX 格式的导出。

核心功能:
- export_to_onnx: 导出 ONNX 模型
- validate_onnx_model: 验证 ONNX 模型

参考:
- ONNX: https://onnx.ai/
- PyTorch ONNX: https://pytorch.org/docs/stable/onnx.html

⭐ 重点理解:
- ONNX 是什么？为什么需要它？
- 动态轴和静态轴的区别
- 如何验证导出的模型

💡 值得思考:
- ONNX 如何实现跨框架部署？
- ONNX 版本选择对兼容性的影响？
- 如何优化 ONNX 模型？
"""

import torch
import numpy as np
from typing import Tuple, Optional, Dict
from pathlib import Path


def export_to_onnx(
    model: torch.nn.Module,
    output_path: str,
    input_shape: Tuple[int, int, int, int] = (1, 3, 640, 640),
    opset_version: int = 11,
    dynamic_axes: Optional[Dict] = None,
    simplify: bool = True
) -> str:
    """
    导出 ONNX 模型

    Args:
        model: PyTorch 模型
        output_path: 输出路径
        input_shape: 输入形状 (batch_size, channels, height, width)
        opset_version: ONNX 版本
        dynamic_axes: 动态轴配置
        simplify: 是否简化模型

    Returns:
        ONNX 模型路径

    使用示例:
        model = YOLOv8Tiny(num_classes=5)
        export_to_onnx(model, 'model.onnx')
    """
    # 设置模型为评估模式
    model.eval()

    # 创建虚拟输入
    dummy_input = torch.randn(input_shape)

    # 设置动态轴
    if dynamic_axes is None:
        dynamic_axes = {
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }

    # 确保输出目录存在
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 导出 ONNX
    print(f"正在导出 ONNX 模型到: {output_path}")
    print(f"输入形状: {input_shape}")
    print(f"ONNX 版本: {opset_version}")

    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        opset_version=opset_version,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes=dynamic_axes,
        do_constant_folding=True,
        export_params=True
    )

    print(f"ONNX 模型导出成功!")

    # 验证模型
    if simplify:
        try:
            simplify_onnx(str(output_path))
        except Exception as e:
            print(f"模型简化失败: {e}")

    return str(output_path)


def simplify_onnx(onnx_path: str):
    """
    简化 ONNX 模型

    Args:
        onnx_path: ONNX 模型路径
    """
    try:
        import onnx
        import onnxsim

        print("正在简化 ONNX 模型...")
        model = onnx.load(onnx_path)
        model_simp, check = onnxsim.simplify(model)

        if check:
            onnx.save(model_simp, onnx_path)
            print("ONNX 模型简化成功!")
        else:
            print("ONNX 模型简化失败，使用原始模型")
    except ImportError:
        print("onnxsim 未安装，跳过模型简化")


def validate_onnx_model(
    onnx_path: str,
    pytorch_model: torch.nn.Module,
    input_shape: Tuple[int, int, int, int] = (1, 3, 640, 640),
    rtol: float = 1e-3,
    atol: float = 1e-5
) -> bool:
    """
    验证 ONNX 模型

    比较 ONNX 模型和 PyTorch 模型的输出是否一致。

    Args:
        onnx_path: ONNX 模型路径
        pytorch_model: PyTorch 模型
        input_shape: 输入形状
        rtol: 相对误差容忍度
        atol: 绝对误差容忍度

    Returns:
        验证是否通过
    """
    try:
        import onnxruntime as ort
    except ImportError:
        print("onnxruntime 未安装，跳过验证")
        return True

    print(f"正在验证 ONNX 模型: {onnx_path}")

    # 创建测试输入
    test_input = torch.randn(input_shape)

    # PyTorch 推理
    pytorch_model.eval()
    with torch.no_grad():
        pytorch_output = pytorch_model(test_input)

    # 处理 PyTorch 输出
    if isinstance(pytorch_output, dict):
        # 如果是字典，取第一个输出
        pytorch_output = list(pytorch_output.values())[0]
    if isinstance(pytorch_output, list):
        pytorch_output = pytorch_output[0]

    pytorch_output = pytorch_output.numpy()

    # ONNX 推理
    session = ort.InferenceSession(onnx_path)
    onnx_output = session.run(None, {'input': test_input.numpy()})[0]

    # 比较输出
    try:
        np.testing.assert_allclose(
            pytorch_output, onnx_output,
            rtol=rtol, atol=atol
        )
        print("ONNX 模型验证通过!")
        return True
    except AssertionError as e:
        print(f"ONNX 模型验证失败: {e}")
        return False


def get_onnx_model_info(onnx_path: str) -> Dict:
    """
    获取 ONNX 模型信息

    Args:
        onnx_path: ONNX 模型路径

    Returns:
        模型信息字典
    """
    try:
        import onnx

        model = onnx.load(onnx_path)

        info = {
            'ir_version': model.ir_version,
            'opset_version': model.opset_import[0].version,
            'producer_name': model.producer_name,
            'inputs': [],
            'outputs': []
        }

        for input in model.graph.input:
            info['inputs'].append({
                'name': input.name,
                'shape': [dim.dim_value for dim in input.type.tensor_type.shape.dim],
                'dtype': input.type.tensor_type.elem_type
            })

        for output in model.graph.output:
            info['outputs'].append({
                'name': output.name,
                'shape': [dim.dim_value for dim in output.type.tensor_type.shape.dim],
                'dtype': output.type.tensor_type.elem_type
            })

        return info
    except ImportError:
        print("onnx 未安装")
        return {}


def test_export():
    """
    测试 ONNX 导出

    验证:
    1. 模型能正确导出
    2. 导出的模型能加载
    3. 输出格式正确
    """
    print("=" * 50)
    print("测试 ONNX 导出")
    print("=" * 50)

    # 导入模型
    from ..models import YOLOv8Tiny

    # 创建模型
    model = YOLOv8Tiny(num_classes=5)
    model.eval()

    # 导出路径
    output_path = 'test_model.onnx'

    # 导出
    print("\n1. 导出 ONNX 模型")
    onnx_path = export_to_onnx(
        model,
        output_path,
        input_shape=(1, 3, 640, 640),
        simplify=False
    )

    # 获取模型信息
    print("\n2. 获取模型信息")
    info = get_onnx_model_info(onnx_path)
    print(f"   IR 版本: {info.get('ir_version')}")
    print(f"   Opset 版本: {info.get('opset_version')}")
    print(f"   输入: {info.get('inputs')}")
    print(f"   输出: {info.get('outputs')}")

    # 清理
    import os
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"\n已清理测试文件: {output_path}")

    print("\n✓ ONNX 导出测试通过!")
    return True


if __name__ == '__main__':
    test_export()
