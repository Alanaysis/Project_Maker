# 01 - 文字检测调研

## 1. 文字检测概述

文字检测（Text Detection）是计算机视觉中的一个重要任务，目标是在图像中自动定位文字区域。它是文字识别（OCR）系统的第一步，广泛应用于：

- 文档数字化
- 车牌识别
- 街景文字识别
- 工业质检
- 自动驾驶（路标识别）

## 2. 主流方法

### 2.1 传统方法

| 方法 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| MSER | 最大稳定极值区域 | 速度快 | 对噪声敏感 |
| SWT | 笔画宽度变换 | 对字体鲁棒 | 对复杂背景效果差 |
| 滑动窗口 | 逐窗口分类 | 简单直观 | 计算量大 |

### 2.2 深度学习方法

| 方法 | 年份 | 特点 |
|------|------|------|
| CTPN | 2016 | 基于 Faster R-CNN，检测文字线 |
| EAST | 2017 | 单阶段，高效准确 |
| PixelLink | 2018 | 基于像素链接 |
| DBNet | 2020 | 可微分二值化 |
| DBNet++ | 2022 | 自适应特征增强 |

## 3. EAST 架构详解

### 3.1 设计理念

EAST (Efficient and Accurate Scene Text Detector) 的核心设计理念：

1. **单阶段检测**：无需候选区域生成，直接预测
2. **端到端训练**：简化训练流程
3. **多任务学习**：同时预测分数和几何信息

### 3.2 网络结构

```
输入图像 (H x W x 3)
    │
    ├── Backbone (PVANet/ResNet)
    │   ├── Stage 1: H/2 x W/2 x 64
    │   ├── Stage 2: H/4 x W/4 x 128
    │   ├── Stage 3: H/8 x W/8 x 256
    │   └── Stage 4: H/16 x W/16 x 512
    │
    ├── Feature Merging (U-Net)
    │   ├── Merge 1: H/8 x W/8 x 128
    │   ├── Merge 2: H/4 x W/4 x 64
    │   └── Merge 3: H/4 x W/4 x 32
    │
    └── Output Head
        ├── Score Map: H/4 x W/4 x 1
        └── Geometry Map: H/4 x W/4 x 5 (RBOX)
```

### 3.3 几何表示

#### RBOX (Rotated Bounding Box)
```
        top
    ┌───────────┐
    │           │
left│   text    │right
    │           │
    └───────────┘
        bottom
```
- 5 个通道：top, right, bottom, left, angle
- 距离表示：每个像素到四条边的距离

#### QUAD (Quadrilateral)
- 8 个通道：4 个角点的偏移 (dx, dy)
- 适用于任意四边形文字

## 4. CTPN 架构详解

### 4.1 设计理念

CTPN (Connectionist Text Proposal Network) 的核心思想：

1. **文字提议**：检测固定宽度的小文字块
2. **序列建模**：使用 BiLSTM 捕获上下文
3. **后处理合并**：将文字块合并成文字行

### 4.2 网络结构

```
输入图像
    │
    ├── VGG16 Backbone
    │
    ├── RPN (Region Proposal Network)
    │   └── 固定宽度 anchor (16px)
    │
    ├── BiLSTM
    │   └── 序列上下文建模
    │
    └── Output
        ├── 文字/非文字分类
        └── 边界框回归
```

## 5. 最新进展

### 5.1 DBNet (2020)
- 可微分二值化：替代固定阈值
- 自适应阈值学习
- 更好的边界检测

### 5.2 Transformer-based 方法 (2022+)
- Vision Transformer 用于特征提取
- 更强的全局上下文建模
- 端到端文字检测与识别

### 5.3 轻量化方法
- MobileNet backbone
- 知识蒸馏
- 模型量化

## 6. 评估指标

### 6.1 IoU (Intersection over Union)
```
IoU = Area of Overlap / Area of Union
```

### 6.2 Precision, Recall, F-measure
- Precision: 检测正确的比例
- Recall: 真实文字被检测到的比例
- F-measure: Precision 和 Recall 的调和平均

### 6.3 Hmean
在 ICDAR 数据集上常用的评估指标：
```
Hmean = 2 * Precision * Recall / (Precision + Recall)
```

## 7. 常用数据集

| 数据集 | 语言 | 图片数 | 特点 |
|--------|------|--------|------|
| ICDAR 2015 | 英文 | 1000 | 自然场景 |
| ICDAR 2017 MLT | 多语言 | 7200 | 多语言 |
| CTW | 中文 | 32285 | 中文场景 |
| TotalText | 英文 | 1555 | 弯曲文字 |
| MSRA-TD500 | 中英文 | 500 | 文档场景 |

## 8. 实际应用场景

### 8.1 文档文字检测
- 扫描件文字定位
- 表格检测
- 版面分析

### 8.2 自然场景文字
- 街景文字识别
- 商品包装文字
- 车牌识别

### 8.3 工业应用
- PCB 文字检测
- 零件编号识别
- 质量标签检测

## 9. 学习资源

### 论文
- [EAST: An Efficient and Accurate Scene Text Detector](https://arxiv.org/abs/1704.03155)
- [Detecting Text in Natural Image with CTPN](https://arxiv.org/abs/1609.03605)
- [Real-Time Scene Text Detection with DBNet](https://arxiv.org/abs/1911.08947)

### 开源实现
- [EAST (TensorFlow)](https://github.com/argman/EAST)
- [DBNet (PyTorch)](https://github.com/MhLiao/DB)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)

### 教程
- [OpenCV Text Detection](https://www.pyimagesearch.com/2018/08/20/opencv-text-detection-east-text-detector/)
- [Scene Text Detection Tutorial](https://towardsdatascience.com/scene-text-detection-with-python-2b6b359a0668)
