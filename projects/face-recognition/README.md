# 面部识别 (Face Recognition)

从零实现面部识别系统，深入理解人脸检测、特征提取和身份识别的核心原理。

## 学习目标

- **理解面部识别原理**：掌握从图像输入到身份识别的完整流程
- **掌握人脸检测**：学会使用 Haar Cascade 和 MTCNN 进行人脸定位
- **学会特征提取和匹配**：理解人脸特征向量的生成和相似度计算

## 核心循环

```
图像输入 → 人脸检测 → 特征提取 → 特征匹配 → 身份识别
```

1. **图像输入**：读取图片或视频帧
2. **人脸检测**：定位图像中的人脸区域
3. **特征提取**：将人脸区域转换为特征向量
4. **特征匹配**：计算与已知人脸特征的相似度
5. **身份识别**：根据相似度判断身份

## 项目结构

```
face-recognition/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── face_detector.py        # 人脸检测器
│   ├── feature_extractor.py    # 特征提取器
│   ├── face_recognizer.py      # 人脸识别器
│   └── utils.py                # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_face_detector.py   # 人脸检测测试
│   ├── test_feature_extractor.py # 特征提取测试
│   └── test_face_recognizer.py # 人脸识别测试
└── examples/
    ├── basic_detection.py      # 基础检测示例
    ├── face_comparison.py      # 人脸对比示例
    └── face_database.py        # 人脸数据库示例
```

## 快速开始

### 安装依赖

```bash
pip install opencv-python numpy torch torchvision pillow
```

### 基本使用

```python
from src import FaceDetector, FeatureExtractor, FaceRecognizer

# 1. 人脸检测
detector = FaceDetector(method="mtcnn")
image = cv2.imread("photo.jpg")
faces = detector.detect(image)

# 2. 特征提取
extractor = FeatureExtractor()
for face in faces:
    feature = extractor.extract(face)
    print(f"特征向量维度: {feature.shape}")

# 3. 人脸识别
recognizer = FaceRecognizer()
recognizer.add_face("张三", feature_zhang)
recognizer.add_face("李四", feature_li)

# 识别新的人脸
identity, confidence = recognizer.identify(feature_unknown)
print(f"识别结果: {identity}, 置信度: {confidence:.2f}")
```

### 人脸验证

```python
# 比较两张人脸是否为同一人
is_same, similarity = recognizer.verify(feature1, feature2)
if is_same:
    print(f"同一人，相似度: {similarity:.2f}")
else:
    print(f"不同人，相似度: {similarity:.2f}")
```

## 核心算法

### 1. 人脸检测 (MTCNN)

```python
class MTCNNDetector:
    """多任务级联卷积网络人脸检测"""

    def detect(self, image):
        # P-Net: 候选区域生成
        candidates = self.pnet(image)
        # R-Net: 候选区域过滤
        refined = self.rnet(candidates)
        # O-Net: 精确定位
        faces = self.onet(refined)
        return faces
```

**原理**：MTCNN 使用三个级联网络，逐步精确定位人脸，同时输出人脸关键点。

### 2. 特征提取 (Embedding Network)

```python
class EmbeddingNetwork(nn.Module):
    """人脸特征提取网络"""

    def forward(self, x):
        # 卷积层提取特征
        x = self.conv_layers(x)
        # 全连接层生成嵌入向量
        x = self.fc_layers(x)
        # L2 归一化
        x = F.normalize(x, p=2, dim=1)
        return x
```

**原理**：将人脸图像映射到高维特征空间，同一个人的不同照片在空间中距离较近。

### 3. 特征匹配

```python
def cosine_similarity(feature1, feature2):
    """计算余弦相似度"""
    return np.dot(feature1, feature2) / (
        np.linalg.norm(feature1) * np.linalg.norm(feature2)
    )
```

**原理**：通过计算特征向量的余弦相似度来衡量两个人脸的相似程度。

## 关键概念

### 人脸对齐 (Face Alignment)

- 检测人脸关键点（眼睛、鼻子、嘴巴）
- 根据关键点进行仿射变换
- 将人脸标准化到统一位置和大小

### Triplet Loss

- 使用锚点(Anchor)、正样本(Positive)、负样本(Negative)三元组
- 目标：使锚点与正样本的距离小于与负样本的距离
- 公式：L = max(d(a,p) - d(a,n) + margin, 0)

### 活体检测 (Anti-Spoofing)

- 检测是否为真实人脸而非照片
- 可使用眨眼检测、头部运动等方法
- 深度学习方法可检测纹理特征

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行人脸检测测试
pytest tests/test_face_detector.py -v

# 运行特征提取测试
pytest tests/test_feature_extractor.py -v

# 运行识别测试
pytest tests/test_face_recognizer.py -v
```

## 参考资料

- [FaceNet: A Unified Embedding for Face Recognition and Clustering (2015)](https://arxiv.org/abs/1503.03832)
- [MTCNN Joint Face Detection and Alignment (2016)](https://arxiv.org/abs/1604.02878)
- [ArcFace: Additive Angular Margin Loss (2019)](https://arxiv.org/abs/1801.07698)
- [OpenCV Face Detection](https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html)

## License

This project is for educational purposes.

---

[返回 CV 模块](../CV_README.md) | [返回主目录](../../README.md)
