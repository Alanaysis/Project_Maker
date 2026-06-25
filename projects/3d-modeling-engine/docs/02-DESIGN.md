# 技术设计文档

## 1. 架构概述

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Vec3    │    │  Mat4    │    │  Mesh    │
│ (3D 向量) │    │(变换矩阵) │    │ (网格)   │
└──────────┘    └──────────┘    └──────────┘
       │                    │
       └───────┬────────────┘
               ▼
         ┌─────────────┐
         │  Transform  │
         │ (变换操作)   │
         └─────────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| Vec3 | 3D 向量 | `include/3d_engine/vec3.h` |
| Mat4 | 4x4 矩阵 | `include/3d_engine/mat4.h` |
| Mesh | 网格结构 | `include/3d_engine/mesh.h` |
| Transform | 变换操作 | `include/3d_engine/transform.h` |
| Primitive | 基础图元 | `include/3d_engine/primitive.h` |

## 2. 数据设计

### Vec3
```
x, y, z: float
```

### Mat4
```
m[4][4]: float
```

### Mesh
```
vertices: Vec3[]
faces: Face[]
```

## 3. 接口设计

```cpp
Vec3::dot(other) -> float
Vec3::cross(other) -> Vec3
Vec3::normalized() -> Vec3

Mat4::translation(tx, ty, tz)
Mat4::scaling(sx, sy, sz)
Mat4::rotation_x(angle)
Mat4::rotation_y(angle)
Mat4::rotation_z(angle)

Transform::translate(mesh, tx, ty, tz)
Transform::scale(mesh, sx, sy, sz)
Transform::rotate_x(mesh, angle)
```
