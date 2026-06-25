# 深度估计 (Depth Estimation)

实现单目深度估计，从单张图像预测深度图。基于编码器-解码器架构，通过编码器提取图像特征，解码器逐步上采样恢复空间分辨率，最终输出单通道深度图。

## 项目概述

### 核心循环

```
图像输入 → 编码器 → 解码器 → 深度图输出
```

### 学习目标

- 理解深度估计原理（单目深度估计 vs 双目深度估计）
- 掌握编码器-解码器架构（跳跃连接、多尺度特征融合）
- 学会深度图回归（SILog 损失、梯度损失、评估指标）

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
cd projects/depth-estimation
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
)
```

### 推理示例

```python
import torch
from src.model import SimpleDepthNet

# 创建模型
model = SimpleDepthNet()

# 模拟输入图像
image = torch.randn(1, 3, 128, 128)

# 前向传播
depth = model(image)
print(f"深度图形状: {depth.shape}")  # (1, 1, 128, 128)
print(f"深度范围: [{depth.min():.4f}, {depth.max():.4f}]")
```

### 可视化

```python
import torch
from src.utils import colorize_depth, visualize_depth

# 创建深度图
depth = torch.rand(1, 128, 128)

# 着色
colored = colorize_depth(depth, colormap="jet")
print(f"着色后形状: {colored.shape}")  # (3, 128, 128)

# 完整可视化
image = torch.rand(3, 128, 128)
pred_depth = torch.rand(1, 128, 128)
result = visualize_depth(image, pred_depth)
```

## 项目结构

```
depth-estimation/
├── src/
│   ├── __init__.py      # 包初始化
│   ├── model.py         # 深度估计网络架构
│   ├── loss.py          # 损失函数 (SILog, 梯度损失)
│   ├── dataset.py       # 数据集处理
│   ├── train.py         # 训练脚本
│   └── utils.py         # 可视化与工具函数
├── tests/
│   ├── __init__.py
│   ├── test_model.py    # 模型测试
│   ├── test_loss.py     # 损失函数测试
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

- **DepthEncoder**: 多层编码器，逐步下采样提取特征
- **DepthDecoder**: 解码器，使用跳跃连接融合多尺度特征
- **DepthEstimationNet**: 完整的编码器-解码器网络
- **SimpleDepthNet**: 简化版网络，用于测试
- **MultiScaleDepthNet**: 多尺度输出网络，支持深度监督

```python
from src.model import DepthEstimationNet, SimpleDepthNet

# 完整模型
model = DepthEstimationNet(in_channels=3, base_channels=64)
depth = model(images)  # (batch, 1, H, W)

# 简化模型
simple_model = SimpleDepthNet()
depth = simple_model(images)  # (batch, 1, H, W)
```

### 2. 损失函数 (`loss.py`)

- **DepthMSELoss**: 均方误差损失
- **DepthMAELoss**: 平均绝对误差损失
- **SILogLoss**: 尺度不变对数损失（Eigen et al.）
- **GradientLoss**: 梯度损失（边缘保持）
- **CombinedDepthLoss**: 组合损失
- **BerHuLoss**: Reverse Huber 损失（Laina et al.）

```python
from src.loss import CombinedDepthLoss, SILogLoss

# 组合损失
criterion = CombinedDepthLoss()
loss_dict = criterion(pred_depth, target_depth, valid_mask)
print(loss_dict["total"], loss_dict["mse"], loss_dict["silog"])

# SILog 损失
silog = SILogLoss(lambda_weight=0.5)
loss = silog(pred_depth, target_depth)
```

### 3. 数据集 (`dataset.py`)

- **SyntheticDepthDataset**: 合成数据集，生成多种场景模式
  - `plane`: 平面场景
  - `slope`: 斜面场景
  - `stairs`: 阶梯场景
  - `sphere`: 球体场景
- **create_dataloader**: 创建数据加载器
- **generate_random_batch**: 快速生成随机批量数据

```python
from src.dataset import SyntheticDepthDataset, create_dataloader

dataset = SyntheticDepthDataset(num_samples=100, image_size=(128, 128))
loader = create_dataloader(dataset, batch_size=16)

for images, depths, masks in loader:
    print(images.shape, depths.shape, masks.shape)
```

### 4. 工具函数 (`utils.py`)

- **normalize_depth**: 深度图归一化
- **colorize_depth**: 深度图着色（jet, viridis, plasma）
- **visualize_depth**: 可视化深度估计结果
- **compute_depth_metrics**: 计算评估指标（Abs Rel, RMSE, delta 等）
- **depth_to_disparity / disparity_to_depth**: 深度-视差转换

```python
from src.utils import compute_depth_metrics, print_metrics

metrics = compute_depth_metrics(pred_depth, target_depth)
print_metrics(metrics)
```

### 5. 训练 (`train.py`)

- **DepthTrainer**: 训练器封装
- **train_simple**: 快速训练函数
- **train_full**: 完整训练函数

```python
from src.train import DepthTrainer, train_simple

# 快速训练
history = train_simple(num_epochs=10, batch_size=8)

# 自定义训练
trainer = DepthTrainer(model, criterion, optimizer, scheduler)
history = trainer.train(train_loader, val_loader, num_epochs=50)
```

## 深度估计算法原理

### 编码器-解码器架构

1. **编码器 (Encoder)**:
   - 多层卷积逐步下采样
   - 提取多尺度特征
   - 使用残差连接保证梯度流

2. **解码器 (Decoder)**:
   - 反卷积逐步上采样
   - 跳跃连接融合编码器特征
   - 恢复空间分辨率

3. **深度预测头**:
   - 1x1 卷积输出单通道
   - Sigmoid 激活输出 [0, 1] 范围

### 损失函数

1. **SILog Loss** (尺度不变对数损失):
   ```
   L = (1/n) * sum(d_i^2) - (lambda/n^2) * (sum(d_i))^2
   d_i = log(pred_i) - log(target_i)
   ```
   - 对深度的绝对尺度不敏感
   - 是 Eigen et al. 提出的标准损失

2. **Gradient Loss** (梯度损失):
   ```
   L = |grad_x(pred) - grad_x(target)| + |grad_y(pred) - grad_y(target)|
   ```
   - 保持边缘锐利
   - 鼓励预测深度图保持细节

3. **BerHu Loss** (Reverse Huber):
   ```
   L = |e|, if |e| <= c
   L = (e^2 + c^2) / (2*c), otherwise
   ```
   - 小误差用 L1，大误差用 L2
   - 自适应阈值

### 评估指标

| 指标 | 说明 | 越小越好 |
|------|------|----------|
| Abs Rel | 绝对相对误差 | ✓ |
| Sq Rel | 平方相对误差 | ✓ |
| RMSE | 均方根误差 | ✓ |
| RMSE Log | 对数均方根误差 | ✓ |
| delta < 1.25 | 阈值精度 | 越大越好 |
| delta < 1.25^2 | 阈值精度 | 越大越好 |
| delta < 1.25^3 | 阈值精度 | 越大越好 |

## 扩展方向

### 1. 使用预训练骨干网络

```python
import torchvision.models as models

class PretrainedEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        resnet = models.resnet50(pretrained=True)
        self.features = nn.Sequential(*list(resnet.children())[:-2])

    def forward(self, x):
        return self.features(x)
```

### 2. 使用真实数据集

```python
# NYU Depth V2 数据集
# KITTI 数据集
# DIODE 数据集
```

### 3. 高级技术

- **深度监督**: 多尺度输出，每个尺度都有损失
- **注意力机制**: 通道注意力、空间注意力
- **Transformer**: 使用 Vision Transformer 作为编码器
- **自监督学习**: 利用视频序列进行自监督训练
- **不确定性估计**: 预测深度的不确定性

### 4. 数据增强

```python
- 随机水平翻转
- 随机裁剪
- 颜色抖动
- 随机旋转
- 深度图扰动
```

## 参考资源

### 讴文

- [Eigen et al. (2014)](https://arxiv.org/abs/1406.2283): Depth Map Prediction from a Single Image using a Multi-Scale Deep Network
- [Laina et al. (2016)](https://arxiv.org/abs/1606.00373): Deeper Depth Prediction with Fully Convolutional Residual Networks
- [Godard et al. (2017)](https://arxiv.org/abs/1609.03677): Unsupervised Monocular Depth Estimation with Left-Right Consistency
- [Ranftl et al. (2021)](https://arxiv.org/abs/2103.13413): Vision Transformers for Dense Prediction

### 开源实现

- [MiDaS](https://github.com/isl-org/MiDaS): Robust Monocular Depth Estimation
- [DPT](https://github.com/isl-org/DPT): Dense Prediction Transformer
- [monodepth2](https://github.com/nianticlabs/monodepth2): Monocular Depth Estimation

### 数据集

- [NYU Depth V2](https://cs.nyu.edu/~silberman/datasets/nyu_depth_v2.html): 室内深度数据集
- [KITTI](http://www.cvlibs.net/datasets/kitti/): 自动驾驶深度数据集
- [DIODE](https://diode-dataset.org/): 多场景深度数据集
