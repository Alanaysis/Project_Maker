# DETR 目标检测 - 研究文档

## 1. 背景与动机

### 1.1 传统目标检测的局限性

传统目标检测方法（如 Faster R-CNN、YOLO）依赖于：
- **锚框（Anchor Boxes）**：预定义的边界框模板
- **非极大值抑制（NMS）**：后处理步骤，去除冗余检测
- **手工设计的组件**：区域提议网络（RPN）、特征金字塔等

这些组件增加了模型复杂性，且需要大量调参。

### 1.2 DETR 的创新

DETR（DEtection TRansformer）由 Facebook AI Research 于 2020 年提出，主要创新：

1. **端到端训练**：无需手工组件
2. **集合预测**：直接预测一组检测结果
3. **二分图匹配**：使用匈牙利算法匹配预测与真实标签
4. **Transformer 架构**：利用注意力机制捕获全局信息

## 2. DETR 架构

### 2.1 整体架构

```
输入图像
    ↓
CNN 骨干网络 (ResNet)
    ↓
Transformer 编码器
    ↓
Transformer 解码器 (Object Queries)
    ↓
预测头 (分类 + 边界框)
    ↓
匈牙利匹配损失
```

### 2.2 核心组件

#### 2.2.1 CNN 骨干网络
- 提取图像特征
- 常用 ResNet-50/101
- 输出特征图尺寸：H/32 × W/32

#### 2.2.2 Transformer 编码器
- 处理特征图序列
- 位置编码保留空间信息
- 自注意力机制捕获全局依赖

#### 2.2.3 Transformer 解码器
- 使用可学习的 Object Queries
- 交叉注意力关注图像特征
- 并行解码所有对象

#### 2.2.4 预测头
- 分类头：预测类别（包括"无对象"类别）
- 边界框头：预测 [cx, cy, w, h]

## 3. 匈牙利匹配

### 3.1 匹配问题

给定 N 个预测和 M 个真实标签（N > M），找到最优的一对一匹配。

### 3.2 匹配代价

```
C(i,j) = λ_cls · L_cls(i,j) + λ_bbox · L_bbox(i,j) + λ_giou · L_giou(i,j)
```

- **分类代价**：负对数似然
- **边界框代价**：L1 距离
- **GIoU 代价**：广义 IoU 损失

### 3.3 匈牙利算法

使用 `scipy.optimize.linear_sum_assignment` 求解最优匹配。

## 4. 集合预测损失

### 4.1 损失组成

```
L = λ_cls · L_cls + λ_bbox · L_bbox + λ_giou · L_giou
```

### 4.2 分类损失

使用 Focal Loss 处理类别不平衡：
- 正样本：匹配到真实标签的预测
- 负样本：未匹配的预测（"无对象"类别）

### 4.3 边界框损失

- **L1 损失**：边界框坐标误差
- **GIoU 损失**：考虑边界框重叠和距离

## 5. 相关工作

### 5.1 DETR 变体

| 模型 | 改进点 | 年份 |
|------|--------|------|
| DETR | 原始模型 | 2020 |
| Deformable DETR | 可变形注意力 | 2021 |
| DAB-DETR | 动态锚框 | 2022 |
| DN-DETR | 去噪训练 | 2022 |
| RT-DETR | 实时检测 | 2023 |

### 5.2 与其他方法的比较

| 方法 | 锚框 | NMS | 端到端 | 实时性 |
|------|------|-----|--------|--------|
| Faster R-CNN | ✓ | ✓ | ✗ | 中 |
| YOLO | ✓ | ✓ | ✗ | 高 |
| DETR | ✗ | ✗ | ✓ | 低 |

## 6. 学习资源

### 6.1 论文
- [End-to-End Object Detection with Transformers](https://arxiv.org/abs/2005.12872)
- [Deformable DETR](https://arxiv.org/abs/2010.04159)

### 6.2 代码
- [官方实现](https://github.com/facebookresearch/detr)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/model_doc/detr)

### 6.3 教程
- [DETR 详解](https://arxiv.org/abs/2005.12872)
- [PyTorch DETR Tutorial](https://pytorch.org/tutorials/intermediate/detr_tutorial.html)
