# 空间划分算法

实现游戏引擎中的空间划分算法（BVH、Octree、BSP），用于加速碰撞检测和空间查询。

## 学习目标

- 理解空间划分原理
- 掌握 BVH 构建
- 学会碰撞检测优化

## 项目结构

```
spatial-partitioning/
├── include/           # 头文件
│   ├── AABB.h         # 轴对齐包围盒
│   ├── BVH.h          # BVH 树
│   ├── Octree.h       # 八叉树
│   ├── BSP.h          # BSP 树
│   └── Collision.h    # 碰撞检测
├── src/               # 源文件
│   ├── BVH.cpp
│   ├── Octree.cpp
│   └── BSP.cpp
├── tests/             # 测试文件
│   ├── test_bvh.cpp
│   ├── test_octree.cpp
│   └── test_bsp.cpp
├── examples/          # 示例程序
│   └── demo.cpp
├── docs/              # 文档
└── CMakeLists.txt     # 构建配置
```

## 构建与运行

```bash
mkdir build && cd build
cmake ..
make
./spatial_demo
```

## 核心算法

### 1. BVH (Bounding Volume Hierarchy)
- 自顶向下构建，按最长轴分割
- 使用 SAH (Surface Area Heuristic) 优化
- 适合动态场景

### 2. Octree (八叉树)
- 递归分割空间为 8 个子节点
- 适合静态场景
- 内存效率高

### 3. BSP (Binary Space Partitioning)
- 使用任意平面分割空间
- 适合室内场景
- 支持背面剔除

## 技术栈

- 语言：C++17
- 构建：CMake
- 测试：Google Test (可选)

## 参考资源

- Real-Time Collision Detection (Ericson)
- Game Physics Engine Development (Millington)
- Physically Based Rendering (Pharr)
