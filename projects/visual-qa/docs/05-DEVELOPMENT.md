# 视觉问答开发文档

## 1. 开发环境

### 1.1 环境要求

- **Python**: 3.8+
- **PyTorch**: 1.9+
- **torchvision**: 0.10+
- **pytest**: 6.0+

### 1.2 安装依赖

```bash
pip install -r requirements.txt
```

### 1.3 目录结构

```
visual-qa/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── vqa_model.py       # VQA 主模型
│   ├── image_encoder.py   # 图像编码器
│   ├── text_encoder.py    # 文本编码器
│   ├── fusion.py          # 融合模块
│   ├── answer_predictor.py # 答案预测器
│   ├── dataset.py         # 数据集
│   └── trainer.py         # 训练器
├── tests/                  # 测试
│   └── test_vqa.py
├── examples/               # 示例
│   ├── train_vqa.py
│   └── inference.py
├── docs/                   # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── requirements.txt
├── README.md
└── LEARNING_NOTES.md
```

## 2. 快速开始

### 2.1 运行示例

```bash
# 训练示例
python examples/train_vqa.py

# 推理示例
python examples/inference.py
```

### 2.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ --cov=src
```

## 3. 开发流程

### 3.1 添加新的骨干网络

1. 在 `image_encoder.py` 中添加新的骨干网络：

```python
def _create_backbone(self, backbone: str, pretrained: bool):
    if backbone == 'resnet18':
        # 现有代码
    elif backbone == 'efficientnet':
        # 新增 EfficientNet
        model = models.efficientnet_b0(pretrained=pretrained)
        backbone_out_dim = model.classifier[1].in_features
        model = model.features
    return model, backbone_out_dim
```

2. 在测试中添加对应测试：

```python
def test_efficientnet_encoder(self):
    encoder = ImageEncoder(backbone='efficientnet', feature_dim=512)
    x = torch.randn(2, 3, 224, 224)
    output = encoder(x)
    assert output.shape == (2, 512)
```

### 3.2 添加新的融合策略

1. 在 `fusion.py` 中添加新的融合类：

```python
class GatedFusion(nn.Module):
    """门控融合"""
    def __init__(self, image_dim, text_dim, output_dim):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(image_dim + text_dim, output_dim),
            nn.Sigmoid(),
        )
        self.transform = nn.Linear(image_dim + text_dim, output_dim)

    def forward(self, image_features, text_features):
        combined = torch.cat([image_features, text_features], dim=1)
        gate = self.gate(combined)
        transformed = self.transform(combined)
        return gate * transformed
```

2. 在 `FusionModule` 中注册：

```python
class FusionModule(nn.Module):
    def __init__(self, fusion_type, ...):
        if fusion_type == 'gated':
            self.fusion = GatedFusion(image_dim, text_dim, output_dim)
```

### 3.3 添加新的文本编码器

1. 在 `text_encoder.py` 中添加新的编码器：

```python
class GRUTextEncoder(nn.Module):
    """GRU 文本编码器"""
    def __init__(self, vocab_size, embed_dim, hidden_dim, feature_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.projection = nn.Linear(hidden_dim, feature_dim)

    def forward(self, input_ids):
        embedded = self.embedding(input_ids)
        output, hidden = self.gru(embedded)
        return self.projection(hidden.squeeze(0))
```

2. 在 `VQAModel` 中支持新的编码器类型。

## 4. 代码规范

### 4.1 命名规范

- **类名**: PascalCase (如 `ImageEncoder`)
- **函数名**: snake_case (如 `forward`)
- **变量名**: snake_case (如 `image_features`)
- **常量**: UPPER_CASE (如 `MAX_SEQ_LEN`)

### 4.2 文档规范

- 每个模块添加文档字符串
- 每个类添加使用示例
- 每个函数添加参数说明

```python
class ImageEncoder(nn.Module):
    """
    图像编码器

    使用预训练 CNN 提取图像特征。

    Args:
        backbone: 骨干网络类型
        pretrained: 是否使用预训练权重
        feature_dim: 输出特征维度

    Example:
        >>> encoder = ImageEncoder(backbone='resnet18')
        >>> images = torch.randn(2, 3, 224, 224)
        >>> features = encoder(images)
        >>> print(features.shape)
        torch.Size([2, 512])
    """
```

### 4.3 类型注解

```python
from typing import Optional, Tuple, Dict

def forward(
    self,
    images: Optional[torch.Tensor] = None,
    question_ids: Optional[torch.Tensor] = None,
    targets: Optional[torch.Tensor] = None,
) -> Dict[str, torch.Tensor]:
    """前向传播"""
    pass
```

## 5. 调试技巧

### 5.1 打印中间结果

```python
def forward(self, images, question_ids):
    # 打印输入形状
    print(f"images shape: {images.shape}")
    print(f"question_ids shape: {question_ids.shape}")

    # 编码
    image_features = self.image_encoder(images)
    print(f"image_features shape: {image_features.shape}")

    text_features = self.text_encoder(question_ids)
    print(f"text_features shape: {text_features.shape}")

    # 融合
    fused_features = self.fusion(image_features, text_features)
    print(f"fused_features shape: {fused_features.shape}")

    return fused_features
```

### 5.2 使用断点调试

```python
import pdb

def forward(self, images, question_ids):
    image_features = self.image_encoder(images)
    pdb.set_trace()  # 断点
    text_features = self.text_encoder(question_ids)
    return self.fusion(image_features, text_features)
```

### 5.3 可视化特征

```python
import matplotlib.pyplot as plt

def visualize_features(features, title):
    """可视化特征分布"""
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.hist(features.flatten().numpy(), bins=50)
    plt.title(f"{title} Distribution")

    plt.subplot(1, 2, 2)
    plt.imshow(features[:10].numpy(), aspect='auto')
    plt.title(f"{title} Heatmap")
    plt.show()
```

## 6. 性能优化

### 6.1 模型优化

#### 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    with autocast():
        outputs = model(batch)
        loss = outputs['loss']

    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

#### 梯度累积

```python
accumulation_steps = 4

for i, batch in enumerate(dataloader):
    outputs = model(batch)
    loss = outputs['loss'] / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 6.2 数据优化

#### 预提取特征

```python
def precompute_features(image_encoder, dataloader, save_path):
    """预提取图像特征"""
    features = {}
    for images, image_ids in dataloader:
        with torch.no_grad():
            feats = image_encoder(images)
        for id, feat in zip(image_ids, feats):
            features[id] = feat.cpu()

    torch.save(features, save_path)
```

#### 多进程数据加载

```python
dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,
    pin_memory=True,
    prefetch_factor=2,
)
```

### 6.3 推理优化

#### 模型量化

```python
# 动态量化
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {nn.Linear},
    dtype=torch.qint8,
)
```

#### TorchScript 导出

```python
# 追踪模型
traced_model = torch.jit.trace(model, example_input)
traced_model.save("model.pt")
```

## 7. 扩展功能

### 7.1 添加注意力可视化

```python
class AttentionVisualizer:
    def __init__(self, model):
        self.model = model
        self.attention_weights = {}

    def hook(self, module, input, output):
        self.attention_weights['attention'] = output[1]

    def visualize(self, images, questions):
        # 注册 hook
        handle = self.model.fusion.fusion.cross_attention.register_forward_hook(self.hook)

        # 前向传播
        outputs = self.model(images, questions)

        # 可视化注意力
        attention = self.attention_weights['attention']
        self.plot_attention(attention)

        handle.remove()
```

### 7.2 添加模型解释

```python
class VQAExplainer:
    def __init__(self, model):
        self.model = model

    def explain(self, image, question):
        """生成模型解释"""
        # 获取中间特征
        outputs = self.model(image, question)

        # 特征重要性
        image_importance = self.compute_importance(outputs['image_features'])
        text_importance = self.compute_importance(outputs['text_features'])

        return {
            'image_importance': image_importance,
            'text_importance': text_importance,
            'prediction': outputs['logits'].argmax(),
        }
```

### 7.3 添加在线学习

```python
class OnlineLearner:
    def __init__(self, model, learning_rate=1e-4):
        self.model = model
        self.optimizer = Adam(model.parameters(), lr=learning_rate)

    def update(self, image, question, answer):
        """在线更新模型"""
        self.model.train()

        outputs = self.model(image, question, targets=answer)
        loss = outputs['loss']

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()
```

## 8. 部署指南

### 8.1 模型导出

```python
# TorchScript 导出
model.eval()
example_input = {
    'images': torch.randn(1, 3, 224, 224),
    'question_ids': torch.randint(0, 1000, (1, 10)),
}
traced_model = torch.jit.trace(model, example_input)
traced_model.save("vqa_model.pt")

# ONNX 导出
torch.onnx.export(
    model,
    example_input,
    "vqa_model.onnx",
    input_names=['images', 'question_ids'],
    output_names=['logits'],
)
```

### 8.2 REST API 服务

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
model = load_model("vqa_model.pt")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    image = preprocess_image(data['image'])
    question = encode_question(data['question'])

    with torch.no_grad():
        outputs = model(image, question)

    return jsonify({
        'answer': decode_answer(outputs['logits'].argmax()),
        'confidence': outputs['logits'].max().item(),
    })
```

### 8.3 Docker 部署

```dockerfile
FROM pytorch/pytorch:1.9.0-cuda11.1-cudnn8-runtime

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "server.py"]
```

## 9. 常见问题

### 9.1 CUDA 内存不足

```python
# 减小批次大小
batch_size = 16  # 而不是 32

# 使用梯度累积
accumulation_steps = 4

# 预提取图像特征
precompute_features = True
```

### 9.2 训练不收敛

```python
# 检查学习率
learning_rate = 1e-3  # 尝试不同值

# 检查数据
print(f"数据集大小: {len(dataset)}")
print(f"答案分布: {Counter(answers)}")

# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_norm={param.grad.norm():.4f}")
```

### 9.3 推理速度慢

```python
# 使用 GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 使用 TorchScript
model = torch.jit.script(model)

# 批量推理
batch_size = 32
```

## 10. 学习资源

### 10.1 相关论文

- VQA: Visual Question Answering (ICCV 2015)
- Stacked Attention Networks (CVPR 2016)
- Bottom-Up Attention (CVPR 2018)
- ViLBERT (NeurIPS 2019)

### 10.2 在线课程

- Stanford CS231n: CNN for Visual Recognition
- Stanford CS224n: NLP with Deep Learning
- CMU 11-777: Multimodal Machine Learning

### 10.3 开源项目

- [CLIP](https://github.com/openai/CLIP)
- [Hugging Face Transformers](https://github.com/huggingface/transformers)
- [LXMERT](https://github.com/airsplay/lxmert)

## 11. 贡献指南

### 11.1 提交代码

1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 提交 PR

### 11.2 代码审查

- 代码风格一致
- 测试覆盖完整
- 文档更新及时

### 11.3 问题反馈

- 使用 GitHub Issues
- 提供复现步骤
- 包含错误信息
