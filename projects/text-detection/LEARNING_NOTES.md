# 学习笔记 - 文字检测

## 1. 文字检测基础

### 1.1 什么是文字检测

文字检测（Text Detection）是计算机视觉的一个子任务，目标是在图像中自动定位文字区域。它是 OCR 系统的第一步。

```
图像输入 → 文字检测 → 文字识别 → 文本输出
```

### 1.2 与其他任务的区别

| 任务 | 目标 | 输出 |
|------|------|------|
| 文字检测 | 定位文字区域 | 边界框 |
| 文字识别 | 识别文字内容 | 文本字符串 |
| OCR | 检测 + 识别 | 文本 + 位置 |

### 1.3 应用场景

1. **文档数字化**：扫描件文字提取
2. **车牌识别**：自动识别车牌号码
3. **街景文字**：识别路标、店铺名
4. **工业质检**：产品标签检测

## 2. 传统方法 vs 深度学习

### 2.1 传统方法

**MSER（最大稳定极值区域）**
```python
mser = cv2.MSER_create()
regions, bboxes = mser.detectRegions(gray_image)
```

优点：
- 速度快
- 实现简单

缺点：
- 对噪声敏感
- 对复杂背景效果差

### 2.2 深度学习方法

**基于 CNN 的方法**
```python
# 使用 CNN 提取特征
features = backbone(image)
# 使用检测头预测
score_map, geo_map = head(features)
```

优点：
- 准确率高
- 鲁棒性强

缺点：
- 计算量大
- 需要大量标注数据

## 3. EAST 架构详解

### 3.1 核心思想

EAST 的核心思想是**单阶段检测**，直接从图像预测文字区域，无需候选区域生成。

```
传统方法：候选区域 → 分类 → 回归 → NMS
EAST：直接预测 → NMS
```

### 3.2 网络结构

```
输入图像 (512 x 512 x 3)
    │
    ├── Backbone (VGG)
    │   ├── Stage 1: 256 x 256 x 64
    │   ├── Stage 2: 128 x 128 x 128
    │   ├── Stage 3: 64 x 64 x 256
    │   ├── Stage 4: 32 x 32 x 512
    │   └── Stage 5: 16 x 16 x 512
    │
    ├── Neck (U-Net)
    │   ├── Merge 1: 32 x 32 x 256
    │   ├── Merge 2: 64 x 64 x 128
    │   └── Merge 3: 128 x 128 x 32
    │
    └── Head
        ├── Score Map: 128 x 128 x 1
        └── Geometry Map: 128 x 128 x 5
```

### 3.3 几何表示

**RBOX（旋转边界框）**
```
        top (d0)
    ┌───────────┐
    │           │
left│   text    │right
(d3)│           │(d1)
    └───────────┘
       bottom (d2)
```

每个像素存储：
- d0: 到顶部的距离
- d1: 到右侧的距离
- d2: 到底部的距离
- d3: 到左侧的距离
- angle: 旋转角度

### 3.4 损失函数

```python
L_total = λ_score * L_score + λ_geo * L_geo

L_score = BCE(pred_score, gt_score)
L_geo = L_iou + L_angle
L_iou = 1 - IoU(pred_box, gt_box)
L_angle = SmoothL1(pred_angle, gt_angle)
```

## 4. CTPN 架构详解

### 4.1 核心思想

CTPN 的核心思想是**文字提议**，检测固定宽度的小文字块，然后合并成文字行。

```
文字行 → 分割成小块 → 逐块检测 → 合并成行
```

### 4.2 网络结构

```
输入图像
    │
    ├── VGG16 Backbone
    │
    ├── RPN (Region Proposal Network)
    │   └── 固定宽度 anchor (16px)
    │
    ├── BiLSTM
    │   └── 序列上下文建模
    │
    └── Output
        ├── 文字/非文字分类
        └── 边界框回归
```

### 4.3 与 EAST 的区别

| 特性 | EAST | CTPN |
|------|------|------|
| 检测方式 | 单阶段 | 两阶段 |
| 速度 | 快 | 慢 |
| 多方向文字 | 支持 | 不支持 |
| 后处理 | 简单 NMS | 复杂合并 |

## 5. 关键技术点

### 5.1 特征金字塔

**为什么需要特征金字塔？**
- 小文字需要高分辨率特征
- 大文字需要低分辨率特征
- 特征金字塔融合多尺度信息

```python
# 自顶向下融合
for i in range(len(features) - 1, 0, -1):
    upsampled = F.interpolate(features[i], size=features[i-1].shape[2:])
    features[i-1] = features[i-1] + upsampled
```

### 5.2 NMS（非极大值抑制）

**为什么需要 NMS？**
- 同一个文字区域可能有多个检测框
- NMS 保留最高分的框，删除重叠框

```python
def nms(boxes, scores, threshold):
    # 按分数排序
    order = scores.argsort()[::-1]
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        # 计算 IoU
        iou = compute_iou(boxes[i], boxes[order[1:]])
        # 保留 IoU <= threshold 的框
        inds = np.where(iou <= threshold)[0]
        order = order[inds + 1]
    return keep
```

### 5.3 LANMS（局部感知 NMS）

**LANMS vs NMS**
- NMS：删除重叠框
- LANMS：合并重叠框（平均坐标）

```python
def lanms(boxes, scores, threshold):
    while len(boxes) > 0:
        # 找到重叠框
        iou = compute_iou(boxes[0], boxes)
        merge_inds = np.where(iou > threshold)[0]
        # 合并
        avg_box = boxes[merge_inds].mean(axis=0)
        merged_boxes.append(avg_box)
```

## 6. 训练技巧

### 6.1 数据增强

```python
# 随机旋转
angle = random.uniform(-15, 15)
M = cv2.getRotationMatrix2D(center, angle, 1.0)
rotated = cv2.warpAffine(image, M, (w, h))

# 随机裁剪
crop_region = random_crop_region(image.shape)
cropped = image[crop_region]

# 颜色抖动
brightness = random.uniform(0.8, 1.2)
image = image * brightness
```

### 6.2 学习率调度

```python
# 余弦退火
scheduler = CosineAnnealingLR(optimizer, T_max=epochs)

# 预热
for epoch in range(warmup_epochs):
    lr = base_lr * (epoch + 1) / warmup_epochs
    optimizer.param_groups[0]['lr'] = lr
```

### 6.3 梯度累积

```python
optimizer.zero_grad()
for i, (images, targets) in enumerate(dataloader):
    loss = criterion(model(images), targets)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## 7. 调试经验

### 7.1 常见问题

**问题 1：损失不下降**
```python
# 检查数据
print(f"Image range: [{images.min():.4f}, {images.max():.4f}]")
print(f"Target range: [{targets.min():.4f}, {targets.max():.4f}]")

# 检查学习率
print(f"Learning rate: {optimizer.param_groups[0]['lr']}")
```

**问题 2：检测结果差**
```python
# 检查分数图
score_map = output['score'][0, 0].numpy()
print(f"Score range: [{score_map.min():.4f}, {score_map.max():.4f}]")

# 降低阈值
boxes, scores = decode_rbox(score_map, geo_map, score_thresh=0.3)
```

**问题 3：内存溢出**
```python
# 减小 batch size
batch_size = 4  # 从 16 减到 4

# 使用梯度检查点
from torch.utils.checkpoint import checkpoint
output = checkpoint(model, images)
```

### 7.2 调试工具

```python
# 打印形状
print(f"Input: {x.shape}")
print(f"Output: {output.shape}")

# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_mean={param.grad.mean():.6f}")

# 可视化
plt.imshow(score_map, cmap='jet')
plt.colorbar()
plt.show()
```

## 8. 进阶学习

### 8.1 DBNet（可微分二值化）

**核心思想**：
- 传统方法使用固定阈值二值化
- DBNet 学习自适应阈值
- 可微分，端到端训练

```python
def differentiable_binarize(prob, thresh, k=50):
    return 1 / (1 + torch.exp(-k * (prob - thresh)))
```

### 8.2 Transformer-based 方法

**核心思想**：
- 使用 Vision Transformer 提取特征
- 更强的全局上下文建模
- 端到端检测与识别

### 8.3 轻量化方法

**MobileNet Backbone**
```python
class MobileNetBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # 深度可分离卷积
            nn.Conv2d(3, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU6(inplace=True),
            # ...
        )
```

## 9. 实践项目

### 9.1 文档文字检测

```python
# 加载文档图像
image = cv2.imread('document.jpg')

# 检测文字区域
results = detector.detect(preprocess(image))

# 提取文字区域
for box in results['boxes']:
    x1, y1, x2, y2 = box.astype(int)
    roi = image[y1:y2, x1:x2]
    # OCR 识别
    text = ocr.recognize(roi)
```

### 9.2 车牌识别

```python
# 检测车牌区域
results = detector.detect(preprocess(car_image))

# 筛选车牌区域
for box, score in zip(results['boxes'], results['scores']):
    if score > 0.8:
        x1, y1, x2, y2 = box.astype(int)
        plate = car_image[y1:y2, x1:x2]
        # 识别车牌号码
        plate_number = plate_ocr(plate)
```

## 10. 学习资源

### 10.1 论文
- [EAST: An Efficient and Accurate Scene Text Detector](https://arxiv.org/abs/1704.03155)
- [Detecting Text in Natural Image with CTPN](https://arxiv.org/abs/1609.03605)
- [Real-Time Scene Text Detection with DBNet](https://arxiv.org/abs/1911.08947)

### 10.2 开源实现
- [EAST (TensorFlow)](https://github.com/argman/EAST)
- [DBNet (PyTorch)](https://github.com/MhLiao/DB)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)

### 10.3 教程
- [OpenCV Text Detection](https://www.pyimagesearch.com/2018/08/20/opencv-text-detection-east-text-detector/)
- [Scene Text Detection Tutorial](https://towardsdatascience.com/scene-text-detection-with-python-2b6b359a0668)

## 11. 总结

### 关键要点

1. **文字检测是 OCR 的第一步**，定位文字区域是识别的前提
2. **EAST 是高效的文字检测架构**，单阶段检测，速度快
3. **特征金字塔融合多尺度信息**，提高检测精度
4. **NMS 去除重复检测**，LANMS 更适合文字检测
5. **数据增强很重要**，旋转、裁剪、颜色抖动提高泛化能力

### 下一步学习

1. 实现 DBNet，学习可微分二值化
2. 学习 Transformer-based 文字检测方法
3. 实践真实场景的文字检测项目
4. 学习模型优化和部署技术
