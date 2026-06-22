# 空间划分算法实现指南

## 1. 环境准备

### 依赖

- C++17 编译器（GCC 7+, Clang 5+, MSVC 2017+）
- CMake 3.10+
- 可选：Google Test（用于单元测试）

### 项目结构

```
spatial-partitioning/
├── include/           # 头文件
├── src/               # 源文件
├── tests/             # 测试
├── examples/          # 示例
└── CMakeLists.txt     # 构建脚本
```

## 2. 核心数据结构实现

### Vec3 向量类

```cpp
struct Vec3 {
    float x, y, z;
    
    Vec3() : x(0), y(0), z(0) {}
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}
    
    Vec3 operator+(const Vec3& v) const { return {x+v.x, y+v.y, z+v.z}; }
    Vec3 operator-(const Vec3& v) const { return {x-v.x, y-v.y, z-v.z}; }
    Vec3 operator*(float s) const { return {x*s, y*s, z*s}; }
    
    float length() const { return std::sqrt(x*x + y*y + z*z); }
    Vec3 normalized() const { float l = length(); return {x/l, y/l, z/l}; }
    float dot(const Vec3& v) const { return x*v.x + y*v.y + z*v.z; }
    Vec3 cross(const Vec3& v) const {
        return {y*v.z - z*v.y, z*v.x - x*v.z, x*v.y - y*v.x};
    }
};
```

### AABB 包围盒

```cpp
struct AABB {
    Vec3 min, max;
    
    AABB() : min(Vec3(1e9)), max(Vec3(-1e9)) {}
    AABB(const Vec3& min, const Vec3& max) : min(min), max(max) {}
    
    void expand(const Vec3& p) {
        min.x = std::min(min.x, p.x);
        min.y = std::min(min.y, p.y);
        min.z = std::min(min.z, p.z);
        max.x = std::max(max.x, p.x);
        max.y = std::max(max.y, p.y);
        max.z = std::max(max.z, p.z);
    }
    
    void expand(const AABB& box) {
        expand(box.min);
        expand(box.max);
    }
    
    bool intersects(const AABB& other) const {
        return (min.x <= other.max.x && max.x >= other.min.x) &&
               (min.y <= other.max.y && max.y >= other.min.y) &&
               (min.z <= other.max.z && max.z >= other.min.z);
    }
    
    float surfaceArea() const {
        Vec3 d = max - min;
        return 2.0f * (d.x*d.y + d.y*d.z + d.z*d.x);
    }
    
    Vec3 center() const { return (min + max) * 0.5f; }
};
```

## 3. BVH 实现

### 节点定义

```cpp
struct BVHNode {
    AABB bounds;
    int left = -1;
    int right = -1;
    int objectIndex = -1;
    bool isLeaf = false;
};
```

### 构建算法

```cpp
int BVH::build(std::vector<int>& indices, int start, int end) {
    if (end - start <= maxLeafSize_) {
        // 创建叶子节点
        return createLeaf(indices, start, end);
    }
    
    // 计算包围盒
    AABB centroidBounds;
    for (int i = start; i < end; i++) {
        centroidBounds.expand(objects_[indices[i]].bounds.center());
    }
    
    // 选择分割轴
    int axis = longestAxis(centroidBounds);
    
    // 按中位数分割
    int mid = (start + end) / 2;
    std::nth_element(indices.begin() + start, indices.begin() + mid,
                     indices.begin() + end, [&](int a, int b) {
        return objects_[a].bounds.center()[axis] < 
               objects_[b].bounds.center()[axis];
    });
    
    // 递归构建
    int nodeIndex = createNode();
    nodes_[nodeIndex].left = build(indices, start, mid);
    nodes_[nodeIndex].right = build(indices, mid, end);
    nodes_[nodeIndex].bounds.expand(nodes_[nodes_[nodeIndex].left].bounds);
    nodes_[nodeIndex].bounds.expand(nodes_[nodes_[nodeIndex].right].bounds);
    
    return nodeIndex;
}
```

### 查询算法

```cpp
void BVH::query(const AABB& region, std::vector<int>& results, int nodeIndex) const {
    if (nodeIndex == -1) return;
    
    const BVHNode& node = nodes_[nodeIndex];
    
    if (!node.bounds.intersects(region)) return;
    
    if (node.isLeaf) {
        if (objects_[node.objectIndex].bounds.intersects(region)) {
            results.push_back(node.objectIndex);
        }
        return;
    }
    
    query(region, results, node.left);
    query(region, results, node.right);
}
```

## 4. Octree 实现

### 节点定义

```cpp
struct OctreeNode {
    AABB bounds;
    std::vector<int> objects;
    std::array<int, 8> children = {-1, -1, -1, -1, -1, -1, -1, -1};
    bool isLeaf = true;
};
```

### 插入算法

```cpp
void Octree::insert(int objectIndex, int nodeIndex, int depth) {
    OctreeNode& node = nodes_[nodeIndex];
    
    if (depth >= maxDepth_ || node.objects.size() < maxObjects_) {
        node.objects.push_back(objectIndex);
        return;
    }
    
    if (node.isLeaf) {
        subdivide(nodeIndex);
    }
    
    // 插入到合适的子节点
    for (int i = 0; i < 8; i++) {
        if (nodes_[node.children[i]].bounds.intersects(
            objects_[objectIndex].bounds)) {
            insert(objectIndex, node.children[i], depth + 1);
        }
    }
}
```

### 细分算法

```cpp
void Octree::subdivide(int nodeIndex) {
    OctreeNode& node = nodes_[nodeIndex];
    Vec3 center = node.bounds.center();
    
    // 创建 8 个子节点
    for (int i = 0; i < 8; i++) {
        Vec3 childMin, childMax;
        childMin.x = (i & 1) ? center.x : node.bounds.min.x;
        childMin.y = (i & 2) ? center.y : node.bounds.min.y;
        childMin.z = (i & 4) ? center.z : node.bounds.min.z;
        childMax.x = (i & 1) ? node.bounds.max.x : center.x;
        childMax.y = (i & 2) ? node.bounds.max.y : center.y;
        childMax.z = (i & 4) ? node.bounds.max.z : center.z;
        
        node.children[i] = createNode(AABB(childMin, childMax));
    }
    
    node.isLeaf = false;
    
    // 重新分配物体
    auto objects = std::move(node.objects);
    for (int idx : objects) {
        for (int i = 0; i < 8; i++) {
            if (nodes_[node.children[i]].bounds.intersects(
                objects_[idx].bounds)) {
                nodes_[node.children[i]].objects.push_back(idx);
            }
        }
    }
}
```

## 5. 碰撞检测

### 宽相检测

```cpp
std::vector<CollisionPair> CollisionSystem::broadPhase() {
    std::vector<CollisionPair> pairs;
    
    for (size_t i = 0; i < objects_.size(); i++) {
        std::vector<int> candidates;
        partition_->query(objects_[i].bounds, candidates);
        
        for (int j : candidates) {
            if (j > i) {  // 避免重复检测
                pairs.push_back({i, j});
            }
        }
    }
    
    return pairs;
}
```

### 窄相检测

```cpp
bool CollisionSystem::narrowPhase(const Object& a, const Object& b) {
    // AABB vs AABB
    if (a.shape == Shape::AABB && b.shape == Shape::AABB) {
        return aabbVsAabb(a.bounds, b.bounds);
    }
    
    // Sphere vs Sphere
    if (a.shape == Shape::Sphere && b.shape == Shape::Sphere) {
        return sphereVsSphere(a.sphere, b.sphere);
    }
    
    // 其他形状组合...
    return false;
}
```

## 6. 性能优化

### 缓存友好

- 使用连续内存存储节点
- 避免指针追逐
- 使用 SOA（Structure of Arrays）布局

### 并行化

- 使用 OpenMP 并行化查询
- 使用任务系统异步构建

### SIMD 优化

```cpp
// 使用 SSE 加速 AABB 碰撞检测
bool aabbIntersectSSE(const AABB& a, const AABB& b) {
    __m128 aMin = _mm_load_ps(&a.min.x);
    __m128 aMax = _mm_load_ps(&a.max.x);
    __m128 bMin = _mm_load_ps(&b.min.x);
    __m128 bMax = _mm_load_ps(&b.max.x);
    
    __m128 cmp1 = _mm_cmpge_ps(aMin, bMax);
    __m128 cmp2 = _mm_cmple_ps(aMax, bMin);
    __m128 orResult = _mm_or_ps(cmp1, cmp2);
    
    return _mm_movemask_ps(orResult) == 0;
}
```

## 7. 调试与可视化

### 统计信息

```cpp
struct Stats {
    int nodeCount;
    int leafCount;
    int maxDepth;
    float avgObjectsPerLeaf;
    float treeBalance;
};
```

### 可视化

- 使用 OpenGL 渲染包围盒
- 使用颜色编码表示深度
- 支持交互式查询
