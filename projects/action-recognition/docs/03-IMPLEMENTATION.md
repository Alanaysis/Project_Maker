# 03 - 实现细节

## 1. 空间特征提取实现

### 1.1 ResNet骨干网络

使用PyTorch的torchvision.models加载预训练ResNet，移除最后的全连接层：

```python
# 构建骨干网络
base_model = models.resnet18(weights="IMAGENET1K_V1")
self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])
```

**关键决策**：
- 使用`children()`而非`modules()`，确保正确分割
- 保留全局平均池化层，输出固定维度特征
- 对于VGG，额外添加AdaptiveAvgPool2d

### 1.2 特征维度投影

当需要自定义特征维度时，添加线性投影层：

```python
if feature_dim > 0 and feature_dim != backbone_dim:
    self.projection = nn.Linear(backbone_dim, feature_dim)
```

### 1.3 批量帧处理

将5D视频张量(B,T,C,H,W)reshape为4D(B*T,C,H,W)进行CNN前向传播：

```python
has_time_dim = x.dim() == 5
if has_time_dim:
    B, T, C, H, W = x.shape
    x = x.view(B * T, C, H, W)

features = self.feature_extractor(x)
features = features.flatten(1)

if has_time_dim:
    features = features.view(B, T, -1)
```

## 2. 时序建模实现

### 2.1 LSTM实现

```python
self.temporal_net = nn.LSTM(
    input_size=input_dim,
    hidden_size=hidden_dim,
    num_layers=num_layers,
    batch_first=True,
    dropout=dropout if num_layers > 1 else 0.0,
    bidirectional=bidirectional,
)
```

**关键点**：
- `batch_first=True`: 输入格式为(B, T, D)
- 多层LSTM之间应用Dropout
- 双向LSTM输出维度为hidden_dim * 2

### 2.2 变长序列处理

使用`pack_padded_sequence`处理变长序列：

```python
if lengths is not None:
    packed = nn.utils.rnn.pack_padded_sequence(
        x, lengths.cpu(), batch_first=True, enforce_sorted=False
    )
    output, hidden = self.temporal_net(packed)
    output, _ = nn.utils.rnn.pad_packed_sequence(output, batch_first=True)
```

### 2.3 Transformer实现

```python
encoder_layer = nn.TransformerEncoderLayer(
    d_model=input_dim,
    nhead=num_heads,
    dim_feedforward=hidden_dim * 4,
    dropout=dropout,
    batch_first=True,
)
self.temporal_net = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
```

**时序特征聚合**：
- LSTM/GRU: 使用最后时刻的隐藏状态
- Transformer: 对所有时刻的输出做平均池化

## 3. 端到端分类器实现

### 3.1 模型构建

```python
self.spatial_model = SpatialModel(backbone=backbone, pretrained=pretrained)
self.temporal_model = TemporalModel(input_dim=self.spatial_model.feature_dim, ...)
self.classifier = nn.Sequential(
    nn.Linear(self.temporal_model.output_dim, hidden_dim),
    nn.ReLU(inplace=True),
    nn.Dropout(dropout),
    nn.Linear(hidden_dim, num_classes),
)
```

### 3.2 前向传播

```python
def forward(self, video_clips, lengths=None):
    B, T, C, H, W = video_clips.shape
    spatial_features = self.spatial_model(video_clips)      # (B, T, feat_dim)
    temporal_features = self.temporal_model(spatial_features, lengths)  # (B, hidden)
    logits = self.classifier(temporal_features)              # (B, num_classes)
    return logits
```

## 4. 帧采样实现

### 4.1 均匀采样

```python
def _uniform_sample(self, total_frames):
    step = total_frames / self.num_frames
    indices = [int(step * i + step / 2) for i in range(self.num_frames)]
    return [min(idx, total_frames - 1) for idx in indices]
```

**设计决策**：
- 使用中心对齐而非左对齐，避免偏向视频开头
- 当视频帧数不足时，返回所有帧索引

### 4.2 密集采样

```python
def _dense_sample(self, total_frames):
    span = (self.num_frames - 1) * self.stride + 1
    max_start = total_frames - span
    start = random.randint(0, max_start)
    return [start + i * self.stride for i in range(self.num_frames)]
```

**特点**：
- 保持固定的时间间隔
- 随机起始位置增加多样性

### 4.3 时序抖动采样

```python
def _temporal_jitter_sample(self, total_frames):
    step = total_frames / self.num_frames
    jitter = step / 4  # +/- 25%抖动
    # 在均匀采样基础上添加随机偏移
```

**作用**：
- 训练时增加数据多样性
- 测试时使用均匀采样保证稳定性

## 5. 数据集实现

### 5.1 合成数据模式

用于测试和调试，无需真实视频数据：

```python
if synthetic:
    self.samples = [
        (f"synthetic_{i}", i % num_synthetic_classes)
        for i in range(num_synthetic_samples)
    ]
```

生成随机张量模拟视频帧：
```python
def _generate_synthetic_frames(self):
    C, H, W = 3, self.frame_size[0], self.frame_size[1]
    T = self.frame_sampler.num_frames
    return [torch.rand(C, H, W) for _ in range(T)]
```

### 5.2 视频文件加载

使用OpenCV读取视频帧：

```python
cap = cv2.VideoCapture(video_path)
cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
ret, frame = cap.read()
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
frame = cv2.resize(frame, (self.frame_size[1], self.frame_size[0]))
frame_tensor = torch.from_numpy(frame).float().permute(2, 0, 1) / 255.0
```

**关键处理**：
- BGR转RGB（OpenCV默认BGR）
- 归一化到[0, 1]
- 调整尺寸并转置为(C, H, W)

## 6. 特征提取管道实现

### 6.1 无梯度提取

```python
@torch.no_grad()
def extract_spatial(self, frames):
    frames = frames.to(self.device)
    return self.spatial_model(frames).cpu()
```

**设计决策**：
- 使用`@torch.no_grad()`节省内存
- 结果移到CPU避免GPU内存占用
- 模型设置为eval模式

### 6.2 特征缓存

```python
def save_features(self, features, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save(features, path)

def load_features(self, path):
    return torch.load(path, map_location="cpu")
```

## 7. 训练流程实现

### 7.1 训练循环

```python
for epoch in range(1, args.epochs + 1):
    train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
    val_loss, val_acc = validate(model, val_loader, criterion, device)
    scheduler.step()

    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), save_path)
```

### 7.2 损失函数

使用交叉熵损失：
```python
criterion = nn.CrossEntropyLoss()
loss = criterion(outputs, labels)
```

### 7.3 优化器

```python
optimizer = optim.Adam(model.parameters(), lr=args.lr)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
```

## 8. 已知限制

1. **内存限制**：长视频需要大量内存存储帧序列
2. **速度瓶颈**：OpenCV视频解码是IO瓶颈
3. **单GPU限制**：未实现分布式训练
4. **数据增强**：未实现视频级数据增强
