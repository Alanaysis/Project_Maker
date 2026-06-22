# 研究文档：CNN图像分类

## 1. 背景知识

### 1.1 什么是CNN

卷积神经网络（Convolutional Neural Network，CNN）是一种专门用于处理网格结构数据（如图像）的深度学习模型。CNN通过卷积操作提取局部特征，并通过层级结构逐步提取更高级的特征。

### 1.2 CNN的发展历史

| 年份 | 模型 | 主要贡献 |
|------|------|----------|
| 1998 | LeNet-5 | 首个成功的CNN架构 |
| 2012 | AlexNet | 深度CNN在ImageNet上取得突破 |
| 2014 | VGG | 小卷积核堆叠的深度网络 |
| 2014 | GoogLeNet | Inception模块 |
| 2015 | ResNet | 残差连接解决退化问题 |

### 1.3 CNN的应用领域

- 图像分类
- 目标检测
- 语义分割
- 图像生成
- 视频分析

## 2. 核心概念

### 2.1 卷积操作

卷积是CNN的核心操作，通过在输入数据上滑动卷积核来提取特征。

**数学定义**：
```
(f * g)(t) = Σ f(τ) * g(t - τ)
```

**图像卷积**：
```
output[i,j] = Σ Σ input[i+m, j+n] * kernel[m, n]
```

**关键特性**：
- 局部连接：每个神经元只连接输入的局部区域
- 权重共享：同一个卷积核在整个输入上共享
- 平移等变性：输入平移，输出也相应平移

### 2.2 池化操作

池化层用于降低特征图的空间尺寸，减少计算量，增强平移不变性。

**最大池化**：
```
output[i,j] = max(input[i*s:i*s+k, j*s:j*s+k])
```

**平均池化**：
```
output[i,j] = mean(input[i*s:i*s+k, j*s:j*s+k])
```

**作用**：
- 降低维度
- 减少参数
- 增强鲁棒性

### 2.3 激活函数

激活函数引入非线性，使网络能够学习复杂的模式。

**ReLU**：
```
f(x) = max(0, x)
```

**优点**：
- 计算简单
- 缓解梯度消失
- 稀疏激活

**Sigmoid**：
```
f(x) = 1 / (1 + exp(-x))
```

**Tanh**：
```
f(x) = (exp(x) - exp(-x)) / (exp(x) + exp(-x))
```

## 3. 经典架构分析

### 3.1 LeNet-5

**架构**：
```
输入(1x32x32) → Conv1(6@5x5) → Pool1(2x2) → Conv2(16@5x5) → Pool2(2x2) → 
FC1(120) → FC2(84) → FC3(10)
```

**设计特点**：
- 使用5x5卷积核
- 使用2x2最大池化
- 使用tanh激活函数（原始版本）
- 适用于灰度图像

**历史意义**：
- 首个成功的CNN架构
- 用于手写数字识别
- 证明了CNN的有效性

### 3.2 AlexNet

**架构**：
```
输入(3x227x227) → Conv1(96@11x11, stride=4) → Pool1(3x3, stride=2) → 
Conv2(256@5x5) → Pool2(3x3, stride=2) → 
Conv3(384@3x3) → Conv4(384@3x3) → Conv5(256@3x3) → Pool5(3x3, stride=2) → 
FC1(4096) → FC2(4096) → FC3(1000)
```

**创新点**：
- 使用ReLU激活函数
- 使用Dropout正则化
- 使用数据增强
- 使用GPU训练

**历史意义**：
- 赢得ImageNet LSVRC-2012比赛
- 开启深度学习时代

### 3.3 VGG

**架构**（以VGG-16为例）：
```
输入(3x224x224) → [3x3 Conv x2] → MaxPool → [3x3 Conv x3] → MaxPool → 
[3x3 Conv x3] → MaxPool → [3x3 Conv x3] → MaxPool → [3x3 Conv x3] → MaxPool → 
FC1(4096) → FC2(4096) → FC3(1000)
```

**设计原则**：
- 使用3x3小卷积核堆叠
- 网络深度增加到16-19层
- 结构规整，易于理解

**创新点**：
- 证明小卷积核堆叠可以替代大卷积核
- 增加网络深度可以提升性能
- 提供了网络设计的通用原则

## 4. 技术细节

### 4.1 参数计算

**卷积层参数数量**：
```
params = in_channels × out_channels × kernel_size × kernel_size + out_channels
```

**全连接层参数数量**：
```
params = input_size × output_size + output_size
```

### 4.2 特征图尺寸计算

**卷积层输出尺寸**：
```
output_size = (input_size - kernel_size + 2 × padding) / stride + 1
```

**池化层输出尺寸**：
```
output_size = (input_size - kernel_size) / stride + 1
```

### 4.3 感受野

感受野是指输出特征图上的一个像素对应输入图像的区域大小。

**计算公式**：
```
RF_l = RF_{l-1} + (kernel_size - 1) × stride_{l-1}
```

**意义**：
- 深层网络的感受野更大
- 可以捕捉更大范围的上下文信息

## 5. 训练技巧

### 5.1 数据增强

**常用方法**：
- 随机裁剪
- 随机翻转
- 随机旋转
- 颜色抖动

**作用**：
- 增加数据多样性
- 防止过拟合
- 提升泛化能力

### 5.2 正则化

**Dropout**：
- 训练时随机丢弃神经元
- 防止过拟合
- 增强泛化能力

**权重衰减**：
- L2正则化
- 限制权重大小
- 防止过拟合

### 5.3 学习率调度

**StepLR**：
- 固定步长衰减
- 简单有效

**CosineAnnealing**：
- 余弦退火
- 平滑调整学习率

**ReduceLROnPlateau**：
- 根据验证损失调整
- 自适应学习率

## 6. 实验设计

### 6.1 数据集选择

**MNIST**：
- 60,000训练样本
- 10,000测试样本
- 28x28灰度图像
- 10个类别（0-9）

**CIFAR-10**：
- 50,000训练样本
- 10,000测试样本
- 32x32彩色图像
- 10个类别

### 6.2 评估指标

**准确率**：
```
accuracy = correct_predictions / total_predictions
```

**损失函数**：
- 交叉熵损失（分类任务）
- 均方误差损失（回归任务）

### 6.3 实验对比

| 模型 | 参数量 | MNIST准确率 | 训练时间 |
|------|--------|-------------|----------|
| LeNet-5 | ~60K | ~99% | ~5分钟 |
| AlexNet | ~60M | ~99.2% | ~30分钟 |
| VGG-11 | ~130M | ~99.3% | ~60分钟 |

## 7. 参考文献

1. LeCun, Y., et al. (1998). Gradient-based learning applied to document recognition.
2. Krizhevsky, A., et al. (2012). ImageNet classification with deep convolutional neural networks.
3. Simonyan, K., & Zisserman, A. (2014). Very deep convolutional networks for large-scale image recognition.
4. He, K., et al. (2016). Deep residual learning for image recognition.
5. Goodfellow, I., et al. (2016). Deep Learning.
