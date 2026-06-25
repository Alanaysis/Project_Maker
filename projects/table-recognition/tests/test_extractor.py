"""
单元格提取器测试
"""

import pytest
import numpy as np
import cv2

from src.extractor import CellExtractor, CellMerger, CellCoordinateMapper
from src.structure import StructureRecognizer
from src.utils import create_sample_table_image


class TestCellExtractor:
    """单元格提取器测试"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return CellExtractor()

    @pytest.fixture
    def table_image(self):
        """创建表格图像"""
        return create_sample_table_image(rows=3, cols=3)

    @pytest.fixture
    def structure(self, table_image):
        """创建表格结构"""
        recognizer = StructureRecognizer()
        return recognizer.recognize(table_image)

    def test_init(self, extractor):
        """测试初始化"""
        assert extractor is not None
        assert extractor.padding == 2

    def test_extract_returns_list(self, extractor, table_image, structure):
        """测试提取返回列表"""
        cells = extractor.extract(table_image, structure)
        assert isinstance(cells, list)

    def test_extract_cell_format(self, extractor, table_image, structure):
        """测试单元格格式"""
        cells = extractor.extract(table_image, structure)

        for cell in cells:
            assert "row" in cell
            assert "col" in cell
            assert "bbox" in cell
            assert "image" in cell

    def test_extract_with_valid_structure(self, extractor, table_image):
        """测试有效结构提取"""
        structure = {
            "rows": 2,
            "columns": 2,
            "horizontal_lines": [0, 50, 100],
            "vertical_lines": [0, 75, 150],
            "cells": [
                {"row": 0, "col": 0, "bbox": [0, 0, 75, 50]},
                {"row": 0, "col": 1, "bbox": [75, 0, 150, 50]},
                {"row": 1, "col": 0, "bbox": [0, 50, 75, 100]},
                {"row": 1, "col": 1, "bbox": [75, 50, 150, 100]},
            ],
        }

        cells = extractor.extract(table_image, structure)
        assert len(cells) == 4

    def test_extract_with_empty_structure(self, extractor, table_image):
        """测试空结构提取"""
        structure = {
            "rows": 0,
            "columns": 0,
            "horizontal_lines": [],
            "vertical_lines": [],
            "cells": [],
        }

        cells = extractor.extract(table_image, structure)
        assert len(cells) == 0

    def test_add_padding(self, extractor):
        """测试添加内边距"""
        bbox = [10, 10, 100, 100]
        image_shape = (200, 200, 3)

        padded = extractor._add_padding(bbox, image_shape)
        assert padded[0] > bbox[0]
        assert padded[1] > bbox[1]
        assert padded[2] < bbox[2]
        assert padded[3] < bbox[3]

    def test_remove_border(self, extractor):
        """测试移除边框"""
        # 创建带边框的图像
        cell_image = np.zeros((50, 50, 3), dtype=np.uint8)
        cell_image[:, :] = [255, 255, 255]

        # 添加边框
        cv2.rectangle(cell_image, (0, 0), (49, 49), (0, 0, 0), 2)

        result = extractor._remove_border(cell_image)
        assert result.shape[0] < cell_image.shape[0]
        assert result.shape[1] < cell_image.shape[1]


class TestCellMerger:
    """单元格合并器测试"""

    @pytest.fixture
    def merger(self):
        """创建合并器实例"""
        return CellMerger()

    def test_init(self, merger):
        """测试初始化"""
        assert merger is not None

    def test_merge_cells_with_empty_list(self, merger):
        """测试空列表合并"""
        result = merger.merge_cells([])
        assert result == []

    def test_merge_cells_with_single_cell(self, merger):
        """测试单个单元格合并"""
        cells = [
            {"row": 0, "col": 0, "bbox": [0, 0, 100, 50], "image": np.zeros((50, 100))}
        ]

        result = merger.merge_cells(cells)
        assert len(result) == 1

    def test_merge_cells_with_adjacent_cells(self, merger):
        """测试相邻单元格合并"""
        cells = [
            {"row": 0, "col": 0, "bbox": [0, 0, 50, 50], "image": np.zeros((50, 50))},
            {"row": 0, "col": 1, "bbox": [50, 0, 100, 50], "image": np.zeros((50, 50))},
        ]

        result = merger.merge_cells(cells)
        assert len(result) == 1
        assert result[0]["col_span"] == 2

    def test_merge_cells_with_non_adjacent_cells(self, merger):
        """测试非相邻单元格合并"""
        cells = [
            {"row": 0, "col": 0, "bbox": [0, 0, 50, 50], "image": np.zeros((50, 50))},
            {"row": 0, "col": 1, "bbox": [100, 0, 150, 50], "image": np.zeros((50, 50))},
        ]

        result = merger.merge_cells(cells)
        assert len(result) == 2

    def test_should_merge(self, merger):
        """测试合并判断"""
        cell1 = {"row": 0, "col": 0, "bbox": [0, 0, 50, 50]}
        cell2 = {"row": 0, "col": 1, "bbox": [50, 0, 100, 50]}

        assert merger._should_merge(cell1, cell2) is True

    def test_should_not_merge_different_rows(self, merger):
        """测试不同行不合并"""
        cell1 = {"row": 0, "col": 0, "bbox": [0, 0, 50, 50]}
        cell2 = {"row": 1, "col": 0, "bbox": [0, 50, 50, 100]}

        assert merger._should_merge(cell1, cell2) is False

    def test_merge_range(self, merger):
        """测试范围合并"""
        cells = [
            {"row": 0, "col": 0, "bbox": [0, 0, 50, 50], "image": np.zeros((50, 50))},
            {"row": 0, "col": 1, "bbox": [50, 0, 100, 50], "image": np.zeros((50, 50))},
        ]

        result = merger._merge_range(cells)
        assert result["col_span"] == 2
        assert result["bbox"] == [0, 0, 100, 50]


class TestCellCoordinateMapper:
    """单元格坐标映射器测试"""

    @pytest.fixture
    def mapper(self):
        """创建映射器实例"""
        return CellCoordinateMapper()

    def test_map_coordinates(self, mapper):
        """测试坐标映射"""
        cells = [
            {"row": 0, "col": 0, "bbox": [10, 10, 100, 50]},
        ]

        source_shape = (100, 200)
        target_shape = (200, 400)

        result = mapper.map_coordinates(cells, source_shape, target_shape)

        assert len(result) == 1
        assert result[0]["bbox"][0] == 20  # 10 * 2
        assert result[0]["bbox"][1] == 20  # 10 * 2

    def test_normalize_coordinates(self, mapper):
        """测试坐标归一化"""
        cells = [
            {"row": 0, "col": 0, "bbox": [10, 10, 100, 50]},
        ]

        image_shape = (100, 200)

        result = mapper.normalize_coordinates(cells, image_shape)

        assert len(result) == 1
        assert "normalized_bbox" in result[0]

        # 检查归一化值在 [0, 1] 范围内
        normalized = result[0]["normalized_bbox"]
        assert all(0 <= v <= 1 for v in normalized)


class TestExtractorIntegration:
    """提取器集成测试"""

    def test_full_extraction_pipeline(self):
        """测试完整提取流程"""
        # 创建表格图像
        image = create_sample_table_image(rows=2, cols=2)

        # 识别结构
        recognizer = StructureRecognizer()
        structure = recognizer.recognize(image)

        # 提取单元格
        extractor = CellExtractor()
        cells = extractor.extract(image, structure)

        # 验证结果
        assert len(cells) > 0
        for cell in cells:
            assert cell["image"] is not None
            assert cell["image"].size > 0

    def test_extraction_with_merge(self):
        """测试带合并的提取"""
        # 创建表格图像
        image = create_sample_table_image(rows=2, cols=3)

        # 识别结构
        recognizer = StructureRecognizer()
        structure = recognizer.recognize(image)

        # 提取单元格
        extractor = CellExtractor()
        cells = extractor.extract(image, structure)

        # 合并单元格
        merger = CellMerger()
        merged_cells = merger.merge_cells(cells)

        # 验证结果
        assert len(merged_cells) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
