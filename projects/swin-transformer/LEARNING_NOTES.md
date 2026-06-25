# 学习笔记：Swin Transformer

## 项目概述

本项目实现了 Swin Transformer，一种层级式视觉 Transformer 架构。通过实现这个项目，我深入理解了窗口注意力机制和移位窗口的工作原理。

## 核心学习点

### 1. 窗口注意力机制

**问题：** 传统全局自注意力的计算复杂度是 O(n²)，对于高分辨率图像来说计算量巨大。

**解决方案：** 窗口注意力将特征图划分为不重叠的局部窗口，在每个窗口内独立计算注意力。

**关键实现：**
```python
def window_partition(x, window_size):
    B, H, W, C = x.shape
    # 重塑为窗口格式
    x = x.view(B, H // window_size, window_size, 
                W // window_size, window_size, C)
    # 重排维度
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
    # 展平为 (B * num_windows, w, w, C)
    x = x.view(-1, window_size, window_size, C)
    return x
```

**学习收获：**
- 局部注意力显著降低计算复杂度
- 窗口划分可以通过张量操作高效实现
- 需要 `contiguous()` 确保内存布局正确

### 2. 移位窗口机制

**问题：** 单纯的窗口注意力缺乏跨窗口信息交流。

**解决方案：** 在相邻层之间移动窗口位置，使得不同层的窗口覆盖不同区域。

**关键实现：**
```python
# 循环移位
if self.shift_size > 0:
    shifted_x = torch.roll(x, 
                           shifts=(-self.shift_size, -self.shift_size), 
                           dims=(1, 2))

# 窗口划分和注意力
x_windows = window_partition(shifted_x, self.window_size)
attn_windows = self.attn(x_windows, mask=self.attn_mask)

# 逆循环移位
if self.shift_size > 0:
    x = torch.roll(shifted_x, 
                   shifts=(self.shift_size, self.shift_size), 
                   dims=(1, 2))
```

**注意力掩码：**
```python
# 计算注意力掩码，防止不同区域之间的注意力
attn_mask = mask_windows.unsqueeze(1) - mask_windows.unsqueeze(2)
attn_mask = attn_mask.masked_fill(attn_mask != 0, float(-100.0))
attn_mask = attn_mask.masked_fill(attn_mask == 0, float(0.0))
```

**学习收获：**
- 循环移位是一种巧妙的技巧，将边界区域移到一起
- 注意力掩码确保只有同一区域的 token 可以相互关注
- 交替使用常规窗口和移位窗口是标准做法

### 3. 相对位置偏置

**问题：** 如何编码 token 之间的空间关系？

**解决方案：** 使用可学习的相对位置偏置表，根据 token 之间的相对位置查询偏置值。

**关键实现：**
```python
# 偏置表：(2*Wh-1) * (2*Ww-1), num_heads
self.relative_position_bias_table = nn.Parameter(
    torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), 
                num_heads)
)

# 计算相对位置索引
relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
relative_coords[:, :, 0] += Wh - 1  # 移位到非负
relative_coords[:, :, 1] += Ww - 1
relative_coords[:, :, 0] *= 2 * Ww - 1  # 展平为 1D 索引
relative_position_index = relative_coords.sum(-1)

# 在注意力计算中添加偏置
attn = q @ k.transpose(-2, -1) * scale
relative_position_bias = self.relative_position_bias_table[
    self.relative_position_index.view(-1)
].view(N, N, -1)
attn = attn + relative_position_bias.unsqueeze(0)
```

**学习收获：**
- 相对位置偏置比绝对位置编码更灵活
- 偏置表是可学习的参数
- 索引映射是固定的（buffer，不是 parameter）

### 4. Patch Merging

**问题：** 如何在不同阶段之间下采样？

**解决方案：** 提取 2×2 的 patch 并拼接，然后通过线性层降维。

**关键实现：**
```python
def forward(self, x):
    H, W = self.input_resolution
    B, L, C = x.shape
    
    # 重塑为 2D
    x = x.view(B, H, W, C)
    
    # 提取 2×2 patch
    x0 = x[:, 0::2, 0::2, :]  # 左上
    x1 = x[:, 1::2, 0::2, :]  # 左下
    x2 = x[:, 0::2, 1::2, :]  # 右上
    x3 = x[:, 1::2, 1::2, :]  # 右下
    
    # 拼接：4*C 通道
    x = torch.cat([x0, x1, x2, x3], dim=-1)
    
    # 归一化和投影：4*C -> 2*C
    x = self.norm(x)
    x = self.reduction(x)
    
    return x
```

**学习收获：**
- Patch Merging 是一种高效的下采样方式
- 拼接保留了空间信息
- 线性投影减少维度

### 5. 层级特征提取

**问题：** 如何生成多尺度特征图？

**解决方案：** 通过多个阶段，每个阶段包含多个 Transformer 块，并在阶段之间进行下采样。

**关键实现：**
```python
# 构建阶段
self.layers = nn.ModuleList()
for i_layer in range(self.num_layers):
    # 计算维度和分辨率
    stage_dim = int(embed_dim * 2 ** i_layer)
    stage_resolution = (
        patches_resolution // (2 ** i_layer),
        patches_resolution // (2 ** i_layer),
    )
    
    # 下采样层（除了最后一个阶段）
    if i_layer < self.num_layers - 1:
        downsample = PatchMerging(
            input_resolution=stage_resolution,
            dim=stage_dim,
        )
    else:
        downsample = None
    
    # 创建阶段
    stage = SwinTransformerStage(
        dim=stage_dim,
        input_resolution=stage_resolution,
        depth=depths[i_layer],
        num_heads=num_heads[i_layer],
        window_size=window_size,
        downsample=downsample,
    )
    self.layers.append(stage)
```

**学习收获：**
- 层级特征对于密集预测任务很重要
- 每个阶段的维度和分辨率都在变化
- 下采样只在阶段之间进行

## 实现挑战

### 1. 形状管理

**挑战：** 在不同组件之间传递张量时，形状会不断变化。

**解决方案：**
- 仔细跟踪每个操作的输入输出形状
- 使用断言验证形状
- 在调试时打印中间形状

**示例：**
```python
def forward(self, x):
    B, L, C = x.shape
    H, W = self.input_resolution
    assert L == H * W, f"Input feature size ({L}) doesn't match resolution ({H}x{W})."
    # ...
```

### 2. 注意力掩码

**挑战：** 移位窗口需要正确的注意力掩码来防止跨区域注意力。

**解决方案：**
- 预计算注意力掩码
- 使用 buffer 存储（不是 parameter）
- 仔细验证掩码的正确性

**调试技巧：**
```python
# 打印掩码形状和值
print(f"Mask shape: {attn_mask.shape}")
print(f"Mask unique values: {attn_mask.unique()}")
```

### 3. 内存布局

**挑战：** 某些操作需要连续的内存布局。

**解决方案：**
- 在 permute 后调用 `.contiguous()`
- 使用 `view` 而不是 `reshape`（当可能时）
- 注意张量的 stride

### 4. 数值稳定性

**挑战：** 注意力计算可能导致数值不稳定。

**解决方案：**
- 使用 LayerNorm 稳定训练
- 适当的权重初始化
- 使用 float32 精度

## 测试策略

### 1. 单元测试

测试每个组件的正确性：
- PatchEmbedding: 输出形状、梯度流
- WindowAttention: 窗口划分、注意力计算
- ShiftedWindowTransformerBlock: 残差连接、移位机制

### 2. 集成测试

测试完整模型：
- 前向传播形状
- 反向传播梯度
- 不同配置的兼容性

### 3. 边界情况

- 小输入尺寸
- 单通道输入
- 大 batch size

## 性能优化

### 1. 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

with autocast():
    output = model(x)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 2. 梯度累积

```python
accumulation_steps = 4

for i, (x, y) in enumerate(dataloader):
    with autocast():
        output = model(x)
        loss = criterion(output, y) / accumulation_steps
    
    scaler.scale(loss).backward()
    
    if (i + 1) % accumulation_steps == 0:
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()
```

### 3. 梯度检查点

```python
from torch.utils.checkpoint import checkpoint

class SwinTransformerStage(nn.Module):
    def forward(self, x):
        for block in self.blocks:
            x = checkpoint(block, x)  # 用计算换内存
        return x
```

## 与 ViT 的对比

| 方面 | ViT | Swin Transformer |
|------|-----|------------------|
| 特征图 | 单尺度 | 多尺度（层级） |
| 注意力 | 全局 | 局部（窗口） |
| 复杂度 | O(n²) | O(n) |
| 位置编码 | 绝对 | 相对位置偏置 |
| 密集预测 | 有限 | 优秀 |
| 预训练 | 需要大数据集 | 小数据集也能工作 |

## 关键洞察

1. **局部注意力的重要性：** 全局注意力对于高分辨率图像来说计算量太大，局部注意力是一个实用的解决方案。

2. **跨窗口信息流动：** 移位窗口是一种巧妙的技巧，在保持线性复杂度的同时实现了跨窗口信息交流。

3. **层级特征的价值：** 多尺度特征图对于密集预测任务（如目标检测、语义分割）非常重要。

4. **相对位置偏置的优势：** 相比绝对位置编码，相对位置偏置更灵活，泛化能力更强。

5. **工程实现的细节：** 正确的形状管理、内存布局、注意力掩码是实现成功的关键。

## 未来学习方向

1. **Swin Transformer V2：** 改进的训练稳定性和效率
2. **下游任务：** 将 Swin Transformer 应用于目标检测、语义分割
3. **模型压缩：** 剪枝、量化、知识蒸馏
4. **高效实现：** 自定义 CUDA 内核优化窗口操作

## 参考资源

- [Swin Transformer 论文](https://arxiv.org/abs/2103.14030)
- [官方代码库](https://github.com/microsoft/Swin-Transformer)
- [timm 库](https://github.com/huggingface/pytorch-image-models)
- [PyTorch 教程](https://pytorch.org/tutorials/)

## 总结

通过实现 Swin Transformer，我深入理解了：

1. **窗口注意力机制**如何降低计算复杂度
2. **移位窗口**如何实现跨窗口信息交流
3. **层级特征提取**如何生成多尺度特征图
4. **相对位置偏置**如何编码空间关系

这些概念不仅适用于 Swin Transformer，也是理解现代视觉 Transformer 的基础。
