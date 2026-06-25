# 学习笔记 - 深度估计

## 核心概念

### 什么是深度估计

深度估计 (Depth Estimation) 是计算机视觉中的核心任务，目标是从图像中预测每个像素到相机的距离（深度）。对于单目深度估计，我们需要从单张 2D 图像推断 3D 深度信息。

### 两种主流方法

#### 1. 单目深度估计 (Monocular Depth Estimation)

从单张图像预测深度。

**优点**:
- 只需要单个摄像头
- 成本低，部署简单
- 适用范围广

**缺点**:
- 尺度模糊（无法确定绝对深度）
- 需要大量标注数据
- 泛化能力有限

#### 2. 双目深度估计 (Stereo Depth Estimation)

从两个视角的图像通过视差计算深度。

**优点**:
- 可以得到绝对深度
- 精度更高

**缺点**:
- 需要双目摄像头
- 标定复杂
- 计算量大

### 深度估计的数学原理

#### 深度与视差的关系

对于双目系统：
```
depth = baseline * focal / disparity
```

其中：
- baseline: 基线距离（两个摄像头之间的距离）
- focal: 焦距
- disparity: 视差（同一点在左右图像中的位置差）

#### 单目深度估计的学习目标

对于单目深度估计，网络学习的是：
```
f: I(x, y) → D(x, y)
```

其中 I 是输入图像，D 是输出深度图。

## 实现细节

### 编码器-解码器架构

#### 编码器 (Encoder)

使用多层卷积逐步下采样图像，提取多尺度特征：

```
输入图像 (H, W)
    ↓ Conv + MaxPool
特征图 1 (H/4, W/4)
    ↓ Conv stride=2
特征图 2 (H/8, W/8)
    ↓ Conv stride=2
特征图 3 (H/16, W/16)
    ↓ Conv stride=2
特征图 4 (H/32, W/32)
```

关键设计：
- 残差连接保证梯度流
- BatchNorm 稳定训练
- ReLU 激活引入非线性

#### 解码器 (Decoder)

逐步上采样特征图，恢复空间分辨率：

```
特征图 4 (H/32, W/32)
    ↓ ConvTranspose + 跳跃连接
特征图 3 (H/16, W/16)
    ↓ ConvTranspose + 跳跃连接
特征图 2 (H/8, W/8)
    ↓ ConvTranspose + 跳跃连接
特征图 1 (H/4, W/4)
    ↓ ConvTranspose
深度图 (H, W)
```

关键设计：
- 跳跃连接融合编码器特征
- 反卷积上采样
- 1x1 卷积输出单通道深度

### 损失函数设计

#### 1. SILog Loss (尺度不变对数损失)

Eigen et al. 提出的标准损失函数：

```python
L = (1/n) * sum(d_i^2) - (lambda/n^2) * (sum(d_i))^2
d_i = log(pred_i) - log(target_i)
```

**优点**:
- 对深度的绝对尺度不敏感
- 鼓励相对深度正确
- 是深度估计的标准评估指标

**超参数**:
- lambda: 正则化权重，通常 0.5

#### 2. Gradient Loss (梯度损失)

保持边缘锐利：

```python
L = |grad_x(pred) - grad_x(target)| + |grad_y(pred) - grad_y(target)|
```

**优点**:
- 鼓励预测深度图保持边缘
- 与 MSE/MAE 互补

#### 3. BerHu Loss (Reverse Huber Loss)

Laina et al. 提出的自适应损失：

```python
L = |e|, if |e| <= c
L = (e^2 + c^2) / (2*c), otherwise
```

其中 c = max(|e|) / 5

**优点**:
- 小误差用 L1（保持边缘）
- 大误差用 L2（避免梯度爆炸）
- 自适应阈值

### 评估指标

#### 绝对相对误差 (Abs Rel)

```python
abs_rel = mean(|pred - target| / target)
```

#### 均方根误差 (RMSE)

```python
rmse = sqrt(mean((pred - target)^2))
```

#### 阈值精度 (delta)

```python
delta = mean(max(pred/target, target/target) < 1.25)
```

这是最常用的指标，表示预测深度在 25% 误差范围内的比例。

## 训练技巧

### 1. 学习率调度

使用余弦退火调度：

```python
scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs)
```

### 2. 梯度裁剪

防止梯度爆炸：

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

### 3. 数据增强

常用增强方法：
- 随机水平翻转
- 随机裁剪
- 颜色抖动
- 随机旋转

### 4. 深度监督

在解码器的多个层级输出深度图，每个层级都有损失：

```python
loss = loss_scale1 + 0.5 * loss_scale2 + 0.25 * loss_scale3
```

## 常见问题

### 问题 1: 深度图全为零或全为 1

**原因**: Sigmoid 输出饱和，或学习率过大。

**解决**:
- 使用更小的学习率
- 检查损失函数
- 使用 BatchNorm

### 问题 2: 预测深度图模糊

**原因**: 缺少边缘保持损失，或下采样过多。

**解决**:
- 添加梯度损失
- 减少下采样层数
- 使用跳跃连接

### 问题 3: 尺度不一致

**原因**: 单目深度估计的固有问题。

**解决**:
- 使用 SILog 损失
- 后处理归一化
- 使用已知物体大小校准

## 关键收获

1. **编码器-解码器是主流架构**: 跳跃连接和多尺度特征融合是关键。

2. **SILog 是标准损失**: 对尺度不敏感，是深度估计的标准评估指标。

3. **梯度损失保持边缘**: 与 MSE/MAE 互补，鼓励预测深度图保持细节。

4. **评估指标很重要**: delta < 1.25 是最常用的指标。

5. **数据增强很关键**: 翻转、裁剪等增强可以显著提升泛化能力。

## 进阶方向

### 1. 自监督深度估计

利用视频序列进行自监督训练，不需要深度标注：

```python
# 利用相邻帧的几何一致性
loss = photometric_loss(I_t, I_t+1, depth_t, pose_t,t+1)
```

### 2. Transformer 架构

使用 Vision Transformer 作为编码器：

```python
# DPT (Dense Prediction Transformer)
encoder = ViT(image_size=384, patch_size=16)
decoder = DPTDecoder()
```

### 3. 不确定性估计

预测深度的不确定性：

```python
# 输出深度和不确定性
depth, uncertainty = model(image)
loss = gaussian_nll_loss(pred_depth, target_depth, uncertainty)
```

### 4. 多任务学习

同时预测深度和语义分割：

```python
# 共享编码器，分别解码
depth, segmentation = model(image)
loss = depth_loss + segmentation_loss
```
