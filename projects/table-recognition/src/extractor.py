"""
单元格提取模块

从表格图像中提取单元格区域。
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class CellExtractor:
    """
    单元格提取器

    根据表格结构信息提取单元格区域。
    """

    def __init__(
        self,
        padding: int = 2,
        min_cell_size: int = 10,
        border_removal: bool = True,
    ):
        """
        初始化单元格提取器

        Args:
            padding: 单元格内边距（像素）
            min_cell_size: 最小单元格尺寸
            border_removal: 是否移除边框
        """
        self.padding = padding
        self.min_cell_size = min_cell_size
        self.border_removal = border_removal

    def extract(
        self,
        table_image: np.ndarray,
        structure: Dict,
    ) -> List[Dict]:
        """
        提取单元格

        Args:
            table_image: 表格图像
            structure: 表格结构信息

        Returns:
            单元格列表，每个单元格包含:
                - row: 行号
                - col: 列号
                - bbox: 边界框
                - image: 单元格图像
                - content: 单元格内容（如有）
        """
        cells = structure.get("cells", [])
        extracted_cells = []

        for cell in cells:
            row = cell["row"]
            col = cell["col"]
            bbox = cell["bbox"]

            # 验证单元格尺寸
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1

            if width < self.min_cell_size or height < self.min_cell_size:
                logger.debug(f"跳过过小的单元格 ({row}, {col}): {width}x{height}")
                continue

            # 添加内边距
            padded_bbox = self._add_padding(bbox, table_image.shape)

            # 提取单元格图像
            px1, py1, px2, py2 = padded_bbox
            cell_image = table_image[py1:py2, px1:px2]

            # 移除边框（可选）
            if self.border_removal:
                cell_image = self._remove_border(cell_image)

            extracted_cell = {
                "row": row,
                "col": col,
                "bbox": bbox,
                "padded_bbox": padded_bbox,
                "image": cell_image,
                "content": None,  # 后续由识别模块填充
            }

            extracted_cells.append(extracted_cell)

        logger.info(f"提取了 {len(extracted_cells)} 个单元格")
        return extracted_cells

    def _add_padding(
        self,
        bbox: List[int],
        image_shape: Tuple[int, ...],
    ) -> List[int]:
        """
        添加内边距

        Args:
            bbox: 原始边界框
            image_shape: 图像形状

        Returns:
            添加边距后的边界框
        """
        x1, y1, x2, y2 = bbox
        h, w = image_shape[:2]

        # 添加边距
        x1 = max(0, x1 + self.padding)
        y1 = max(0, y1 + self.padding)
        x2 = min(w, x2 - self.padding)
        y2 = min(h, y2 - self.padding)

        return [x1, y1, x2, y2]

    def _remove_border(self, cell_image: np.ndarray) -> np.ndarray:
        """
        移除单元格边框

        Args:
            cell_image: 单元格图像

        Returns:
            移除边框后的图像
        """
        if cell_image.size == 0:
            return cell_image

        h, w = cell_image.shape[:2]

        # 移除边缘像素
        border = 2
        if h > 2 * border and w > 2 * border:
            return cell_image[border:h-border, border:w-border]

        return cell_image


class AdaptiveCellExtractor:
    """
    自适应单元格提取器

    根据表格内容自适应调整单元格提取策略。
    """

    def __init__(
        self,
        threshold_method: str = "otsu",
        min_cell_area: int = 100,
        max_cell_area: int = 100000,
    ):
        """
        初始化自适应提取器

        Args:
            threshold_method: 二值化方法 (otsu/adaptive)
            min_cell_area: 最小单元格面积
            max_cell_area: 最大单元格面积
        """
        self.threshold_method = threshold_method
        self.min_cell_area = min_cell_area
        self.max_cell_area = max_cell_area

    def extract(
        self,
        table_image: np.ndarray,
        structure: Dict,
    ) -> List[Dict]:
        """
        提取单元格

        Args:
            table_image: 表格图像
            structure: 表格结构信息

        Returns:
            单元格列表
        """
        # 基础提取
        extractor = CellExtractor()
        cells = extractor.extract(table_image, structure)

        # 自适应后处理
        processed_cells = []
        for cell in cells:
            # 检查单元格质量
            if self._is_valid_cell(cell["image"]):
                # 增强单元格图像
                cell["image"] = self._enhance_cell(cell["image"])
                processed_cells.append(cell)

        return processed_cells

    def _is_valid_cell(self, cell_image: np.ndarray) -> bool:
        """
        验证单元格是否有效

        Args:
            cell_image: 单元格图像

        Returns:
            是否有效
        """
        if cell_image.size == 0:
            return False

        h, w = cell_image.shape[:2]
        area = h * w

        if area < self.min_cell_area or area > self.max_cell_area:
            return False

        return True

    def _enhance_cell(self, cell_image: np.ndarray) -> np.ndarray:
        """
        增强单元格图像

        Args:
            cell_image: 原始单元格图像

        Returns:
            增强后的图像
        """
        if cell_image.size == 0:
            return cell_image

        # 转灰度
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()

        # 对比度增强
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 转回原格式
        if len(cell_image.shape) == 3:
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        return enhanced


class CellMerger:
    """
    单元格合并器

    处理合并单元格的情况。
    """

    def __init__(self, overlap_threshold: float = 0.5):
        """
        初始化合并器

        Args:
            overlap_threshold: 重叠阈值
        """
        self.overlap_threshold = overlap_threshold

    def merge_cells(self, cells: List[Dict]) -> List[Dict]:
        """
        合并单元格

        Args:
            cells: 单元格列表

        Returns:
            合并后的单元格列表
        """
        if not cells:
            return []

        # 按行分组
        rows = {}
        for cell in cells:
            row = cell["row"]
            if row not in rows:
                rows[row] = []
            rows[row].append(cell)

        # 处理每一行
        merged_cells = []
        for row in sorted(rows.keys()):
            row_cells = sorted(rows[row], key=lambda c: c["col"])

            # 检测合并单元格
            i = 0
            while i < len(row_cells):
                current = row_cells[i]
                merge_start = i

                # 查找需要合并的单元格
                while i + 1 < len(row_cells):
                    next_cell = row_cells[i + 1]
                    if self._should_merge(current, next_cell):
                        i += 1
                    else:
                        break

                # 如果有合并
                if i > merge_start:
                    merged = self._merge_range(row_cells[merge_start:i + 1])
                    merged_cells.append(merged)
                else:
                    merged_cells.append(current)

                i += 1

        return merged_cells

    def _should_merge(self, cell1: Dict, cell2: Dict) -> bool:
        """
        判断两个单元格是否应该合并

        Args:
            cell1: 单元格 1
            cell2: 单元格 2

        Returns:
            是否应该合并
        """
        # 检查是否在同一行
        if cell1["row"] != cell2["row"]:
            return False

        # 检查边界是否相邻
        bbox1 = cell1["bbox"]
        bbox2 = cell2["bbox"]

        # 水平相邻
        if abs(bbox1[2] - bbox2[0]) < 5:
            return True

        return False

    def _merge_range(self, cells: List[Dict]) -> Dict:
        """
        合并一系列单元格

        Args:
            cells: 要合并的单元格列表

        Returns:
            合并后的单元格
        """
        # 获取合并后的边界框
        x1 = min(cell["bbox"][0] for cell in cells)
        y1 = min(cell["bbox"][1] for cell in cells)
        x2 = max(cell["bbox"][2] for cell in cells)
        y2 = max(cell["bbox"][3] for cell in cells)

        # 合并图像
        images = [cell["image"] for cell in cells if cell["image"] is not None]
        merged_image = None

        if images:
            # 水平拼接
            try:
                merged_image = np.concatenate(images, axis=1)
            except Exception:
                merged_image = images[0]

        return {
            "row": cells[0]["row"],
            "col": cells[0]["col"],
            "col_span": len(cells),
            "bbox": [x1, y1, x2, y2],
            "image": merged_image,
            "content": None,
        }


class CellCoordinateMapper:
    """
    单元格坐标映射器

    在不同分辨率之间映射单元格坐标。
    """

    def __init__(self):
        """初始化坐标映射器"""
        pass

    def map_coordinates(
        self,
        cells: List[Dict],
        source_shape: Tuple[int, int],
        target_shape: Tuple[int, int],
    ) -> List[Dict]:
        """
        映射坐标

        Args:
            cells: 单元格列表
            source_shape: 源图像形状 (h, w)
            target_shape: 目标图像形状 (h, w)

        Returns:
            映射后的单元格列表
        """
        src_h, src_w = source_shape
        tgt_h, tgt_w = target_shape

        # 计算缩放比例
        scale_x = tgt_w / src_w
        scale_y = tgt_h / src_h

        mapped_cells = []
        for cell in cells:
            bbox = cell["bbox"]

            # 缩放坐标
            new_bbox = [
                int(bbox[0] * scale_x),
                int(bbox[1] * scale_y),
                int(bbox[2] * scale_x),
                int(bbox[3] * scale_y),
            ]

            # 创建新单元格
            new_cell = cell.copy()
            new_cell["bbox"] = new_bbox
            new_cell["original_bbox"] = bbox

            mapped_cells.append(new_cell)

        return mapped_cells

    def normalize_coordinates(
        self,
        cells: List[Dict],
        image_shape: Tuple[int, int],
    ) -> List[Dict]:
        """
        归一化坐标到 [0, 1] 范围

        Args:
            cells: 单元格列表
            image_shape: 图像形状 (h, w)

        Returns:
            归一化后的单元格列表
        """
        h, w = image_shape

        normalized_cells = []
        for cell in cells:
            bbox = cell["bbox"]

            # 归一化
            normalized_bbox = [
                bbox[0] / w,
                bbox[1] / h,
                bbox[2] / w,
                bbox[3] / h,
            ]

            new_cell = cell.copy()
            new_cell["normalized_bbox"] = normalized_bbox

            normalized_cells.append(new_cell)

        return normalized_cells
