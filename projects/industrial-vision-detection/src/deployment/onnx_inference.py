"""
ONNX 推理实现

使用 ONNX Runtime 进行模型推理。

核心类:
- ONNXDetector: ONNX 检测器

参考:
- ONNX Runtime: https://onnxruntime.ai/

⭐ 重点理解:
- ONNX Runtime 的优势
- 如何优化推理性能
- CPU vs GPU 推理

💡 值得思考:
- ONNX Runtime 如何优化计算图？
- 如何选择合适的执行提供程序？
- 如何处理动态形状输入？
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from ..utils.boxes import non_max_suppression


class ONNXDetector:
    """
    ONNX 检测器

    使用 ONNX Runtime 加载和运行 ONNX 模型。

    Args:
        onnx_path (str): ONNX 模型路径
        providers (List[str]): 执行提供程序列表

    使用示例:
        detector = ONNXDetector('model.onnx')
        result = detector.predict(image)
    """

    def __init__(
        self,
        onnx_path: str,
        providers: Optional[List[str]] = None
    ):
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError("请安装 onnxruntime: pip install onnxruntime")

        self.onnx_path = Path(onnx_path)

        if not self.onnx_path.exists():
            raise FileNotFoundError(f"ONNX 模型不存在: {onnx_path}")

        # 设置执行提供程序
        if providers is None:
            providers = ['CPUExecutionProvider']
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers.insert(0, 'CUDAExecutionProvider')

        # 创建推理会话
        self.session = ort.InferenceSession(
            str(self.onnx_path),
            providers=providers
        )

        # 获取输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape

        print(f"加载 ONNX 模型: {self.onnx_path}")
        print(f"输入形状: {self.input_shape}")
        print(f"执行提供程序: {self.session.get_providers()}")

    def predict(
        self,
        image: Union[np.ndarray, torch.Tensor],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> Dict:
        """
        执行推理

        Args:
            image: 输入图像，可以是:
                - numpy.ndarray [H, W, 3] (BGR 或 RGB)
                - torch.Tensor [3, H, W] 或 [1, 3, H, W]
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值

        Returns:
            检测结果字典:
            - boxes: 边界框 [N, 4]
            - scores: 置信度 [N]
            - labels: 类别标签 [N]
            - inference_time: 推理时间 (秒)
        """
        import time

        # 预处理
        input_tensor = self._preprocess(image)

        # 推理
        start_time = time.time()
        outputs = self.session.run(None, {self.input_name: input_tensor})
        inference_time = time.time() - start_time

        # 后处理
        results = self._postprocess(outputs, conf_threshold, iou_threshold)
        results['inference_time'] = inference_time

        return results

    def _preprocess(
        self,
        image: Union[np.ndarray, torch.Tensor]
    ) -> np.ndarray:
        """
        预处理图像

        Args:
            image: 输入图像

        Returns:
            预处理后的张量
        """
        # 转换为 numpy
        if isinstance(image, torch.Tensor):
            image = image.numpy()

        # 确保形状正确
        if image.ndim == 3:
            # [H, W, 3] -> [1, 3, H, W]
            if image.shape[2] == 3:
                image = image.transpose(2, 0, 1)
            image = np.expand_dims(image, 0)

        # 归一化到 [0, 1]
        if image.max() > 1:
            image = image.astype(np.float32) / 255.0

        return image

    def _postprocess(
        self,
        outputs: List[np.ndarray],
        conf_threshold: float,
        iou_threshold: float
    ) -> Dict:
        """
        后处理输出

        Args:
            outputs: ONNX 输出
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值

        Returns:
            检测结果
        """
        # 假设输出格式为 [batch, num_detections, 5 + num_classes]
        # 其中每个检测包含 [x1, y1, x2, y2, confidence, class_scores...]
        predictions = outputs[0]

        if len(predictions.shape) == 3:
            predictions = predictions[0]  # 移除 batch 维度

        # 分离边界框和类别分数
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]

        # 计算最大类别分数
        max_scores = scores.max(axis=1)
        max_score_indices = scores.argmax(axis=1)

        # 过滤低置信度
        mask = max_scores > conf_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        max_score_indices = max_score_indices[mask]
        max_scores = max_scores[mask]

        # 应用 NMS
        if len(boxes) > 0:
            boxes_tensor = torch.from_numpy(boxes).float()
            scores_tensor = torch.from_numpy(scores).float()

            keep_indices = non_max_suppression(
                boxes_tensor, scores_tensor,
                iou_threshold=iou_threshold,
                score_threshold=conf_threshold
            )

            if len(keep_indices) > 0:
                return {
                    'boxes': boxes[keep_indices],
                    'scores': max_scores[keep_indices],
                    'labels': max_score_indices[keep_indices]
                }

        return {
            'boxes': np.zeros((0, 4)),
            'scores': np.zeros(0),
            'labels': np.zeros(0, dtype=np.int64)
        }

    def benchmark(
        self,
        input_shape: Tuple[int, int, int, int] = (1, 3, 640, 640),
        num_iterations: int = 100,
        warmup_iterations: int = 10
    ) -> Dict:
        """
        性能基准测试

        Args:
            input_shape: 输入形状
            num_iterations: 测试迭代次数
            warmup_iterations: 预热迭代次数

        Returns:
            性能指标字典
        """
        import time

        print(f"开始性能基准测试...")
        print(f"输入形状: {input_shape}")
        print(f"迭代次数: {num_iterations}")

        # 创建随机输入
        dummy_input = np.random.randn(*input_shape).astype(np.float32)

        # 预热
        print("预热中...")
        for _ in range(warmup_iterations):
            self.session.run(None, {self.input_name: dummy_input})

        # 测试
        print("测试中...")
        times = []
        for _ in range(num_iterations):
            start = time.time()
            self.session.run(None, {self.input_name: dummy_input})
            times.append(time.time() - start)

        # 计算统计信息
        times = np.array(times)
        results = {
            'mean_time': times.mean(),
            'std_time': times.std(),
            'min_time': times.min(),
            'max_time': times.max(),
            'fps': 1.0 / times.mean(),
            'num_iterations': num_iterations
        }

        print(f"\n性能测试结果:")
        print(f"  平均推理时间: {results['mean_time']*1000:.2f} ms")
        print(f"  FPS: {results['fps']:.1f}")
        print(f"  最小时间: {results['min_time']*1000:.2f} ms")
        print(f"  最大时间: {results['max_time']*1000:.2f} ms")

        return results


def test_onnx_inference():
    """
    测试 ONNX 推理

    验证:
    1. ONNX 检测器能正常加载
    2. 推理功能正常
    3. 输出格式正确
    """
    print("=" * 50)
    print("测试 ONNX 推理")
    print("=" * 50)

    # 导入模型
    from ..models import YOLOv8Tiny
    from .onnx_export import export_to_onnx

    # 创建模型
    model = YOLOv8Tiny(num_classes=5)
    model.eval()

    # 导出 ONNX
    onnx_path = 'test_detector.onnx'
    export_to_onnx(model, onnx_path, simplify=False)

    try:
        # 创建检测器
        print("\n1. 加载 ONNX 检测器")
        detector = ONNXDetector(onnx_path)

        # 创建测试图像
        print("\n2. 测试推理")
        image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        result = detector.predict(image, conf_threshold=0.1)

        print(f"   检测结果:")
        print(f"     boxes: {result['boxes'].shape}")
        print(f"     scores: {result['scores'].shape}")
        print(f"     labels: {result['labels'].shape}")
        print(f"     inference_time: {result['inference_time']*1000:.2f} ms")

        print("\n✓ ONNX 推理测试通过!")
    finally:
        # 清理
        import os
        if os.path.exists(onnx_path):
            os.remove(onnx_path)

    return True


if __name__ == '__main__':
    test_onnx_inference()
