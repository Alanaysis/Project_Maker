# 场景图系统 (Scene Graph System)

一个用于组织和管理 3D 场景中物体层级关系的数据结构系统，支持变换层级传播和视锥体裁剪。

## 学习目标

- [ ] 理解场景图（Scene Graph）的核心架构设计
- [ ] 掌握变换层级（Transform Hierarchy）的计算原理
- [ ] 学会视锥裁剪（Frustum Culling）的实现方法
- [ ] 掌握 AABB 包围盒的计算和变换
- [ ] 理解四元数旋转的原理和应用
- [ ] 学会层级脏标记（Dirty Flag）优化模式

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| C++17 | 核心实现语言 | ★★★☆☆ |
| 线性代数 | 变换矩阵、四元数、向量运算 | ★★★★☆ |
| 树形数据结构 | 场景图节点层级管理 | ★★☆☆☆ |
| Gribb/Hartmann 方法 | 从 VP 矩阵提取视锥体平面 | ★★★☆☆ |
| Google Test | 单元测试框架 | ★☆☆☆☆ |

## 核心循环

```
场景图 → 遍历 → 变换计算 → 裁剪 → 渲染
  │        │         │         │       │
  │        │         │         │       └─ 收集可见节点列表
  │        │         │         └─ AABB 与视锥体相交测试
  │        │         └─ 自顶向下计算世界变换矩阵
  │        └─ 深度优先遍历场景树
  └─ 构建父子节点层级关系
```

## 重点难点

### 1. 变换层级（Transform Hierarchy）

**为什么重要**：这是场景图最核心的功能，允许子物体跟随父物体移动、旋转和缩放。

**关键代码**：`include/scene_node.h` - `update_world_transform()` 方法

**理解要点**：
- 世界变换 = 父节点世界变换 × 本节点局部变换
- 变换组合顺序：先缩放 → 再旋转 → 最后平移（TRS）
- 使用脏标记（Dirty Flag）避免不必要的重复计算

### 2. 视锥裁剪（Frustum Culling）

**为什么重要**：裁剪掉摄像机看不到的物体，大幅提升渲染性能。

**关键代码**：`include/bounds.h` - `Frustum::test_aabb()` 方法

**理解要点**：
- 视锥体由 6 个平面定义（近/远/左/右/上/下）
- 使用 Gribb/Hartmann 方法从 VP 矩阵提取平面
- p-vertex 优化：只需测试 AABB 在法向量方向最远的顶点

### 3. 包围盒变换

**为什么重要**：物体移动时，其包围盒也需要相应变换，用于碰撞检测和裁剪。

**关键代码**：`include/bounds.h` - `AABB::transform()` 方法

**理解要点**：
- 变换 AABB 的 8 个顶点，然后重新计算 AABB
- 层级包围盒：父节点的包围盒包含所有子节点的包围盒
- 包围盒变换比直接变换几何体快得多

### 4. 四元数旋转

**为什么重要**：避免万向锁（Gimbal Lock），支持平滑插值。

**关键代码**：`include/math_types.h` - `Quaternion` 结构体

**理解要点**：
- 四元数由 (x, y, z, w) 四个分量表示旋转
- 旋转向量：q * v * q^-1
- 组合旋转：四元数乘法
- 与欧拉角相比，没有万向锁问题

## 值得思考

### 1. 场景图 vs ECS（实体-组件-系统）

**背景**：现代游戏引擎中，场景图和 ECS 是两种主流的架构模式。

**权衡**：
- 场景图：直观的层级关系，适合有父子关系的场景（如骨骼动画）
- ECS：数据驱动，缓存友好，适合大量同类实体

**结论**：两者不矛盾，可以结合使用。场景图管理空间关系，ECS 管理组件逻辑。

### 2. 脏标记传播策略

**背景**：当一个节点变换改变时，需要更新其所有后代节点。

**权衡**：
- 自顶向下：每次更新从根节点开始，简单但可能多余
- 自底向上：只更新真正改变的分支，复杂但高效
- 混合策略：标记脏 → 按需更新（本项目采用的方式）

**结论**：混合策略是最佳实践，脏标记避免不必要的计算，按需更新减少即时开销。

### 3. 包围盒精度 vs 性能

**背景**：包围盒越精确，裁剪效果越好，但计算开销越大。

**权衡**：
- AABB：计算最快，但不够紧密（旋转后变大）
- OBB：更紧密，但相交测试更复杂
- 球体：旋转不变，但可能不够紧凑

**结论**：AABB 适合大多数场景，OBB 适合需要精确裁剪的场景。

## 快速开始

### 环境要求

- C++17 编译器（GCC 7+, Clang 5+, MSVC 2017+）
- CMake 3.14+
- Google Test（自动下载）

### 构建

```bash
cd projects/scene-graph
mkdir build && cd build
cmake .. -DBUILD_TESTS=ON
make -j$(nproc)
```

### 运行示例

```bash
./scene_graph_demo
```

### 运行测试

```bash
ctest --output-on-failure
```

## 项目结构

```
scene-graph/
├── include/
│   ├── math_types.h          # 数学类型（Vec3, Mat4, Quaternion）
│   ├── transform.h           # 变换组件
│   ├── bounds.h              # AABB 和 Frustum
│   ├── scene_node.h          # 场景图节点
│   └── scene_graph.h         # 场景图管理器和摄像机
├── src/
│   └── scene_graph.cpp       # 静态成员变量定义
├── tests/
│   ├── test_main.cpp         # 测试入口
│   ├── test_math_types.cpp   # 数学类型测试
│   ├── test_transform.cpp    # 变换测试
│   ├── test_bounds.cpp       # 包围盒和视锥体测试
│   ├── test_scene_node.cpp   # 场景节点测试
│   └── test_scene_graph.cpp  # 场景图和裁剪测试
├── examples/
│   └── demo.cpp              # 演示程序
├── docs/
│   ├── 01-RESEARCH.md        # 调研报告
│   ├── 02-DESIGN.md          # 设计文档
│   ├── 03-IMPLEMENTATION.md  # 实现细节
│   ├── 04-TESTING.md         # 测试策略
│   └── 05-DEVELOPMENT.md     # 开发指南
├── CMakeLists.txt            # 构建配置
├── README.md                 # 项目说明
└── LEARNING_NOTES.md         # 学习笔记
```

## 学习路径

1. **数学基础**（1-2天）
   - 阅读 `docs/01-RESEARCH.md` 了解场景图概念
   - 阅读 `include/math_types.h` 理解向量、矩阵、四元数

2. **变换层级**（2-3天）
   - 阅读 `docs/02-DESIGN.md` 了解架构设计
   - 阅读 `include/transform.h` 和 `include/scene_node.h`
   - 运行测试 `test_transform` 和 `test_scene_node`

3. **视锥裁剪**（2-3天）
   - 阅读 `include/bounds.h` 理解 AABB 和 Frustum
   - 运行测试 `test_bounds` 和 `test_scene_graph`
   - 运行 demo 查看裁剪效果

4. **综合实践**（1-2天）
   - 阅读 `docs/03-IMPLEMENTATION.md` 了解实现细节
   - 修改 demo 程序，添加自己的场景
   - 完成 `LEARNING_NOTES.md` 中的练习任务

## 相关资源

- [Game Programming Patterns - Scene Graph](https://gameprogrammingpatterns.com/component.html)
- [Gribb/Hartmann Frustum Plane Extraction](http://www.cs.otago.ac.nz/postgrads/alexis/planeExtraction.pdf)
- [Quaternions and Spatial Rotation (Wikipedia)](https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation)
- [Real-Time Rendering - Chapter 16: Scene Graph](http://www.realtimerendering.com/)
- [Introduction to 3D Game Programming with DirectX - Chapter 5](https://www.d3dcoder.net/)

## License

MIT License - 仅用于学习目的
