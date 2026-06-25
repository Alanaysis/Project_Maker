# 03 - 实现文档

## 1. 实现概述

### 1.1 技术栈

- **Python 3.8+**：主要编程语言
- **PyTorch 1.12+**：深度学习框架
- **torchvision 0.13+**：预训练模型和图像处理
- **OpenCV 4.5+**：视频读写和传统图像处理
- **NumPy 1.21+**：数值计算

### 1.2 代码统计

| 模块 | 文件 | 行数 | 功能 |
|------|------|------|------|
| data | frame_sampler.py | 98 | 帧采样策略 |
| data | video_dataset.py | 148 | 数据集加载 |
| models | feature_extractor.py | 157 | 特征提取器 |
| models | classifier.py | 116 | 内容分类器 |
| models | summarizer.py | 169 | 摘要生成器 |
| core | keyframe_extractor.py | 250 | 关键帧提取 |
| core | content_analyzer.py | 180 | 内容分析器 |
| utils | video_utils.py | 141 | 工具函数 |

## 2. 核心实现

### 2.1 帧采样器 (frame_sampler.py)

**关键实现**：

```python
def _uniform_sample(self, total: int, n: int) -> np.ndarray:
    """均匀采样"""
    return np.linspace(0, total - 1, n, dtype=int)
```

**实现细节**：
- 使用 `np.linspace` 保证首尾帧都被包含
- `dtype=int` 确保返回整数索引
- 自动处理 `n > total` 的情况

```python
def _random_sample(self, total: int, n: int) -> np.ndarray:
    """随机采样"""
    rng = np.random.RandomState(self.seed)
    indices = rng.choice(total, size=n, replace=False)
    return np.sort(indices)
```

**实现细节**：
- 使用 `RandomState` 而非全局随机，保证可重复性
- `replace=False` 确保不重复采样
- 返回排序后的索引

### 2.2 特征提取器 (feature_extractor.py)

**骨干网络构建**：

```python
def _build_backbone(self, name: str, pretrained: bool) -> tuple:
    if name == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        net = models.resnet18(weights=weights)
        out_dim = net.fc.in_features
        net.fc = nn.Identity()
    return net, out_dim
```

**关键技巧**：
- 使用 `nn.Identity()` 替换分类层，保留特征提取能力
- `net.fc.in_features` 获取正确的特征维度
- 支持预训练权重的动态加载

**帧特征提取**：

```python
def extract_frame_features(self, frames: torch.Tensor) -> torch.Tensor:
    squeeze = False
    if frames.dim() == 4:
        frames = frames.unsqueeze(0)
        squeeze = True

    B, T, C, H, W = frames.shape
    x = frames.view(B * T, C, H, W)  # 合并维度
    features = self.backbone(x)
    features = self.projection(features)
    features = features.view(B, T, -1)

    if squeeze:
        features = features.squeeze(0)
    return features
```

**关键技巧**：
- 合并 batch 和 time 维度，利用 GPU 并行
- 自动处理 4D 和 5D 输入
- 使用 `view` 而非 `reshape`，避免不必要的内存拷贝

**时序池化**：

```python
def temporal_pool(self, features: torch.Tensor) -> torch.Tensor:
    if self.pooling_type == "mean":
        pooled = features.mean(dim=1)
    elif self.pooling_type == "max":
        pooled = features.max(dim=1)[0]
    elif self.pooling_type == "attention":
        attn_scores = self.attention(features)
        attn_weights = torch.softmax(attn_scores, dim=1)
        pooled = (features * attn_weights).sum(dim=1)
    return pooled
```

**注意力池化细节**：
- 使用两层 MLP 计算注意力分数
- `softmax` 归一化确保权重和为 1
- 加权求和得到视频级特征

### 2.3 关键帧提取器 (keyframe_extractor.py)

**直方图差异计算**：

```python
def _extract_by_histogram(self, frames):
    histograms = []
    for frame in frames:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        histograms.append(hist.flatten())

    scores = [0.0]
    for i in range(1, len(histograms)):
        diff = cv2.compareHist(histograms[i-1], histograms[i], cv2.HISTCMP_BHATTACHARYYA)
        scores.append(diff)
```

**实现细节**：
- 使用 HSV 颜色空间，对光照变化更鲁棒
- 32x32 的直方图 bin，平衡精度和计算量
- Bhattacharyya 距离范围 [0, 1]，便于归一化

**光流计算**：

```python
def _extract_by_optical_flow(self, frames):
    gray_prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    scores = [0.0]
    for i in range(1, len(frames)):
        gray_curr = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(gray_prev, gray_curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        scores.append(magnitude.mean())
        gray_prev = gray_curr
```

**光流参数说明**：
- `0.5`：金字塔缩放比例
- `3`：金字塔层数
- `15`：窗口大小
- `3`：迭代次数
- `5`：多项式展开的邻域大小
- `1.2`：高斯标准差

**K-Means 聚类**：

```python
def _simple_kmeans(self, data, n_clusters, max_iter=50):
    indices = rng.choice(n_samples, size=n_clusters, replace=False)
    centroids = data[indices].copy()

    for _ in range(max_iter):
        distances = np.linalg.norm(data[:, np.newaxis] - centroids, axis=2)
        labels = np.argmin(distances, axis=1)

        new_centroids = np.zeros_like(centroids)
        for c in range(n_clusters):
            mask = labels == c
            if mask.any():
                new_centroids[c] = data[mask].mean(axis=0)
            else:
                new_centroids[c] = centroids[c]

        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    return centroids, labels
```

**实现细节**：
- 随机初始化聚类中心
- 处理空聚类（保持原中心）
- 收敛检查使用 `allclose`

### 2.4 内容分析器 (content_analyzer.py)

**完整分析流程**：

```python
def analyze_frames(self, frames: torch.Tensor) -> Dict:
    # 1. 特征提取
    frame_features = self.feature_extractor.extract_frame_features(frames)
    video_feature = self.feature_extractor.temporal_pool(frame_features)

    # 2. 内容分类
    frames_batch = frames.unsqueeze(0)
    predictions = self.classifier.predict(frames_batch)

    # 3. 重要性评分
    importance_scores = self.summarizer.compute_importance_scores(frames)

    # 4. 关键帧选取
    k = min(self.num_keyframes, frames.shape[0])
    top_indices = torch.topk(importance_scores, k).indices
    keyframe_indices = top_indices.sort().values.tolist()

    # 5. 组装结果
    return {
        "video_feature": video_feature.detach().numpy(),
        "frame_features": frame_features.detach().numpy(),
        "predictions": predictions[0],
        "importance_scores": importance_scores.detach().numpy().tolist(),
        "keyframe_indices": keyframe_indices,
    }
```

**片段检测**：

```python
def detect_segments(self, frames, min_segment_length=3):
    features = self.feature_extractor.extract_frame_features(frames)
    features_np = features.detach().numpy()

    distances = []
    for i in range(1, len(features_np)):
        dist = np.linalg.norm(features_np[i] - features_np[i-1])
        distances.append(dist)

    mean_dist = np.mean(distances)
    std_dist = np.std(distances)
    threshold = mean_dist + std_dist

    segments = []
    start = 0
    for i, dist in enumerate(distances):
        if dist > threshold and (i - start + 1) >= min_segment_length:
            segments.append((start, i))
            start = i + 1

    if start < frames.shape[0]:
        segments.append((start, frames.shape[0] - 1))

    return segments
```

**阈值选择**：
- 使用 `mean + std` 作为阈值
- 自适应于不同视频的内容差异
- `min_segment_length` 避免过短的片段

## 3. 工具函数实现

### 3.1 视频读取

```python
def load_video(video_path, max_frames=None):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()
    return frames
```

### 3.2 帧转张量

```python
def frames_to_tensor(frames, size=(224, 224), normalize=True):
    tensors = []
    for frame in frames:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (size[1], size[0]))
        frame_chw = frame_resized.transpose(2, 0, 1)
        tensors.append(frame_chw)

    tensor = np.stack(tensors, axis=0).astype(np.float32)
    if normalize:
        tensor = tensor / 255.0
    return torch.from_numpy(tensor)
```

**关键步骤**：
1. BGR → RGB 颜色空间转换
2. Resize 到目标大小
3. HWC → CHW 维度转换
4. 归一化到 [0, 1]

## 4. 训练流程实现

### 4.1 训练循环

```python
def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    for frames, labels in dataloader:
        frames, labels = frames.to(device), labels.to(device)
        optimizer.zero_grad()
        logits = model(frames)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
```

### 4.2 学习率调度

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
```

使用余弦退火调度，学习率从初始值平滑下降到 0。

## 5. 性能考虑

### 5.1 内存优化

- 使用 `torch.no_grad()` 禁用梯度计算
- 及时释放中间变量
- 使用 `detach()` 切断计算图

### 5.2 计算优化

- 合并 batch 和 time 维度，利用 GPU 并行
- 使用 `view` 而非 `reshape`
- 预计算特征并缓存

### 5.3 I/O 优化

- 使用 OpenCV 的 `VideoCapture` 流式读取
- 支持 `max_frames` 限制读取量
- 批量处理帧转换
