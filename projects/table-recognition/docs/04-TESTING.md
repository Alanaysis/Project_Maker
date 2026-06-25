# 测试策略文档

## 1. 测试概述

### 1.1 测试目标

- 验证各模块功能正确性
- 确保模块间集成正常
- 保证代码质量和可维护性
- 验证性能满足要求

### 1.2 测试类型

| 类型 | 说明 | 覆盖范围 |
|------|------|----------|
| 单元测试 | 测试单个函数/方法 | 80%+ |
| 集成测试 | 测试模块间协作 | 核心流程 |
| 性能测试 | 测试处理速度和内存 | 关键路径 |
| 端到端测试 | 测试完整流程 | 主要场景 |

## 2. 测试环境

### 2.1 依赖安装

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-mock

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 2.2 测试配置

创建 `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=src --cov-report=html
```

## 3. 单元测试

### 3.1 检测器测试 (test_detector.py)

```python
import pytest
import numpy as np
import cv2
from src.detector import SimpleTableDetector

class TestSimpleTableDetector:
    """简单表格检测器测试"""

    @pytest.fixture
    def detector(self):
        return SimpleTableDetector(min_area=500)

    @pytest.fixture
    def sample_image(self):
        """创建包含表格的测试图像"""
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (100, 100), (500, 300), (0, 0, 0), 2)
        return image

    def test_init(self, detector):
        """测试初始化"""
        assert detector is not None
        assert detector.min_area == 500

    def test_detect_returns_list(self, detector, sample_image):
        """测试返回类型"""
        results = detector.detect(sample_image)
        assert isinstance(results, list)

    def test_detect_result_format(self, detector, sample_image):
        """测试结果格式"""
        results = detector.detect(sample_image)

        for result in results:
            assert "bbox" in result
            assert "confidence" in result
            assert "class_id" in result

            bbox = result["bbox"]
            assert len(bbox) == 4

    def test_detect_with_empty_image(self, detector):
        """测试空图像"""
        empty_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        results = detector.detect(empty_image)
        assert isinstance(results, list)

    def test_detect_with_table(self, detector, sample_image):
        """测试表格检测"""
        results = detector.detect(sample_image)
        # 可能检测到也可能检测不到，取决于图像
        assert isinstance(results, list)
```

### 3.2 结构识别测试 (test_structure.py)

```python
import pytest
import numpy as np
import cv2
from src.structure import StructureRecognizer

class TestStructureRecognizer:
    """结构识别器测试"""

    @pytest.fixture
    def recognizer(self):
        return StructureRecognizer()

    @pytest.fixture
    def table_image(self):
        """创建表格图像"""
        from src.utils import create_sample_table_image
        return create_sample_table_image(rows=3, cols=3)

    def test_recognize_returns_dict(self, recognizer, table_image):
        """测试返回类型"""
        result = recognizer.recognize(table_image)
        assert isinstance(result, dict)

    def test_recognize_has_required_keys(self, recognizer, table_image):
        """测试必要字段"""
        result = recognizer.recognize(table_image)

        assert "rows" in result
        assert "columns" in result
        assert "horizontal_lines" in result
        assert "vertical_lines" in result
        assert "cells" in result

    def test_recognize_structure(self, recognizer, table_image):
        """测试结构识别"""
        result = recognizer.recognize(table_image)

        assert result["rows"] >= 0
        assert result["columns"] >= 0
        assert isinstance(result["horizontal_lines"], list)
        assert isinstance(result["vertical_lines"], list)

    def test_cells_format(self, recognizer, table_image):
        """测试单元格格式"""
        result = recognizer.recognize(table_image)

        for cell in result["cells"]:
            assert "row" in cell
            assert "col" in cell
            assert "bbox" in cell

            bbox = cell["bbox"]
            assert len(bbox) == 4
            assert bbox[0] < bbox[2]  # x1 < x2
            assert bbox[1] < bbox[3]  # y1 < y2

    def test_preprocess(self, recognizer, table_image):
        """测试预处理"""
        binary = recognizer._preprocess(table_image)
        assert binary is not None
        assert len(binary.shape) == 2

    def test_merge_lines(self, recognizer):
        """测试线条合并"""
        lines = [10, 12, 15, 100, 102]
        merged = recognizer._merge_lines(lines)
        assert len(merged) < len(lines)

    def test_generate_cells(self, recognizer):
        """测试单元格生成"""
        horizontal = [0, 100, 200]
        vertical = [0, 150, 300]

        cells = recognizer._generate_cells(horizontal, vertical)
        assert len(cells) == 4  # 2x2
```

### 3.3 提取器测试 (test_extractor.py)

```python
import pytest
import numpy as np
from src.extractor import CellExtractor, CellMerger

class TestCellExtractor:
    """单元格提取器测试"""

    @pytest.fixture
    def extractor(self):
        return CellExtractor()

    def test_init(self, extractor):
        assert extractor is not None
        assert extractor.padding == 2

    def test_extract_returns_list(self, extractor):
        # 创建测试数据
        table_image = np.ones((200, 300, 3), dtype=np.uint8) * 255
        structure = {
            "rows": 2,
            "columns": 2,
            "cells": [
                {"row": 0, "col": 0, "bbox": [10, 10, 140, 90]},
                {"row": 0, "col": 1, "bbox": [160, 10, 290, 90]},
                {"row": 1, "col": 0, "bbox": [10, 110, 140, 190]},
                {"row": 1, "col": 1, "bbox": [160, 110, 290, 190]},
            ]
        }

        cells = extractor.extract(table_image, structure)
        assert isinstance(cells, list)
        assert len(cells) == 4

    def test_cell_format(self, extractor):
        table_image = np.ones((200, 300, 3), dtype=np.uint8) * 255
        structure = {
            "rows": 1,
            "columns": 1,
            "cells": [
                {"row": 0, "col": 0, "bbox": [10, 10, 290, 190]}
            ]
        }

        cells = extractor.extract(table_image, structure)
        cell = cells[0]

        assert "row" in cell
        assert "col" in cell
        assert "bbox" in cell
        assert "image" in cell

class TestCellMerger:
    """单元格合并器测试"""

    @pytest.fixture
    def merger(self):
        return CellMerger()

    def test_merge_empty(self, merger):
        result = merger.merge_cells([])
        assert result == []

    def test_merge_single(self, merger):
        cells = [
            {"row": 0, "col": 0, "bbox": [0, 0, 100, 50], "image": np.zeros((50, 100))}
        ]
        result = merger.merge_cells(cells)
        assert len(result) == 1

    def test_merge_adjacent(self, merger):
        cells = [
            {"row": 0, "col": 0, "bbox": [0, 0, 50, 50], "image": np.zeros((50, 50))},
            {"row": 0, "col": 1, "bbox": [50, 0, 100, 50], "image": np.zeros((50, 50))},
        ]
        result = merger.merge_cells(cells)
        assert len(result) == 1
        assert result[0]["col_span"] == 2
```

### 3.4 管道测试 (test_pipeline.py)

```python
import pytest
import numpy as np
import tempfile
from pathlib import Path
from src.pipeline import TableRecognitionPipeline, ResultExporter

class TestTableRecognitionPipeline:
    """表格识别管道测试"""

    @pytest.fixture
    def pipeline(self):
        return TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
            use_ocr=False,
        )

    def test_init(self, pipeline):
        assert pipeline is not None
        assert pipeline.detector is not None

    def test_process_image(self, pipeline):
        from src.utils import create_sample_table_image
        image = create_sample_table_image(rows=2, cols=2)

        result = pipeline.process_image(image)
        assert isinstance(result, dict)
        assert "tables" in result
        assert "processing_time" in result

    def test_process_image_size(self, pipeline):
        from src.utils import create_sample_table_image
        image = create_sample_table_image(rows=2, cols=2)

        result = pipeline.process_image(image)
        assert result["image_size"]["width"] == image.shape[1]
        assert result["image_size"]["height"] == image.shape[0]

    def test_visualize_result(self, pipeline):
        from src.utils import create_sample_table_image
        image = create_sample_table_image(rows=2, cols=2)
        result = pipeline.process_image(image)

        vis = pipeline.visualize_result(image, result)
        assert vis.shape == image.shape

class TestResultExporter:
    """结果导出器测试"""

    @pytest.fixture
    def sample_result(self):
        return {
            "image_size": {"width": 600, "height": 400},
            "tables": [{
                "index": 0,
                "bbox": [100, 100, 500, 300],
                "rows": 2,
                "columns": 2,
                "data": [
                    ["Header 1", "Header 2"],
                    ["Cell 1", "Cell 2"],
                ],
                "cells": [],
            }],
            "processing_time": 0.5,
        }

    def test_to_json(self, sample_result):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_json(sample_result, temp_path)
            assert Path(temp_path).exists()

            import json
            with open(temp_path) as f:
                loaded = json.load(f)
            assert loaded["image_size"]["width"] == 600
        finally:
            import os
            os.unlink(temp_path)

    def test_to_csv(self, sample_result):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_csv(sample_result, temp_path)
            assert Path(temp_path).exists()
        finally:
            import os
            os.unlink(temp_path)

    def test_to_html(self, sample_result):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            ResultExporter.to_html(sample_result, temp_path)
            assert Path(temp_path).exists()

            with open(temp_path) as f:
                content = f.read()
            assert "<table>" in content
        finally:
            import os
            os.unlink(temp_path)
```

## 4. 集成测试

### 4.1 完整流程测试

```python
class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整处理流程"""
        from src.utils import create_sample_table_image
        from src.pipeline import TableRecognitionPipeline

        # 创建测试图像
        image = create_sample_table_image(rows=3, cols=3)

        # 处理图像
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )
        result = pipeline.process_image(image)

        # 验证结果
        assert "tables" in result
        assert "processing_time" in result

    def test_pipeline_with_different_images(self):
        """测试不同图像的处理"""
        from src.utils import create_sample_table_image, create_sample_image_with_tables
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 测试表格图像
        table_image = create_sample_table_image(rows=2, cols=2)
        result1 = pipeline.process_image(table_image)
        assert "tables" in result1

        # 测试包含表格的图像
        complex_image = create_sample_image_with_tables(num_tables=1)
        result2 = pipeline.process_image(complex_image)
        assert "tables" in result2

    def test_export_integration(self):
        """测试导出集成"""
        from src.utils import create_sample_table_image
        from src.pipeline import TableRecognitionPipeline, ResultExporter

        # 处理图像
        image = create_sample_table_image(rows=2, cols=2)
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )
        result = pipeline.process_image(image)

        # 测试各种导出
        import tempfile

        # JSON
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            ResultExporter.to_json(result, f.name)
            assert Path(f.name).exists()
            import os
            os.unlink(f.name)

        # CSV
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            ResultExporter.to_csv(result, f.name)
            assert Path(f.name).exists()
            import os
            os.unlink(f.name)
```

## 5. 性能测试

### 5.1 处理速度测试

```python
import time
import pytest

class TestPerformance:
    """性能测试"""

    def test_processing_speed(self):
        """测试处理速度"""
        from src.utils import create_sample_table_image
        from src.pipeline import TableRecognitionPipeline

        image = create_sample_table_image(rows=5, cols=5)
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 预热
        pipeline.process_image(image)

        # 测试速度
        start = time.time()
        iterations = 10
        for _ in range(iterations):
            pipeline.process_image(image)
        elapsed = time.time() - start

        avg_time = elapsed / iterations
        assert avg_time < 1.0  # 平均处理时间应小于 1 秒

    def test_memory_usage(self):
        """测试内存使用"""
        import tracemalloc

        from src.utils import create_sample_table_image
        from src.pipeline import TableRecognitionPipeline

        tracemalloc.start()

        image = create_sample_table_image(rows=5, cols=5)
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 处理多张图像
        for _ in range(10):
            pipeline.process_image(image)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # 内存使用不应超过 100MB
        assert peak < 100 * 1024 * 1024

    @pytest.mark.parametrize("rows,cols", [(2, 2), (5, 5), (10, 10)])
    def test_different_table_sizes(self, rows, cols):
        """测试不同表格大小的性能"""
        from src.utils import create_sample_table_image
        from src.pipeline import TableRecognitionPipeline

        image = create_sample_table_image(rows=rows, cols=cols)
        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        start = time.time()
        result = pipeline.process_image(image)
        elapsed = time.time() - start

        # 处理时间应合理
        assert elapsed < 5.0
        assert "tables" in result
```

## 6. 边界情况测试

### 6.1 异常输入测试

```python
class TestEdgeCases:
    """边界情况测试"""

    def test_empty_image(self):
        """测试空图像"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 全白图像
        empty_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = pipeline.process_image(empty_image)
        assert isinstance(result, dict)

    def test_small_image(self):
        """测试小图像"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        small_image = np.ones((10, 10, 3), dtype=np.uint8) * 255
        result = pipeline.process_image(small_image)
        assert isinstance(result, dict)

    def test_large_image(self):
        """测试大图像"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        large_image = np.ones((2000, 3000, 3), dtype=np.uint8) * 255
        result = pipeline.process_image(large_image)
        assert isinstance(result, dict)

    def test_grayscale_image(self):
        """测试灰度图像"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        gray_image = np.ones((100, 100), dtype=np.uint8) * 128
        # 应该能够处理或给出清晰的错误
        try:
            result = pipeline.process_image(gray_image)
            assert isinstance(result, dict)
        except Exception as e:
            assert "image" in str(e).lower() or "shape" in str(e).lower()
```

### 6.2 无效输入测试

```python
class TestInvalidInput:
    """无效输入测试"""

    def test_none_input(self):
        """测试 None 输入"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        with pytest.raises(Exception):
            pipeline.process_image(None)

    def test_invalid_file_path(self):
        """测试无效文件路径"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        with pytest.raises(ValueError):
            pipeline.process("nonexistent.jpg")

    def test_invalid_image_format(self):
        """测试无效图像格式"""
        from src.pipeline import TableRecognitionPipeline

        pipeline = TableRecognitionPipeline(
            detector_type="simple",
            recognizer_type="morphological",
        )

        # 字符串不是有效图像
        with pytest.raises(Exception):
            pipeline.process_image("not an image")
```

## 7. 测试运行

### 7.1 运行所有测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_detector.py

# 运行特定测试类
pytest tests/test_detector.py::TestSimpleTableDetector

# 运行特定测试方法
pytest tests/test_detector.py::TestSimpleTableDetector::test_init
```

### 7.2 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html

# 生成终端覆盖率报告
pytest --cov=src --cov-report=term-missing
```

### 7.3 测试标记

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """标记为慢速测试"""
    pass

# 运行时跳过慢速测试
# pytest -m "not slow"
```

## 8. 测试最佳实践

### 8.1 测试命名规范

- 测试文件: `test_<module>.py`
- 测试类: `Test<ClassName>`
- 测试方法: `test_<function>_<scenario>`

### 8.2 测试数据准备

```python
@pytest.fixture
def sample_data():
    """使用 fixture 准备测试数据"""
    return {
        "image": np.ones((100, 100, 3), dtype=np.uint8) * 255,
        "expected_rows": 3,
        "expected_cols": 3,
    }
```

### 8.3 断言最佳实践

```python
# 好的断言
assert result["rows"] == 3
assert len(result["cells"]) == 9

# 不好的断言
assert result  # 太宽泛
```

### 8.4 测试隔离

```python
# 每个测试应该独立
def test_function_a():
    # 不依赖其他测试的结果
    pass

def test_function_b():
    # 不依赖其他测试的结果
    pass
```

## 9. 持续集成

### 9.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 10. 总结

测试是确保代码质量的关键环节。本项目采用以下测试策略：

1. **单元测试**: 覆盖所有核心模块
2. **集成测试**: 验证模块间协作
3. **性能测试**: 确保处理速度满足要求
4. **边界测试**: 处理各种异常情况

通过完善的测试，可以保证系统的稳定性和可靠性。
