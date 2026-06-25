# 表格识别示例

本目录包含表格识别系统的使用示例。

## 示例列表

### 1. demo.py - 基础演示

演示如何使用表格识别系统处理图像并提取表格数据。

```bash
cd projects/table-recognition
python examples/demo.py
```

运行后会在 `examples/` 目录下生成以下文件：
- `sample_table.png` - 示例表格图像
- `sample_tables.png` - 包含多个表格的图像
- `visualization_result.png` - 可视化结果
- `result.json` - JSON 格式结果
- `result.csv` - CSV 格式结果
- `result.html` - HTML 格式结果
- `complex_table.png` - 复杂表格图像
- `batch_table_*.png` - 批量处理的表格图像

### 2. 代码示例

#### 基础使用

```python
from src.pipeline import TableRecognitionPipeline

# 初始化管道
pipeline = TableRecognitionPipeline(
    detector_type="simple",
    recognizer_type="morphological",
    use_ocr=False,
)

# 处理图像
result = pipeline.process_image(image)

# 获取结果
print(f"检测到 {len(result['tables'])} 个表格")
for table in result['tables']:
    print(f"  行数: {table['rows']}, 列数: {table['columns']}")
```

#### 导出结果

```python
from src.pipeline import ResultExporter

# 导出为 JSON
ResultExporter.to_json(result, "result.json")

# 导出为 CSV
ResultExporter.to_csv(result, "result.csv")

# 导出为 HTML
ResultExporter.to_html(result, "result.html")
```

#### 可视化结果

```python
# 可视化检测结果
vis_image = pipeline.visualize_result(
    image,
    result,
    show_cells=True,
    show_text=False
)

# 保存可视化结果
cv2.imwrite("visualization.png", vis_image)
```

## 输出示例

### JSON 输出格式

```json
{
  "image_size": {
    "width": 600,
    "height": 400
  },
  "tables": [
    {
      "index": 0,
      "bbox": [100, 100, 500, 300],
      "rows": 3,
      "columns": 3,
      "cells": [
        {
          "row": 0,
          "col": 0,
          "bbox": [100, 100, 233, 166]
        }
      ],
      "data": [
        ["R0C0", "R0C1", "R0C2"],
        ["R1C0", "R1C1", "R1C2"],
        ["R2C0", "R2C1", "R2C2"]
      ]
    }
  ],
  "processing_time": 0.15
}
```

### CSV 输出格式

```csv
R0C0,R0C1,R0C2
R1C0,R1C1,R1C2
R2C0,R2C1,R2C2
```

### HTML 输出格式

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>表格识别结果</title>
</head>
<body>
  <table>
    <tr>
      <th>R0C0</th>
      <th>R0C1</th>
      <th>R0C2</th>
    </tr>
    <tr>
      <td>R1C0</td>
      <td>R1C1</td>
      <td>R1C2</td>
    </tr>
  </table>
</body>
</html>
```

## 注意事项

1. 示例中的 OCR 功能默认关闭，如需使用请安装 EasyOCR 或 Tesseract
2. 生成的图像文件位于 `examples/` 目录下
3. 处理大图像可能需要较长时间

## 扩展示例

更多使用示例请参考：
- `examples/demo.py` - 完整演示脚本
- `tests/` - 测试用例
- `docs/` - 详细文档
