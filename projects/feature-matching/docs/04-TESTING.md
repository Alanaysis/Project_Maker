# 特征匹配测试文档

## 1. 测试策略

### 测试层次
1. **单元测试**: 测试各个模块的功能
2. **集成测试**: 测试模块间协作
3. **性能测试**: 测试处理速度和内存使用

### 测试工具
- pytest: 测试框架
- pytest-cov: 覆盖率报告
- OpenCV测试工具: 生成测试图像

## 2. 单元测试

### 2.1 检测器测试

```python
# test_detector.py
import cv2
import numpy as np
import pytest
from src.detector import FeatureDetector

@pytest.fixture
def sample_image():
    """创建测试图像"""
    img = np.zeros((100, 100), dtype=np.uint8)
    # 添加角点
    cv2.rectangle(img, (20, 20), (40, 40), 255, -1)
    cv2.rectangle(img, (60, 60), (80, 80), 255, -1)
    return img

def test_sift_detection(sample_image):
    """测试SIFT检测"""
    detector = FeatureDetector(method='sift')
    keypoints = detector.detect(sample_image)
    assert len(keypoints) > 0

def test_orb_detection(sample_image):
    """测试ORB检测"""
    detector = FeatureDetector(method='orb')
    keypoints = detector.detect(sample_image)
    assert len(keypoints) > 0

def test_invalid_image():
    """测试无效图像"""
    detector = FeatureDetector(method='sift')
    with pytest.raises(ValueError):
        detector.detect(None)

def test_detect_and_compute(sample_image):
    """测试同时检测和计算"""
    detector = FeatureDetector(method='sift')
    keypoints, descriptors = detector.detect_and_compute(sample_image)
    assert len(keypoints) > 0
    assert descriptors is not None
    assert descriptors.shape[0] == len(keypoints)
```

### 2.2 描述子测试

```python
# test_descriptor.py
import cv2
import numpy as np
import pytest
from src.descriptor import DescriptorExtractor

@pytest.fixture
def keypoints_and_image():
    """创建关键点和图像"""
    img = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), 255, -1)

    detector = cv2.SIFT_create()
    keypoints = detector.detect(img)
    return img, keypoints

def test_sift_descriptor(keypoints_and_image):
    """测试SIFT描述子"""
    img, keypoints = keypoints_and_image
    extractor = DescriptorExtractor(method='sift')
    _, descriptors = extractor.compute(img, keypoints)

    assert descriptors is not None
    assert descriptors.shape[1] == 128  # SIFT描述子维度

def test_orb_descriptor(keypoints_and_image):
    """测试ORB描述子"""
    img, keypoints = keypoints_and_image
    extractor = DescriptorExtractor(method='orb')
    _, descriptors = extractor.compute(img, keypoints)

    assert descriptors is not None
    assert descriptors.shape[1] == 32  # ORB描述子维度

def test_empty_keypoints():
    """测试空关键点"""
    img = np.zeros((100, 100), dtype=np.uint8)
    extractor = DescriptorExtractor(method='sift')
    _, descriptors = extractor.compute(img, [])
    assert descriptors is None
```

### 2.3 匹配器测试

```python
# test_matcher.py
import cv2
import numpy as np
import pytest
from src.matcher import FeatureMatcher

@pytest.fixture
def sample_descriptors():
    """创建测试描述子"""
    # 创建两个相似的描述子集
    desc1 = np.random.randn(10, 128).astype(np.float32)
    desc2 = desc1 + np.random.randn(10, 128).astype(np.float32) * 0.1
    return desc1, desc2

def test_bf_match(sample_descriptors):
    """测试暴力匹配"""
    desc1, desc2 = sample_descriptors
    matcher = FeatureMatcher(method='bf', cross_check=True)
    matches = matcher.match(desc1, desc2)
    assert len(matches) > 0

def test_flann_match(sample_descriptors):
    """测试FLANN匹配"""
    desc1, desc2 = sample_descriptors
    matcher = FeatureMatcher(method='flann')
    matches = matcher.match(desc1, desc2)
    assert len(matches) > 0

def test_knn_match(sample_descriptors):
    """测试KNN匹配"""
    desc1, desc2 = sample_descriptors
    matcher = FeatureMatcher(method='bf', cross_check=False)
    matches = matcher.knn_match(desc1, desc2, k=2)
    assert len(matches) > 0
    assert len(matches[0]) == 2

def test_ratio_test(sample_descriptors):
    """测试比率测试"""
    desc1, desc2 = sample_descriptors
    matcher = FeatureMatcher(method='bf', cross_check=False)
    matches = matcher.knn_match(desc1, desc2, k=2)
    good_matches = matcher.ratio_test(matches, ratio=0.7)
    assert len(good_matches) <= len(matches)

def test_empty_descriptors():
    """测试空描述子"""
    matcher = FeatureMatcher(method='bf')
    matches = matcher.match(None, None)
    assert len(matches) == 0
```

## 3. 集成测试

```python
# test_integration.py
import cv2
import numpy as np
import pytest
from src.detector import FeatureDetector
from src.descriptor import DescriptorExtractor
from src.matcher import FeatureMatcher

def test_full_pipeline():
    """测试完整流程"""
    # 创建测试图像
    img1 = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img1, (50, 50), (100, 100), 255, -1)
    cv2.circle(img1, (150, 150), 30, 255, -1)

    img2 = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img2, (60, 60), (110, 110), 255, -1)
    cv2.circle(img2, (140, 140), 30, 255, -1)

    # 检测特征点
    detector = FeatureDetector(method='sift')
    kp1, des1 = detector.detect_and_compute(img1)
    kp2, des2 = detector.detect_and_compute(img2)

    # 匹配
    matcher = FeatureMatcher(method='bf', cross_check=True)
    matches = matcher.match(des1, des2)

    assert len(matches) > 0
    assert len(kp1) > 0
    assert len(kp2) > 0
```

## 4. 性能测试

```python
# test_performance.py
import time
import cv2
import numpy as np
from src.detector import FeatureDetector
from src.matcher import FeatureMatcher

def test_detection_speed():
    """测试检测速度"""
    img = cv2.imread('data/examples/test.jpg', cv2.IMREAD_GRAYSCALE)

    detector = FeatureDetector(method='sift')

    start = time.time()
    for _ in range(100):
        detector.detect(img)
    elapsed = time.time() - start

    print(f"SIFT检测速度: {elapsed/100*1000:.1f} ms/图像")

def test_matching_speed():
    """测试匹配速度"""
    desc1 = np.random.randn(1000, 128).astype(np.float32)
    desc2 = np.random.randn(1000, 128).astype(np.float32)

    # 暴力匹配
    matcher_bf = FeatureMatcher(method='bf', cross_check=False)
    start = time.time()
    matcher_bf.match(desc1, desc2)
    bf_time = time.time() - start

    # FLANN匹配
    matcher_flann = FeatureMatcher(method='flann')
    start = time.time()
    matcher_flann.match(desc1, desc2)
    flann_time = time.time() - start

    print(f"暴力匹配: {bf_time*1000:.1f} ms")
    print(f"FLANN匹配: {flann_time*1000:.1f} ms")
    print(f"加速比: {bf_time/flann_time:.1f}x")
```

## 5. 测试数据

### 测试图像生成
```python
def generate_test_images():
    """生成测试图像"""
    # 1. 简单几何图形
    img1 = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img1, (50, 50), (150, 150), 255, -1)

    # 2. 添加噪声
    img2 = img1.copy()
    noise = np.random.randn(200, 200) * 20
    img2 = np.clip(img2 + noise, 0, 255).astype(np.uint8)

    # 3. 轻微变换
    M = np.float32([[1, 0, 10], [0, 1, 10]])
    img3 = cv2.warpAffine(img1, M, (200, 200))

    return img1, img2, img3
```

## 6. 测试覆盖率

### 覆盖率目标
- 整体覆盖率 > 80%
- 核心模块覆盖率 > 90%

### 运行覆盖率测试
```bash
pytest --cov=src --cov-report=html tests/
```

### 覆盖率报告
```
Name                    Stmts   Miss  Cover
-------------------------------------------
src/detector.py            45      5    89%
src/descriptor.py          30      3    90%
src/matcher.py             50      8    84%
src/visualizer.py          40      6    85%
-------------------------------------------
TOTAL                     165     22    87%
```

## 7. 测试最佳实践

### 测试命名
- 使用描述性名称
- 格式: `test_<功能>_<场景>_<预期结果>`

### 测试数据
- 使用fixtures共享测试数据
- 避免硬编码
- 清理测试文件

### 断言
- 使用具体的断言
- 提供清晰的错误信息
- 检查边界条件

### 测试隔离
- 每个测试独立
- 不依赖外部资源
- 清理测试状态
