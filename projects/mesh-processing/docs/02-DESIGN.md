# 设计文档

## 架构设计

### 模块划分

```
mesh-processing/
├── src/
│   ├── mesh_data.py      # 数据结构层
│   ├── simplification.py # 算法层 - 简化
│   ├── subdivision.py    # 算法层 - 细分
│   └── smoothing.py      # 算法层 - 平滑
└── tests/
    └── test_mesh.py      # 测试层
```

### 数据结构设计

#### TriangleMesh
核心网格类，管理顶点和面的存储及拓扑关系。

**关键属性**：
- `_vertices`: 顶点字典 {id: Vertex}
- `_faces`: 面字典 {id: Face}
- `_next_vertex_id`, `_next_face_id`: ID 计数器

**关键方法**：
- `add_vertex(position)`: 添加顶点
- `add_face(v0, v1, v2)`: 添加面，自动更新拓扑
- `remove_face(face_id)`: 移除面
- `get_edge_faces(v0, v1)`: 获取边的相邻面
- `compute_all_normals()`: 计算法向量
- `clone()`: 深拷贝

#### Vertex
顶点类，存储位置、法向量和拓扑信息。

**属性**：
- `id`: 唯一标识符
- `position`: 三维坐标 [x, y, z]
- `normal`: 法向量
- `adjacent_vertices`: 相邻顶点集合
- `adjacent_faces`: 相邻面集合

#### Face
面类，存储顶点索引和法向量。

**属性**：
- `id`: 唯一标识符
- `vertices`: 顶点ID元组 (v0, v1, v2)
- `normal`: 面法向量
- `adjacent_faces`: 相邻面集合

### 算法设计

#### MeshSimplifier
基于 QEM 的网格简化器。

**核心数据结构**：
- `QuadricMatrix`: 4x4 二次误差矩阵

**算法流程**：
1. `_initialize_quadrics()`: 初始化二次矩阵
2. `_find_best_collapse()`: 找最优折叠边
3. `_compute_collapse_cost()`: 计算折叠代价
4. `_perform_collapse()`: 执行折叠操作

#### LoopSubdivision
Loop 细分算法实现。

**算法流程**：
1. 计算旧顶点的新位置（使用 beta 权重）
2. 计算边上新顶点的位置（3/8 + 1/8 权重）
3. 创建新的三角形面

#### LaplacianSmoother / TaubinSmoother
平滑算法实现。

**设计选择**：
- 使用不可变操作（返回新网格）
- 支持迭代次数控制
- 提供不同的加权方式

## 设计原则

1. **单一职责**：每个模块专注于一种算法
2. **接口一致**：所有算法都接受 TriangleMesh，返回 TriangleMesh
3. **不可变性**：算法操作返回新网格，不修改输入
4. **可测试性**：每个组件都可以独立测试
