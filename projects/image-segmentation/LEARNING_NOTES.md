# 学习笔记：图像分割

## 1. 项目目标

从零实现 U-Net 语义分割网络，深入理解编码器-解码器架构和跳跃连接的核心原理：
- 理解语义分割
- 掌握 U-Net 架构
- 学会上采样

## 2. 核心概念

### 2.1 什么是语义分割？

语义分割是计算机视觉中的像素级分类任务：
- 输入：一张图像 (H x W x C)
- 输出：每个像素的类别标签 (H x W)
- 目标：理解图像中每个像素属于什么物体

**与相关任务的区别**：

| 任务 | 输出 | 粒度 |
|------|------|------|
| 图像分类 | 一个标签 | 整张图 |
| 目标检测 | 边界框 + 标签 | 区域级 |
| 语义分割 | 像素级标签 | 像素级 |
| 实例分割 | 像素级实例标签 | 像素级（区分实例） |

### 2.2 U-Net 架构

U-Net 是一种编码器-解码器架构，由 Olaf Ronneberger 等人于 2015 年提出。

**核心思想**：
1. 编码器逐步下采样，提取语义特征
2. 解码器逐步上采样，恢复空间分辨率
3. 跳跃连接融合低层细节和高层语义

**为什么叫 U-Net？**

因为网络结构呈 U 形：
```
输入 → [编码器] → 瓶颈 → [解码器] → 输出
         ↓                      ↑
         └──── 跳跃连接 ────┘
```

### 2.3 跳跃连接

**问题**：编码器通过多次下采样丢失了空间细节信息。

**解决方案**：跳跃连接将编码器各层的特征直接传递给解码器对应层。

**作用**：
- 恢复空间细节（边缘、纹理）
- 加速训练收敛
- 提高分割精度

**实现方式**：
```python
# 编码器保存中间特征
skips = [layer1_out, layer2_out, layer3_out, layer4_out]

# 解码器逐层融合
x = bottleneck
for i, up in enumerate(up_blocks):
    x = up(x, skips[n_levels - 1 - i])  # 上采样 + 拼接 + 卷积
```

## 3. 实现细节

### 3.1 DoubleConv 块

每个 DoubleConv 包含两次 3x3 卷积，每次后跟 BatchNorm 和 ReLU。

**设计要点**：
- padding=1 保持空间尺寸不变
- bias=False 当使用 BatchNorm 时
- inplace=True 节省内存

```python
Conv2d(3, 64, 3, padding=1) → BN(64) → ReLU → Conv2d(64, 64, 3, padding=1) → BN(64) → ReLU
```

### 3.2 编码器（收缩路径）

编码器通过下采样逐步减小空间尺寸，增加通道数。

```
输入 (3, 256, 256)
    ↓ DoubleConv
(64, 256, 256)  ← skip_0
    ↓ MaxPool + DoubleConv
(128, 128, 128) ← skip_1
    ↓ MaxPool + DoubleConv
(256, 64, 64)   ← skip_2
    ↓ MaxPool + DoubleConv
(512, 32, 32)   ← skip_3
    ↓ MaxPool + DoubleConv
(1024, 16, 16)  ← bottleneck
```

### 3.3 解码器（扩张路径）

解码器通过上采样逐步恢复空间尺寸，减少通道数。

```
bottleneck (1024, 16, 16)
    ↓ Upsample + Concat(skip_3) + DoubleConv
(512, 32, 32)
    ↓ Upsample + Concat(skip_2) + DoubleConv
(256, 64, 64)
    ↓ Upsample + Concat(skip_1) + DoubleConv
(128, 128, 128)
    ↓ Upsample + Concat(skip_0) + DoubleConv
(64, 256, 256)
    ↓ Conv2d 1x1
(1, 256, 256)
```

### 3.4 上采样方式

**双线性插值**：
- 将像素值按距离加权平均
- 结果平滑，无棋盘伪影
- 无可学习参数

**转置卷积**：
- 通过学习的卷积核进行上采样
- 可以学习上采样方式
- 可能产生棋盘伪影

**选择**：默认使用双线性插值，因为更稳定。

### 3.5 损失函数

**Dice Loss**：
```
Dice = 2 * |预测 ∩ 真值| / (|预测| + |真值|)
Loss = 1 - Dice
```

**优点**：对类别不平衡鲁棒
**缺点**：梯度可能不稳定

**BCE + Dice 组合**：
```
Loss = 0.5 * BCE + 0.5 * Dice
```

结合两种损失的优势。

## 4. 关键收获

### 4.1 编码器-解码器的力量

- 编码器提取语义特征，解码器恢复空间细节
- 跳跃连接是关键创新，融合了多尺度信息
- 这种架构可以端到端训练

### 4.2 跳跃连接的重要性

- 解决了深层网络中空间信息丢失的问题
- 加速了训练收敛
- 显著提高了分割精度

### 4.3 上采样的选择

- 双线性插值：简单、稳定、无棋盘伪影
- 转置卷积：可学习、但可能有伪影
- 实际应用中差异不大，双线性插值是更安全的选择

### 4.4 损失函数的设计

- 像素级交叉熵：类别不平衡时效果差
- Dice Loss：对类别不平衡鲁棒
- 组合损失：结合多种损失的优势

## 5. 实际应用

### 5.1 医学影像

- 器官分割（心脏、肝脏、肾脏）
- 肿瘤检测和分割
- 细胞分割

### 5.2 自动驾驶

- 道路分割
- 行人检测
- 可行驶区域

### 5.3 遥感图像

- 地物分类
- 建筑物提取
- 植被监测

### 5.4 人像分割

- 背景替换
- 美颜
- 特效

## 6. 超参数调优

### 6.1 关键超参数

| 超参数 | 作用 | 建议值 |
|--------|------|--------|
| base_channels | 基础通道数 | 32-64 |
| n_levels | 网络深度 | 3-4 |
| learning_rate | 学习率 | 1e-3 到 1e-4 |
| batch_size | 批大小 | 4-16 |
| loss_fn | 损失函数 | BCE + Dice |

### 6.2 调优策略

- **base_channels**：越大模型越强，但计算量和内存需求也越大
- **n_levels**：越深感受野越大，但细节丢失也越多
- **learning_rate**：配合学习率调度器使用
- **batch_size**：根据 GPU 内存调整

## 7. 与其他方法的对比

| 方法 | 特点 | 适用场景 |
|------|------|----------|
| FCN | 简单、端到端 | 粗粒度分割 |
| U-Net | 跳跃连接、细节恢复 | 医学影像、精细分割 |
| DeepLab | 空洞卷积、多尺度 | 自然场景分割 |
| SegFormer | Transformer、全局特征 | 大场景分割 |

## 8. 数学基础

### 8.1 卷积输出尺寸

```
H_out = (H_in + 2*padding - kernel_size) / stride + 1
```

对于 3x3 卷积、padding=1、stride=1：
```
H_out = (H_in + 2*1 - 3) / 1 + 1 = H_in
```

### 8.2 池化输出尺寸

对于 2x2 最大池化、stride=2：
```
H_out = H_in / 2
```

### 8.3 转置卷积输出尺寸

```
H_out = (H_in - 1) * stride - 2*padding + kernel_size
```

对于 kernel=2、stride=2、padding=0：
```
H_out = (H_in - 1) * 2 + 2 = 2 * H_in
```

### 8.4 Dice 系数

```
Dice = 2 * |A ∩ B| / (|A| + |B|)
     = 2 * TP / (2 * TP + FP + FN)
```

与 IoU 的关系：
```
Dice = 2 * IoU / (1 + IoU)
IoU = Dice / (2 - Dice)
```

## 9. 调试经验

### 9.1 常见问题

1. **形状不匹配**：检查 skip_channels 配置
2. **尺寸不匹配**：确保输入尺寸是 2 的幂，或使用 padding 处理
3. **内存不足**：减小 base_channels 或 n_levels
4. **训练不收敛**：检查学习率和损失函数

### 9.2 调试技巧

- 打印每层的输出形状
- 检查梯度是否正常流动
- 使用小数据集快速验证
- 可视化分割结果

## 10. 进一步学习

### 10.1 相关架构

- **Attention U-Net**：添加注意力机制
- **U-Net++**：密集跳跃连接
- **U-Net 3D**：三维分割
- **TransUNet**：Transformer + U-Net

### 10.2 深入主题

- 语义分割的最新进展
- 实例分割（Mask R-CNN）
- 全景分割
- 视频分割

### 10.3 参考资料

- Ronneberger, O., et al. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation.
- Long, J., et al. (2015). Fully Convolutional Networks for Semantic Segmentation.
- [PyTorch Segmentation Models](https://github.com/qubvel/segmentation_models.pytorch)
