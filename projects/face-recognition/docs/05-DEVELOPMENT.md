# 面部识别开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- OpenCV 4.x
- PyTorch 1.9+
- NumPy 1.19+

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install opencv-python numpy torch torchvision pillow pytest
```

## 2. 开发流程

### 2.1 模块开发顺序

1. **工具函数 (utils.py)**：基础工具，无依赖
2. **人脸检测器 (face_detector.py)**：依赖 OpenCV
3. **特征提取器 (feature_extractor.py)**：依赖 PyTorch
4. **人脸识别器 (face_recognizer.py)**：依赖 NumPy

### 2.2 测试驱动开发

```python
# 1. 先写测试
def test_face_detector():
    detector = FaceDetector()
    image = create_test_image()
    faces = detector.detect(image)
    assert len(faces) > 0

# 2. 再实现功能
class FaceDetector:
    def detect(self, image):
        # 实现检测逻辑
        pass
```

## 3. 核心实现细节

### 3.1 MTCNN 实现

```python
class PNet(nn.Module):
    """Proposal Network"""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 10, 3, 1),
            nn.PReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(10, 16, 3, 1),
            nn.PReLU(),
            nn.Conv2d(16, 32, 3, 1),
            nn.PReLU()
        )
        self.conv4_1 = nn.Conv2d(32, 2, 1, 1)
        self.conv4_2 = nn.Conv2d(32, 4, 1, 1)

    def forward(self, x):
        x = self.features(x)
        label = torch.sigmoid(self.conv4_1(x))
        bbox = self.conv4_2(x)
        return label, bbox
```

### 3.2 Triplet Loss 实现

```python
class TripletLoss(nn.Module):
    """三元组损失函数"""

    def __init__(self, margin=0.2):
        super().__init__()
        self.margin = margin

    def forward(self, anchor, positive, negative):
        d_pos = torch.sum((anchor - positive) ** 2, dim=1)
        d_neg = torch.sum((anchor - negative) ** 2, dim=1)
        loss = torch.clamp(d_pos - d_neg + self.margin, min=0.0)
        return loss.mean()
```

### 3.3 人脸对齐实现

```python
def align_face(image, landmarks, target_size=(160, 160)):
    """人脸对齐"""
    # 获取眼睛位置
    left_eye = landmarks['left_eye']
    right_eye = landmarks['right_eye']

    # 计算旋转角度
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    angle = np.degrees(np.arctan2(dy, dx))

    # 计算中心点
    center = ((left_eye[0] + right_eye[0]) // 2,
              (left_eye[1] + right_eye[1]) // 2)

    # 计算缩放比例
    desired_left_eye = (0.35, 0.35)
    dist = np.sqrt(dx**2 + dy**2)
    desired_dist = (1 - 2 * desired_left_eye[0]) * target_size[0]
    scale = desired_dist / dist

    # 仿射变换
    M = cv2.getRotationMatrix2D(center, angle, scale)
    M[0, 2] += target_size[0] * 0.5 - center[0]
    M[1, 2] += target_size[1] * desired_left_eye[1] - center[1]

    aligned = cv2.warpAffine(image, M, target_size)
    return aligned
```

## 4. 优化技巧

### 4.1 数据增强

```python
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])
```

### 4.2 学习率调度

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=100, eta_min=1e-6
)
```

### 4.3 梯度裁剪

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

## 5. 调试技巧

### 5.1 可视化检测结果

```python
def visualize_detection(image, faces):
    """可视化检测结果"""
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.imshow('Detection', image)
    cv2.waitKey(0)
```

### 5.2 特征可视化

```python
def visualize_features(features, labels):
    """使用 t-SNE 可视化特征"""
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt

    tsne = TSNE(n_components=2, random_state=42)
    features_2d = tsne.fit_transform(features)

    plt.scatter(features_2d[:, 0], features_2d[:, 1], c=labels, cmap='tab10')
    plt.colorbar()
    plt.savefig('features_tsne.png')
```

### 5.3 距离分布分析

```python
def analyze_distances(features, labels):
    """分析正负样本距离分布"""
    positive_distances = []
    negative_distances = []

    for i in range(len(features)):
        for j in range(i+1, len(features)):
            dist = np.linalg.norm(features[i] - features[j])
            if labels[i] == labels[j]:
                positive_distances.append(dist)
            else:
                negative_distances.append(dist)

    plt.hist(positive_distances, bins=50, alpha=0.5, label='Positive')
    plt.hist(negative_distances, bins=50, alpha=0.5, label='Negative')
    plt.legend()
    plt.savefig('distance_distribution.png')
```

## 6. 常见问题

### 6.1 检测不到人脸

**可能原因**：
- 图像质量差
- 人脸太小
- 光照条件差

**解决方案**：
- 调整 `min_face_size` 参数
- 使用更敏感的检测器
- 预处理图像（直方图均衡化）

### 6.2 特征区分度低

**可能原因**：
- 模型未充分训练
- 损失函数不合适
- 数据集质量差

**解决方案**：
- 增加训练轮数
- 使用 ArcFace Loss
- 增加数据增强

### 6.3 识别速度慢

**可能原因**：
- 模型太大
- 数据库太大
- 未使用批量处理

**解决方案**：
- 使用模型压缩
- 使用 FAISS 索引
- 批量处理请求

## 7. 扩展功能

### 7.1 活体检测

```python
class LivenessDetector:
    """活体检测器"""

    def detect(self, image):
        # 检测眨眼
        # 检测头部运动
        # 分析纹理特征
        pass
```

### 7.2 情绪识别

```python
class EmotionRecognizer:
    """情绪识别器"""

    def __init__(self):
        self.emotions = ['happy', 'sad', 'angry', 'surprise', 'neutral']

    def recognize(self, face_image):
        # 使用 CNN 分类情绪
        pass
```

### 7.3 年龄性别识别

```python
class AgeGenderPredictor:
    """年龄性别预测器"""

    def predict(self, face_image):
        # 预测年龄和性别
        pass
```

## 8. 部署指南

### 8.1 Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

### 8.2 API 服务

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/detect', methods=['POST'])
def detect_faces():
    image = request.files['image']
    faces = detector.detect(image)
    return jsonify({'faces': faces})

@app.route('/identify', methods=['POST'])
def identify_face():
    image = request.files['image']
    # 识别逻辑
    return jsonify({'identity': identity, 'confidence': confidence})
```

## 9. 版本历史

- **v1.0.0**：基础人脸检测和识别
- **v1.1.0**：添加 MTCNN 检测器
- **v1.2.0**：添加批量处理
- **v2.0.0**：重构为模块化架构
