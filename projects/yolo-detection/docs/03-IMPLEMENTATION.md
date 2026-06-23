# 03 - 实现细节

## 核心算法实现

### 1. IoU 计算

#### 算法

```python
def compute_iou(boxes1, boxes2):
    # 计算交集坐标
    x1 = max(boxes1.x1, boxes2.x1)
    y1 = max(boxes1.y1, boxes2.y1)
    x2 = min(boxes1.x2, boxes2.x2)
    y2 = min(boxes1.y2, boxes2.y2)

    # 计算交集面积
    intersection = max(0, x2 - x1) × max(0, y2 - y1)

    # 计算并集面积
    area1 = (boxes1.x2 - boxes1.x1) × (boxes1.y2 - boxes1.y1)
    area2 = (boxes2.x2 - boxes2.x1) × (boxes2.y2 - boxes2.y1)
    union = area1 + area2 - intersection

    return intersection / union
```

#### 向量化实现

使用 PyTorch 广播机制批量计算：

```python
# boxes1: (N, 4), boxes2: (M, 4)
# 扩展维度实现批量计算
boxes1 = boxes1.unsqueeze(1)  # (N, 1, 4)
boxes2 = boxes2.unsqueeze(0)  # (1, M, 4)

# 利用广播计算 (N, M) 的 IoU 矩阵
```

### 2. 边界框格式转换

#### xywh → xyxy

```python
def xywh_to_xyxy(boxes):
    x, y, w, h = boxes[..., 0], boxes[..., 1], boxes[..., 2], boxes[..., 3]
    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2
    return torch.stack([x1, y1, x2, y2], dim=-1)
```

#### xyxy → xywh

```python
def xyxy_to_xywh(boxes):
    x1, y1, x2, y2 = boxes[..., 0], boxes[..., 1], boxes[..., 2], boxes[..., 3]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    w = x2 - x1
    h = y2 - y1
    return torch.stack([cx, cy, w, h], dim=-1)
```

### 3. 预测解码

#### 网格坐标 → 绝对坐标

```python
def decode_predictions(predictions, grid_size, image_size):
    cell_size = image_size / grid_size

    # 创建网格偏移
    grid_y, grid_x = torch.meshgrid(
        torch.arange(grid_size),
        torch.arange(grid_size),
        indexing='ij'
    )

    # 转换坐标
    x = (predictions[..., 0] + grid_x) * cell_size
    y = (predictions[..., 1] + grid_y) * cell_size
    w = predictions[..., 2] * image_size
    h = predictions[..., 3] * image_size
```

### 4. NMS 实现

#### 标准 NMS

```python
def non_max_suppression(boxes, scores, iou_threshold=0.5):
    # 按分数降序排序
    sorted_indices = torch.argsort(scores, descending=True)

    keep = []
    suppressed = torch.zeros(len(boxes), dtype=torch.bool)

    for i in sorted_indices:
        if suppressed[i]:
            continue

        keep.append(i)

        # 计算当前框与其他框的 IoU
        ious = compute_iou(boxes[i], boxes[~suppressed])

        # 抑制高 IoU 的框
        high_iou_mask = ious > iou_threshold
        suppressed[~suppressed] |= high_iou_mask

    return keep
```

#### Soft NMS

```python
def soft_nms(boxes, scores, sigma=0.5):
    # 不删除框，而是衰减分数
    for i in range(len(boxes)):
        # 计算 IoU
        ious = compute_iou(boxes[i], boxes[i+1:])

        # 高斯衰减
        decay = torch.exp(-ious ** 2 / sigma)
        scores[i+1:] *= decay

    return scores
```

## 损失函数实现

### 目标张量创建

```python
def create_target_tensor(boxes, labels, grid_size, num_classes):
    target = torch.zeros(grid_size, grid_size, 2 * 5 + num_classes)

    for box, label in zip(boxes, labels):
        # 确定所属网格单元
        cell_x = int(box.x / cell_size)
        cell_y = int(box.y / cell_size)

        # 计算单元内相对坐标
        x_rel = (box.x / cell_size) - cell_x
        y_rel = (box.y / cell_size) - cell_y

        # 填充目标张量
        target[cell_y, cell_x, 0:4] = [x_rel, y_rel, w_rel, h_rel]
        target[cell_y, cell_x, 4] = 1.0  # 置信度
        target[cell_y, cell_x, 5 + label] = 1.0  # 类别

    return target
```

### 损失计算

```python
def yolo_loss(predictions, targets):
    # 1. 定位损失
    loc_loss = lambda_coord * (
        sum((pred_xy - target_xy)²) +
        sum((sqrt(pred_wh) - sqrt(target_wh))²)
    )

    # 2. 置信度损失 (有目标)
    conf_obj_loss = sum((pred_conf - target_conf)²)

    # 3. 置信度损失 (无目标)
    conf_noobj_loss = lambda_noobj * sum(pred_conf²)

    # 4. 分类损失
    class_loss = sum((pred_class - target_class)²)

    return loc_loss + conf_obj_loss + conf_noobj_loss + class_loss
```

## 训练流程实现

### 训练循环

```python
for epoch in range(num_epochs):
    for images, targets in train_loader:
        # 前向传播
        predictions = model(images)
        loss, loss_dict = criterion(predictions, targets)

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # 学习率调度
    scheduler.step()

    # 验证
    val_loss = validate(model, val_loader)

    # 保存检查点
    if epoch % save_every == 0:
        save_checkpoint(model, optimizer, epoch)
```

### 学习率调度

```python
# 余弦退火
scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs)

# 或者阶梯衰减
scheduler = StepLR(optimizer, step_size=30, gamma=0.1)
```

## 推理流程实现

### 完整推理管道

```python
class YOLOPredictor:
    def detect(self, image):
        # 1. 预处理
        input_tensor = self.preprocess(image)

        # 2. 前向传播
        raw_output = self.model(input_tensor)

        # 3. 解码预测
        predictions = self.decode(raw_output)

        # 4. 置信度过滤
        predictions = self.filter_by_confidence(predictions)

        # 5. NMS 去重
        predictions = self.apply_nms(predictions)

        return predictions
```

### 预处理

```python
def preprocess(self, image):
    # BGR → RGB
    image = image[:, :, ::-1]

    # 缩放到固定大小
    image = cv2.resize(image, (448, 448))

    # 归一化
    image = image / 255.0

    # 转换为张量
    tensor = torch.from_numpy(image).permute(2, 0, 1)
    return tensor.unsqueeze(0)
```

## 关键技术点

### 1. 批量 IoU 计算

使用 PyTorch 广播避免循环：

```python
# (N, 1, 4) 和 (1, M, 4) 广播 → (N, M, 4)
inter_x1 = torch.max(boxes1[:, None, 0], boxes2[None, :, 0])
```

### 2. 梯度裁剪

防止梯度爆炸：

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
```

### 3. 数据增强

提高模型泛化能力：

```python
# 随机水平翻转
if random.random() > 0.5:
    image = torch.flip(image, [-1])
    boxes[:, 0] = image_width - boxes[:, 0]

# 颜色抖动
image = adjust_brightness(image, random.uniform(0.8, 1.2))
image = adjust_contrast(image, random.uniform(0.8, 1.2))
```

### 4. 多尺度训练

提高小物体检测能力：

```python
# 随机选择输入尺寸
scales = [320, 352, 384, 416, 448]
scale = random.choice(scales)
image = F.interpolate(image, size=scale)
```

## 性能优化

### 1. 模型优化

- 使用 BatchNorm 加速训练
- 使用 LeakyReLU 防止死神经元
- Dropout 防止过拟合

### 2. 推理优化

- 使用 torch.no_grad() 减少内存
- 批量处理提高吞吐量
- 使用 TensorRT 加速

### 3. 内存优化

- 梯度累积处理大 batch
- 混合精度训练
- 及时释放不需要的张量
