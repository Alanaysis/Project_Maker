# 实现文档：CNN图像分类

## 1. 实现概述

本文档详细描述CNN图像分类项目的实现细节，包括核心算法、代码结构和关键实现。

## 2. 核心算法实现

### 2.1 卷积层实现

**文件**：`src/layers.py`

**实现原理**：
```python
class Conv2D(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0):
        # 初始化卷积核权重
        self.weight = nn.Parameter(torch.randn(out_channels, in_channels, *kernel_size))
        self.bias = nn.Parameter(torch.zeros(out_channels))
        
        # Kaiming初始化
        nn.init.kaiming_normal_(self.weight, mode='fan_out', nonlinearity='relu')
    
    def forward(self, x):
        # 使用PyTorch的F.conv2d实现卷积操作
        return F.conv2d(x, self.weight, self.bias, self.stride, self.padding)
```

**关键点**：
- 使用`nn.Parameter`注册可学习参数
- 使用Kaiming初始化权重
- 使用`F.conv2d`实现高效卷积

### 2.2 池化层实现

**文件**：`src/layers.py`

**实现原理**：
```python
class MaxPool2D(nn.Module):
    def __init__(self, kernel_size, stride=None):
        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size
    
    def forward(self, x):
        return F.max_pool2d(x, self.kernel_size, self.stride)
```

**关键点**：
- 使用`F.max_pool2d`实现最大池化
- 默认步长等于池化窗口大小

### 2.3 LeNet-5实现

**文件**：`src/lenet.py`

**网络结构**：
```python
class LeNet5(nn.Module):
    def __init__(self, num_classes=10, in_channels=1):
        super().__init__()
        
        # 第一个卷积块
        self.conv1 = nn.Conv2d(in_channels, 6, kernel_size=5)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # 第二个卷积块
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # 全连接层
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)
    
    def forward(self, x):
        # 第一个卷积块
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        
        # 第二个卷积块
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        
        # 展平
        x = x.view(x.size(0), -1)
        
        # 全连接层
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        
        return x
```

**关键点**：
- 使用ReLU激活函数
- 使用最大池化降低维度
- 使用view操作展平特征图

### 2.4 AlexNet实现

**文件**：`src/alexnet.py`

**网络结构**：
```python
class AlexNet(nn.Module):
    def __init__(self, num_classes=1000, in_channels=3):
        super().__init__()
        
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 96, kernel_size=11, stride=4, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            
            nn.Conv2d(96, 256, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            
            nn.Conv2d(256, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            
            nn.Conv2d(384, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            
            nn.Conv2d(384, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
        )
        
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(256 * 6 * 6, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_classes),
        )
```

**关键点**：
- 使用`nn.Sequential`组织层
- 使用Dropout正则化
- 使用`inplace=True`节省内存

### 2.5 VGG实现

**文件**：`src/vgg.py`

**配置系统**：
```python
VGG_CONFIGS = {
    'vgg11': [64, 'M', 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'vgg13': [64, 64, 'M', 128, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'vgg16': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    'vgg19': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M'],
}

def make_layers(config, batch_norm=False):
    layers = []
    in_channels = 3
    
    for v in config:
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=1)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v
    
    return nn.Sequential(*layers)
```

**关键点**：
- 使用配置字典定义网络结构
- 支持批归一化
- 使用工厂函数创建模型

## 3. 数据处理实现

### 3.1 数据预处理

**文件**：`src/dataset.py`

**实现**：
```python
def get_mnist_transforms():
    train_transform = transforms.Compose([
        transforms.Resize((32, 32)),  # LeNet-5要求32x32输入
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1)),  # 数据增强
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))  # MNIST均值和标准差
    ])
    
    test_transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    return train_transform, test_transform
```

**关键点**：
- 调整图像大小到32x32
- 应用数据增强
- 标准化处理

### 3.2 DataLoader创建

**实现**：
```python
def get_mnist_dataloaders(data_dir, batch_size, num_workers, val_split):
    train_dataset = datasets.MNIST(root=data_dir, train=True, download=True, transform=train_transform)
    test_dataset = datasets.MNIST(root=data_dir, train=False, download=True, transform=test_transform)
    
    # 分割训练集和验证集
    val_size = int(len(train_dataset) * val_split)
    train_size = len(train_dataset) - val_size
    train_dataset, val_dataset = random_split(train_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, 
                             num_workers=num_workers, pin_memory=True)
    
    return train_loader, val_loader, test_loader
```

**关键点**：
- 使用`random_split`分割数据集
- 使用`pin_memory`加速GPU传输
- 使用`num_workers`并行加载

## 4. 训练实现

### 4.1 训练循环

**文件**：`src/trainer.py`

**实现**：
```python
def train_epoch(self):
    self.model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for data, target in self.train_loader:
        data, target = data.to(self.device), target.to(self.device)
        
        # 前向传播
        self.optimizer.zero_grad()
        output = self.model(data)
        loss = self.criterion(output, target)
        
        # 反向传播
        loss.backward()
        self.optimizer.step()
        
        # 统计
        total_loss += loss.item() * data.size(0)
        _, predicted = output.max(1)
        total += target.size(0)
        correct += predicted.eq(target).sum().item()
    
    return total_loss / total, 100. * correct / total
```

**关键点**：
- 使用`model.train()`设置训练模式
- 使用`optimizer.zero_grad()`清零梯度
- 使用`loss.backward()`计算梯度
- 使用`optimizer.step()`更新参数

### 4.2 评估循环

**实现**：
```python
@torch.no_grad()
def evaluate(self, data_loader):
    self.model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for data, target in data_loader:
        data, target = data.to(self.device), target.to(self.device)
        output = self.model(data)
        loss = self.criterion(output, target)
        
        total_loss += loss.item() * data.size(0)
        _, predicted = output.max(1)
        total += target.size(0)
        correct += predicted.eq(target).sum().item()
    
    return total_loss / total, 100. * correct / total
```

**关键点**：
- 使用`@torch.no_grad()`禁用梯度计算
- 使用`model.eval()`设置评估模式
- 不更新参数

### 4.3 学习率调度

**实现**：
```python
def compile(self, optimizer, lr, scheduler, **kwargs):
    if scheduler == 'step':
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.1)
    elif scheduler == 'cosine':
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=50)
    elif scheduler == 'plateau':
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode='max', patience=5)
```

**关键点**：
- 支持多种调度策略
- StepLR：固定步长衰减
- CosineAnnealing：余弦退火
- ReduceLROnPlateau：根据指标调整

## 5. 可视化实现

### 5.1 训练历史可视化

**文件**：`src/visualization.py`

**实现**：
```python
def plot_training_history(history, save_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # 损失曲线
    axes[0].plot(history['train_loss'], label='Train Loss')
    axes[0].plot(history['val_loss'], label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].legend()
    axes[0].grid(True)
    
    # 准确率曲线
    axes[1].plot(history['train_acc'], label='Train Acc')
    axes[1].plot(history['val_acc'], label='Val Acc')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy (%)')
    axes[1].legend()
    axes[1].grid(True)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
```

**关键点**：
- 绘制损失和准确率曲线
- 支持保存图片
- 使用网格增强可读性

### 5.2 特征图可视化

**实现**：
```python
def visualize_feature_maps(model, image, save_path):
    model.eval()
    
    with torch.no_grad():
        features = model.get_feature_maps(image.unsqueeze(0))
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    for idx, (name, feat) in enumerate(features.items()):
        ax = axes[idx // 2][idx % 2]
        feat = feat.squeeze(0)[:16]
        
        # 创建网格
        grid_size = int(np.ceil(np.sqrt(len(feat))))
        grid = torch.zeros(grid_size * feat.shape[1], grid_size * feat.shape[2])
        
        for i in range(len(feat)):
            row = i // grid_size
            col = i % grid_size
            grid[row * feat.shape[1]:(row + 1) * feat.shape[1],
                 col * feat.shape[2]:(col + 1) * feat.shape[2]] = feat[i]
        
        ax.imshow(grid.numpy(), cmap='viridis')
        ax.set_title(f'{name} ({len(feat)} channels)')
```

**关键点**：
- 可视化各层特征图
- 使用网格布局
- 使用颜色映射

## 6. 测试实现

### 6.1 层测试

**文件**：`tests/test_layers.py`

**测试用例**：
```python
class TestConv2D:
    def test_conv2d_output_shape(self):
        """测试卷积层输出形状"""
        x = torch.randn(4, 3, 32, 32)
        conv = Conv2D(3, 16, kernel_size=3)
        output = conv(x)
        assert output.shape == (4, 16, 30, 30)
    
    def test_conv2d_gradient(self):
        """测试卷积层梯度计算"""
        conv = Conv2D(3, 16, kernel_size=3)
        x = torch.randn(2, 3, 10, 10, requires_grad=True)
        output = conv(x)
        loss = output.sum()
        loss.backward()
        assert x.grad is not None
```

**关键点**：
- 测试输出形状
- 测试梯度计算
- 测试边界情况

### 6.2 模型测试

**文件**：`tests/test_models.py`

**测试用例**：
```python
class TestLeNet5:
    def test_lenet5_output_shape(self):
        """测试LeNet-5输出形状"""
        model = LeNet5(10, 1)
        x = torch.randn(4, 1, 32, 32)
        output = model(x)
        assert output.shape == (4, 10)
    
    def test_lenet5_gradient_flow(self):
        """测试LeNet-5梯度流"""
        model = LeNet5(10, 1)
        x = torch.randn(2, 1, 32, 32, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()
        
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None
```

**关键点**：
- 测试模型输出
- 测试梯度流
- 测试参数更新

## 7. 性能优化

### 7.1 内存优化

- 使用`pin_memory=True`加速GPU传输
- 使用`inplace=True`节省内存
- 使用梯度累积减少显存占用

### 7.2 计算优化

- 使用GPU加速训练
- 使用`torch.no_grad()`禁用梯度计算
- 使用`model.eval()`设置评估模式

### 7.3 IO优化

- 使用`num_workers`并行加载数据
- 使用缓存减少重复计算
- 使用异步IO

## 8. 部署说明

### 8.1 环境要求

- Python 3.8+
- PyTorch 2.0+
- torchvision 0.15+
- matplotlib 3.7+
- numpy 1.24+

### 8.2 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd cnn-classification

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 运行演示
python demo.py

# 训练模型
python train.py
```

### 8.3 使用示例

```python
from src import LeNet5, Trainer, get_mnist_dataloaders

# 加载数据
train_loader, val_loader, test_loader = get_mnist_dataloaders(batch_size=64)

# 创建模型
model = LeNet5(num_classes=10, in_channels=1)

# 创建训练器
trainer = Trainer(model, train_loader, val_loader, test_loader)

# 配置训练
trainer.compile(optimizer='adam', lr=0.001)

# 训练模型
history = trainer.fit(epochs=20)

# 测试模型
test_loss, test_acc = trainer.test()
```

## 9. 故障排除

### 9.1 常见问题

**CUDA内存不足**：
- 减小批次大小
- 使用梯度累积
- 使用混合精度训练

**训练不收敛**：
- 检查学习率
- 检查数据预处理
- 检查损失函数

**过拟合**：
- 增加数据增强
- 使用Dropout
- 使用权重衰减

### 9.2 调试技巧

- 使用`print`语句调试
- 使用`pdb`调试器
- 使用TensorBoard可视化

## 10. 参考资料

1. [PyTorch官方文档](https://pytorch.org/docs/stable/)
2. [PyTorch教程](https://pytorch.org/tutorials/)
3. [深度学习实践](https://d2l.ai/chapter_convolutional-neural-networks/lenet.html)
