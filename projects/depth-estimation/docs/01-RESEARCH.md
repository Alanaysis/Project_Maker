# 研究笔记 - 深度估计

## 1. 深度估计概述

### 1.1 定义

深度估计是从 2D 图像推断 3D 深度信息的任务。对于每个像素 (x, y)，预测其到相机的距离 d。

### 1.2 应用场景

- **自动驾驶**: 感知周围环境的 3D 结构
- **机器人导航**: 避障和路径规划
- **增强现实**: 虚实融合
- **3D 重建**: 从单张图像重建 3D 模型
- **图像编辑**: 景深效果、背景虚化

### 1.3 深度传感器 vs 深度估计

| 方法 | 优点 | 缺点 |
|------|------|------|
| LiDAR | 高精度、远距离 | 成本高、稀疏 |
| 结构光 | 高精度、密集 | 近距离、室外受限 |
| ToF | 实时、低功耗 | 分辨率低 |
| 深度估计 | 成本低、密集 | 精度相对低 |

## 2. 单目深度估计方法

### 2.1 有监督方法

使用真实深度图作为监督信号。

**代表论文**:
- Eigen et al. (2014): 多尺度网络
- Laina et al. (2016): 全卷积残差网络
- Fu et al. (2018): 有序回归

**挑战**:
- 需要大量标注数据
- 深度标注获取困难
- 泛化能力有限

### 2.2 自监督方法

利用视频序列或双目图像进行自监督训练。

**代表论文**:
- Godard et al. (2017): 左右一致性
- Zhou et al. (2017): 视图合成
- Bian et al. (2019): 几何一致性

**优点**:
- 不需要深度标注
- 可以使用大量视频数据
- 泛化能力更强

### 2.3 基于 Transformer 的方法

使用 Vision Transformer 作为编码器。

**代表论文**:
- Ranftl et al. (2021): DPT
- Bhat et al. (2021): AdaBins

**优点**:
- 全局感受野
- 更强的特征提取能力
- 多尺度特征融合

## 3. 编码器-解码器架构

### 3.1 编码器设计

**常用骨干网络**:
- ResNet (He et al., 2016)
- EfficientNet (Tan & Le, 2019)
- Vision Transformer (Dosovitskiy et al., 2020)

**设计原则**:
- 逐步下采样，提取多尺度特征
- 使用残差连接保证梯度流
- 使用 BatchNorm 稳定训练

### 3.2 解码器设计

**常用结构**:
- 反卷积上采样
- 双线性插值 + 卷积
- 亚像素卷积

**跳跃连接**:
- 融合编码器的低级特征
- 保持空间细节
- 缓解梯度消失

### 3.3 多尺度特征融合

**FPN (Feature Pyramid Network)**:
- 自顶向下路径
- 横向连接
- 多尺度预测

**ASPP (Atrous Spatial Pyramid Pooling)**:
- 多尺度空洞卷积
- 全局上下文
- 并行处理

## 4. 损失函数

### 4.1 逐像素损失

**L1 Loss**:
```
L = mean(|pred - target|)
```

**L2 Loss (MSE)**:
```
L = mean((pred - target)^2)
```

**Huber Loss**:
```
L = 0.5 * e^2, if |e| <= delta
L = delta * (|e| - 0.5 * delta), otherwise
```

### 4.2 尺度不变损失

**SILog Loss**:
```
L = (1/n) * sum(d_i^2) - (lambda/n^2) * (sum(d_i))^2
d_i = log(pred_i) - log(target_i)
```

**优点**:
- 对深度的绝对尺度不敏感
- 鼓励相对深度正确

### 4.3 边缘保持损失

**Gradient Loss**:
```
L = |grad_x(pred) - grad_x(target)| + |grad_y(pred) - grad_y(target)|
```

**优点**:
- 保持边缘锐利
- 与逐像素损失互补

### 4.4 组合损失

```python
L = w1 * MSE + w2 * SILog + w3 * Gradient
```

## 5. 评估指标

### 5.1 绝对指标

- **Abs Rel**: 绝对相对误差
- **Sq Rel**: 平方相对误差
- **RMSE**: 均方根误差
- **RMSE Log**: 对数均方根误差

### 5.2 阈值指标

- **delta < 1.25**: 预测深度在 25% 误差范围内的比例
- **delta < 1.25^2**: 预测深度在 56% 误差范围内的比例
- **delta < 1.25^3**: 预测深度在 95% 误差范围内的比例

### 5.3 相对指标

- **SILog**: 尺度不变对数误差
- **log10**: 对数误差

## 6. 数据集

### 6.1 室内数据集

**NYU Depth V2**:
- 1449 张标注图像
- 407,024 帧未标注视频
- 640 x 480 分辨率
- 深度范围 0-10m

**ScanNet**:
- 1513 个场景
- 2.5M 帧
- 深度 + 语义标注

### 6.2 室外数据集

**KITTI**:
- 自动驾驶场景
- 深度范围 0-80m
- 稀疏 LiDAR 标注

**Make3D**:
- 534 张图像
- 深度范围 0-80m
- 室外场景

### 6.3 混合数据集

**DIODE**:
- 室内 + 室外
- 高质量深度标注
- 多种场景

## 7. 最新进展

### 7.1 Foundation Models

- **MiDaS**: 鲁棒的单目深度估计
- **DPT**: Dense Prediction Transformer
- ** ZoeDepth**: 零样本深度估计

### 7.2 生成式方法

- **Marigold**: 基于 Stable Diffusion 的深度估计
- **Depth Anything**: 大规模预训练

### 7.3 实时方法

- **FastDepth**: 实时深度估计
- **MobileDepth**: 移动端深度估计

## 8. 参考文献

1. Eigen, D., Puhrsch, C., & Fergus, R. (2014). Depth Map Prediction from a Single Image using a Multi-Scale Deep Network.
2. Laina, I., et al. (2016). Deeper Depth Prediction with Fully Convolutional Residual Networks.
3. Godard, C., et al. (2017). Unsupervised Monocular Depth Estimation with Left-Right Consistency.
4. Ranftl, R., et al. (2021). Vision Transformers for Dense Prediction.
5. Bhat, S. F., et al. (2021). AdaBins: Depth Estimation Using Adaptive Bins.
6. Yang, L., et al. (2024). Depth Anything: Unleashing the Power of Large-Scale Unlabeled Data.
