# 研究文档：OCR 文字识别

## 1. 背景知识

### 1.1 什么是 OCR

OCR（Optical Character Recognition，光学字符识别）是指对文本资料的图像文件进行分析识别处理，获取文字及版面信息的过程。OCR 技术将图像中的文字转换为可编辑的文本格式。

### 1.2 OCR 的发展历史

| 年份 | 技术/系统 | 主要贡献 |
|------|-----------|----------|
| 1929 | Taushek | 光学字符识别专利 |
| 1974 | Kurzweil | 商业 OCR 系统 |
| 1990s | Tesseract | 开源 OCR 引擎 |
| 2012 | CNN | 深度学习用于文字识别 |
| 2015 | CRNN | 端到端文字识别 |
| 2017 | EAST | 高效场景文字检测 |

### 1.3 OCR 的应用领域

- 文档数字化
- 车牌识别
- 名片识别
- 票据识别
- 街景文字识别
- 古籍数字化

## 2. 核心概念

### 2.1 OCR 系统组成

一个完整的 OCR 系统通常包含：

1. **图像预处理**：灰度化、二值化、去噪、倾斜校正
2. **文字检测**：定位图像中的文字区域
3. **文字识别**：将文字图像转换为文本
4. **后处理**：纠错、格式化

### 2.2 文字检测方法

**传统方法**：
- 基于连通组件分析
- 基于边缘检测
- 滑动窗口

**深度学习方法**：
- CTPN (Connectionist Text Proposal Network)
- EAST (Efficient and Accurate Scene Text Detector)
- TextBoxes
- SegLink

### 2.3 文字识别方法

**传统方法**：
- 模板匹配
- 特征提取 + 分类器

**深度学习方法**：
- CNN + RNN + CTC (CRNN)
- Attention-based 识别
- Transformer-based 识别

## 3. CRNN 架构详解

### 3.1 CRNN 概述

CRNN（Convolutional Recurrent Neural Network）是一种端到端的文字识别模型，由以下部分组成：

1. **卷积层**：提取图像特征
2. **循环层**：建模序列依赖关系
3. **转录层**：CTC 解码输出

### 3.2 网络结构

```
输入图像 (1x32xW)
    ↓
卷积层 (CNN)
    ↓
特征序列
    ↓
循环层 (BiLSTM)
    ↓
预测序列
    ↓
CTC 转录层
    ↓
输出文本
```

### 3.3 CNN 特征提取

CRNN 使用 CNN 提取图像特征，典型结构：

```
Conv(64, 3x3) → ReLU → MaxPool(2x2)
Conv(128, 3x3) → ReLU → MaxPool(2x2)
Conv(256, 3x3) → ReLU → BN
Conv(256, 3x3) → ReLU → MaxPool(2x2, stride=(2,1))
Conv(512, 3x3) → ReLU → BN
Conv(512, 3x3) → ReLU → MaxPool(2x2, stride=(2,1))
Conv(512, 2x2) → ReLU
```

### 3.4 RNN 序列建模

使用双向 LSTM 建模序列依赖：

```python
# 双向 LSTM
self.rnn = nn.LSTM(input_size, hidden_size, 
                   num_layers=2, 
                   bidirectional=True)
```

### 3.5 CTC 转录

CTC（Connectionist Temporal Classification）解决输入输出对齐问题：

**特点**：
- 不需要逐字符标注位置
- 自动学习输入输出对齐
- 处理变长序列

**损失函数**：
```
L = -log P(y|x)
```

## 4. EAST 文字检测

### 4.1 EAST 概述

EAST（Efficient and Accurate Scene Text Detector）是一种高效的文字检测算法：

**特点**：
- 单阶段检测
- 直接预测文字区域
- 支持任意方向文字
- 速度快、精度高

### 4.2 网络结构

```
输入图像
    ↓
特征提取 (PVANet/ResNet)
    ↓
特征融合 (U-net 结构)
    ↓
输出层
    ├── Score Map (文字置信度)
    └── Geometry Map (文字区域)
        ├── RBOX: 4个边距 + 角度
        └── QUAD: 4个顶点坐标
```

### 4.3 损失函数

```
L = L_score + λ * L_geometry
```

- L_score: 交叉熵损失
- L_geometry: IoU 损失 + 角度损失

## 5. 数据集

### 5.1 常用 OCR 数据集

| 数据集 | 类型 | 规模 | 特点 |
|--------|------|------|------|
| ICDAR 2013 | 场景文字 | 229/233 | 英文，水平文字 |
| ICDAR 2015 | 场景文字 | 1000/500 | 任意方向 |
| SynthText | 合成数据 | 80万 | 大规模预训练 |
| MJSynth | 合成数据 | 900万 | 英文单词 |
| CTW | 中文 | 32K | 中文街景 |

### 5.2 数据标注格式

**检测标注**：
```json
{
  "image": "image_001.jpg",
  "annotations": [
    {
      "bbox": [x1, y1, x2, y2, x3, y3, x4, y4],
      "text": "Hello"
    }
  ]
}
```

**识别标注**：
```
image_001.jpg\tHello
image_002.jpg\tWorld
```

## 6. 评估指标

### 6.1 检测评估

**IoU (Intersection over Union)**：
```
IoU = Area(Intersection) / Area(Union)
```

**Precision & Recall**：
```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 * P * R / (P + R)
```

### 6.2 识别评估

**字符准确率**：
```
Char Accuracy = 正确字符数 / 总字符数
```

**词准确率**：
```
Word Accuracy = 完全正确的词数 / 总词数
```

**编辑距离**：
```
Normalized Edit Distance = EditDistance(pred, gt) / len(gt)
```

## 7. 参考文献

1. Shi, B., et al. (2017). An End-to-End Trainable Neural Network for Image-based Sequence Recognition and Its Application to Scene Text Recognition. IEEE TPAMI.
2. Zhou, X., et al. (2017). EAST: An Efficient and Accurate Scene Text Detector. CVPR.
3. Graves, A., et al. (2006). Connectionist Temporal Classification: Labelling Unsegmented Sequence Data with Recurrent Neural Networks. ICML.
4. He, T., et al. (2018). Real-time Accurate Scene Text Detection based on Prediction of Overlapping Polygons. CVPR.
5. Baek, J., et al. (2019). What is wrong with scene text recognition model comparisons? Dataset and model analysis. ICCV.