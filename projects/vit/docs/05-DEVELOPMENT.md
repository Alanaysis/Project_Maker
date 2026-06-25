# 05 - 开发文档：Vision Transformer

## 1. 环境搭建

### 1.1 系统要求

- Python 3.8+
- PyTorch 1.12+
- 操作系统：Linux / macOS / Windows

### 1.2 安装依赖

```bash
cd projects/vit
pip install -r requirements.txt
```

依赖列表：
- `torch>=1.12.0` - 深度学习框架
- `torchvision>=0.13.0` - 计算机视觉工具
- `numpy>=1.21.0` - 数值计算
- `pytest>=7.0.0` - 测试框架

### 1.3 虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

## 2. 项目结构

```
vit/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── patch_embedding.py # Patch Embedding
│   ├── attention.py       # Multi-Head Self-Attention
│   ├── transformer.py     # Transformer Encoder
│   ├── vit.py            # Vision Transformer
│   ├── trainer.py        # 训练器
│   └── visualization.py  # 可视化工具
├── tests/                  # 测试
│   ├── test_patch_embedding.py
│   ├── test_attention.py
│   ├── test_transformer.py
│   └── test_vit.py
├── examples/               # 示例
│   ├── compare_models.py
│   └── attention_visualization.py
├── docs/                   # 文档
├── train.py               # 训练脚本
├── demo.py                # 演示脚本
├── requirements.txt       # 依赖
├── README.md              # 项目说明
└── LEARNING_NOTES.md      # 学习笔记
```

## 3. 快速开始

### 3.1 运行演示

```bash
python demo.py
```

演示内容：
1. Patch Embedding 工作原理
2. Multi-Head Self-Attention 机制
3. Transformer Encoder 结构
4. 完整 ViT 模型
5. 端到端训练

### 3.2 运行测试

```bash
pytest tests/ -v
```

### 3.3 训练模型

```bash
# 使用 MNIST 数据集（默认）
python train.py

# 使用 CIFAR-10 数据集
python train.py --dataset cifar10

# 自定义参数
python train.py --epochs 20 --lr 1e-3 --model tiny
```

### 3.4 运行示例

```bash
# 模型对比
python examples/compare_models.py

# 注意力可视化
python examples/attention_visualization.py
```

## 4. 代码规范

### 4.1 命名规范

- **类名**：PascalCase（如 `VisionTransformer`）
- **函数名**：snake_case（如 `forward`）
- **变量名**：snake_case（如 `embed_dim`）
- **常量**：UPPER_CASE（如 `NUM_HEADS`）

### 4.2 文档规范

- 每个模块有模块级 docstring
- 每个类有类级 docstring
- 每个公共方法有方法级 docstring
- 关键代码有行内注释

### 4.3 类型注解

```python
def forward(
    self,
    x: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    ...
```

## 5. 调试技巧

### 5.1 形状调试

在关键位置打印张量形状：

```python
print(f"x.shape: {x.shape}")  # 调试用
```

### 5.2 梯度调试

检查梯度是否存在和数值：

```python
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_norm={param.grad.norm():.6f}")
    else:
        print(f"{name}: NO GRADIENT")
```

### 5.3 注意力可视化

使用 `get_attention_maps` 查看注意力分布：

```python
attn_maps = model.get_attention_maps(x)
for i, attn in enumerate(attn_maps):
    print(f"Layer {i}: {attn.shape}, range=[{attn.min():.4f}, {attn.max():.4f}]")
```

### 5.4 数值稳定性

检查是否有 NaN 或 Inf：

```python
assert not torch.isnan(output).any(), "NaN detected!"
assert not torch.isinf(output).any(), "Inf detected!"
```

## 6. 扩展指南

### 6.1 添加新的模型变体

在 `vit.py` 中添加工厂方法：

```python
@staticmethod
def vit_custom(img_size=224, patch_size=16, num_classes=10, **kwargs):
    return VisionTransformer(
        img_size=img_size,
        patch_size=patch_size,
        num_classes=num_classes,
        embed_dim=512,
        depth=6,
        num_heads=8,
        **kwargs,
    )
```

### 6.2 添加新的注意力机制

在 `attention.py` 中添加新类：

```python
class RelativePositionAttention(nn.Module):
    """带相对位置编码的注意力"""
    ...
```

### 6.3 添加新的数据集

在 `trainer.py` 中添加数据加载器：

```python
@staticmethod
def create_custom_loaders(batch_size=64, ...):
    ...
```

## 7. 常见问题

### 7.1 CUDA 内存不足

**问题**：`RuntimeError: CUDA out of memory`

**解决**：
- 减小 batch_size
- 使用更小的模型（ViT-Tiny）
- 使用梯度累积
- 使用混合精度训练

### 7.2 训练损失不下降

**问题**：训练损失保持在较高水平

**解决**：
- 检查学习率是否合适
- 检查数据预处理是否正确
- 检查标签是否正确
- 使用学习率 warmup

### 7.3 过拟合

**问题**：训练准确率高，验证准确率低

**解决**：
- 增加数据增强
- 增加 Dropout
- 增加权重衰减
- 使用更小的模型

## 8. 参考资源

### 8.1 论文

1. [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929)
2. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
3. [Training Data-Efficient Image Transformers](https://arxiv.org/abs/2012.12877)

### 8.2 教程

1. [PyTorch ViT Tutorial](https://pytorch.org/tutorials/intermediate/vt_tutorial.html)
2. [The Annotated Transformer](https://nlp.seas.harvard.edu/annotated-transformer/)

### 8.3 代码库

1. [Google ViT](https://github.com/google-research/vision_transformer)
2. [Facebook DeiT](https://github.com/facebookresearch/deit)
3. [timm](https://github.com/huggingface/pytorch-image-models)
