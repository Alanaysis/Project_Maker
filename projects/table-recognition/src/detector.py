"""
表格检测模块

使用深度学习模型检测图像中的表格区域。
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2
import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.transforms import functional as F

logger = logging.getLogger(__name__)


class TableDetector:
    """
    表格检测器

    使用 Faster R-CNN 模型检测图像中的表格区域。
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        device: Optional[str] = None,
    ):
        """
        初始化表格检测器

        Args:
            model_path: 预训练模型路径，None 则使用默认模型
            confidence_threshold: 置信度阈值
            device: 计算设备 (cpu/cuda)
        """
        self.confidence_threshold = confidence_threshold

        # 设置设备
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"使用设备: {self.device}")

        # 加载模型
        self.model = self._load_model(model_path)
        self.model.to(self.device)
        self.model.eval()

    def _load_model(self, model_path: Optional[str]) -> nn.Module:
        """
        加载检测模型

        Args:
            model_path: 模型路径

        Returns:
            加载的模型
        """
        if model_path is not None:
            logger.info(f"加载自定义模型: {model_path}")
            model = torch.load(model_path, map_location=self.device)
        else:
            logger.info("加载预训练 Faster R-CNN 模型")
            # 使用预训练的 Faster R-CNN，修改为表格检测
            model = fasterrcnn_resnet50_fpn(pretrained=True)

            # 修改分类头：1 个类（表格）+ 背景
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(
                in_features, num_classes=2
            )

        return model

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        预处理图像

        Args:
            image: 输入图像 (BGR 格式)

        Returns:
            预处理后的张量
        """
        # BGR 转 RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 转换为张量并归一化
        image_tensor = F.to_tensor(image_rgb)

        return image_tensor

    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        检测图像中的表格

        Args:
            image: 输入图像 (BGR 格式)

        Returns:
            检测结果列表，每个结果包含:
                - bbox: 边界框 [x1, y1, x2, y2]
                - confidence: 置信度
                - class_id: 类别 ID
        """
        # 保存原始尺寸
        orig_h, orig_w = image.shape[:2]

        # 预处理
        image_tensor = self.preprocess(image)
        image_tensor = image_tensor.unsqueeze(0).to(self.device)

        # 推理
        with torch.no_grad():
            predictions = self.model(image_tensor)

        # 解析结果
        pred = predictions[0]
        boxes = pred["boxes"].cpu().numpy()
        scores = pred["scores"].cpu().numpy()
        labels = pred["labels"].cpu().numpy()

        # 过滤低置信度结果
        results = []
        for box, score, label in zip(boxes, scores, labels):
            if score >= self.confidence_threshold:
                # 确保坐标在图像范围内
                x1, y1, x2, y2 = box
                x1 = max(0, min(x1, orig_w))
                y1 = max(0, min(y1, orig_h))
                x2 = max(0, min(x2, orig_w))
                y2 = max(0, min(y2, orig_h))

                results.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(score),
                    "class_id": int(label),
                })

        logger.info(f"检测到 {len(results)} 个表格")
        return results

    def detect_with_visualization(
        self,
        image: np.ndarray,
        results: List[Dict],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
    ) -> np.ndarray:
        """
        在图像上绘制检测结果

        Args:
            image: 原始图像
            results: 检测结果
            color: 边界框颜色 (BGR)
            thickness: 线条粗细

        Returns:
            绘制了边界框的图像
        """
        vis_image = image.copy()

        for result in results:
            bbox = result["bbox"]
            confidence = result["confidence"]

            # 绘制边界框
            cv2.rectangle(
                vis_image,
                (bbox[0], bbox[1]),
                (bbox[2], bbox[3]),
                color,
                thickness,
            )

            # 添加标签
            label = f"Table: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            cv2.rectangle(
                vis_image,
                (bbox[0], bbox[1] - label_size[1] - 10),
                (bbox[0] + label_size[0], bbox[1]),
                color,
                -1,
            )
            cv2.putText(
                vis_image,
                label,
                (bbox[0], bbox[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        return vis_image

    def crop_table_regions(
        self,
        image: np.ndarray,
        results: List[Dict],
        padding: int = 5,
    ) -> List[np.ndarray]:
        """
        裁剪表格区域

        Args:
            image: 原始图像
            results: 检测结果
            padding: 边界填充像素

        Returns:
            裁剪的表格图像列表
        """
        h, w = image.shape[:2]
        crops = []

        for result in results:
            x1, y1, x2, y2 = result["bbox"]

            # 添加填充
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            # 裁剪
            crop = image[y1:y2, x1:x2]
            crops.append(crop)

        return crops


class SimpleTableDetector:
    """
    简单表格检测器

    使用传统图像处理方法检测表格（无需深度学习）。
    适用于简单场景。
    """

    def __init__(
        self,
        min_area: int = 1000,
        aspect_ratio_range: Tuple[float, float] = (0.2, 5.0),
    ):
        """
        初始化简单表格检测器

        Args:
            min_area: 最小区域面积
            aspect_ratio_range: 宽高比范围
        """
        self.min_area = min_area
        self.aspect_ratio_range = aspect_ratio_range

    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        检测图像中的表格

        Args:
            image: 输入图像

        Returns:
            检测结果列表
        """
        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 膨胀操作连接线条
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # 查找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.min_area:
                continue

            # 获取边界框
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h

            # 检查宽高比
            if not (self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]):
                continue

            # 计算矩形度
            rect_area = w * h
            extent = area / rect_area

            if extent > 0.5:  # 矩形度阈值
                results.append({
                    "bbox": [x, y, x + w, y + h],
                    "confidence": extent,
                    "class_id": 1,
                })

        logger.info(f"简单检测器检测到 {len(results)} 个表格")
        return results
