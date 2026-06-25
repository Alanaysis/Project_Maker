# 研究笔记 - 人体姿态估计

## 背景

人体姿态估计是计算机视觉的基础任务之一，广泛应用于：
- 动作识别
- 人机交互
- 运动分析
- 虚拟现实
- 医疗康复

## 主流方法对比

### 1. 热力图回归方法 (Heatmap-based)

**代表方法**: SimpleBaseline, HRNet, Stacked Hourglass

**原理**:
- 为每个关键点预测一个高斯热力图
- 热力图峰值位置即为关键点坐标
- 使用 MSE 损失训练

**优点**:
- 精度高
- 可以表达不确定性
- 适合多关键点检测

**缺点**:
- 计算量较大
- 需要后处理

### 2. 回归方法 (Regression-based)

**代表方法**: CPM, DeepPose

**原理**:
- 直接从图像特征回归关键点坐标
- 使用 L1/L2 损失训练

**优点**:
- 计算量小
- 端到端训练

**缺点**:
- 精度较低
- 难以表达不确定性

### 3. 基于 Transformer 的方法

**代表方法**: ViTPose, TokenPose

**原理**:
- 使用 Vision Transformer 提取特征
- 利用注意力机制建模关键点关系

**优点**:
- 全局建模能力强
- 精度高

**缺点**:
- 计算量大
- 需要大量数据

## 网络架构演进

### Stacked Hourglass (2016)

```
输入 → 编码器 → 解码器 → 中间监督
     → 编码器 → 解码器 → 中间监督
     → ... → 最终输出
```

**特点**:
- 多尺度特征融合
- 中间监督
- 沙漏结构

### SimpleBaseline (2018)

```
输入 → ResNet → 反卷积 → 热力图
```

**特点**:
- 架构简单
- 效果好
- 易于实现

### HRNet (2019)

```
输入 → 高分辨率分支 ──────────→ 高分辨率输出
     → 中分辨率分支 ←→ 高分辨率分支
     → 低分辨率分支 ←→ 中分辨率分支
```

**特点**:
- 保持高分辨率
- 多尺度并行
- 精度高

## 关键技术

### 1. 热力图生成

高斯热力图公式：
```
H(x, y) = exp(-((x - x_k)^2 + (y - y_k)^2) / (2 * sigma^2))
```

**sigma 选择**:
- sigma 小 (1-2): 热力图集中，适合高分辨率
- sigma 大 (3-5): 热力图分散，适合低分辨率

### 2. 关键点提取

**Argmax**:
```python
keypoint = argmax(heatmap)
```

**Soft-Argmax** (可微):
```python
keypoint = sum(x * softmax(beta * heatmap))
```

**亚像素精度**:
```python
# 在 argmax 邻域内插值
dx = (H[x-1] - H[x+1]) / (2 * (H[x-1] + H[x+1] - 2*H[x]))
```

### 3. 损失函数

**MSE Loss**:
```python
L = ||pred_heatmap - gt_heatmap||^2
```

**OKHMLoss** (Online Hard Keypoint Mining):
```python
# 只对损失最大的 Top-K 个关键点计算损失
topk_loss = topk(per_keypoint_loss, k)
loss = mean(topk_loss)
```

### 4. 数据增强

**常用增强**:
- 随机翻转 (水平)
- 随机旋转 (-30° ~ 30°)
- 随机缩放 (0.75 ~ 1.25)
- 颜色抖动
- 遮挡增强

**关键点变换**:
- 翻转时需要交换左右关键点
- 旋转/缩放时需要变换关键点坐标

## 评估指标

### PCK (Percentage of Correct Keypoints)

```
PCK = |{d(pred, gt) < threshold * ref_length}| / |all keypoints|
```

- threshold: 通常 0.05 ~ 0.2
- ref_length: 图像对角线或躯干长度

### OKS (Object Keypoint Similarity)

```
OKS = sum(exp(-d^2 / (2 * s^2 * kappa^2)) * v) / sum(v)
```

- d: 预测与 GT 的距离
- s: 目标面积的平方根
- kappa: 每个关键点的标准差 (COCO 给定)
- v: 可见性标记

### AP (Average Precision)

基于 OKS 计算：
```
AP = integral(precision-recall curve)
```

## 数据集

### COCO Keypoints

- 200K 图像
- 250K 人体实例
- 17 个关键点
- 评估指标: AP (OKS)

### MPII Human Pose

- 25K 图像
- 40K 人体实例
- 16 个关键点
- 评估指标: PCKh

## 参考论文

1. **SimpleBaseline**: Xiao et al., "Simple Baselines for Human Pose Estimation and Tracking", ECCV 2018
2. **HRNet**: Sun et al., "Deep High-Resolution Representation Learning for Visual Recognition", CVPR 2019
3. **Stacked Hourglass**: Newell et al., "Stacked Hourglass Networks for Human Pose Estimation", ECCV 2016
4. **CPM**: Wei et al., "Convolutional Pose Machines", CVPR 2016
5. **ViTPose**: Xu et al., "ViTPose: Simple Vision Transformer Baselines for Human Pose Estimation", NeurIPS 2022
