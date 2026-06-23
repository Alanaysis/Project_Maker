# YOLO 目标检测

实现 YOLO (You Only Look Once) 目标检测算法，包括网络架构、损失函数、NMS 后处理、训练和推理流程。

## 项目概述

### 核心循环

```
图像 → 特征提取 → 边界框预测 → NMS → 检测结果
```

### 学习目标

- 理解目标检测任务和评估指标
- 掌握 YOLO 网络架构设计
- 实现边界框预测和锚框机制
- 学会 NMS 后处理算法

### 技术栈

- **语言**: Python
- **框架**: PyTorch
- **测试**: pytest

## 快速开始

### 安装依赖

```bash
pip install torch torchvision numpy matplotlib pytest
```

### 运行测试

```bash
cd projects/yolo-detection
pytest tests/ -v
```

### 简单训练示例

```python
from src.train import train_simple

# 快速训练测试
history = train_simple(
    num_epochs=5,
    batch_size=4,
    num_train_samples=50,
    num_val_samples=10,
)
```

### 推理示例

```python
from src.model import TinyYOLOv1
from src.predict import YOLOPredictor
import numpy as np

# 创建模型和预测器
model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
predictor = YOLOPredictor(model, confidence_threshold=0.1)

# 创建随机输入（实际使用时加载真实图像）
image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

# 运行检测
detections = predictor.detect(image)
print(f"Detected {len(detections['boxes'])} objects")
```

## 项目结构

```
yolo-detection/
├── src/
│   ├── __init__.py      # 包初始化
│   ├── model.py         # YOLO 网络架构 (YOLOv1, TinyYOLOv1)
│   ├── loss.py          # YOLO 损失函数
│   ├── nms.py           # 非极大值抑制 (NMS, Soft-NMS)
│   ├── dataset.py       # 数据集和数据加载
│   ├── utils.py         # 工具函数 (IoU, 坐标转换)
│   ├── train.py         # 训练脚本
│   └── predict.py       # 推理脚本
├── tests/
│   ├── test_model.py    # 模型测试
│   ├── test_loss.py     # 损失函数测试
│   ├── test_nms.py      # NMS 测试
│   ├── test_utils.py    # 工具函数测试
│   └── test_dataset.py  # 数据集测试
├── docs/
│   ├── 01-RESEARCH.md   # 研究笔记
│   ├── 02-ARCHITECTURE.md # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md    # 测试策略
│   └── 05-DEVELOPMENT.md # 开发指南
├── README.md
└── LEARNING_NOTES.md
```

## 核心模块

### 1. 网络架构 (`model.py`)

- **YOLOv1**: 完整的 YOLO v1 网络，24 层卷积 + 2 层全连接
- **TinyYOLOv1**: 简化版本，用于快速实验和测试

```python
from src.model import YOLOv1, TinyYOLOv1

model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
output = model(images)  # (batch, S*S*(B*5+C))
```

### 2. 损失函数 (`loss.py`)

YOLO 损失由五部分组成：
- 定位损失 (xy)
- 定位损失 (wh，使用平方根)
- 置信度损失 (有目标)
- 置信度损失 (无目标)
- 分类损失

```python
from src.loss import YOLOLoss

criterion = YOLOLoss(grid_size=7, num_boxes=2, num_classes=20)
loss, loss_dict = criterion(predictions, targets)
```

### 3. NMS 后处理 (`nms.py`)

- **标准 NMS**: 贪心算法，删除高 IoU 的框
- **批量 NMS**: 按类别分别做 NMS
- **Soft NMS**: 衰减分数而非删除框

```python
from src.nms import non_max_suppression, batched_nms, soft_nms

# 标准 NMS
keep_boxes, keep_scores = non_max_suppression(boxes, scores, iou_threshold=0.5)

# 按类别 NMS
keep_boxes, keep_scores, keep_labels = batched_nms(boxes, scores, labels)

# Soft NMS
keep_boxes, keep_scores = soft_nms(boxes, scores, sigma=0.5)
```

### 4. 工具函数 (`utils.py`)

- IoU 计算
- 边界框格式转换 (xywh ↔ xyxy)
- 预测解码
- 结果可视化

```python
from src.utils import compute_iou, xywh_to_xyxy, decode_predictions

iou = compute_iou(boxes1, boxes2)
xyxy_boxes = xywh_to_xyxy(xywh_boxes)
```

### 5. 数据集 (`dataset.py`)

- **SimpleDetectionDataset**: 合成数据集，用于快速测试
- **MultiScaleDataset**: 多尺度训练包装器
- 自定义 collate 函数处理变长标注

```python
from src.dataset import SimpleDetectionDataset, create_dataloader

dataset = SimpleDetectionDataset(num_samples=100, grid_size=7, num_classes=5)
loader = create_dataloader(dataset, batch_size=8)
```

### 6. 训练 (`train.py`)

- 完整的训练循环
- 学习率调度
- 模型检查点
- 训练历史记录

```python
from src.train import Trainer, train_simple

# 快速测试
history = train_simple(num_epochs=5)

# 自定义训练
trainer = Trainer(model, train_loader, val_loader, config)
history = trainer.train()
```

### 7. 推理 (`predict.py`)

- 图像预处理
- 模型推理
- NMS 后处理
- 结果可视化

```python
from src.predict import YOLOPredictor

predictor = YOLOPredictor.from_checkpoint("best_model.pt")
detections = predictor.detect(image)
```

## YOLO 算法原理

### 网格划分

将输入图像划分为 S×S 网格（默认 S=7）：
- 每个网格单元负责检测中心落在该区域的物体
- 每个单元预测 B 个边界框（默认 B=2）

### 输出格式

每个边界框包含 5 个值：(x, y, w, h, confidence)
- x, y: 相对于单元格的坐标（归一化到 [0,1]）
- w, h: 相对于图像的尺寸（归一化到 [0,1]）
- confidence: 置信度 = P(Object) × IoU

### NMS 算法

1. 按置信度降序排序所有检测框
2. 选择置信度最高的框
3. 删除与该框 IoU > 阈值的其他框
4. 重复直到没有框剩余

## 扩展方向

### 1. 使用真实数据集

```python
# 加载 PASCAL VOC 数据集
from torchvision.datasets import VOCDetection

dataset = VOCDetection(root="data", year="2012", download=True)
```

### 2. 实现更多 YOLO 版本

- YOLOv2: 引入锚框、批归一化
- YOLOv3: 多尺度预测、特征金字塔
- YOLOv4/v5: 更多优化技巧

### 3. 数据增强

```python
# 添加更多数据增强
- 随机裁剪
- 颜色抖动
- Mixup
- Mosaic
```

### 4. 评估指标

```python
# 实现 mAP 计算
- Precision-Recall 曲线
- AP (Average Precision)
- mAP (mean Average Precision)
```

## 参考资源

### 论文

- [YOLOv1](https://arxiv.org/abs/1506.02640): You Only Look Once: Unified, Real-Time Object Detection
- [YOLOv2](https://arxiv.org/abs/1612.08242): YOLO9000: Better, Faster, Stronger
- [YOLOv3](https://arxiv.org/abs/1804.02767): An Incremental Improvement

### 开源实现

- [Darknet](https://github.com/pjreddie/darknet): 官方实现
- [YOLOv5](https://github.com/ultralytics/yolov5): PyTorch 实现
- [YOLOv7](https://github.com/WongKinYiu/yolov7): 最新实现

### 数据集

- [PASCAL VOC](http://host.robots.ox.ac.uk/pascal/VOC/): 经典目标检测数据集
- [COCO](https://cocodataset.org/): 大规模目标检测数据集
- [Open Images](https://storage.googleapis.com/openimages/web/index.html): Google 大规模数据集
