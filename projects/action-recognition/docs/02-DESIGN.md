# 02 - 项目架构设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Action Recognition System                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Data Layer   │  │ Model Layer  │  │   Application Layer  │  │
│  │              │  │              │  │                      │  │
│  │ VideoDataset │  │ SpatialModel │  │ Training Pipeline    │  │
│  │ FrameSampler │  │ TemporalModel│  │ Evaluation Pipeline  │  │
│  │ Transforms   │  │ Classifier   │  │ Feature Extraction   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Utility Layer                            │
│         VideoUtils  |  Visualization  |  Metrics               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
视频文件
    │
    ▼
┌──────────────┐
│ FrameSampler │  ──→ 均匀/随机/密集采样帧索引
└──────────────┘
    │
    ▼
┌──────────────┐
│ VideoDataset │  ──→ 加载帧、预处理、返回(T,C,H,W)张量
└──────────────┘
    │
    ▼
┌──────────────┐
│ SpatialModel │  ──→ CNN提取每帧空间特征 → (B, T, feat_dim)
└──────────────┘
    │
    ▼
┌──────────────┐
│TemporalModel │  ──→ LSTM/GRU/Transformer建模时序 → (B, hidden_dim)
└──────────────┘
    │
    ▼
┌──────────────┐
│  Classifier  │  ──→ FC层分类 → (B, num_classes)
└──────────────┘
    │
    ▼
动作类别 + 置信度
```

## 2. 模块设计

### 2.1 数据模块 (`data/`)

#### FrameSampler

```python
class FrameSampler:
    """视频帧采样器"""

    def __init__(self, num_frames: int, strategy: str, stride: int):
        ...

    def sample(self, total_frames: int) -> List[int]:
        """返回采样的帧索引列表"""
        ...
```

**采样策略**：
| 策略 | 描述 | 适用场景 |
|------|------|----------|
| uniform | 均匀采样 | 通用 |
| random | 随机采样 | 数据增强 |
| dense | 固定步长密集采样 | 短时动作 |
| temporal_jitter | 带抖动的均匀采样 | 训练增强 |

#### VideoDataset

```python
class VideoDataset(Dataset):
    """视频数据集"""

    def __init__(self, data_root, frame_sampler, transform, frame_size, synthetic):
        ...

    def __getitem__(self, idx) -> Tuple[torch.Tensor, int]:
        """返回 (video_tensor, label)"""
        ...
```

**支持的数据格式**：
- 视频文件（.mp4, .avi, .mov）
- 图像帧目录
- 合成数据（用于测试）

### 2.2 模型模块 (`models/`)

#### SpatialModel

```python
class SpatialModel(nn.Module):
    """空间特征提取模型"""

    BACKBONE_FEATURE_DIMS = {
        "resnet18": 512,
        "resnet34": 512,
        "resnet50": 2048,
        "vgg16": 4096,
    }

    def __init__(self, backbone, pretrained, feature_dim, freeze_backbone):
        ...

    def forward(self, x: Tensor) -> Tensor:
        """
        输入: (B, C, H, W) 或 (B, T, C, H, W)
        输出: (B, feat_dim) 或 (B, T, feat_dim)
        """
        ...
```

**骨干网络选择**：
| 网络 | 参数量 | 特征维度 | 速度 | 精度 |
|------|--------|----------|------|------|
| ResNet-18 | 11M | 512 | 快 | 中 |
| ResNet-34 | 21M | 512 | 中 | 中 |
| ResNet-50 | 25M | 2048 | 慢 | 高 |
| VGG-16 | 138M | 4096 | 慢 | 中 |

#### TemporalModel

```python
class TemporalModel(nn.Module):
    """时序建模模型"""

    def __init__(self, input_dim, hidden_dim, num_layers, arch, num_heads, dropout, bidirectional):
        ...

    def forward(self, x: Tensor, lengths: Optional[Tensor]) -> Tensor:
        """
        输入: (B, T, input_dim)
        输出: (B, output_dim)
        """
        ...
```

**时序架构对比**：
| 架构 | 优点 | 缺点 | 输出维度 |
|------|------|------|----------|
| LSTM | 捕捉长期依赖 | 序列处理慢 | hidden_dim |
| GRU | 参数更少、训练快 | 表达能力略弱 | hidden_dim |
| Transformer | 并行计算、全局注意力 | 需要更多数据 | input_dim |

#### ActionClassifier

```python
class ActionClassifier(nn.Module):
    """端到端动作分类器"""

    def __init__(self, num_classes, backbone, temporal_arch, hidden_dim, ...):
        ...

    def forward(self, video_clips: Tensor, lengths: Optional[Tensor]) -> Tensor:
        """
        输入: (B, T, C, H, W)
        输出: (B, num_classes)
        """
        ...

    def predict(self, video_clips, top_k) -> List[Dict[int, float]]:
        """返回top-k预测结果"""
        ...
```

### 2.3 特征模块 (`features/`)

#### FeatureExtractor

```python
class FeatureExtractor:
    """特征提取管道"""

    def extract_spatial(self, frames: Tensor) -> Tensor:
        """提取空间特征"""
        ...

    def extract_temporal(self, spatial_features: Tensor) -> Tensor:
        """提取时序特征"""
        ...

    def extract(self, frames: Tensor) -> Dict[str, Tensor]:
        """提取完整特征"""
        ...

    def save_features(self, features: Dict, path: str) -> None:
        """保存特征到磁盘"""
        ...

    def load_features(self, path: str) -> Dict[str, Tensor]:
        """加载缓存特征"""
        ...
```

### 2.4 工具模块 (`utils/`)

| 函数 | 功能 |
|------|------|
| `load_video_frames()` | 从视频文件加载帧 |
| `get_video_info()` | 获取视频元数据 |
| `resize_frames()` | 批量调整帧大小 |
| `plot_predictions()` | 可视化预测结果 |
| `plot_training_curves()` | 绘制训练曲线 |
| `visualize_features()` | 特征降维可视化 |

## 3. 超参数设计

### 3.1 默认超参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| num_frames | 8 | 每个视频片段的帧数 |
| frame_size | (224, 224) | 帧的空间尺寸 |
| backbone | resnet18 | CNN骨干网络 |
| temporal_arch | lstm | 时序模型架构 |
| hidden_dim | 256 | 时序模型隐藏维度 |
| num_layers | 2 | 时序模型层数 |
| dropout | 0.3 | Dropout概率 |
| batch_size | 8 | 批大小 |
| learning_rate | 1e-3 | 学习率 |
| epochs | 30 | 训练轮数 |

### 3.2 训练策略

- **优化器**: Adam (lr=1e-3, weight_decay=1e-4)
- **学习率调度**: StepLR (step_size=10, gamma=0.5)
- **数据增强**: RandomCrop, HorizontalFlip, ColorJitter
- **正则化**: Dropout, Weight Decay

## 4. 文件结构

```
action-recognition/
├── src/action_recognition/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── spatial_model.py      # CNN空间特征提取
│   │   ├── temporal_model.py     # RNN/Transformer时序建模
│   │   └── action_classifier.py  # 端到端分类器
│   ├── data/
│   │   ├── __init__.py
│   │   ├── frame_sampler.py      # 帧采样策略
│   │   └── video_dataset.py      # 视频数据集
│   ├── features/
│   │   ├── __init__.py
│   │   └── extractor.py          # 特征提取管道
│   └── utils/
│       ├── __init__.py
│       ├── video_utils.py        # 视频工具函数
│       └── visualization.py      # 可视化工具
├── tests/                        # 测试文件
├── scripts/                      # 训练/评估脚本
├── configs/                      # 配置文件
├── examples/                     # 使用示例
└── docs/                         # 文档
```
