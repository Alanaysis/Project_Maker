# 学习笔记 - 人体姿态估计

## 核心概念

### 什么是人体姿态估计

人体姿态估计 (Human Pose Estimation) 是计算机视觉中的一个核心任务，目标是从图像或视频中检测人体的关键点（如鼻子、肩膀、肘部等），从而描述人体的姿态。

### 两种主流方法

#### 1. 热力图回归 (Heatmap Regression)

为每个关键点预测一个概率热力图，热力图的峰值位置即为关键点坐标。

**优点**:
- 精度高，是目前主流方法
- 可以表达不确定性
- 适合多关键点检测

**缺点**:
- 计算量较大
- 需要后处理（argmax 或 soft-argmax）

#### 2. 直接回归 (Direct Regression)

直接从图像特征回归关键点坐标。

**优点**:
- 计算量小
- 端到端训练

**缺点**:
- 精度较低
- 难以表达不确定性

### 热力图回归的数学原理

#### 高斯热力图生成

给定关键点坐标 (x_k, y_k)，生成高斯热力图：

```
H(x, y) = exp(-((x - x_k)^2 + (y - y_k)^2) / (2 * sigma^2))
```

其中 sigma 控制热力图的"宽度"：
- sigma 小：热力图更集中，峰值更尖锐
- sigma 大：热力图更分散，峰值更平缓

#### 关键点提取

**Argmax 方法**:
```
(x_pred, y_pred) = argmax_{x,y} H(x, y)
```

**Soft-Argmax 方法** (可微):
```
x_pred = sum(x * softmax(beta * H(x, y))) 
y_pred = sum(y * softmax(beta * H(x, y)))
```

其中 beta 是温度参数，越大越接近 argmax。

## 实现细节

### 网络架构设计

#### 骨干网络 (Backbone)

使用轻量级 CNN 提取特征：
- 多层卷积 + BatchNorm + ReLU
- 残差连接保证梯度流
- 逐步下采样（通常到 1/4 分辨率）

```python
class LightweightBackbone(nn.Module):
    def __init__(self, in_channels=3):
        self.stem = nn.Sequential(
            ConvBlock(3, 64, kernel_size=7, stride=2, padding=3),
            nn.MaxPool2d(2, stride=2),  # 1/4 下采样
        )
        self.layer1 = nn.Sequential(ConvBlock(64, 128), ResidualBlock(128))
        self.layer2 = nn.Sequential(ConvBlock(128, 256), ResidualBlock(256))
        self.layer3 = nn.Sequential(ConvBlock(256, 256), ResidualBlock(256))
```

#### 热力图预测头 (Head)

使用反卷积上采样 + 卷积生成热力图：

```python
class HeatmapHead(nn.Module):
    def __init__(self, in_channels=256, num_keypoints=17):
        self.deconv = nn.Sequential(
            nn.ConvTranspose2d(in_channels, 256, 4, 2, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            # ... 更多反卷积层
        )
        self.final = nn.Conv2d(256, num_keypoints, 1)
```

### 损失函数

#### MSE Loss

最基础的热力图回归损失：

```python
L = (1/K) * sum_k ||H_k - H_k^gt||^2
```

#### OHKM Loss (Online Hard Keypoint Mining)

只对损失最大的 Top-K 个关键点计算损失：

```python
# 计算每个关键点的损失
mse_per_keypoint = ((pred - target) ** 2).mean(dim=2)

# 选择 Top-K
topk_loss, _ = torch.topk(mse_per_keypoint, topk, dim=1)
loss = topk_loss.mean()
```

### 关键点定义

COCO 17 关键点格式：

```
0: 鼻子 (nose)
1: 左眼 (left_eye)
2: 右眼 (right_eye)
3: 左耳 (left_ear)
4: 右耳 (right_ear)
5: 左肩 (left_shoulder)
6: 右肩 (right_shoulder)
7: 左肘 (left_elbow)
8: 右肘 (right_elbow)
9: 左腕 (left_wrist)
10: 右腕 (right_wrist)
11: 左髋 (left_hip)
12: 右髋 (right_hip)
13: 左膝 (left_knee)
14: 右膝 (right_knee)
15: 左踝 (left_ankle)
16: 右踝 (right_ankle)
```

### 骨骼连接关系

定义人体骨架的拓扑结构：

```python
SKELETON_CONNECTIONS = [
    # 头部
    (0, 1),   # 鼻子 - 左眼
    (0, 2),   # 鼻子 - 右眼
    (1, 3),   # 左眼 - 左耳
    (2, 4),   # 右眼 - 右耳
    # 躯干
    (5, 6),   # 左肩 - 右肩
    (5, 11),  # 左肩 - 左髋
    (6, 12),  # 右肩 - 右髋
    (11, 12), # 左髋 - 右髋
    # 左臂
    (5, 7),   # 左肩 - 左肘
    (7, 9),   # 左肘 - 左腕
    # 右臂
    (6, 8),   # 右肩 - 右肘
    (8, 10),  # 右肘 - 右腕
    # 左腿
    (11, 13), # 左髋 - 左膝
    (13, 15), # 左膝 - 左踝
    # 右腿
    (12, 14), # 右髋 - 右膝
    (14, 16), # 右膝 - 右踝
]
```

## 评估指标

### PCK (Percentage of Correct Keypoints)

预测关键点与 GT 的距离 < 阈值 * 参考长度 的比例。

```python
def compute_pck(pred_keypoints, target_keypoints, threshold=0.2):
    dist = torch.norm(pred_keypoints - target_keypoints, dim=2)
    ref_len = np.sqrt(2)  # 图像对角线
    correct = (dist < threshold * ref_len).float()
    return correct.mean()
```

### OKS (Object Keypoint Similarity)

COCO 官方使用的姿态估计评估指标：

```python
OKS = sum(exp(-d^2 / (2 * s^2 * kappa^2)) * v) / sum(v)
```

其中：
- d: 预测关键点与 GT 的距离
- s: 目标面积的平方根
- kappa: 每个关键点的标准差
- v: 可见性标记

## 调试经验

### 问题 1: 热力图全为零

**原因**: 关键点坐标超出 [0, 1] 范围，或权重为 0。

**解决**: 检查关键点坐标范围和权重值。

### 问题 2: 训练不收敛

**原因**: 学习率过大，或损失函数权重不当。

**解决**: 
- 使用更小的学习率 (1e-4)
- 检查损失函数的权重设置
- 确保数据预处理正确

### 问题 3: 关键点精度低

**原因**: sigma 值不合适，或热力图分辨率太低。

**解决**:
- 调整 sigma 值 (通常 2-3 像素)
- 使用更高的热力图分辨率
- 使用 soft-argmax 替代 argmax

## 关键收获

1. **热力图回归是主流方法**: 相比直接回归，热力图方法精度更高，是目前的主流选择。

2. **sigma 参数很重要**: sigma 控制热力图的"宽度"，需要根据关键点密度和图像分辨率调整。

3. **soft-argmax 是可微的**: 在训练时使用 soft-argmax 可以实现端到端训练。

4. **OHKM 可以提升精度**: 在线困难关键点挖掘可以让模型专注于难以检测的关键点。

5. **数据增强很关键**: 翻转、旋转、缩放等增强可以显著提升模型泛化能力。
