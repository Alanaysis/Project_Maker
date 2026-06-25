# NeRF 神经辐射场

实现 NeRF (Neural Radiance Fields)，理解神经辐射场和 3D 重建。

## 项目简介

NeRF 是一种使用神经网络表示 3D 场景的方法，能够从 2D 图像生成新视角。

**核心思想**：
- 使用 MLP 网络表示连续的 3D 辐射场
- 输入：3D 坐标 + 观察方向
- 输出：颜色 + 体积密度
- 通过体渲染合成 2D 图像

**核心流程**：
```
相机光线 → 采样点 → 位置编码 → MLP → 颜色/密度 → 体渲染 → 图像
```

## 学习目标

- 理解 NeRF 原理
- 掌握体渲染技术
- 学会位置编码

## 技术栈

- **语言**：Python
- **框架**：PyTorch
- **测试**：pytest

## 项目结构

```
nerf/
├── src/                        # 源代码
│   ├── __init__.py
│   ├── positional_encoding.py  # 位置编码
│   ├── nerf_model.py           # NeRF 模型
│   ├── volume_renderer.py      # 体渲染器
│   ├── ray_utils.py            # 光线工具
│   ├── scene.py                # 简单场景
│   └── trainer.py              # 训练器
├── tests/                      # 测试代码
├── examples/                   # 示例代码
├── docs/                       # 文档
├── README.md                   # 项目说明
└── LEARNING_NOTES.md           # 学习笔记
```

## 核心组件

### 1. 位置编码 (PositionalEncoding)

将低维坐标映射到高维空间，使 MLP 能够学习高频细节。

```python
from src import PositionalEncoding

pe = PositionalEncoding(input_dim=3, num_freqs=10)
encoded = pe(positions)  # (N, 3) -> (N, 63)
```

### 2. NeRF 模型 (NeRFModel)

多层感知机，预测 3D 点的颜色和密度。

```python
from src import NeRFModel

model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
density, color = model(pos_encoded, dir_encoded)
```

### 3. 体渲染器 (VolumeRenderer)

将 3D 信息合成 2D 图像。

```python
from src import VolumeRenderer

renderer = VolumeRenderer(white_background=True)
pixel_colors, depth_map, extras = renderer(colors, densities, distances)
```

### 4. 光线工具 (RayGenerator)

生成相机光线和采样点。

```python
from src import RayGenerator, sample_points_along_rays

generator = RayGenerator(height=64, width=64, focal_length=32.0)
rays_o, rays_d = generator.get_rays_simple()
points, distances = sample_points_along_rays(rays_o, rays_d, near=2.0, far=6.0)
```

## 快速开始

### 安装依赖

```bash
pip install torch numpy pytest
```

### 运行示例

```bash
# 简单演示
python examples/simple_demo.py

# 位置编码可视化
python examples/visualize_positional_encoding.py

# 体渲染演示
python examples/volume_rendering_demo.py
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=src
```

## 训练流程

```python
from src import (
    PositionalEncoding, NeRFModel, VolumeRenderer,
    RayGenerator, SphereScene, NeRFTrainer
)

# 1. 创建场景
scene = SphereScene(radius=1.0, color=(1.0, 0.0, 0.0))

# 2. 生成训练数据
generator = RayGenerator(height=64, width=64, focal_length=32.0)
# ... 生成多视角数据

# 3. 创建模型
pos_encoding = PositionalEncoding(input_dim=3, num_freqs=10)
dir_encoding = PositionalEncoding(input_dim=3, num_freqs=6)
model = NeRFModel(
    pos_encoding_dim=pos_encoding.output_dim,
    dir_encoding_dim=dir_encoding.output_dim,
)
renderer = VolumeRenderer(white_background=True)

# 4. 训练
trainer = NeRFTrainer(model, pos_encoding, dir_encoding, renderer)
trainer.train(train_rays_o, train_rays_d, train_colors, num_epochs=100)

# 5. 渲染新视角
image = trainer.render_image(rays_o_new, rays_d_new)
```

## 文档

- [01-RESEARCH.md](docs/01-RESEARCH.md) - 研究笔记
- [02-DESIGN.md](docs/02-DESIGN.md) - 设计文档
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现文档
- [04-TESTING.md](docs/04-TESTING.md) - 测试文档
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发文档

## 参考资源

### 论文

1. NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis (ECCV 2020)
2. Mip-NeRF: A Multiscale Representation for Anti-Aliasing Neural Radiance Fields (ICCV 2021)
3. Instant-NGP: Instant Neural Graphics Primitives with a Multiresolution Hash Encoding (SIGGRAPH 2022)

### 代码库

1. 官方 NeRF: https://github.com/bmild/nerf
2. NeRF-pytorch: https://github.com/yenchenlin/nerf-pytorch

## 许可证

MIT License
