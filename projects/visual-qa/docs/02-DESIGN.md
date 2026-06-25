# 视觉问答设计文档

## 1. 系统架构

### 1.1 整体架构

```
输入层
├── 图像输入 [B, C, H, W]
└── 问题输入 [B, seq_len]

编码层
├── 图像编码器 (CNN)
│   ├── ResNet-18/34/50
│   └── 特征投影
└── 文本编码器 (RNN/Transformer)
    ├── 词嵌入
    ├── 序列编码
    └── 特征提取

融合层
├── 拼接融合
├── 双线性融合
├── 注意力融合
└── 协同注意力融合

预测层
├── 全连接网络
└── Softmax 分类

输出层
└── 答案预测
```

### 1.2 数据流

```python
# 1. 图像特征提取
image_features = image_encoder(images)  # [B, image_dim]

# 2. 文本特征提取
text_features = text_encoder(questions)  # [B, text_dim]

# 3. 多模态融合
fused_features = fusion(image_features, text_features)  # [B, fusion_dim]

# 4. 答案预测
logits = predictor(fused_features)  # [B, num_answers]
```

## 2. 模块设计

### 2.1 图像编码器 (ImageEncoder)

#### 设计目标
- 提取图像的高级语义特征
- 支持多种预训练骨干网络
- 可选择是否冻结参数

#### 架构设计

```python
class ImageEncoder:
    backbone: CNN骨干网络
    projection: 特征投影层

    forward(images) -> features
```

#### 骨干网络选择

| 网络 | 层数 | 参数量 | 特点 |
|------|------|--------|------|
| ResNet-18 | 18 | 11M | 轻量级，适合快速实验 |
| ResNet-34 | 34 | 21M | 中等规模 |
| ResNet-50 | 50 | 25M | 更强的表达能力 |
| VGG-16 | 16 | 138M | 传统架构 |

#### 输出维度
- 默认: 512
- 可配置: 128, 256, 512, 1024

### 2.2 文本编码器 (TextEncoder)

#### 设计目标
- 编码问题的语义信息
- 支持 RNN 和 Transformer 架构
- 处理变长序列

#### RNN 架构

```python
class TextEncoder:
    embedding: 词嵌入层
    rnn: LSTM/GRU
    projection: 特征投影

    forward(input_ids) -> features
```

#### Transformer 架构

```python
class TransformerTextEncoder:
    embedding: 词嵌入
    position_embedding: 位置编码
    transformer: Transformer Encoder
    projection: 特征投影

    forward(input_ids) -> features
```

#### 关键设计决策

1. **双向 RNN**: 使用双向 LSTM/GRU 捕获前后文信息
2. **Padding 处理**: 使用 padding_idx=0 处理变长序列
3. **最终表示**: 使用最后隐藏状态或平均池化

### 2.3 融合模块 (FusionModule)

#### 设计目标
- 有效融合图像和文本特征
- 支持多种融合策略
- 可扩展新的融合方法

#### 融合策略

##### 2.3.1 拼接融合 (ConcatFusion)

```python
# 最简单的融合方式
combined = concat(image_features, text_features)
output = MLP(combined)
```

- 优点: 简单有效
- 缺点: 不建模模态间交互

##### 2.3.2 双线性融合 (BilinearFusion)

```python
# 建模二阶交互
output = bilinear(image_features, text_features)
```

- 优点: 建模二阶交互
- 缺点: 计算复杂度高

##### 2.3.3 注意力融合 (AttentionFusion)

```python
# 使用注意力机制融合
query = image_features
key_value = concat(image_features, text_features)
output = cross_attention(query, key_value)
```

- 优点: 动态聚焦相关信息
- 缺点: 需要更多计算

##### 2.3.4 协同注意力融合 (CoAttentionFusion)

```python
# 双向注意力
i2t_attention = attend(image, text)
t2i_attention = attend(text, image)
output = fuse(i2t, t2i)
```

- 优点: 双向交互
- 缺点: 实现复杂

### 2.4 答案预测器 (AnswerPredictor)

#### 设计目标
- 基于融合特征预测答案
- 支持分类和 top-k 预测
- 计算损失和准确率

#### 架构设计

```python
class AnswerPredictor:
    classifier: MLP 分类器

    forward(fused_features, targets) -> outputs
    predict(fused_features) -> (predictions, confidence)
    predict_top_k(fused_features, k) -> (top_k_preds, top_k_conf)
```

#### 分类策略

- **答案集合**: 预定义最常见的 N 个答案
- **多类分类**: 使用交叉熵损失
- **Top-K**: 输出最可能的 K 个答案

## 3. 数据设计

### 3.1 数据格式

```python
{
    'question': "what color is the cat",
    'image_id': "image_0001",
    'answer': "red",
    'question_ids': [5, 12, 3, 7, 8],  # 编码后的问题
    'image_features': tensor,  # 图像特征
    'answer_idx': 2,  # 答案索引
}
```

### 3.2 词汇表设计

```python
class Vocab:
    word2idx: Dict[str, int]  # 词到索引映射
    idx2word: Dict[int, str]  # 索引到词映射

    encode(text) -> List[int]
    decode(ids) -> str
```

### 3.3 数据集类

```python
class VQADataset(Dataset):
    questions: List[str]
    image_ids: List[str]
    answers: List[str]
    vocab: Vocab

    __getitem__(idx) -> Dict[str, Tensor]
```

## 4. 训练设计

### 4.1 损失函数

使用交叉熵损失：

```python
loss = CrossEntropyLoss(logits, targets)
```

### 4.2 优化器

使用 Adam 优化器：

```python
optimizer = Adam(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-4,
)
```

### 4.3 学习率调度

使用 StepLR 调度器：

```python
scheduler = StepLR(
    optimizer,
    step_size=10,
    gamma=0.5,
)
```

### 4.4 训练流程

```
for epoch in range(num_epochs):
    for batch in train_loader:
        # 1. 前向传播
        outputs = model(batch)

        # 2. 计算损失
        loss = outputs['loss']

        # 3. 反向传播
        loss.backward()

        # 4. 梯度裁剪
        clip_grad_norm_(model.parameters(), max_norm=1.0)

        # 5. 更新参数
        optimizer.step()
        optimizer.zero_grad()

    # 6. 学习率调度
    scheduler.step()

    # 7. 验证
    val_metrics = evaluate(model, val_loader)
```

## 5. 评估设计

### 5.1 评估指标

- **准确率 (Accuracy)**: 正确预测的比例
- **损失 (Loss)**: 交叉熵损失

### 5.2 评估流程

```python
@torch.no_grad()
def evaluate(model, dataloader):
    model.eval()
    correct = 0
    total = 0

    for batch in dataloader:
        outputs = model(batch)
        predictions = outputs['logits'].argmax(dim=1)
        correct += (predictions == targets).sum()
        total += targets.size(0)

    return correct / total
```

## 6. 接口设计

### 6.1 模型接口

```python
class VQAModel:
    def forward(images, question_ids, image_features, targets)
    def predict(images, question_ids, image_features)
    def get_model_info()
```

### 6.2 训练器接口

```python
class VQATrainer:
    def train_epoch(dataloader)
    def evaluate(dataloader)
    def train(train_loader, val_loader, num_epochs)
    def save_model(save_dir)
    def load_model(save_dir)
```

### 6.3 数据集接口

```python
class VQADataset:
    def __len__()
    def __getitem__(idx)
```

## 7. 配置设计

### 7.1 模型配置

```python
model_config = {
    'vocab_size': 10000,
    'num_answers': 1000,
    'image_backbone': 'resnet18',
    'text_encoder_type': 'lstm',
    'fusion_type': 'concat',
    'embed_dim': 300,
    'image_feature_dim': 512,
    'text_feature_dim': 512,
    'fusion_dim': 1024,
    'hidden_dim': 512,
    'dropout': 0.1,
}
```

### 7.2 训练配置

```python
train_config = {
    'learning_rate': 1e-3,
    'weight_decay': 1e-4,
    'batch_size': 32,
    'num_epochs': 20,
}
```

## 8. 扩展性设计

### 8.1 新增骨干网络

```python
def _create_backbone(backbone: str):
    if backbone == 'resnet18':
        # ...
    elif backbone == 'efficientnet':
        # 新增 EfficientNet
        pass
```

### 8.2 新增融合策略

```python
class NewFusion(nn.Module):
    def forward(image_features, text_features):
        # 新的融合逻辑
        pass
```

### 8.3 新增编码器

```python
class NewTextEncoder(nn.Module):
    def forward(input_ids):
        # 新的编码逻辑
        pass
```

## 9. 性能优化

### 9.1 模型优化

- 使用预训练权重
- 冻结部分参数
- 使用混合精度训练

### 9.2 数据优化

- 预提取图像特征
- 数据预加载
- 多进程数据加载

### 9.3 训练优化

- 梯度累积
- 学习率预热
- 梯度裁剪

## 10. 部署考虑

### 10.1 模型导出

- TorchScript 导出
- ONNX 导出
- 模型量化

### 10.2 推理优化

- 批量推理
- 缓存图像特征
- 模型蒸馏
