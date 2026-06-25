# 架构设计 - 深度估计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      深度估计系统                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  数据集   │  │   模型   │  │  损失函数 │  │   训练   │   │
│  │ Dataset  │  │  Model   │  │   Loss   │  │  Train   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       │             │             │             │            │
│       ▼             ▼             ▼             ▼            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    工具函数                            │   │
│  │              Utils (可视化、指标)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
train.py ──────────┬─────────────────────────────────┐
    │              │                                 │
    ▼              ▼                                 ▼
model.py      loss.py                          dataset.py
    │              │                                 │
    └──────────────┴─────────────────────────────────┘
                         │
                         ▼
                    utils.py
```

## 2. 模型架构设计

### 2.1 编码器设计

```python
class DepthEncoder(nn.Module):
    """
    编码器: 多层卷积逐步下采样

    架构:
    input (3, H, W)
        ↓ stem (7x7 conv + maxpool)
    feature_0 (64, H/4, W/4)
        ↓ layer1 (conv stride=2 + residual)
    feature_1 (128, H/8, W/8)
        ↓ layer2 (conv stride=2 + residual)
    feature_2 (256, H/16, W/16)
        ↓ layer3 (conv stride=2 + residual)
    feature_3 (512, H/32, W/32)
        ↓ layer4 (conv stride=2 + residual)
    feature_4 (1024, H/64, W/64)
    """
```

**设计原则**:
- 每层使用 stride=2 卷积下采样
- 使用残差连接保证梯度流
- BatchNorm + ReLU 稳定训练

### 2.2 解码器设计

```python
class DepthDecoder(nn.Module):
    """
    解码器: 反卷积上采样 + 跳跃连接

    架构:
    feature_4 (1024, H/64, W/64)
        ↓ deconv + concat(feature_3)
    decoded_3 (512, H/32, W/32)
        ↓ deconv + concat(feature_2)
    decoded_2 (256, H/16, W/16)
        ↓ deconv + concat(feature_1)
    decoded_1 (128, H/8, W/8)
        ↓ deconv + concat(feature_0)
    decoded_0 (64, H/4, W/4)
        ↓ deconv
    depth (1, H, W)
    """
```

**设计原则**:
- 反卷积逐步上采样
- 跳跃连接融合编码器特征
- 1x1 卷积输出单通道深度

### 2.3 多尺度输出

```python
class MultiScaleDepthNet(nn.Module):
    """
    多尺度深度估计网络

    在解码器的多个层级输出深度图，用于深度监督训练。

    输出:
    - depth_1: 1/4 分辨率
    - depth_2: 1/8 分辨率
    - depth_3: 1/16 分辨率
    - depth_4: 1/32 分辨率
    """
```

**优点**:
- 深度监督加速训练
- 多尺度特征融合
- 更好的梯度流

## 3. 损失函数设计

### 3.1 损失函数组合

```python
class CombinedDepthLoss(nn.Module):
    """
    组合损失函数

    L = w_mse * MSE + w_mae * MAE + w_silog * SILog + w_grad * Gradient

    默认权重:
    - MSE: 1.0
    - MAE: 0.5
    - SILog: 1.0
    - Gradient: 0.5
    """
```

### 3.2 各损失函数的作用

| 损失函数 | 作用 | 权重 |
|----------|------|------|
| MSE | 逐像素精度 | 1.0 |
| MAE | 鲁棒性 | 0.5 |
| SILog | 尺度不变性 | 1.0 |
| Gradient | 边缘保持 | 0.5 |

### 3.3 损失函数实现

```python
# MSE Loss
L_mse = mean((pred - target)^2)

# MAE Loss
L_mae = mean(|pred - target|)

# SILog Loss
d = log(pred) - log(target)
L_silog = mean(d^2) - lambda * mean(d)^2

# Gradient Loss
L_grad = |grad_x(pred) - grad_x(target)| + |grad_y(pred) - grad_y(target)|
```

## 4. 数据流设计

### 4.1 训练流程

```
1. 数据加载
   Dataset → DataLoader → Batch(images, depths, masks)

2. 前向传播
   images → Encoder → features → Decoder → pred_depths

3. 损失计算
   pred_depths + depths + masks → Loss → loss_dict

4. 反向传播
   loss.backward() → gradients

5. 参数更新
   optimizer.step() → updated_parameters
```

### 4.2 推理流程

```
1. 图像预处理
   image → normalize → tensor

2. 前向传播
   tensor → model → pred_depth

3. 后处理
   pred_depth → denormalize → depth_map
```

## 5. 评估指标设计

### 5.1 指标计算

```python
def compute_depth_metrics(pred, target, valid_mask):
    """
    计算深度估计评估指标

    返回:
    - abs_rel: 绝对相对误差
    - sq_rel: 平方相对误差
    - rmse: 均方根误差
    - rmse_log: 对数均方根误差
    - delta1: delta < 1.25
    - delta2: delta < 1.25^2
    - delta3: delta < 1.25^3
    """
```

### 5.2 指标评估流程

```
1. 批量推理
   for batch in test_loader:
       pred = model(batch.images)

2. 指标计算
   metrics = compute_depth_metrics(pred, batch.depths)

3. 指标平均
   avg_metrics = mean(all_metrics)
```

## 6. 可视化设计

### 6.1 深度图着色

```python
def colorize_depth(depth, colormap="jet"):
    """
    将深度图转换为彩色可视化

    流程:
    1. 归一化深度到 [0, 1]
    2. 应用颜色映射
    3. 输出 RGB 图像
    """
```

### 6.2 可视化布局

```
┌──────────────────────────────────────────┐
│  输入图像  │  预测深度  │  目标深度     │
└──────────────────────────────────────────┘
```

## 7. 扩展性设计

### 7.1 模型扩展

- 更换编码器（ResNet, EfficientNet, ViT）
- 添加注意力机制
- 多任务学习

### 7.2 损失函数扩展

- 添加感知损失
- 添加对抗损失
- 自适应权重

### 7.3 数据扩展

- 支持真实数据集
- 数据增强管道
- 在线数据生成

## 8. 性能优化

### 8.1 训练优化

- 混合精度训练
- 梯度累积
- 学习率调度

### 8.2 推理优化

- 模型量化
- 模型剪枝
- TensorRT 优化
