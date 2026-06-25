# 05 - 开发指南

## 1. 环境搭建

### 1.1 依赖安装

```bash
# 克隆项目
cd projects/action-recognition

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装项目（开发模式）
pip install -e ".[dev]"

# 或仅安装依赖
pip install -r requirements.txt
```

### 1.2 系统要求

- Python >= 3.8
- PyTorch >= 1.12.0
- torchvision >= 0.13.0
- OpenCV >= 4.5.0
- CUDA（可选，用于GPU加速）

### 1.3 验证安装

```bash
# 运行测试验证安装
pytest tests/ -v

# 快速功能验证
python examples/basic_recognition.py
```

## 2. 开发工作流

### 2.1 代码规范

- 遵循PEP 8代码风格
- 使用类型注解（Type Hints）
- 编写文档字符串（Google风格）
- 每个公共方法必须有文档字符串

### 2.2 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
test: 添加/修改测试
refactor: 代码重构
style: 代码格式调整
perf: 性能优化
```

### 2.3 分支策略

- `main`: 稳定版本
- `dev`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

## 3. 代码约定

### 3.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | 小写下划线 | `frame_sampler.py` |
| 类名 | 大驼峰 | `ActionClassifier` |
| 函数名 | 小写下划线 | `load_video_frames()` |
| 常量 | 大写下划线 | `VIDEO_EXTENSIONS` |
| 私有方法 | 前缀下划线 | `_build_backbone()` |

### 3.2 类型注解

```python
from typing import Optional, List, Tuple, Dict

def sample(self, total_frames: int) -> List[int]:
    """采样帧索引"""
    ...

def forward(self, x: torch.Tensor, lengths: Optional[torch.Tensor] = None) -> torch.Tensor:
    """前向传播"""
    ...
```

### 3.3 文档字符串

```python
def extract_spatial(self, frames: torch.Tensor) -> torch.Tensor:
    """Extract spatial features from video frames.

    Args:
        frames: Tensor of shape (B, T, C, H, W).

    Returns:
        Spatial features of shape (B, T, feature_dim).
    """
    ...
```

## 4. 调试技巧

### 4.1 维度调试

```python
# 在前向传播中添加维度检查
def forward(self, x):
    print(f"Input shape: {x.shape}")
    # ... 处理逻辑
    print(f"Output shape: {output.shape}")
    return output
```

### 4.2 梯度检查

```python
# 检查梯度是否正常传播
loss.backward()
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_mean={param.grad.mean():.6f}")
```

### 4.3 内存监控

```python
import torch

# 查看GPU内存使用
if torch.cuda.is_available():
    print(f"GPU内存: {torch.cuda.memory_allocated()/1024**2:.1f} MB")
```

### 4.4 合成数据调试

使用合成数据快速验证模型逻辑：

```python
dataset = VideoDataset(synthetic=True, num_synthetic_classes=5, num_frames=4)
video, label = dataset[0]
model = ActionClassifier(num_classes=5, pretrained=False)
output = model(video.unsqueeze(0))
print(f"Output shape: {output.shape}")
```

## 5. 性能优化

### 5.1 数据加载优化

```python
DataLoader(
    dataset,
    batch_size=8,
    num_workers=4,      # 多进程加载
    pin_memory=True,    # GPU训练时启用
    prefetch_factor=2,  # 预加载批次数
)
```

### 5.2 模型优化

- 使用`torch.jit.script`进行JIT编译
- 使用混合精度训练（AMP）
- 冻结骨干网络减少计算量

### 5.3 特征缓存

预先提取特征并缓存到磁盘：

```python
extractor = FeatureExtractor()
features = extractor.extract(frames)
extractor.save_features(features, "cache/video_001.pt")
```

## 6. 常见问题

### Q1: CUDA内存不足

**问题**: `RuntimeError: CUDA out of memory`

**解决**:
- 减小batch_size
- 减少num_frames
- 使用较小的backbone（resnet18）
- 启用gradient checkpointing

### Q2: OpenCV无法读取视频

**问题**: `cv2.error: ...`

**解决**:
- 检查视频文件路径
- 确认视频编码格式支持
- 安装完整版OpenCV: `pip install opencv-python-headless`

### Q3: 模型不收敛

**问题**: 训练loss不下降

**解决**:
- 检查数据标签是否正确
- 降低学习率
- 增加模型容量
- 检查数据预处理

### Q4: 测试失败

**问题**: pytest测试报错

**解决**:
- 确认已安装所有依赖: `pip install -e ".[dev]"`
- 检查Python路径配置
- 查看详细错误信息: `pytest tests/ -v -s`

## 7. 扩展开发

### 7.1 添加新的骨干网络

在`SpatialModel`中添加：

```python
BACKBONE_FEATURE_DIMS = {
    "resnet18": 512,
    "resnet34": 512,
    "resnet50": 2048,
    "efficientnet_b0": 1280,  # 新增
}

def _build_backbone(self, backbone, pretrained, freeze):
    if backbone.startswith("efficientnet"):
        model_fn = getattr(models, backbone)
        base_model = model_fn(weights=weights)
        self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])
```

### 7.2 添加新的时序架构

在`TemporalModel`中添加：

```python
elif arch == "gru_v2":
    self.temporal_net = nn.GRU(
        input_size=input_dim,
        hidden_size=hidden_dim,
        num_layers=num_layers,
        batch_first=True,
        dropout=dropout if num_layers > 1 else 0.0,
    )
```

### 7.3 添加新的采样策略

在`FrameSampler`中添加：

```python
def _keyframe_sample(self, total_frames):
    """关键帧采样（基于帧差）"""
    # 实现关键帧检测逻辑
    ...
```

## 8. 部署

### 8.1 模型导出

```python
# 导出为ONNX
dummy_input = torch.randn(1, 8, 3, 224, 224)
torch.onnx.export(model, dummy_input, "model.onnx")

# 导出为TorchScript
scripted_model = torch.jit.script(model)
scripted_model.save("model.pt")
```

### 8.2 推理服务

```python
# 加载模型
model = ActionClassifier(num_classes=10)
model.load_state_dict(torch.load("checkpoints/best_model.pth"))
model.eval()

# 推理
predictions = model.predict(video_tensor, top_k=5)
```
