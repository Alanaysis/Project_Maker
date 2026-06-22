# 场景图系统 - 调研报告

## 1. 场景图概述

### 1.1 什么是场景图

场景图（Scene Graph）是一种用于组织和管理 3D 场景中物体的数据结构。它以树形结构表示物体之间的层级关系，每个节点代表一个物体或变换，边表示父子关系。

**核心思想**：
- 将复杂场景分解为层级化的节点
- 子节点继承父节点的变换
- 通过遍历树结构进行渲染和更新

### 1.2 为什么需要场景图

**问题**：在复杂的 3D 场景中，可能有成千上万个物体，每个物体都有自己的位置、旋转和缩放。如果直接管理每个物体的变换，当一个父物体移动时，需要手动更新所有子物体。

**解决方案**：场景图通过层级关系自动传播变换，大大简化了场景管理。

**优势**：
1. **变换继承**：子物体自动跟随父物体移动
2. **层级裁剪**：父物体不可见时，跳过所有子物体
3. **逻辑分组**：将相关物体组织在一起
4. **易于编辑**：在编辑器中可以直观地操作层级

---

## 2. 场景图架构

### 2.1 典型架构

```
Root
├── Camera
├── Lights
│   ├── DirectionalLight
│   ├── PointLight1
│   └── PointLight2
├── Terrain
├── Buildings
│   ├── House1
│   │   ├── Door
│   │   └── Window
│   └── House2
└── Characters
    ├── Player
    │   ├── Body
    │   │   ├── Head
    │   │   ├── LeftArm
    │   │   └── RightArm
    │   └── Weapon
    └── Enemy
```

### 2.2 节点类型

| 节点类型 | 描述 | 示例 |
|----------|------|------|
| Transform Node | 只包含变换，无渲染 | 组节点、相机 |
| Mesh Node | 包含几何数据 | 角色、建筑 |
| Light Node | 光源 | 点光源、聚光灯 |
| Camera Node | 摄像机 | 主摄像机 |
| Group Node | 逻辑分组 | "敌人"组 |

### 2.3 业界实现对比

| 引擎 | 场景图实现 | 特点 |
|------|-----------|------|
| Unity | Transform 组件 | 每个 GameObject 都有 Transform |
| Unreal | FSceneNode | 与渲染管线深度集成 |
| Three.js | Object3D | JavaScript 实现，易于学习 |
| OpenSceneGraph | osg::Node | C++ 实现，功能完整 |
| Godot | Node | 树形结构，一切都是节点 |

---

## 3. 变换层级

### 3.1 变换矩阵

在 3D 图形中，物体的变换用 4x4 矩阵表示：

```
| sx  rx  ry  tx |
| ry  sy  ry  ty |
| rz  rz  sz  tz |
| 0   0   0   1  |
```

其中：
- (sx, sy, sz) = 缩放
- (rx, ry, rz) = 旋转
- (tx, ty, tz) = 平移

### 3.2 变换组合顺序

**TRS 顺序**（本项目采用）：
```
M = T × R × S
```

1. 先缩放：物体在模型空间中缩放
2. 再旋转：缩放后的物体旋转
3. 最后平移：旋转后的物体移到指定位置

**为什么不能改变顺序？**

- SRT：平移后缩放，位置也会被缩放 → 错误
- RTS：缩放后旋转，缩放轴会改变 → 错误
- TRS：正确，每个变换在正确的空间中应用

### 3.3 层级变换计算

对于场景图中的节点：

```
M_world(node) = M_world(parent) × M_local(node)
```

其中 M_local = T × R × S

**例子**：
```
Root (平移 10, 0, 0)
└── Child (平移 5, 0, 0)
    └── GrandChild (平移 3, 0, 0)

M_world(Root) = T(10, 0, 0)
M_world(Child) = T(10, 0, 0) × T(5, 0, 0) = T(15, 0, 0)
M_world(GrandChild) = T(15, 0, 0) × T(3, 0, 0) = T(18, 0, 0)
```

---

## 4. 旋转表示

### 4.1 旋转矩阵

3x3 矩阵表示旋转：

```cpp
// 绕 Y 轴旋转 θ
| cos(θ)  0  sin(θ) |
| 0       1  0      |
| -sin(θ) 0  cos(θ) |
```

**优点**：直观，直接乘以向量
**缺点**：9 个参数，有冗余，插值困难

### 4.2 欧拉角

用三个角度表示旋转：(pitch, yaw, roll)

**优点**：直观，只需 3 个数
**缺点**：万向锁（Gimbal Lock），插值困难

### 4.3 四元数

用四个数 (x, y, z, w) 表示旋转：

```
q = w + xi + yj + zk
```

其中 i, j, k 是虚数单位。

**优点**：
- 无万向锁
- 插值平滑（Slerp）
- 组合旋转简单（乘法）
- 只需 4 个数

**缺点**：
- 不直观
- 需要理解复数数学

**关键公式**：
- 旋转向量：`v' = q × v × q*`
- 组合旋转：`q_combined = q2 × q1`
- 插值：`Slerp(q1, q2, t) = q1 × sin((1-t)θ) / sinθ + q2 × sin(tθ) / sinθ`

---

## 5. 视锥裁剪

### 5.1 什么是视锥体

视锥体是摄像机可见的空间区域，形状为一个截断的金字塔：

```
       Far Plane
      /--------\
     /          \
    /            \
   /              \
  /                \
 /                  \
/____________________\
      Near Plane
```

由 6 个平面定义：
1. 近平面（Near Plane）
2. 远平面（Far Plane）
3. 左平面（Left Plane）
4. 右平面（Right Plane）
5. 上平面（Top Plane）
6. 下平面（Bottom Plane）

### 5.2 裁剪算法

**基本思想**：如果一个物体的包围盒完全在某个平面的外侧，则该物体不可见。

**算法流程**：
```
for each plane in frustum:
    if AABB 完全在 plane 的外侧:
        return false  // 被裁剪
return true  // 可见
```

### 5.3 p-vertex 优化

**问题**：如何快速判断 AABB 是否在平面外侧？

**解决方案**：p-vertex（正顶点）

对于每个平面，找到 AABB 在法向量方向上最远的顶点：
```cpp
p_vertex.x = (normal.x >= 0) ? aabb.max.x : aabb.min.x;
p_vertex.y = (normal.y >= 0) ? aabb.max.y : aabb.min.y;
p_vertex.z = (normal.z >= 0) ? aabb.max.z : aabb.min.z;
```

如果这个顶点在平面背面，则整个 AABB 在平面背面。

### 5.4 Gribb/Hartmann 平面提取

从 View-Projection 矩阵直接提取 6 个平面：

```cpp
// VP 矩阵的行
row0 = VP[0], row1 = VP[1], row2 = VP[2], row3 = VP[3]

// 左平面 = row3 + row0
left.normal = (row3.x + row0.x, row3.y + row0.y, row3.z + row0.z)
left.distance = row3.w + row0.w

// 右平面 = row3 - row0
right.normal = (row3.x - row0.x, row3.y - row0.y, row3.z - row0.z)
right.distance = row3.w - row0.w

// 类似地计算其他平面
```

---

## 6. 包围盒

### 6.1 AABB（轴对齐包围盒）

最小的长方体，边与坐标轴平行：

```cpp
struct AABB {
    Vec3 min;  // 最小角
    Vec3 max;  // 最大角
};
```

**优点**：
- 计算简单
- 相交测试快速
- 内存占用小

**缺点**：
- 旋转后变大，不够紧密

### 6.2 OBB（有向包围盒）

可以任意方向的长方体：

```cpp
struct OBB {
    Vec3 center;
    Vec3 axes[3];  // 三个方向轴
    Vec3 extents;  // 半尺寸
};
```

**优点**：
- 更紧密
- 旋转后不变

**缺点**：
- 相交测试复杂
- 内存占用大

### 6.3 球体包围盒

```cpp
struct BoundingSphere {
    Vec3 center;
    float radius;
};
```

**优点**：
- 旋转不变
- 相交测试最简单

**缺点**：
- 可能不够紧凑

---

## 7. 空间划分

### 7.1 BVH（层次包围体）

将物体分组，构建树形的包围体层次：

```
        Root AABB
       /         \
   AABB1        AABB2
   /    \       /    \
 AABB1a AABB1b AABB2a AABB2b
```

**优点**：
- 快速剔除
- 动态场景友好

### 7.2 Octree（八叉树）

将空间递归地分成 8 个子空间：

```
       Root
      / | | \
    / | | | \ \
   8 个子节点
```

**优点**：
- 均匀分布场景高效
- 内存效率高

### 7.3 BSP（二叉空间划分）

用平面递归地划分空间：

**优点**：
- 精确裁剪
- 适合室内场景

---

## 8. 性能优化

### 8.1 脏标记（Dirty Flag）

**问题**：每次更新都遍历整棵树开销大。

**解决方案**：使用脏标记，只在需要时更新。

```cpp
void mark_dirty() {
    is_dirty = true;
    for (auto& child : children) {
        child->mark_dirty();
    }
}

void update() {
    if (is_dirty) {
        // 重新计算
        is_dirty = false;
    }
}
```

### 8.2 层级裁剪

**优化**：如果父节点被裁剪，跳过所有子节点。

```cpp
void cull(Frustum frustum, bool parent_culled) {
    if (parent_culled) {
        // 跳过当前节点和所有子节点
        return;
    }

    if (!frustum.test_aabb(bounds)) {
        // 裁剪当前节点和所有子节点
        cull_children(frustum, true);
        return;
    }

    // 可见，继续检查子节点
    cull_children(frustum, false);
}
```

### 8.3 批量更新

**优化**：延迟更新，批量处理。

```cpp
void update_all() {
    // 收集所有脏节点
    collect_dirty_nodes();

    // 按深度排序
    sort_by_depth();

    // 从浅到深更新
    for (auto& node : dirty_nodes) {
        node->update();
    }
}
```

---

## 9. 相关项目

| 项目 | 语言 | 特点 | 链接 |
|------|------|------|------|
| Three.js | JavaScript | Web 3D 引擎 | https://threejs.org/ |
| OpenSceneGraph | C++ | 高性能场景图 | http://www.openscenegraph.org/ |
| assimp | C++ | 3D 模型导入 | https://www.assimp.org/ |
| bgfx | C++ | 跨平台渲染 | https://github.com/bkaradzic/bgfx |

---

## 10. 学习路径建议

1. **第 1 天**：理解场景图概念和树形结构
2. **第 2-3 天**：学习变换矩阵和四元数
3. **第 4-5 天**：实现基本的场景图节点和变换层级
4. **第 6-7 天**：学习 AABB 和视锥裁剪
5. **第 8-9 天**：实现裁剪系统
6. **第 10 天**：测试、优化和文档
