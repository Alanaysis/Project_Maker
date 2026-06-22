# 空间划分算法学习笔记

## 1. 核心概念

### 空间划分的目的

在游戏引擎中，碰撞检测是计算密集型任务。朴素算法需要 O(n²) 时间，空间划分可以优化到 O(n log n)。

### 核心思想

```
场景物体 → 空间划分 → 加速结构 → 查询优化
```

## 2. BVH (Bounding Volume Hierarchy)

### 原理

BVH 是一棵二叉树，每个节点包含一个包围盒，叶子节点存储实际物体。

### 关键点

1. **构建策略**：按最长轴分割，取中位数
2. **SAH 优化**：最小化表面积启发式，优化遍历代价
3. **动态更新**：支持物体移动时的增量更新

### 学到的教训

- 递归构建简单但可能栈溢出，大数据量用迭代
- 内存布局很重要，连续存储比指针树更快
- SAH 比简单的中位数分割效果更好

## 3. Octree (八叉树)

### 原理

八叉树递归地将空间分割为 8 个相等的子立方体，直到满足终止条件。

### 关键点

1. **边界物体**：物体可能跨越多个子节点，需要插入到所有相交的子节点
2. **深度控制**：限制最大深度避免过度细分
3. **内存管理**：使用内存池预分配节点

### 学到的教训

- 八叉树适合静态场景，动态场景需要频繁重建
- 边界物体处理需要特别小心
- 内存占用可能比 BVH 高

## 4. BSP (Binary Space Partitioning)

### 原理

BSP 使用任意平面将空间分割为两个半空间，递归分割直到满足条件。

### 关键点

1. **分割平面选择**：使用物体表面作为分割平面
2. **平衡性**：限制左右子树大小差异
3. **背面剔除**：利用 BSP 树进行背面剔除

### 学到的教训

- BSP 构建时间较长，适合静态场景
- 分割平面选择对性能影响很大
- 可以用于渲染优化（确定绘制顺序）

## 5. 碰撞检测优化

### 宽相检测

使用空间划分快速找出潜在碰撞对，减少需要精确检测的物体对数量。

### 窄相检测

使用精确算法（如 GJK、SAT）判断物体是否真正碰撞。

### 学到的教训

- 宽相检测是性能瓶颈，需要高效实现
- 窄相检测需要处理各种形状组合
- 缓存友好的数据结构很重要

## 6. 性能优化技巧

### SIMD 加速

使用 SSE/AVX 指令加速 AABB 碰撞检测：

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

### 缓存优化

- 使用连续内存存储节点
- 避免指针追逐
- 使用 SOA（Structure of Arrays）布局

### 并行化

- 使用 OpenMP 并行化查询
- 使用任务系统异步构建

## 7. 常见问题

### 浮点精度问题

AABB 碰撞检测需要处理浮点误差：

```cpp
bool intersects(const AABB& other) const {
    return (min.x <= other.max.x + epsilon && 
            max.x >= other.min.x - epsilon) &&
           (min.y <= other.max.y + epsilon && 
            max.y >= other.min.y - epsilon) &&
           (min.z <= other.max.z + epsilon && 
            max.z >= other.min.z - epsilon);
}
```

### 内存管理

使用内存池减少分配开销：

```cpp
class MemoryPool {
    std::vector<std::unique_ptr<Block>> blocks_;
    Block* currentBlock_;
    size_t offset_;
    
public:
    void* allocate(size_t size) {
        if (offset_ + size > BLOCK_SIZE) {
            currentBlock_ = new Block();
            blocks_.push_back(currentBlock_);
            offset_ = 0;
        }
        void* ptr = currentBlock_->data + offset_;
        offset_ += size;
        return ptr;
    }
};
```

### 边界条件

需要处理各种边界情况：

- 空场景
- 单个物体
- 物体在边界上
- 物体跨越多个区域

## 8. 最佳实践

1. **选择合适的算法**：
   - 动态场景：BVH
   - 静态场景：Octree
   - 室内场景：BSP

2. **性能优化**：
   - 使用 SIMD 加速
   - 使用缓存友好的数据结构
   - 使用并行化

3. **内存管理**：
   - 使用内存池
   - 避免频繁分配
   - 使用紧凑的数据结构

4. **测试**：
   - 单元测试覆盖所有功能
   - 性能测试验证性能指标
   - 边界测试处理各种情况

## 9. 参考资源

1. Real-Time Collision Detection (Ericson)
2. Game Physics Engine Development (Millington)
3. Physically Based Rendering (Pharr)
4. GPU Gems 3 - Chapter 32: Broad-Phase Collision Detection
5. [Geometric Tools](https://www.geometrictools.com/)
6. [Bullet Physics](https://pybullet.org/)
