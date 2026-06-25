# 面部识别测试文档

## 1. 测试策略

### 1.1 测试层次

| 层次 | 测试内容 | 工具 |
|------|----------|------|
| 单元测试 | 各模块功能 | pytest |
| 集成测试 | 模块协作 | pytest |
| 性能测试 | 速度和准确率 | pytest-benchmark |

### 1.2 测试覆盖率目标

- 核心模块：> 90%
- 工具函数：> 85%
- 整体覆盖率：> 85%

## 2. 单元测试

### 2.1 人脸检测器测试

```python
class TestFaceDetector:
    """人脸检测器测试"""

    def test_detect_single_face(self):
        """测试检测单张人脸"""
        detector = FaceDetector(method="haar")
        image = create_test_image_with_face()
        faces = detector.detect(image)
        assert len(faces) == 1

    def test_detect_multiple_faces(self):
        """测试检测多张人脸"""
        detector = FaceDetector(method="haar")
        image = create_test_image_with_faces(3)
        faces = detector.detect(image)
        assert len(faces) == 3

    def test_detect_no_face(self):
        """测试无人脸图像"""
        detector = FaceDetector(method="haar")
        image = create_test_image_without_face()
        faces = detector.detect(image)
        assert len(faces) == 0

    def test_detect_returns_coordinates(self):
        """测试返回正确的坐标"""
        detector = FaceDetector(method="haar")
        image = create_test_image_with_face()
        faces = detector.detect(image)
        x, y, w, h = faces[0]
        assert x >= 0 and y >= 0
        assert w > 0 and h > 0

    def test_mtcnn_detector(self):
        """测试 MTCNN 检测器"""
        detector = FaceDetector(method="mtcnn")
        image = create_test_image_with_face()
        faces = detector.detect(image)
        assert len(faces) >= 1
```

### 2.2 特征提取器测试

```python
class TestFeatureExtractor:
    """特征提取器测试"""

    def test_extract_feature_shape(self):
        """测试特征向量形状"""
        extractor = FeatureExtractor(embedding_size=128)
        face = create_test_face()
        feature = extractor.extract(face)
        assert feature.shape == (128,)

    def test_extract_feature_normalized(self):
        """测试特征向量已归一化"""
        extractor = FeatureExtractor(embedding_size=128)
        face = create_test_face()
        feature = extractor.extract(face)
        norm = np.linalg.norm(feature)
        assert abs(norm - 1.0) < 1e-5

    def test_same_face_similar_features(self):
        """测试同一人脸特征相似"""
        extractor = FeatureExtractor(embedding_size=128)
        face1 = create_test_face(seed=42)
        face2 = create_test_face(seed=42)
        feat1 = extractor.extract(face1)
        feat2 = extractor.extract(face2)
        similarity = cosine_similarity(feat1, feat2)
        assert similarity > 0.9

    def test_different_face_different_features(self):
        """测试不同人脸特征不同"""
        extractor = FeatureExtractor(embedding_size=128)
        face1 = create_test_face(seed=42)
        face2 = create_test_face(seed=123)
        feat1 = extractor.extract(face1)
        feat2 = extractor.extract(face2)
        similarity = cosine_similarity(feat1, feat2)
        assert similarity < 0.8

    def test_batch_extract(self):
        """测试批量提取"""
        extractor = FeatureExtractor(embedding_size=128)
        faces = [create_test_face(seed=i) for i in range(4)]
        features = extractor.extract_batch(faces)
        assert features.shape == (4, 128)
```

### 2.3 人脸识别器测试

```python
class TestFaceRecognizer:
    """人脸识别器测试"""

    def test_add_face(self):
        """测试添加人脸"""
        recognizer = FaceRecognizer()
        feature = np.random.randn(128)
        recognizer.add_face("张三", feature)
        assert "张三" in recognizer.database

    def test_identify_known_face(self):
        """测试识别已知人脸"""
        recognizer = FaceRecognizer(threshold=0.5)
        feature = np.random.randn(128)
        feature = feature / np.linalg.norm(feature)
        recognizer.add_face("张三", feature)

        # 使用相似的特征查询
        query = feature + np.random.randn(128) * 0.1
        query = query / np.linalg.norm(query)
        identity, confidence = recognizer.identify(query)
        assert identity == "张三"
        assert confidence > 0.5

    def test_identify_unknown_face(self):
        """测试识别未知人脸"""
        recognizer = FaceRecognizer(threshold=0.8)
        feature = np.random.randn(128)
        feature = feature / np.linalg.norm(feature)
        recognizer.add_face("张三", feature)

        # 使用完全不同的特征查询
        query = np.random.randn(128)
        query = query / np.linalg.norm(query)
        identity, confidence = recognizer.identify(query)
        assert identity == "Unknown"

    def test_verify_same_person(self):
        """测试验证同一人"""
        recognizer = FaceRecognizer(threshold=0.5)
        feature = np.random.randn(128)
        feature = feature / np.linalg.norm(feature)

        # 添加微小扰动
        feat1 = feature + np.random.randn(128) * 0.01
        feat2 = feature + np.random.randn(128) * 0.01
        feat1 = feat1 / np.linalg.norm(feat1)
        feat2 = feat2 / np.linalg.norm(feat2)

        is_same, similarity = recognizer.verify(feat1, feat2)
        assert is_same == True
        assert similarity > 0.5

    def test_verify_different_person(self):
        """测试验证不同人"""
        recognizer = FaceRecognizer(threshold=0.8)
        feat1 = np.random.randn(128)
        feat2 = np.random.randn(128)
        feat1 = feat1 / np.linalg.norm(feat1)
        feat2 = feat2 / np.linalg.norm(feat2)

        is_same, similarity = recognizer.verify(feat1, feat2)
        assert is_same == False

    def test_remove_face(self):
        """测试移除人脸"""
        recognizer = FaceRecognizer()
        feature = np.random.randn(128)
        recognizer.add_face("张三", feature)
        recognizer.remove_face("张三")
        assert "张三" not in recognizer.database

    def test_save_load_database(self, tmp_path):
        """测试保存和加载数据库"""
        recognizer = FaceRecognizer()
        feature = np.random.randn(128)
        recognizer.add_face("张三", feature)

        # 保存
        save_path = tmp_path / "database.npz"
        recognizer.save_database(str(save_path))

        # 加载
        new_recognizer = FaceRecognizer()
        new_recognizer.load_database(str(save_path))
        assert "张三" in new_recognizer.database
```

## 3. 集成测试

### 3.1 完整流程测试

```python
class TestFaceRecognitionPipeline:
    """面部识别流程集成测试"""

    def test_full_pipeline(self):
        """测试完整识别流程"""
        # 初始化组件
        detector = FaceDetector(method="haar")
        extractor = FeatureExtractor(embedding_size=128)
        recognizer = FaceRecognizer(threshold=0.6)

        # 添加已知人脸
        known_image = load_image("known_face.jpg")
        faces = detector.detect(known_image)
        face = crop_face(known_image, faces[0])
        feature = extractor.extract(face)
        recognizer.add_face("张三", feature)

        # 识别新图像
        test_image = load_image("test_face.jpg")
        faces = detector.detect(test_image)
        assert len(faces) > 0

        face = crop_face(test_image, faces[0])
        feature = extractor.extract(face)
        identity, confidence = recognizer.identify(feature)

        print(f"识别结果: {identity}, 置信度: {confidence:.2f}")

    def test_batch_recognition(self):
        """测试批量识别"""
        detector = FaceDetector(method="haar")
        extractor = FeatureExtractor(embedding_size=128)

        # 批量检测
        images = [load_image(f"face_{i}.jpg") for i in range(10)]
        all_faces = []
        for image in images:
            faces = detector.detect(image)
            all_faces.extend(faces)

        # 批量特征提取
        face_images = [crop_face(images[i], face) for i, face in enumerate(all_faces)]
        features = extractor.extract_batch(face_images)
        assert features.shape[0] == len(all_faces)
```

## 4. 性能测试

### 4.1 速度测试

```python
class TestPerformance:
    """性能测试"""

    def test_detection_speed(self):
        """测试检测速度"""
        detector = FaceDetector(method="haar")
        image = create_large_image(1920, 1080)

        start = time.time()
        for _ in range(100):
            detector.detect(image)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        print(f"平均检测时间: {avg_time*1000:.2f}ms")
        assert avg_time < 0.1  # 100ms

    def test_extraction_speed(self):
        """测试特征提取速度"""
        extractor = FeatureExtractor(embedding_size=128)
        face = create_test_face()

        start = time.time()
        for _ in range(100):
            extractor.extract(face)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        print(f"平均提取时间: {avg_time*1000:.2f}ms")
        assert avg_time < 0.05  # 50ms

    def test_recognition_speed(self):
        """测试识别速度"""
        recognizer = FaceRecognizer()
        # 添加 1000 个人脸
        for i in range(1000):
            feature = np.random.randn(128)
            feature = feature / np.linalg.norm(feature)
            recognizer.add_face(f"person_{i}", feature)

        query = np.random.randn(128)
        query = query / np.linalg.norm(query)

        start = time.time()
        for _ in range(100):
            recognizer.identify(query)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        print(f"平均识别时间: {avg_time*1000:.2f}ms")
        assert avg_time < 0.01  # 10ms
```

### 4.2 准确率测试

```python
def test_accuracy():
    """测试识别准确率"""
    # 加载测试数据集
    test_pairs = load_test_pairs()  # [(img1, img2, is_same)]

    extractor = FeatureExtractor(embedding_size=128)
    recognizer = FaceRecognizer(threshold=0.6)

    correct = 0
    total = len(test_pairs)

    for img1, img2, is_same in test_pairs:
        feat1 = extractor.extract(img1)
        feat2 = extractor.extract(img2)
        result, _ = recognizer.verify(feat1, feat2)

        if result == is_same:
            correct += 1

    accuracy = correct / total
    print(f"准确率: {accuracy:.2%}")
    assert accuracy > 0.95
```

## 5. 测试数据

### 5.1 测试图像生成

```python
def create_test_image_with_face(size=(300, 300)):
    """创建包含人脸的测试图像"""
    image = np.ones((*size, 3), dtype=np.uint8) * 200

    # 绘制简单的脸部特征
    center = (size[0]//2, size[1]//2)
    cv2.circle(image, center, 80, (180, 150, 120), -1)  # 脸
    cv2.circle(image, (center[0]-25, center[1]-20), 8, (50, 50, 50), -1)  # 左眼
    cv2.circle(image, (center[0]+25, center[1]-20), 8, (50, 50, 50), -1)  # 右眼
    cv2.ellipse(image, (center[0], center[1]+20), (15, 8), 0, 0, 180, (50, 50, 50), 2)  # 嘴

    return image

def create_test_face(size=(160, 160), seed=None):
    """创建测试人脸图像"""
    if seed is not None:
        np.random.seed(seed)
    return np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
```

## 6. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_face_detector.py -v

# 运行并显示覆盖率
pytest tests/ -v --cov=src --cov-report=html

# 运行性能测试
pytest tests/test_performance.py -v -s
```
