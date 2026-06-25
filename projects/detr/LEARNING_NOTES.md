# DETR 目标检测 - 学习笔记

## 1. 学习目标回顾

### 1.1 原始学习目标

- 理解 DETR 架构
- 掌握匈牙利匹配
- 学会集合预测

### 1.2 实际收获

通过实现 DETR，我深入理解了：

1. **Transformer 在视觉任务中的应用**
2. **端到端目标检测的优势**
3. **匈牙利匹配的数学原理和实现**
4. **集合预测损失的设计思想**

## 2. 核心概念理解

### 2.1 DETR 架构

#### 传统目标检测 vs DETR

| 特性 | 传统方法 | DETR |
|------|----------|------|
| 锚框 | 需要 | 不需要 |
| NMS | 需要 | 不需要 |
| 训练方式 | 多阶段 | 端到端 |
| 全局信息 | 有限 | 充分 |

#### DETR 的创新点

1. **端到端训练**：移除了手工设计的组件
2. **集合预测**：直接预测一组检测结果
3. **二分图匹配**：使用匈牙利算法匹配预测与真实标签
4. **注意力机制**：捕获全局依赖关系

### 2.2 匈牙利匹配

#### 问题定义

给定 N 个预测和 M 个真实标签（N > M），找到最优的一对一匹配。

#### 匹配代价

```
C(i,j) = λ_cls · L_cls(i,j) + λ_bbox · L_bbox(i,j) + λ_giou · L_giou(i,j)
```

- **分类代价**：负对数似然
- **边界框代价**：L1 距离
- **GIoU 代价**：广义 IoU 损失

#### 匈牙利算法

使用 `scipy.optimize.linear_sum_assignment` 求解最优匹配。

### 2.3 集合预测损失

#### 损失组成

```
L = λ_cls · L_cls + λ_bbox · L_bbox + λ_giou · L_giou
```

#### 关键设计

1. **Focal Loss**：处理类别不平衡
2. **无对象类别**：处理背景
3. **辅助损失**：解码器中间层

## 3. 实现细节

### 3.1 骨干网络

```python
class Backbone(nn.Module):
    def __init__(self, model_name='resnet18', train_backbone=True):
        # 加载预训练ResNet
        # 移除最后两层
        # 冻结参数（可选）
```

**关键点**：
- 使用 torchvision 预训练模型
- 移除最后的全连接层和平均池化层
- 支持冻结骨干网络参数

### 3.2 Transformer

```python
class Transformer(nn.Module):
    def forward(self, src, mask, query_embed, pos_embed):
        # 重塑输入：(B, C, H, W) -> (H*W, B, C)
        # 编码器处理
        # 解码器处理
        # 返回预测结果
```

**关键点**：
- 位置编码保留空间信息
- Object Queries 是可学习的参数
- 并行解码所有对象

### 3.3 匈牙利匹配实现

```python
class HungarianMatcher(nn.Module):
    def forward(self, outputs, targets):
        # 计算代价矩阵
        cost_class = -out_prob[:, tgt_ids]
        cost_bbox = torch.cdist(out_bbox, tgt_bbox, p=1)
        cost_giou = -generalized_box_iou(...)
        
        # 匈牙利算法
        indices = linear_sum_assignment(C)
```

**关键点**：
- 使用负概率作为分类代价
- 使用 L1 距离作为边界框代价
- 使用 GIoU 作为重叠度量

### 3.4 损失函数

```python
class SetCriterion(nn.Module):
    def forward(self, outputs, targets):
        # 匈牙利匹配
        indices = self.matcher(outputs_without_aux, targets)
        
        # 计算各项损失
        losses = {}
        for loss in self.losses:
            losses.update(self.get_loss(loss, outputs, targets, indices, num_boxes))
        
        return losses
```

**关键点**：
- 使用 Focal Loss 处理类别不平衡
- 使用 L1 + GIoU 作为边界框损失
- 支持辅助损失

## 4. 遇到的问题和解决方案

### 4.1 问题 1：损失不收敛

**现象**：训练损失不下降

**原因**：
- 学习率设置不当
- 匹配质量差
- 数据格式错误

**解决方案**：
- 调整学习率（1e-4）
- 检查匹配结果
- 验证数据格式

### 4.2 问题 2：内存不足

**现象**：`CUDA out of memory`

**原因**：
- 批量大小过大
- 查询数量过多
- 模型过大

**解决方案**：
- 减小批量大小
- 减少查询数量
- 使用梯度检查点

### 4.3 问题 3：检测效果差

**现象**：模型检测效果不理想

**原因**：
- 训练轮数不足
- 数据增强不足
- 模型容量不足

**解决方案**：
- 增加训练轮数
- 增加数据增强
- 使用更强的骨干网络

## 5. 关键代码片段

### 5.1 位置编码

```python
class PositionEmbeddingSine(nn.Module):
    def forward(self, tensor_list):
        # 计算正弦位置编码
        dim_t = torch.arange(self.num_pos_feats, dtype=torch.float32)
        dim_t = self.temperature ** (2 * (dim_t // 2) / self.num_pos_feats)
        
        pos_x = x_embed[:, :, :, None] / dim_t
        pos_y = y_embed[:, :, :, None] / dim_t
        
        pos_x = torch.stack((pos_x[..., 0::2].sin(), pos_x[..., 1::2].cos()), dim=4)
        pos_y = torch.stack((pos_y[..., 0::2].sin(), pos_y[..., 1::2].cos()), dim=4)
        
        return pos
```

### 5.2 Object Queries

```python
class DETR(nn.Module):
    def __init__(self, ...):
        # 可学习的查询嵌入
        self.query_embed = nn.Embedding(num_queries, hidden_dim)
        
        # 输入投影
        self.input_proj = nn.Conv2d(backbone.num_channels[0], hidden_dim, kernel_size=1)
```

### 5.3 边界框预测

```python
# 边界框头
self.bbox_embed = MLP(hidden_dim, hidden_dim, 4, 3)

# 预测边界框（归一化坐标）
outputs_coord = self.bbox_embed(hs).sigmoid()
```

## 6. 性能优化

### 6.1 内存优化

1. **梯度检查点**：减少内存使用
2. **混合精度训练**：使用 FP16
3. **批量大小调整**：根据 GPU 内存调整

### 6.2 计算优化

1. **模型编译**：使用 torch.compile
2. **批量推理**：并行处理多张图像
3. **模型量化**：减少模型大小

## 7. 扩展思考

### 7.1 DETR 变体

1. **Deformable DETR**：使用可变形注意力，收敛更快
2. **DAB-DETR**：动态锚框，提高检测精度
3. **DN-DETR**：去噪训练，加速收敛
4. **RT-DETR**：实时检测，提高推理速度

### 7.2 应用场景

1. **目标检测**：通用目标检测
2. **实例分割**：检测 + 分割
3. **全景分割**：场景理解
4. **视频检测**：时序信息利用

### 7.3 未来方向

1. **更高效的注意力机制**
2. **更强的骨干网络**
3. **更好的训练策略**
4. **更广泛的应用**

## 8. 学习资源

### 8.1 论文

- [End-to-End Object Detection with Transformers](https://arxiv.org/abs/2005.12872)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [Deformable DETR](https://arxiv.org/abs/2010.04159)

### 8.2 代码

- [官方实现](https://github.com/facebookresearch/detr)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/model_doc/detr)

### 8.3 教程

- [PyTorch DETR Tutorial](https://pytorch.org/tutorials/intermediate/detr_tutorial.html)
- [DETR 详解](https://arxiv.org/abs/2005.12872)

## 9. 总结

### 9.1 主要收获

1. **理解了 DETR 的核心思想**
   - 端到端训练
   - 集合预测
   - 二分图匹配

2. **掌握了关键实现**
   - Transformer 编码器-解码器
   - 匈牙利匹配算法
   - 集合预测损失

3. **学会了调试技巧**
   - 损失监控
   - 匹配可视化
   - 性能分析

### 9.2 下一步计划

1. **尝试 DETR 变体**：Deformable DETR、DAB-DETR
2. **应用到实际数据集**：COCO、Pascal VOC
3. **优化模型性能**：量化、剪枝、蒸馏
4. **探索更多应用**：实例分割、全景分割

## 10. 代码示例

### 10.1 完整训练流程

```python
from src.detr import build_detr
from src.loss import SetCriterion
from src.matcher import build_matcher
from src.dataset import create_simple_dataset, collate_fn

# 创建模型
model = build_detr(num_classes=5, num_queries=100)

# 创建损失函数
matcher = build_matcher()
criterion = SetCriterion(5, matcher, weight_dict, eos_coef=0.1, losses=['labels', 'boxes'])

# 创建数据集
dataset = create_simple_dataset(num_samples=1000)
dataloader = DataLoader(dataset, batch_size=4, collate_fn=collate_fn)

# 训练循环
for epoch in range(10):
    for images, targets in dataloader:
        outputs = model(images)
        losses = criterion(outputs, targets)
        loss = sum(losses.values())
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

### 10.2 推理示例

```python
from src.detr import build_detr
from src.matcher import box_cxcywh_to_xyxy

# 加载模型
model = build_detr(num_classes=5, num_queries=100)
model.load_state_dict(torch.load('detr_model.pth'))

# 推理
model.eval()
with torch.no_grad():
    outputs = model(images)
    
    # 后处理
    prob = outputs['pred_logits'].softmax(-1)
    scores, labels = prob[..., :-1].max(-1)
    boxes = box_cxcywh_to_xyxy(outputs['pred_boxes'])
    
    # 过滤低置信度预测
    mask = scores > 0.5
    final_scores = scores[mask]
    final_labels = labels[mask]
    final_boxes = boxes[mask]
```

## 11. 常见问题

### Q1: DETR 为什么不需要锚框？

**A1**: DETR 使用可学习的 Object Queries，每个查询负责检测一个对象。通过注意力机制，查询可以关注图像中的任意位置，无需预定义锚框。

### Q2: 匈牙利匹配的作用是什么？

**A2**: 匈牙利匹配用于将预测结果与真实标签进行最优匹配。这样可以确保每个预测只与一个真实标签对应，避免重复检测。

### Q3: 为什么使用 Focal Loss？

**A3**: Focal Loss 用于处理类别不平衡问题。在目标检测中，背景区域远多于目标区域，Focal Loss 可以降低易分类样本的权重，关注难分类样本。

### Q4: DETR 的缺点是什么？

**A4**: DETR 的主要缺点：
1. 训练收敛慢（需要 500 个 epoch）
2. 小目标检测效果差
3. 计算成本高

### Q5: 如何改进 DETR？

**A5**: 改进方向：
1. 使用更强的骨干网络
2. 使用可变形注意力
3. 使用去噪训练
4. 使用更好的训练策略
