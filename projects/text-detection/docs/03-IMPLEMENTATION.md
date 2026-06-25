# 03 - 实现细节

## 1. 核心模块实现

### 1.1 Backbone 实现

#### ConvBNReLU 块

```python
class ConvBNReLU(nn.Module):
    """Conv2d + BatchNorm + ReLU block."""

    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))
```

**设计要点**：
- `bias=False`：因为 BatchNorm 会学习偏置
- `inplace=True`：节省显存

#### VGG Backbone

```python
class VGGBackbone(nn.Module):
    def __init__(self, in_channels=3):
        super().__init__()

        # 每个 stage 包含 2-3 个卷积层 + MaxPool
        self.stage1 = nn.Sequential(
            ConvBNReLU(in_channels, 64),
            ConvBNReLU(64, 64),
            nn.MaxPool2d(2, 2),  # /2
        )
        # ... 类似定义 stage2-stage5

    def forward(self, x):
        f1 = self.stage1(x)    # [B, 64, H/2, W/2]
        f2 = self.stage2(f1)   # [B, 128, H/4, W/4]
        f3 = self.stage3(f2)   # [B, 256, H/8, W/8]
        f4 = self.stage4(f3)   # [B, 512, H/16, W/16]
        f5 = self.stage5(f4)   # [B, 512, H/32, W/32]
        return f1, f2, f3, f4, f5
```

**关键点**：
- 返回所有中间特征用于特征融合
- 渐进式下采样保持信息完整性

### 1.2 Neck 实现

#### U-Net Neck

```python
class UNetNeck(nn.Module):
    def __init__(self, in_channels_list, out_channels=32):
        super().__init__()

        # 横向连接：1x1 卷积调整通道数
        self.lateral_convs = nn.ModuleList([
            nn.Conv2d(ch, out_channels, 1, bias=False)
            for ch in in_channels_list
        ])

        # 平滑层：3x3 卷积
        self.smooth_convs = nn.ModuleList([
            ConvBlock(out_channels, out_channels)
            for _ in range(len(in_channels_list) - 1)
        ])

    def forward(self, features):
        # 1. 横向连接
        laterals = [conv(f) for conv, f in zip(self.lateral_convs, features)]

        # 2. 自顶向下融合
        for i in range(len(laterals) - 1, 0, -1):
            upsampled = F.interpolate(laterals[i], size=laterals[i-1].shape[2:])
            laterals[i-1] = laterals[i-1] + upsampled

        # 3. 平滑处理
        result = laterals[-1]
        for i in range(len(self.smooth_convs) - 1, -1, -1):
            result = F.interpolate(result, size=laterals[i].shape[2:])
            result = self.smooth_convs[i](result + laterals[i])

        return result
```

**融合流程**：
```
f5 (1/32) → lateral_conv → upsample → add → f4
f4 (1/16) → lateral_conv → upsample → add → f3
f3 (1/8)  → lateral_conv → upsample → add → f2
f2 (1/4)  → lateral_conv → upsample → add → f1
f1 (1/2)  → smooth_conv → output (1/4)
```

### 1.3 Head 实现

#### EAST Head

```python
class EASTHead(nn.Module):
    def __init__(self, in_channels, geo_type='rbox'):
        super().__init__()

        # 共享层
        self.shared = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )

        # 分数分支
        self.score_branch = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid(),  # 输出 [0, 1]
        )

        # 几何分支
        geo_out = 5 if geo_type == 'rbox' else 8
        self.geo_branch = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, geo_out, 1),
            nn.Sigmoid(),  # 输出 [0, 1]，后续缩放
        )

    def forward(self, x):
        shared = self.shared(x)
        score = self.score_branch(shared)
        geo = self.geo_branch(shared)
        return score, geo
```

**输出说明**：
- Score: 文字概率，Sigmoid 激活
- Geometry: 归一化到 [0, 1]，需要后处理缩放

### 1.4 损失函数实现

#### EAST Loss

```python
class EASTLoss(nn.Module):
    def forward(self, pred_score, pred_geo, gt_score, gt_geo, mask):
        # 1. 分数损失：BCE
        score_loss = F.binary_cross_entropy(pred_score, gt_score)

        # 2. 几何损失：IoU + Smooth L1
        if mask.sum() > 0:
            # IoU 损失
            pred_dists = pred_geo[:, :4]
            gt_dists = gt_geo[:, :4]
            iou = compute_iou(pred_dists, gt_dists)
            iou_loss = (1 - iou) * mask

            # 角度损失
            angle_loss = F.smooth_l1_loss(pred_geo[:, 4], gt_geo[:, 4])

            geo_loss = iou_loss + angle_loss
        else:
            geo_loss = 0

        # 3. 总损失
        total = lambda_score * score_loss + lambda_geo * geo_loss
        return total, score_loss, geo_loss
```

## 2. 后处理实现

### 2.1 NMS 实现

```python
def nms(boxes, scores, threshold):
    """标准 NMS 算法"""
    # 1. 按分数降序排序
    order = scores.argsort()[::-1]

    keep = []
    while len(order) > 0:
        # 2. 选择最高分的框
        i = order[0]
        keep.append(i)

        # 3. 计算与其他框的 IoU
        iou = compute_iou(boxes[i], boxes[order[1:]])

        # 4. 保留 IoU <= threshold 的框
        inds = np.where(iou <= threshold)[0]
        order = order[inds + 1]

    return keep
```

### 2.2 LANMS 实现

```python
def lanms(boxes, scores, threshold):
    """Locality-Aware NMS"""
    merged_boxes, merged_scores = [], []

    while len(boxes) > 0:
        # 1. 选择最高分的框
        i = scores.argmax()

        # 2. 找到重叠框
        iou = compute_iou(boxes[i], boxes)
        merge_inds = np.where(iou > threshold)[0]

        # 3. 合并重叠框（平均坐标）
        avg_box = boxes[merge_inds].mean(axis=0)
        avg_score = scores[merge_inds].mean()

        merged_boxes.append(avg_box)
        merged_scores.append(avg_score)

        # 4. 移除已合并的框
        boxes = np.delete(boxes, merge_inds, axis=0)
        scores = np.delete(scores, merge_inds)

    return merged_boxes, merged_scores
```

### 2.3 边界框解码

```python
def decode_rbox(score_map, geo_map, score_thresh, scale=4.0):
    """将分数图和几何图解码为边界框"""
    # 1. 阈值过滤
    mask = score_map > score_thresh
    ys, xs = np.where(mask)

    # 2. 提取几何值
    d_top = geo_map[0, mask]
    d_right = geo_map[1, mask]
    d_bottom = geo_map[2, mask]
    d_left = geo_map[3, mask]

    # 3. 转换为边界框坐标
    x1 = (xs - d_left) * scale
    y1 = (ys - d_top) * scale
    x2 = (xs + d_right) * scale
    y2 = (ys + d_bottom) * scale

    boxes = np.stack([x1, y1, x2, y2], axis=1)
    scores = score_map[mask]

    return boxes, scores
```

## 3. 数据处理实现

### 3.1 合成数据生成

```python
class TextDetectionDataset(Dataset):
    def __getitem__(self, idx):
        # 1. 生成随机背景
        img = np.random.randint(200, 255, (H, W, 3))

        # 2. 生成文字区域
        for _ in range(num_texts):
            # 随机位置和大小
            x, y = random_position()
            w, h = random_size()

            # 绘制文字区域
            img[y:y+h, x:x+w] = text_color

            # 3. 生成分数图（缩小的文字区域）
            score_map[y//4+shrink:(y+h)//4-shrink,
                     x//4+shrink:(x+w)//4-shrink] = 1.0

            # 4. 生成几何图
            for py in range(y//4, (y+h)//4):
                for px in range(x//4, (x+w)//4):
                    geo_map[0, py, px] = py - y//4      # top
                    geo_map[1, py, px] = (x+w)//4 - px  # right
                    geo_map[2, py, px] = (y+h)//4 - py  # bottom
                    geo_map[3, py, px] = px - x//4      # left
                    geo_map[4, py, px] = angle           # angle

        return img, score_map, geo_map, mask
```

### 3.2 数据增强

```python
class RandomRotate:
    """随机旋转"""
    def __call__(self, image, boxes):
        angle = random.uniform(-15, 15)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))
        # 更新边界框坐标
        new_boxes = rotate_boxes(boxes, M)
        return rotated, new_boxes


class RandomCrop:
    """随机裁剪"""
    def __call__(self, image, boxes):
        # 随机裁剪区域
        crop_region = random_crop_region(image.shape)
        cropped = image[crop_region]
        # 裁剪并过滤边界框
        new_boxes = clip_boxes(boxes, crop_region)
        return cropped, new_boxes
```

## 4. 训练流程实现

### 4.1 训练循环

```python
def train_one_epoch(model, dataloader, criterion, optimizer):
    model.train()
    for images, score_maps, geo_maps, masks in dataloader:
        # 前向传播
        output = model(images)
        loss, score_loss, geo_loss = criterion(
            output['score'], output['geo'],
            score_maps, geo_maps, masks
        )

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

### 4.2 学习率调度

```python
optimizer = Adam(model.parameters(), lr=1e-3)
scheduler = CosineAnnealingLR(optimizer, T_max=epochs)

# 每个 epoch 结束
scheduler.step()
```

## 5. 推理流程实现

### 5.1 完整推理管道

```python
class TextDetector:
    def detect(self, images):
        self.model.eval()
        with torch.no_grad():
            output = self.model(images)

        results = []
        for i in range(images.shape[0]):
            # 1. 解码边界框
            boxes, scores = decode_rbox(
                output['score'][i, 0],
                output['geo'][i],
                score_thresh=0.5,
                scale=4.0
            )

            # 2. NMS 去重
            if len(boxes) > 0:
                keep = nms(boxes, scores, nms_thresh=0.4)
                boxes, scores = boxes[keep], scores[keep]

            results.append({'boxes': boxes, 'scores': scores})

        return results
```

## 6. 性能优化技巧

### 6.1 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
with autocast():
    output = model(images)
    loss = criterion(output, targets)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 6.2 模型量化

```python
# 动态量化
quantized_model = torch.quantization.quantize_dynamic(
    model, {nn.Linear, nn.Conv2d}, dtype=torch.qint8
)
```

### 6.3 ONNX 导出

```python
torch.onnx.export(
    model,
    dummy_input,
    "text_detection.onnx",
    opset_version=11,
    input_names=['input'],
    output_names=['score', 'geometry']
)
```
