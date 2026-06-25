# 02 - 设计文档

## 1. 系统架构

### 1.1 整体架构

```
video-understanding/
├── core/              # 核心业务逻辑
│   ├── content_analyzer.py   # 内容分析器（整合所有组件）
│   └── keyframe_extractor.py # 关键帧提取器
├── data/              # 数据处理
│   ├── frame_sampler.py      # 帧采样策略
│   └── video_dataset.py      # 数据集加载
├── models/            # 模型定义
│   ├── feature_extractor.py  # 特征提取器
│   ├── classifier.py         # 分类器
│   └── summarizer.py         # 摘要生成器
└── utils/             # 工具函数
    └── video_utils.py        # 视频处理工具
```

### 1.2 数据流

```
视频文件
    │
    ▼
video_utils.load_video()     # 读取视频帧
    │
    ▼
FrameSampler.sample()         # 采样帧索引
    │
    ▼
VideoFeatureExtractor         # 提取帧特征
    ├── backbone(frames)      #   CNN 提取
    ├── projection(features)  #   降维投影
    └── temporal_pool(feats)  #   时序池化
    │
    ▼
VideoContentClassifier        # 内容分类
    └── classifier(features)  #   分类头
    │
    ▼
VideoSummarizer               # 摘要生成
    ├── importance_net(feats) #   重要性评分
    └── change_net(feats)     #   场景变化检测
    │
    ▼
ContentAnalyzer               # 整合分析
```

## 2. 模块设计

### 2.1 FrameSampler（帧采样器）

**职责**：从视频帧序列中选取代表性帧

**接口设计**：
```python
class FrameSampler:
    def __init__(self, num_frames=16, method="uniform", seed=42)
    def sample(self, total_frames: int) -> np.ndarray
    def sample_with_scores(self, frames, scores, top_k=None) -> Tuple[np.ndarray, np.ndarray]
```

**支持的采样方法**：
- `uniform`：均匀采样，使用 `np.linspace`
- `random`：随机采样，使用固定种子保证可重复性
- `dense`：密集采样，等间距但包含更多帧

**设计决策**：
- 使用 numpy 而非 torch，因为采样是数据处理层
- 返回索引而非帧本身，保持灵活性
- 支持 `sample_with_scores` 用于基于重要性的采样

### 2.2 VideoFeatureExtractor（特征提取器）

**职责**：提取视频帧的空间特征并聚合为视频级特征

**接口设计**：
```python
class VideoFeatureExtractor(nn.Module):
    def __init__(self, backbone="resnet18", pretrained=True, feature_dim=512, pooling="mean")
    def extract_frame_features(self, frames: torch.Tensor) -> torch.Tensor
    def temporal_pool(self, features: torch.Tensor) -> torch.Tensor
    def forward(self, frames: torch.Tensor) -> torch.Tensor
```

**骨干网络**：
- ResNet-18：轻量级，512 维特征
- ResNet-34：中等规模，512 维特征
- ResNet-50：较大规模，2048 维特征（需投影）

**时序池化**：
- Mean：所有帧特征取平均
- Max：每个维度取最大值
- Attention：学习帧重要性权重

**设计决策**：
- 使用 `nn.Identity()` 替换 ResNet 的分类层
- 投影层包含 ReLU 和 Dropout，增强泛化能力
- 支持 4D (T,C,H,W) 和 5D (B,T,C,H,W) 输入

### 2.3 VideoContentClassifier（内容分类器）

**职责**：基于特征提取器实现视频内容分类

**接口设计**：
```python
class VideoContentClassifier(nn.Module):
    def __init__(self, num_classes, backbone="resnet18", feature_dim=512, dropout=0.3)
    def forward(self, frames: torch.Tensor) -> torch.Tensor
    def predict(self, frames: torch.Tensor, top_k=5) -> List[Dict]
    def get_features(self, frames: torch.Tensor) -> torch.Tensor
```

**分类头结构**：
```
Linear(feature_dim, feature_dim//2) → ReLU → Dropout → Linear(feature_dim//2, num_classes)
```

**设计决策**：
- `predict()` 返回字典列表，包含类别、概率等信息
- `get_features()` 单独暴露特征提取，便于迁移学习
- 使用 `F.softmax` 计算概率

### 2.4 VideoSummarizer（摘要生成器）

**职责**：生成视频摘要，包括关键帧选取和场景变化检测

**接口设计**：
```python
class VideoSummarizer(nn.Module):
    def __init__(self, backbone="resnet18", feature_dim=512, num_keyframes=5)
    def compute_importance_scores(self, frames: torch.Tensor) -> torch.Tensor
    def detect_scene_changes(self, frames: torch.Tensor, threshold=0.5) -> List[int]
    def extract_keyframes(self, frames: torch.Tensor) -> Tuple[List[int], np.ndarray]
    def generate_summary(self, frames: torch.Tensor) -> Dict
```

**重要性评分网络**：
```
Linear(feature_dim, feature_dim//2) → ReLU → Linear(feature_dim//2, 1) → Sigmoid
```

**场景变化检测网络**：
```
Linear(feature_dim*2, feature_dim) → ReLU → Linear(feature_dim, 1) → Sigmoid
```

**设计决策**：
- 使用独立的网络学习重要性和场景变化
- `generate_summary()` 返回完整的摘要信息
- 场景变化检测基于相邻帧特征拼接

### 2.5 KeyframeExtractor（关键帧提取器）

**职责**：使用传统方法提取关键帧

**接口设计**：
```python
class KeyframeExtractor:
    def __init__(self, method="histogram", threshold=0.5, max_keyframes=20)
    def extract(self, frames: List[np.ndarray]) -> Tuple[List[int], List[float]]
```

**提取方法**：
- `histogram`：基于 HSV 直方图差异
- `optical_flow`：基于光流幅度
- `threshold`：基于固定阈值
- `clustering`：基于 K-Means 聚类

**设计决策**：
- 使用 OpenCV 实现传统方法，不依赖深度学习
- 内置 K-Means 实现，避免额外依赖
- 返回索引和分数，便于后续处理

### 2.6 ContentAnalyzer（内容分析器）

**职责**：整合所有组件，提供统一的分析接口

**接口设计**：
```python
class ContentAnalyzer:
    def __init__(self, num_classes=10, num_frames=16, num_keyframes=5, backbone="resnet18", feature_dim=512)
    def analyze_frames(self, frames: torch.Tensor) -> Dict
    def analyze_numpy_frames(self, frames: List[np.ndarray]) -> Dict
    def compute_frame_similarity(self, frames: torch.Tensor) -> np.ndarray
    def detect_segments(self, frames: torch.Tensor, min_segment_length=3) -> List[Tuple[int, int]]
```

**分析结果**：
```python
{
    "video_feature": np.ndarray,      # 视频级特征
    "frame_features": np.ndarray,     # 帧级特征
    "predictions": Dict,              # 分类预测
    "importance_scores": List[float], # 重要性分数
    "keyframe_indices": List[int],    # 关键帧索引
    "num_frames": int,                # 总帧数
    "feature_dim": int,               # 特征维度
}
```

**设计决策**：
- 组合模式：内部持有所有子组件
- 提供 numpy 和 torch 两种接口
- 帧间相似度使用余弦相似度
- 片段检测基于特征距离的阈值分割

## 3. 数据设计

### 3.1 VideoDataset

**目录结构**：
```
root/
├── class1/
│   ├── video1.mp4
│   └── video2.mp4
└── class2/
    ├── video3.mp4
    └── video4.mp4
```

**返回格式**：
- `frames_tensor`：形状 (T, C, H, W)
- `label`：整数类别标签

### 3.2 SyntheticVideoDataset

用于测试和调试，生成随机张量。

**参数**：
- `num_samples`：样本数量
- `num_frames`：每视频帧数
- `num_classes`：类别数
- `frame_size`：帧大小

## 4. 配置设计

### 4.1 配置文件结构

```yaml
data:
  num_frames: 16
  frame_size: [224, 224]
  sampling_method: "uniform"

model:
  backbone: "resnet18"
  pretrained: true
  feature_dim: 512
  pooling: "mean"
  num_classes: 10

summary:
  num_keyframes: 5
  scene_change_threshold: 0.5

training:
  batch_size: 8
  learning_rate: 0.001
  epochs: 30
```

## 5. 接口设计原则

1. **一致性**：所有组件使用相似的接口风格
2. **灵活性**：支持多种输入格式（tensor, numpy, 文件路径）
3. **可组合**：组件可以独立使用或组合使用
4. **可测试**：所有接口都可以单元测试
