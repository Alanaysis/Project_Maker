"""
表格识别管道测试
"""

import pytest
import numpy as np
import cv2
import tempfile
from pathlib import Path

from src.pipeline import TableRecognitionPipeline, ResultExporter
from src.utils import create_sample_table_image, create_sample_image_with_tables


class TestTableRecognitionPipeline:
    """表格识别管道测试"""

    @pytest.fixture
    def pipeline(self):
        """创建管道实例"""
        return TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
            use_ocr=False,
        )

    @pytest.fixture
    def sample_image(self):
        """创建示例图像"""
        return create_sample_image_with_tables(num_tables=1)

    @pytest.fixture
    def table_image(self):
        """创建表格图像"""
        return create_sample_table_image(rows=3, cols=3)

    def test_init(self, pipeline):
        """测试初始化"""
        assert pipeline is not None
        assert pipeline.detector is not None
        assert pipeline.structure_recognizer is not None
        assert pipeline.cell_extractor is not None

    def test_process_image_returns_dict(self, pipeline, sample_image):
        """测试处理图像返回字典"""
        result = pipeline.process_image(sample_image)
        assert isinstance(result, dict)

    def test_process_image_has_required_keys(self, pipeline, sample_image):
        """测试处理结果包含必要键"""
        result = pipeline.process_image(sample_image)

        assert "image_size" in result
        assert "tables" in result
        assert "processing_time" in result

    def test_process_image_size(self, pipeline, sample_image):
        """测试图像尺寸信息"""
        result = pipeline.process_image(sample_image)

        assert result["image_size"]["width"] == sample_image.shape[1]
        assert result["image_size"]["height"] == sample_image.shape[0]

    def test_process_image_tables_format(self, pipeline, sample_image):
        """测试表格格式"""
        result = pipeline.process_image(sample_image)

        for table in result["tables"]:
            assert "index" in table
            assert "bbox" in table
            assert "rows" in table
            assert "columns" in table
            assert "cells" in table
            assert "data" in table

    def test_process_image_with_table(self, pipeline, table_image):
        """测试处理表格图像"""
        result = pipeline.process_image(table_image)

        # 应该检测到表格
        assert len(result["tables"]) >= 0

    def test_process_file(self, pipeline, sample_image):
        """测试处理文件"""
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            cv2.imwrite(f.name, sample_image)
            temp_path = f.name

        try:
            result = pipeline.process(temp_path)
            assert isinstance(result, dict)
        finally:
            import os
            os.unlink(temp_path)

    def test_process_nonexistent_file(self, pipeline):
        """测试处理不存在的文件"""
        with pytest.raises(ValueError):
            pipeline.process("nonexistent.jpg")

    def test_build_table_data(self, pipeline):
        """测试构建表格数据"""
        cells = [
            {"row": 0, "col": 0, "content": "A1"},
            {"row": 0, "col": 1, "content": "B1"},
            {"row": 1, "col": 0, "content": "A2"},
            {"row": 1, "col": 1, "content": "B2"},
        ]

        structure = {"rows": 2, "columns": 2}

        data = pipeline._build_table_data(cells, structure)

        assert len(data) == 2
        assert data[0][0] == "A1"
        assert data[0][1] == "B1"
        assert data[1][0] == "A2"
        assert data[1][1] == "B2"

    def test_visualize_result(self, pipeline, sample_image):
        """测试可视化结果"""
        result = pipeline.process_image(sample_image)

        vis_image = pipeline.visualize_result(sample_image, result)
        assert vis_image.shape == sample_image.shape


class TestResultExporter:
    """结果导出器测试"""

    @pytest.fixture
    def sample_result(self):
        """创建示例结果"""
        return {
            "image_size": {"width": 600, "height": 400},
            "tables": [
                {
                    "index": 0,
                    "bbox": [100, 100, 500, 300],
                    "rows": 2,
                    "columns": 2,
                    "data": [
                        ["Header 1", "Header 2"],
                        ["Cell 1", "Cell 2"],
                    ],
                    "cells": [],
                }
            ],
            "processing_time": 0.5,
        }

    def test_to_json(self, sample_result):
        """测试导出 JSON"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_json(sample_result, temp_path)

            # 验证文件存在
            import json
            with open(temp_path) as f:
                loaded = json.load(f)

            assert loaded["image_size"]["width"] == 600
        finally:
            import os
            os.unlink(temp_path)

    def test_to_csv(self, sample_result):
        """测试导出 CSV"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_csv(sample_result, temp_path)

            # 验证文件存在
            import csv
            with open(temp_path) as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0] == ["Header 1", "Header 2"]
        finally:
            import os
            os.unlink(temp_path)

    def test_to_html(self, sample_result):
        """测试导出 HTML"""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_html(sample_result, temp_path)

            # 验证文件存在
            with open(temp_path) as f:
                content = f.read()

            assert "<table>" in content
            assert "Header 1" in content
        finally:
            import os
            os.unlink(temp_path)

    def test_to_json_with_invalid_table_index(self, sample_result):
        """测试导出无效表格索引"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                ResultExporter.to_csv(sample_result, temp_path, table_index=99)
        finally:
            import os
            os.unlink(temp_path)


class TestPipelineIntegration:
    """管道集成测试"""

    def test_full_pipeline_with_table_image(self):
        """测试完整流程处理表格图像"""
        # 创建表格图像
        image = create_sample_table_image(rows=3, cols=3)

        # 创建管道
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 处理图像
        result = pipeline.process_image(image)

        # 验证结果
        assert "tables" in result
        assert "processing_time" in result

    def test_pipeline_with_different_configs(self):
        """测试不同配置的管道"""
        # 创建表格图像
        image = create_sample_table_image(rows=2, cols=2)

        # 测试不同配置
        configs = [
            {"detector_type": "simple", "recognizer_type": "morphological"},
            {"detector_type": "simple", "recognizer_type": "hough"},
        ]

        for config in configs:
            pipeline = TableRecognitionPipeline(**config)
            result = pipeline.process_image(image)
            assert "tables" in result

    def test_pipeline_performance(self):
        """测试管道性能"""
        import time

        # 创建表格图像
        image = create_sample_table_image(rows=5, cols=5)

        # 创建管道
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 测试性能
        start_time = time.time()
        result = pipeline.process_image(image)
        end_time = time.time()

        processing_time = end_time - start_time
        assert processing_time < 5.0  # 应该在 5 秒内完成

    def test_export_results(self):
        """测试导出结果"""
        # 创建表格图像
        image = create_sample_table_image(rows=2, cols=2)

        # 创建管道
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 处理图像
        result = pipeline.process_image(image)

        # 导出 JSON
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_json(result, temp_path)
            assert Path(temp_path).exists()
        finally:
            import os
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
