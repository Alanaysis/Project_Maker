"""
表格结构识别测试
"""

import pytest
import numpy as np
import cv2

from src.structure import StructureRecognizer, LineBasedStructureRecognizer
from src.utils import create_sample_table_image


class TestStructureRecognizer:
    """结构识别器测试"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return StructureRecognizer()

    @pytest.fixture
    def table_image(self):
        """创建表格图像"""
        return create_sample_table_image(rows=3, cols=3)

    def test_init(self, recognizer):
        """测试初始化"""
        assert recognizer is not None
        assert recognizer.line_threshold == 50

    def test_recognize_returns_dict(self, recognizer, table_image):
        """测试识别返回字典"""
        result = recognizer.recognize(table_image)
        assert isinstance(result, dict)

    def test_recognize_has_required_keys(self, recognizer, table_image):
        """测试识别结果包含必要键"""
        result = recognizer.recognize(table_image)

        assert "rows" in result
        assert "columns" in result
        assert "horizontal_lines" in result
        assert "vertical_lines" in result
        assert "cells" in result

    def test_recognize_table_structure(self, recognizer, table_image):
        """测试识别表格结构"""
        result = recognizer.recognize(table_image)

        # 检查行列数
        assert result["rows"] >= 0
        assert result["columns"] >= 0

        # 检查线条
        assert isinstance(result["horizontal_lines"], list)
        assert isinstance(result["vertical_lines"], list)

    def test_recognize_cells_format(self, recognizer, table_image):
        """测试单元格格式"""
        result = recognizer.recognize(table_image)

        for cell in result["cells"]:
            assert "row" in cell
            assert "col" in cell
            assert "bbox" in cell

            # 检查边界框格式
            bbox = cell["bbox"]
            assert len(bbox) == 4
            assert bbox[0] < bbox[2]  # x1 < x2
            assert bbox[1] < bbox[3]  # y1 < y2

    def test_recognize_with_empty_image(self, recognizer):
        """测试空图像识别"""
        empty_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = recognizer.recognize(empty_image)
        assert isinstance(result, dict)

    def test_preprocess(self, recognizer, table_image):
        """测试预处理"""
        binary = recognizer._preprocess(table_image)
        assert binary is not None
        assert len(binary.shape) == 2  # 灰度图

    def test_detect_horizontal_lines(self, recognizer, table_image):
        """测试水平线检测"""
        binary = recognizer._preprocess(table_image)
        lines = recognizer._detect_horizontal_lines(binary)
        assert isinstance(lines, list)

    def test_detect_vertical_lines(self, recognizer, table_image):
        """测试垂直线检测"""
        binary = recognizer._preprocess(table_image)
        lines = recognizer._detect_vertical_lines(binary)
        assert isinstance(lines, list)

    def test_merge_lines(self, recognizer):
        """测试线条合并"""
        # 测试合并相近的线
        lines = [10, 12, 15, 100, 102]
        merged = recognizer._merge_lines(lines)
        assert len(merged) < len(lines)

    def test_generate_cells(self, recognizer):
        """测试单元格生成"""
        horizontal = [0, 100, 200]
        vertical = [0, 150, 300]

        cells = recognizer._generate_cells(horizontal, vertical)
        assert len(cells) == 4  # 2x2 表格

        for cell in cells:
            assert "row" in cell
            assert "col" in cell
            assert "bbox" in cell


class TestLineBasedStructureRecognizer:
    """基于线条的结构识别器测试"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return LineBasedStructureRecognizer()

    @pytest.fixture
    def table_image(self):
        """创建表格图像"""
        return create_sample_table_image(rows=3, cols=3)

    def test_init(self, recognizer):
        """测试初始化"""
        assert recognizer is not None
        assert recognizer.hough_threshold == 100

    def test_recognize_returns_dict(self, recognizer, table_image):
        """测试识别返回字典"""
        result = recognizer.recognize(table_image)
        assert isinstance(result, dict)

    def test_recognize_has_required_keys(self, recognizer, table_image):
        """测试识别结果包含必要键"""
        result = recognizer.recognize(table_image)

        assert "rows" in result
        assert "columns" in result
        assert "horizontal_lines" in result
        assert "vertical_lines" in result
        assert "cells" in result

    def test_merge_close_lines(self, recognizer):
        """测试合并相近线条"""
        lines = [10, 12, 15, 100, 102, 200]
        merged = recognizer._merge_close_lines(lines, threshold=10)
        assert len(merged) < len(lines)

    def test_generate_cells(self, recognizer):
        """测试单元格生成"""
        horizontal = [0, 100, 200]
        vertical = [0, 150, 300]

        cells = recognizer._generate_cells(horizontal, vertical)
        assert len(cells) == 4


class TestStructureRecognizerIntegration:
    """结构识别器集成测试"""

    def test_recognize_real_table(self):
        """测试识别真实表格"""
        # 创建带有明显线条的表格
        image = np.ones((300, 400, 3), dtype=np.uint8) * 255

        # 绘制表格边框
        cv2.rectangle(image, (50, 50), (350, 250), (0, 0, 0), 2)

        # 绘制水平线
        cv2.line(image, (50, 150), (350, 150), (0, 0, 0), 2)

        # 绘制垂直线
        cv2.line(image, (200, 50), (200, 250), (0, 0, 0), 2)

        # 识别
        recognizer = StructureRecognizer()
        result = recognizer.recognize(image)

        # 验证结果
        assert result["rows"] >= 1
        assert result["columns"] >= 1

    def test_compare_recognizers(self):
        """测试比较不同识别器"""
        # 创建表格图像
        image = create_sample_table_image(rows=2, cols=2)

        # 使用两种识别器
        recognizer1 = StructureRecognizer()
        recognizer2 = LineBasedStructureRecognizer()

        result1 = recognizer1.recognize(image)
        result2 = recognizer2.recognize(image)

        # 两者都应该返回有效结果
        assert "rows" in result1
        assert "rows" in result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
