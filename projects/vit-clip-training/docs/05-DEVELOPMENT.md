# 开发手册：ViT/CLIP 训练框架

## 1. 环境搭建

### 1.1 系统要求

**操作系统**：
- Linux (推荐 Ubuntu 20.04+)
- macOS (10.15+)
- Windows 10 (WSL2 推荐)

**硬件要求**：
- **最低配置**：8GB RAM, CPU
- **推荐配置**：16GB RAM, NVIDIA GPU (8GB+)
- **最佳配置**：32GB RAM, NVIDIA A100

**软件要求**：
- Python 3.8+
- CUDA 11.7+ (如果使用 GPU)
- cuDNN 8.0+ (如果使用 GPU)

### 1.2 安装步骤

#### 1.2.1 创建虚拟环境

```bash
# 使用 conda
conda create -n vit-clip python=3.10
conda activate vit-clip

# 或使用 venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

#### 1.2.2 安装 PyTorch

```bash
# GPU 版本 (推荐)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117

# CPU 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 1.2.3 安装项目依赖

```bash
# 克隆项目
git clone <repository-url>
cd vit-clip-training

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖 (可选)
pip install -r requirements-dev.txt
```

#### 1.2.4 验证安装

```bash
# 检查 PyTorch
python -c "import torch; print(f'PyTorch {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# 运行测试
pytest tests/ -v
```

### 1.3 IDE 配置

#### 1.3.1 VS Code

安装扩展：
- Python
- Pylance
- Python Test Explorer
- Jupyter

配置 settings.json：
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

#### 1.3.2 PyCharm

1. 打开项目目录
2. 配置 Python 解释器
3. 配置测试框架

## 2. 项目结构详解

### 2.1 目录结构

```
vit-clip-training/
├── README.md                    # 项目说明
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装脚本 (可选)
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-REQUIREMENTS.md      # 需求分析
│   ├── 03-DESIGN.md            # 技术设计
│   ├── 04-PRODUCT.md           # 产品思维
│   └── 05-DEVELOPMENT.md       # 开发手册
├── src/                         # 源代码
│   ├── __init__.py
│   ├── models/                  # 模型实现
│   │   ├── __init__.py
│   │   ├── vit.py              # Vision Transformer
│   │   ├── text_encoder.py     # 文本编码器
│   │   └── clip.py             # CLIP 模型
│   ├── losses/                  # 损失函数
│   │   ├── __init__.py
│   │   └── contrastive.py      # 对比损失
│   ├── data/                    # 数据处理
│   │   ├── __init__.py
│   │   └── dataset.py          # 数据集实现
│   ├── training/                # 训练逻辑
│   │   ├── __init__.py
│   │   └── trainer.py          # 训练器
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       └── metrics.py          # 评估指标
├── tests/                       # 单元测试
│   ├── __init__.py
│   ├── test_vit.py
│   ├── test_clip.py
│   └── test_contrastive.py
├── examples/                    # 使用示例
│   ├── train_clip.py           # 训练示例
│   └── evaluate.py             # 评估示例
├── configs/                     # 配置文件 (可选)
│   └── default.yaml
└── scripts/                     # 脚本 (可选)
    ├── train.sh
    └── evaluate.sh
```

### 2.2 模块说明

#### 2.2.1 src/models/

**vit.py**：Vision Transformer 实现
- `PatchEmbedding`：将图像分割为 patch
- `MultiHeadAttention`：多头自注意力
- `TransformerBlock`：Transformer 编码块
- `VisionTransformer`：完整的 ViT 模型

**text_encoder.py**：文本编码器实现
- `TextTransformer`：Transformer 文本编码器
- `TextTransformerBlock`：文本 Transformer 块
- `MultiHeadAttention`：带因果掩码的注意力

**clip.py**：CLIP 模型实现
- `CLIPModel`：双编码器架构
- `CLIPConfig`：模型配置
- `create_clip_model`：工厂函数

#### 2.2.2 src/losses/

**contrastive.py**：对比损失函数
- `ContrastiveLoss`：基础对比损失
- `CLIPLoss`：CLIP 对称对比损失
- `SupConLoss`：监督对比损失
- `NTXentLoss`：归一化温度损失

#### 2.2.3 src/data/

**dataset.py**：数据集实现
- `SimpleTokenizer`：简单分词器
- `ImageTextDataset`：图像-文本数据集
- `SyntheticDataset`：合成数据集
- `create_dataloader`：创建数据加载器

#### 2.2.4 src/training/

**trainer.py**：训练器实现
- `TrainingConfig`：训练配置
- `CLIPTrainer`：训练循环
- 检查点保存加载
- 学习率调度

#### 2.2.5 src/utils/

**metrics.py**：评估指标
- `CLIPMetrics`：CLIP 评估指标
- `RetrievalMetrics`：检索指标
- `compute_retrieval_metrics`：计算检索指标

## 3. 核心模块解析

### 3.1 Vision Transformer (ViT)

#### 3.1.1 Patch Embedding

**作用**：将图像转换为序列

**实现细节**：
```python
class PatchEmbedding(nn.Module):
    def __init__(self, image_size, patch_size, in_channels, embed_dim):
        # 使用卷积实现 patch 提取
        self.projection = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size,
            stride=patch_size
        )
        # 可学习的 [CLS] token
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim))
        # 可学习的位置编码
        self.position_embedding = nn.Parameter(
            torch.randn(1, num_patches + 1, embed_dim)
        )

    def forward(self, x):
        # x: (B, C, H, W) -> (B, num_patches, embed_dim)
        x = self.projection(x)
        x = x.flatten(2).transpose(1, 2)
        # 添加 [CLS] token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        # 添加位置编码
        x = x + self.position_embedding
        return x
```

**关键点**：
1. 使用卷积实现 patch 提取和投影
2. [CLS] token 用于分类
3. 位置编码是可学习的

#### 3.1.2 Multi-Head Attention

**作用**：计算自注意力

**实现细节**：
```python
class MultiHeadAttention(nn.Module):
    def __init__(self, embed_dim, num_heads):
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)

    def forward(self, x):
        B, N, D = x.shape
        # 计算 Q, K, V
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        q, k, v = qkv.unbind(0)
        # 计算注意力
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = F.softmax(attn, dim=-1)
        # 加权求和
        x = (attn @ v).transpose(1, 2).reshape(B, N, D)
        return self.proj(x)
```

**关键点**：
1. 使用缩放点积注意力
2. 多头可以学习不同类型的注意力模式
3. 注意力分数需要缩放

#### 3.1.3 Transformer Block

**作用**：组合注意力和 MLP

**实现细节**：
```python
class TransformerBlock(nn.Module):
    def __init__(self, embed_dim, num_heads, mlp_ratio):
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadAttention(embed_dim, num_heads)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, int(embed_dim * mlp_ratio)),
            nn.GELU(),
            nn.Linear(int(embed_dim * mlp_ratio), embed_dim),
        )

    def forward(self, x):
        # Pre-norm: 先归一化再计算
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x
```

**关键点**：
1. Pre-norm 比 Post-norm 更稳定
2. 残差连接帮助梯度流动
3. MLP 使用 GELU 激活函数

### 3.2 CLIP 对比学习

#### 3.2.1 双编码器架构

**作用**：分别编码图像和文本

**实现细节**：
```python
class CLIPModel(nn.Module):
    def __init__(self):
        self.image_encoder = VisionTransformer(...)
        self.text_encoder = TextTransformer(...)
        self.image_projection = nn.Linear(embed_dim, projection_dim)
        self.text_projection = nn.Linear(embed_dim, projection_dim)
        self.logit_scale = nn.Parameter(torch.ones([]) * log(1/0.07))

    def encode_image(self, images):
        features = self.image_encoder(images, return_features=True)
        embeddings = self.image_projection(features)
        return F.normalize(embeddings, dim=-1)

    def encode_text(self, tokens):
        features = self.text_encoder(tokens)
        embeddings = self.text_projection(features)
        return F.normalize(embeddings, dim=-1)
```

**关键点**：
1. 两个编码器独立工作
2. 投影层将特征映射到共享空间
3. L2 归一化确保相似度计算正确

#### 3.2.2 对比损失

**作用**：学习对齐的表示

**实现细节**：
```python
def clip_loss(image_features, text_features):
    # 计算相似度矩阵
    logits = image_features @ text_features.T / temperature
    # 标签：对角线是正样本
    labels = torch.arange(batch_size)
    # 对称损失
    loss_i2t = F.cross_entropy(logits, labels)
    loss_t2i = F.cross_entropy(logits.T, labels)
    return (loss_i2t + loss_t2i) / 2
```

**关键点**：
1. 温度参数控制分布锐度
2. 对称损失确保双向对齐
3. Batch 内负样本提供对比信号

### 3.3 训练循环

#### 3.3.1 学习率调度

**作用**：稳定训练过程

**实现细节**：
```python
def get_lr_scale(step, warmup_steps, total_steps):
    if step < warmup_steps:
        return step / warmup_steps
    progress = (step - warmup_steps) / (total_steps - warmup_steps)
    return 0.5 * (1 + math.cos(math.pi * progress))
```

**关键点**：
1. Warmup 防止早期不稳定
2. 余弦退火平滑学习率下降
3. 最终学习率通常为初始的 1/100

#### 3.3.2 混合精度训练

**作用**：加速训练，节省内存

**实现细节**：
```python
scaler = GradScaler()

with autocast():
    outputs = model(images, texts)
    loss = outputs["loss"]

scaler.scale(loss).backward()
scaler.unscale_(optimizer)
nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
scaler.step(optimizer)
scaler.update()
```

**关键点**：
1. float16 加速计算
2. 梯度缩放防止下溢
3. 梯度裁剪防止爆炸

## 4. 开发流程

### 4.1 代码规范

**风格指南**：
- 遵循 PEP 8
- 使用 Black 格式化
- 使用 isort 排序导入

**类型提示**：
```python
def forward(
    self,
    x: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """Forward pass."""
    pass
```

**文档字符串**：
```python
def compute_loss(
    image_features: torch.Tensor,
    text_features: torch.Tensor,
) -> torch.Tensor:
    """
    Compute CLIP contrastive loss.

    Args:
        image_features: Image embeddings, shape (B, D)
        text_features: Text embeddings, shape (B, D)

    Returns:
        Scalar loss
    """
    pass
```

### 4.2 测试流程

**运行测试**：
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_vit.py -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=src --cov-report=html
```

**编写测试**：
```python
class TestVisionTransformer:
    def test_forward_shape(self):
        model = VisionTransformer(image_size=224, patch_size=16)
        x = torch.randn(2, 3, 224, 224)
        output = model(x)
        assert output.shape == (2, 1000)

    def test_gradient_flow(self):
        model = VisionTransformer()
        x = torch.randn(1, 3, 224, 224)
        output = model(x)
        loss = output.sum()
        loss.backward()
        for param in model.parameters():
            assert param.grad is not None
```

### 4.3 调试技巧

**打印中间结果**：
```python
def forward(self, x):
    print(f"Input shape: {x.shape}")
    x = self.patch_embed(x)
    print(f"After patch embedding: {x.shape}")
    for block in self.blocks:
        x = block(x)
    print(f"After transformer: {x.shape}")
    return x
```

**使用断言**：
```python
def forward(self, x):
    assert x.dim() == 4, "Input must be 4D tensor"
    assert x.shape[1] == 3, "Input must have 3 channels"
    # ...
```

**梯度检查**：
```python
# 检查梯度是否存在
for name, param in model.named_parameters():
    if param.grad is None:
        print(f"Warning: No gradient for {name}")
```

## 5. 性能优化

### 5.1 训练优化

**混合精度训练**：
```python
# 启用 AMP
scaler = GradScaler()
with autocast():
    outputs = model(images, texts)
    loss = outputs["loss"]
scaler.scale(loss).backward()
```

**梯度累积**：
```python
accumulation_steps = 4
for i, batch in enumerate(dataloader):
    loss = model(batch) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

**数据加载优化**：
```python
dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,  # 多进程加载
    pin_memory=True,  # 锁页内存
    prefetch_factor=2,  # 预加载
)
```

### 5.2 内存优化

**梯度检查点**：
```python
from torch.utils.checkpoint import checkpoint

def forward(self, x):
    for block in self.blocks:
        x = checkpoint(block, x)  # 节省内存
    return x
```

**模型并行**：
```python
# 将模型放到不同 GPU
model.image_encoder.to("cuda:0")
model.text_encoder.to("cuda:1")
```

### 5.3 推理优化

**TorchScript**：
```python
scripted_model = torch.jit.script(model)
scripted_model.save("model.pt")
```

**ONNX 导出**：
```python
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    opset_version=14,
)
```

## 6. 常见问题

### 6.1 安装问题

**问题**：PyTorch 安装失败
**解决**：
```bash
# 检查 Python 版本
python --version

# 清理缓存
pip cache purge

# 重新安装
pip install torch --no-cache-dir
```

**问题**：CUDA 不可用
**解决**：
```bash
# 检查 CUDA 版本
nvcc --version

# 安装对应版本的 PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu117
```

### 6.2 训练问题

**问题**：损失不下降
**解决**：
- 检查学习率是否合适
- 检查数据是否正确
- 检查梯度是否正常

**问题**：内存溢出
**解决**：
- 减小 batch size
- 使用梯度累积
- 使用梯度检查点

**问题**：训练速度慢
**解决**：
- 使用混合精度训练
- 增加 num_workers
- 使用 pin_memory

### 6.3 模型问题

**问题**：输出形状不对
**解决**：
- 检查输入形状
- 检查模型配置
- 打印中间结果

**问题**：梯度消失/爆炸
**解决**：
- 检查归一化层
- 调整学习率
- 使用梯度裁剪

## 7. 最佳实践

### 7.1 代码组织

1. **模块化**：每个功能一个模块
2. **清晰命名**：变量名要有意义
3. **适当注释**：解释为什么这样做
4. **类型提示**：提高代码可读性

### 7.2 训练流程

1. **从小开始**：先用小数据集验证
2. **监控训练**：记录损失和指标
3. **定期保存**：避免丢失进度
4. **验证效果**：定期评估模型

### 7.3 版本控制

1. **频繁提交**：小步前进
2. **清晰提交信息**：说明做了什么
3. **使用分支**：开发新功能用新分支
4. **代码审查**：合并前审查代码

## 8. 扩展阅读

### 8.1 论文

- [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929)
- [Learning Transferable Visual Models](https://arxiv.org/abs/2103.00020)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### 8.2 教程

- [PyTorch 官方教程](https://pytorch.org/tutorials/)
- [Hugging Face 教程](https://huggingface.co/docs/transformers)
- [OpenCLIP 文档](https://github.com/mlfoundations/open_clip)

### 8.3 工具

- [Weights & Biases](https://wandb.ai/)：实验跟踪
- [TensorBoard](https://www.tensorflow.org/tensorboard)：可视化
- [Hydra](https://hydra.cc/)：配置管理
