# 视频理解 (Video Understanding) - 视频内容理解与摘要系统

实现视频内容理解和摘要，通过帧采样、特征提取、内容分类和关键帧选择完成端到端的视频分析。

## 学习目标

- 理解视频理解的基本原理和核心流程
- 掌握视频特征提取方法（CNN 骨干 + 时序池化）
- 学会视频摘要生成（关键帧选取 + 场景变化检测）
- 实现完整的视频内容分析管道

## 项目结构

```
video-understanding/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── requirements.txt        # 依赖
├── setup.py                # 安装配置
├── configs/
│   └── default.yaml        # 默认配置
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
├── src/                    # 源代码
│   └── video_understanding/
│       ├── __init__.py
│       ├── core/           # 核心模块
│       │   ├── content_analyzer.py  # 内容分析器
│       │   └── keyframe_extractor.py # 关键帧提取
│       ├── data/           # 数据模块
│       │   ├── frame_sampler.py     # 帧采样器
│       │   └── video_dataset.py     # 视频数据集
│       ├── models/         # 模型模块
│       │   ├── classifier.py        # 内容分类器
│       │   ├── feature_extractor.py # 特征提取器
│       │   └── summarizer.py        # 摘要生成器
│       └── utils/          # 工具模块
│           └── video_utils.py       # 视频处理工具
├── scripts/                # 脚本
│   ├── train.py            # 训练脚本
│   ├── evaluate.py         # 评估脚本
│   └── summarize.py        # 摘要脚本
├── examples/               # 示例
│   ├── basic_understanding.py  # 基础示例
│   └── custom_pipeline.py      # 自定义管道
└── tests/                  # 测试
    ├── conftest.py
    ├── test_classifier.py
    ├── test_content_analyzer.py
    ├── test_feature_extractor.py
    ├── test_frame_sampler.py
    ├── test_keyframe_extractor.py
    ├── test_summarizer.py
    └── test_video_dataset.py
```

## 核心概念

### 视频理解流程

```
视频输入 → 帧采样 → 特征提取 → 内容理解 → 摘要生成
   │          │          │          │          │
   │     FrameSampler  VideoFeature Content   VideoSummarizer
   │     (均匀/随机/    Extractor   Analyzer  (关键帧+场景
   │      密集采样)    (ResNet+池化) (分类+    变化检测)
   │                              片段检测)
   ▼
 OpenCV 读取       CNN 提取空间特征    时序聚合      重要性评分
```

### 帧采样策略

| 策略 | 原理 | 适用场景 |
|------|------|----------|
| uniform | 等间距选取帧 | 通用场景 |
| random | 随机选取帧 | 数据增强 |
| dense | 密集均匀采样 | 需要更多细节 |
| keyframe | 基于场景变化选取 | 场景切换频繁的视频 |

### 特征提取架构

```
输入帧 (T, C, H, W)
       │
       ▼
  ResNet Backbone (逐帧提取)
       │
       ▼
  Projection Layer (降维)
       │
       ▼
  帧特征 (T, feature_dim)
       │
       ▼
  时序池化 (mean / max / attention)
       │
       ▼
  视频特征 (feature_dim,)
```

### 关键帧提取方法

| 方法 | 原理 |
|------|------|
| histogram | 计算相邻帧 HSV 直方图的 Bhattacharyya 距离 |
| optical_flow | 计算相邻帧的光流幅度 |
| threshold | 当帧间差异超过阈值时选取关键帧 |
| clustering | 对帧特征进行 K-Means 聚类，选取聚类中心帧 |

## 快速开始

### 安装依赖

```bash
pip install torch torchvision opencv-python numpy pytest
```

### 基础使用

```python
import torch
from video_understanding import VideoFeatureExtractor, VideoContentClassifier, VideoSummarizer

# 1. 特征提取
extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False, feature_dim=256)
frames = torch.randn(16, 3, 224, 224)  # 16帧视频
video_feature = extractor(frames)
print(f"视频特征: {video_feature.shape}")  # (256,)

# 2. 内容分类
classifier = VideoContentClassifier(num_classes=10, pretrained=False)
logits = classifier(frames.unsqueeze(0))  # 添加 batch 维度
print(f"分类 logits: {logits.shape}")  # (1, 10)

# 3. 视频摘要
summarizer = VideoSummarizer(num_keyframes=5)
summary = summarizer.generate_summary(frames)
print(f"关键帧: {summary['keyframe_indices']}")
print(f"场景变化: {summary['scene_changes']}")
```

### 完整分析管道

```python
from video_understanding import ContentAnalyzer

analyzer = ContentAnalyzer(num_classes=10, num_frames=16, num_keyframes=5)
frames = torch.randn(16, 3, 224, 224)

results = analyzer.analyze_frames(frames)
print(f"预测类别: {results['predictions']['predicted_class']}")
print(f"置信度: {results['predictions']['confidence']:.4f}")
print(f"关键帧: {results['keyframe_indices']}")

# 帧间相似度
similarity = analyzer.compute_frame_similarity(frames)

# 片段检测
segments = analyzer.detect_segments(frames)
```

### 运行示例

```bash
cd projects/video-understanding
python examples/basic_understanding.py
python examples/custom_pipeline.py
```

### 运行测试

```bash
cd projects/video-understanding
python -m pytest tests/ -v
```

### 训练模型

```bash
# 使用合成数据训练
python scripts/train.py --synthetic --epochs 5 --batch-size 4

# 评估模型
python scripts/evaluate.py --synthetic --checkpoint checkpoints/best_model.pth

# 生成视频摘要
python scripts/summarize.py video.mp4 --num-frames 16 --save-keyframes
```

## 参数说明

### VideoFeatureExtractor

| 参数 | 说明 | 默认值 |
|------|------|--------|
| backbone | 骨干网络: "resnet18", "resnet34", "resnet50" | "resnet18" |
| pretrained | 是否使用预训练权重 | True |
| feature_dim | 输出特征维度 | 512 |
| pooling | 时序池化: "mean", "max", "attention" | "mean" |

### VideoContentClassifier

| 参数 | 说明 | 默认值 |
|------|------|--------|
| num_classes | 分类类别数 | - |
| backbone | 骨干网络 | "resnet18" |
| feature_dim | 特征维度 | 512 |
| dropout | Dropout 比率 | 0.3 |

### KeyframeExtractor

| 参数 | 说明 | 默认值 |
|------|------|--------|
| method | 提取方法: "histogram", "optical_flow", "threshold", "clustering" | "histogram" |
| threshold | 差异阈值 | 0.5 |
| max_keyframes | 最大关键帧数 | 20 |

### VideoSummarizer

| 参数 | 说明 | 默认值 |
|------|------|--------|
| backbone | 特征提取骨干网络 | "resnet18" |
| feature_dim | 特征维度 | 512 |
| num_keyframes | 关键帧数量 | 5 |

## 参考资料

- [PyTorch ResNet 文档](https://pytorch.org/vision/stable/models/resnet.html)
- [OpenCV 光流文档](https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html)
- [视频理解综述 (2023)](https://arxiv.org/abs/2304.01aborting)
- [TSN: Temporal Segment Networks](https://arxiv.org/abs/1608.00859)

## License

MIT

---

[返回 AI 模块](../AI_README.md) | [返回主目录](../../README.md)
