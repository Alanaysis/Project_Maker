# CAD Kernel Basics / CAD 内核基础

> A learning project implementing fundamental CAD kernel concepts in C++
> 用 C++ 实现基础 CAD 内核概念的学习项目

---

## Overview / 项目概述

This project implements the core components of a CAD (Computer-Aided Design) kernel from scratch.
It covers the fundamental algorithms and data structures used in commercial CAD systems like
OpenCASCADE, FreeCAD, and AutoCAD.

本项目从零实现 CAD（计算机辅助设计）内核的核心组件。涵盖商业 CAD 系统（如 OpenCASCADE、FreeCAD、AutoCAD）
中使用的基础算法和数据结构。

**Learning Path / 学习路径:**
```
几何定义 → 拓扑构建 → 布尔运算 → 模型输出
Geometric Definition → Topology Building → Boolean Operations → Model Output
```

---

## Learning Objectives / 学习目标

### English
- Understand B-rep (Boundary Representation) data structures
- Master solid modeling primitives and their geometric representations
- Implement boolean operations (union, intersection, difference)
- Learn surface-surface intersection algorithms
- Generate triangular meshes from B-rep geometry

### 中文
- 理解 B-rep（边界表示）数据结构
- 掌握实体建模基本体及其几何表示
- 实现布尔运算（并、交、差）
- 学习曲面相交算法
- 从 B-rep 几何生成三角网格

---

## CAD Kernel Theory Background / CAD 内核理论基础

### 1. B-rep (Boundary Representation) / 边界表示

B-rep is the standard way to represent 3D solids in CAD. A solid is defined by its
bounding surfaces (faces), which are bounded by edges, which are bounded by vertices.

B-rep 是 CAD 中表示 3D 实体的标准方式。实体由其边界曲面（面）定义，面由边界定，边由顶点界定。

**Hierarchy / 层次结构:**
```
Solid (实体)
 └── Shell (壳)
      └── Face (面)
           └── HalfEdge (半边)
                └── Edge (边)
                     └── Vertex (顶点)
```

**Euler's Formula / 欧拉公式:**
For a convex solid: **V - E + F = 2**
Where V = vertices, E = edges, F = faces.

### 2. Geometric Primitives / 几何基本体

| Primitive | Parametric Form | Parameters |
|-----------|----------------|------------|
| Line | P(u) = O + u·D | Origin, Direction |
| Plane | (P - O) · N = 0 | Origin, Normal |
| Cylinder | |P - proj_axis(P)| = R | Axis, Radius |
| Sphere | \|P - C\| = R | Center, Radius |
| Torus | (√(x²+y²) - R)² + z² = r² | Major/Minor Radius, Axis |
| Cone | |P - apex| · sin(θ) = |proj_axis(P)| | Apex, Axis, Angle |

### 3. Boolean Operations / 布尔运算

The three fundamental boolean operations:

| Operation | Symbol | Description |
|-----------|--------|-------------|
| Union | A ∪ B | Combined volume |
| Intersection | A ∩ B | Common volume |
| Difference | A - B | A minus B |

**Algorithm Steps:**
1. Compute face-face intersections
2. Classify regions as inside/outside each solid
3. Construct new topology from classified regions
4. Validate topological consistency

### 4. Mesh Generation / 网格生成

Converting B-rep to triangular meshes for rendering and analysis:

| Method | Use Case |
|--------|----------|
| Face triangulation | Planar faces |
| Surface sampling | Parametric surfaces |
| Loop subdivision | Mesh refinement |
| Marching Cubes | Implicit surfaces |

---

## Project Structure / 项目结构

```
cad-kernel/
├── src/
│   ├── brep.h           # B-rep data structures (Vertex, Edge, Face, Shell, Solid)
│   ├── geometry.h       # Geometric primitives (Line, Plane, Cylinder, Sphere, Torus, Cone)
│   ├── topology.h       # Topology management (Wiring, ShellBuilder, SolidBuilder)
│   ├── boolean.h        # Boolean operations (Union, Intersection, Difference)
│   ├── intersection.h   # Surface-surface intersection algorithms
│   └── mesh.h           # Mesh generation (triangulation, STL export)
├── examples/
│   ├── basic_solid_modeling.cpp   # Create and query basic solids
│   ├── boolean_operations.cpp     # Boolean operations demo
│   ├── surface_modeling.cpp       # Surface modeling demo
│   └── mesh_generation.cpp        # Mesh generation demo
├── tests/
│   └── test_cad_kernel.cpp        # Unit tests
├── README.md
├── Makefile
└── requirements.txt
```

---

## How to Build and Run / 如何构建和运行

### Prerequisites / 前置条件

- C++17 compatible compiler (g++ >= 7, clang++ >= 5)
- Make

### Build / 构建

```bash
# Build all examples and tests
make all

# Build only examples
make examples

# Build only tests
make tests
```

### Run Examples / 运行示例

```bash
# 1. Basic Solid Modeling
./examples/basic_solid_modeling

# 2. Boolean Operations
./examples/boolean_operations

# 3. Surface Modeling
./examples/surface_modeling

# 4. Mesh Generation
./examples/mesh_generation
```

### Run Tests / 运行测试

```bash
# Run all tests
make test

# Or directly:
./tests/test_cad_kernel
```

### Clean / 清理

```bash
make clean
```

---

## CAD Concepts Explained / CAD 概念详解

### What is a CAD Kernel? / 什么是 CAD 内核？

A CAD kernel is the mathematical and algorithmic core of a CAD system. It provides:
- Geometric modeling (points, curves, surfaces, solids)
- Topological modeling (connectivity between geometric entities)
- Boolean operations (combining solids)
- Mesh generation (for rendering and analysis)

CAD 内核是 CAD 系统的数学和算法核心。它提供：
- 几何建模（点、曲线、曲面、实体）
- 拓扑建模（几何实体间的连接关系）
- 布尔运算（实体组合）
- 网格生成（用于渲染和分析）

### B-rep vs CSG / B-rep 与 CSG

| Aspect | B-rep | CSG |
|--------|-------|-----|
| Representation | Boundary of solid | Tree of operations |
| Query speed | Fast (direct access) | Slow (traverse tree) |
| Editability | Hard (maintain consistency) | Easy (modify tree) |
| Use case | Direct modeling | Feature-based modeling |

### Euler Characteristic / 欧拉特征数

For any convex polyhedron: **V - E + F = 2**

This is a fundamental topological invariant. For solids with holes (like a torus):
**V - E + F = 2 - 2g** where g is the genus (number of holes).

### Surface-Surface Intersection / 曲面相交

Finding the intersection curve between two surfaces is one of the most important
operations in CAD. It's used for:
- Boolean operations (finding where faces meet)
- Filleting and blending
- Drafting and sectioning

Common intersection types:
- Plane-Plane → Line
- Plane-Sphere → Circle
- Plane-Cylinder → Ellipse or Circle
- Sphere-Sphere → Circle

---

## References / 参考

### Books / 书籍
1. "Geometric Modeling" by Marc Hoffmann - 几何建模经典教材
2. "Curves and Surfaces for CAGD" by Gerald Farin - 计算机辅助几何设计
3. "Real-Time Rendering" by Tomas Akenine-Möller - 实时渲染
4. "Computational Geometry: Algorithms and Applications" by de Berg et al.

### CAD Kernels / CAD 内核
- [OpenCASCADE](https://www.opencascade.com/) - Open source CAD kernel
- [FreeCAD](https://www.freecad.org/) - Open source CAD application
- [ACIS](https://www.siemens.com/) - Commercial CAD kernel (Siemens)
- [Parasolid](https://www.siemens.com/) - Commercial CAD kernel (Siemens)

### Papers / 论文
- Boubeke & Clementin, "A Classification of Surface-Surface Intersection Curves"
- Weiler & Atherton, "Hidden Surface Removal Using Polygon Area Sorting"
- Lorensen & Cline, "Marching Cubes: A High Resolution 3D Surface Construction Algorithm"

---

## License / 许可证

This project is for educational purposes only. MIT License.

本项目仅供学习用途。MIT 许可证。
