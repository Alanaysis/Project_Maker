# 文字检测 (Text Detection)

> 实现文字检测系统，检测图像中的文字区域

---

## 项目概述

本项目实现了一个基于 EAST (Efficient and Accurate Scene Text Detector) 架构的文字检测系统。系统能够检测图像中的文字区域，并输出文字的边界框坐标。

### 核心功能

- **特征提取**：VGG-like 骨干网络提取多尺度特征
- **特征融合**：U-Net 风格的特征金字塔网络
- **文字检测**：同时预测文字区域分数图和几何信息
- **后处理**：NMS 和 LANMS 去重处理

### 技术栈

- **主语言**：Python
- **深度学习框架**：PyTorch
- **图像处理**：OpenCV
- **测试框架**：pytest

---

## 项目结构

```
text-detection/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md           # 学习笔记
├── requirements.txt            # 依赖清单
├── src/                        # 源代码
│   ├── __init__.py
│   ├── model/                  # 模型架构
│   │   ├── backbone.py         # 骨干网络
│   │   ├── neck.py             # 特征融合
│   │   ├── head.py             # 检测头
│   │   └── east_net.py         # 完整网络
│   ├── loss/                   # 损失函数
│   │   └── east_loss.py
│   ├── postprocess/            # 后处理
│   │   └── nms.py
│   ├── data/                   # 数据处理
│   │   ├── dataset.py
│   │   └── transforms.py
│   └── utils/                  # 工具函数
│       └── visualizer.py
├── tests/                      # 测试文件
│   ├── test_model.py
│   ├── test_loss.py
│   ├── test_nms.py
│   └── test_dataset.py
├── examples/                   # 示例脚本
│   ├── demo.py                 # 快速演示
│   ├── train.py                # 训练脚本
│   └── inference.py            # 推理脚本
└── docs/                       # 文档
    ├── 01-RESEARCH.md
    ├── 02-ARCHITECTURE.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

---

## 快速开始

### 安装依赖

```bash
cd text-detection
pip install -r requirements.txt
```

### 运行演示

```bash
python examples/demo.py
```

### 运行测试

```bash
pytest tests/ -v
```

### 训练模型

```bash
python examples/train.py
```

---

## 核心架构

### EAST 架构

```
输入图像
    ↓
┌─────────────────┐
│  Backbone (VGG) │  → 多尺度特征
└─────────────────┘
    ↓
┌─────────────────┐
│  Neck (U-Net)   │  → 特征融合
└─────────────────┘
    ↓
┌─────────────────┐
│  Head (Score +  │  → 分数图 + 几何图
│    Geometry)    │
└─────────────────┘
    ↓
┌─────────────────┐
│  Post-process   │  → 边界框
│  (NMS/LANMS)   │
└─────────────────┘
```

### 输出格式

- **Score Map**: [B, 1, H/4, W/4] - 文字区域概率
- **Geometry Map**: [B, 5, H/4, W/4] - 边界框几何信息
  - 通道 0: 到顶部的距离
  - 通道 1: 到右侧的距离
  - 通道 2: 到底部的距离
  - 通道 3: 到左侧的距离
  - 通道 4: 旋转角度

---

## 学习目标

通过本项目，你将学到：

1. **文字检测原理**：理解场景文字检测的基本概念
2. **EAST 架构**：掌握高效的文字检测网络设计
3. **多尺度特征融合**：学习 U-Net 风格的特征金字塔
4. **边界框回归**：理解旋转边界框的表示方法
5. **NMS 后处理**：掌握非极大值抑制算法

---

## 参考文献

1. Zhou et al., "EAST: An Efficient and Accurate Scene Text Detector", CVPR 2017
2. Tian et al., "Detecting Text in Natural Image with Connectionist Text Proposal Network", ECCV 2016
3. Liao et al., "Real-Time Scene Text Detection with Differentiable Binarization", AAAI 2020

---

## 相关链接

- [返回 AI 模块](../AI_README.md)
- [学习笔记](LEARNING_NOTES.md)
- [项目文档](docs/)
