# 05 - 开发文档

## 开发环境

### 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 依赖说明

```
torch>=2.0.0        # PyTorch 深度学习框架
torchvision>=0.15.0 # 计算机视觉工具
numpy>=1.24.0       # 数值计算
pytest>=7.0.0       # 测试框架
```

## 项目结构

```
clip/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── clip_model.py      # CLIP 主模型
│   ├── encoders.py        # 编码器
│   ├── contrastive_loss.py # 损失函数
│   ├── trainer.py         # 训练器
│   └── dataset.py         # 数据集
├── tests/                  # 测试
│   ├── test_clip.py
│   └── test_trainer.py
├── examples/               # 示例
│   ├── train_clip.py
│   └── zero_shot.py
├── docs/                   # 文档
├── requirements.txt
└── README.md
```

## 开发流程

### 1. 代码风格

遵循 PEP 8 规范：

```python
# 函数命名
def compute_similarity(embeddings1, embeddings2):
    pass

# 类命名
class ImageEncoder(nn.Module):
    pass

# 常量命名
MAX_SEQ_LENGTH = 77
EMBED_DIM = 512
```

### 2. 类型注解

使用类型注解提高代码可读性：

```python
from typing import Optional, Tuple, List

def encode_image(
    self,
    images: torch.Tensor,
    return_features: bool = False,
) -> torch.Tensor:
    """Encode images to embeddings."""
    pass
```

### 3. 文档字符串

使用 Google 风格文档字符串：

```python
def forward(
    self,
    images: torch.Tensor,
    input_ids: torch.Tensor,
) -> Tuple[torch.Tensor, dict]:
    """
    Forward pass for training.

    Args:
        images: Input images [batch_size, channels, height, width]
        input_ids: Token IDs [batch_size, seq_length]

    Returns:
        loss: Contrastive loss
        metrics: Dictionary of metrics
    """
    pass
```

### 4. 测试

编写测试时遵循：

```python
class TestComponent:
    """Tests for Component."""

    def test_normal_behavior(self):
        """测试正常行为"""
        pass

    def test_edge_cases(self):
        """测试边界情况"""
        pass

    def test_error_handling(self):
        """测试错误处理"""
        pass
```

## 运行命令

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_clip.py -v

# 运行特定测试类
pytest tests/test_clip.py::TestCLIPModel -v

# 运行特定测试方法
pytest tests/test_clip.py::TestCLIPModel::test_forward_pass -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 运行示例

```bash
# 训练示例
python examples/train_clip.py

# 零样本分类示例
python examples/zero_shot.py
```

### 代码检查

```bash
# 格式化代码
black src/ tests/ examples/

# 代码风格检查
flake8 src/ tests/ examples/

# 类型检查
mypy src/
```

## 调试技巧

### 1. 使用断点

```python
import pdb; pdb.set_trace()
```

### 2. 打印张量形状

```python
print(f"Tensor shape: {tensor.shape}")
print(f"Tensor dtype: {tensor.dtype}")
print(f"Tensor device: {tensor.device}")
```

### 3. 检查梯度

```python
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm():.6f}")
```

### 4. 监控内存

```python
import torch

print(f"Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
print(f"Cached: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")
```

## 常见问题

### Q: 如何添加新的编码器？

1. 在 `encoders.py` 中创建新类
2. 继承 `nn.Module`
3. 实现 `forward` 方法
4. 在 `__init__.py` 中导出
5. 编写测试

```python
class NewEncoder(nn.Module):
    def __init__(self, embed_dim):
        super().__init__()
        # 初始化层

    def forward(self, x):
        # 前向传播
        return embeddings
```

### Q: 如何修改损失函数？

1. 在 `contrastive_loss.py` 中创建新类
2. 继承 `nn.Module`
3. 实现 `forward` 方法
4. 返回损失和指标字典

```python
class NewLoss(nn.Module):
    def forward(self, embeddings1, embeddings2):
        loss = compute_loss(embeddings1, embeddings2)
        metrics = {"loss": loss.item()}
        return loss, metrics
```

### Q: 如何使用自定义数据集？

1. 创建 `Dataset` 子类
2. 实现 `__getitem__` 方法
3. 返回字典格式数据

```python
class CustomDataset(Dataset):
    def __getitem__(self, idx):
        return {
            "images": image_tensor,
            "input_ids": token_ids,
            "attention_mask": mask,
        }
```

## 部署

### 模型导出

```python
# 保存模型
torch.save(model.state_dict(), "clip_model.pt")

# 加载模型
model = CLIP(embed_dim=512)
model.load_state_dict(torch.load("clip_model.pt"))
model.eval()
```

### ONNX 导出

```python
import torch.onnx

dummy_images = torch.randn(1, 3, 224, 224)
dummy_input_ids = torch.randint(0, 10000, (1, 77))

torch.onnx.export(
    model,
    (dummy_images, dummy_input_ids),
    "clip_model.onnx",
    input_names=["images", "input_ids"],
    output_names=["embeddings"],
)
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
style: 代码格式
chore: 其他更改
```

## 版本历史

- **v0.1.0** - 初始版本
  - 实现 CLIP 核心架构
  - 实现对比损失
  - 实现训练流程
  - 实现零样本分类
