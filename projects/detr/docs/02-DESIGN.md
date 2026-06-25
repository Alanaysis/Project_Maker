# DETR 目标检测 - 设计文档

## 1. 系统架构

### 1.1 模块划分

```
detr/
├── src/
│   ├── __init__.py          # 模块初始化
│   ├── backbone.py          # CNN骨干网络
│   ├── transformer.py       # Transformer编码器-解码器
│   ├── matcher.py           # 匈牙利匹配
│   ├── loss.py              # 损失函数
│   ├── detr.py              # DETR主模型
│   ├── dataset.py           # 数据集
│   └── utils.py             # 工具函数
├── tests/                   # 测试文件
├── examples/                # 示例代码
└── docs/                    # 文档
```

### 1.2 数据流

```
输入图像 (B, 3, H, W)
    ↓
Backbone (ResNet)
    ↓
特征图 (B, C, H/32, W/32)
    ↓
Position Encoding
    ↓
Transformer Encoder
    ↓
Transformer Decoder + Object Queries
    ↓
预测头
    ├── 分类 (B, N, num_classes+1)
    └── 边界框 (B, N, 4)
    ↓
匈牙利匹配 + 损失计算
```

## 2. 核心类设计

### 2.1 Backbone

```python
class Backbone(nn.Module):
    """CNN骨干网络"""
    def __init__(self, model_name='resnet18', train_backbone=True):
        # 初始化ResNet
        # 移除最后的全连接层

    def forward(self, tensor_list: NestedTensor):
        # 提取特征
        # 返回特征图和掩码
```

### 2.2 Transformer

```python
class Transformer(nn.Module):
    """Transformer编码器-解码器"""
    def __init__(self, d_model=256, nhead=8, num_encoder_layers=6, 
                 num_decoder_layers=6, dim_feedforward=2048):
        # 初始化编码器和解码器

    def forward(self, src, mask, query_embed, pos_embed):
        # 编码器前向传播
        # 解码器前向传播
        # 返回预测结果
```

### 2.3 HungarianMatcher

```python
class HungarianMatcher(nn.Module):
    """匈牙利匹配器"""
    def __init__(self, cost_class=1, cost_bbox=1, cost_giou=1):
        # 初始化匹配代价权重

    def forward(self, outputs, targets):
        # 计算代价矩阵
        # 执行匈牙利算法
        # 返回匹配索引
```

### 2.4 SetCriterion

```python
class SetCriterion(nn.Module):
    """集合预测损失"""
    def __init__(self, num_classes, matcher, weight_dict, eos_coef, losses):
        # 初始化损失函数
        # 注册"无对象"类别权重

    def forward(self, outputs, targets):
        # 执行匈牙利匹配
        # 计算各项损失
        # 返回损失字典
```

### 2.5 DETR

```python
class DETR(nn.Module):
    """DETR主模型"""
    def __init__(self, backbone, transformer, num_classes, num_queries, aux_loss):
        # 初始化各组件
        # 创建Object Queries
        # 创建预测头

    def forward(self, samples):
        # 特征提取
        # Transformer前向传播
        # 预测类别和边界框
        # 返回结果
```

## 3. 关键算法设计

### 3.1 位置编码

使用正弦位置编码：

```python
PE(pos, 2i) = sin(pos / 10000^(2i/d))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d))
```

### 3.2 匈牙利匹配

1. 计算代价矩阵 C (N × M)
2. 使用 `linear_sum_assignment` 求解
3. 返回匹配的索引对

### 3.3 Focal Loss

```python
FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)
```

- α = 0.25（正样本权重）
- γ = 2（聚焦参数）

## 4. 接口设计

### 4.1 模型输入

```python
# 图像输入
images: torch.Tensor  # (B, 3, H, W)

# 嵌套张量输入（支持不同尺寸）
NestedTensor:
    tensors: torch.Tensor  # (B, 3, H_max, W_max)
    mask: torch.Tensor     # (B, H_max, W_max)
```

### 4.2 模型输出

```python
{
    'pred_logits': torch.Tensor,  # (B, N, num_classes+1)
    'pred_boxes': torch.Tensor,   # (B, N, 4) [cx, cy, w, h]
    'aux_outputs': [              # 辅助输出（可选）
        {
            'pred_logits': torch.Tensor,
            'pred_boxes': torch.Tensor
        }
    ]
}
```

### 4.3 目标格式

```python
targets = [
    {
        'labels': torch.Tensor,  # (M,) 类别标签
        'boxes': torch.Tensor    # (M, 4) 边界框 [cx, cy, w, h]
    }
]
```

## 5. 配置参数

### 5.1 模型配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| num_classes | 91 | 类别数量 |
| num_queries | 100 | 查询数量 |
| hidden_dim | 256 | Transformer隐藏维度 |
| nhead | 8 | 注意力头数 |
| num_encoder_layers | 6 | 编码器层数 |
| num_decoder_layers | 6 | 解码器层数 |
| dropout | 0.1 | Dropout概率 |

### 5.2 损失配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| cost_class | 1 | 分类代价权重 |
| cost_bbox | 5 | 边界框L1代价权重 |
| cost_giou | 2 | GIoU代价权重 |
| eos_coef | 0.1 | "无对象"类别权重 |

## 6. 性能优化

### 6.1 内存优化
- 使用梯度检查点
- 混合精度训练
- 批量大小调整

### 6.2 计算优化
- 编译优化（torch.compile）
- 批量推理
- 模型量化

## 7. 扩展性设计

### 7.1 支持不同的骨干网络
- ResNet-18/50/101
- Swin Transformer
- ConvNeXt

### 7.2 支持不同的检测任务
- 目标检测
- 实例分割
- 全景分割

### 7.3 支持不同的匹配策略
- 匈牙利匹配
- 最优传输
- 二部图匹配
