# 有限元分析基础 / Finite Element Analysis Basics

## 中文

**实现基础有限元分析，用于学习FEM核心概念。**

### 学习目标
- 理解有限元原理
- 掌握网格划分
- 学会应力分析

### 技术栈
- Python, numpy, scipy, matplotlib

### 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/01_cantilever_beam.py
python examples/02_plate_with_hole.py
python examples/03_3d_truss.py
python examples/04_mesh_convergence.py

# 运行测试
python -m pytest tests/
```

### 示例说明

| 示例 | 描述 |
|------|------|
| 01_cantilever_beam | 2D悬臂梁弯曲模拟，对比解析解 |
| 02_plate_with_hole | 带孔平板应力集中分析 |
| 03_3d_truss | 3D空间桁架分析 |
| 04_mesh_convergence | 网格收敛性研究 |

### FEM理论基础

**核心流程:** 几何模型 → 网格划分 → 刚度矩阵 → 求解 → 应力分析

**基本原理:**
- **离散化**: 将连续体划分为有限个单元
- **近似**: 用多项式形函数近似单元内的位移场
- **组装**: 将单元刚度矩阵组装为全局刚度矩阵
- **求解**: 求解线性方程组 K·U = F
- **后处理**: 从位移计算应变和应力

**控制方程:**
```
K · U = F
ε = B · u
σ = D · ε
```

其中:
- K: 全局刚度矩阵
- U: 节点位移向量
- F: 节点力向量
- ε: 应变向量
- σ: 应力向量
- B: 应变-位移矩阵
- D: 弹性矩阵

---

## English

**Implement basic finite element analysis for learning core FEM concepts.**

### Learning Goals
- Understand finite element principles
- Master mesh generation
- Learn stress analysis

### Tech Stack
- Python, numpy, scipy, matplotlib

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run examples
python examples/01_cantilever_beam.py
python examples/02_plate_with_hole.py
python examples/03_3d_truss.py
python examples/04_mesh_convergence.py

# Run tests
python -m pytest tests/
```

### Examples

| Example | Description |
|---------|-------------|
| 01_cantilever_beam | 2D cantilever beam bending, compare with analytical solution |
| 02_plate_with_hole | Stress concentration in plate with hole |
| 03_3d_truss | 3D space truss analysis |
| 04_mesh_convergence | Mesh convergence study |

### FEM Theory Background

**Core Workflow:** Geometry → Mesh → Stiffness Matrix → Solve → Stress Analysis

**Fundamental Principles:**
- **Discretization**: Divide continuous body into finite elements
- **Approximation**: Use polynomial shape functions to approximate displacement field
- **Assembly**: Assemble element stiffness matrices into global stiffness matrix
- **Solution**: Solve linear system K·U = F
- **Post-processing**: Calculate strain and stress from displacement

**Governing Equations:**
```
K · U = F
ε = B · u
σ = D · ε
```

Where:
- K: Global stiffness matrix
- U: Nodal displacement vector
- F: Nodal force vector
- ε: Strain vector
- σ: Stress vector
- B: Strain-displacement matrix
- D: Constitutive (elasticity) matrix

### Project Structure

```
finite-element/
├── src/
│   ├── __init__.py          # Package init
│   ├── mesh.py              # Mesh generation (triangular, quadrilateral, tetrahedral)
│   ├── elements.py          # Element stiffness matrices (CST, beam, truss, quad)
│   ├── assembly.py          # Global stiffness assembly and boundary conditions
│   ├── postprocess.py       # Stress calculation, Von Mises, visualization
│   └── visualize.py         # Plotting utilities
├── examples/
│   ├── 01_cantilever_beam.py       # 2D cantilever beam
│   ├── 02_plate_with_hole.py       # Plate with hole
│   ├── 03_3d_truss.py             # 3D truss analysis
│   └── 04_mesh_convergence.py     # Mesh convergence study
├── tests/
│   ├── test_mesh.py           # Mesh generation tests
│   ├── test_elements.py       # Element stiffness tests
│   ├── test_assembly.py       # Assembly tests
│   └── test_postprocess.py    # Post-processing tests
├── requirements.txt
└── README.md
```

### Key FEM Concepts Covered

1. **Mesh Generation**: 2D triangular/quadrilateral, 3D tetrahedral meshes
2. **Element Types**: CST (Constant Strain Triangle), beam, truss, quad elements
3. **Constitutive Models**: Plane stress, plane strain, 3D elasticity
4. **Assembly**: Direct stiffness method for global matrix construction
5. **Boundary Conditions**: Direct method and penalty method
6. **Stress Analysis**: Strain computation, stress recovery, Von Mises criterion
7. **Convergence**: Mesh refinement and convergence analysis

### References

- Zienkiewicz, O.C. & Taylor, R.L. "The Finite Element Method"
- Bathe, K.J. "Finite Element Procedures"
- Hughes, T.J.R. "The Finite Element Method: Linear Static and Dynamic FEM"
