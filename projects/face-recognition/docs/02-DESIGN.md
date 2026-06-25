# 面部识别系统设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    面部识别系统                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐    │
│  │ 图像输入 │ → │ 人脸检测 │ → │ 特征提取 │ → │ 身份识别 │    │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘    │
│       ↓             ↓             ↓             ↓          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   核心处理引擎                        │   │
│  └─────────────────────────────────────────────────────┘   │
│       ↓             ↓             ↓             ↓          │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐    │
│  │ OpenCV  │   │ MTCNN   │   │ CNN网络 │   │ 特征数据库│    │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
face-recognition/
├── src/
│   ├── __init__.py              # 包初始化
│   ├── face_detector.py         # 人脸检测模块
│   ├── feature_extractor.py     # 特征提取模块
│   ├── face_recognizer.py       # 人脸识别模块
│   └── utils.py                 # 工具函数
├── tests/                       # 测试模块
└── examples/                    # 示例代码
```

## 2. 核心类设计

### 2.1 FaceDetector (人脸检测器)

```python
class FaceDetector:
    """人脸检测器基类"""

    def __init__(self, method="mtcnn"):
        """
        初始化检测器

        Args:
            method: 检测方法 ("haar", "mtcnn")
        """
        self.method = method
        self._init_detector()

    def _init_detector(self):
        """初始化具体的检测器"""
        if self.method == "haar":
            self.detector = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
        elif self.method == "mtcnn":
            self.detector = MTCNN()

    def detect(self, image):
        """
        检测图像中的人脸

        Args:
            image: 输入图像 (numpy array)

        Returns:
            List[Face]: 检测到的人脸列表
        """
        pass

    def detect_and_crop(self, image, target_size=(160, 160)):
        """
        检测并裁剪人脸

        Args:
            image: 输入图像
            target_size: 目标大小

        Returns:
            List[numpy array]: 裁剪后的人脸图像列表
        """
        pass
```

### 2.2 FeatureExtractor (特征提取器)

```python
class FeatureExtractor:
    """人脸特征提取器"""

    def __init__(self, model_type="custom", embedding_size=128):
        """
        初始化特征提取器

        Args:
            model_type: 模型类型 ("custom", "resnet")
            embedding_size: 特征向量维度
        """
        self.model_type = model_type
        self.embedding_size = embedding_size
        self.model = self._build_model()

    def _build_model(self):
        """构建特征提取网络"""
        pass

    def extract(self, face_image):
        """
        提取人脸特征

        Args:
            face_image: 人脸图像 (已裁剪和对齐)

        Returns:
            numpy array: 特征向量
        """
        pass

    def extract_batch(self, face_images):
        """
        批量提取特征

        Args:
            face_images: 人脸图像列表

        Returns:
            numpy array: 特征向量矩阵
        """
        pass
```

### 2.3 FaceRecognizer (人脸识别器)

```python
class FaceRecognizer:
    """人脸识别器"""

    def __init__(self, threshold=0.6):
        """
        初始化识别器

        Args:
            threshold: 匹配阈值
        """
        self.threshold = threshold
        self.database = {}  # {name: [features]}

    def add_face(self, name, feature):
        """
        添加人脸到数据库

        Args:
            name: 人名
            feature: 特征向量
        """
        pass

    def remove_face(self, name):
        """从数据库移除人脸"""
        pass

    def identify(self, feature):
        """
        识别未知人脸

        Args:
            feature: 特征向量

        Returns:
            Tuple[str, float]: (身份, 置信度)
        """
        pass

    def verify(self, feature1, feature2):
        """
        验证两张人脸是否为同一人

        Args:
            feature1: 特征向量 1
            feature2: 特征向量 2

        Returns:
            Tuple[bool, float]: (是否匹配, 相似度)
        """
        pass

    def save_database(self, path):
        """保存数据库到文件"""
        pass

    def load_database(self, path):
        """从文件加载数据库"""
        pass
```

## 3. 数据流设计

### 3.1 检测流程

```python
def detection_pipeline(image):
    # 1. 预处理
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 2. 人脸检测
    faces = detector.detect(image_rgb)

    # 3. 人脸裁剪和对齐
    cropped_faces = []
    for face in faces:
        x, y, w, h = face.bbox
        cropped = image_rgb[y:y+h, x:x+w]
        cropped = cv2.resize(cropped, (160, 160))
        cropped_faces.append(cropped)

    return faces, cropped_faces
```

### 3.2 识别流程

```python
def recognition_pipeline(image):
    # 1. 检测人脸
    faces, cropped_faces = detection_pipeline(image)

    # 2. 提取特征
    features = []
    for face in cropped_faces:
        feature = extractor.extract(face)
        features.append(feature)

    # 3. 识别身份
    results = []
    for feature in features:
        identity, confidence = recognizer.identify(feature)
        results.append((identity, confidence))

    return results
```

## 4. 存储设计

### 4.1 人脸数据库结构

```python
face_database = {
    "张三": {
        "features": [
            np.array([0.1, 0.2, ...]),  # 特征向量 1
            np.array([0.15, 0.25, ...]), # 特征向量 2
        ],
        "metadata": {
            "added_date": "2024-01-01",
            "num_samples": 2
        }
    },
    "李四": {
        "features": [...],
        "metadata": {...}
    }
}
```

### 4.2 文件存储格式

- **JSON**: 存储元数据和配置
- **NPZ**: 存储特征向量
- **目录结构**:
  ```
  face_db/
  ├── metadata.json
  ├── 张三/
  │   ├── features.npz
  │   └── images/
  └── 李四/
      ├── features.npz
      └── images/
  ```

## 5. 接口设计

### 5.1 命令行接口

```bash
# 人脸检测
python -m face_recognition detect --input photo.jpg --output result.jpg

# 添加人脸到数据库
python -m face_recognition add --name "张三" --images photos/zhang/*.jpg

# 识别图像中的人脸
python -m face_recognition identify --input photo.jpg

# 验证两张人脸
python -m face_recognition verify --face1 img1.jpg --face2 img2.jpg
```

### 5.2 Python API

```python
from face_recognition import FaceDetector, FeatureExtractor, FaceRecognizer

# 初始化
detector = FaceDetector(method="mtcnn")
extractor = FeatureExtractor(model_type="custom")
recognizer = FaceRecognizer(threshold=0.6)

# 检测
faces = detector.detect(image)

# 提取特征
feature = extractor.extract(face_image)

# 识别
identity, confidence = recognizer.identify(feature)
```

## 6. 性能设计

### 6.1 性能目标

| 指标 | 目标值 |
|------|--------|
| 检测速度 | < 100ms / 图像 |
| 特征提取 | < 50ms / 人脸 |
| 识别速度 | < 10ms / 查询 |
| 准确率 | > 95% |

### 6.2 优化策略

1. **批量处理**：同时处理多张图像
2. **模型优化**：使用 ONNX 或 TensorRT 加速
3. **索引优化**：使用 FAISS 进行快速特征检索
4. **缓存机制**：缓存已提取的特征

## 7. 错误处理

### 7.1 异常类型

```python
class FaceDetectionError(Exception):
    """人脸检测失败"""
    pass

class NoFaceFoundError(FaceDetectionError):
    """未检测到人脸"""
    pass

class MultipleFacesError(FaceDetectionError):
    """检测到多张人脸"""
    pass

class FeatureExtractionError(Exception):
    """特征提取失败"""
    pass
```

### 7.2 错误处理策略

```python
def safe_detect(image):
    try:
        faces = detector.detect(image)
        if len(faces) == 0:
            raise NoFaceFoundError("未检测到人脸")
        if len(faces) > 1:
            logger.warning(f"检测到 {len(faces)} 张人脸")
        return faces
    except Exception as e:
        logger.error(f"检测失败: {e}")
        raise
```

## 8. 扩展性设计

### 8.1 插件化检测器

```python
class DetectorFactory:
    """检测器工厂"""

    @staticmethod
    def create(method):
        if method == "haar":
            return HaarDetector()
        elif method == "mtcnn":
            return MTCNNDetector()
        elif method == "retinaface":
            return RetinaFaceDetector()
        else:
            raise ValueError(f"Unknown method: {method}")
```

### 8.2 可配置参数

```python
config = {
    "detector": {
        "method": "mtcnn",
        "min_face_size": 20,
        "thresholds": [0.6, 0.7, 0.7]
    },
    "extractor": {
        "model_type": "custom",
        "embedding_size": 128,
        "pretrained": True
    },
    "recognizer": {
        "threshold": 0.6,
        "distance_metric": "cosine"
    }
}
```
