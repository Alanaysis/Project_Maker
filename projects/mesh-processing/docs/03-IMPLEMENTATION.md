# 实现细节

## 数据结构实现

### TriangleMesh

网格类使用字典存储顶点和面，支持 O(1) 的查找操作。

**拓扑关系维护**：
- 添加面时自动更新顶点的相邻顶点和相邻面
- 移除面时清理相关拓扑关系
- 使用集合存储相邻关系，避免重复

**法向量计算**：
- 面法向量：使用叉积计算 `normal = (v1-v0) x (v2-v0)`
- 顶点法向量：相邻面法向量的平均值

### QuadricMatrix

二次误差矩阵用于 QEM 简化算法。

**矩阵构建**：
- 从顶点和平面法向量构建：`K_p = n * n^T`（外积）
- 从三角形构建：计算面法向量后构建

**误差计算**：
- `error = v^T * Q * v`，其中 v = [x, y, z, 1]

**最优位置**：
- 求解 `Q * v = 0` 的最小二乘解
- 如果矩阵奇异，回退到端点或中点

## 算法实现

### 网格简化 (QEM)

```python
def simplify(mesh, target_faces):
    initialize_quadrics(mesh)
    while mesh.num_faces > target_faces:
        collapse = find_best_collapse(mesh)
        perform_collapse(mesh, collapse)
    return mesh
```

**关键实现细节**：
- 边折叠后更新二次矩阵：`Q_new = Q_v0 + Q_v1`
- 处理退化面（折叠后形成的无效面）
- 处理边界边和非流形边

### Loop 细分

```python
def subdivide(mesh):
    # 1. 计算旧顶点新位置
    for v in mesh.vertices:
        new_pos = (1 - n*beta) * old_pos + beta * avg(neighbors)

    # 2. 计算边上新顶点
    for edge in mesh.edges:
        new_pos = 3/8 * (v0 + v1) + 1/8 * (opp0 + opp1)

    # 3. 创建新面
    for face in mesh.faces:
        create 4 new faces
```

**权重计算**：
- beta = (1/n) * (5/8 - (3/8 + 1/4 * cos(2*pi/n))^2)
- 对于 n=6（规则顶点），beta ≈ 1/16

### 拉普拉斯平滑

```python
def smooth(mesh, iterations):
    for _ in range(iterations):
        for v in mesh.vertices:
            avg = average(neighbors)
            new_pos = old_pos + lambda * (avg - old_pos)
    return mesh
```

### Taubin 平滑

```python
def smooth(mesh, iterations):
    for _ in range(iterations):
        mesh = smooth_step(mesh, lambda)   # 收缩
        mesh = smooth_step(mesh, mu)       # 膨胀
    return mesh
```

**参数选择**：
- lambda = 0.5, mu = -0.53 是常用组合
- lambda + mu < 0 确保收敛

## 性能考虑

1. **数据结构选择**：使用字典而非列表，便于动态增删
2. **拓扑缓存**：维护相邻关系，避免重复计算
3. **法向量增量更新**：只在需要时重新计算
4. **内存管理**：使用深拷贝避免副作用

## 已知限制

1. **简化算法**：O(E log E) 复杂度，大规模网格可能较慢
2. **细分算法**：内存使用随细分次数指数增长
3. **平滑算法**：可能导致网格收缩（拉普拉斯）或体积变化
