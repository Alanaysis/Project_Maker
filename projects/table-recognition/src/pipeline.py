"""
表格识别完整流程

实现从图像输入到数据输出的完整处理管道。
"""

import logging
import json
import csv
from typing import List, Dict, Optional, Union
from pathlib import Path
import numpy as np
import cv2

from .detector import TableDetector, SimpleTableDetector
from .structure import StructureRecognizer, LineBasedStructureRecognizer
from .extractor import CellExtractor, CellMerger
from .recognizer import TextRecognizer

logger = logging.getLogger(__name__)


class TableRecognitionPipeline:
    """
    表格识别完整流程

    整合表格检测、结构识别、单元格提取和文字识别。
    """

    def __init__(
        self,
        detector_type: str = "simple",
        recognizer_type: str = "morphological",
        use_ocr: bool = False,
        ocr_engine: str = "easyocr",
        config: Optional[Dict] = None,
    ):
        """
        初始化处理管道

        Args:
            detector_type: 检测器类型 (simple/deep)
            recognizer_type: 结构识别器类型 (morphological/hough)
            use_ocr: 是否使用 OCR
            ocr_engine: OCR 引擎
            config: 配置参数
        """
        self.config = config or {}

        # 初始化检测器
        if detector_type == "simple":
            self.detector = SimpleTableDetector()
        else:
            self.detector = TableDetector()

        # 初始化结构识别器
        if recognizer_type == "morphological":
            self.structure_recognizer = StructureRecognizer()
        else:
            self.structure_recognizer = LineBasedStructureRecognizer()

        # 初始化单元格提取器
        self.cell_extractor = CellExtractor()
        self.cell_merger = CellMerger()

        # 初始化文字识别器（可选）
        self.text_recognizer = None
        if use_ocr:
            self.text_recognizer = TextRecognizer(engine=ocr_engine)

        logger.info("表格识别管道初始化完成")

    def process(self, image_path: Union[str, Path]) -> Dict:
        """
        处理单个图像

        Args:
            image_path: 图像路径

        Returns:
            处理结果
        """
        # 读取图像
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")

        return self.process_image(image)

    def process_image(self, image: np.ndarray) -> Dict:
        """
        处理图像

        Args:
            image: 输入图像 (BGR 格式)

        Returns:
            处理结果，包含:
                - tables: 检测到的表格列表
                - image_size: 图像尺寸
                - processing_time: 处理时间
        """
        import time
        start_time = time.time()

        # 1. 表格检测
        logger.info("开始表格检测...")
        detections = self.detector.detect(image)
        logger.info(f"检测到 {len(detections)} 个表格")

        # 2. 处理每个表格
        tables = []
        for i, detection in enumerate(detections):
            logger.info(f"处理表格 {i + 1}/{len(detections)}...")

            # 裁剪表格区域
            bbox = detection["bbox"]
            x1, y1, x2, y2 = bbox
            table_image = image[y1:y2, x1:x2]

            # 3. 结构识别
            structure = self.structure_recognizer.recognize(table_image)
            logger.info(f"识别到 {structure['rows']} 行 x {structure['columns']} 列")

            # 4. 单元格提取
            cells = self.cell_extractor.extract(table_image, structure)

            # 5. 合并单元格（处理合并单元格情况）
            cells = self.cell_merger.merge_cells(cells)

            # 6. 文字识别（可选）
            if self.text_recognizer:
                for cell in cells:
                    if cell["image"] is not None:
                        cell["content"] = self.text_recognizer.recognize(cell["image"])

            # 7. 转换坐标到原图
            for cell in cells:
                cell["original_bbox"] = [
                    cell["bbox"][0] + x1,
                    cell["bbox"][1] + y1,
                    cell["bbox"][2] + x1,
                    cell["bbox"][3] + y1,
                ]

            # 构建表格数据
            table_data = self._build_table_data(cells, structure)
            table = {
                "index": i,
                "bbox": bbox,
                "confidence": detection.get("confidence", 1.0),
                "rows": structure["rows"],
                "columns": structure["columns"],
                "cells": cells,
                "data": table_data,
            }

            tables.append(table)

        # 计算处理时间
        processing_time = time.time() - start_time

        result = {
            "image_size": {
                "width": image.shape[1],
                "height": image.shape[0],
            },
            "tables": tables,
            "processing_time": processing_time,
        }

        logger.info(f"处理完成，耗时 {processing_time:.2f} 秒")
        return result

    def _build_table_data(self, cells: List[Dict], structure: Dict) -> List[List[str]]:
        """
        构建表格数据矩阵

        Args:
            cells: 单元格列表
            structure: 表格结构

        Returns:
            二维数据数组
        """
        rows = structure["rows"]
        cols = structure["columns"]

        # 初始化空表格
        table_data = [["" for _ in range(cols)] for _ in range(rows)]

        # 填充数据
        for cell in cells:
            row = cell["row"]
            col = cell["col"]

            if 0 <= row < rows and 0 <= col < cols:
                content = cell.get("content", "")
                if content:
                    table_data[row][col] = content

        return table_data

    def visualize_result(
        self,
        image: np.ndarray,
        result: Dict,
        show_cells: bool = True,
        show_text: bool = False,
    ) -> np.ndarray:
        """
        可视化处理结果

        Args:
            image: 原始图像
            result: 处理结果
            show_cells: 是否显示单元格
            show_text: 是否显示识别的文字

        Returns:
            可视化图像
        """
        vis_image = image.copy()

        for table in result["tables"]:
            # 绘制表格边界框
            bbox = table["bbox"]
            cv2.rectangle(
                vis_image,
                (bbox[0], bbox[1]),
                (bbox[2], bbox[3]),
                (0, 255, 0),
                2,
            )

            # 添加表格标签
            label = f"Table {table['index'] + 1}: {table['rows']}x{table['columns']}"
            cv2.putText(
                vis_image,
                label,
                (bbox[0], bbox[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            if show_cells:
                # 绘制单元格
                for cell in table["cells"]:
                    if "original_bbox" in cell:
                        cell_bbox = cell["original_bbox"]
                        cv2.rectangle(
                            vis_image,
                            (cell_bbox[0], cell_bbox[1]),
                            (cell_bbox[2], cell_bbox[3]),
                            (255, 0, 0),
                            1,
                        )

                        if show_text and cell.get("content"):
                            cv2.putText(
                                vis_image,
                                cell["content"][:10],
                                (cell_bbox[0] + 2, cell_bbox[1] + 15),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.3,
                                (0, 0, 255),
                                1,
                            )

        return vis_image


class ResultExporter:
    """
    结果导出器

    将处理结果导出为各种格式。
    """

    @staticmethod
    def to_json(result: Dict, output_path: Union[str, Path], indent: int = 2):
        """
        导出为 JSON 格式

        Args:
            result: 处理结果
            output_path: 输出路径
            indent: 缩进空格数
        """
        # 转换 numpy 类型
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # 清理结果
        clean_result = json.loads(json.dumps(result, default=convert))

        # 移除图像数据
        for table in clean_result.get("tables", []):
            for cell in table.get("cells", []):
                if "image" in cell:
                    del cell["image"]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(clean_result, f, ensure_ascii=False, indent=indent)

        logger.info(f"结果已导出到 {output_path}")

    @staticmethod
    def to_csv(result: Dict, output_path: Union[str, Path], table_index: int = 0):
        """
        导出为 CSV 格式

        Args:
            result: 处理结果
            output_path: 输出路径
            table_index: 表格索引
        """
        tables = result.get("tables", [])
        if table_index >= len(tables):
            raise ValueError(f"表格索引 {table_index} 超出范围")

        table = tables[table_index]
        data = table.get("data", [])

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)

        logger.info(f"表格 {table_index} 已导出到 {output_path}")

    @staticmethod
    def to_html(result: Dict, output_path: Union[str, Path], table_index: int = 0):
        """
        导出为 HTML 格式

        Args:
            result: 处理结果
            output_path: 输出路径
            table_index: 表格索引
        """
        tables = result.get("tables", [])
        if table_index >= len(tables):
            raise ValueError(f"表格索引 {table_index} 超出范围")

        table = tables[table_index]
        data = table.get("data", [])

        # 生成 HTML
        html = "<!DOCTYPE html>\n<html>\n<head>\n"
        html += "<meta charset='UTF-8'>\n"
        html += "<title>表格识别结果</title>\n"
        html += "<style>\n"
        html += "table { border-collapse: collapse; width: 100%; }\n"
        html += "th, td { border: 1px solid black; padding: 8px; text-align: left; }\n"
        html += "th { background-color: #f2f2f2; }\n"
        html += "</style>\n</head>\n<body>\n"
        html += "<h1>表格识别结果</h1>\n"

        # 表格信息
        html += f"<p>表格尺寸: {table['rows']} 行 x {table['columns']} 列</p>\n"

        # 表格内容
        html += "<table>\n"
        for i, row in enumerate(data):
            html += "<tr>\n"
            for cell in row:
                if i == 0:
                    html += f"<th>{cell}</th>\n"
                else:
                    html += f"<td>{cell}</td>\n"
            html += "</tr>\n"
        html += "</table>\n"

        html += "</body>\n</html>"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"HTML 已导出到 {output_path}")

    @staticmethod
    def to_excel(result: Dict, output_path: Union[str, Path]):
        """
        导出为 Excel 格式

        Args:
            result: 处理结果
            output_path: 输出路径
        """
        try:
            import pandas as pd

            tables = result.get("tables", [])

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for i, table in enumerate(tables):
                    data = table.get("data", [])
                    if data:
                        df = pd.DataFrame(data[1:], columns=data[0] if data else [])
                        df.to_excel(writer, sheet_name=f"Table_{i}", index=False)

            logger.info(f"Excel 已导出到 {output_path}")

        except ImportError:
            logger.warning("pandas 或 openpyxl 未安装，无法导出 Excel")
            # 回退到 CSV
            csv_path = output_path.with_suffix(".csv")
            ResultExporter.to_csv(result, csv_path)
