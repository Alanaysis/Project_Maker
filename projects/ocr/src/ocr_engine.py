"""OCR 引擎"""

import numpy as np
from typing import List, Dict, Optional
from .detector import TextDetector, SimpleTextDetector
from .recognizer import TextRecognizer
from .utils import crop_text_region, draw_results


class OCREngine:
    """OCR 引擎

    整合文字检测和文字识别的完整 OCR 系统
    """

    def __init__(self, detector: Optional[TextDetector] = None,
                 recognizer: Optional[TextRecognizer] = None):
        """
        Args:
            detector: 文字检测器
            recognizer: 文字识别器
        """
        self.detector = detector or SimpleTextDetector()
        self.recognizer = recognizer or TextRecognizer()

    def process(self, image: np.ndarray) -> List[Dict]:
        """
        处理单张图像

        Args:
            image: 输入图像 (H, W, C)

        Returns:
            识别结果列表
            [
                {
                    "bbox": np.ndarray,  # 文字区域坐标
                    "text": str,         # 识别文本
                    "confidence": float  # 置信度
                },
                ...
            ]
        """
        # 文字检测
        bboxes = self.detector.detect(image)

        results = []
        for bbox in bboxes:
            # 裁剪文字区域
            cropped = crop_text_region(image, bbox)

            # 检查裁剪结果
            if cropped.size == 0:
                continue

            # 文字识别
            text, confidence = self.recognizer.recognize(cropped)

            if text:  # 过滤空结果
                results.append({
                    "bbox": bbox,
                    "text": text,
                    "confidence": confidence
                })

        return results

    def process_batch(self, images: List[np.ndarray]) -> List[List[Dict]]:
        """
        批量处理

        Args:
            images: 图像列表

        Returns:
            每张图像的识别结果列表
        """
        all_results = []
        for image in images:
            results = self.process(image)
            all_results.append(results)
        return all_results

    def visualize(self, image: np.ndarray, results: List[Dict]) -> np.ndarray:
        """
        可视化结果

        Args:
            image: 输入图像
            results: 识别结果

        Returns:
            可视化后的图像
        """
        return draw_results(image, results)

    def detect_only(self, image: np.ndarray) -> List[np.ndarray]:
        """
        仅检测文字区域

        Args:
            image: 输入图像

        Returns:
            检测到的文字区域坐标列表
        """
        return self.detector.detect(image)

    def recognize_only(self, image: np.ndarray):
        """
        仅识别文字（假设整个图像都是文字）

        Args:
            image: 输入图像

        Returns:
            (识别文本, 置信度)
        """
        return self.recognizer.recognize(image)


class OCRError(Exception):
    """OCR 基础异常"""
    pass


class DetectionError(OCRError):
    """检测错误"""
    pass


class RecognitionError(OCRError):
    """识别错误"""
    pass


class ModelLoadError(OCRError):
    """模型加载错误"""
    pass


def create_ocr_engine(detector_type: str = "simple",
                      recognizer_model: Optional[str] = None,
                      charset: Optional[str] = None,
                      device: str = "cpu") -> OCREngine:
    """
    创建 OCR 引擎工厂函数

    Args:
        detector_type: 检测器类型
        recognizer_model: 识别器模型路径
        charset: 字符集
        device: 设备

    Returns:
        OCR 引擎实例
    """
    from .detector import create_detector
    from .recognizer import create_recognizer

    detector = create_detector(detector_type)
    recognizer = create_recognizer(
        model_path=recognizer_model,
        charset=charset,
        device=device
    )

    return OCREngine(detector, recognizer)