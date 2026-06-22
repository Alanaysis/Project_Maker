# 03 - 实现细节文档

## 核心算法实现

### 1. PointPillars 编码器

#### 算法原理

PointPillars 的核心思想是将 3D 点云转换为 2D 伪图像，然后使用 2D CNN 进行处理。

**步骤**:
1. 将点云空间划分为网格 (Pillars)
2. 将每个 Pillar 内的点特征聚合
3. 生成伪图像

#### 实现代码

```python
class PillarEncoder(nn.Module):
    def __init__(self, voxel_size, point_cloud_range, 
                 max_points_per_pillar=32, max_pillars=12000):
        super().__init__()
        self.voxel_size = voxel_size
        self.point_cloud_range = point_cloud_range
        self.max_points = max_points_per_pillar
        self.max_pillars = max_pillars
        
        # 计算网格尺寸
        self.x_size = int((point_cloud_range[3] - point_cloud_range[0]) / voxel_size[0])
        self.y_size = int((point_cloud_range[4] - point_cloud_range[1]) / voxel_size[1])
        
        # 特征提取网络
        self.feature_net = nn.Sequential(
            nn.Linear(9, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, 64)
        )
    
    def forward(self, points):
        """
        Args:
            points: (B, N, C) 点云数据
        Returns:
            pillars: (B, D, H, W) 伪图像
        """
        batch_size = points.shape[0]
        
        # 1. 点云转 Pillars
        pillars, coords, num_points = self._create_pillars(points)
        
        # 2. Pillar 特征提取
        pillar_features = self._extract_features(pillars, num_points)
        
        # 3. 生成伪图像
        pseudo_image = self._scatter_to_image(pillar_features, coords)
        
        return pseudo_image
    
    def _create_pillars(self, points):
        """将点云组织成 Pillars"""
        # 实现细节...
        pass
    
    def _extract_features(self, pillars, num_points):
        """提取 Pillar 特征"""
        # 实现细节...
        pass
    
    def _scatter_to_image(self, features, coords):
        """将 Pillar 特征散射到图像"""
        # 实现细节...
        pass
```

#### 关键点

1. **点特征增强**: 每个点的特征包括:
   - 原始坐标 (x, y, z)
   - 反射强度 (r)
   - 相对于 Pillar 中心的偏移 (xc, yc, zc)
   - 相对于 Pillar 内所有点平均值的偏移 (xp, yp, zp)

2. **Pillar 特征聚合**: 使用最大池化聚合每个 Pillar 内的点特征

3. **伪图像生成**: 将 Pillar 特征散射到对应的网格位置

### 2. 2D 骨干网络

#### 网络结构

```
输入: (B, 64, H, W)
        │
        ▼
┌─────────────────────────────┐
│  Block 1: 64 通道           │
│  - Conv2d(64, 64, 3, 2)    │
│  - BatchNorm2d(64)          │
│  - ReLU                     │
│  × 2 层                    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Block 2: 128 通道          │
│  - Conv2d(64, 128, 3, 2)   │
│  - BatchNorm2d(128)         │
│  - ReLU                     │
│  × 2 层                    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Block 3: 256 通道          │
│  - Conv2d(128, 256, 3, 2)  │
│  - BatchNorm2d(256)         │
│  - ReLU                     │
│  × 2 层                    │
└────────────┬────────────────┘
             │
             ▼
输出: 多尺度特征图
```

#### 实现代码

```python
class Backbone2D(nn.Module):
    def __init__(self, in_channels=64):
        super().__init__()
        
        self.block1 = self._make_block(in_channels, 64, num_blocks=2)
        self.block2 = self._make_block(64, 128, num_blocks=2)
        self.block3 = self._make_block(128, 256, num_blocks=2)
    
    def _make_block(self, in_channels, out_channels, num_blocks):
        """创建卷积块"""
        layers = []
        for i in range(num_blocks):
            if i == 0:
                stride = 2  # 第一个卷积下采样
            else:
                stride = 1
            layers.extend([
                nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU()
            ])
            in_channels = out_channels
        return nn.Sequential(*layers)
    
    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) 输入特征图
        Returns:
            多尺度特征图列表
        """
        x1 = self.block1(x)   # 1/2 分辨率
        x2 = self.block2(x1)  # 1/4 分辨率
        x3 = self.block3(x2)  # 1/8 分辨率
        
        return [x1, x2, x3]
```

### 3. 特征金字塔网络 (FPN)

#### 网络结构

```
输入: 多尺度特征图 [C2, C3, C4]
        │
        ▼
┌─────────────────────────────┐
│  自顶向下路径               │
│  - 上采样                   │
│  - 1×1 卷积                 │
│  - 元素相加                 │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  横向连接                   │
│  - 3×3 卷积                 │
│  - 消除混叠效应             │
└────────────┬────────────────┘
             │
             ▼
输出: 融合特征图
```

#### 实现代码

```python
class FPN(nn.Module):
    def __init__(self, in_channels_list, out_channels):
        super().__init__()
        
        self.lateral_convs = nn.ModuleList()
        self.output_convs = nn.ModuleList()
        
        for in_channels in in_channels_list:
            self.lateral_convs.append(
                nn.Conv2d(in_channels, out_channels, 1)
            )
            self.output_convs.append(
                nn.Conv2d(out_channels, out_channels, 3, padding=1)
            )
    
    def forward(self, features):
        """
        Args:
            features: 多尺度特征图列表
        Returns:
            融合后的特征图列表
        """
        laterals = [
            conv(feat) 
            for conv, feat in zip(self.lateral_convs, features)
        ]
        
        # 自顶向下路径
        for i in range(len(laterals) - 1, 0, -1):
            laterals[i - 1] += F.interpolate(
                laterals[i], 
                size=laterals[i - 1].shape[2:],
                mode='nearest'
            )
        
        # 输出卷积
        outputs = [
            conv(feat) 
            for conv, feat in zip(self.output_convs, laterals)
        ]
        
        return outputs
```

### 4. 检测头

#### Anchor 设计

```python
# KITTI 数据集的 Anchor 配置
anchors = {
    'Car': {
        'size': [1.6, 3.9, 1.56],  # 宽、长、高
        'rotation': [0, 1.57],  # 0度和90度
    },
    'Pedestrian': {
        'size': [0.6, 0.8, 1.73],
        'rotation': [0, 1.57],
    },
    'Cyclist': {
        'size': [0.6, 1.76, 1.73],
        'rotation': [0, 1.57],
    }
}
```

#### 实现代码

```python
class DetectionHead(nn.Module):
    def __init__(self, in_channels, num_classes, num_anchors_per_location):
        super().__init__()
        self.num_classes = num_classes
        self.num_anchors = num_anchors_per_location
        
        # 分类分支
        self.cls_head = nn.Conv2d(
            in_channels,
            num_anchors_per_location * num_classes,
            kernel_size=1
        )
        
        # 回归分支 (x, y, z, w, l, h, θ)
        self.reg_head = nn.Conv2d(
            in_channels,
            num_anchors_per_location * 7,
            kernel_size=1
        )
        
        # 方向分类分支
        self.dir_head = nn.Conv2d(
            in_channels,
            num_anchors_per_location * 2,
            kernel_size=1
        )
    
    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) 特征图
        Returns:
            cls_score: 分类分数
            bbox_pred: 边界框预测
            dir_pred: 方向预测
        """
        cls_score = self.cls_head(x)
        bbox_pred = self.reg_head(x)
        dir_pred = self.dir_head(x)
        
        return cls_score, bbox_pred, dir_pred
```

### 5. 损失函数

#### Focal Loss

```python
class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
    
    def forward(self, pred, target):
        """
        Args:
            pred: (N, C) 预测分数
            target: (N,) 目标标签
        Returns:
            loss: 焦点损失
        """
        ce_loss = F.cross_entropy(pred, target, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss.mean()
```

#### Smooth L1 Loss

```python
class SmoothL1Loss(nn.Module):
    def __init__(self, beta=1.0):
        super().__init__()
        self.beta = beta
    
    def forward(self, pred, target):
        """
        Args:
            pred: (N, 7) 预测边界框
            target: (N, 7) 目标边界框
        Returns:
            loss: 平滑 L1 损失
        """
        diff = torch.abs(pred - target)
        loss = torch.where(
            diff < self.beta,
            0.5 * diff ** 2 / self.beta,
            diff - 0.5 * self.beta
        )
        return loss.mean()
```

### 6. 后处理

#### NMS 实现

```python
def nms_3d(boxes, scores, iou_threshold=0.5):
    """
    3D 非极大值抑制
    
    Args:
        boxes: (N, 7) 3D 边界框 [x, y, z, w, l, h, θ]
        scores: (N,) 置信度分数
        iou_threshold: IoU 阈值
    Returns:
        keep: 保留的边界框索引
    """
    # 1. 按分数排序
    order = scores.argsort()[::-1]
    
    # 2. 计算 BEV IoU
    keep = []
    while order.numel() > 0:
        i = order[0]
        keep.append(i)
        
        if order.numel() == 1:
            break
        
        # 计算当前框与其他框的 IoU
        ious = compute_bev_iou(
            boxes[i:i+1], 
            boxes[order[1:]]
        )
        
        # 保留 IoU 小于阈值的框
        mask = ious < iou_threshold
        order = order[1:][mask]
    
    return torch.tensor(keep, dtype=torch.long)
```

#### 边界框解码

```python
def decode_boxes(anchors, preds):
    """
    解码预测的边界框
    
    Args:
        anchors: (N, 7) Anchor 框
        preds: (N, 7) 预测值
    Returns:
        boxes: (N, 7) 解码后的边界框
    """
    # 解码公式
    # x = pred_x * anchor_w + anchor_x
    # y = pred_y * anchor_l + anchor_y
    # z = pred_z * anchor_h + anchor_z
    # w = anchor_w * exp(pred_w)
    # l = anchor_l * exp(pred_l)
    # h = anchor_h * exp(pred_h)
    # θ = pred_θ + anchor_θ
    
    xa, ya, za, wa, la, ha, ra = anchors.split(1, dim=-1)
    xp, yp, zp, wp, lp, hp, rp = preds.split(1, dim=-1)
    
    x = xp * wa + xa
    y = yp * la + ya
    z = zp * ha + za
    w = wa * torch.exp(wp)
    l = la * torch.exp(lp)
    h = ha * torch.exp(hp)
    r = rp + ra
    
    return torch.cat([x, y, z, w, l, h, r], dim=-1)
```

## 数据增强实现

### 1. 随机翻转

```python
def random_flip(points, boxes, prob=0.5):
    """
    随机沿 X 轴或 Y 轴翻转
    
    Args:
        points: (N, C) 点云
        boxes: (M, 7) 边界框
        prob: 翻转概率
    Returns:
        翻转后的点云和边界框
    """
    if random.random() < prob:
        # 沿 X 轴翻转
        points[:, 0] = -points[:, 0]
        boxes[:, 0] = -boxes[:, 0]
        boxes[:, 6] = -boxes[:, 6]  # 角度取反
    
    if random.random() < prob:
        # 沿 Y 轴翻转
        points[:, 1] = -points[:, 1]
        boxes[:, 1] = -boxes[:, 1]
        boxes[:, 6] = -boxes[:, 6]  # 角度取反
    
    return points, boxes
```

### 2. 随机旋转

```python
def random_rotation(points, boxes, range=(-0.78, 0.78)):
    """
    随机旋转点云
    
    Args:
        points: (N, C) 点云
        boxes: (M, 7) 边界框
        range: 旋转角度范围 (弧度)
    Returns:
        旋转后的点云和边界框
    """
    angle = random.uniform(*range)
    
    # 旋转矩阵
    cos_val = np.cos(angle)
    sin_val = np.sin(angle)
    rot_matrix = np.array([
        [cos_val, -sin_val, 0],
        [sin_val, cos_val, 0],
        [0, 0, 1]
    ])
    
    # 旋转点云
    points[:, :3] = points[:, :3] @ rot_matrix.T
    
    # 旋转边界框中心
    boxes[:, :3] = boxes[:, :3] @ rot_matrix.T
    
    # 更新角度
    boxes[:, 6] += angle
    
    return points, boxes
```

### 3. 随机缩放

```python
def random_scaling(points, boxes, range=(0.95, 1.05)):
    """
    随机缩放点云
    
    Args:
        points: (N, C) 点云
        boxes: (M, 7) 边界框
        range: 缩放范围
    Returns:
        缩放后的点云和边界框
    """
    scale = random.uniform(*range)
    
    # 缩放点云
    points[:, :3] *= scale
    
    # 缩放边界框
    boxes[:, :3] *= scale  # 中心
    boxes[:, 3:6] *= scale  # 尺寸
    
    return points, boxes
```

## 训练流程实现

### 1. 数据加载

```python
class KITTIDataset(Dataset):
    def __init__(self, root_dir, split='training', transform=None):
        self.root_dir = root_dir
        self.split = split
        self.transform = transform
        
        # 获取样本列表
        self.sample_ids = self._get_sample_ids()
    
    def __len__(self):
        return len(self.sample_ids)
    
    def __getitem__(self, idx):
        sample_id = self.sample_ids[idx]
        
        # 加载点云
        points = self._load_point_cloud(sample_id)
        
        # 加载标注
        labels = self._load_labels(sample_id)
        
        # 数据增强
        if self.transform:
            points, labels = self.transform(points, labels)
        
        return {
            'points': points,
            'labels': labels,
            'sample_id': sample_id
        }
```

### 2. 训练循环

```python
def train_one_epoch(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0
    
    for batch in dataloader:
        # 数据移至设备
        points = batch['points'].to(device)
        labels = batch['labels'].to(device)
        
        # 前向传播
        predictions = model(points)
        
        # 计算损失
        loss = compute_loss(predictions, labels)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)
```

### 3. 验证流程

```python
def validate(model, dataloader, device):
    model.eval()
    results = []
    
    with torch.no_grad():
        for batch in dataloader:
            points = batch['points'].to(device)
            
            # 推理
            predictions = model(points)
            
            # 后处理
            boxes, scores, labels = post_process(predictions)
            
            results.append({
                'boxes': boxes,
                'scores': scores,
                'labels': labels
            })
    
    # 计算 mAP
    mAP = compute_map(results, dataloader.dataset.labels)
    
    return mAP
```

## 推理流程实现

### 1. 单帧推理

```python
class PointPillarsDetector:
    def __init__(self, model_path, device='cuda'):
        self.device = device
        self.model = self._load_model(model_path)
        self.model.eval()
    
    def detect(self, points):
        """
        单帧检测
        
        Args:
            points: (N, 4) 点云数据
        Returns:
            boxes: (M, 7) 3D 边界框
            scores: (M,) 置信度
            labels: (M,) 类别标签
        """
        # 预处理
        points = self._preprocess(points)
        
        # 转换为 tensor
        points_tensor = torch.from_numpy(points).float().to(self.device)
        points_tensor = points_tensor.unsqueeze(0)  # 添加 batch 维度
        
        # 推理
        with torch.no_grad():
            predictions = self.model(points_tensor)
        
        # 后处理
        boxes, scores, labels = self._post_process(predictions)
        
        return boxes, scores, labels
    
    def _preprocess(self, points):
        """预处理点云"""
        # 范围过滤
        mask = (
            (points[:, 0] >= -40) & (points[:, 0] <= 40) &
            (points[:, 1] >= -40) & (points[:, 1] <= 40) &
            (points[:, 2] >= -3) & (points[:, 2] <= 1)
        )
        return points[mask]
    
    def _post_process(self, predictions):
        """后处理预测结果"""
        cls_score, bbox_pred, dir_pred = predictions
        
        # 解码边界框
        boxes = decode_boxes(self.anchors, bbox_pred)
        
        # 应用 NMS
        keep = nms_3d(boxes, cls_score)
        
        return boxes[keep], cls_score[keep], self.labels[keep]
```

## 性能优化技巧

### 1. 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    with autocast():
        predictions = model(points)
        loss = compute_loss(predictions, labels)
    
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### 2. 梯度累积

```python
accumulation_steps = 4

for i, batch in enumerate(dataloader):
    predictions = model(points)
    loss = compute_loss(predictions, labels)
    loss = loss / accumulation_steps
    loss.backward()
    
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 3. 数据加载优化

```python
# 使用多进程数据加载
dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,
    pin_memory=True,
    prefetch_factor=2
)
```

## 参考实现

1. OpenPCDet: https://github.com/open-mmlab/OpenPCDet
2. mmdetection3d: https://github.com/open-mmlab/mmdetection3d
3. second.pytorch: https://github.com/traveller59/second.pytorch
