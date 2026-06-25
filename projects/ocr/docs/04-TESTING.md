# 测试文档：OCR 文字识别系统

## 1. 测试策略

### 1.1 测试层次

```
单元测试 → 集成测试 → 系统测试 → 性能测试
```

### 1.2 测试覆盖

- 模块独立测试
- 模块间集成测试
- 端到端功能测试
- 边界条件测试
- 性能基准测试

## 2. 单元测试

### 2.1 工具函数测试

```python
"""测试工具函数"""

import pytest
import numpy as np
import cv2
from src.utils import (
    resize_image, order_points, crop_text_region,
    compute_iou, nms
)


class TestResizeImage:
    """测试图像缩放"""
    
    def test_resize_normal(self):
        """正常缩放"""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=100)
        assert resized.shape[0] <= 100
        assert resized.shape[1] <= 100
    
    def test_resize_small_image(self):
        """小图像不缩放"""
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=100)
        assert resized.shape == image.shape
    
    def test_resize_preserve_ratio(self):
        """保持宽高比"""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=100)
        ratio_orig = 200 / 100
        ratio_resized = resized.shape[1] / resized.shape[0]
        assert abs(ratio_orig - ratio_resized) < 0.1


class TestOrderPoints:
    """测试点排序"""
    
    def test_order_square(self):
        """正方形点排序"""
        pts = np.array([[10, 10], [10, 0], [0, 0], [0, 10]], dtype=np.float32)
        ordered = order_points(pts)
        # 左上、右上、右下、左下
        assert ordered[0][0] < ordered[1][0]  # 左上.x < 右上.x
        assert ordered[0][1] < ordered[3][1]  # 左上.y < 左下.y
    
    def test_order_rectangle(self):
        """矩形点排序"""
        pts = np.array([[100, 50], [0, 50], [0, 0], [100, 0]], dtype=np.float32)
        ordered = order_points(pts)
        assert ordered[0][0] < ordered[1][0]


class TestComputeIoU:
    """测试 IoU 计算"""
    
    def test_iou_no_overlap(self):
        """无重叠"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([20, 20, 30, 30])
        assert compute_iou(box1, box2) == 0
    
    def test_iou_full_overlap(self):
        """完全重叠"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([0, 0, 10, 10])
        assert compute_iou(box1, box2) == 1.0
    
    def test_iou_partial_overlap(self):
        """部分重叠"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([5, 5, 15, 15])
        iou = compute_iou(box1, box2)
        assert 0 < iou < 1


class TestNMS:
    """测试 NMS"""
    
    def test_nms_empty(self):
        """空输入"""
        boxes = np.array([])
        scores = np.array([])
        assert nms(boxes, scores) == []
    
    def test_nms_no_overlap(self):
        """无重叠框"""
        boxes = np.array([
            [0, 0, 10, 10],
            [20, 20, 30, 30]
        ])
        scores = np.array([0.9, 0.8])
        keep = nms(boxes, scores, threshold=0.5)
        assert len(keep) == 2
    
    def test_nms_overlap(self):
        """重叠框"""
        boxes = np.array([
            [0, 0, 10, 10],
            [1, 1, 11, 11],
            [20, 20, 30, 30]
        ])
        scores = np.array([0.9, 0.8, 0.7])
        keep = nms(boxes, scores, threshold=0.5)
        assert len(keep) == 2
```

### 2.2 文字检测器测试

```python
"""测试文字检测器"""

import pytest
import numpy as np
import cv2
from src.detector import SimpleTextDetector


class TestSimpleTextDetector:
    """测试简单文字检测器"""
    
    @pytest.fixture
    def detector(self):
        return SimpleTextDetector(min_area=50, max_area=100000)
    
    @pytest.fixture
    def text_image(self):
        """创建包含文字的测试图像"""
        image = np.zeros((100, 400, 3), dtype=np.uint8)
        cv2.putText(image, "Hello World", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return image
    
    @pytest.fixture
    def empty_image(self):
        """空白图像"""
        return np.zeros((100, 400, 3), dtype=np.uint8)
    
    def test_detect_text(self, detector, text_image):
        """检测文字"""
        bboxes = detector.detect(text_image)
        assert len(bboxes) > 0
    
    def test_detect_empty(self, detector, empty_image):
        """空白图像检测"""
        bboxes = detector.detect(empty_image)
        assert len(bboxes) == 0
    
    def test_bbox_format(self, detector, text_image):
        """检测框格式"""
        bboxes = detector.detect(text_image)
        for bbox in bboxes:
            assert bbox.shape == (4, 2)
    
    def test_bbox_valid(self, detector, text_image):
        """检测框有效性"""
        bboxes = detector.detect(text_image)
        h, w = text_image.shape[:2]
        for bbox in bboxes:
            assert np.all(bbox >= 0)
            assert np.all(bbox[:, 0] <= w)
            assert np.all(bbox[:, 1] <= h)
```

### 2.3 CRNN 模型测试

```python
"""测试 CRNN 模型"""

import pytest
import torch
from src.recognizer import CRNN, CTCDecoder


class TestCRNN:
    """测试 CRNN 模型"""
    
    @pytest.fixture
    def model(self):
        return CRNN(num_classes=63)
    
    def test_forward(self, model):
        """前向传播"""
        x = torch.randn(2, 1, 32, 100)
        output = model(x)
        # 输出形状: (T, B, num_classes)
        assert output.shape[1] == 2
        assert output.shape[2] == 63
    
    def test_output_sequence(self, model):
        """输出序列长度"""
        x = torch.randn(1, 1, 32, 100)
        output = model(x)
        # 序列长度应大于0
        assert output.shape[0] > 0
    
    def test_gradient(self, model):
        """梯度计算"""
        x = torch.randn(2, 1, 32, 100)
        output = model(x)
        loss = output.sum()
        loss.backward()
        
        for param in model.parameters():
            assert param.grad is not None


class TestCTCDecoder:
    """测试 CTC 解码器"""
    
    @pytest.fixture
    def decoder(self):
        charset = "0123456789abcdefghijklmnopqrstuvwxyz"
        return CTCDecoder(charset)
    
    def test_greedy_decode(self, decoder):
        """贪心解码"""
        # 模拟输出: 3个时间步, 63个类别
        logits = torch.randn(3, 63)
        text = decoder.greedy_decode(logits)
        assert isinstance(text, str)
    
    def test_decode_no_repeat(self, decoder):
        """去重测试"""
        # 创建有重复的输出
        logits = torch.zeros(5, 63)
        logits[0, 1] = 1  # 字符 '0'
        logits[1, 1] = 1  # 重复
        logits[2, 2] = 1  # 字符 '1'
        
        text = decoder.greedy_decode(logits)
        # 应该去重
        assert len(text) <= 3
```

### 2.4 文字识别器测试

```python
"""测试文字识别器"""

import pytest
import numpy as np
import cv2
from src.recognizer import TextRecognizer


class TestTextRecognizer:
    """测试文字识别器"""
    
    @pytest.fixture
    def recognizer(self):
        return TextRecognizer()
    
    @pytest.fixture
    def digit_image(self):
        """创建数字图像"""
        image = np.zeros((32, 100), dtype=np.uint8)
        cv2.putText(image, "123", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)
        return image
    
    def test_preprocess(self, recognizer, digit_image):
        """预处理"""
        tensor = recognizer.preprocess(digit_image)
        assert tensor.shape == (1, 1, 32, 100)
    
    def test_recognize(self, recognizer, digit_image):
        """识别"""
        text, confidence = recognizer.recognize(digit_image)
        assert isinstance(text, str)
        assert 0 <= confidence <= 1
    
    def test_recognize_batch(self, recognizer):
        """批量识别"""
        images = [
            np.zeros((32, 100), dtype=np.uint8),
            np.zeros((32, 100), dtype=np.uint8)
        ]
        results = recognizer.recognize_batch(images)
        assert len(results) == 2
```

## 3. 集成测试

### 3.1 OCR 引擎测试

```python
"""测试 OCR 引擎"""

import pytest
import numpy as np
import cv2
from src.ocr_engine import OCREngine


class TestOCREngine:
    """测试 OCR 引擎"""
    
    @pytest.fixture
    def engine(self):
        return OCREngine()
    
    @pytest.fixture
    def text_image(self):
        """创建包含文字的测试图像"""
        image = np.zeros((200, 600, 3), dtype=np.uint8)
        cv2.putText(image, "Hello", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(image, "World", (300, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        return image
    
    def test_process(self, engine, text_image):
        """处理图像"""
        results = engine.process(text_image)
        assert isinstance(results, list)
    
    def test_result_format(self, engine, text_image):
        """结果格式"""
        results = engine.process(text_image)
        for result in results:
            assert "bbox" in result
            assert "text" in result
            assert "confidence" in result
    
    def test_process_batch(self, engine):
        """批量处理"""
        images = [
            np.zeros((200, 600, 3), dtype=np.uint8),
            np.zeros((200, 600, 3), dtype=np.uint8)
        ]
        all_results = engine.process_batch(images)
        assert len(all_results) == 2
```

## 4. 评估测试

### 4.1 评估器测试

```python
"""测试评估器"""

import pytest
from src.evaluator import OCREvaluator


class TestOCREvaluator:
    """测试评估器"""
    
    @pytest.fixture
    def evaluator(self):
        return OCREvaluator()
    
    def test_char_accuracy(self, evaluator):
        """字符准确率"""
        evaluator.add_result("hello", "hello")
        evaluator.add_result("helo", "hello")
        
        accuracy = evaluator.compute_char_accuracy()
        assert 0 < accuracy < 1
    
    def test_word_accuracy(self, evaluator):
        """词准确率"""
        evaluator.add_result("hello", "hello")
        evaluator.add_result("world", "world")
        evaluator.add_result("helo", "hello")
        
        accuracy = evaluator.compute_word_accuracy()
        assert abs(accuracy - 2/3) < 0.01
    
    def test_edit_distance(self, evaluator):
        """编辑距离"""
        d1 = evaluator.compute_edit_distance("hello", "hello")
        assert d1 == 0
        
        d2 = evaluator.compute_edit_distance("hello", "helo")
        assert d2 == 1
        
        d3 = evaluator.compute_edit_distance("abc", "xyz")
        assert d3 == 3
    
    def test_summary(self, evaluator):
        """评估摘要"""
        evaluator.add_result("test", "test")
        summary = evaluator.summary()
        
        assert "char_accuracy" in summary
        assert "word_accuracy" in summary
        assert "normalized_edit_distance" in summary
        assert "num_samples" in summary
```

## 5. 边界条件测试

### 5.1 边界测试用例

```python
"""边界条件测试"""

import pytest
import numpy as np
from src.ocr_engine import OCREngine


class TestEdgeCases:
    """边界条件测试"""
    
    @pytest.fixture
    def engine(self):
        return OCREngine()
    
    def test_empty_image(self, engine):
        """空图像"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        results = engine.process(image)
        assert isinstance(results, list)
    
    def test_small_image(self, engine):
        """极小图像"""
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        results = engine.process(image)
        assert isinstance(results, list)
    
    def test_large_image(self, engine):
        """大图像"""
        image = np.zeros((4000, 4000, 3), dtype=np.uint8)
        results = engine.process(image)
        assert isinstance(results, list)
    
    def test_grayscale_image(self, engine):
        """灰度图像"""
        image = np.zeros((100, 100), dtype=np.uint8)
        # 应该能处理灰度图像
        results = engine.process(image)
        assert isinstance(results, list)
    
    def test_noisy_image(self, engine):
        """噪声图像"""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        results = engine.process(image)
        assert isinstance(results, list)
```

## 6. 性能测试

### 6.1 性能基准

```python
"""性能测试"""

import pytest
import time
import numpy as np
from src.ocr_engine import OCREngine


class TestPerformance:
    """性能测试"""
    
    @pytest.fixture
    def engine(self):
        return OCREngine()
    
    def test_detection_speed(self, engine):
        """检测速度"""
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        
        start = time.time()
        for _ in range(10):
            engine.detector.detect(image)
        elapsed = time.time() - start
        
        avg_time = elapsed / 10
        print(f"Detection time: {avg_time:.3f}s")
        assert avg_time < 1.0  # 应该在1秒内
    
    def test_recognition_speed(self, engine):
        """识别速度"""
        image = np.zeros((32, 100), dtype=np.uint8)
        
        start = time.time()
        for _ in range(100):
            engine.recognizer.recognize(image)
        elapsed = time.time() - start
        
        avg_time = elapsed / 100
        print(f"Recognition time: {avg_time:.3f}s")
        assert avg_time < 0.1  # 应该在0.1秒内
    
    def test_end_to_end_speed(self, engine):
        """端到端速度"""
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        
        start = time.time()
        engine.process(image)
        elapsed = time.time() - start
        
        print(f"End-to-end time: {elapsed:.3f}s")
        assert elapsed < 5.0  # 应该在5秒内
```

## 7. 测试运行

### 7.1 运行所有测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_utils.py

# 运行带详细输出
pytest tests/ -v

# 运行并显示覆盖率
pytest tests/ --cov=src
```

### 7.2 测试配置

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 8. 测试覆盖率

### 8.1 覆盖率目标

- 工具函数: 100%
- 检测模块: 90%+
- 识别模块: 90%+
- OCR 引擎: 85%+

### 8.2 生成覆盖率报告

```bash
pytest --cov=src --cov-report=html tests/
```

## 9. 持续集成

### 9.1 CI 配置示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=src tests/
```