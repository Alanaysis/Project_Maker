# 开发文档：CNN图像分类

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- PyTorch 2.0+
- torchvision 0.15+
- matplotlib 3.7+
- numpy 1.24+

### 1.2 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov black flake8 mypy
```

### 1.3 IDE配置

**VSCode配置**：
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

**PyCharm配置**：
- 设置Python解释器
- 配置pytest
- 配置代码风格

## 2. 代码规范

### 2.1 命名规范

**变量命名**：
- 使用小写字母和下划线
- 避免单字母变量（除了循环变量）
- 使用有意义的变量名

```python
# 好
batch_size = 64
learning_rate = 0.001

# 不好
bs = 64
lr = 0.001
```

**函数命名**：
- 使用小写字母和下划线
- 使用动词开头
- 描述函数功能

```python
# 好
def train_epoch():
    pass

def evaluate_model():
    pass

# 不好
def train():
    pass

def eval():
    pass
```

**类命名**：
- 使用驼峰命名法
- 使用名词
- 描述类的功能

```python
# 好
class Conv2D:
    pass

class MaxPool2D:
    pass

# 不好
class conv2d:
    pass

class maxpool:
    pass
```

### 2.2 代码风格

**缩进**：
- 使用4个空格缩进
- 不要使用Tab

**行长度**：
- 最大行长度：88字符
- 使用换行符分割长行

**空行**：
- 函数之间：2个空行
- 类之间：2个空行
- 方法之间：1个空行

**导入顺序**：
1. 标准库
2. 第三方库
3. 本地库

```python
import os
import sys

import torch
import numpy as np

from src.layers import Conv2D
from src.lenet import LeNet5
```

### 2.3 注释规范

**文档字符串**：
```python
def train_epoch(self) -> Tuple[float, float]:
    """
    训练一个epoch

    返回：
        (平均损失, 准确率)
    """
    pass
```

**行内注释**：
```python
# 计算损失
loss = criterion(output, target)

# 更新参数
optimizer.step()
```

## 3. 版本控制

### 3.1 Git工作流

**分支策略**：
- `main`：主分支，稳定版本
- `develop`：开发分支
- `feature/*`：功能分支
- `bugfix/*`：修复分支

**提交规范**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`：新功能
- `fix`：修复
- `docs`：文档
- `style`：格式
- `refactor`：重构
- `test`：测试
- `chore`：构建

**示例**：
```
feat(layers): add Conv2D implementation

- Implement Conv2D layer with PyTorch
- Add unit tests for Conv2D
- Update documentation

Closes #123
```

### 3.2 Git配置

```bash
# 配置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 配置编辑器
git config --global core.editor vim

# 配置别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
```

## 4. 开发流程

### 4.1 功能开发

1. **创建功能分支**
   ```bash
   git checkout -b feature/new-layer
   ```

2. **编写代码**
   - 实现功能
   - 编写测试
   - 更新文档

3. **运行测试**
   ```bash
   pytest tests/ -v
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat(layers): add new layer implementation"
   ```

5. **推送分支**
   ```bash
   git push origin feature/new-layer
   ```

6. **创建Pull Request**
   - 描述功能
   - 关联Issue
   - 请求代码审查

### 4.2 Bug修复

1. **创建修复分支**
   ```bash
   git checkout -b bugfix/fix-conv2d
   ```

2. **修复Bug**
   - 重现问题
   - 分析原因
   - 修复代码

3. **编写测试**
   - 编写回归测试
   - 验证修复

4. **提交代码**
   ```bash
   git commit -m "fix(layers): fix Conv2D gradient computation"
   ```

### 4.3 代码审查

**审查要点**：
- 代码风格
- 功能正确性
- 测试覆盖
- 文档更新

**审查流程**：
1. 提交Pull Request
2. 自动化测试
3. 人工审查
4. 修改反馈
5. 合并代码

## 5. 测试开发

### 5.1 测试策略

**单元测试**：
- 测试单个函数/方法
- 测试边界条件
- 测试异常情况

**集成测试**：
- 测试组件协作
- 测试数据流
- 测试端到端

**性能测试**：
- 测试内存使用
- 测试计算速度
- 测试扩展性

### 5.2 测试编写

```python
import pytest
import torch

class TestConv2D:
    """测试Conv2D层"""

    def test_output_shape(self):
        """测试输出形状"""
        x = torch.randn(4, 3, 32, 32)
        conv = Conv2D(3, 16, kernel_size=3)
        output = conv(x)
        assert output.shape == (4, 16, 30, 30)

    def test_gradient(self):
        """测试梯度计算"""
        conv = Conv2D(3, 16, kernel_size=3)
        x = torch.randn(2, 3, 10, 10, requires_grad=True)
        output = conv(x)
        loss = output.sum()
        loss.backward()
        assert x.grad is not None

    @pytest.mark.parametrize("in_channels,out_channels", [
        (1, 6),
        (3, 16),
        (64, 128)
    ])
    def test_different_channels(self, in_channels, out_channels):
        """测试不同通道数"""
        x = torch.randn(2, in_channels, 10, 10)
        conv = Conv2D(in_channels, out_channels, kernel_size=3)
        output = conv(x)
        assert output.shape == (2, out_channels, 8, 8)
```

### 5.3 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_layers.py -v

# 运行带覆盖率
pytest tests/ --cov=src --cov-report=html

# 运行性能测试
pytest tests/ -v -m "performance"
```

## 6. 调试技巧

### 6.1 调试工具

**pdb调试器**：
```python
import pdb

def train_epoch():
    pdb.set_trace()  # 设置断点
    # 代码...
```

**print调试**：
```python
def forward(self, x):
    print(f"Input shape: {x.shape}")
    x = self.conv1(x)
    print(f"After conv1: {x.shape}")
    return x
```

**PyTorch调试**：
```python
# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")

# 检查中间结果
x = model.conv1(x)
print(f"conv1 output: min={x.min()}, max={x.max()}, mean={x.mean()}")
```

### 6.2 常见问题

**维度错误**：
```python
# 检查张量形状
print(f"x shape: {x.shape}")
print(f"weight shape: {self.weight.shape}")

# 检查矩阵乘法维度
assert x.shape[1] == self.weight.shape[1]
```

**梯度问题**：
```python
# 检查requires_grad
print(f"x requires_grad: {x.requires_grad}")

# 检查梯度是否存在
for name, param in model.named_parameters():
    print(f"{name}: grad={param.grad is not None}")
```

**内存问题**：
```python
# 检查内存使用
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# 释放不需要的张量
del x
torch.cuda.empty_cache()
```

## 7. 性能优化

### 7.1 代码优化

**使用inplace操作**：
```python
# 不好
x = torch.relu(x)
x = torch.dropout(x, p=0.5, training=self.training)

# 好
x = torch.relu_(x)
x = torch.dropout_(x, p=0.5, training=self.training)
```

**避免重复计算**：
```python
# 不好
for i in range(100):
    result = expensive_function(x)

# 好
result = expensive_function(x)
for i in range(100):
    use_result(result)
```

**使用向量化操作**：
```python
# 不好
for i in range(len(x)):
    y[i] = x[i] * 2

# 好
y = x * 2
```

### 7.2 内存优化

**使用梯度检查点**：
```python
from torch.utils.checkpoint import checkpoint

def forward(self, x):
    x = checkpoint(self.conv1, x)
    x = checkpoint(self.conv2, x)
    return x
```

**使用混合精度训练**：
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

with autocast():
    output = model(x)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 7.3 计算优化

**使用GPU**：
```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
x = x.to(device)
```

**使用DataParallel**：
```python
if torch.cuda.device_count() > 1:
    model = torch.nn.DataParallel(model)
```

**使用编译优化**：
```python
model = torch.compile(model)
```

## 8. 文档编写

### 8.1 代码文档

**模块文档**：
```python
"""
CNN Classification - 图像分类卷积神经网络

实现经典CNN架构：LeNet-5、AlexNet、VGG
用于MNIST图像分类任务
"""
```

**类文档**：
```python
class Conv2D(nn.Module):
    """
    2D卷积层实现

    参数：
        in_channels: 输入通道数
        out_channels: 输出通道数
        kernel_size: 卷积核大小
    """
```

**函数文档**：
```python
def forward(self, x: torch.Tensor) -> torch.Tensor:
    """
    前向传播

    参数：
        x: 输入张量，形状 (batch_size, in_channels, height, width)

    返回：
        输出张量，形状 (batch_size, out_channels, height_out, width_out)
    """
```

### 8.2 README编写

**结构**：
1. 项目标题
2. 项目描述
3. 安装说明
4. 使用说明
5. API文档
6. 贡献指南
7. 许可证

### 8.3 变更日志

```markdown
# Changelog

## [1.0.0] - 2024-01-01

### Added
- Conv2D layer implementation
- MaxPool2D layer implementation
- LeNet-5 model
- AlexNet model
- VGG model

### Changed
- None

### Deprecated
- None

### Removed
- None

### Fixed
- None
```

## 9. 部署发布

### 9.1 版本号

**语义化版本**：
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

**示例**：
- 1.0.0：初始版本
- 1.1.0：添加新功能
- 1.1.1：修复Bug

### 9.2 发布流程

1. **更新版本号**
   ```python
   __version__ = '1.1.0'
   ```

2. **更新变更日志**

3. **运行测试**
   ```bash
   pytest tests/ -v
   ```

4. **创建发布分支**
   ```bash
   git checkout -b release/1.1.0
   ```

5. **构建包**
   ```bash
   python setup.py sdist bdist_wheel
   ```

6. **上传到PyPI**
   ```bash
   twine upload dist/*
   ```

7. **创建Git标签**
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

### 9.3 持续集成

**GitHub Actions配置**：
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src
```

## 10. 贡献指南

### 10.1 如何贡献

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 10.2 代码审查

**审查要点**：
- 代码风格
- 功能正确性
- 测试覆盖
- 文档更新

### 10.3 行为准则

- 尊重他人
- 接受批评
- 关注问题
- 展示同理心

## 11. 参考资料

1. [Python代码规范](https://www.python.org/dev/peps/pep-0008/)
2. [Git工作流](https://www.atlassian.com/git/tutorials/comparing-workflows)
3. [PyTorch最佳实践](https://pytorch.org/tutorials/beginner/ptchg_tutorial.html)
4. [语义化版本](https://semver.org/)
