# 图像修复 (Image Inpainting)

从零实现基于上下文编码器的图像修复算法，深入理解生成式图像修复的核心原理。

## 学习目标

- **理解图像修复原理**：掌握编码器-解码器架构在图像修复中的应用
- **掌握上下文编码器**：理解 U-Net 跳跃连接和瓶颈层的作用
- **学会生成式修复**：掌握 GAN 训练技巧和损失函数设计

## 核心循环

```
损坏图像 → 掩码 → 编码器 → 解码器 → 修复图像
```

1. **损坏图像**：原始图像与掩码结合，掩码区域被遮挡
2. **掩码**：定义缺失区域（中心、随机矩形、不规则形状）
3. **编码器**：逐步下采样，提取图像的语义特征
4. **解码器**：逐步上采样，结合跳跃连接恢复空间细节
5. **修复图像**：输出完整的修复结果，混合已知区域和生成区域

## 项目结构

```
image-inpainting/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── requirements.txt             # 依赖清单
├── docs/
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-REQUIREMENTS.md      # 需求分析
│   ├── 03-DESIGN.md            # 技术设计
│   ├── 04-PRODUCT.md           # 产品思维
│   └── 05-DEVELOPMENT.md       # 开发手册
├── src/
│   ├── __init__.py
│   ├── context_encoder.py      # U-Net 生成器 + PatchGAN 判别器
│   ├── mask.py                 # 掩码生成工具
│   ├── losses.py               # 损失函数
│   ├── metrics.py              # 评估指标
│   └── inpainting.py           # 高级管线封装
├── tests/
│   ├── test_context_encoder.py
│   ├── test_mask.py
│   ├── test_losses.py
│   ├── test_metrics.py
│   └── test_inpainting.py
└── examples/
    ├── basic_inpainting.py      # 基础推理示例
    └── train_context_encoder.py # 训练示例
```

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装

```bash
# 进入项目目录
cd projects/image-inpainting

# 安装依赖
pip install -r requirements.txt
```

### 运行示例

```bash
# 基础推理示例
python examples/basic_inpainting.py

# 训练示例
python examples/train_context_encoder.py
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v
```

## 重点难点

### 重点1：U-Net 跳跃连接

**为什么重要**：跳跃连接是 U-Net 的核心设计，它将编码器的空间细节传递给解码器，对于图像修复的质量至关重要。

**关键代码**：`src/context_encoder.py` - `forward()` 方法

**理解要点**：
- 编码器下采样丢失空间信息
- 跳跃连接通过拼接弥补信息丢失
- 解码器可以利用编码器的细节恢复精确边界

### 重点2：重建损失 vs 对抗损失

**为什么重要**：两种损失的平衡决定了修复结果的质量。重建损失保证内容正确，对抗损失增加真实感。

**关键代码**：`src/losses.py` - `InpaintingLoss` 类

**理解要点**：
- L1 损失产生锐利结果，L2 产生平滑结果
- 对抗损失推动生成器产生更真实的结果
- 权重平衡是关键：lambda_rec=1.0, lambda_adv=0.001

### 重点3：掩码设计

**为什么重要**：掩码类型影响训练效果和应用场景。不同类型的掩码模拟不同的真实损坏模式。

**关键代码**：`src/mask.py`

**理解要点**：
- 中心掩码：最简单，用于基准评估
- 随机矩形：提供更多样化的训练数据
- 不规则掩码：模拟真实损坏场景

## 值得思考

### 1. 为什么选择 U-Net 而不是其他架构？

**背景**：图像修复需要什么样的网络架构？

**权衡**：
- U-Net：跳跃连接保留细节，但参数较多
- ResNet：参数效率高，但丢失空间信息
- Transformer：全局注意力好，但计算量大

**结论**：U-Net 的跳跃连接对图像修复至关重要，因为它需要精确恢复空间细节。

### 2. L1 vs L2 损失哪个更好？

**背景**：像素级损失应该用哪种？

**优点**：
- L1：产生锐利结果，对异常值鲁棒
- L2：产生平滑结果，数学性质好

**缺点**：
- L1：梯度不连续
- L2：产生模糊结果

**适用场景**：图像修复通常选择 L1，因为需要锐利的结果。

### 3. PatchGAN 为什么比 Global GAN 好？

**背景**：判别器应该关注局部还是全局？

**优点**：
- PatchGAN：关注纹理质量，参数少，可处理任意大小图像
- Global GAN：关注全局结构，但参数多

**缺点**：
- PatchGAN：可能忽略全局一致性
- Global GAN：可能忽略局部细节

**适用场景**：图像修复选择 PatchGAN，因为纹理质量更重要。

## 相关资源

- [Context Encoders: Feature Learning by Inpainting (CVPR 2016)](https://arxiv.org/abs/1604.07379)
- [U-Net: Convolutional Networks for Biomedical Image Segmentation (2015)](https://arxiv.org/abs/1505.04597)
- [Image-to-Image Translation with Conditional Adversarial Networks (2016)](https://arxiv.org/abs/1611.07004)
- [PyTorch 官方文档](https://pytorch.org/docs/stable/)

## 学习路径

建议学习顺序：

1. 阅读 [01-RESEARCH.md](docs/01-RESEARCH.md) 了解技术背景和发展
2. 阅读 [02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) 理解需求和边界
3. 阅读 [03-DESIGN.md](docs/03-DESIGN.md) 学习架构设计
4. 阅读 [04-PRODUCT.md](docs/04-PRODUCT.md) 理解产品思维
5. 阅读 [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) 开始开发
6. 运行 [examples/basic_inpainting.py](examples/basic_inpainting.py) 查看效果
7. 运行 [examples/train_context_encoder.py](examples/train_context_encoder.py) 理解训练
8. 阅读源代码，重点关注 ⭐ 标记的部分
9. 完成 [LEARNING_NOTES.md](LEARNING_NOTES.md) 中的练习
