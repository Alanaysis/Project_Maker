# NeRF 开发文档

## 1. 开发概述

本文档描述 NeRF 项目的开发环境、开发流程、代码规范和发布流程。

### 1.1 开发目标

1. **学习目标**：理解 NeRF 原理，掌握体渲染和位置编码
2. **技术目标**：实现完整的 NeRF 训练和渲染流程
3. **质量目标**：代码清晰、测试完整、文档齐全

### 1.2 技术栈

- **语言**：Python 3.8+
- **框架**：PyTorch 2.0+
- **测试**：pytest
- **文档**：Markdown

## 2. 开发环境

### 2.1 环境要求

```bash
# Python 版本
Python >= 3.8

# 依赖包
torch >= 2.0.0
numpy >= 1.24.0
pytest >= 7.0.0
pytest-cov >= 4.0.0

# 可选依赖
matplotlib >= 3.7.0  # 可视化
tqdm >= 4.65.0       # 进度条
```

### 2.2 环境搭建

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install torch numpy pytest pytest-cov

# 或者使用 requirements.txt
pip install -r requirements.txt
```

### 2.3 项目结构

```
projects/nerf/
├── src/                        # 源代码
│   ├── __init__.py
│   ├── positional_encoding.py
│   ├── nerf_model.py
│   ├── volume_renderer.py
│   ├── ray_utils.py
│   ├── scene.py
│   └── trainer.py
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_positional_encoding.py
│   ├── test_nerf_model.py
│   ├── test_volume_renderer.py
│   └── test_ray_utils.py
├── examples/                   # 示例代码
│   ├── simple_demo.py
│   ├── visualize_positional_encoding.py
│   └── volume_rendering_demo.py
├── docs/                       # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 3. 开发流程

### 3.1 开发步骤

1. **需求分析**
   - 理解 NeRF 原理
   - 确定功能范围
   - 设计接口

2. **架构设计**
   - 模块划分
   - 接口定义
   - 数据流设计

3. **核心实现**
   - 位置编码
   - NeRF 模型
   - 体渲染器
   - 光线工具

4. **测试验证**
   - 单元测试
   - 集成测试
   - 物理测试

5. **文档编写**
   - 代码注释
   - API 文档
   - 使用示例

6. **优化改进**
   - 性能优化
   - 代码重构
   - 功能扩展

### 3.2 开发顺序

```
阶段 1：基础组件
├── 位置编码器
├── 基础 NeRF 模型（TinyNeRF）
└── 简单场景

阶段 2：核心功能
├── 完整 NeRF 模型
├── 体渲染器
└── 光线工具

阶段 3：训练流程
├── 训练器
├── 数据生成
└── 评估指标

阶段 4：优化完善
├── 分层采样
├── 性能优化
└── 文档完善
```

### 3.3 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/positional-encoding

# 开发和提交
git add .
git commit -m "feat: 实现位置编码器"

# 合并到主分支
git checkout master
git merge feature/positional-encoding

# 推送
git push origin master
```

## 4. 代码规范

### 4.1 Python 代码规范

#### 命名规范

```python
# 模块名：小写 + 下划线
positional_encoding.py
nerf_model.py

# 类名：大驼峰
class PositionalEncoding:
class NeRFModel:

# 函数名：小写 + 下划线
def sample_points_along_rays():
def volume_render():

# 变量名：小写 + 下划线
num_samples = 64
learning_rate = 5e-4

# 常量：大写 + 下划线
MAX_NUM_SAMPLES = 128
DEFAULT_LEARNING_RATE = 5e-4
```

#### 代码格式

```python
# 使用 4 空格缩进
def function():
    if condition:
        do_something()

# 行长度限制 88 字符
long_variable = some_function(
    argument1, argument2, argument3
)

# 空行分隔函数和类
class MyClass:
    pass


def my_function():
    pass
```

#### 导入规范

```python
# 标准库
import os
import sys
from typing import Optional, Tuple

# 第三方库
import torch
import torch.nn as nn
import numpy as np

# 本地模块
from .positional_encoding import PositionalEncoding
from .nerf_model import NeRFModel
```

### 4.2 文档规范

#### 模块文档

```python
"""
模块名称
========

模块描述，包括：
- 主要功能
- 核心概念
- 使用示例

典型用法:
    >>> from module import Class
    >>> obj = Class()
    >>> result = obj.method()
"""
```

#### 类文档

```python
class NeRFModel(nn.Module):
    """
    NeRF 核心模型

    使用 MLP 表示连续的3D场景。

    参数:
        pos_encoding_dim: 位置编码后的维度
        dir_encoding_dim: 方向编码后的维度
        hidden_dim: 隐藏层维度
        num_layers: 层数

    示例:
        >>> model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
        >>> density, color = model(positions, directions)
    """
```

#### 函数文档

```python
def sample_points_along_rays(
    rays_o: torch.Tensor,
    rays_d: torch.Tensor,
    near: float,
    far: float,
    num_samples: int,
    perturb: bool = True,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    沿光线采样3D点

    参数:
        rays_o: 光线原点 (num_rays, 3)
        rays_d: 光线方向 (num_rays, 3)
        near: 近裁剪面距离
        far: 远裁剪面距离
        num_samples: 每条光线的采样点数
        perturb: 是否添加随机扰动

    返回:
        points: 采样点坐标 (num_rays, num_samples, 3)
        distances: 沿光线的距离 (num_rays, num_samples)

    示例:
        >>> points, distances = sample_points_along_rays(
        ...     rays_o, rays_d, near=2.0, far=6.0, num_samples=64
        ... )
    """
```

### 4.3 注释规范

```python
# 行内注释：解释复杂逻辑
result = some_complex_calculation()  # 计算累积透射率

# 块注释：解释代码块功能
# ===== 计算 alpha 不透明度 =====
# α = 1 - exp(-σ * δ)
alpha = 1 - torch.exp(-densities * deltas)

# TODO 注释：标记待完成
# TODO: 实现重要性采样

# FIXME 注释：标记已知问题
# FIXME: 处理边界情况
```

## 5. 测试流程

### 5.1 测试策略

```python
# 单元测试：测试单个函数/类
def test_positional_encoding():
    pe = PositionalEncoding(input_dim=3, num_freqs=10)
    x = torch.randn(10, 3)
    encoded = pe(x)
    assert encoded.shape == (10, 63)

# 集成测试：测试组件协作
def test_full_pipeline():
    pos_enc = PositionalEncoding()
    model = NeRFModel()
    renderer = VolumeRenderer()
    # ...

# 物理测试：验证物理正确性
def test_energy_conservation():
    renderer = VolumeRenderer(white_background=False)
    densities = torch.zeros(1, 32, 1)
    colors, _, _ = renderer(torch.randn(1, 32, 3), densities, distances)
    assert torch.allclose(colors, torch.zeros_like(colors), atol=1e-5)
```

### 5.2 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_positional_encoding.py -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=src --cov-report=html

# 运行特定测试类
pytest tests/test_positional_encoding.py::TestPositionalEncoding -v
```

### 5.3 测试检查清单

- [ ] 所有测试通过
- [ ] 覆盖率达标（>80%）
- [ ] 无内存泄漏
- [ ] 无数值不稳定
- [ ] 边界情况处理

## 6. 调试技巧

### 6.1 常见问题

#### 训练不收敛

```python
# 检查学习率
print(f"学习率: {optimizer.param_groups[0]['lr']}")

# 检查损失
print(f"损失: {loss.item()}")
print(f"PSNR: {-10 * torch.log10(loss).item()}")

# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")
```

#### 数值不稳定

```python
# 检查 NaN
if torch.isnan(tensor).any():
    print("发现 NaN!")
    print(f"位置: {torch.isnan(tensor).nonzero()}")

# 检查 Inf
if torch.isinf(tensor).any():
    print("发现 Inf!")

# 使用 eps 避免 log(0)
eps = 1e-10
log_value = torch.log(value + eps)
```

#### 内存问题

```python
# 监控内存
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"内存使用: {memory_mb:.2f} MB")

# 清空缓存
torch.cuda.empty_cache()

# 分块处理
for i in range(0, len(data), chunk_size):
    chunk = data[i:i + chunk_size]
    result = process(chunk)
```

### 6.2 调试工具

```python
# 打印张量信息
def debug_tensor(tensor, name="tensor"):
    print(f"{name}:")
    print(f"  形状: {tensor.shape}")
    print(f"  类型: {tensor.dtype}")
    print(f"  设备: {tensor.device}")
    print(f"  范围: [{tensor.min():.4f}, {tensor.max():.4f}]")
    print(f"  均值: {tensor.mean():.4f}")
    print(f"  标准差: {tensor.std():.4f}")
    print(f"  NaN: {torch.isnan(tensor).any()}")
    print(f"  Inf: {torch.isinf(tensor).any()}")

# 使用示例
debug_tensor(encoded, "encoded")
debug_tensor(density, "density")
debug_tensor(color, "color")
```

### 6.3 可视化调试

```python
import matplotlib.pyplot as plt

# 可视化图像
def visualize_image(image, title="Image"):
    plt.figure(figsize=(8, 8))
    plt.imshow(image)
    plt.title(title)
    plt.axis('off')
    plt.show()

# 可视化深度图
def visualize_depth(depth, title="Depth"):
    plt.figure(figsize=(8, 8))
    plt.imshow(depth, cmap='plasma')
    plt.colorbar()
    plt.title(title)
    plt.show()

# 可视化损失曲线
def plot_loss(history):
    plt.figure(figsize=(10, 5))
    plt.plot(history['train_loss'], label='Train')
    plt.plot(history['val_loss'], label='Validation')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
```

## 7. 性能优化

### 7.1 代码优化

```python
# 使用向量化操作
# 差的写法
result = []
for i in range(n):
    result.append(compute(i))
result = torch.stack(result)

# 好的写法
indices = torch.arange(n)
result = compute(indices)

# 使用就地操作
# 差的写法
tensor = tensor + 1

# 好的写法
tensor.add_(1)

# 避免重复计算
# 差的写法
for i in range(n):
    result = expensive_computation(input)

# 好的写法
cached = expensive_computation(input)
for i in range(n):
    result = cached
```

### 7.2 内存优化

```python
# 使用 torch.no_grad()
with torch.no_grad():
    result = model(input)

# 使用分块处理
def process_chunks(data, chunk_size=1024):
    results = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        result = process(chunk)
        results.append(result)
    return torch.cat(results)

# 及时释放不需要的张量
del intermediate_tensor
torch.cuda.empty_cache()
```

### 7.3 GPU 优化

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

# 使用 DataLoader 的 num_workers
dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,
    pin_memory=True,
)
```

## 8. 代码审查

### 8.1 审查清单

- [ ] 代码符合规范
- [ ] 注释清晰完整
- [ ] 测试覆盖充分
- [ ] 无明显 bug
- [ ] 性能可接受
- [ ] 文档齐全

### 8.2 常见问题

1. **命名不清晰**
   ```python
   # 差
   x = compute(x, y, z)
   
   # 好
   positions = compute_positions(points, directions, distances)
   ```

2. **缺少类型提示**
   ```python
   # 差
   def compute(x, y):
       return x + y
   
   # 好
   def compute(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
       return x + y
   ```

3. **魔法数字**
   ```python
   # 差
   result = x * 63 + 27
   
   # 好
   POS_ENCODING_DIM = 63
   DIR_ENCODING_DIM = 27
   result = x * POS_ENCODING_DIM + DIR_ENCODING_DIM
   ```

## 9. 发布流程

### 9.1 版本管理

```python
# 版本号格式：主版本.次版本.修订号
__version__ = "1.0.0"

# 版本号规则
# 主版本：不兼容的 API 变更
# 次版本：向下兼容的功能性新增
# 修订号：向下兼容的问题修正
```

### 9.2 发布检查清单

- [ ] 所有测试通过
- [ ] 文档更新
- [ ] 版本号更新
- [ ] CHANGELOG 更新
- [ ] 无已知 bug

### 9.3 发布步骤

```bash
# 1. 更新版本号
# 在 src/__init__.py 中更新 __version__

# 2. 运行测试
pytest tests/ -v

# 3. 生成文档
# 手动更新文档

# 4. 提交代码
git add .
git commit -m "release: v1.0.0"
git tag v1.0.0

# 5. 推送
git push origin master --tags
```

## 10. 持续集成

### 10.1 CI 配置

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

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
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### 10.2 代码质量检查

```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install linters
      run: |
        pip install flake8 black mypy
    
    - name: Run flake8
      run: flake8 src/ tests/
    
    - name: Run black
      run: black --check src/ tests/
    
    - name: Run mypy
      run: mypy src/
```

## 11. 学习资源

### 11.1 NeRF 学习

1. **论文**
   - NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis
   - Mip-NeRF: A Multiscale Representation for Anti-Aliasing Neural Radiance Fields
   - Instant-NGP: Instant Neural Graphics Primitives

2. **代码库**
   - 官方 NeRF: https://github.com/bmild/nerf
   - NeRF-pytorch: https://github.com/yenchenlin/nerf-pytorch
   - Instant-NGP: https://github.com/NVlabs/instant-ngp

3. **教程**
   - NeRF 论文解读（多篇博客）
   - NeRF 实现教程（YouTube）
   - NeRF 入门指南（GitHub）

### 11.2 PyTorch 学习

1. **官方文档**
   - PyTorch 教程：https://pytorch.org/tutorials/
   - PyTorch 文档：https://pytorch.org/docs/

2. **学习资源**
   - PyTorch 官方示例
   - PyTorch Lightning
   - Hugging Face

### 11.3 3D 视觉学习

1. **计算机视觉**
   - 多视图几何
   - Structure from Motion
   - 深度估计

2. **神经渲染**
   - Neural Rendering
   - Differentiable Rendering
   - Neural Scene Representation

## 12. 常见问题

### 12.1 安装问题

**问题**：PyTorch 安装失败

**解决方案**：
```bash
# 使用官方安装命令
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或者使用 conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

**问题**：CUDA 不可用

**解决方案**：
```python
import torch
print(f"CUDA 可用: {torch.cuda.is_available()}")
print(f"CUDA 版本: {torch.version.cuda}")

# 如果不可用，使用 CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

### 12.2 运行问题

**问题**：内存不足

**解决方案**：
```python
# 减小批量大小
batch_size = 512  # 原来是 4096

# 使用分块处理
chunk_size = 512

# 降低分辨率
height, width = 64, 64  # 原来是 800, 800
```

**问题**：训练不收敛

**解决方案**：
```python
# 降低学习率
learning_rate = 1e-4  # 原来是 5e-4

# 增加训练时间
num_epochs = 200  # 原来是 100

# 检查数据
print(f"数据范围: [{data.min()}, {data.max()}]")
```

### 12.3 测试问题

**问题**：测试失败

**解决方案**：
```bash
# 查看详细错误
pytest tests/ -v --tb=long

# 运行特定测试
pytest tests/test_positional_encoding.py::TestPositionalEncoding::test_output_shape -v

# 调试测试
pytest tests/ -v --pdb
```

## 13. 总结

### 13.1 开发流程

1. **需求分析**：理解 NeRF 原理，确定功能范围
2. **架构设计**：模块划分，接口定义
3. **核心实现**：位置编码、NeRF 模型、体渲染器
4. **测试验证**：单元测试、集成测试、物理测试
5. **文档编写**：代码注释、API 文档、使用示例
6. **优化改进**：性能优化、代码重构

### 13.2 关键点

1. **代码规范**：命名清晰、注释完整、类型提示
2. **测试覆盖**：单元测试、集成测试、物理测试
3. **文档齐全**：代码注释、API 文档、使用示例
4. **性能优化**：向量化、内存管理、GPU 优化

### 13.3 学习建议

1. **从小开始**：先实现 Tiny NeRF
2. **逐步验证**：每个组件单独测试
3. **可视化调试**：检查中间结果
4. **参考实现**：对比官方代码
5. **理解原理**：不只是复制代码

## 14. 附录

### 14.1 快速参考

```bash
# 环境搭建
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 运行示例
python examples/simple_demo.py

# 生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html
```

### 14.2 代码模板

```python
# 新模块模板
"""
模块名称
========

模块描述
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple


class MyClass(nn.Module):
    """
    类描述

    参数:
        param1: 参数1描述
        param2: 参数2描述
    """

    def __init__(self, param1: int, param2: float = 1.0):
        super().__init__()
        self.param1 = param1
        self.param2 = param2

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数:
            x: 输入张量

        返回:
            输出张量
        """
        # 实现
        return x


def my_function(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    函数描述

    参数:
        x: 参数1
        y: 参数2

    返回:
        结果
    """
    # 实现
    return x + y
```

### 14.3 测试模板

```python
# 新测试模板
"""
模块测试
========

测试模块功能
"""

import pytest
import torch
from projects.nerf.src.module import MyClass


class TestMyClass:
    """MyClass 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        obj = MyClass(param1=10)
        x = torch.randn(5, 10)
        output = obj(x)
        assert output.shape == (5, 10)

    def test_gradient_flow(self):
        """测试梯度流"""
        obj = MyClass(param1=10)
        x = torch.randn(5, 10, requires_grad=True)
        output = obj(x)
        loss = output.sum()
        loss.backward()
        assert x.grad is not None

    def test_device_compatibility(self):
        """测试设备兼容性"""
        if torch.cuda.is_available():
            obj = MyClass(param1=10).cuda()
            x = torch.randn(5, 10).cuda()
            output = obj(x)
            assert output.is_cuda


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```
