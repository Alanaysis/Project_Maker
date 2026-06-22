# 空间划分算法设计文档

## 1. 整体架构

### 核心类图

```
┌─────────────────────────────────────────────────────────────┐
│                      SpatialPartition                        │
├─────────────────────────────────────────────────────────────┤
│ + insert(object)                                           │
│ + remove(object)                                           │
│ + query(region) -> list<object>                            │
│ + ray_cast(ray) -> list<object>                            │
│ + get_stats() -> Stats                                     │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │      BVH      │ │    Octree     │ │      BSP      │
    ├───────────────┤ ├───────────────┤ ├───────────────┤
    │ - root_       │ │ - root_       │ │ - root_       │
    │ - maxDepth_   │ │ - maxDepth_   │ │ - maxDepth_   │
    │ - maxLeafSize_│ │ - maxObjects_ │ │ - minSize_    │
    └───────────────┘ └───────────────┘ └───────────────┘
```

## 2. AABB (Axis-Aligned Bounding Box)

### 设计

```cpp
struct AABB {
    Vec3 min;
    Vec3 max;
    
    // 核心操作
    void expand(const Vec3& point);
    void expand(const AABB& other);
    bool contains(const Vec3& point) const;
    bool intersects(const AABB& other) const;
    float surfaceArea() const;
    Vec3 center() const;
    Vec3 extent() const;
};
```

### 碰撞检测

AABB 碰撞检测使用分离轴定理（SAT）的简化版本：

```cpp
bool intersects(const AABB& other) const {
    return (min.x <= other.max.x && max.x >= other.min.x) &&
           (min.y <= other.max.y && max.y >= other.min.y) &&
           (min.z <= other.max.z && max.z >= other.min.z);
}
```

## 3. BVH 设计

### 节点结构

```cpp
struct BVHNode {
    AABB bounds;
    BVHNode* left;
    BVHNode* right;
    int objectIndex;  // 叶子节点使用
    bool isLeaf;
};
```

### 构建算法

1. 计算所有物体的 AABB
2. 选择分割轴（最长轴）
3. 按中位数分割物体
4. 递归构建左右子树

### 查询算法

1. 从根节点开始
2. 如果节点 AABB 与查询区域不相交，返回
3. 如果是叶子节点，检查所有物体
4. 递归查询左右子树

## 4. Octree 设计

### 节点结构

```cpp
struct OctreeNode {
    AABB bounds;
    std::vector<int> objects;
    std::array<std::unique_ptr<OctreeNode>, 8> children;
    bool isLeaf;
};
```

### 八叉树分割

```
      +-------+-------+
     /|      /|      /|
    +-------+-------+ |
   /|  0   /|  1   /| +
  +-------+-------+ |/|
  | +-----|-+-----|-+-------+
  |/|  2  |/|  3  |/|      /|
  +-------+-------+ +     / +
  | +-----|-+-----|-|----+  |
  |/  4   |/  5   |/|   |  +
  +-------+-------+ +   | /|
  | +-----|-+-----|-+----+  |
  |/  6   |/  7   |/    |  +
  +-------+-------+     | /
  |       |       |     |/
  +-------+-------+-----+
```

## 5. BSP 设计

### 节点结构

```cpp
struct BSPNode {
    Plane splitPlane;
    std::unique_ptr<BSPNode> front;
    std::unique_ptr<BSPNode> back;
    std::vector<int> objects;  // 叶子节点
    bool isLeaf;
};
```

### 分割策略

1. 选择分割平面（通常使用物体表面）
2. 将物体分为前、后、跨越三组
3. 跨越的物体根据大小决定归属
4. 递归构建前、后子树

## 6. 碰撞检测系统

### 宽相检测

```cpp
class CollisionBroadPhase {
    std::unique_ptr<SpatialPartition> partition_;
    
    void update(const std::vector<Object>& objects);
    std::vector<CollisionPair> findPotentialCollisions();
};
```

### 窄相检测

```cpp
class CollisionNarrowPhase {
    bool checkCollision(const Object& a, const Object& b);
    ContactManifold computeContacts(const Object& a, const Object& b);
};
```

## 7. 内存管理

### 策略

- BVH：使用对象池分配节点，减少内存碎片
- Octree：使用内存池，预分配子节点
- BSP：使用智能指针管理节点生命周期

### 优化

- 使用紧凑的数据结构减少缓存未命中
- 避免动态内存分配
- 使用 SIMD 指令加速 AABB 碰撞检测
