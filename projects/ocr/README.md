# OCR 文字识别系统

## 项目概述

本项目实现了一个完整的 OCR（Optical Character Recognition）文字识别系统，包含文字检测和文字识别两大核心模块。通过深度学习技术，系统能够从图像中自动检测文字区域并识别文字内容。

## 核心功能

- **文字检测**：基于 EAST 模型检测图像中的文字区域
- **文字识别**：基于 CRNN（卷积循环神经网络）进行序列文字识别
- **端到端 OCR**：集成检测和识别的完整流程
- **评估系统**：提供准确率、召回率等评估指标

## 技术栈

- **深度学习框架**：PyTorch
- **图像处理**：OpenCV
- **语言**：Python 3.8+

## 项目结构

```
ocr/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md           # 学习笔记
├── requirements.txt            # 依赖包
├── docs/                       # 文档目录
│   ├── 01-RESEARCH.md         # 研究文档
│   ├── 02-DESIGN.md           # 设计文档
│   ├── 03-IMPLEMENTATION.md   # 实现文档
│   ├── 04-TESTING.md          # 测试文档
│   └── 05-DEVELOPMENT.md      # 开发文档
├── src/                        # 源代码
│   ├── __init__.py
│   ├── detector.py            # 文字检测模块
│   ├── recognizer.py          # 文字识别模块 (CRNN)
│   ├── ocr_engine.py          # OCR 引擎
│   └── utils.py               # 工具函数
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_detector.py       # 检测模块测试
│   ├── test_recognizer.py     # 识别模块测试
│   └── test_ocr_engine.py     # OCR 引擎测试
└── examples/                   # 示例代码
    ├── demo.py                # 演示脚本
    └── sample_images/         # 示例图像
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
python examples/demo.py
```

### 运行测试

```bash
pytest tests/
```

## 核心架构

### OCR 流程

```
图像输入 → 预处理 → 文字检测 → 区域裁剪 → 文字识别 → 文本输出
```

### CRNN 架构

```
输入图像 → CNN特征提取 → RNN序列建模 → CTC解码 → 文字输出
```

## 学习目标

1. **理解 OCR 原理**：掌握光学字符识别的基本流程
2. **掌握文字检测**：学习 EAST 等文字检测算法
3. **掌握文字识别**：深入理解 CRNN 架构
4. **端到端系统**：构建完整的 OCR 系统

## 评估指标

- **检测准确率**：IoU > 0.5 的检测框比例
- **识别准确率**：正确识别的字符比例
- **端到端准确率**：完全正确的文本行比例

## 参考文献

1. Shi, B., et al. (2017). An End-to-End Trainable Neural Network for Image-based Sequence Recognition.
2. Zhou, X., et al. (2017). EAST: An Efficient and Accurate Scene Text Detector.
3. Graves, A., et al. (2006). Connectionist Temporal Classification: Labelling Unsegmented Sequence Data.

## 许可证

本项目仅用于学习目的。