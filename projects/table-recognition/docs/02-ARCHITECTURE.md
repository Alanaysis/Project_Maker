# 架构设计文档

## 1. 系统概述

### 1.1 设计目标

本项目旨在实现一个完整但简洁的表格识别系统，具备以下特点：

- **模块化设计**: 各组件独立，便于扩展和维护
- **可插拔架构**: 支持多种检测和识别方法
- **易于理解**: 代码清晰，适合学习
- **完整流程**: 覆盖从图像输入到数据输出的全流程

### 1.2 核心流程

```
图像输入 → 表格检测 → 结构识别 → 单元格提取 → 数据输出
```

详细流程图：

```
┌─────────────┐
│   图像输入   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   预处理    │────▶│   表格检测   │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  表格区域裁剪 │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  结构识别    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  单元格提取  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  文字识别    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  数据输出    │
                    └─────────────┘
```

## 2. 系统架构

### 2.1 模块划分

```
table-recognition/
├── src/
│   ├── __init__.py          # 模块初始化
│   ├── detector.py          # 表格检测模块
│   ├── structure.py         # 结构识别模块
│   ├── extractor.py         # 单元格提取模块
│   ├── recognizer.py        # 文字识别模块
│   ├── pipeline.py          # 处理管道
│   └── utils.py             # 工具函数
├── tests/                   # 测试模块
├── examples/                # 示例代码
└── docs/                    # 文档
```

### 2.2 模块依赖关系

```
┌─────────────┐
│  pipeline   │ ◀── 主入口
└──────┬──────┘
       │
       ├──▶┌─────────────┐
       │   │  detector   │ ◀── 表格检测
       │   └─────────────┘
       │
       ├──▶┌─────────────┐
       │   │  structure  │ ◀── 结构识别
       │   └─────────────┘
       │
       ├──▶┌─────────────┐
       │   │  extractor  │ ◀── 单元格提取
       │   └─────────────┘
       │
       └──▶┌─────────────┐
           │ recognizer  │ ◀── 文字识别
           └─────────────┘
```

## 3. 核心模块设计

### 3.1 表格检测模块 (detector.py)

#### 类设计

```python
class TableDetector:
    """基于深度学习的表格检测器"""

    def __init__(self, model_path, confidence_threshold, device):
        """初始化检测器"""
        pass

    def preprocess(self, image):
        """图像预处理"""
        pass

    def detect(self, image):
        """检测表格区域"""
        pass

    def crop_table_regions(self, image, results):
        """裁剪表格区域"""
        pass

class SimpleTableDetector:
    """基于传统图像处理的表格检测器"""

    def __init__(self, min_area, aspect_ratio_range):
        """初始化检测器"""
        pass

    def detect(self, image):
        """检测表格区域"""
        pass
```

#### 设计要点

1. **策略模式**: 提供多种检测策略（深度学习/传统方法）
2. **统一接口**: 所有检测器实现相同的 `detect` 方法
3. **可配置性**: 通过参数控制检测行为

### 3.2 结构识别模块 (structure.py)

#### 类设计

```python
class StructureRecognizer:
    """基于形态学操作的结构识别器"""

    def __init__(self, line_threshold, min_line_length, merge_threshold):
        """初始化识别器"""
        pass

    def recognize(self, table_image):
        """识别表格结构"""
        pass

    def _preprocess(self, image):
        """图像预处理"""
        pass

    def _detect_horizontal_lines(self, binary):
        """检测水平线"""
        pass

    def _detect_vertical_lines(self, binary):
        """检测垂直线"""
        pass

    def _merge_lines(self, lines, direction):
        """合并相近的线"""
        pass

    def _generate_cells(self, horizontal_lines, vertical_lines):
        """生成单元格坐标"""
        pass
```

#### 输出数据结构

```python
{
    "rows": int,                    # 行数
    "columns": int,                 # 列数
    "horizontal_lines": List[int],  # 水平线 y 坐标
    "vertical_lines": List[int],    # 垂直线 x 坐标
    "cells": [                      # 单元格列表
        {
            "row": int,             # 行号
            "col": int,             # 列号
            "bbox": [x1, y1, x2, y2]  # 边界框
        }
    ]
}
```

### 3.3 单元格提取模块 (extractor.py)

#### 类设计

```python
class CellExtractor:
    """单元格提取器"""

    def __init__(self, padding, min_cell_size, border_removal):
        """初始化提取器"""
        pass

    def extract(self, table_image, structure):
        """提取单元格"""
        pass

class CellMerger:
    """单元格合并器"""

    def __init__(self, overlap_threshold):
        """初始化合并器"""
        pass

    def merge_cells(self, cells):
        """合并单元格"""
        pass

class CellCoordinateMapper:
    """单元格坐标映射器"""

    def map_coordinates(self, cells, source_shape, target_shape):
        """映射坐标"""
        pass
```

#### 设计要点

1. **职责分离**: 提取、合并、映射分别由不同类处理
2. **可扩展性**: 易于添加新的处理逻辑
3. **数据流**: 清晰的数据流向

### 3.4 文字识别模块 (recognizer.py)

#### 类设计

```python
class TextRecognizer:
    """文字识别器"""

    def __init__(self, engine, language):
        """初始化识别器"""
        pass

    def recognize(self, cell_image):
        """识别单元格文字"""
        pass

    def batch_recognize(self, cell_images):
        """批量识别"""
        pass
```

#### 支持的 OCR 引擎

| 引擎 | 特点 | 适用场景 |
|------|------|----------|
| EasyOCR | 简单易用，支持多语言 | 快速开发 |
| Tesseract | 开源，社区活跃 | 通用场景 |
| PaddleOCR | 中文识别效果好 | 中文文档 |

### 3.5 处理管道 (pipeline.py)

#### 类设计

```python
class TableRecognitionPipeline:
    """表格识别完整流程"""

    def __init__(self, detector_type, recognizer_type, use_ocr, config):
        """初始化管道"""
        pass

    def process(self, image_path):
        """处理图像文件"""
        pass

    def process_image(self, image):
        """处理图像数组"""
        pass

    def visualize_result(self, image, result):
        """可视化结果"""
        pass

class ResultExporter:
    """结果导出器"""

    @staticmethod
    def to_json(result, output_path):
        """导出为 JSON"""
        pass

    @staticmethod
    def to_csv(result, output_path):
        """导出为 CSV"""
        pass

    @staticmethod
    def to_html(result, output_path):
        """导出为 HTML"""
        pass
```

## 4. 数据流设计

### 4.1 处理流程数据流

```
输入图像 (numpy array)
    │
    ▼
┌─────────────────────────────────────┐
│ 表格检测                            │
│ 输入: 图像                          │
│ 输出: 检测结果列表                   │
│       [{bbox, confidence, class_id}]│
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 表格区域裁剪                        │
│ 输入: 图像, 检测结果                 │
│ 输出: 裁剪的表格图像列表             │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 结构识别                            │
│ 输入: 表格图像                       │
│ 输出: 结构信息                       │
│       {rows, columns, cells, ...}   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 单元格提取                          │
│ 输入: 表格图像, 结构信息             │
│ 输出: 单元格列表                     │
│       [{row, col, bbox, image}]     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 文字识别 (可选)                     │
│ 输入: 单元格图像                     │
│ 输出: 文字内容                       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 数据输出                            │
│ 输入: 处理结果                       │
│ 输出: JSON/CSV/HTML                 │
└─────────────────────────────────────┘
```

### 4.2 数据结构定义

#### 检测结果

```python
DetectionResult = {
    "bbox": [x1, y1, x2, y2],  # 边界框坐标
    "confidence": float,        # 置信度 (0-1)
    "class_id": int             # 类别 ID
}
```

#### 表格结构

```python
TableStructure = {
    "rows": int,                    # 行数
    "columns": int,                 # 列数
    "horizontal_lines": List[int],  # 水平线坐标
    "vertical_lines": List[int],    # 垂直线坐标
    "cells": List[CellInfo]         # 单元格信息
}
```

#### 单元格信息

```python
CellInfo = {
    "row": int,                     # 行号
    "col": int,                     # 列号
    "bbox": [x1, y1, x2, y2],      # 边界框
    "image": numpy.ndarray,         # 单元格图像
    "content": str                  # 文字内容
}
```

#### 处理结果

```python
ProcessingResult = {
    "image_size": {
        "width": int,
        "height": int
    },
    "tables": [
        {
            "index": int,
            "bbox": [x1, y1, x2, y2],
            "confidence": float,
            "rows": int,
            "columns": int,
            "cells": List[CellInfo],
            "data": List[List[str]]  # 二维数据数组
        }
    ],
    "processing_time": float
}
```

## 5. 接口设计

### 5.1 公共 API

```python
# 快速使用
from src import TableRecognitionPipeline

pipeline = TableRecognitionPipeline()
result = pipeline.process("image.jpg")

# 导出结果
from src import ResultExporter

ResultExporter.to_json(result, "result.json")
ResultExporter.to_csv(result, "result.csv")
```

### 5.2 高级 API

```python
# 自定义检测器
from src.detector import SimpleTableDetector
from src.structure import StructureRecognizer
from src.extractor import CellExtractor

detector = SimpleTableDetector(min_area=1000)
recognizer = StructureRecognizer()
extractor = CellExtractor(padding=5)

# 分步骤处理
detections = detector.detect(image)
for detection in detections:
    table_image = crop(image, detection["bbox"])
    structure = recognizer.recognize(table_image)
    cells = extractor.extract(table_image, structure)
```

## 6. 扩展性设计

### 6.1 添加新的检测器

```python
class MyDetector:
    """自定义检测器"""

    def detect(self, image):
        """实现检测逻辑"""
        # ...
        return results  # 返回格式与标准检测器一致
```

### 6.2 添加新的结构识别器

```python
class MyStructureRecognizer:
    """自定义结构识别器"""

    def recognize(self, table_image):
        """实现识别逻辑"""
        # ...
        return {
            "rows": rows,
            "columns": columns,
            "horizontal_lines": h_lines,
            "vertical_lines": v_lines,
            "cells": cells,
        }
```

### 6.3 添加新的导出格式

```python
class MyExporter:
    """自定义导出器"""

    @staticmethod
    def to_my_format(result, output_path):
        """实现导出逻辑"""
        # ...
```

## 7. 性能优化策略

### 7.1 图像预处理优化

- **缩放**: 对大图像进行适当缩放
- **裁剪**: 只处理感兴趣区域
- **灰度化**: 单通道处理减少计算量

### 7.2 检测优化

- **批量处理**: 同时处理多张图像
- **模型优化**: 使用 TensorRT 或 ONNX 加速
- **NMS 优化**: 使用高效的非极大值抑制

### 7.3 内存优化

- **流式处理**: 避免一次性加载所有数据
- **及时释放**: 处理完的中间结果及时释放
- **数据类型**: 使用合适的数据类型（如 uint8）

## 8. 错误处理设计

### 8.1 异常类型

```python
class TableRecognitionError(Exception):
    """表格识别基础异常"""
    pass

class DetectionError(TableRecognitionError):
    """检测错误"""
    pass

class StructureError(TableRecognitionError):
    """结构识别错误"""
    pass

class ExtractionError(TableRecognitionError):
    """提取错误"""
    pass
```

### 8.2 错误处理策略

1. **输入验证**: 验证输入图像的有效性
2. **优雅降级**: 当一种方法失败时尝试备选方法
3. **日志记录**: 记录详细的错误信息
4. **用户提示**: 提供清晰的错误提示

## 9. 测试策略

### 9.1 单元测试

- 每个模块独立测试
- 测试各种边界情况
- 测试错误处理

### 9.2 集成测试

- 测试模块间的协作
- 测试完整处理流程
- 测试导出功能

### 9.3 性能测试

- 测试处理速度
- 测试内存使用
- 测试并发性能

## 10. 总结

本架构设计遵循以下原则：

1. **模块化**: 各组件职责清晰，便于维护
2. **可扩展**: 易于添加新的实现
3. **易用性**: 提供简洁的公共 API
4. **健壮性**: 完善的错误处理
5. **可测试**: 便于编写测试

通过这种架构设计，系统既适合学习表格识别的基本原理，又具备一定的实用价值。
