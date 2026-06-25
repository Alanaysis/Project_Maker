# Super Resolution - 图像超分辨率

实现图像超分辨率算法（SRCNN、ESPCN），将低分辨率图像转换为高分辨率图像，学习深度学习在图像复原领域的应用。

## 学习目标

- 理解超分辨率原理和挑战
- 掌握 SRCNN（超分辨率卷积神经网络）架构
- 掌握 ESPCN（高效亚像素卷积神经网络）架构
- 学会像素重排（Pixel Shuffle）技术
- 实现完整的训练和评估流程

## 核心循环

```
低分辨率图像 → 特征提取 → 上采样 → 高分辨率图像
```

## 项目结构

```
super-resolution/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── models.py            # SRCNN 和 ESPCN 模型实现
│   ├── dataset.py           # 数据集加载和预处理
│   ├── trainer.py           # 模型训练器
│   ├── evaluator.py         # 模型评估器
│   └── utils.py             # 工具函数
├── tests/
│   ├── test_models.py       # 模型测试
│   ├── test_dataset.py      # 数据集测试
│   └── test_trainer.py      # 训练器测试
├── docs/
│   ├── 01-RESEARCH.md       # 研究文档
│   ├── 02-REQUIREMENTS.md   # 需求文档
│   ├── 03-DESIGN.md         # 设计文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── examples/
│   ├── demo.py              # 演示脚本
│   ├── generate_samples.py  # 生成示例图像
│   └── sample_images/       # 示例图像
├── train.py                 # 训练脚本
├── evaluate.py              # 评估脚本
├── requirements.txt         # 依赖包
├── README.md                # 项目说明
└── LEARNING_NOTES.md        # 学习笔记
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
# 生成示例图像
python examples/generate_samples.py

# 运行演示
python examples/demo.py
```

### 训练模型

```bash
# 训练 SRCNN 模型
python train.py --model srcnn --epochs 100 --scale_factor 2

# 训练 ESPCN 模型
python train.py --model espcn --epochs 100 --scale_factor 2
```

### 评估模型

```bash
python evaluate.py --model srcnn --checkpoint checkpoints/srcnn_best.pth
```

### 运行测试

```bash
pytest tests/ -v
```

## 模型架构

### SRCNN（超分辨率卷积神经网络）

由 Dong 等人在 2014 年提出的开创性超分辨率方法。

```
输入(低分辨率) → 插值上采样 → Conv1(特征提取) → Conv2(非线性映射) → Conv3(重建) → 输出(高分辨率)
```

**特点**：
- 端到端学习
- 三层卷积网络
- 先上采样再处理
- 简单有效

### ESPCN（高效亚像素卷积神经网络）

由 Shi 等人在 2016 年提出的高效超分辨率方法。

```
输入(低分辨率) → Conv1(特征提取) → Conv2(特征映射) → PixelShuffle(亚像素卷积) → 输出(高分辨率)
```

**特点**：
- 亚像素卷积（Pixel Shuffle）
- 在低分辨率空间提取特征
- 计算效率高
- 实时处理能力

## 核心概念

### 超分辨率（Super Resolution）

从低分辨率图像恢复高分辨率图像的技术。

**挑战**：
- 一对多映射问题（一个低分辨率图像可能对应多个高分辨率图像）
- 细节恢复困难
- 计算复杂度高

### 亚像素卷积（Sub-pixel Convolution）

通过重新排列特征图通道来实现上采样的技术。

```
特征图 [B, C*r^2, H, W] → PixelShuffle → [B, C, H*r, W*r]
```

**优势**：
- 无插值伪影
- 计算效率高
- 可学习的上采样

### 损失函数

- **MSE Loss**：均方误差，像素级损失
- **L1 Loss**：绝对误差，边缘更清晰
- **Perceptual Loss**：感知损失，基于特征
- **SSIM Loss**：结构相似性损失

## 评估指标

### PSNR（峰值信噪比）

```
PSNR = 10 * log10(MAX^2 / MSE)
```

- 越高越好
- 单位：dB
- 典型范围：20-40 dB

### SSIM（结构相似性）

```
SSIM = (2*μx*μy + C1)(2*σxy + C2) / ((μx^2 + μy^2 + C1)(σx^2 + σy^2 + C2))
```

- 越高越好
- 范围：[0, 1]
- 考虑亮度、对比度、结构

## 数据集

### 常用数据集

| 数据集 | 图像数量 | 用途 | 特点 |
|--------|----------|------|------|
| DIV2K | 1000 | 训练/验证 | 高质量2K图像 |
| Set5 | 5 | 测试 | 经典测试集 |
| Set14 | 14 | 测试 | 多样化测试集 |
| BSD100 | 100 | 测试 | 自然图像 |
| Urban100 | 100 | 测试 | 城市建筑 |

### 数据预处理

1. **降采样**：使用双三次插值生成低分辨率图像
2. **裁剪**：随机裁剪训练块
3. **增强**：随机翻转、旋转
4. **归一化**：像素值归一化到 [0, 1]

## 训练技巧

### 学习率调度

- 初始学习率：1e-4
- 使用余弦退火或步长衰减
- 每 20-30 个 epoch 衰减

### 数据增强

- 随机水平翻转
- 随机垂直翻转
- 随机 90 度旋转

### 模型选择

- **SRCNN**：适合学习基础概念
- **ESPCN**：适合实时应用
- **EDSR**：适合高质量输出
- **RCAN**：适合复杂场景

## 性能对比

| 模型 | 参数量 | Set5 PSNR | 速度 | 特点 |
|------|--------|-----------|------|------|
| Bicubic | - | 28.42 | 最快 | 传统方法 |
| SRCNN | 57K | 30.48 | 慢 | 深度学习先驱 |
| ESPCN | 25K | 30.32 | 快 | 亚像素卷积 |
| EDSR | 1.5M | 31.02 | 中 | 残差网络 |

## 常见问题

### 1. 图像模糊

**问题**：输出图像缺乏细节
**解决**：
- 使用感知损失
- 增加网络深度
- 使用对抗训练

### 2. 训练不稳定

**问题**：损失震荡不收敛
**解决**：
- 降低学习率
- 使用梯度裁剪
- 调整批次大小

### 3. 内存不足

**问题**：GPU 显存溢出
**解决**：
- 减小训练块大小
- 使用梯度累积
- 使用混合精度训练

## 扩展学习

1. **EDSR**：增强深度超分辨率网络
2. **RCAN**：残差通道注意力网络
3. **ESRGAN**：增强超分辨率生成对抗网络
4. **Real-ESRGAN**：真实世界超分辨率
5. **SwinIR**：基于 Swin Transformer 的图像恢复

## 参考资料

1. [SRCNN 论文](https://arxiv.org/abs/1501.00092)
2. [ESPCN 论文](https://arxiv.org/abs/1609.05158)
3. [EDSR 论文](https://arxiv.org/abs/1707.02921)
4. [RCAN 论文](https://arxiv.org/abs/1807.02758)
5. [PyTorch 官方教程](https://pytorch.org/tutorials/)

## 许可证

MIT License
