# 人体姿态估计

实现人体姿态估计，检测骨骼关键点。基于热力图回归的方法，通过骨干网络提取特征，预测关键点热力图，最终解码为关键点坐标。

## 项目概述

### 核心循环

```
图像输入 → 骨干网络 → 特征提取 → 热力图回归 → 关键点坐标
```

### 学习目标

- 理解姿态估计原理（热力图回归 vs 回归方法）
- 掌握关键点检测（COCO 17 关键点格式）
- 学会热力图回归（高斯热力图生成、MSE 损失、soft-argmax）

### 技术栈

- **语言**: Python
- **框架**: PyTorch
- **其他**: OpenCV, NumPy, Matplotlib
- **测试**: pytest

## 快速开始

### 安装依赖

```bash
pip install torch torchvision numpy opencv-python matplotlib pytest
```

### 运行测试

```bash
cd projects/pose-estimation
pytest tests/ -v
```

### 运行演示

```bash
python examples/demo.py
```

### 训练模型

```python
from src.train import train_simple

# 快速训练测试
history = train_simple(
    num_epochs=10,
    batch_size=8,
    num_train_samples=100,
    num_val_samples=20,
    image_size=(128, 128),
    heatmap_size=(64, 64),
)
```

### 推理示例

```python
import torch
from src.model import SimplePoseNet
from src.keypoints import extract_keypoints

# 创建模型
model = SimplePoseNet(num_keypoints=17, input_size=128)

# 模拟输入图像
image = torch.randn(1, 3, 128, 128)

# 前向传播
heatmaps = model(image)

# 提取关键点
keypoints, confidence = extract_keypoints(heatmaps)
print(f"关键点形状: {keypoints.shape}")  # (1, 17, 2)
print(f"置信度形状: {confidence.shape}")  # (1, 17)
```

### 可视化

```python
import torch
import numpy as np
from src.utils import visualize_pose

# 创建图像和关键点
image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
keypoints = np.array([[128, 50], [115, 40], [141, 40], ...])  # 17个关键点

# 可视化
result = visualize_pose(
    torch.from_numpy(image).permute(2, 0, 1),
    torch.from_numpy(keypoints),
)
```

## 项目结构

```
pose-estimation/
├── src/
│   ├── __init__.py      # 包初始化
│   ├── model.py         # 姿态估计网络架构
│   ├── heatmap.py       # 热力图生成与处理
│   ├── loss.py          # 损失函数 (MSE, OHKM)
│   ├── keypoints.py     # 关键点检测与处理
│   ├── dataset.py       # 数据集处理
│   ├── utils.py         # 可视化与工具函数
│   └── train.py         # 训练脚本
├── tests/
│   ├── test_model.py    # 模型测试
│   ├── test_heatmap.py  # 热力图测试
│   ├── test_loss.py     # 损失函数测试
│   ├── test_keypoints.py # 关键点测试
│   ├── test_dataset.py  # 数据集测试
│   └── test_utils.py    # 工具函数测试
├── examples/
│   └── demo.py          # 完整演示脚本
├── docs/
│   ├── 01-RESEARCH.md   # 研究笔记
│   ├── 02-DESIGN.md     # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md    # 测试策略
│   └── 05-DEVELOPMENT.md # 开发指南
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 核心模块

### 1. 网络架构 (`model.py`)

- **LightweightBackbone**: 轻量级骨干网络，类似简化版 ResNet
- **HeatmapHead**: 热力图预测头，使用反卷积上采样
- **PoseEstimationNet**: 完整的姿态估计网络
- **SimplePoseNet**: 简化版网络，用于测试

```python
from src.model import PoseEstimationNet, SimplePoseNet

model = PoseEstimationNet(num_keypoints=17, input_size=256, heatmap_size=64)
heatmaps = model(images)  # (batch, 17, 64, 64)
```

### 2. 热力图处理 (`heatmap.py`)

- **generate_heatmaps**: 从关键点坐标生成高斯热力图
- **heatmaps_to_keypoints**: 使用 argmax 从热力图提取关键点
- **soft_argmax**: 可微的 soft-argmax 关键点提取

```python
from src.heatmap import generate_heatmaps, soft_argmax

# 生成热力图
heatmaps = generate_heatmaps(keypoints, weights, (64, 64), sigma=2.0)

# 提取关键点 (可微)
keypoints, confidence = soft_argmax(heatmaps, beta=100.0)
```

### 3. 损失函数 (`loss.py`)

- **KeypointMSELoss**: 均方误差损失
- **KeypointOHKMLoss**: 在线困难关键点挖掘损失
- **CombinedPoseLoss**: 组合损失

```python
from src.loss import KeypointMSELoss

criterion = KeypointMSELoss(use_target_weight=True)
loss_dict = criterion(pred_heatmaps, target_heatmaps, target_weights)
```

### 4. 关键点处理 (`keypoints.py`)

- **COCO 17 关键点定义**: 鼻子、眼睛、耳朵、肩膀、肘部、手腕、髋部、膝盖、脚踝
- **骨骼连接关系**: 定义人体骨架的连接拓扑
- **关键点提取**: argmax 和亚像素精度提取
- **PCK 评估**: Percentage of Correct Keypoints

```python
from src.keypoints import KEYPOINT_NAMES, SKELETON_CONNECTIONS, compute_pck

# 评估
pck = compute_pck(pred_keypoints, target_keypoints, threshold=0.2)
```

### 5. 数据集 (`dataset.py`)

- **SyntheticPoseDataset**: 合成数据集，生成简笔画人形
- 支持自定义图像尺寸、热力图尺寸、关键点数量

```python
from src.dataset import SyntheticPoseDataset, create_dataloader

dataset = SyntheticPoseDataset(num_samples=100, image_size=(256, 256))
loader = create_dataloader(dataset, batch_size=16)
```

### 6. 可视化 (`utils.py`)

- **draw_skeleton**: 在图像上绘制骨骼
- **visualize_pose**: 自动处理张量转换和坐标归一化

```python
from src.utils import draw_skeleton, visualize_pose

result = draw_skeleton(image, keypoints, confidence)
result = visualize_pose(image_tensor, keypoints_tensor)
```

## 姿态估计算法原理

### 热力图回归方法

1. **热力图生成**: 为每个关键点生成高斯热力图
   - H(x,y) = exp(-((x-x_k)^2 + (y-y_k)^2) / (2*sigma^2))
   - 峰值位置对应关键点坐标

2. **网络预测**: 骨干网络提取特征，预测头输出热力图

3. **关键点解码**: 从预测热力图中提取关键点坐标
   - argmax: 找到热力图最大值位置
   - soft-argmax: 可微的期望坐标计算

### COCO 17 关键点

```
     鼻子(0)
    /       \
左眼(1)   右眼(2)
  |           |
左耳(3)   右耳(4)

左肩(5)---右肩(6)
  |    \   /    |
左肘(7)  躯干  右肘(8)
  |           |
左腕(9)   右腕(10)

左髋(11)--右髋(12)
  |    \   /    |
左膝(13)      右膝(14)
  |           |
左踝(15)  右踝(16)
```

### 评估指标

- **PCK**: 预测关键点与 GT 距离 < 阈值 * 参考长度的比例
- **OKS**: Object Keypoint Similarity，COCO 官方指标

## 扩展方向

### 1. 使用真实数据集

```python
# 加载 COCO 数据集
from torchvision.datasets import CocoDetection

dataset = CocoDetection(
    root="data/coco/train2017",
    annFile="data/coco/annotations/person_keypoints_train2017.json",
)
```

### 2. 更强的骨干网络

```python
# 使用预训练 ResNet
import torchvision.models as models

backbone = models.resnet50(pretrained=True)
# 移除最后的全连接层，添加热力图预测头
```

### 3. 高级技术

- **自顶向下**: 先检测人体，再估计姿态
- **自底向上**: 先检测所有关键点，再分组
- **Transformer**: 使用注意力机制
- **3D 姿态估计**: 从 2D 推断 3D

### 4. 数据增强

```python
- 随机翻转
- 随机旋转
- 随机缩放
- 颜色抖动
- 遮挡增强
```

## 参考资源

### 论文

- [SimpleBaseline](https://arxiv.org/abs/1804.06208): Simple Baselines for Human Pose Estimation
- [HRNet](https://arxiv.org/abs/1902.09212): Deep High-Resolution Representation Learning
- [CPM](https://arxiv.org/abs/1602.00134): Convolutional Pose Machines
- [Stacked Hourglass](https://arxiv.org/abs/1603.06937): Stacked Hourglass Network

### 开源实现

- [mmpose](https://github.com/open-mmlab/mmpose): OpenMMLab 姿态估计工具箱
- [HRNet](https://github.com/leoxiaobin/deep-high-resolution-net.pytorch): HRNet 官方实现
- [lightweight-human-pose-estimation](https://github.com/Daniil-Osokin/lightweight-human-pose-estimation.pytorch): 轻量级实现

### 数据集

- [COCO Keypoints](https://cocodataset.org/#keypoints-2020): COCO 关键点数据集
- [MPII Human Pose](http://human-pose.mpi-inf.mpg.de/): MPII 人体姿态数据集
- [OCHuman](https://github.com/liruilong940607/OCHumanApi): 遮挡人体数据集
