"""文字检测模块"""

import cv2
import numpy as np
from typing import List
from abc import ABC, abstractmethod


class TextDetector(ABC):
    """文字检测器基类"""

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        检测图像中的文字区域

        Args:
            image: 输入图像 (H, W, C)

        Returns:
            检测到的文字区域坐标列表
            每个元素为 (4, 2) 的数组，表示四边形的4个顶点
        """
        pass


class SimpleTextDetector(TextDetector):
    """基于传统方法的简单文字检测器

    使用形态学操作和轮廓检测来定位文字区域
    """

    def __init__(self, min_area: int = 100, max_area: int = 100000,
                 min_ratio: float = 0.1, max_ratio: float = 10.0):
        """
        Args:
            min_area: 最小区域面积
            max_area: 最大区域面积
            min_ratio: 最小宽高比
            max_ratio: 最大宽高比
        """
        self.min_area = min_area
        self.max_area = max_area
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio

    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        检测图像中的文字区域

        实现步骤：
        1. 灰度化
        2. 高斯模糊
        3. 自适应二值化
        4. 形态学操作
        5. 轮廓检测
        6. 矩形框提取

        Args:
            image: 输入图像 (H, W, C) 或 (H, W)

        Returns:
            检测到的文字区域坐标列表
        """
        # 灰度化
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 自适应二值化
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # 形态学操作：连接相邻文字
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(binary, kernel, iterations=1)

        # 轮廓检测
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 提取文字区域
        bboxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_area < area < self.max_area:
                # 获取最小外接矩形
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = box.astype(np.int32)

                # 检查宽高比
                width = rect[1][0]
                height = rect[1][1]
                if height > 0:
                    ratio = width / height
                    if self.min_ratio < ratio < self.max_ratio:
                        bboxes.append(box)

        return bboxes


class EASTTextDetector(TextDetector):
    """基于 EAST 的文字检测器

    注意：需要预训练的 EAST 模型文件
    """

    def __init__(self, model_path: str, input_size: int = 512,
                 confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.4):
        """
        Args:
            model_path: EAST 模型路径
            input_size: 输入图像大小
            confidence_threshold: 置信度阈值
            nms_threshold: NMS 阈值
        """
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold

        # 加载模型
        try:
            self.net = cv2.dnn.readNet(model_path)
            self.model_loaded = True
        except Exception as e:
            print(f"Warning: Failed to load EAST model: {e}")
            self.model_loaded = False

    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        使用 EAST 模型检测文字

        Args:
            image: 输入图像

        Returns:
            检测到的文字区域坐标列表
        """
        if not self.model_loaded:
            print("EAST model not loaded, returning empty results")
            return []

        orig_h, orig_w = image.shape[:2]

        # 预处理
        blob = cv2.dnn.blobFromImage(
            image, 1.0, (self.input_size, self.input_size),
            (123.68, 116.78, 103.94), True, False
        )

        # 前向传播
        self.net.setInput(blob)
        try:
            scores, geometry = self.net.forward([
                "feature_fusion/Conv_7/Sigmoid",
                "feature_fusion/concat_3"
            ])
        except Exception as e:
            print(f"EAST forward failed: {e}")
            return []

        # 解码检测结果
        bboxes, confidences = self._decode(scores, geometry)

        if len(bboxes) == 0:
            return []

        # NMS
        indices = cv2.dnn.NMSBoxesRotated(
            bboxes, confidences,
            self.confidence_threshold,
            self.nms_threshold
        )

        # 转换坐标
        results = []
        for i in indices:
            bbox = bboxes[i[0]]
            pts = self._rotated_rect_to_points(bbox, orig_w, orig_h)
            results.append(pts)

        return results

    def _decode(self, scores: np.ndarray, geometry: np.ndarray):
        """解码 EAST 输出"""
        num_rows, num_cols = scores.shape[2:4]
        bboxes = []
        confidences = []

        for y in range(num_rows):
            scores_data = scores[0, 0, y]
            x_data0 = geometry[0, 0, y]
            x_data1 = geometry[0, 1, y]
            x_data2 = geometry[0, 2, y]
            x_data3 = geometry[0, 3, y]
            angles_data = geometry[0, 4, y]

            for x in range(num_cols):
                score = scores_data[x]
                if score < self.confidence_threshold:
                    continue

                offset_x = x * 4.0
                offset_y = y * 4.0

                angle = angles_data[x]
                cos = np.cos(angle)
                sin = np.sin(angle)

                h = x_data0[x] + x_data2[x]
                w = x_data1[x] + x_data3[x]

                end_x = int(offset_x + cos * x_data1[x] + sin * x_data2[x])
                end_y = int(offset_y - sin * x_data1[x] + cos * x_data2[x])
                start_x = int(end_x - w)
                start_y = int(end_y - h)

                bboxes.append([start_x, start_y, end_x, end_y])
                confidences.append(float(score))

        return bboxes, confidences

    def _rotated_rect_to_points(self, bbox, orig_w: int, orig_h: int) -> np.ndarray:
        """将旋转矩形转换为四边形点"""
        # 简化实现
        x1, y1, x2, y2 = bbox
        pts = np.array([
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2]
        ], dtype=np.float32)
        return pts


def create_detector(detector_type: str = "simple", **kwargs) -> TextDetector:
    """
    创建检测器工厂函数

    Args:
        detector_type: 检测器类型 ("simple" 或 "east")
        **kwargs: 其他参数

    Returns:
        检测器实例
    """
    detectors = {
        "simple": SimpleTextDetector,
        "east": EASTTextDetector,
    }

    if detector_type not in detectors:
        raise ValueError(f"Unknown detector type: {detector_type}")

    return detectors[detector_type](**kwargs)