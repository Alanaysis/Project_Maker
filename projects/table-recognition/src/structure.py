"""
表格结构识别模块

识别表格的行列结构，包括检测横线和竖线。
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class StructureRecognizer:
    """
    表格结构识别器

    通过检测水平线和垂直线来识别表格的行列结构。
    """

    def __init__(
        self,
        line_threshold: int = 50,
        min_line_length: int = 100,
        max_line_gap: int = 10,
        merge_threshold: int = 10,
    ):
        """
        初始化结构识别器

        Args:
            line_threshold: 霍夫变换阈值
            min_line_length: 最小线段长度
            max_line_gap: 最大线段间隔
            merge_threshold: 线段合并阈值（像素）
        """
        self.line_threshold = line_threshold
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap
        self.merge_threshold = merge_threshold

    def recognize(self, table_image: np.ndarray) -> Dict:
        """
        识别表格结构

        Args:
            table_image: 表格图像

        Returns:
            结构信息，包含:
                - rows: 行数
                - columns: 列数
                - horizontal_lines: 水平线位置列表
                - vertical_lines: 垂直线位置列表
                - cells: 单元格坐标列表
        """
        # 预处理
        binary = self._preprocess(table_image)

        # 检测水平线
        horizontal_lines = self._detect_horizontal_lines(binary)

        # 检测垂直线
        vertical_lines = self._detect_vertical_lines(binary)

        # 合并相近的线
        horizontal_lines = self._merge_lines(horizontal_lines, direction="horizontal")
        vertical_lines = self._merge_lines(vertical_lines, direction="vertical")

        # 计算行列数
        rows = max(0, len(horizontal_lines) - 1)
        columns = max(0, len(vertical_lines) - 1)

        # 生成单元格坐标
        cells = self._generate_cells(horizontal_lines, vertical_lines)

        result = {
            "rows": rows,
            "columns": columns,
            "horizontal_lines": horizontal_lines,
            "vertical_lines": vertical_lines,
            "cells": cells,
        }

        logger.info(f"识别到 {rows} 行 x {columns} 列的表格结构")
        return result

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像

        Args:
            image: 输入图像

        Returns:
            二值化图像
        """
        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 高斯模糊去噪
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 自适应二值化
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        return binary

    def _detect_horizontal_lines(self, binary: np.ndarray) -> List[int]:
        """
        检测水平线

        Args:
            binary: 二值化图像

        Returns:
            水平线 y 坐标列表
        """
        h, w = binary.shape

        # 创建水平线检测核
        kernel_length = max(w // 10, self.min_line_length)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))

        # 形态学开运算提取水平线
        horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        # 膨胀连接断开的线
        horizontal = cv2.dilate(horizontal, kernel, iterations=1)

        # 查找轮廓
        contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 提取 y 坐标
        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > self.min_line_length:
                lines.append(y + h // 2)

        # 排序
        lines.sort()

        return lines

    def _detect_vertical_lines(self, binary: np.ndarray) -> List[int]:
        """
        检测垂直线

        Args:
            binary: 二值化图像

        Returns:
            垂直线 x 坐标列表
        """
        h, w = binary.shape

        # 创建垂直线检测核
        kernel_length = max(h // 10, self.min_line_length)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))

        # 形态学开运算提取垂直线
        vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        # 膨胀连接断开的线
        vertical = cv2.dilate(vertical, kernel, iterations=1)

        # 查找轮廓
        contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 提取 x 坐标
        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > self.min_line_length:
                lines.append(x + w // 2)

        # 排序
        lines.sort()

        return lines

    def _merge_lines(self, lines: List[int], direction: str) -> List[int]:
        """
        合并相近的线

        Args:
            lines: 线坐标列表
            direction: 方向 (horizontal/vertical)

        Returns:
            合并后的线坐标列表
        """
        if not lines:
            return []

        merged = [lines[0]]
        for line in lines[1:]:
            if abs(line - merged[-1]) <= self.merge_threshold:
                # 合并
                merged[-1] = (merged[-1] + line) // 2
            else:
                merged.append(line)

        return merged

    def _generate_cells(
        self,
        horizontal_lines: List[int],
        vertical_lines: List[int],
    ) -> List[Dict]:
        """
        生成单元格坐标

        Args:
            horizontal_lines: 水平线坐标列表
            vertical_lines: 垂直线坐标列表

        Returns:
            单元格坐标列表
        """
        cells = []

        if len(horizontal_lines) < 2 or len(vertical_lines) < 2:
            return cells

        for i in range(len(horizontal_lines) - 1):
            for j in range(len(vertical_lines) - 1):
                cell = {
                    "row": i,
                    "col": j,
                    "bbox": [
                        vertical_lines[j],      # x1
                        horizontal_lines[i],    # y1
                        vertical_lines[j + 1],  # x2
                        horizontal_lines[i + 1], # y2
                    ],
                }
                cells.append(cell)

        return cells


class LineBasedStructureRecognizer:
    """
    基于线条的表格结构识别器

    使用霍夫变换检测线条来识别表格结构。
    """

    def __init__(
        self,
        hough_threshold: int = 100,
        min_line_length: int = 50,
        max_line_gap: int = 5,
        angle_threshold: float = 5.0,
    ):
        """
        初始化识别器

        Args:
            hough_threshold: 霍夫变换累加器阈值
            min_line_length: 最小线段长度
            max_line_gap: 最大线段间隔
            angle_threshold: 角度阈值（度）
        """
        self.hough_threshold = hough_threshold
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap
        self.angle_threshold = angle_threshold

    def recognize(self, table_image: np.ndarray) -> Dict:
        """
        识别表格结构

        Args:
            table_image: 表格图像

        Returns:
            结构信息
        """
        # 预处理
        if len(table_image.shape) == 3:
            gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = table_image.copy()

        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # 霍夫线变换
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap,
        )

        if lines is None:
            return {
                "rows": 0,
                "columns": 0,
                "horizontal_lines": [],
                "vertical_lines": [],
                "cells": [],
            }

        # 分类线条
        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # 计算角度
            if x2 - x1 == 0:
                angle = 90.0
            else:
                angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))

            # 分类
            if angle < self.angle_threshold or angle > (180 - self.angle_threshold):
                # 水平线
                horizontal_lines.append((y1 + y2) // 2)
            elif abs(angle - 90) < self.angle_threshold:
                # 垂直线
                vertical_lines.append((x1 + x2) // 2)

        # 排序
        horizontal_lines.sort()
        vertical_lines.sort()

        # 合并相近的线
        horizontal_lines = self._merge_close_lines(horizontal_lines)
        vertical_lines = self._merge_close_lines(vertical_lines)

        # 生成单元格
        cells = self._generate_cells(horizontal_lines, vertical_lines)

        return {
            "rows": max(0, len(horizontal_lines) - 1),
            "columns": max(0, len(vertical_lines) - 1),
            "horizontal_lines": horizontal_lines,
            "vertical_lines": vertical_lines,
            "cells": cells,
        }

    def _merge_close_lines(self, lines: List[int], threshold: int = 10) -> List[int]:
        """合并相近的线"""
        if not lines:
            return []

        merged = [lines[0]]
        for line in lines[1:]:
            if abs(line - merged[-1]) <= threshold:
                merged[-1] = (merged[-1] + line) // 2
            else:
                merged.append(line)

        return merged

    def _generate_cells(
        self,
        horizontal_lines: List[int],
        vertical_lines: List[int],
    ) -> List[Dict]:
        """生成单元格坐标"""
        cells = []

        if len(horizontal_lines) < 2 or len(vertical_lines) < 2:
            return cells

        for i in range(len(horizontal_lines) - 1):
            for j in range(len(vertical_lines) - 1):
                cell = {
                    "row": i,
                    "col": j,
                    "bbox": [
                        vertical_lines[j],
                        horizontal_lines[i],
                        vertical_lines[j + 1],
                        horizontal_lines[i + 1],
                    ],
                }
                cells.append(cell)

        return cells


class CNNStructureRecognizer:
    """
    基于 CNN 的表格结构识别器

    使用语义分割模型识别表格结构。
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        初始化 CNN 结构识别器

        Args:
            model_path: 模型路径
        """
        self.model_path = model_path
        self.model = None

        # 如果有模型路径，加载模型
        if model_path:
            self._load_model()

    def _load_model(self):
        """加载模型"""
        try:
            import torch
            self.model = torch.load(self.model_path)
            self.model.eval()
            logger.info(f"加载 CNN 结构识别模型: {self.model_path}")
        except Exception as e:
            logger.warning(f"无法加载 CNN 模型: {e}")
            self.model = None

    def recognize(self, table_image: np.ndarray) -> Dict:
        """
        识别表格结构

        Args:
            table_image: 表格图像

        Returns:
            结构信息
        """
        # 如果没有模型，回退到传统方法
        if self.model is None:
            logger.warning("CNN 模型未加载，使用传统方法")
            recognizer = StructureRecognizer()
            return recognizer.recognize(table_image)

        # 使用 CNN 模型
        # 这里简化实现，实际应该有完整的推理流程
        import torch
        from torchvision.transforms import functional as F

        # 预处理
        if len(table_image.shape) == 3:
            image_rgb = cv2.cvtColor(table_image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(table_image, cv2.COLOR_GRAY2RGB)

        image_tensor = F.to_tensor(image_rgb).unsqueeze(0)

        # 推理
        with torch.no_grad():
            output = self.model(image_tensor)

        # 后处理（简化）
        # 实际应该解析模型输出得到线条位置
        return {
            "rows": 0,
            "columns": 0,
            "horizontal_lines": [],
            "vertical_lines": [],
            "cells": [],
        }
