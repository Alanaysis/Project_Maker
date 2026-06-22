# 场景图系统 - 设计文档

## 1. 架构概述

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                       SceneGraph                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │
│  │  Root   │  │ Camera  │  │ CullResult│ │  traverse() │  │
│  │  Node   │  │         │  │         │  │  cull()     │  │
│  └────┬────┘  └─────────┘  └─────────┘  └─────────────┘  │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   SceneNode                          │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │   │
│  │  │ Transform │  │   AABB    │  │  Renderable   │   │   │
│  │  │ position  │  │   min     │  │  (interface)  │   │   │
│  │  │ rotation  │  │   max     │  │               │   │   │
│  │  │ scale     │  │           │  │               │   │   │
│  │  └───────────┘  └───────────┘  └───────────────┘   │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │              Children (vector)                │  │   │
│  │  │  [child1] [child2] [child3] ...               │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
scene-graph/
├── include/
│   ├── math_types.h      # 数学基础（Vec3, Mat4, Quaternion）
│   ├── transform.h       # 变换组件
│   ├── bounds.h          # AABB 和 Frustum
│   ├── scene_node.h      # 场景图节点
│   └── scene_graph.h     # 场景图管理器
├── src/
│   └── scene_graph.cpp   # 静态成员定义
└── tests/
    └── test_*.cpp        # 测试文件
```

### 1.3 依赖关系

```
math_types.h
    ↓
transform.h
    ↓
bounds.h
    ↓
scene_node.h
    ↓
scene_graph.h
```

---

## 2. 核心类设计

### 2.1 MathTypes - 数学类型

```
┌─────────────────────────────────────────────────┐
│                  MathTypes                        │
├─────────────────────────────────────────────────┤
│ Vec3                                             │
│   - x, y, z: float                              │
│   + operator+,-,*,/: Vec3                       │
│   + dot(): float                                │
│   + cross(): Vec3                               │
│   + length(): float                             │
│   + normalized(): Vec3                          │
├─────────────────────────────────────────────────┤
│ Vec4                                             │
│   - x, y, z, w: float                          │
│   + xyz(): Vec3                                 │
│   + to_vec3(): Vec3                             │
├─────────────────────────────────────────────────┤
│ Quaternion                                       │
│   - x, y, z, w: float                          │
│   + from_euler(): Quaternion                    │
│   + from_axis_angle(): Quaternion               │
│   + operator*: Quaternion                       │
│   + conjugate(): Quaternion                     │
│   + rotate(): Vec3                              │
├─────────────────────────────────────────────────┤
│ Mat4                                             │
│   - m: array<float, 16>                        │
│   + at(row, col): float&                       │
│   + translation(): Mat4                         │
│   + scaling(): Mat4                             │
│   + rotation(): Mat4                            │
│   + perspective(): Mat4                         │
│   + look_at(): Mat4                             │
│   + operator*: Mat4                             │
│   + transform_point(): Vec3                     │
│   + transform_direction(): Vec3                 │
│   + inverse(): Mat4                             │
│   + determinant(): float                        │
└─────────────────────────────────────────────────┘
```

### 2.2 Transform - 变换组件

```
┌─────────────────────────────────────────────────┐
│                 Transform                        │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - position: Vec3                              │
│   - rotation: Quaternion                        │
│   - scale: Vec3                                 │
├─────────────────────────────────────────────────┤
│ 方法:                                            │
│   + get_local_matrix(): Mat4                    │
│   + set_rotation_euler(): void                  │
│   + rotate_axis(): void                         │
│   + translate(): void                           │
│   + scale_by(): void                            │
│   + forward(): Vec3                             │
│   + right(): Vec3                               │
│   + up(): Vec3                                  │
└─────────────────────────────────────────────────┘
```

### 2.3 Bounds - 包围盒和视锥体

```
┌─────────────────────────────────────────────────┐
│                    AABB                          │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - min: Vec3                                   │
│   - max: Vec3                                   │
├─────────────────────────────────────────────────┤
│ 方法:                                            │
│   + from_center_size(): AABB                    │
│   + expand(): void                              │
│   + merge(): AABB                               │
│   + center(): Vec3                              │
│   + contains(): bool                            │
│   + intersects(): bool                          │
│   + transform(): AABB                           │
│   + volume(): float                             │
│   + surface_area(): float                       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                    Plane                         │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - normal: Vec3                                │
│   - distance: float                             │
├─────────────────────────────────────────────────┤
│ 方法:                                            │
│   + from_points(): Plane                        │
│   + distance_to(): float                        │
│   + normalized(): Plane                         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                   Frustum                        │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - planes[6]: Plane                            │
├─────────────────────────────────────────────────┤
│ 方法:                                            │
│   + from_view_projection(): Frustum             │
│   + test_aabb(): bool                           │
│   + test_point(): bool                          │
│   + test_sphere(): bool                         │
└─────────────────────────────────────────────────┘
```

### 2.4 SceneNode - 场景图节点

```
┌─────────────────────────────────────────────────┐
│                  SceneNode                       │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - name: string                                │
│   - id: uint64_t                                │
│   - visible: bool                               │
│   - transform: Transform                        │
│   - renderable: RenderablePtr                   │
│   - parent: weak_ptr<SceneNode>                 │
│   - children: vector<SceneNodePtr>              │
│   - world_matrix: Mat4 (mutable)                │
│   - world_bounds: AABB (mutable)                │
│   - dirty flags (mutable)                       │
├─────────────────────────────────────────────────┤
│ 层级管理:                                        │
│   + add_child(): void                           │
│   + remove_child(): bool                        │
│   + find(): SceneNodePtr                        │
│   + get_parent(): SceneNodePtr                  │
│   + get_children(): vector<SceneNodePtr>        │
├─────────────────────────────────────────────────┤
│ 变换管理:                                        │
│   + get_transform(): Transform&                 │
│   + set_transform(): void                       │
│   + get_world_matrix(): Mat4                    │
│   + get_world_position(): Vec3                  │
│   + update_transforms(): void                   │
├─────────────────────────────────────────────────┤
│ 包围盒管理:                                      │
│   + set_renderable(): void                      │
│   + get_world_bounds(): AABB                    │
│   + set_local_bounds(): void                    │
├─────────────────────────────────────────────────┤
│ 遍历:                                            │
│   + traverse_dfs(): void                        │
│   + total_node_count(): size_t                  │
│   + get_depth(): int                            │
└─────────────────────────────────────────────────┘
```

### 2.5 SceneGraph - 场景图管理器

```
┌─────────────────────────────────────────────────┐
│                  SceneGraph                      │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - root: SceneNodePtr                          │
│   - camera: Camera                              │
│   - visible_nodes: vector<SceneNodePtr>         │
├─────────────────────────────────────────────────┤
│ 方法:                                            │
│   + get_root(): SceneNodePtr                    │
│   + set_camera(): void                          │
│   + get_camera(): Camera                        │
│   + update(): void                              │
│   + cull(): CullResult                          │
│   + get_visible_nodes(): vector<SceneNodePtr>   │
│   + traverse(): void                            │
│   + find(): SceneNodePtr                        │
└─────────────────────────────────────────────────┘
```

### 2.6 Camera - 摄像机

```
┌─────────────────────────────────────────────────┐
│                    Camera                        │
├─────────────────────────────────────────────────┤
│ 属性:                                            │
│   - position: Vec3                              │
│   - target: Vec3                                │
│   - up: Vec3                                    │
│   - fov_y_deg: float                            │
│   - aspect_ratio: float                         │
│   - near_plane: float                           │
│   - far_plane: float                            │
├─────────────────────────────────────────────────┤
│ 方法:                                            │
│   + set_position/target/fov/near_far(): void    │
│   + get_view_matrix(): Mat4                     │
│   + get_projection_matrix(): Mat4               │
│   + get_view_projection_matrix(): Mat4          │
│   + get_frustum(): Frustum                      │
└─────────────────────────────────────────────────┘
```

---

## 3. 核心流程设计

### 3.1 场景更新流程

```
SceneGraph::update()
    │
    ▼
Root::update_transforms()
    │
    ├─► 计算局部变换矩阵: local_matrix = T × R × S
    │
    ├─► 计算世界变换矩阵: world_matrix = parent.world_matrix × local_matrix
    │
    └─► 递归更新子节点
        │
        └─► Child::update_transforms()
            │
            ├─► 计算局部变换矩阵
            ├─► 计算世界变换矩阵
            └─► 递归...
```

### 3.2 裁剪流程

```
SceneGraph::cull()
    │
    ▼
从摄像机构建视锥体: frustum = camera.get_frustum()
    │
    ▼
cull_recursive(root, frustum, parent_culled=false)
    │
    ├─► 如果 parent_culled:
    │   ├─► early_exits++
    │   └─► 递归子节点 (parent_culled=true)
    │
    ├─► 如果 !visible:
    │   └─► 递归子节点 (parent_culled=true)
    │
    ├─► 测试 AABB 与视锥体: frustum.test_aabb(bounds)
    │   │
    │   ├─► false (在视锥体外):
    │   │   └─► 递归子节点 (parent_culled=true)
    │   │
    │   └─► true (在视锥体内):
    │       ├─► visible_nodes++
    │       ├─► 如果有 renderable，加入可见列表
    │       └─► 递归子节点 (parent_culled=false)
    │
    └─► 返回 CullResult
```

### 3.3 视锥体测试算法

```
test_aabb(aabb):
    for each plane in frustum:
        │
        ├─► 找到 p-vertex (法向量方向最远的顶点)
        │   p_vertex.x = (normal.x >= 0) ? aabb.max.x : aabb.min.x
        │   p_vertex.y = (normal.y >= 0) ? aabb.max.y : aabb.min.y
        │   p_vertex.z = (normal.z >= 0) ? aabb.max.z : aabb.min.z
        │
        └─► 如果 p_vertex 在平面背面:
            return false

    return true
```

---

## 4. 数据结构设计

### 4.1 内存布局

```
SceneNode 内存布局:
┌──────────────────────┐
│ name (string)        │  32 bytes
│ id (uint64_t)        │  8 bytes
│ visible (bool)       │  1 byte + padding
│ transform            │  56 bytes (Vec3 + Quat + Vec3)
│ renderable (shared)  │  16 bytes
│ parent (weak)        │  16 bytes
│ children (vector)    │  24 bytes
│ world_matrix (Mat4)  │  64 bytes
│ world_bounds (AABB)  │  24 bytes
│ dirty flags          │  4 bytes
└──────────────────────┘
总计: ~245 bytes / 节点
```

### 4.2 指针管理

```
父节点 ──shared_ptr──► 子节点
子节点 ──weak_ptr──► 父节点

场景图根节点 ──shared_ptr──► 根节点
SceneGraph 持有根节点的 shared_ptr
```

---

## 5. 接口设计

### 5.1 创建场景

```cpp
SceneGraph scene;

// 创建节点
auto root = scene.get_root();
auto node = std::make_shared<SceneNode>("MyNode");
node->get_transform().position = Vec3(1, 2, 3);
root->add_child(node);
```

### 5.2 设置变换

```cpp
// 平移
node->get_transform().position = Vec3(10, 0, 0);

// 旋转（欧拉角）
node->get_transform().set_rotation_euler(0, 90, 0);

// 缩放
node->get_transform().scale = Vec3(2, 2, 2);
```

### 5.3 设置可渲染对象

```cpp
class MyMesh : public Renderable {
    AABB get_local_bounds() const override {
        return AABB::from_center_size({0,0,0}, {1,1,1});
    }
    std::string get_type() const override {
        return "MyMesh";
    }
};

node->set_renderable(std::make_shared<MyMesh>());
```

### 5.4 执行裁剪

```cpp
// 设置摄像机
Camera camera;
camera.set_position({0, 5, 10});
camera.set_target({0, 0, 0});
camera.set_fov(60.0f);
camera.set_near_far(0.1f, 100.0f);
scene.set_camera(camera);

// 更新变换
scene.update();

// 执行裁剪
auto result = scene.cull();
// result.visible_nodes = 可见节点数
// result.culled_nodes = 裁剪节点数

// 获取可见节点
for (auto& node : scene.get_visible_nodes()) {
    // 渲染 node
}
```

### 5.5 遍历场景

```cpp
// 深度优先遍历
scene.traverse([](const SceneNodePtr& node) {
    std::cout << node->get_name() << std::endl;
});
```

---

## 6. 设计决策

### 6.1 决策 1：使用 shared_ptr 管理节点

**背景**：需要决定节点的所有权模型。

**选项**：
1. unique_ptr：独占所有权，转移时需要 std::move
2. shared_ptr：共享所有权，引用计数
3. 原始指针：手动管理，容易出错

**选择**：shared_ptr

**理由**：
- 节点可能被多个地方引用（如查找结果）
- 自动内存管理，避免内存泄漏
- 配合 weak_ptr 避免循环引用

### 6.2 决策 2：使用 mutable 缓存世界变换

**背景**：世界变换只在需要时计算，但需要在 const 方法中访问。

**选项**：
1. 每次调用都计算：简单但低效
2. 使用 mutable 缓存：高效但需要维护一致性

**选择**：mutable 缓存

**理由**：
- 世界变换计算涉及矩阵乘法，开销大
- 脏标记确保一致性
- mutable 允许在 const 方法中更新缓存

### 6.3 决策 3：AABB 而非 OBB

**背景**：需要选择包围盒类型。

**选项**：
1. AABB：计算快，旋转后变大
2. OBB：更紧密，相交测试复杂
3. 球体：旋转不变，不够紧凑

**选择**：AABB

**理由**：
- 视锥裁剪场景下，AABB 足够高效
- 实现简单，易于理解
- 可以通过重新计算避免旋转问题

### 6.4 决策 4：使用接口而非具体类

**背景**：需要决定如何表示可渲染对象。

**选项**：
1. 具体类（如 Mesh, Light）：耦合度高
2. 接口（Renderable）：灵活，易于扩展

**选择**：接口

**理由**：
- 场景图不应该知道具体的渲染对象类型
- 用户可以自由扩展
- 依赖倒置原则

---

## 7. 扩展性设计

### 7.1 添加新的渲染对象

```cpp
class ParticleSystem : public Renderable {
public:
    AABB get_local_bounds() const override {
        return particle_bounds_;
    }
    std::string get_type() const override {
        return "ParticleSystem";
    }
private:
    AABB particle_bounds_;
};

auto particles = std::make_shared<SceneNode>("Particles");
particles->set_renderable(std::make_shared<ParticleSystem>());
```

### 7.2 添加自定义属性

```cpp
// 通过继承扩展节点
class GameNode : public SceneNode {
public:
    int health = 100;
    std::string tag;
};

auto enemy = std::make_shared<GameNode>();
enemy->health = 50;
enemy->tag = "enemy";
```

### 7.3 添加空间划分

```cpp
// 可以在 SceneGraph 中添加 BVH 或 Octree
class SpatialIndex {
public:
    void build(const std::vector<SceneNodePtr>& nodes);
    std::vector<SceneNodePtr> query(const AABB& region);
};
```

---

## 8. 性能分析

### 8.1 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| add_child | O(1) | push_back |
| remove_child | O(n) | 查找 + 删除 |
| find | O(n) | 递归搜索 |
| update_transforms | O(n) | 遍历所有节点 |
| cull | O(n) | 最坏情况遍历所有节点 |
| traverse | O(n) | 遍历所有节点 |

### 8.2 空间复杂度

| 结构 | 空间 | 说明 |
|------|------|------|
| 每个节点 | ~245 bytes | 见内存布局 |
| n 个节点 | O(n) | 线性增长 |

### 8.3 优化机会

1. **脏标记优化**：只更新真正改变的分支
2. **空间索引**：BVH 或 Octree 加速裁剪
3. **批量处理**：连续内存布局，缓存友好
4. **多线程**：并行更新独立的子树

---

## 9. 测试策略

### 9.1 单元测试

- 数学类型：向量、矩阵、四元数运算
- 变换：局部矩阵计算
- 包围盒：AABB 操作
- 节点：层级管理、变换传播
- 场景图：裁剪算法

### 9.2 集成测试

- 复杂场景的变换计算
- 裁剪的准确性
- 边界情况处理

### 9.3 性能测试

- 大量节点的更新性能
- 裁剪的吞吐量
- 内存使用情况
