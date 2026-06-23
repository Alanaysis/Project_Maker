# 02 - 架构设计

## 系统架构

### 整体流程

```
输入图像
    ↓
[数据预处理] → 归一化、缩放
    ↓
[YOLO 网络] → 特征提取 + 预测
    ↓
[后处理] → 解码 + NMS
    ↓
检测结果
```

### 模块划分

```
yolo-detection/
├── src/
│   ├── model.py      # 网络架构
│   ├── loss.py       # 损失函数
│   ├── nms.py        # NMS 后处理
│   ├── dataset.py    # 数据集处理
│   ├── utils.py      # 工具函数
│   ├── train.py      # 训练脚本
│   └── predict.py    # 推理脚本
└── tests/            # 测试文件
```

## 网络架构设计

### YOLOv1 网络

#### 骨干网络 (Backbone)

```python
# 24 层卷积 + 2 层全连接
Conv(7×7, 64) → MaxPool
Conv(3×3, 192) → MaxPool
Conv(1×1, 128) → Conv(3×3, 256) → Conv(1×1, 256) → Conv(3×3, 512) → MaxPool
# 4× [Conv(1×1, 256) → Conv(3×3, 512)]
Conv(1×1, 512) → Conv(3×3, 1024) → MaxPool
# 2× [Conv(1×1, 512) → Conv(3×3, 1024)]
Conv(3×3, 1024) → Conv(3×3, 1024, stride=2)
Conv(3×3, 1024) → Conv(3×3, 1024)
```

#### 检测头 (Head)

```python
Flatten → FC(4096) → Dropout(0.5) → FC(S×S×(B×5+C))
```

### TinyYOLOv1

简化版本，用于快速实验：

```python
# 更少的卷积层
Conv(3×3, 16) → MaxPool
Conv(3×3, 32) → MaxPool
Conv(3×3, 64) → MaxPool
Conv(3×3, 128) → MaxPool
Conv(3×3, 256) → MaxPool
Conv(3×3, 512) → MaxPool
Conv(3×3, 1024) → MaxPool

# 自适应池化 + 全连接
AdaptiveAvgPool(S×S) → FC(256) → FC(S×S×(B×5+C))
```

## 损失函数设计

### 组成部分

```python
Loss = λ_coord × (定位损失_xy + 定位损失_wh)
     + 置信度损失_有目标
     + λ_noobj × 置信度损失_无目标
     + 分类损失
```

### 各部分详解

#### 1. 定位损失 (xy)

```python
loc_xy = Σ 1_obj^ij × [(x - x̂)² + (y - ŷ)²]
```

- 只对有目标的单元格计算
- 预测值和真实值都是归一化坐标

#### 2. 定位损失 (wh)

```python
loc_wh = Σ 1_obj^ij × [(√w - √ŵ)² + (√h - √ĥ)²]
```

- 使用平方根是为了对小物体更敏感
- 大物体和小物体的误差权重不同

#### 3. 置信度损失 (有目标)

```python
conf_obj = Σ 1_obj^ij × (C - Ĉ)²
```

- C 是预测置信度
- Ĉ 是目标置信度（通常用 IoU）

#### 4. 置信度损失 (无目标)

```python
conf_noobj = λ_noobj × Σ 1_noobj^ij × (C - Ĉ)²
```

- 大部分单元格没有目标
- 使用较小的权重 λ_noobj 防止梯度消失

#### 5. 分类损失

```python
class_loss = Σ 1_obj^i × Σ_c (p(c) - p̂(c))²
```

- 只对有目标的单元格计算
- 使用 softmax 输出

### 超参数

| 参数 | 值 | 说明 |
|------|-----|------|
| λ_coord | 5.0 | 定位损失权重 |
| λ_noobj | 0.5 | 无目标置信度损失权重 |
| S | 7 | 网格大小 |
| B | 2 | 每单元格框数 |
| C | 20 | 类别数 (VOC) |

## NMS 实现设计

### 标准 NMS

```python
def nms(boxes, scores, iou_threshold=0.5):
    # 1. 按分数排序
    # 2. 选择最高分的框
    # 3. 删除高 IoU 的框
    # 4. 重复
```

### 批量 NMS (per-class)

```python
def batched_nms(boxes, scores, labels):
    # 对每个类别分别做 NMS
    # 避免不同类别的框相互抑制
```

### Soft NMS

```python
def soft_nms(boxes, scores, sigma=0.5):
    # 不直接删除框，而是衰减分数
    # score = score × exp(-iou² / sigma)
    # 更适合密集场景
```

## 数据流设计

### 训练数据流

```
原始图像 + 标注
    ↓
数据增强 (随机缩放、翻转、颜色抖动)
    ↓
归一化 (像素值 / 255)
    ↓
创建目标张量 (S×S×(B×5+C))
    ↓
输入网络
```

### 推理数据流

```
输入图像
    ↓
预处理 (缩放到 448×448, 归一化)
    ↓
网络前向传播
    ↓
解码预测 (网格坐标 → 绝对坐标)
    ↓
置信度过滤
    ↓
NMS 去重
    ↓
输出检测结果
```

## 模块接口设计

### YOLOv1

```python
class YOLOv1(nn.Module):
    def forward(x: Tensor) -> Tensor
    def predict(x: Tensor, threshold: float) -> List[Dict]
```

### YOLOLoss

```python
class YOLOLoss(nn.Module):
    def forward(predictions: Tensor, targets: Tensor) -> Tuple[Tensor, Dict]
```

### NMS

```python
def non_max_suppression(boxes, scores, iou_threshold, score_threshold) -> Tuple[Tensor, Tensor]
def batched_nms(boxes, scores, labels, iou_threshold) -> Tuple[Tensor, Tensor, Tensor]
```

### YOLOPredictor

```python
class YOLOPredictor:
    def detect(image: ndarray) -> Dict[str, Tensor]
    def detect_batch(images: List[ndarray]) -> List[Dict]
    def visualize(image, detections) -> ndarray
```
