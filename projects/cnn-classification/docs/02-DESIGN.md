# 设计文档：CNN图像分类

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CNN Classification                        │
├─────────────────────────────────────────────────────────────┤
│  src/                                                        │
│  ├── layers.py        # 自定义CNN层实现                       │
│  ├── lenet.py         # LeNet-5网络                          │
│  ├── alexnet.py       # AlexNet网络                          │
│  ├── vgg.py           # VGG网络                              │
│  ├── dataset.py       # 数据集加载                            │
│  ├── trainer.py       # 模型训练器                            │
│  └── visualization.py # 可视化工具                            │
├─────────────────────────────────────────────────────────────┤
│  tests/                                                      │
│  ├── test_layers.py   # 层测试                               │
│  └── test_models.py   # 模型测试                             │
├─────────────────────────────────────────────────────────────┤
│  train.py            # 训练脚本                               │
│  demo.py             # 演示脚本                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
┌─────────────┐
│   train.py   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  Trainer    │────▶│   Model     │
└──────┬──────┘     └──────┬──────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Dataset    │     │   Layers    │
└─────────────┘     └─────────────┘
```

## 2. 类设计

### 2.1 Conv2D类

**职责**：实现2D卷积操作

**属性**：
- `in_channels`: 输入通道数
- `out_channels`: 输出通道数
- `kernel_size`: 卷积核大小
- `stride`: 步长
- `padding`: 填充
- `weight`: 卷积核权重
- `bias`: 偏置

**方法**：
- `forward(x)`: 前向传播
- `extra_repr()`: 返回层描述

### 2.2 MaxPool2D类

**职责**：实现2D最大池化操作

**属性**：
- `kernel_size`: 池化窗口大小
- `stride`: 步长

**方法**：
- `forward(x)`: 前向传播

### 2.3 Flatten类

**职责**：将多维特征图展平为一维向量

**方法**：
- `forward(x)`: 前向传播

### 2.4 LeNet5类

**职责**：实现LeNet-5网络架构

**属性**：
- `conv1`: 第一个卷积层
- `pool1`: 第一个池化层
- `conv2`: 第二个卷积层
- `pool2`: 第二个池化层
- `fc1`: 第一个全连接层
- `fc2`: 第二个全连接层
- `fc3`: 第三个全连接层

**方法**：
- `forward(x)`: 前向传播
- `get_feature_maps(x)`: 获取特征图

### 2.5 Trainer类

**职责**：封装训练循环和评估逻辑

**属性**：
- `model`: 要训练的模型
- `train_loader`: 训练数据加载器
- `val_loader`: 验证数据加载器
- `test_loader`: 测试数据加载器
- `device`: 计算设备
- `history`: 训练历史

**方法**：
- `compile(optimizer, lr, ...)`: 配置优化器
- `train_epoch()`: 训练一个epoch
- `evaluate(data_loader)`: 评估模型
- `fit(epochs, ...)`: 训练模型
- `test()`: 测试模型
- `save_model(path)`: 保存模型
- `load_model(path)`: 加载模型

## 3. 数据流设计

### 3.1 训练流程

```
输入图像
    │
    ▼
┌─────────────┐
│ 数据预处理   │
│ - Resize    │
│ - Normalize │
│ - Augment   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  DataLoader │
│ - Batch     │
│ - Shuffle   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Model     │
│ - Conv      │
│ - Pool      │
│ - FC        │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Loss      │
│ CrossEntropy│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Backward   │
│ - Gradient  │
│ - Update    │
└─────────────┘
```

### 3.2 推理流程

```
输入图像
    │
    ▼
┌─────────────┐
│ 数据预处理   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Model     │
│ (eval mode) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Softmax    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Prediction │
└─────────────┘
```

## 4. 接口设计

### 4.1 模型接口

```python
class CNNModel(nn.Module):
    """CNN模型基类"""
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        pass
    
    def get_feature_maps(self, x: torch.Tensor) -> dict:
        """获取特征图"""
        pass
```

### 4.2 数据加载接口

```python
def get_mnist_dataloaders(
    data_dir: str,
    batch_size: int,
    num_workers: int,
    val_split: float
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """获取MNIST数据加载器"""
    pass
```

### 4.3 训练器接口

```python
class Trainer:
    """模型训练器"""
    
    def compile(self, optimizer: str, lr: float, ...):
        """配置优化器"""
        pass
    
    def fit(self, epochs: int, ...) -> dict:
        """训练模型"""
        pass
    
    def test(self) -> Tuple[float, float]:
        """测试模型"""
        pass
```

## 5. 配置设计

### 5.1 模型配置

```python
# LeNet-5配置
lenet_config = {
    'num_classes': 10,
    'in_channels': 1
}

# AlexNet配置
alexnet_config = {
    'num_classes': 1000,
    'in_channels': 3
}

# VGG配置
vgg_config = {
    'model': 'vgg16',
    'num_classes': 1000,
    'in_channels': 3,
    'batch_norm': False
}
```

### 5.2 训练配置

```python
training_config = {
    'batch_size': 64,
    'epochs': 20,
    'optimizer': 'adam',
    'lr': 0.001,
    'weight_decay': 0.0,
    'scheduler': None,
    'early_stopping': None
}
```

## 6. 错误处理设计

### 6.1 输入验证

- 检查输入维度
- 检查输入数据类型
- 检查输入值范围

### 6.2 异常处理

- 捕获CUDA内存不足异常
- 捕获数据加载异常
- 捕获模型保存/加载异常

### 6.3 日志记录

- 训练进度日志
- 错误日志
- 性能指标日志

## 7. 性能设计

### 7.1 内存优化

- 使用`pin_memory`加速数据传输
- 使用`num_workers`并行加载数据
- 使用梯度累积减少显存占用

### 7.2 计算优化

- 使用GPU加速训练
- 使用混合精度训练
- 使用编译优化

### 7.3 IO优化

- 使用缓存减少重复计算
- 使用异步IO
- 使用压缩存储

## 8. 扩展性设计

### 8.1 模型扩展

- 支持添加新的CNN架构
- 支持自定义层
- 支持模型组合

### 8.2 数据集扩展

- 支持添加新的数据集
- 支持自定义数据增强
- 支持自定义预处理

### 8.3 训练扩展

- 支持分布式训练
- 支持自定义损失函数
- 支持自定义评估指标

## 9. 测试设计

### 9.1 单元测试

- 层测试：测试每个层的正确性
- 模型测试：测试模型的正确性
- 工具测试：测试工具函数的正确性

### 9.2 集成测试

- 训练流程测试
- 推理流程测试
- 保存/加载测试

### 9.3 性能测试

- 内存使用测试
- 训练速度测试
- 推理速度测试

## 10. 部署设计

### 10.1 模型导出

- 导出为ONNX格式
- 导出为TorchScript格式
- 导出为TensorRT格式

### 10.2 模型服务

- REST API服务
- gRPC服务
- 边缘部署

## 11. 参考资料

1. [PyTorch设计模式](https://pytorch.org/docs/stable/notes/best_practices.html)
2. [CNN架构设计](https://arxiv.org/abs/1409.1556)
3. [深度学习系统设计](https://d2l.ai/)
