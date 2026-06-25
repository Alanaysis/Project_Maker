# 动作识别 (Action Recognition)

基于深度学习的视频动作识别系统，实现从视频输入到动作分类的完整流程。

## 核心流程

```
视频输入 → 帧采样 → 特征提取 → 时序建模 → 动作分类
   │         │         │           │           │
   ▼         ▼         ▼           ▼           ▼
 .mp4    均匀/随机   CNN提取    LSTM/GRU    Softmax
 .avi    采样策略   空间特征   捕捉时序    输出类别
```

## 项目结构

```
action-recognition/
├── README.md
├── LEARNING_NOTES.md
├── setup.py
├── requirements.txt
├── src/action_recognition/
│   ├── __init__.py
│   ├── models/
│   │   ├── spatial_model.py      # CNN空间特征提取
│   │   ├── temporal_model.py     # 时序建模(LSTM/GRU/Transformer)
│   │   └── action_classifier.py  # 端到端动作分类器
│   ├── data/
│   │   ├── frame_sampler.py      # 视频帧采样策略
│   │   └── video_dataset.py      # 视频数据集加载
│   ├── features/
│   │   └── extractor.py          # 特征提取管道
│   └── utils/
│       ├── video_utils.py        # 视频工具函数
│       └── visualization.py      # 可视化工具
├── tests/                        # 单元测试
├── scripts/
│   ├── train.py                  # 训练脚本
│   └── evaluate.py               # 评估脚本
├── configs/
│   └── default.yaml              # 默认配置
├── examples/
│   ├── basic_recognition.py      # 基础识别示例
│   └── custom_dataset.py         # 自定义数据集示例
└── docs/
    ├── 01-RESEARCH.md            # 研究调研
    ├── 02-DESIGN.md              # 架构设计
    ├── 03-IMPLEMENTATION.md      # 实现细节
    ├── 04-TESTING.md             # 测试策略
    └── 05-DEVELOPMENT.md         # 开发指南
```

## 安装

```bash
# 克隆项目后进入目录
cd projects/action-recognition

# 安装项目（开发模式）
pip install -e ".[dev]"

# 或安装依赖
pip install -r requirements.txt
```

## 使用

### 基础用法（合成数据）

```bash
# 使用合成数据训练（无需真实视频）
python scripts/train.py --synthetic --epochs 5 --batch-size 4

# 评估模型
python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --synthetic
```

### 自定义数据训练

```bash
# 准备数据目录结构:
# data/train/class1/video1.mp4
# data/val/class1/video1.mp4

python scripts/train.py --data-root data --epochs 30 --batch-size 8
```

### 运行示例

```bash
# 基础识别示例
python examples/basic_recognition.py

# 自定义数据集示例
python examples/custom_dataset.py --data-root /path/to/data
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=action_recognition
```

## 学习目标

- **动作识别原理**: 理解视频动作识别的基本流程和核心算法
- **时序建模**: 掌握LSTM、GRU、Transformer在时序数据上的应用
- **视频特征提取**: 学会使用CNN提取视频帧的空间特征
- **端到端训练**: 理解从原始视频到动作分类的完整训练流程
- **数据采样策略**: 了解不同的视频帧采样方法及其适用场景

## 技术栈

- **语言**: Python 3.8+
- **深度学习框架**: PyTorch 1.12+
- **视觉处理**: torchvision, OpenCV
- **数据处理**: NumPy
- **可视化**: Matplotlib
- **测试**: pytest

## API示例

```python
import torch
from action_recognition import ActionClassifier, FrameSampler, VideoDataset

# 创建模型
model = ActionClassifier(
    num_classes=10,
    backbone="resnet18",
    temporal_arch="lstm",
)

# 推理
video = torch.randn(1, 8, 3, 224, 224)  # (B, T, C, H, W)
predictions = model.predict(video, top_k=5)

# 提取特征
features = model.get_spatial_features(video)   # 空间特征
temporal = model.get_temporal_features(video)  # 时序特征
```

## 参考资源

- [Two-Stream Networks](https://arxiv.org/abs/1406.2199) - Simonyan & Zisserman, NIPS 2014
- [Temporal Segment Networks](https://arxiv.org/abs/1608.00859) - Wang et al., ECCV 2016
- [SlowFast Networks](https://arxiv.org/abs/1812.03982) - Feichtenhofer et al., ICCV 2019
- [MMAction2](https://github.com/open-mmlab/mmaction2) - OpenMMLab视频理解工具箱
