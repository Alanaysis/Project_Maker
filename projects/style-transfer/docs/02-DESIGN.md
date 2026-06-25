# 神经风格迁移 - 设计文档

## 1. 系统架构

### 1.1 整体架构

```
style-transfer/
├── src/
│   ├── __init__.py              # 模块导出
│   ├── gram_matrix.py           # Gram 矩阵计算
│   ├── losses.py                # 损失函数
│   ├── style_transfer.py        # 风格迁移核心
│   └── utils.py                 # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_gram_matrix.py      # Gram 矩阵测试
│   ├── test_losses.py           # 损失函数测试
│   └── test_style_transfer.py   # 风格迁移测试
├── examples/
│   ├── basic_transfer.py        # 基本示例
│   ├── advanced_transfer.py     # 高级示例
│   └── gram_matrix_demo.py      # Gram 矩阵演示
└── docs/
    ├── 01-RESEARCH.md           # 调研文档
    ├── 02-DESIGN.md             # 设计文档
    ├── 03-IMPLEMENTATION.md     # 实现文档
    ├── 04-TESTING.md            # 测试文档
    └── 05-DEVELOPMENT.md        # 开发文档
```

### 1.2 模块依赖关系

```
style_transfer.py
    ├── gram_matrix.py
    ├── losses.py
    └── utils.py
```

### 1.3 核心类设计

#### GramMatrix 类
```
GramMatrix
├── forward(features) -> gram
└── gram_matrix(features) -> gram
```

#### 损失函数类
```
ContentLoss
├── set_target(target)
├── forward(input) -> input
└── get_loss() -> loss

StyleLoss
├── set_target(target)
├── forward(input) -> input
└── get_loss() -> loss

TotalVariationLoss
├── forward(input) -> input
└── get_loss() -> loss
```

#### StyleTransfer 类
```
StyleTransfer
├── __init__(content_layers, style_layers, weights)
├── _load_vgg() -> model
├── _build_model() -> model
├── _set_targets(content, style)
├── transfer(content, style, steps) -> output
└── get_loss_summary() -> dict
```

## 2. 数据流设计

### 2.1 前向传播流程

```
输入图像
    ↓
VGG19 特征提取
    ↓
┌─────────────────────────────────────┐
│                                     │
├─> conv1_1 ──> StyleLoss ──────────┤
│                                     │
├─> conv2_1 ──> StyleLoss ──────────┤
│                                     │
├─> conv3_1 ──> StyleLoss ──────────┤
│                                     │
├─> conv4_1 ──> StyleLoss ──────────┤
│                                     │
├─> conv4_2 ──> ContentLoss ────────┤
│                                     │
├─> conv5_1 ──> StyleLoss ──────────┤
│                                     │
└─────────────────────────────────────┘
    ↓
TotalVariationLoss
    ↓
总损失计算
```

### 2.2 优化流程

```
初始化生成图像
    ↓
┌─────────────────────────────────────┐
│ 优化循环                            │
│                                     │
│ 1. 前向传播                         │
│    ↓                                │
│ 2. 计算损失                         │
│    - ContentLoss                    │
│    - StyleLoss                      │
│    - TotalVariationLoss             │
│    ↓                                │
│ 3. 反向传播                         │
│    ↓                                │
│ 4. 更新生成图像                     │
│    ↓                                │
│ 5. 检查收敛                         │
└─────────────────────────────────────┘
    ↓
输出生成图像
```

## 3. 接口设计

### 3.1 公共 API

#### load_image
```python
def load_image(
    image_path: Union[str, Path],
    size: int = 512,
    device: str = "cpu",
) -> torch.Tensor:
    """加载并预处理图像"""
```

#### save_image
```python
def save_image(
    tensor: torch.Tensor,
    save_path: Union[str, Path],
    denormalize: bool = True,
) -> None:
    """保存图像张量为图像文件"""
```

#### gram_matrix
```python
def gram_matrix(
    features: torch.Tensor,
    normalize: bool = True,
) -> torch.Tensor:
    """计算 Gram 矩阵"""
```

#### StyleTransfer
```python
class StyleTransfer:
    def __init__(
        self,
        content_layers: Optional[list[str]] = None,
        style_layers: Optional[list[str]] = None,
        content_weight: float = 1.0,
        style_weight: float = 1e6,
        tv_weight: float = 1e-5,
        device: str = "auto",
    ):
        """初始化风格迁移器"""

    def transfer(
        self,
        content_image: torch.Tensor,
        style_image: torch.Tensor,
        num_steps: int = 300,
        optimizer_type: str = "lbfgs",
        learning_rate: float = 1.0,
        init_method: str = "content",
        noise_ratio: float = 0.6,
        callback: Optional[Callable] = None,
    ) -> torch.Tensor:
        """执行风格迁移"""
```

### 3.2 内部 API

#### ContentLoss
```python
class ContentLoss(nn.Module):
    def set_target(self, target: torch.Tensor) -> None:
        """设置目标特征"""

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """前向传播"""

    def get_loss(self) -> torch.Tensor:
        """获取损失值"""
```

#### StyleLoss
```python
class StyleLoss(nn.Module):
    def set_target(self, target: torch.Tensor) -> None:
        """设置目标特征"""

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """前向传播"""

    def get_loss(self) -> torch.Tensor:
        """获取损失值"""
```

## 4. 配置设计

### 4.1 默认配置

```python
DEFAULT_CONFIG = {
    "content_layers": ["conv4_2"],
    "style_layers": ["conv1_1", "conv2_1", "conv3_1", "conv4_1", "conv5_1"],
    "content_weight": 1.0,
    "style_weight": 1e6,
    "tv_weight": 1e-5,
    "optimizer": "lbfgs",
    "learning_rate": 1.0,
    "num_steps": 300,
    "init_method": "content",
    "image_size": 512,
}
```

### 4.2 预设配置

```python
PRESETS = {
    "fast": {
        "num_steps": 100,
        "image_size": 256,
    },
    "quality": {
        "num_steps": 500,
        "image_size": 1024,
    },
    "artistic": {
        "style_weight": 1e7,
        "content_weight": 0.5,
    },
    "photo": {
        "style_weight": 1e5,
        "content_weight": 2.0,
        "tv_weight": 1e-4,
    },
}
```

## 5. 错误处理设计

### 5.1 输入验证

```python
def validate_inputs(content_image, style_image):
    """验证输入图像"""
    if content_image.dim() != 4:
        raise ValueError("内容图像必须是 4D 张量 (batch, channels, height, width)")

    if style_image.dim() != 4:
        raise ValueError("风格图像必须是 4D 张量 (batch, channels, height, width)")

    if content_image.shape[1] != 3:
        raise ValueError("图像必须是 RGB 格式（3 个通道）")

    if style_image.shape[1] != 3:
        raise ValueError("图像必须是 RGB 格式（3 个通道）")
```

### 5.2 错误类型

```python
class StyleTransferError(Exception):
    """风格迁移基础异常"""
    pass

class InvalidInputError(StyleTransferError):
    """输入验证错误"""
    pass

class ModelLoadError(StyleTransferError):
    """模型加载错误"""
    pass

class OptimizationError(StyleTransferError):
    """优化过程错误"""
    pass
```

## 6. 性能设计

### 6.1 内存优化

```python
# 使用梯度检查点
torch.utils.checkpoint.checkpoint(layer, input)

# 清理中间结果
del intermediate_features
torch.cuda.empty_cache()
```

### 6.2 计算优化

```python
# 使用混合精度训练
with torch.cuda.amp.autocast():
    output = model(input)

# 使用编译优化
model = torch.compile(model)
```

### 6.3 并行处理

```python
# 批量处理多个风格
def batch_transfer(content, styles):
    """批量风格迁移"""
    return [transfer(content, style) for style in styles]
```

## 7. 扩展性设计

### 7.1 新特征提取器

```python
class CustomFeatureExtractor(nn.Module):
    """自定义特征提取器"""
    def __init__(self, model_name):
        super().__init__()
        if model_name == "resnet":
            self.model = models.resnet50(pretrained=True)
        elif model_name == "efficientnet":
            self.model = models.efficientnet_b0(pretrained=True)
```

### 7.2 新损失函数

```python
class PerceptualLoss(nn.Module):
    """感知损失"""
    def __init__(self, layer_weights):
        super().__init__()
        self.layer_weights = layer_weights

    def forward(self, input, target):
        loss = 0
        for layer, weight in self.layer_weights.items():
            input_features = self.extract_features(input, layer)
            target_features = self.extract_features(target, layer)
            loss += weight * F.mse_loss(input_features, target_features)
        return loss
```

### 7.3 新优化策略

```python
class AdaptiveOptimizer:
    """自适应优化器"""
    def __init__(self, lr, momentum):
        self.lr = lr
        self.momentum = momentum

    def step(self, gradients):
        """自适应更新"""
        # 根据梯度调整学习率
        adaptive_lr = self.lr / (1 + gradients.norm())
        return -adaptive_lr * gradients
```

## 8. 测试设计

### 8.1 单元测试

```python
class TestGramMatrix:
    def test_shape(self):
        """测试输出形状"""

    def test_symmetry(self):
        """测试对称性"""

    def test_positive_semidefinite(self):
        """测试半正定性"""
```

### 8.2 集成测试

```python
class TestStyleTransfer:
    def test_end_to_end(self):
        """端到端测试"""

    def test_different_configs(self):
        """不同配置测试"""
```

### 8.3 性能测试

```python
class TestPerformance:
    def test_memory_usage(self):
        """内存使用测试"""

    def test_speed(self):
        """速度测试"""
```

## 9. 部署设计

### 9.1 依赖管理

```txt
# requirements.txt
torch>=1.9.0
torchvision>=0.10.0
numpy>=1.19.0
Pillow>=8.0.0
matplotlib>=3.3.0
```

### 9.2 打包

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="style-transfer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "numpy>=1.19.0",
        "Pillow>=8.0.0",
    ],
)
```

## 10. 未来扩展

### 10.1 短期目标
- 添加更多预训练模型
- 支持更多图像格式
- 优化内存使用

### 10.2 中期目标
- 实现快速风格迁移
- 支持视频风格迁移
- 添加用户界面

### 10.3 长期目标
- 支持任意风格迁移
- 实现实时处理
- 部署到移动端
