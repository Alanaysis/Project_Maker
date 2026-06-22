# 学习笔记：CNN图像分类

## 1. 核心概念

### 1.1 什么是CNN

卷积神经网络（CNN）是一种专门用于处理网格结构数据（如图像）的深度学习模型。CNN通过卷积操作提取局部特征，并通过层级结构逐步提取更高级的特征。

**关键特性**：
- 局部连接：每个神经元只连接输入的局部区域
- 权重共享：同一个卷积核在整个输入上共享
- 平移等变性：输入平移，输出也相应平移

### 1.2 CNN的基本组件

**卷积层（Convolutional Layer）**：
- 提取局部特征
- 使用卷积核滑动计算
- 输出特征图

**池化层（Pooling Layer）**：
- 降低特征图尺寸
- 增强平移不变性
- 减少计算量

**激活函数（Activation Function）**：
- 引入非线性
- 增强表达能力
- 常用ReLU

**全连接层（Fully Connected Layer）**：
- 分类决策
- 整合全局特征
- 输出类别概率

## 2. 卷积操作详解

### 2.1 卷积的数学定义

```
(f * g)(t) = Σ f(τ) * g(t - τ)
```

**图像卷积**：
```
output[i,j] = Σ Σ input[i+m, j+n] * kernel[m, n]
```

### 2.2 卷积的关键参数

**kernel_size（卷积核大小）**：
- 3x3：最常用，感受野小，参数少
- 5x5：感受野较大，参数较多
- 1x1：用于通道变换

**stride（步长）**：
- 1：默认步长，不跳跃
- 2：降低特征图尺寸
- 更大的步长：更大幅度降低尺寸

**padding（填充）**：
- 0：不填充，输出尺寸减小
- 1：填充一圈，保持尺寸
- same：自动填充保持尺寸

**out_channels（输出通道数）**：
- 卷积核数量
- 决定特征图数量
- 通常逐层增加

### 2.3 特征图尺寸计算

```
output_size = (input_size - kernel_size + 2 × padding) / stride + 1
```

**示例**：
- 输入：32x32
- 卷积核：5x5
- 填充：0
- 步长：1
- 输出：(32 - 5 + 0) / 1 + 1 = 28x28

### 2.4 卷积的直觉理解

**特征检测**：
- 卷积核可以看作特征检测器
- 不同的卷积核检测不同的特征
- 边缘、角点、纹理等

**层级特征**：
- 低层：边缘、纹理
- 中层：部件、模式
- 高层：物体、场景

## 3. 池化操作详解

### 3.1 最大池化

```
output[i,j] = max(input[i*s:i*s+k, j*s:j*s+k])
```

**特点**：
- 保留最显著特征
- 增强平移不变性
- 减少计算量

### 3.2 平均池化

```
output[i,j] = mean(input[i*s:i*s+k, j*s:j*s+k])
```

**特点**：
- 保留平均特征
- 平滑特征图
- 减少噪声

### 3.3 池化的作用

**降低维度**：
- 减少参数数量
- 减少计算量
- 防止过拟合

**增强鲁棒性**：
- 平移不变性
- 轻微变形不变性
- 噪声鲁棒性

**扩大感受野**：
- 后层神经元覆盖更大区域
- 捕获更全局的特征

## 4. 经典架构分析

### 4.1 LeNet-5

**架构**：
```
输入(1x32x32) → Conv1(6@5x5) → Pool1 → Conv2(16@5x5) → Pool2 → FC1(120) → FC2(84) → FC3(10)
```

**设计特点**：
- 使用5x5卷积核
- 使用2x2最大池化
- 使用tanh激活函数（原始版本）
- 适用于灰度图像

**学习要点**：
- 卷积-池化交替结构
- 特征图逐层增加
- 全连接层分类

**历史意义**：
- 首个成功的CNN架构
- 用于手写数字识别
- 证明了CNN的有效性

### 4.2 AlexNet

**架构**：
```
输入(3x227x227) → Conv1(96@11x11) → Pool1 → Conv2(256@5x5) → Pool2 → 
Conv3(384@3x3) → Conv4(384@3x3) → Conv5(256@3x3) → Pool5 → FC1(4096) → FC2(4096) → FC3(1000)
```

**创新点**：
- 使用ReLU激活函数
- 使用Dropout正则化
- 使用数据增强
- 使用GPU训练

**学习要点**：
- 深度网络设计
- 正则化技术
- 训练技巧

**历史意义**：
- 赢得ImageNet LSVRC-2012比赛
- 开启深度学习时代
- 证明深度网络的有效性

### 4.3 VGG

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

**学习要点**：
- 小卷积核的优势
- 网络深度的影响
- 规整结构设计

**创新点**：
- 证明小卷积核堆叠可以替代大卷积核
- 增加网络深度可以提升性能
- 提供了网络设计的通用原则

## 5. 实现细节

### 5.1 权重初始化

**Kaiming初始化**：
```python
nn.init.kaiming_normal_(weight, mode='fan_out', nonlinearity='relu')
```

**作用**：
- 保持方差稳定
- 缓解梯度消失/爆炸
- 加速收敛

### 5.2 批归一化

**实现**：
```python
nn.BatchNorm2d(num_features)
```

**作用**：
- 加速训练
- 允许更大的学习率
- 轻微正则化效果

### 5.3 Dropout

**实现**：
```python
nn.Dropout(p=0.5)
```

**作用**：
- 防止过拟合
- 增强泛化能力
- 随机丢弃神经元

### 5.4 数据增强

**常用方法**：
- 随机裁剪
- 随机翻转
- 随机旋转
- 颜色抖动

**作用**：
- 增加数据多样性
- 防止过拟合
- 提升泛化能力

## 6. 训练技巧

### 6.1 学习率调度

**StepLR**：
```python
scheduler = StepLR(optimizer, step_size=10, gamma=0.1)
```

**CosineAnnealing**：
```python
scheduler = CosineAnnealingLR(optimizer, T_max=50)
```

**ReduceLROnPlateau**：
```python
scheduler = ReduceLROnPlateau(optimizer, mode='max', patience=5)
```

### 6.2 优化器选择

**Adam**：
- 自适应学习率
- 收敛快
- 适合大多数任务

**SGD+Momentum**：
- 收敛稳定
- 泛化好
- 需要调参

**AdamW**：
- Adam + 权重衰减
- 更好的正则化
- 适合大模型

### 6.3 正则化技术

**权重衰减**：
```python
optimizer = Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
```

**早停**：
```python
if val_acc > best_val_acc:
    best_val_acc = val_acc
    patience_counter = 0
else:
    patience_counter += 1
    
if patience_counter >= patience:
    break
```

## 7. 调试经验

### 7.1 常见问题

**梯度消失**：
- 使用ReLU激活函数
- 使用批归一化
- 使用残差连接

**过拟合**：
- 增加数据增强
- 使用Dropout
- 使用权重衰减
- 减少模型复杂度

**不收敛**：
- 检查学习率
- 检查数据预处理
- 检查损失函数
- 检查梯度流

### 7.2 调试技巧

**打印中间结果**：
```python
print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")
print(f"Loss: {loss.item()}")
```

**检查梯度**：
```python
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")
```

**可视化特征图**：
```python
features = model.get_feature_maps(x)
for name, feat in features.items():
    print(f"{name}: {feat.shape}")
```

## 8. 性能优化

### 8.1 内存优化

- 使用`pin_memory=True`加速GPU传输
- 使用`inplace=True`节省内存
- 使用梯度累积减少显存占用
- 使用混合精度训练

### 8.2 计算优化

- 使用GPU加速训练
- 使用`torch.no_grad()`禁用梯度计算
- 使用`model.eval()`设置评估模式
- 使用编译优化

### 8.3 数据加载优化

- 使用`num_workers`并行加载
- 使用缓存减少重复计算
- 使用异步IO
- 预加载数据

## 9. 实验记录

### 9.1 LeNet-5实验

**配置**：
- 数据集：MNIST
- 批次大小：64
- 学习率：0.001
- 优化器：Adam
- 训练轮数：20

**结果**：
- 训练准确率：99.5%
- 验证准确率：99.2%
- 测试准确率：99.1%
- 训练时间：5分钟

**观察**：
- 收敛快
- 准确率高
- 轻微过拟合

### 9.2 AlexNet实验

**配置**：
- 数据集：CIFAR-10
- 批次大小：128
- 学习率：0.001
- 优化器：Adam
- 训练轮数：50

**结果**：
- 训练准确率：95.2%
- 验证准确率：91.5%
- 测试准确率：91.2%
- 训练时间：30分钟

**观察**：
- 需要更多训练轮数
- 有明显过拟合
- 数据增强很重要

### 9.3 VGG实验

**配置**：
- 数据集：CIFAR-10
- 批次大小：64
- 学习率：0.01
- 优化器：SGD+Momentum
- 训练轮数：100

**结果**：
- 训练准确率：97.8%
- 验证准确率：93.2%
- 测试准确率：93.0%
- 训练时间：60分钟

**观察**：
- 需要更大学习率
- 批归一化很重要
- 深度网络需要更多训练

## 10. 学习资源

### 10.1 论文

1. LeNet-5: http://yann.lecun.com/exdb/publis/pdf/lecun-98.pdf
2. AlexNet: https://papers.nips.cc/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html
3. VGG: https://arxiv.org/abs/1409.1556
4. ResNet: https://arxiv.org/abs/1512.03385

### 10.2 教程

1. PyTorch官方教程: https://pytorch.org/tutorials/
2. 深度学习实践: https://d2l.ai/
3. CS231n: http://cs231n.stanford.edu/

### 10.3 代码

1. PyTorch官方示例: https://github.com/pytorch/examples
2. torchvision: https://github.com/pytorch/vision
3. timm: https://github.com/huggingface/pytorch-image-models

## 11. 总结

### 11.1 核心要点

1. CNN通过卷积操作提取局部特征
2. 池化层降低维度，增强鲁棒性
3. 激活函数引入非线性
4. 全连接层进行分类决策

### 11.2 设计原则

1. 卷积-池化交替结构
2. 特征图逐层增加
3. 使用小卷积核堆叠
4. 适当使用正则化

### 11.3 训练技巧

1. 合理选择学习率
2. 使用数据增强
3. 使用正则化技术
4. 监控训练过程

### 11.4 未来方向

1. 残差网络（ResNet）
2. 注意力机制（Attention）
3. 轻量级网络（MobileNet）
4. 自监督学习
