# 技术设计：ViT/CLIP 训练框架

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIP Training Framework                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Models    │  │   Losses    │  │    Data     │            │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤            │
│  │ - ViT       │  │ - CLIPLoss  │  │ - Dataset   │            │
│  │ - TextEnc   │  │ - InfoNCE   │  │ - Tokenizer │            │
│  │ - CLIP      │  │ - SupCon    │  │ - Transform │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Training Engine                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ - Trainer        - Optimizer        - Scheduler         │   │
│  │ - Checkpoint     - Mixed Precision  - Logging           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Evaluation                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ - Retrieval Metrics    - Zero-shot Accuracy             │   │
│  │ - Similarity Analysis  - Representation Quality         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
                    ┌─────────────┐
                    │   CLIP      │
                    │   Model     │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │    ViT    │   │   Text    │   │  Project  │
    │  Encoder  │   │  Encoder  │   │   Layer   │
    └───────────┘   └───────────┘   └───────────┘
          │                │
          ▼                ▼
    ┌───────────┐   ┌───────────┐
    │  Patch    │   │   Token   │
    │ Embedding │   │ Embedding │
    └───────────┘   └───────────┘
```

## 2. 数据结构设计

### 2.1 模型配置

```python
@dataclass
class ViTConfig:
    image_size: int = 224
    patch_size: int = 16
    in_channels: int = 3
    embed_dim: int = 768
    depth: int = 12
    num_heads: int = 12
    mlp_ratio: float = 4.0
    dropout: float = 0.0
    global_pool: str = "cls"

@dataclass
class TextConfig:
    vocab_size: int = 49408
    max_seq_len: int = 77
    embed_dim: int = 512
    depth: int = 12
    num_heads: int = 8
    mlp_ratio: float = 4.0
    dropout: float = 0.0

@dataclass
class CLIPConfig:
    image_config: ViTConfig
    text_config: TextConfig
    projection_dim: int = 512
    init_temperature: float = 0.07
```

### 2.2 训练配置

```python
@dataclass
class TrainingConfig:
    # 模型配置
    model_config: str = "vit_b32"
    image_size: int = 224
    embed_dim: int = 512

    # 训练超参数
    batch_size: int = 32
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    max_epochs: int = 100
    warmup_steps: int = 1000
    max_grad_norm: float = 1.0

    # 损失配置
    loss_type: str = "clip"
    temperature: float = 0.07

    # 混合精度
    use_amp: bool = True

    # 检查点
    checkpoint_dir: str = "checkpoints"
    save_every: int = 1000
    log_every: int = 100
```

### 2.3 数据格式

```python
# 图像-文本对
@dataclass
class ImageTextPair:
    image_path: str
    text: str
    image_id: Optional[str] = None
    caption_id: Optional[str] = None

# 批次数据
@dataclass
class Batch:
    images: torch.Tensor      # (B, C, H, W)
    texts: torch.Tensor       # (B, seq_len)
    labels: Optional[torch.Tensor] = None  # (B,)
```

### 2.4 评估指标

```python
@dataclass
class RetrievalMetrics:
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    median_rank: float
    mean_rank: float
    num_queries: int

@dataclass
class ZeroShotMetrics:
    accuracy: float
    top5_accuracy: float
    num_samples: int
    num_classes: int
```

## 3. 接口设计

### 3.1 模型接口

```python
class VisionTransformer(nn.Module):
    def forward(
        self,
        x: torch.Tensor,
        return_features: bool = False,
    ) -> torch.Tensor:
        """
        Args:
            x: Input images, shape (B, C, H, W)
            return_features: If True, return features before classification head

        Returns:
            If return_features=False: Classification logits, shape (B, num_classes)
            If return_features=True: Features, shape (B, embed_dim)
        """
        pass

class TextTransformer(nn.Module):
    def forward(
        self,
        tokens: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            tokens: Token IDs, shape (B, seq_len)
            attention_mask: Optional mask for padding tokens

        Returns:
            Text features, shape (B, embed_dim)
        """
        pass

class CLIPModel(nn.Module):
    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """Encode images to embeddings."""
        pass

    def encode_text(self, tokens: torch.Tensor) -> torch.Tensor:
        """Encode text to embeddings."""
        pass

    def forward(
        self,
        images: torch.Tensor,
        tokens: torch.Tensor,
        return_loss: bool = True,
    ) -> Dict[str, torch.Tensor]:
        """Forward pass."""
        pass
```

### 3.2 损失函数接口

```python
class CLIPLoss(nn.Module):
    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Compute CLIP contrastive loss.

        Args:
            image_features: Image embeddings, shape (B, D)
            text_features: Text embeddings, shape (B, D)
            labels: Optional labels for computing accuracy

        Returns:
            Scalar loss
        """
        pass
```

### 3.3 训练器接口

```python
class CLIPTrainer:
    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
    ) -> Dict[str, list]:
        """
        Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader (optional)

        Returns:
            Training history
        """
        pass

    def evaluate(
        self,
        test_loader: DataLoader,
    ) -> Dict[str, float]:
        """
        Evaluate model on test set.

        Args:
            test_loader: Test data loader

        Returns:
            Evaluation metrics
        """
        pass

    def save_checkpoint(self, filename: str):
        """Save training checkpoint."""
        pass

    def load_checkpoint(self, filename: str):
        """Load training checkpoint."""
        pass
```

### 3.4 评估接口

```python
class CLIPMetrics:
    def compute_retrieval(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
        k_values: List[int] = [1, 5, 10],
    ) -> Tuple[RetrievalMetrics, RetrievalMetrics]:
        """
        Compute retrieval metrics.

        Returns:
            Tuple of (I2T metrics, T2I metrics)
        """
        pass

    def compute_zero_shot_accuracy(
        self,
        image_features: torch.Tensor,
        class_features: torch.Tensor,
        labels: torch.Tensor,
    ) -> Dict[str, float]:
        """
        Compute zero-shot classification accuracy.
        """
        pass
```

## 4. 算法设计

### 4.1 Patch Embedding 算法

```python
def patch_embedding(image, patch_size, embed_dim):
    """
    将图像分割为 patch 并嵌入

    算法步骤：
    1. 将图像分割为不重叠的 patch
    2. 将每个 patch 展平为向量
    3. 线性投影到 embed_dim 维度
    4. 添加 [CLS] token
    5. 添加位置编码
    """
    # 使用卷积实现 patch 提取和投影
    # kernel_size = stride = patch_size
    patches = conv2d(image, kernel_size=patch_size, stride=patch_size)

    # 展平空间维度
    patches = patches.flatten(2).transpose(1, 2)  # (B, num_patches, embed_dim)

    # 添加 [CLS] token
    cls_token = learnable_parameter(1, 1, embed_dim)
    patches = concat([cls_token.expand(B, -1, -1), patches], dim=1)

    # 添加位置编码
    position_embedding = learnable_parameter(1, num_patches + 1, embed_dim)
    patches = patches + position_embedding

    return patches
```

### 4.2 自注意力算法

```python
def self_attention(x, num_heads):
    """
    多头自注意力

    算法步骤：
    1. 计算 Q, K, V
    2. 计算注意力分数
    3. 应用 softmax
    4. 加权求和
    """
    B, N, D = x.shape
    head_dim = D // num_heads

    # 计算 Q, K, V
    Q = linear(x)  # (B, N, D)
    K = linear(x)  # (B, N, D)
    V = linear(x)  # (B, N, D)

    # 分割多头
    Q = Q.reshape(B, N, num_heads, head_dim).transpose(1, 2)  # (B, H, N, head_dim)
    K = K.reshape(B, N, num_heads, head_dim).transpose(1, 2)
    V = V.reshape(B, N, num_heads, head_dim).transpose(1, 2)

    # 计算注意力分数
    attn = (Q @ K.transpose(-2, -1)) / sqrt(head_dim)  # (B, H, N, N)

    # 应用 softmax
    attn = softmax(attn, dim=-1)

    # 加权求和
    out = attn @ V  # (B, H, N, head_dim)
    out = out.transpose(1, 2).reshape(B, N, D)  # (B, N, D)

    # 输出投影
    out = linear(out)

    return out
```

### 4.3 CLIP 对比损失算法

```python
def clip_loss(image_features, text_features, temperature):
    """
    CLIP 对称对比损失

    算法步骤：
    1. L2 归一化特征
    2. 计算相似度矩阵
    3. 计算图像到文本的交叉熵
    4. 计算文本到图像的交叉熵
    5. 取平均
    """
    # L2 归一化
    image_features = normalize(image_features, dim=1)
    text_features = normalize(text_features, dim=1)

    # 计算相似度矩阵
    logits_per_image = image_features @ text_features.T / temperature
    logits_per_text = logits_per_image.T

    # 标签：对角线是正样本
    labels = arange(batch_size)

    # 对称交叉熵损失
    loss_i2t = cross_entropy(logits_per_image, labels)
    loss_t2i = cross_entropy(logits_per_text, labels)

    return (loss_i2t + loss_t2i) / 2
```

### 4.4 学习率调度算法

```python
def cosine_warmup_schedule(step, warmup_steps, total_steps, base_lr):
    """
    带 warmup 的余弦退火调度

    算法步骤：
    1. 如果 step < warmup_steps: 线性增加
    2. 否则: 余弦退火
    """
    if step < warmup_steps:
        # 线性 warmup
        return base_lr * step / warmup_steps
    else:
        # 余弦退火
        progress = (step - warmup_steps) / (total_steps - warmup_steps)
        return base_lr * 0.5 * (1 + cos(pi * progress))
```

## 5. 数据流设计

### 5.1 训练数据流

```
输入: (images, texts)
    │
    ├── images: (B, C, H, W)
    │   │
    │   ▼
    │   Image Augmentation
    │   │
    │   ▼
    │   ViT Encoder
    │   │
    │   ▼
    │   Projection Layer
    │   │
    │   ▼
    │   image_features: (B, D)
    │
    ├── texts: (B, seq_len)
    │   │
    │   ▼
    │   Text Tokenization
    │   │
    │   ▼
    │   Text Encoder
    │   │
    │   ▼
    │   Projection Layer
    │   │
    │   ▼
    │   text_features: (B, D)
    │
    ▼
    Contrastive Loss
    │
    ▼
    Backward Pass
    │
    ▼
    Optimizer Step
```

### 5.2 推理数据流

```
输入: image
    │
    ▼
    Image Preprocessing
    │
    ▼
    ViT Encoder
    │
    ▼
    Projection Layer
    │
    ▼
    L2 Normalization
    │
    ▼
    image_embedding: (D,)
    │
    ▼
    Similarity Search
    │
    ▼
    Top-K Results
```

## 6. 存储设计

### 6.1 检查点格式

```python
checkpoint = {
    "epoch": int,
    "global_step": int,
    "model_state_dict": dict,
    "optimizer_state_dict": dict,
    "scheduler_state_dict": dict,
    "best_loss": float,
    "history": dict,
    "config": TrainingConfig,
}
```

### 6.2 模型权重格式

```python
model_weights = {
    "image_encoder": dict,
    "text_encoder": dict,
    "image_projection": dict,
    "text_projection": dict,
    "logit_scale": tensor,
}
```

## 7. 错误处理设计

### 7.1 输入验证

```python
def validate_inputs(images, tokens):
    """验证输入数据的形状和类型"""
    assert images.dim() == 4, "Images must be 4D tensor"
    assert images.shape[1] == 3, "Images must have 3 channels"
    assert tokens.dim() == 2, "Tokens must be 2D tensor"
    assert tokens.max() < vocab_size, "Token ID out of vocabulary"
```

### 7.2 数值稳定性

```python
def stable_softmax(logits, dim=-1):
    """数值稳定的 softmax"""
    max_val = logits.max(dim=dim, keepdim=True)
    exp_logits = torch.exp(logits - max_val)
    return exp_logits / exp_logits.sum(dim=dim, keepdim=True)
```

### 7.3 内存管理

```python
def gradient_checkpointing(module, *inputs):
    """梯度检查点以节省内存"""
    return torch.utils.checkpoint.checkpoint(module, *inputs)
```

## 8. 扩展性设计

### 8.1 模型扩展

```python
# 注册新的模型配置
VIT_CONFIGS["vit_huge"] = lambda: VisionTransformer(
    embed_dim=1280,
    depth=32,
    num_heads=16,
)

# 创建新模型
model = create_vit("vit_huge")
```

### 8.2 损失函数扩展

```python
# 注册新的损失函数
LOSS_REGISTRY["my_loss"] = MyCustomLoss

# 使用新损失
loss_fn = create_loss("my_loss")
```

### 8.3 数据集扩展

```python
# 自定义数据集
class MyDataset(ImageTextDataset):
    def __getitem__(self, idx):
        # 自定义数据加载逻辑
        pass
```

## 9. 性能设计

### 9.1 计算优化

- **混合精度训练**：使用 float16 加速计算
- **梯度累积**：模拟大 batch size
- **梯度检查点**：减少内存占用

### 9.2 内存优化

- **模型并行**：大模型分割到多 GPU
- **数据并行**：多 GPU 并行训练
- **激活检查点**：减少中间激活存储

### 9.3 IO 优化

- **预加载数据**：后台预加载下一批数据
- **内存映射**：大文件使用内存映射
- **多进程加载**：并行数据加载

## 10. 测试设计

### 10.1 单元测试

- 模型形状测试
- 损失函数测试
- 数据处理测试

### 10.2 集成测试

- 训练循环测试
- 评估流程测试
- 检查点保存加载测试

### 10.3 性能测试

- 训练速度测试
- 内存占用测试
- 推理延迟测试
