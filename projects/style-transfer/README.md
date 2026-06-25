# 神经风格迁移 (Neural Style Transfer)

实现基于 PyTorch 的神经风格迁移算法，将照片转换为艺术风格。

## 学习目标

- **理解风格迁移原理**：掌握如何使用 CNN 分离图像的内容和风格
- **掌握内容损失和风格损失**：理解两种损失函数的设计原理和实现方式
- **学会 Gram 矩阵计算**：理解 Gram 矩阵如何捕捉图像的纹理和风格信息

## 核心循环

```
内容图像 + 风格图像 → 特征提取 → 损失计算 → 图像优化 → 迁移结果
```

1. **特征提取**：使用预训练 VGG19 网络提取图像特征
2. **损失计算**：计算内容损失和风格损失
3. **图像优化**：通过梯度下降优化生成图像
4. **迁移结果**：得到融合内容和风格的生成图像

## 项目结构

```
style-transfer/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── gram_matrix.py           # Gram 矩阵计算
│   ├── losses.py                # 损失函数
│   ├── style_transfer.py        # 风格迁移核心
│   └── utils.py                 # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_gram_matrix.py      # Gram 矩阵测试
│   ├── test_losses.py           # 损失函数测试
│   └── test_style_transfer.py   # 风格迁移测试
└── examples/
    ├── basic_transfer.py        # 基本示例
    ├── advanced_transfer.py     # 高级示例
    └── gram_matrix_demo.py      # Gram 矩阵演示
```

## 快速开始

### 安装依赖

```bash
pip install torch torchvision numpy Pillow matplotlib pytest
```

### 基本使用

```python
import torch
from src import StyleTransfer, load_image, save_image

# 加载图像
content = load_image("content.jpg", size=512)
style = load_image("style.jpg", size=512)

# 创建风格迁移器
transfer = StyleTransfer(
    content_layers=["conv4_2"],
    style_layers=["conv1_1", "conv2_1", "conv3_1", "conv4_1", "conv5_1"],
    content_weight=1.0,
    style_weight=1e6,
)

# 执行风格迁移
output = transfer.transfer(
    content_image=content,
    style_image=style,
    num_steps=300,
)

# 保存结果
save_image(output, "output.jpg")
```

### 使用回调函数监控进度

```python
def print_progress(step, loss_dict):
    if step % 50 == 0:
        print(f"Step {step}: total_loss={loss_dict['total_loss']:.4f}")

output = transfer.transfer(
    content_image=content,
    style_image=style,
    num_steps=300,
    callback=print_progress,
)
```

## 核心概念

### Gram 矩阵

Gram 矩阵用于捕捉图像的风格信息。它计算不同特征通道之间的相关性：

```python
from src import gram_matrix

# 输入：特征图，shape 为 (batch_size, channels, height, width)
features = torch.randn(1, 64, 32, 32)

# 计算 Gram 矩阵
gram = gram_matrix(features, normalize=True)
# 输出：shape 为 (batch_size, channels, channels)
```

### 内容损失

内容损失衡量生成图像与内容图像在高层特征上的差异：

```python
from src import ContentLoss

content_loss = ContentLoss(weight=1.0)
content_loss.set_target(content_features)  # 设置内容图像的特征
content_loss(generated_features)  # 计算损失
loss = content_loss.get_loss()
```

### 风格损失

风格损失衡量生成图像与风格图像在纹理特征上的差异：

```python
from src import StyleLoss

style_loss = StyleLoss(weight=1e6)
style_loss.set_target(style_features)  # 设置风格图像的特征
style_loss(generated_features)  # 计算损失
loss = style_loss.get_loss()
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_gram_matrix.py
pytest tests/test_losses.py
pytest tests/test_style_transfer.py

# 运行测试并显示覆盖率
pytest tests/ --cov=src
```

## 运行示例

```bash
# 基本风格迁移示例
python examples/basic_transfer.py

# 高级风格迁移示例
python examples/advanced_transfer.py

# Gram 矩阵演示
python examples/gram_matrix_demo.py
```

## 技术细节

### 算法流程

1. **加载预训练 VGG19 模型**：使用在 ImageNet 上预训练的 VGG19 作为特征提取器
2. **提取内容特征**：从 VGG19 的高层（如 conv4_2）提取内容图像的特征
3. **提取风格特征**：从 VGG19 的多层（如 conv1_1, conv2_1, ...）计算风格图像的 Gram 矩阵
4. **初始化生成图像**：通常使用内容图像或随机噪声作为初始值
5. **优化生成图像**：通过最小化内容损失和风格损失来优化生成图像

### 损失函数

总损失函数由三部分组成：

```
L_total = α * L_content + β * L_style + γ * L_tv
```

- **L_content**：内容损失，保持生成图像的内容信息
- **L_style**：风格损失，迁移风格图像的纹理特征
- **L_tv**：全变分损失，平滑生成图像，减少噪声

### 超参数

- **content_weight (α)**：内容损失权重，通常为 1.0
- **style_weight (β)**：风格损失权重，通常为 1e5 ~ 1e7
- **tv_weight (γ)**：全变分损失权重，通常为 1e-5 ~ 1e-3
- **num_steps**：优化迭代次数，通常为 300 ~ 500

## 参考资料

### 核心论文

1. Gatys et al. (2015) - A Neural Algorithm of Artistic Style
2. Johnson et al. (2016) - Perceptual Losses for Real-Time Style Transfer
3. Huang & Belongie (2017) - Arbitrary Style Transfer in Real-time with Adaptive Instance Normalization

### 官方教程

- [PyTorch Neural Style Tutorial](https://pytorch.org/tutorials/advanced/neural_style_tutorial.html)
- [TensorFlow Style Transfer](https://www.tensorflow.org/tutorials/generative/style_transfer)

### 开源项目

- [neural-style](https://github.com/jcjohnson/neural-style)
- [fast-neural-style](https://github.com/pytorch/examples/tree/main/fast_neural_style)

## 常见问题

### Q: 风格迁移速度很慢怎么办？

A: 可以尝试以下方法：
- 减小图像大小（如从 512 降到 256）
- 减少优化步数（如从 300 降到 100）
- 使用 Adam 优化器代替 L-BFGS
- 使用 GPU 加速

### Q: 生成的图像质量不好怎么办？

A: 可以尝试以下方法：
- 调整内容权重和风格权重的比例
- 增加全变分损失权重以平滑图像
- 增加优化步数
- 尝试不同的内容层和风格层

### Q: 内存不足怎么办？

A: 可以尝试以下方法：
- 减小图像大小
- 使用 CPU 而不是 GPU
- 清理不需要的张量：`torch.cuda.empty_cache()`
- 使用梯度检查点

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

MIT License

## 作者

Your Name

## 致谢

- PyTorch 团队
- Gatys et al. 的开创性工作
- 所有开源贡献者
