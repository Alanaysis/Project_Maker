# 开发手册 - 图像修复

## 1. 环境搭建

### 系统要求

- 操作系统：Windows/macOS/Linux
- Python 版本：3.8+
- 其他：pip

### 安装步骤

```bash
# 1. 进入项目目录
cd projects/image-inpainting

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "from src import UNetGenerator; print('安装成功')"
```

## 2. 项目结构

```
image-inpainting/
├── README.md                    # 项目总览
├── LEARNING_NOTES.md            # 学习笔记模板
├── requirements.txt             # 依赖清单
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-REQUIREMENTS.md      # 需求分析
│   ├── 03-DESIGN.md            # 技术设计
│   ├── 04-PRODUCT.md           # 产品思维
│   └── 05-DEVELOPMENT.md       # 开发手册（本文件）
├── src/                         # 源代码
│   ├── __init__.py
│   ├── context_encoder.py      # U-Net 生成器 + PatchGAN 判别器
│   ├── mask.py                 # 掩码生成工具
│   ├── losses.py               # 损失函数
│   ├── metrics.py              # 评估指标
│   └── inpainting.py           # 高级管线封装
├── tests/                       # 测试
│   ├── __init__.py
│   ├── test_context_encoder.py
│   ├── test_mask.py
│   ├── test_losses.py
│   ├── test_metrics.py
│   └── test_inpainting.py
└── examples/                    # 使用示例
    ├── basic_inpainting.py      # 基础推理示例
    └── train_context_encoder.py # 训练示例
```

## 3. 核心模块解析

### 模块1：U-Net 生成器 (`context_encoder.py`)

**文件位置**：`src/context_encoder.py`

**职责**：将损坏的图像修复为完整的图像

**核心代码**：

```python
# ⭐ 重点代码 - U-Net 前向传播
def forward(self, x: torch.Tensor) -> torch.Tensor:
    # Encoder path (save for skip connections)
    e1 = self.encoder1(x)
    e2 = self.encoder2(e1)
    e3 = self.encoder3(e2)
    e4 = self.encoder4(e3)
    e5 = self.encoder5(e4)
    e6 = self.encoder6(e5)
    e7 = self.encoder7(e6)

    # Bottleneck
    bottleneck = self.bottleneck(e7)

    # Decoder with skip connections
    d1 = self.decoder1(bottleneck)
    d2 = self.decoder2(torch.cat([d1, e6], dim=1))
    d3 = self.decoder3(torch.cat([d2, e5], dim=1))
    d4 = self.decoder4(torch.cat([d3, e4], dim=1))
    d5 = self.decoder5(torch.cat([d4, e3], dim=1))
    d6 = self.decoder6(torch.cat([d5, e2], dim=1))

    return self.output_layer(torch.cat([d6, e1], dim=1))
```

**理解要点**：
- 跳跃连接通过 `torch.cat` 将编码器特征传递给解码器
- 编码器逐步下采样（128→64→32→16→8→4→2→1）
- 解码器逐步上采样，结合编码器的细节信息
- Tanh 激活函数将输出限制在 [-1, 1] 范围

### 模块2：掩码生成 (`mask.py`)

**文件位置**：`src/mask.py`

**职责**：生成不同类型的掩码用于训练和评估

**核心代码**：

```python
# ⭐ 重点代码 - 不规则掩码生成
def generate_irregular_mask(image_size, num_strokes=10, ...):
    for _ in range(num_strokes):
        # 随机生成控制点
        vertices_x = [start_x]
        vertices_y = [start_y]
        for _ in range(num_vertices - 1):
            dx = np.random.randint(-30, 31)
            dy = np.random.randint(-30, 31)
            # ...

        # 用线段连接控制点
        for i in range(len(vertices_x) - 1):
            _draw_line(mask, vertices_x[i], vertices_y[i], ...)
```

**理解要点**：
- 中心掩码：最简单，用于基准评估
- 随机矩形：提供更多样化的训练数据
- 不规则掩码：模拟真实损坏场景

### 模块3：损失函数 (`losses.py`)

**文件位置**：`src/losses.py`

**职责**：计算训练损失，指导模型优化

**核心代码**：

```python
# ⭐ 重点代码 - 组合损失
class InpaintingLoss:
    def generator_loss(self, predicted, target, mask, fake_pred):
        rec = self.rec_loss(predicted, target, mask)  # 重建损失
        adv = self.adv_loss.generator_loss(fake_pred)  # 对抗损失
        total = self.lambda_rec * rec + self.lambda_adv * adv
        return total, rec, adv
```

**理解要点**：
- L1 损失：像素级差异，产生锐利结果
- 对抗损失：判别器提供感知反馈
- 权重平衡：lambda_rec=1.0, lambda_adv=0.001

## 4. 重点难点攻克

### 难点1：GAN 训练不稳定

**问题描述**：GAN 训练容易出现模式崩溃或不收敛

**解决方案**：
1. 使用 Hinge 损失（比原始 GAN 损失更稳定）
2. 判别器使用光谱归一化（本项目未实现，可扩展）
3. 学习率使用 Adam，beta1=0.5
4. 先训练判别器，再训练生成器

**关键代码**：
```python
# 训练判别器
d_loss = criterion.discriminator_loss(real_pred, fake_pred)
d_loss.backward()
optimizer_d.step()

# 训练生成器（需要重新前向传播）
fake_images = generator(input)
g_loss = criterion.generator_loss(...)
g_loss.backward()
optimizer_g.step()
```

### 难点2：重建质量 vs 真实感的平衡

**问题描述**：重建损失产生模糊结果，对抗损失产生伪影

**解决方案**：
1. 使用 L1 而不是 L2 损失（更锐利）
2. 对抗损失权重设为 0.001（远小于重建损失）
3. 只在掩码区域计算重建损失

**关键代码**：
```python
# 只在掩码区域计算损失
if mask is not None:
    loss = loss * mask_expanded
    return loss.sum() / mask_expanded.sum()
```

### 难点3：跳跃连接的信息传递

**问题描述**：如何有效传递编码器的空间信息到解码器

**解决方案**：
1. 使用 `torch.cat` 拼接（而不是相加）
2. 拼接后通过卷积层融合信息
3. 保持编码器和解码器的对称结构

**关键代码**：
```python
# 跳跃连接：拼接编码器和解码器特征
d2 = self.decoder2(torch.cat([d1, e6], dim=1))
```

## 5. 调试技巧

### 常用调试方法

1. **检查输入输出形状**
   ```python
   print(f"Input shape: {x.shape}")
   output = model(x)
   print(f"Output shape: {output.shape}")
   ```

2. **检查梯度**
   ```python
   for name, param in model.named_parameters():
       if param.grad is not None:
           print(f"{name}: grad norm = {param.grad.norm():.4f}")
   ```

3. **可视化掩码效果**
   ```python
   import matplotlib.pyplot as plt
   plt.imshow(mask[0], cmap='gray')
   plt.title("Mask")
   plt.show()
   ```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 生成器输出全黑 | Tanh 激活 + 不当初始化 | 检查权重初始化 |
| 训练 loss 不下降 | 学习率过高/过低 | 调整学习率 |
| 结果模糊 | 重建损失权重过大 | 增加对抗损失权重 |
| 有伪影 | 对抗损失权重过大 | 减少对抗损失权重 |
| CUDA 内存不足 | 图像太大 | 减小 batch size 或图像尺寸 |

## 6. 性能优化

### 已优化的部分

1. **卷积层使用 bias=False**：配合 BatchNorm，减少参数
2. **LeakyReLU slope=0.2**：标准 GAN 设置，防止梯度消失
3. **Adam optimizer beta1=0.5**：GAN 训练的标准设置

### 可优化的方向

1. **光谱归一化**：添加到判别器，提高训练稳定性
2. **渐进式训练**：从小分辨率开始，逐步增加
3. **混合精度训练**：使用 float16 加速训练
4. **梯度惩罚**：替代或补充光谱归一化

## 7. 扩展指南

### 如何添加门控卷积

1. 在 `context_encoder.py` 中定义 `GatedConv2d` 类
2. 替换 `EncoderBlock` 和 `DecoderBlock` 中的 `nn.Conv2d`
3. 训练时掩码需要作为额外输入

### 如何添加注意力机制

1. 定义自注意力模块（参考 SAGAN）
2. 在 U-Net 瓶颈层添加
3. 可选：在解码器添加上下文注意力

### 代码规范

- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 保持函数简短
- 使用 ⭐ 标记重点代码
