# DETR 目标检测 - 实现文档

## 1. 实现概述

### 1.1 核心实现

本项目实现了 DETR（Detection Transformer）的核心组件：

1. **CNN 骨干网络**：使用 ResNet 提取图像特征
2. **Transformer**：编码器-解码器架构
3. **匈牙利匹配**：预测与真实标签的最优匹配
4. **集合预测损失**：端到端训练损失

### 1.2 技术栈

- **Python 3.8+**
- **PyTorch 1.10+**
- **torchvision**：预训练模型
- **scipy**：匈牙利算法
- **numpy**：数值计算

## 2. 模块实现

### 2.1 骨干网络 (backbone.py)

#### 2.1.1 Backbone 类

```python
class Backbone(BackboneBase):
    def __init__(self, model_name='resnet18', train_backbone=True):
        # 加载预训练ResNet
        # 移除最后两层（全连接和平均池化）
        # 冻结参数（可选）
```

**关键实现细节：**
- 使用 `torchvision.models` 加载预训练模型
- 移除最后的全连接层和平均池化层
- 支持冻结骨干网络参数

#### 2.1.2 FrozenBatchNorm2d

```python
class FrozenBatchNorm2d(nn.Module):
    def forward(self, x):
        # 使用固定的均值和方差
        # 避免训练时的统计波动
```

#### 2.1.3 位置编码

```python
class PositionEmbeddingSine(nn.Module):
    def forward(self, tensor_list):
        # 计算正弦位置编码
        # 支持归一化坐标
```

### 2.2 Transformer (transformer.py)

#### 2.2.1 编码器层

```python
class TransformerEncoderLayer(nn.Module):
    def forward(self, src, src_mask=None, src_key_padding_mask=None, pos=None):
        # 自注意力
        # 前馈网络
        # 残差连接和层归一化
```

#### 2.2.2 解码器层

```python
class TransformerDecoderLayer(nn.Module):
    def forward(self, tgt, memory, tgt_mask=None, memory_mask=None, ...):
        # 自注意力
        # 交叉注意力（关注编码器输出）
        # 前馈网络
```

#### 2.2.3 Transformer 主类

```python
class Transformer(nn.Module):
    def forward(self, src, mask, query_embed, pos_embed):
        # 重塑输入：(B, C, H, W) -> (H*W, B, C)
        # 编码器处理
        # 解码器处理
        # 返回预测结果
```

### 2.3 匈牙利匹配 (matcher.py)

#### 2.3.1 匹配代价计算

```python
# 分类代价
cost_class = -out_prob[:, tgt_ids]

# 边界框L1代价
cost_bbox = torch.cdist(out_bbox, tgt_bbox, p=1)

# GIoU代价
cost_giou = -generalized_box_iou(...)
```

#### 2.3.2 匈牙利算法

```python
from scipy.optimize import linear_sum_assignment

indices = [linear_sum_assignment(c[i]) for i, c in enumerate(C.split(sizes, -1))]
```

### 2.4 损失函数 (loss.py)

#### 2.4.1 分类损失

```python
def loss_labels(self, outputs, targets, indices, num_boxes):
    # 获取匹配的预测和目标
    # 计算交叉熵损失
    # 使用"无对象"类别权重
```

#### 2.4.2 边界框损失

```python
def loss_boxes(self, outputs, targets, indices, num_boxes):
    # L1损失
    loss_bbox = F.l1_loss(src_boxes, target_boxes)
    
    # GIoU损失
    loss_giou = 1 - generalized_box_iou(...)
```

#### 2.4.3 Focal Loss

```python
def sigmoid_focal_loss(inputs, targets, num_boxes, alpha=0.25, gamma=2):
    # 计算sigmoid交叉熵
    # 应用聚焦因子 (1 - p_t)^gamma
    # 应用类别权重 alpha
```

### 2.5 DETR 主模型 (detr.py)

```python
class DETR(nn.Module):
    def forward(self, samples):
        # 特征提取
        features, pos = self.backbone(samples)
        
        # Transformer处理
        hs = self.transformer(self.input_proj(src), mask, 
                             self.query_embed.weight, pos[-1])[0]
        
        # 预测
        outputs_class = self.class_embed(hs)
        outputs_coord = self.bbox_embed(hs).sigmoid()
        
        return {
            'pred_logits': outputs_class[-1],
            'pred_boxes': outputs_coord[-1]
        }
```

## 3. 数据处理

### 3.1 数据集 (dataset.py)

#### 3.1.1 简单检测数据集

```python
class SimpleDetectionDataset(data.Dataset):
    def __getitem__(self, idx):
        return {
            'image': image,      # (3, H, W)
            'boxes': boxes,      # (N, 4) [cx, cy, w, h]
            'labels': labels     # (N,)
        }
```

#### 3.1.2 批处理函数

```python
def collate_fn(batch):
    images = torch.stack([item['image'] for item in batch])
    targets = [{'boxes': item['boxes'], 'labels': item['labels']} for item in batch]
    return images, targets
```

### 3.2 数据增强

支持的数据增强：
- 随机裁剪
- 随机翻转
- 颜色抖动
- 归一化

## 4. 训练流程

### 4.1 训练循环

```python
for epoch in range(num_epochs):
    for images, targets in data_loader:
        # 前向传播
        outputs = model(images)
        
        # 计算损失
        losses = criterion(outputs, targets)
        total_loss = sum(losses.values())
        
        # 反向传播
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()
```

### 4.2 优化器配置

```python
# 参数分组
param_dicts = [
    {"params": [p for n, p in model.named_parameters() if "backbone" not in n]},
    {"params": [p for n, p in model.named_parameters() if "backbone" in n], 
     "lr": lr * 0.1},
]

optimizer = optim.AdamW(param_dicts, lr=1e-4, weight_decay=1e-4)
```

### 4.3 学习率调度

```python
lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=200, gamma=0.1)
```

## 5. 推理流程

### 5.1 后处理

```python
def post_process(outputs, target_sizes):
    # softmax获取类别概率
    prob = F.softmax(out_logits, -1)
    scores, labels = prob[..., :-1].max(-1)
    
    # 边界框格式转换
    boxes = box_cxcywh_to_xyxy(out_bbox)
    
    # 缩放到目标尺寸
    boxes = boxes * scale_fct
```

### 5.2 结果过滤

```python
def filter_predictions(results, threshold=0.5):
    mask = scores > threshold
    return {
        'scores': scores[mask],
        'labels': labels[mask],
        'boxes': boxes[mask]
    }
```

## 6. 测试策略

### 6.1 单元测试

- **骨干网络测试**：验证输出形状、参数可训练性
- **Transformer测试**：验证编码器-解码器功能
- **匹配器测试**：验证匹配正确性
- **损失函数测试**：验证梯度流动
- **数据集测试**：验证数据格式

### 6.2 集成测试

- **模型前向传播**：验证完整流程
- **损失计算**：验证损失值合理
- **训练循环**：验证损失下降

## 7. 性能优化

### 7.1 内存优化
- 梯度检查点
- 混合精度训练
- 批量大小调整

### 7.2 计算优化
- 模型编译（torch.compile）
- 批量推理
- 模型量化

## 8. 调试技巧

### 8.1 常见问题

1. **损失不收敛**
   - 检查学习率
   - 检查匹配质量
   - 检查数据格式

2. **内存溢出**
   - 减小批量大小
   - 使用梯度检查点
   - 减少查询数量

3. **检测效果差**
   - 增加训练轮数
   - 调整损失权重
   - 增加数据增强

### 8.2 调试工具

```python
# 打印匹配结果
indices = matcher(outputs, targets)
print(f"Matched {len(indices[0][0])} predictions")

# 打印损失值
losses = criterion(outputs, targets)
for k, v in losses.items():
    print(f"{k}: {v.item():.4f}")
```
