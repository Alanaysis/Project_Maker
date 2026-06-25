# 实现细节文档

## 1. 表格检测实现

### 1.1 传统图像处理方法

#### 形态学操作

```python
def detect_tables_morphological(image):
    # 1. 转灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. 二值化
    _, binary = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3. 膨胀连接线条
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    dilated = cv2.dilate(binary, kernel, iterations=2)

    # 4. 查找轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    # 5. 过滤表格区域
    tables = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            tables.append([x, y, x + w, y + h])

    return tables
```

#### 关键参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `min_area` | 最小表格面积 | 1000-5000 |
| `kernel_size` | 膨胀核大小 | (15, 3) |
| `iterations` | 膨胀迭代次数 | 2-3 |

### 1.2 深度学习方法

#### Faster R-CNN 实现

```python
import torch
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn

class DeepTableDetector:
    def __init__(self, num_classes=2):
        # 加载预训练模型
        self.model = fasterrcnn_resnet50_fpn(pretrained=True)

        # 修改分类头
        in_features = self.model.roi_heads.box_predictor.cls_score.in_features
        self.model.roi_heads.box_predictor = FastRCNNPredictor(
            in_features, num_classes
        )

    def detect(self, image):
        # 预处理
        image_tensor = self.preprocess(image)

        # 推理
        with torch.no_grad():
            predictions = self.model(image_tensor)

        # 后处理
        results = self.postprocess(predictions)
        return results
```

#### 模型训练要点

1. **数据准备**: 收集和标注表格图像
2. **数据增强**: 翻转、旋转、缩放
3. **损失函数**: 分类损失 + 回归损失
4. **优化器**: SGD 或 Adam
5. **学习率**: 0.001-0.01

## 2. 结构识别实现

### 2.1 形态学线条检测

#### 水平线检测

```python
def detect_horizontal_lines(binary, min_length=100):
    h, w = binary.shape

    # 创建水平核
    kernel_length = w // 10
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))

    # 形态学开运算
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

    # 膨胀连接
    horizontal = cv2.dilate(horizontal, kernel, iterations=1)

    # 查找轮廓
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    # 提取 y 坐标
    lines = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > min_length:
            lines.append(y + h // 2)

    return sorted(lines)
```

#### 垂直线检测

```python
def detect_vertical_lines(binary, min_length=100):
    h, w = binary.shape

    # 创建垂直核
    kernel_length = h // 10
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))

    # 形态学开运算
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

    # 膨胀连接
    vertical = cv2.dilate(vertical, kernel, iterations=1)

    # 查找轮廓
    contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    # 提取 x 坐标
    lines = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h > min_length:
            lines.append(x + w // 2)

    return sorted(lines)
```

### 2.2 线条合并算法

```python
def merge_lines(lines, threshold=10):
    """
    合并相近的线条

    Args:
        lines: 线条坐标列表
        threshold: 合并阈值（像素）

    Returns:
        合并后的线条列表
    """
    if not lines:
        return []

    merged = [lines[0]]
    for line in lines[1:]:
        if abs(line - merged[-1]) <= threshold:
            # 合并：取平均值
            merged[-1] = (merged[-1] + line) // 2
        else:
            merged.append(line)

    return merged
```

### 2.3 霍夫变换方法

```python
def detect_lines_hough(image, threshold=100):
    # 边缘检测
    edges = cv2.Canny(image, 50, 150, apertureSize=3)

    # 霍夫线变换
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=threshold,
        minLineLength=50,
        maxLineGap=5
    )

    # 分类线条
    horizontal = []
    vertical = []

    for line in lines:
        x1, y1, x2, y2 = line[0]

        # 计算角度
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

        if abs(angle) < 5 or abs(angle) > 175:
            horizontal.append((y1 + y2) // 2)
        elif abs(angle - 90) < 5 or abs(angle + 90) < 5:
            vertical.append((x1 + x2) // 2)

    return horizontal, vertical
```

### 2.4 单元格坐标生成

```python
def generate_cells(horizontal_lines, vertical_lines):
    """
    根据线条坐标生成单元格

    Args:
        horizontal_lines: 水平线 y 坐标列表
        vertical_lines: 垂直线 x 坐标列表

    Returns:
        单元格列表
    """
    cells = []

    for i in range(len(horizontal_lines) - 1):
        for j in range(len(vertical_lines) - 1):
            cell = {
                "row": i,
                "col": j,
                "bbox": [
                    vertical_lines[j],      # x1
                    horizontal_lines[i],    # y1
                    vertical_lines[j + 1],  # x2
                    horizontal_lines[i + 1] # y2
                ]
            }
            cells.append(cell)

    return cells
```

## 3. 单元格提取实现

### 3.1 基础提取

```python
def extract_cells(table_image, structure, padding=2):
    cells = structure["cells"]
    extracted = []

    for cell in cells:
        x1, y1, x2, y2 = cell["bbox"]

        # 添加内边距
        x1 = max(0, x1 + padding)
        y1 = max(0, y1 + padding)
        x2 = min(table_image.shape[1], x2 - padding)
        y2 = min(table_image.shape[0], y2 - padding)

        # 提取图像
        cell_image = table_image[y1:y2, x1:x2]

        extracted.append({
            "row": cell["row"],
            "col": cell["col"],
            "bbox": cell["bbox"],
            "image": cell_image
        })

    return extracted
```

### 3.2 边框移除

```python
def remove_border(cell_image, border_width=2):
    """移除单元格边框"""
    h, w = cell_image.shape[:2]

    if h > 2 * border_width and w > 2 * border_width:
        return cell_image[border_width:h-border_width,
                         border_width:w-border_width]

    return cell_image
```

### 3.3 合并单元格处理

```python
def detect_merged_cells(cells, threshold=0.5):
    """
    检测合并单元格

    Args:
        cells: 单元格列表
        threshold: 重叠阈值

    Returns:
        合并后的单元格列表
    """
    merged = []
    processed = set()

    for i, cell1 in enumerate(cells):
        if i in processed:
            continue

        current_group = [cell1]

        for j, cell2 in enumerate(cells[i+1:], i+1):
            if j in processed:
                continue

            # 检查是否应该合并
            if should_merge(cell1, cell2, threshold):
                current_group.append(cell2)
                processed.add(j)

        # 合并单元格组
        if len(current_group) > 1:
            merged_cell = merge_cell_group(current_group)
            merged.append(merged_cell)
        else:
            merged.append(cell1)

        processed.add(i)

    return merged
```

## 4. 文字识别实现

### 4.1 EasyOCR 集成

```python
import easyocr

class EasyOCRRecognizer:
    def __init__(self, languages=['ch_sim', 'en']):
        self.reader = easyocr.Reader(languages)

    def recognize(self, image):
        results = self.reader.readtext(image)

        texts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                texts.append(text)

        return ' '.join(texts)
```

### 4.2 Tesseract 集成

```python
import pytesseract

class TesseractRecognizer:
    def __init__(self, language='chi_sim+eng'):
        self.language = language

    def recognize(self, image):
        config = f'--oem 3 --psm 6 -l {self.language}'
        text = pytesseract.image_to_string(image, config=config)
        return text.strip()
```

### 4.3 图像预处理优化

```python
def preprocess_for_ocr(image):
    """为 OCR 优化图像"""
    # 转灰度
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # 去噪
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 对比度增强
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 二值化
    _, binary = cv2.threshold(enhanced, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 膨胀使文字更清晰
    kernel = np.ones((1, 1), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)

    return dilated
```

## 5. 数据导出实现

### 5.1 JSON 导出

```python
import json

def export_to_json(result, output_path):
    """导出为 JSON 格式"""

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

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(clean_result, f, ensure_ascii=False, indent=2)
```

### 5.2 CSV 导出

```python
import csv

def export_to_csv(result, output_path, table_index=0):
    """导出为 CSV 格式"""
    table = result["tables"][table_index]
    data = table["data"]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
```

### 5.3 HTML 导出

```python
def export_to_html(result, output_path, table_index=0):
    """导出为 HTML 格式"""
    table = result["tables"][table_index]
    data = table["data"]

    html = "<!DOCTYPE html>\n<html>\n<head>\n"
    html += "<meta charset='UTF-8'>\n"
    html += "<style>\n"
    html += "table { border-collapse: collapse; width: 100%; }\n"
    html += "th, td { border: 1px solid black; padding: 8px; }\n"
    html += "</style>\n</head>\n<body>\n"

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

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
```

## 6. 可视化实现

### 6.1 检测结果可视化

```python
def visualize_detections(image, detections):
    """可视化检测结果"""
    vis_image = image.copy()

    for det in detections:
        bbox = det["bbox"]
        confidence = det["confidence"]

        # 绘制边界框
        cv2.rectangle(vis_image,
                     (bbox[0], bbox[1]),
                     (bbox[2], bbox[3]),
                     (0, 255, 0), 2)

        # 添加标签
        label = f"Table: {confidence:.2f}"
        cv2.putText(vis_image, label,
                   (bbox[0], bbox[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX,
                   0.5, (0, 255, 0), 2)

    return vis_image
```

### 6.2 结构识别可视化

```python
def visualize_structure(table_image, structure):
    """可视化表格结构"""
    vis_image = table_image.copy()

    # 绘制水平线
    for y in structure["horizontal_lines"]:
        cv2.line(vis_image, (0, y), (vis_image.shape[1], y),
                (0, 0, 255), 1)

    # 绘制垂直线
    for x in structure["vertical_lines"]:
        cv2.line(vis_image, (x, 0), (x, vis_image.shape[0]),
                (255, 0, 0), 1)

    # 绘制单元格
    for cell in structure["cells"]:
        bbox = cell["bbox"]
        cv2.rectangle(vis_image,
                     (bbox[0], bbox[1]),
                     (bbox[2], bbox[3]),
                     (0, 255, 0), 1)

    return vis_image
```

## 7. 性能优化技巧

### 7.1 图像缩放

```python
def resize_for_processing(image, max_size=1000):
    """调整图像大小以加快处理"""
    h, w = image.shape[:2]

    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h))

    return image
```

### 7.2 批量处理

```python
def batch_process(images, pipeline):
    """批量处理图像"""
    results = []
    for image in images:
        result = pipeline.process_image(image)
        results.append(result)
    return results
```

### 7.3 内存优化

```python
def process_large_image(image_path, tile_size=500):
    """处理大图像（分块处理）"""
    image = cv2.imread(image_path)
    h, w = image.shape[:2]

    results = []
    for y in range(0, h, tile_size):
        for x in range(0, w, tile_size):
            # 提取块
            tile = image[y:y+tile_size, x:x+tile_size]

            # 处理块
            tile_result = process_tile(tile)

            # 调整坐标
            for table in tile_result["tables"]:
                bbox = table["bbox"]
                table["bbox"] = [
                    bbox[0] + x, bbox[1] + y,
                    bbox[2] + x, bbox[3] + y
                ]

            results.extend(tile_result["tables"])

    return results
```

## 8. 常见问题与解决方案

### 8.1 表格检测不准确

**问题**: 检测到的表格边界不准确

**解决方案**:
1. 调整形态学核大小
2. 增加/减少膨胀迭代次数
3. 调整面积阈值

### 8.2 线条检测失败

**问题**: 无法检测到表格线条

**解决方案**:
1. 检查图像质量
2. 调整二值化参数
3. 尝试不同的边缘检测方法

### 8.3 合并单元格处理

**问题**: 合并单元格被错误识别

**解决方案**:
1. 检测空单元格
2. 使用投影分析
3. 考虑使用深度学习方法

### 8.4 OCR 准确率低

**问题**: 文字识别错误率高

**解决方案**:
1. 优化图像预处理
2. 调整 OCR 参数
3. 使用更好的 OCR 引擎
4. 训练自定义模型

## 9. 调试技巧

### 9.1 中间结果可视化

```python
def debug_pipeline(image, pipeline):
    """调试管道，显示中间结果"""

    # 1. 显示原图
    cv2.imshow("Original", image)

    # 2. 显示预处理结果
    preprocessed = pipeline.preprocess(image)
    cv2.imshow("Preprocessed", preprocessed)

    # 3. 显示检测结果
    detections = pipeline.detect(image)
    vis_detections = visualize_detections(image, detections)
    cv2.imshow("Detections", vis_detections)

    # 4. 显示结构识别结果
    for det in detections:
        table_image = crop(image, det["bbox"])
        structure = pipeline.recognize_structure(table_image)
        vis_structure = visualize_structure(table_image, structure)
        cv2.imshow("Structure", vis_structure)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

### 9.2 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def process_with_logging(image, pipeline):
    """带日志的处理流程"""
    logger.info("开始处理图像")

    try:
        result = pipeline.process_image(image)
        logger.info(f"处理完成，检测到 {len(result['tables'])} 个表格")
        return result
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
```

## 10. 总结

本实现文档涵盖了表格识别系统的核心实现细节，包括：

1. **表格检测**: 传统方法和深度学习方法
2. **结构识别**: 形态学操作和霍夫变换
3. **单元格提取**: 基础提取和合并单元格处理
4. **文字识别**: EasyOCR 和 Tesseract 集成
5. **数据导出**: JSON、CSV、HTML 格式
6. **性能优化**: 图像缩放、批量处理、内存优化

通过理解这些实现细节，可以更好地掌握表格识别技术，并根据实际需求进行定制和优化。
