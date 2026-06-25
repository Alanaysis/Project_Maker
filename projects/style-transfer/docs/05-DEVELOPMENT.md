# 神经风格迁移 - 开发文档

## 1. 开发环境

### 1.1 系统要求

- **操作系统**：Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**：3.8 或更高版本
- **内存**：8GB+ (推荐 16GB)
- **GPU**：NVIDIA GPU with CUDA 11.0+ (可选，但推荐)

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 或者手动安装
pip install torch torchvision numpy Pillow matplotlib pytest
```

### 1.3 项目结构

```
style-transfer/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装配置
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

## 2. 开发流程

### 2.1 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发功能
# ...

# 提交更改
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature

# 创建 Pull Request
# ...

# 合并到主分支
git checkout master
git merge feature/new-feature
```

### 2.2 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`：新功能
- `fix`：修复 bug
- `docs`：文档更新
- `style`：代码格式调整
- `refactor`：重构
- `test`：测试相关
- `chore`：构建/工具相关

**示例**：
```
feat(gram-matrix): 添加 Gram 矩阵计算模块

- 实现 gram_matrix 函数
- 实现 GramMatrix 类
- 添加单元测试

Closes #123
```

### 2.3 代码审查

1. **自我审查**：提交前自己检查代码
2. **同行审查**：让同事审查代码
3. **自动化检查**：使用 linter 和 formatter

## 3. 编码规范

### 3.1 Python 代码风格

遵循 PEP 8 规范：

```python
# 命名约定
class GramMatrix:  # 类名使用 CamelCase
    def __init__(self):  # 方法名使用 snake_case
        self.target_gram = None  # 变量名使用 snake_case

# 函数定义
def gram_matrix(
    features: torch.Tensor,
    normalize: bool = True,
) -> torch.Tensor:
    """函数文档字符串"""
    pass
```

### 3.2 类型注解

使用类型注解提高代码可读性：

```python
from typing import Optional, Union
import torch

def load_image(
    image_path: Union[str, Path],
    size: int = 512,
    device: str = "cpu",
) -> torch.Tensor:
    """加载并预处理图像"""
    pass
```

### 3.3 文档字符串

使用 Google 风格的文档字符串：

```python
def gram_matrix(features: torch.Tensor, normalize: bool = True) -> torch.Tensor:
    """计算特征图的 Gram 矩阵

    Args:
        features: 特征图，shape 为 (batch_size, channels, height, width)
        normalize: 是否对 Gram 矩阵进行归一化

    Returns:
        Gram 矩阵，shape 为 (batch_size, channels, channels)

    Raises:
        ValueError: 如果输入张量维度不正确

    示例：
        >>> import torch
        >>> from src import gram_matrix
        >>> features = torch.randn(1, 64, 32, 32)
        >>> gram = gram_matrix(features)
        >>> print(gram.shape)
        torch.Size([1, 64, 64])
    """
    pass
```

### 3.4 代码组织

```python
# 1. 导入顺序
import os  # 标准库
import sys

import torch  # 第三方库
import numpy as np

from src import gram_matrix  # 本地模块

# 2. 常量定义
VGG_LAYERS = {
    "conv1_1": 0,
    "relu1_1": 1,
}

# 3. 类定义
class StyleTransfer:
    """风格迁移类"""

    def __init__(self):
        pass

# 4. 函数定义
def load_image():
    pass
```

## 4. 测试开发

### 4.1 测试驱动开发 (TDD)

1. **编写测试**：先写测试用例
2. **运行测试**：测试应该失败
3. **编写代码**：实现功能
4. **运行测试**：测试应该通过
5. **重构代码**：优化代码结构

### 4.2 测试覆盖率

```bash
# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

### 4.3 测试数据管理

```python
# 使用 fixtures 共享测试数据
@pytest.fixture
def content_image():
    """创建内容图像"""
    return torch.randn(1, 3, 64, 64)

@pytest.fixture
def style_image():
    """创建风格图像"""
    return torch.randn(1, 3, 64, 64)
```

## 5. 调试技巧

### 5.1 PyTorch 调试

```python
# 打印张量信息
print(f"Shape: {tensor.shape}")
print(f"Dtype: {tensor.dtype}")
print(f"Device: {tensor.device}")
print(f"Min: {tensor.min()}, Max: {tensor.max()}")

# 检查梯度
print(f"Requires grad: {tensor.requires_grad}")
print(f"Grad: {tensor.grad}")

# 检查 NaN/Inf
print(f"Has NaN: {torch.isnan(tensor).any()}")
print(f"Has Inf: {torch.isinf(tensor).any()}")
```

### 5.2 损失调试

```python
# 打印损失信息
print(f"Content loss: {content_loss.item():.4f}")
print(f"Style loss: {style_loss.item():.4f}")
print(f"TV loss: {tv_loss.item():.4f}")
print(f"Total loss: {total_loss.item():.4f}")

# 检查损失变化
if step % 10 == 0:
    print(f"Step {step}: loss = {loss.item():.4f}")
```

### 5.3 可视化调试

```python
import matplotlib.pyplot as plt

# 可视化特征图
def visualize_features(features, title="Features"):
    """可视化特征图"""
    fig, axes = plt.subplots(4, 4, figsize=(10, 10))
    for i, ax in enumerate(axes.flat):
        if i < features.shape[1]:
            ax.imshow(features[0, i].cpu().numpy(), cmap='viridis')
        ax.axis('off')
    plt.title(title)
    plt.show()

# 可视化 Gram 矩阵
def visualize_gram(gram, title="Gram Matrix"):
    """可视化 Gram 矩阵"""
    plt.figure(figsize=(8, 8))
    plt.imshow(gram[0].cpu().numpy(), cmap='hot')
    plt.colorbar()
    plt.title(title)
    plt.show()
```

## 6. 性能优化

### 6.1 内存优化

```python
# 使用梯度检查点
from torch.utils.checkpoint import checkpoint

def forward_with_checkpoint(x):
    return checkpoint(self.layer, x)

# 清理不需要的张量
del intermediate_result
torch.cuda.empty_cache()

# 使用 no_grad() 禁用梯度计算
with torch.no_grad():
    output = model(input)
```

### 6.2 计算优化

```python
# 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
with autocast():
    output = model(input)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# 使用编译优化
model = torch.compile(model)
```

### 6.3 数据加载优化

```python
# 使用 DataLoader
from torch.utils.data import DataLoader

dataloader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4,
    pin_memory=True,
)
```

## 7. 错误处理

### 7.1 输入验证

```python
def validate_inputs(content_image, style_image):
    """验证输入图像"""
    if content_image.dim() != 4:
        raise ValueError(
            f"内容图像必须是 4D 张量，当前维度: {content_image.dim()}"
        )

    if style_image.dim() != 4:
        raise ValueError(
            f"风格图像必须是 4D 张量，当前维度: {style_image.dim()}"
        )

    if content_image.shape[1] != 3:
        raise ValueError(
            f"图像必须是 RGB 格式（3 个通道），当前通道数: {content_image.shape[1]}"
        )
```

### 7.2 异常处理

```python
try:
    output = transfer.transfer(content_image, style_image)
except ValueError as e:
    print(f"输入错误: {e}")
    sys.exit(1)
except RuntimeError as e:
    print(f"运行时错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"未知错误: {e}")
    sys.exit(1)
```

### 7.3 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 使用日志
logger.info("开始风格迁移")
logger.debug(f"内容图像形状: {content_image.shape}")
logger.warning("GPU 内存不足，使用 CPU")
logger.error("风格迁移失败", exc_info=True)
```

## 8. 文档编写

### 8.1 代码注释

```python
def gram_matrix(features: torch.Tensor, normalize: bool = True) -> torch.Tensor:
    """计算特征图的 Gram 矩阵

    Gram 矩阵用于捕捉图像的风格信息。它计算不同特征通道之间的相关性，
    这种相关性编码了图像的纹理和风格特征。

    Args:
        features: 特征图，shape 为 (batch_size, channels, height, width)
        normalize: 是否对 Gram 矩阵进行归一化

    Returns:
        Gram 矩阵，shape 为 (batch_size, channels, channels)

    示例：
        >>> import torch
        >>> from src import gram_matrix
        >>> features = torch.randn(1, 64, 32, 32)
        >>> gram = gram_matrix(features)
        >>> print(gram.shape)
        torch.Size([1, 64, 64])
    """
    # 重塑特征图：(batch_size, channels, height*width)
    # 这样每个通道的特征被展平为一维向量
    features_reshaped = features.view(batch_size, channels, -1)

    # 计算 Gram 矩阵：G = F * F^T
    # 对于每个 batch，计算 (C, H*W) @ (H*W, C) = (C, C)
    gram = torch.bmm(features_reshaped, features_reshaped.transpose(1, 2))

    return gram
```

### 8.2 README 编写

```markdown
# 项目名称

简短的项目描述

## 功能特性

- 功能 1
- 功能 2
- 功能 3

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

```python
from src import StyleTransfer

# 创建风格迁移器
transfer = StyleTransfer()

# 执行风格迁移
output = transfer.transfer(content, style)
```

## 贡献

欢迎贡献！请查看 CONTRIBUTING.md

## 许可证

MIT License
```

## 9. 部署

### 9.1 打包

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="style-transfer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "numpy>=1.19.0",
        "Pillow>=8.0.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Neural Style Transfer",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/style-transfer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
```

### 9.2 发布

```bash
# 构建包
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

### 9.3 Docker

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "examples/basic_transfer.py"]
```

## 10. 持续集成

### 10.1 GitHub Actions

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
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### 10.2 代码质量

```yaml
  lint:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install linters
      run: |
        pip install flake8 black isort

    - name: Run flake8
      run: flake8 src/ tests/

    - name: Run black
      run: black --check src/ tests/

    - name: Run isort
      run: isort --check-only src/ tests/
```

## 11. 常见问题

### 11.1 安装问题

**问题**：PyTorch 安装失败
**解决**：
```bash
# 使用官方安装命令
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 11.2 内存问题

**问题**：GPU 内存不足
**解决**：
```python
# 减小图像大小
content_image = load_image("content.jpg", size=256)

# 使用 CPU
transfer = StyleTransfer(device="cpu")

# 清理内存
torch.cuda.empty_cache()
```

### 11.3 性能问题

**问题**：风格迁移速度慢
**解决**：
```python
# 减少优化步数
output = transfer.transfer(content, style, num_steps=100)

# 使用更快的优化器
output = transfer.transfer(content, style, optimizer_type="adam", learning_rate=0.01)

# 减小图像大小
content = load_image("content.jpg", size=256)
```

## 12. 最佳实践

### 12.1 代码质量

- 使用类型注解
- 编写文档字符串
- 遵循 PEP 8
- 使用 linter 和 formatter

### 12.2 测试实践

- 测试驱动开发
- 高测试覆盖率
- 自动化测试
- 持续集成

### 12.3 版本控制

- 使用语义化版本
- 编写清晰的提交信息
- 使用分支策略
- 代码审查

### 12.4 文档实践

- 及时更新文档
- 使用示例代码
- 提供 API 文档
- 维护变更日志
