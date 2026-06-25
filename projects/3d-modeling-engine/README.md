# 3D 建模引擎 (3D Modeling Engine)

实现基础 3D 几何建模，支持基本图元创建和变换操作。

## 核心循环

```
几何创建 → 变换矩阵 → 网格构建 → 输出
```

## 学习目标

- 理解 3D 几何基础
- 掌握变换矩阵
- 学会网格操作

## 技术栈

- 主语言：C++17
- 框架：无
- 依赖：无

## 项目结构

```
3d-modeling-engine/
├── include/3d_engine/
│   ├── 3d_engine.h
│   ├── vec3.h
│   ├── mat4.h
│   ├── mesh.h
│   ├── transform.h
│   └── primitive.h
├── src/
├── tests/
├── examples/
└── docs/
```

## 快速开始

### 编译

```bash
cd projects/3d-modeling-engine
mkdir build && cd build
cmake ..
make
```

### 运行测试

```bash
ctest
```

### 运行示例

```bash
./demo_mesh
./demo_transform
```

## 核心功能

```cpp
#include "3d_engine/primitive.h"
#include "3d_engine/transform.h"

// 创建基本图元
auto cube = create_cube(2.0f);
auto sphere = create_sphere(16, 8);
auto cylinder = create_cylinder(0.5f, 1.0f, 16);

// 变换
auto rotated = Transform::rotate_y(cube, 0.785f);
auto scaled = Transform::scale(cube, 2.0f, 2.0f, 2.0f);
auto translated = Transform::translate(cube, 1.0f, 0.0f, 0.0f);
```
