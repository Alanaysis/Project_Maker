# 05 - 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- PyTorch 1.12+
- torchvision 0.13+
- OpenCV 4.5+
- NumPy 1.21+
- pytest 7.0+

### 1.2 安装依赖

```bash
pip install torch torchvision opencv-python numpy pytest pytest-cov
```

### 1.3 项目结构

```
video-understanding/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── requirements.txt        # 依赖列表
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
│       ├── core/
│       ├── data/
│       ├── models/
│       └── utils/
├── scripts/                # 脚本
├── examples/               # 示例
└── tests/                  # 测试
```

## 2. 开发流程

### 2.1 开发步骤

1. **需求分析**：明确功能需求和学习目标
2. **设计**：确定模块划分和接口设计
3. **实现**：编写核心代码
4. **测试**：编写单元测试和集成测试
5. **文档**：更新文档和学习笔记
6. **示例**：编写使用示例

### 2.2 代码规范

**命名规范**：
- 类名：PascalCase（如 `VideoFeatureExtractor`）
- 函数名：snake_case（如 `extract_frames`）
- 变量名：snake_case（如 `frame_features`）
- 常量名：UPPER_CASE（如 `DEFAULT_FEATURE_DIM`）

**文档规范**：
- 每个模块有模块级 docstring
- 每个类有类级 docstring
- 每个公共方法有方法级 docstring
- 使用 Google 风格的 docstring

**类型注解**：
```python
def extract_frames(
    video_path: str,
    method: str = "uniform",
    num_frames: int = 16,
) -> List[np.ndarray]:
    ...
```

### 2.3 Git 工作流

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和测试
# ...

# 3. 提交
git add .
git commit -m "feat: 添加新功能"

# 4. 合并到主分支
git checkout master
git merge feature/new-feature
```

## 3. 快速开始

### 3.1 克隆项目

```bash
git clone <repo-url>
cd projects/video-understanding
```

### 3.2 安装依赖

```bash
pip install -e .
```

### 3.3 运行测试

```bash
python -m pytest tests/ -v
```

### 3.4 运行示例

```bash
python examples/basic_understanding.py
python examples/custom_pipeline.py
```

## 4. 使用指南

### 4.1 特征提取

```python
from video_understanding import VideoFeatureExtractor
import torch

# 创建提取器
extractor = VideoFeatureExtractor(
    backbone="resnet18",
    pretrained=True,
    feature_dim=512,
    pooling="mean"
)

# 提取特征
frames = torch.randn(16, 3, 224, 224)
video_feature = extractor(frames)
print(f"视频特征: {video_feature.shape}")  # (512,)
```

### 4.2 内容分类

```python
from video_understanding import VideoContentClassifier
import torch

# 创建分类器
classifier = VideoContentClassifier(
    num_classes=10,
    backbone="resnet18",
    pretrained=False
)

# 预测
frames = torch.randn(1, 16, 3, 224, 224)  # (B, T, C, H, W)
results = classifier.predict(frames, top_k=5)
print(f"预测类别: {results[0]['predicted_class']}")
print(f"置信度: {results[0]['confidence']:.4f}")
```

### 4.3 视频摘要

```python
from video_understanding import VideoSummarizer
import torch

# 创建摘要器
summarizer = VideoSummarizer(num_keyframes=5)

# 生成摘要
frames = torch.randn(16, 3, 224, 224)
summary = summarizer.generate_summary(frames)
print(f"关键帧: {summary['keyframe_indices']}")
print(f"场景变化: {summary['scene_changes']}")
```

### 4.4 完整分析

```python
from video_understanding import ContentAnalyzer
import torch

# 创建分析器
analyzer = ContentAnalyzer(
    num_classes=10,
    num_frames=16,
    num_keyframes=5
)

# 分析
frames = torch.randn(16, 3, 224, 224)
results = analyzer.analyze_frames(frames)

# 帧间相似度
similarity = analyzer.compute_frame_similarity(frames)

# 片段检测
segments = analyzer.detect_segments(frames)
```

### 4.5 关键帧提取（传统方法）

```python
from video_understanding import KeyframeExtractor
import numpy as np

# 创建提取器
extractor = KeyframeExtractor(method="histogram", max_keyframes=5)

# 准备帧数据
frames = [np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8) for _ in range(20)]

# 提取关键帧
indices, scores = extractor.extract(frames)
print(f"关键帧索引: {indices}")
```

## 5. 训练指南

### 5.1 使用合成数据训练

```bash
python scripts/train.py \
    --synthetic \
    --epochs 10 \
    --batch-size 8 \
    --lr 0.001 \
    --num-classes 10 \
    --num-frames 8 \
    --feature-dim 256 \
    --backbone resnet18 \
    --save-dir checkpoints
```

### 5.2 评估模型

```bash
python scripts/evaluate.py \
    --synthetic \
    --checkpoint checkpoints/best_model.pth \
    --num-classes 10
```

### 5.3 生成视频摘要

```bash
python scripts/summarize.py \
    path/to/video.mp4 \
    --num-frames 16 \
    --num-keyframes 5 \
    --output summary.json \
    --save-keyframes
```

## 6. 扩展开发

### 6.1 添加新的采样策略

```python
class FrameSampler:
    def sample(self, total_frames: int) -> np.ndarray:
        if self.method == "your_method":
            return self._your_method(total_frames, n)
        # ...

    def _your_method(self, total: int, n: int) -> np.ndarray:
        # 实现你的采样逻辑
        return indices
```

### 6.2 添加新的骨干网络

```python
class VideoFeatureExtractor:
    def _build_backbone(self, name: str, pretrained: bool) -> tuple:
        if name == "your_backbone":
            net = your_backbone(pretrained=pretrained)
            out_dim = net.final_layer.in_features
            net.final_layer = nn.Identity()
            return net, out_dim
        # ...
```

### 6.3 添加新的时序池化

```python
class VideoFeatureExtractor:
    def temporal_pool(self, features: torch.Tensor) -> torch.Tensor:
        if self.pooling_type == "your_pooling":
            # 实现你的池化逻辑
            return pooled
        # ...
```

### 6.4 添加新的关键帧提取方法

```python
class KeyframeExtractor:
    def extract(self, frames: List[np.ndarray]) -> Tuple[List[int], List[float]]:
        if self.method == "your_method":
            return self._extract_by_your_method(frames)
        # ...

    def _extract_by_your_method(self, frames):
        # 实现你的提取逻辑
        return indices, scores
```

## 7. 调试技巧

### 7.1 打印中间结果

```python
# 打印特征形状
features = extractor.extract_frame_features(frames)
print(f"帧特征形状: {features.shape}")

# 打印池化结果
pooled = extractor.temporal_pool(features)
print(f"池化特征形状: {pooled.shape}")
```

### 7.2 使用小数据快速验证

```python
# 使用小尺寸帧
small_frames = torch.randn(4, 3, 64, 64)
result = analyzer.analyze_frames(small_frames)
```

### 7.3 检查梯度

```python
# 确保梯度正常
loss.backward()
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm().item()}")
```

## 8. 常见问题

### 8.1 内存不足

**问题**：处理长视频时内存不足

**解决方案**：
- 减少采样帧数
- 使用更小的骨干网络
- 分批处理帧

### 8.2 训练不收敛

**问题**：模型训练不收敛

**解决方案**：
- 检查学习率
- 使用预训练权重
- 增加数据增强
- 检查标签是否正确

### 8.3 测试失败

**问题**：测试用例失败

**解决方案**：
- 检查依赖版本
- 清理 `__pycache__`
- 重新安装包

## 9. 性能优化

### 9.1 GPU 加速

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
frames = frames.to(device)
```

### 9.2 批量处理

```python
# 一次性处理多帧
x = frames.view(B * T, C, H, W)
features = backbone(x)
```

### 9.3 预计算缓存

```python
# 预计算特征并保存
features = extractor(frames)
torch.save(features, "features.pt")

# 加载缓存
features = torch.load("features.pt")
```

## 10. 部署建议

### 10.1 模型导出

```python
# 导出为 ONNX
torch.onnx.export(model, dummy_input, "model.onnx")
```

### 10.2 模型量化

```python
# 动态量化
quantized_model = torch.quantization.quantize_dynamic(
    model, {nn.Linear}, dtype=torch.qint8
)
```

### 10.3 服务部署

```python
# 使用 Flask/FastAPI 部署
from fastapi import FastAPI
app = FastAPI()

@app.post("/analyze")
async def analyze_video(video_path: str):
    results = analyzer.analyze_frames(frames)
    return results
```
