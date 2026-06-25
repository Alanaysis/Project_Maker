# 面部识别实现文档

## 1. 环境配置

### 1.1 依赖安装

```bash
pip install opencv-python numpy torch torchvision pillow
```

### 1.2 目录结构

```
face-recognition/
├── src/
│   ├── __init__.py
│   ├── face_detector.py
│   ├── feature_extractor.py
│   ├── face_recognizer.py
│   └── utils.py
└── tests/
```

## 2. 核心实现

### 2.1 人脸检测器 (face_detector.py)

#### Haar Cascade 检测器

```python
class HaarDetector:
    """基于 Haar Cascade 的人脸检测器"""

    def __init__(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return [(x, y, w, h) for (x, y, w, h) in faces]
```

#### MTCNN 检测器

```python
class MTCNNDetector:
    """基于 MTCNN 的人脸检测器"""

    def __init__(self):
        self.pnet = PNet()
        self.rnet = RNet()
        self.onet = ONet()

    def detect(self, image):
        # 1. P-Net: 生成候选区域
        candidates = self._pnet_detect(image)

        # 2. R-Net: 过滤候选区域
        refined = self._rnet_detect(image, candidates)

        # 3. O-Net: 精确定位
        faces = self._onet_detect(image, refined)

        return faces
```

### 2.2 特征提取器 (feature_extractor.py)

#### 自定义 CNN 网络

```python
class FaceEmbeddingNet(nn.Module):
    """人脸特征提取网络"""

    def __init__(self, embedding_size=128):
        super().__init__()

        # 卷积层
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )

        # 全连接层
        self.fc_layers = nn.Sequential(
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, embedding_size)
        )

    def forward(self, x):
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        x = self.fc_layers(x)
        # L2 归一化
        x = F.normalize(x, p=2, dim=1)
        return x
```

#### 特征提取流程

```python
class FeatureExtractor:
    """特征提取器"""

    def __init__(self, model_type="custom", embedding_size=128):
        self.embedding_size = embedding_size
        self.model = self._build_model(model_type)
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def extract(self, face_image):
        # 预处理
        tensor = self.transform(face_image)
        tensor = tensor.unsqueeze(0)

        # 提取特征
        with torch.no_grad():
            feature = self.model(tensor)

        return feature.numpy().flatten()
```

### 2.3 人脸识别器 (face_recognizer.py)

#### 人脸识别器实现

```python
class FaceRecognizer:
    """人脸识别器"""

    def __init__(self, threshold=0.6):
        self.threshold = threshold
        self.database = {}

    def add_face(self, name, feature):
        """添加人脸到数据库"""
        if name not in self.database:
            self.database[name] = []
        self.database[name].append(feature)

    def identify(self, feature):
        """识别未知人脸"""
        best_match = None
        best_similarity = -1

        for name, features in self.database.items():
            for db_feature in features:
                similarity = self._cosine_similarity(feature, db_feature)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = name

        if best_similarity >= self.threshold:
            return best_match, best_similarity
        return "Unknown", best_similarity

    def verify(self, feature1, feature2):
        """验证两张人脸是否为同一人"""
        similarity = self._cosine_similarity(feature1, feature2)
        return similarity >= self.threshold, similarity

    def _cosine_similarity(self, feature1, feature2):
        """计算余弦相似度"""
        dot_product = np.dot(feature1, feature2)
        norm1 = np.linalg.norm(feature1)
        norm2 = np.linalg.norm(feature2)
        return dot_product / (norm1 * norm2)
```

### 2.4 工具函数 (utils.py)

```python
def preprocess_image(image, target_size=(160, 160)):
    """图像预处理"""
    # 调整大小
    image = cv2.resize(image, target_size)
    # 归一化
    image = image.astype(np.float32) / 255.0
    return image

def draw_faces(image, faces, identities=None):
    """在图像上绘制人脸框"""
    for i, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        if identities:
            label = identities[i]
            cv2.putText(image, label, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    return image

def save_feature_database(database, path):
    """保存特征数据库"""
    np.savez(path, **database)

def load_feature_database(path):
    """加载特征数据库"""
    data = np.load(path)
    return dict(data)
```

## 3. 训练流程

### 3.1 数据准备

```python
def prepare_triplet_dataset(dataset_path):
    """准备三元组数据集"""
    triplets = []

    # 遍历每个人的文件夹
    for person_dir in os.listdir(dataset_path):
        person_path = os.path.join(dataset_path, person_dir)
        images = os.listdir(person_path)

        # 生成三元组
        for i in range(len(images)):
            anchor = os.path.join(person_path, images[i])
            positive = os.path.join(person_path, images[(i+1) % len(images)])

            # 随机选择不同人的图片作为负样本
            other_persons = [p for p in os.listdir(dataset_path) if p != person_dir]
            negative_person = np.random.choice(other_persons)
            negative = os.path.join(dataset_path, negative_person,
                                   np.random.choice(os.listdir(os.path.join(dataset_path, negative_person))))

            triplets.append((anchor, positive, negative))

    return triplets
```

### 3.2 训练循环

```python
def train(model, train_loader, optimizer, criterion, epochs=100):
    """训练模型"""
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for anchor, positive, negative in train_loader:
            # 前向传播
            anchor_feat = model(anchor)
            positive_feat = model(positive)
            negative_feat = model(negative)

            # 计算损失
            loss = criterion(anchor_feat, positive_feat, negative_feat)

            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
```

## 4. 性能优化

### 4.1 批量处理

```python
def extract_batch_features(extractor, face_images, batch_size=32):
    """批量提取特征"""
    features = []
    for i in range(0, len(face_images), batch_size):
        batch = face_images[i:i+batch_size]
        batch_tensor = torch.stack([transform(img) for img in batch])
        with torch.no_grad():
            batch_features = extractor.model(batch_tensor)
        features.append(batch_features.numpy())
    return np.vstack(features)
```

### 4.2 特征索引

```python
class FeatureIndex:
    """特征索引，用于快速检索"""

    def __init__(self, dimension=128):
        self.dimension = dimension
        self.index = {}  # 简单实现，生产环境可用 FAISS

    def add(self, name, feature):
        self.index[name] = feature

    def search(self, query_feature, top_k=5):
        similarities = []
        for name, feature in self.index.items():
            sim = cosine_similarity(query_feature, feature)
            similarities.append((name, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
```

## 5. 部署配置

### 5.1 模型导出

```python
def export_to_onnx(model, output_path):
    """导出模型为 ONNX 格式"""
    dummy_input = torch.randn(1, 3, 160, 160)
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        input_names=['input'],
        output_names=['output']
    )
```

### 5.2 配置文件

```yaml
# config.yaml
detector:
  method: mtcnn
  min_face_size: 20
  thresholds: [0.6, 0.7, 0.7]

extractor:
  model_type: custom
  embedding_size: 128
  model_path: models/face_embedding.pth

recognizer:
  threshold: 0.6
  distance_metric: cosine
  database_path: data/face_database/
```
