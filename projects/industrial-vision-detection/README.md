# 工业化视觉检测神经网络

> Industrial Vision Detection Neural Network

一个用于学习工业级视觉缺陷检测系统的学习项目，支持目标检测和实例分割。

## 📋 项目概述

本项目旨在帮助学习者理解并实现工业视觉检测的核心技术栈，包括 YOLO 系列目标检测模型、数据增强策略、模型训练与评估流程，以及模型部署优化。

### 核心处理流程

```
图像输入 → 预处理 → 模型推理 → 后处理 → 缺陷标注 → 结果输出
```

## 🎯 学习目标

### 核心知识点

1. **目标检测架构理解**
   - YOLO 系列 (YOLOv5/v8/v9/v10) 架构原理
   - Faster R-CNN 两阶段检测器
   - Anchor-based vs Anchor-free 检测策略
   - 特征金字塔网络 (FPN/PANet)

2. **数据处理与增强**
   - 工业图像预处理流程
   - 数据增强策略 (Mosaic, MixUp, CutOut)
   - 标注格式转换 (COCO, VOC, YOLO)

3. **模型训练技巧**
   - 学习率调度策略
   - 损失函数设计 (CIoU, DIoU, GIoU)
   - 迁移学习与微调
   - 分布式训练基础

4. **模型部署与优化**
   - ONNX 模型导出
   - TensorRT 优化
   - 模型量化 (INT8/FP16)
   - 边缘设备部署

### ⭐ 重点难点

- **多尺度特征融合**: 理解 FPN 如何处理不同尺度的目标
- **锚框机制**: 理解 Anchor 的设计与匹配策略
- **NMS 算法**: 非极大值抑制的实现与优化
- **损失函数**: IoU 系列损失函数的数学原理

### 💡 值得思考的地方

1. 为什么 YOLO 系列从 Anchor-based 演进到 Anchor-free？
2. NMS-Free 设计 (YOLOv10) 如何解决传统 NMS 的瓶颈？
3. 工业场景与通用目标检测的差异是什么？
4. 如何平衡检测精度与推理速度？

## 🛠️ 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Python 3.8+ | 主要开发语言 | ⭐⭐ |
| PyTorch 2.0+ | 深度学习框架 | ⭐⭐⭐ |
| torchvision | 视觉工具库 | ⭐⭐ |
| ONNX | 模型交换格式 | ⭐⭐ |
| ONNX Runtime | ONNX 推理引擎 | ⭐⭐ |
| OpenCV | 图像处理 | ⭐⭐ |
| NumPy | 数值计算 | ⭐ |
| Matplotlib | 可视化 | ⭐ |
| TensorRT (可选) | GPU 推理优化 | ⭐⭐⭐⭐ |
| CUDA (可选) | GPU 加速 | ⭐⭐⭐ |

## 📁 项目结构

```
industrial-vision-detection/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记模板
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装配置
│
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md           # 市场调研
│   ├── 02-REQUIREMENTS.md       # 需求分析
│   ├── 03-DESIGN.md             # 技术设计
│   ├── 04-PRODUCT.md            # 产品思维
│   └── 05-DEVELOPMENT.md        # 开发手册
│
├── src/                         # 源代码
│   ├── __init__.py
│   ├── models/                  # 模型定义
│   │   ├── __init__.py
│   │   ├── backbone.py          # 骨干网络
│   │   ├── neck.py              # 特征融合
│   │   ├── head.py              # 检测头
│   │   ├── yolo.py              # YOLO 模型
│   │   └── losses.py            # 损失函数
│   │
│   ├── data/                    # 数据处理
│   │   ├── __init__.py
│   │   ├── dataset.py           # 数据集类
│   │   ├── transforms.py        # 数据增强
│   │   ├── augmentations.py     # 高级增强
│   │   └── utils.py             # 数据工具
│   │
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── metrics.py           # 评估指标
│   │   ├── visualization.py     # 可视化
│   │   ├── boxes.py             # 边界框操作
│   │   └── general.py           # 通用工具
│   │
│   └── deployment/              # 部署相关
│       ├── __init__.py
│       ├── onnx_export.py       # ONNX 导出
│       └── onnx_inference.py    # ONNX 推理
│
├── configs/                     # 配置文件
│   ├── default.yaml             # 默认配置
│   └── yolov8_tiny.yaml         # YOLOv8-tiny 配置
│
├── tests/                       # 单元测试
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_data.py
│   ├── test_losses.py
│   └── test_utils.py
│
├── examples/                    # 使用示例
│   ├── train_example.py         # 训练示例
│   ├── inference_example.py     # 推理示例
│   └── export_example.py        # 导出示例
│
└── scripts/                     # 脚本工具
    ├── train.py                 # 训练脚本
    ├── evaluate.py              # 评估脚本
    └── export.py                # 导出脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyTorch 2.0+
- CUDA 11.8+ (可选，用于 GPU 加速)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd industrial-vision-detection

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 基本使用

#### 1. 训练模型

```python
from src.models.yolo import YOLOv8Tiny
from src.data.dataset import DefectDataset
from src.data.transforms import get_train_transforms

# 创建模型
model = YOLOv8Tiny(num_classes=5)

# 准备数据
transforms = get_train_transforms(image_size=640)
dataset = DefectDataset(
    data_dir='path/to/data',
    transforms=transforms
)

# 训练 (详见 examples/train_example.py)
```

#### 2. 推理

```python
from src.models.yolo import YOLOv8Tiny
import cv2

# 加载模型
model = YOLOv8Tiny.load_pretrained('path/to/checkpoint.pth')

# 推理
image = cv2.imread('test_image.jpg')
results = model.predict(image)

# 结果处理
for det in results['detections']:
    print(f"Class: {det['class']}, Confidence: {det['score']:.2f}")
```

#### 3. 导出 ONNX

```python
from src.deployment.onnx_export import export_to_onnx

export_to_onnx(
    model=model,
    output_path='model.onnx',
    input_shape=(1, 3, 640, 640)
)
```

## 📚 学习路径

### 阶段一：基础理解 (1-2 周)

1. 阅读项目文档 (`docs/` 目录)
2. 理解 YOLO 架构原理
3. 运行基础示例

### 阶段二：核心实现 (2-3 周)

1. 实现骨干网络 (Backbone)
2. 实现特征融合 (Neck)
3. 实现检测头 (Head)
4. 实现损失函数

### 阶段三：训练优化 (1-2 周)

1. 实现数据增强
2. 调整训练策略
3. 分析训练结果

### 阶段四：部署实践 (1 周)

1. ONNX 模型导出
2. 推理性能测试
3. 模型优化

## 🔗 相关资源

### 论文

- [You Only Look Once: Unified, Real-Time Object Detection](https://arxiv.org/abs/1506.02640)
- [YOLOv8: A New State-of-the-Art Computer Vision Model](https://github.com/ultralytics/ultralytics)
- [YOLOv9: Learning What You Want to Learn Using Programmable Gradient Information](https://arxiv.org/abs/2402.13616)
- [YOLOv10: Real-Time End-to-End Object Detection](https://arxiv.org/abs/2405.14458)

### 开源项目

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 官方 YOLOv8 实现
- [MMDetection](https://github.com/open-mmlab/mmdetection) - OpenMMLab 检测工具箱
- [Detectron2](https://github.com/facebookresearch/detectron2) - Facebook AI 检测库
- [Anomalib](https://github.com/openvinotoolkit/anomalib) - Intel 异常检测库

### 数据集

- [MVTec AD](https://www.mvtec.com/company/research/datasets/mvtec-ad) - 工业异常检测基准
- [COCO](https://cocodataset.org/) - 通用目标检测数据集
- [PASCAL VOC](http://host.robots.ox.ac.uk/pascal/VOC/) - 经典检测数据集

### 教程

- [PyTorch 官方教程](https://pytorch.org/tutorials/)
- [目标检测入门](https://github.com/amusi/awesome-object-detection)

## 📝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅用于学习目的。

---

**开始你的工业视觉检测学习之旅！** 🚀
