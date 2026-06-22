# 测试文档：CNN图像分类

## 1. 测试概述

### 1.1 测试目标

- 验证CNN层的正确性
- 验证模型架构的正确性
- 验证训练流程的正确性
- 验证数据处理的正确性

### 1.2 测试范围

- 单元测试：测试单个组件
- 集成测试：测试组件协作
- 性能测试：测试性能指标

### 1.3 测试工具

- pytest：测试框架
- torch：深度学习框架
- numpy：数值计算库

## 2. 测试环境

### 2.1 依赖包

```bash
torch>=2.0.0
torchvision>=0.15.0
numpy>=1.24.0
pytest>=7.3.0
```

### 2.2 运行环境

- Python 3.8+
- CPU或GPU
- 内存：至少4GB

### 2.3 运行命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_layers.py -v

# 运行特定测试类
pytest tests/test_layers.py::TestConv2D -v

# 运行特定测试方法
pytest tests/test_layers.py::TestConv2D::test_conv2d_output_shape -v
```

## 3. 单元测试

### 3.1 Conv2D层测试

**文件**：`tests/test_layers.py`

**测试用例**：

```python
class TestConv2D:
    def test_conv2d_output_shape(self):
        """测试卷积层输出形状"""
        batch_size = 4
        in_channels = 3
        height, width = 32, 32
        out_channels = 16
        kernel_size = 3

        x = torch.randn(batch_size, in_channels, height, width)
        conv = Conv2D(in_channels, out_channels, kernel_size)

        output = conv(x)

        assert output.shape == (batch_size, out_channels, 
                                height - kernel_size + 1, 
                                width - kernel_size + 1)

    def test_conv2d_with_padding(self):
        """测试带填充的卷积层"""
        x = torch.randn(4, 1, 28, 28)
        conv = Conv2D(1, 6, kernel_size=5, padding=2)
        output = conv(x)
        assert output.shape == (4, 6, 28, 28)

    def test_conv2d_with_stride(self):
        """测试带步长的卷积层"""
        x = torch.randn(4, 3, 32, 32)
        conv = Conv2D(3, 16, kernel_size=3, stride=2)
        output = conv(x)
        assert output.shape == (4, 16, 15, 15)

    def test_conv2d_gradient(self):
        """测试卷积层梯度计算"""
        conv = Conv2D(3, 16, kernel_size=3)
        x = torch.randn(2, 3, 10, 10, requires_grad=True)
        output = conv(x)
        loss = output.sum()
        loss.backward()
        
        assert x.grad is not None
        assert conv.weight.grad is not None
        assert conv.bias.grad is not None
```

**测试要点**：
- 输出形状正确性
- 填充和步长处理
- 梯度计算正确性

### 3.2 MaxPool2D层测试

**测试用例**：

```python
class TestMaxPool2D:
    def test_maxpool2d_output_shape(self):
        """测试最大池化层输出形状"""
        x = torch.randn(4, 16, 32, 32)
        pool = MaxPool2D(kernel_size=2)
        output = pool(x)
        assert output.shape == (4, 16, 16, 16)

    def test_maxpool2d_with_stride(self):
        """测试带步长的最大池化层"""
        x = torch.randn(4, 16, 32, 32)
        pool = MaxPool2D(kernel_size=3, stride=2)
        output = pool(x)
        assert output.shape == (4, 16, 15, 15)

    def test_maxpool2d_preserves_max(self):
        """测试最大池化保留最大值"""
        x = torch.tensor([[[[1, 2], [3, 4]]]], dtype=torch.float32)
        pool = MaxPool2D(2)
        output = pool(x)
        assert output.item() == 4.0
```

**测试要点**：
- 输出形状正确性
- 最大值保留
- 步长处理

### 3.3 Flatten层测试

**测试用例**：

```python
class TestFlatten:
    def test_flatten_output_shape(self):
        """测试展平层输出形状"""
        x = torch.randn(4, 16, 5, 5)
        flatten = Flatten()
        output = flatten(x)
        assert output.shape == (4, 400)

    def test_flatten_preserves_batch(self):
        """测试展平层保持批次大小"""
        x = torch.randn(8, 3, 10, 10)
        flatten = Flatten()
        output = flatten(x)
        assert output.shape[0] == 8
```

**测试要点**：
- 输出形状正确性
- 批次大小保持

### 3.4 LeNet-5模型测试

**测试用例**：

```python
class TestLeNet5:
    def test_lenet5_output_shape(self):
        """测试LeNet-5输出形状"""
        model = LeNet5(10, 1)
        x = torch.randn(4, 1, 32, 32)
        output = model(x)
        assert output.shape == (4, 10)

    def test_lenet5_custom_output_shape(self):
        """测试自定义LeNet-5输出形状"""
        model = LeNet5Custom(10, 1)
        x = torch.randn(4, 1, 32, 32)
        output = model(x)
        assert output.shape == (4, 10)

    def test_lenet5_factory(self):
        """测试LeNet-5工厂函数"""
        model = lenet5(num_classes=10)
        assert isinstance(model, LeNet5)
        assert model.fc3.out_features == 10

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

    def test_lenet5_feature_maps(self):
        """测试LeNet-5特征图提取"""
        model = LeNet5(10, 1)
        x = torch.randn(2, 1, 32, 32)
        features = model.get_feature_maps(x)
        
        assert 'conv1' in features
        assert 'pool1' in features
        assert 'conv2' in features
        assert 'pool2' in features
        
        assert features['conv1'].shape == (2, 6, 28, 28)
        assert features['pool1'].shape == (2, 6, 14, 14)
        assert features['conv2'].shape == (2, 16, 10, 10)
        assert features['pool2'].shape == (2, 16, 5, 5)
```

**测试要点**：
- 模型输出形状
- 梯度流正确性
- 特征图提取

### 3.5 AlexNet模型测试

**测试用例**：

```python
class TestAlexNet:
    def test_alexnet_output_shape(self):
        """测试AlexNet输出形状"""
        model = AlexNet(1000, 3)
        x = torch.randn(4, 3, 227, 227)
        output = model(x)
        assert output.shape == (4, 1000)

    def test_alexnet_cifar_output_shape(self):
        """测试CIFAR版AlexNet输出形状"""
        model = AlexNetCIFAR(10, 3)
        x = torch.randn(4, 3, 32, 32)
        output = model(x)
        assert output.shape == (4, 10)

    def test_alexnet_factory(self):
        """测试AlexNet工厂函数"""
        model = alexnet(num_classes=1000)
        assert isinstance(model, AlexNet)
        assert model.classifier[-1].out_features == 1000
```

**测试要点**：
- 标准AlexNet输出
- CIFAR版AlexNet输出
- 工厂函数

### 3.6 VGG模型测试

**测试用例**：

```python
class TestVGG:
    def test_vgg11_output_shape(self):
        """测试VGG-11输出形状"""
        model = vgg11(num_classes=1000)
        x = torch.randn(4, 3, 224, 224)
        output = model(x)
        assert output.shape == (4, 1000)

    def test_vgg16_output_shape(self):
        """测试VGG-16输出形状"""
        model = vgg16(num_classes=1000)
        x = torch.randn(4, 3, 224, 224)
        output = model(x)
        assert output.shape == (4, 1000)

    def test_vgg_cifar_output_shape(self):
        """测试CIFAR版VGG输出形状"""
        model = vgg_cifar('vgg16', num_classes=10)
        x = torch.randn(4, 3, 32, 32)
        output = model(x)
        assert output.shape == (4, 10)

    def test_vgg_with_batch_norm(self):
        """测试带批归一化的VGG"""
        model = vgg16(batch_norm=True)
        has_batchnorm = any(isinstance(m, torch.nn.BatchNorm2d) for m in model.modules())
        assert has_batchnorm
```

**测试要点**：
- 不同VGG变体输出
- 批归一化支持
- CIFAR版本输出

## 4. 集成测试

### 4.1 模型集成测试

**测试用例**：

```python
class TestModelIntegration:
    def test_models_train_mode(self):
        """测试模型训练模式切换"""
        models = [
            LeNet5(10, 1),
            AlexNetCIFAR(10, 3),
            vgg_cifar('vgg11', 10, 3)
        ]

        for model in models:
            model.train()
            assert model.training

            model.eval()
            assert not model.training

    def test_models_parameter_count(self):
        """测试模型参数数量"""
        lenet = LeNet5(10, 1)
        alexnet_model = AlexNetCIFAR(10, 3)
        vgg_model = vgg_cifar('vgg11', 10, 3)

        lenet_params = sum(p.numel() for p in lenet.parameters())
        alexnet_params = sum(p.numel() for p in alexnet_model.parameters())
        vgg_params = sum(p.numel() for p in vgg_model.parameters())

        assert lenet_params < alexnet_params < vgg_params

    def test_models_to_device(self):
        """测试模型设备迁移"""
        device = torch.device('cpu')
        model = LeNet5(10, 1).to(device)

        x = torch.randn(2, 1, 32, 32).to(device)
        output = model(x)

        assert output.device == device
```

**测试要点**：
- 训练/评估模式切换
- 参数数量对比
- 设备迁移

## 5. 性能测试

### 5.1 内存测试

**测试目标**：
- 测试模型内存占用
- 测试训练内存占用
- 测试推理内存占用

**测试方法**：
```python
import torch
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def test_memory_usage():
    """测试内存使用"""
    model = LeNet5(10, 1)
    
    # 测试前向传播内存
    x = torch.randn(32, 1, 32, 32)
    initial_memory = get_memory_usage()
    output = model(x)
    forward_memory = get_memory_usage()
    
    # 测试反向传播内存
    loss = output.sum()
    loss.backward()
    backward_memory = get_memory_usage()
    
    print(f"Initial memory: {initial_memory:.2f} MB")
    print(f"Forward memory: {forward_memory:.2f} MB")
    print(f"Backward memory: {backward_memory:.2f} MB")
```

### 5.2 速度测试

**测试目标**：
- 测试前向传播速度
- 测试反向传播速度
- 测试推理速度

**测试方法**：
```python
import time

def test_speed():
    """测试速度"""
    model = LeNet5(10, 1)
    x = torch.randn(32, 1, 32, 32)
    
    # 预热
    for _ in range(10):
        model(x)
    
    # 测试前向传播
    start = time.time()
    for _ in range(100):
        model(x)
    forward_time = time.time() - start
    
    print(f"Forward time: {forward_time:.3f}s")
    print(f"Average: {forward_time/100*1000:.2f}ms per batch")
```

### 5.3 精度测试

**测试目标**：
- 测试模型收敛性
- 测试最终准确率
- 测试训练稳定性

**测试方法**：
```python
def test_accuracy():
    """测试准确率"""
    train_loader, val_loader, test_loader = get_mnist_dataloaders(batch_size=64)
    model = LeNet5(10, 1)
    trainer = Trainer(model, train_loader, val_loader, test_loader)
    trainer.compile(optimizer='adam', lr=0.001)
    
    history = trainer.fit(epochs=5)
    
    # 检查训练是否收敛
    assert history['train_loss'][-1] < history['train_loss'][0]
    
    # 检查准确率
    test_loss, test_acc = trainer.test()
    assert test_acc > 90.0  # 至少90%准确率
```

## 6. 边界测试

### 6.1 输入边界

**测试用例**：

```python
def test_boundary_inputs():
    """测试边界输入"""
    model = LeNet5(10, 1)
    
    # 测试最小输入
    x_min = torch.randn(1, 1, 32, 32)
    output = model(x_min)
    assert output.shape == (1, 10)
    
    # 测试最大输入（受内存限制）
    x_max = torch.randn(256, 1, 32, 32)
    output = model(x_max)
    assert output.shape == (256, 10)
```

### 6.2 参数边界

**测试用例**：

```python
def test_boundary_parameters():
    """测试边界参数"""
    # 测试最小类别数
    model = LeNet5(num_classes=2, in_channels=1)
    assert model.fc3.out_features == 2
    
    # 测试最大类别数
    model = LeNet5(num_classes=1000, in_channels=1)
    assert model.fc3.out_features == 1000
```

## 7. 回归测试

### 7.1 已知问题

- 梯度消失问题
- 内存泄漏问题
- 数值不稳定问题

### 7.2 测试策略

- 每次代码修改后运行完整测试
- 关键修改后运行相关测试
- 定期运行性能测试

## 8. 测试覆盖率

### 8.1 覆盖率目标

- 代码覆盖率：>90%
- 分支覆盖率：>80%
- 函数覆盖率：100%

### 8.2 覆盖率检查

```bash
# 安装coverage
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 9. 持续集成

### 9.1 CI配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src
```

### 9.2 测试报告

- 生成JUnit XML报告
- 生成HTML覆盖率报告
- 上传到CI/CD平台

## 10. 测试维护

### 10.1 测试更新

- 代码修改后更新测试
- 新功能添加新测试
- 删除过时测试

### 10.2 测试文档

- 记录测试用例
- 记录测试结果
- 记录测试问题

## 11. 参考资料

1. [pytest官方文档](https://docs.pytest.org/)
2. [PyTorch测试最佳实践](https://pytorch.org/docs/stable/testing.html)
3. [Python测试覆盖率](https://coverage.readthedocs.io/)
