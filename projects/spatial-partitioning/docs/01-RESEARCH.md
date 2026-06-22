# 空间划分算法研究

## 1. 背景与动机

### 为什么需要空间划分？

在游戏引擎和物理仿真中，碰撞检测是核心功能之一。朴素的碰撞检测算法时间复杂度为 O(n²)，当场景中有大量物体时，性能急剧下降。

空间划分算法通过将空间分割成更小的区域，可以快速剔除不可能碰撞的物体对，将碰撞检测优化到 O(n log n) 甚至更好。

### 核心思想

```
场景物体 → 空间划分 → 加速结构 → 查询优化
```

## 2. 主要算法对比

| 算法 | 构建时间 | 查询时间 | 内存占用 | 适用场景 |
|------|----------|----------|----------|----------|
| BVH | O(n log n) | O(log n) | 中等 | 动态场景 |
| Octree | O(n log n) | O(log n) | 较高 | 静态场景 |
| BSP | O(n²) | O(log n) | 较低 | 室内场景 |
| Grid | O(n) | O(1) | 高 | 均匀分布 |

## 3. BVH (Bounding Volume Hierarchy)

### 原理

BVH 是一棵二叉树，每个节点包含一个包围盒，叶子节点存储实际物体。

### 构建策略

1. **按最长轴分割**：选择物体分布最长的轴进行分割
2. **按中位数分割**：将物体按位置排序，取中位数
3. **SAH 分割**：最小化表面积启发式，优化遍历代价

### SAH 公式

```
Cost = C_traversal + P_left * N_left * C_intersect + P_right * N_right * C_intersect
```

其中：
- P_left, P_right：左右子节点包围盒的表面积比例
- N_left, N_right：左右子节点中的物体数量

## 4. Octree (八叉树)

### 原理

八叉树递归地将空间分割为 8 个相等的子立方体，直到满足终止条件（如最大深度或最小物体数）。

### 优点

- 构建简单
- 查询高效
- 内存局部性好

### 缺点

- 不适合物体分布不均匀的场景
- 边界物体处理复杂

## 5. BSP (Binary Space Partitioning)

### 原理

BSP 使用任意平面将空间分割为两个半空间，递归分割直到满足条件。

### 应用

- 室内场景渲染（用于确定绘制顺序）
- 碰撞检测
- 可见性判断

## 6. 碰撞检测优化

### 层次包围盒

- 粗检测：使用 AABB 快速排除
- 细检测：使用精确几何体进行碰撞检测

### 宽相与窄相

- 宽相（Broad Phase）：使用空间划分找出潜在碰撞对
- 窄相（Narrow Phase）：使用精确算法判断是否碰撞

## 7. 参考资料

1. Ericson, C. (2005). Real-Time Collision Detection. Morgan Kaufmann.
2. Millington, I. (2010). Game Physics Engine Development. CRC Press.
3. Pharr, M., Humphreys, G. (2010). Physically Based Rendering. Morgan Kaufmann.
