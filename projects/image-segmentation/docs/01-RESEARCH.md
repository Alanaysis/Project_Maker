# 01 - 调研文档：图像分割

## 1. 图像分割简介

图像分割是计算机视觉中的基础任务，目标是将图像中的每个像素分配到一个语义类别。与图像分类（整张图一个标签）和目标检测（给出边界框）不同，图像分割提供了像素级的精细理解。

### 1.1 分割任务分类

| 任务 | 描述 | 输出 | 代表方法 |
|------|------|------|----------|
| 语义分割 | 每个像素分配一个类别标签 | 像素级类别图 | FCN, U-Net, DeepLab |
| 实例分割 | 区分同类物体的不同实例 | 像素级实例图 | Mask R-CNN |
| 全景分割 | 语义分割 + 实例分割的统一 | 像素级全景图 | Panoptic FPN |

### 1.2 应用场景

- **医学影像**：器官分割、肿瘤检测、细胞分割
- **自动驾驶**：道路分割、行人检测、可行驶区域
- **遥感图像**：地物分类、建筑物提取、植被监测
- **人像分割**：背景替换、美颜、特效
- **工业检测**：缺陷检测、质量控制

## 2. 语义分割发展历史

### 2.1 传统方法

- **阈值法**：基于像素灰度值的简单分割
- **区域生长**：从种子点扩展相似区域
- **边缘检测**：基于梯度的边缘提取
- **图割方法**：将分割建模为图的最小割问题

### 2.2 深度学习方法

| 年份 | 方法 | 贡献 |
|------|------|------|
| 2014 | FCN | 首次将 CNN 用于端到端分割 |
| 2015 | U-Net | 编码器-解码器 + 跳跃连接 |
| 2015 | SegNet | 编码器-解码器 + 池化索引 |
| 2017 | DeepLab v3 | 空洞卷积 + ASPP |
| 2017 | PSPNet | 金字塔池化模块 |
| 2019 | HRNet | 高分辨率特征保持 |
| 2021 | SegFormer | Transformer 用于分割 |

## 3. U-Net 详解

### 3.1 历史背景

U-Net 由 Olaf Ronneberger 等人于 2015 年提出，最初用于医学图像分割。论文标题中的 "U-Net" 源于其 U 形的网络结构。

**论文信息**：
- 标题：U-Net: Convolutional Networks for Biomedical Image Segmentation
- 会议：MICCAI 2015
- 引用数：50,000+（截至 2024 年）

### 3.2 核心创新

1. **编码器-解码器结构**：对称的收缩和扩张路径
2. **跳跃连接**：将编码器特征直接传递给解码器
3. **数据增强**：使用弹性变形进行数据增强
4. **Overlap-Tile 策略**：处理大图像的无缝分割

### 3.3 架构详解

```
输入 (572x572x1)
    |
[编码器]
    |-- 64 通道, 568x568
    |-- MaxPool -> 128 通道, 280x280
    |-- MaxPool -> 256 通道, 136x136
    |-- MaxPool -> 512 通道, 64x64
    |-- MaxPool -> 1024 通道, 28x28 (瓶颈)
    |
[解码器]
    |-- UpConv + Skip -> 512 通道, 52x52
    |-- UpConv + Skip -> 256 通道, 100x100
    |-- UpConv + Skip -> 128 通道, 196x196
    |-- UpConv + Skip -> 64 通道, 388x388
    |
输出 (388x388x1)
```

### 3.4 跳跃连接的作用

**问题**：编码器通过多次下采样丢失了空间细节信息。

**解决方案**：跳跃连接将编码器各层的特征直接传递给解码器对应层。

**效果**：
- 恢复空间细节（边缘、纹理）
- 加速训练收敛
- 提高分割精度

## 4. 上采样技术

### 4.1 最近邻插值

最简单的上采样方式，将每个像素复制到 2x2 区域。

**优点**：计算简单，无参数
**缺点**：产生块状伪影

### 4.2 双线性插值

基于相邻 4 个像素的加权平均进行插值。

**优点**：结果平滑
**缺点**：可能模糊边缘

### 4.3 转置卷积 (Transposed Convolution)

也称为反卷积（Deconvolution），通过学习的卷积核进行上采样。

**优点**：可以学习上采样方式
**缺点**：可能产生棋盘伪影（checkerboard artifacts）

**原理**：
```
输入 (2x2) --[转置卷积 kernel=3x3, stride=2]--> 输出 (4x4)
```

### 4.4 亚像素卷积 (Pixel Shuffle)

通过重排通道维度来实现上采样。

**优点**：无棋盘伪影
**缺点**：需要较多通道

## 5. 损失函数

### 5.1 交叉熵损失 (Cross-Entropy Loss)

像素级分类损失，对每个像素独立计算。

**问题**：类别不平衡时，背景像素主导梯度。

### 5.2 Dice Loss

基于 Dice 系数的损失函数，衡量预测与真值的重叠度。

**优点**：对类别不平衡鲁棒
**缺点**：梯度可能不稳定

### 5.3 Focal Loss

对难分类样本给予更大权重。

**公式**：FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

### 5.4 组合损失

实际应用中常组合多种损失：
- BCE + Dice
- CE + Dice + 边界损失

## 6. 评估指标

### 6.1 IoU (Intersection over Union)

```
IoU = |A ∩ B| / |A ∪ B|
```

最常用的分割评估指标，也称为 Jaccard 指数。

### 6.2 Dice 系数

```
Dice = 2 * |A ∩ B| / (|A| + |B|)
```

与 IoU 相关但更常用在医学影像领域。

### 6.3 像素准确率 (Pixel Accuracy)

```
PA = 正确分类的像素数 / 总像素数
```

简单但在类别不平衡时有误导性。

### 6.4 平均 IoU (mIoU)

所有类别的 IoU 的平均值，是语义分割的标准评估指标。

## 7. 数据增强策略

### 7.1 几何变换

- 随机翻转（水平/垂直）
- 随机旋转
- 随机缩放
- 弹性变形（U-Net 论文的关键创新）

### 7.2 颜色变换

- 亮度/对比度调整
- 颜色抖动
- 高斯噪声

### 7.3 裁剪策略

- 随机裁剪
- 中心裁剪
- Overlap-Tile（U-Net 论文）

## 8. 参考文献

1. Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. MICCAI.
2. Long, J., Shelhamer, E., & Darrell, T. (2015). Fully Convolutional Networks for Semantic Segmentation. CVPR.
3. Chen, L. C., et al. (2017). DeepLab: Semantic Image Segmentation with Deep Convolutional Nets, Atrous Convolution, and Fully Connected CRFs. TPAMI.
4. Zhao, H., et al. (2017). Pyramid Scene Parsing Network. CVPR.
5. Milletari, F., Navab, N., & Ahmadi, S. A. (2016). V-Net: Fully Convolutional Neural Networks for Volumetric Medical Image Segmentation. 3DV.
