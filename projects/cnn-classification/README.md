# CNN Classification - 图像分类卷积神经网络

实现经典CNN架构（LeNet-5、AlexNet、VGG）进行图像分类，重点学习CNN的基本组件和架构设计。

## 学习目标

- 理解CNN架构设计原理
- 掌握卷积层、池化层的工作机制
- 学会实现经典网络（LeNet-5、AlexNet、VGG）
- 在MNIST数据集上进行图像分类

## 核心循环

```
图像 → 卷积 → 池化 → 全连接 → 分类
```

## 项目结构

```
cnn-classification/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── layers.py            # 自定义CNN层实现
│   ├── lenet.py             # LeNet-5网络
│   ├── alexnet.py           # AlexNet网络
│   ├── vgg.py               # VGG网络
│   ├── dataset.py           # 数据集加载
│   ├── trainer.py           # 模型训练器
│   └── visualization.py     # 可视化工具
├── tests/
│   ├── test_layers.py       # 层测试
│   └── test_models.py       # 模型测试
├── docs/
│   ├── 01-RESEARCH.md       # 研究文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── train.py                 # 训练脚本
├── demo.py                  # 演示脚本
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
python demo.py
```

### 训练模型

```bash
# 使用默认参数训练LeNet-5
python train.py

# 自定义参数训练
python train.py --epochs 30 --lr 0.001 --optimizer adam --scheduler cosine
```

### 运行测试

```bash
pytest tests/ -v
```

## 模型架构

### LeNet-5

经典CNN架构，由Yann LeCun在1998年提出。

```
输入(1x32x32) → Conv1(6@5x5) → Pool1 → Conv2(16@5x5) → Pool2 → FC1(120) → FC2(84) → FC3(10)
```

**特点**：
- 使用5x5卷积核
- 使用2x2最大池化
- 适用于灰度图像

### AlexNet

深度CNN架构，由Alex Krizhevsky在2012年提出。

```
输入(3x227x227) → Conv1(96@11x11) → Pool1 → Conv2(256@5x5) → Pool2 → 
Conv3(384@3x3) → Conv4(384@3x3) → Conv5(256@3x3) → Pool5 → FC1(4096) → FC2(4096) → FC3(1000)
```

**特点**：
- 使用11x11大卷积核
- 使用ReLU激活函数
- 使用Dropout正则化

### VGG

深度CNN架构，由Karen Simonyan和Andrew Zisserman在2014年提出。

```
输入(3x224x224) → [3x3 Conv] x N → MaxPool → [3x3 Conv] x N → MaxPool → ... → FC1(4096) → FC2(4096) → FC3(1000)
```

**特点**：
- 使用3x3小卷积核堆叠
- 网络深度可配置（11/13/16/19层）
- 结构规整，易于理解

## 核心概念

### 卷积层（Convolutional Layer）

卷积操作：在输入特征图上滑动卷积核，计算局部区域的加权和。

```
输出[i,j] = Σ Σ 输入[i+m, j+n] * 卷积核[m, n] + 偏置
```

**关键参数**：
- `kernel_size`: 卷积核大小
- `stride`: 滑动步长
- `padding`: 边缘填充
- `out_channels`: 卷积核数量

### 池化层（Pooling Layer）

池化操作：降低特征图尺寸，减少计算量，增强平移不变性。

**最大池化**：取局部区域最大值
**平均池化**：取局部区域平均值

### 激活函数（Activation Function）

引入非线性，增强网络表达能力。

**ReLU**: f(x) = max(0, x)
- 计算简单
- 缓解梯度消失
- 稀疏激活

### 全连接层（Fully Connected Layer）

将特征图展平后进行分类。

```
输出 = 权重 × 输入 + 偏置
```

## 训练技巧

### 数据增强

- 随机旋转
- 随机平移
- 随机缩放

### 正则化

- Dropout：随机丢弃神经元
- 权重衰减（L2正则化）
- 批归一化

### 学习率调度

- StepLR：固定步长衰减
- CosineAnnealingLR：余弦退火
- ReduceLROnPlateau：根据验证损失调整

## 性能对比

| 模型 | 参数量 | MNIST准确率 | 训练时间 |
|------|--------|-------------|----------|
| LeNet-5 | ~60K | ~99% | ~5分钟 |
| AlexNet | ~60M | ~99.2% | ~30分钟 |
| VGG-11 | ~130M | ~99.3% | ~60分钟 |

## 常见问题

### 1. 梯度消失/爆炸

**问题**：深层网络训练困难
**解决**：
- 使用ReLU激活函数
- 使用批归一化
- 使用残差连接

### 2. 过拟合

**问题**：训练准确率高，验证准确率低
**解决**：
- 增加数据增强
- 使用Dropout
- 使用权重衰减

### 3. 计算资源不足

**问题**：GPU显存不足
**解决**：
- 减小批次大小
- 使用梯度累积
- 使用混合精度训练

## 扩展学习

1. **ResNet**：残差网络，解决深层网络退化问题
2. **Inception**：多尺度特征提取
3. **DenseNet**：密集连接网络
4. **Attention**：注意力机制

## 参考资料

1. [LeNet-5论文](http://yann.lecun.com/exdb/publis/pdf/lecun-98.pdf)
2. [AlexNet论文](https://papers.nips.cc/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html)
3. [VGG论文](https://arxiv.org/abs/1409.1556)
4. [PyTorch官方教程](https://pytorch.org/tutorials/)

## 许可证

MIT License
