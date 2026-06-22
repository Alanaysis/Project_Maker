# 网格处理算法

3D 网格处理算法库，支持网格简化、细分和平滑操作。

## 项目概述

本项目实现了三种核心网格处理算法：
- **网格简化**：通过边折叠减少网格面数
- **网格细分**：Loop 细分曲面，增加网格细节
- **网格平滑**：拉普拉斯平滑，改善网格质量

## 目录结构

```
mesh-processing/
├── src/
│   ├── __init__.py
│   ├── mesh_data.py      # 网格数据结构
│   ├── simplification.py # 网格简化算法
│   ├── subdivision.py    # 网格细分算法
│   └── smoothing.py      # 网格平滑算法
├── tests/
│   ├── __init__.py
│   └── test_mesh.py      # 单元测试
├── docs/                  # 文档
├── requirements.txt
└── README.md
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v
```

## 使用示例

```python
from src.mesh_data import TriangleMesh
from src.simplification import MeshSimplifier
from src.subdivision import LoopSubdivision
from src.smoothing import LaplacianSmoother

# 创建网格
mesh = TriangleMesh()
# ... 添加顶点和面 ...

# 简化网格
simplifier = MeshSimplifier()
simplified = simplifier.simplify(mesh, target_faces=100)

# 细分网格
subdivider = LoopSubdivision()
refined = subdivider.subdivide(mesh)

# 平滑网格
smoother = LaplacianSmoother()
smoothed = smoother.smooth(mesh, iterations=5)
```

## 文档

- [01-RESEARCH.md](docs/01-RESEARCH.md) - 研究背景
- [02-DESIGN.md](docs/02-DESIGN.md) - 设计文档
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试文档
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发记录
