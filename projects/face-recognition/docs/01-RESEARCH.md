# 面部识别技术调研

## 1. 技术背景

面部识别是计算机视觉领域的重要应用，广泛应用于安防、身份验证、社交媒体等场景。

### 1.1 发展历史

| 时期 | 技术 | 特点 |
|------|------|------|
| 1990s | Eigenfaces | 基于 PCA 的经典方法 |
| 2000s | Fisherfaces | 基于 LDA 的改进方法 |
| 2012 | DeepFace | Facebook 的深度学习方法 |
| 2015 | FaceNet | Google 的三元组损失方法 |
| 2019 | ArcFace | 加性角度间隔损失 |

### 1.2 应用场景

- **安防监控**：实时人脸检测和识别
- **身份验证**：手机解锁、支付认证
- **社交媒体**：自动标签、人脸美化
- **智能零售**：客流统计、VIP 识别

## 2. 核心技术

### 2.1 人脸检测

#### Haar Cascade

- **原理**：使用 Haar 特征和级联分类器
- **优点**：速度快，易于实现
- **缺点**：对光照和姿态敏感

```python
# OpenCV Haar Cascade 示例
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray, 1.3, 5)
```

#### MTCNN (Multi-task Cascaded Convolutional Networks)

- **原理**：三个级联网络逐步精确定位
  - P-Net (Proposal Network): 生成候选区域
  - R-Net (Refinement Network): 过滤和精炼
  - O-Net (Output Network): 精确定位和关键点
- **优点**：准确率高，能检测小人脸
- **缺点**：速度较慢

#### RetinaFace

- **原理**：单阶段检测器，使用特征金字塔
- **优点**：速度快，准确率高
- **缺点**：需要 GPU 加速

### 2.2 人脸对齐

**目的**：将检测到的人脸标准化，消除姿态和位置差异。

**步骤**：
1. 检测关键点（眼睛、鼻子、嘴巴）
2. 计算仿射变换矩阵
3. 应用变换，裁剪和缩放

```python
def align_face(image, landmarks):
    # 计算眼睛中心
    left_eye = landmarks['left_eye']
    right_eye = landmarks['right_eye']

    # 计算旋转角度
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    angle = np.degrees(np.arctan2(dy, dx))

    # 仿射变换
    M = cv2.getRotationMatrix2D(center, angle, scale)
    aligned = cv2.warpAffine(image, M, (width, height))
    return aligned
```

### 2.3 特征提取

#### 传统方法

- **LBP (Local Binary Patterns)**：局部纹理特征
- **HOG (Histogram of Oriented Gradients)**：梯度方向直方图
- **Gabor 滤波器**：频率和方向特征

#### 深度学习方法

- **FaceNet**：使用 Inception 网络 + Triplet Loss
- **ArcFace**：使用 ResNet + Additive Angular Margin Loss
- **CosFace**：使用 Large Margin Cosine Loss

```python
# ArcFace 特征提取网络
class ArcFaceModel(nn.Module):
    def __init__(self, embedding_size=512):
        super().__init__()
        self.backbone = resnet50()
        self.fc = nn.Linear(2048, embedding_size)

    def forward(self, x):
        features = self.backbone(x)
        embedding = self.fc(features)
        embedding = F.normalize(embedding, p=2, dim=1)
        return embedding
```

### 2.4 特征匹配

#### 距离度量

- **欧氏距离**：`d = sqrt(sum((x1 - x2)^2))`
- **余弦相似度**：`cos = dot(x1, x2) / (||x1|| * ||x2||)`
- **马氏距离**：考虑特征协方差

#### 匹配策略

- **阈值法**：距离小于阈值则匹配
- **最近邻**：选择距离最小的已知人脸
- **KNN**：选择 K 个最近邻投票

### 2.5 损失函数

#### Triplet Loss

```python
def triplet_loss(anchor, positive, negative, margin=0.2):
    d_pos = torch.sum((anchor - positive) ** 2, dim=1)
    d_neg = torch.sum((anchor - negative) ** 2, dim=1)
    loss = torch.clamp(d_pos - d_neg + margin, min=0.0)
    return loss.mean()
```

#### ArcFace Loss

```python
def arcface_loss(cosine, labels, s=30.0, m=0.50):
    theta = torch.acos(cosine)
    one_hot = F.one_hot(labels, num_classes)
    margin_theta = theta + one_hot * m
    output = torch.cos(margin_theta) * s
    return F.cross_entropy(output, labels)
```

## 3. 开源方案对比

| 方案 | 检测 | 特征提取 | 准确率 | 速度 |
|------|------|----------|--------|------|
| dlib | HOG/CNN | ResNet | 99.38% | 中 |
| FaceNet | MTCNN | Inception | 99.63% | 慢 |
| InsightFace | RetinaFace | ArcFace | 99.83% | 快 |
| DeepFace | 多种 | 多种 | 99.5%+ | 中 |

## 4. 技术选型

### 4.1 本项目选择

| 组件 | 选择 | 理由 |
|------|------|------|
| 人脸检测 | MTCNN | 准确率高，有关键点输出 |
| 特征提取 | 自定义 CNN | 学习原理，可自定义 |
| 特征匹配 | 余弦相似度 | 计算简单，效果好 |

### 4.2 依赖库

- **OpenCV**：图像处理和 Haar Cascade
- **PyTorch**：深度学习框架
- **PIL/Pillow**：图像读取
- **NumPy**：数值计算

## 5. 参考文献

1. Schroff, F., et al. (2015). FaceNet: A Unified Embedding for Face Recognition and Clustering.
2. Zhang, K., et al. (2016). Joint Face Detection and Alignment Using Multitask Cascaded Convolutional Networks.
3. Deng, J., et al. (2019). ArcFace: Additive Angular Margin Loss for Deep Face Recognition.
4. Parkhi, O., et al. (2015). Deep Face Recognition.
