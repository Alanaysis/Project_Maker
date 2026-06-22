# 测试文档

## 测试策略

### 测试层次

1. **单元测试**：测试各个组件的独立功能
2. **集成测试**：测试多个组件的协作
3. **回归测试**：确保修改不破坏已有功能

### 测试数据

使用程序化生成的网格进行测试：

- **四面体**：最简单的封闭网格，4个面
- **二十面体球**：规则网格，20个面
- **带噪声网格**：用于测试平滑效果

## 测试用例

### 数据结构测试

| 测试用例 | 描述 |
|---------|------|
| test_create_empty_mesh | 创建空网格 |
| test_add_vertex | 添加顶点 |
| test_add_face | 添加面 |
| test_topology_update | 拓扑关系更新 |
| test_face_normal | 面法向量计算 |
| test_remove_face | 移除面 |
| test_clone | 网格克隆 |

### 简化算法测试

| 测试用例 | 描述 |
|---------|------|
| test_simplification_reduces_faces | 面数减少 |
| test_simplification_preserves_topology | 拓扑有效 |
| test_simplification_no_change_if_target_met | 已达标不改变 |

### 细分算法测试

| 测试用例 | 描述 |
|---------|------|
| test_subdivision_increases_faces | 面数增加 |
| test_subdivision_increases_vertices | 顶点数增加 |
| test_multiple_subdivisions | 多次细分 |
| test_subdivision_maintains_valid_mesh | 网格有效 |

### 平滑算法测试

| 测试用例 | 描述 |
|---------|------|
| test_smoothing_maintains_vertices | 顶点数不变 |
| test_smoothing_maintains_faces | 面数不变 |
| test_smoothing_changes_positions | 位置改变 |
| test_smoothing_reduces_noise | 噪声减少 |

### 集成测试

| 测试用例 | 描述 |
|---------|------|
| test_simplify_then_subdivide | 简化后细分 |
| test_subdivide_then_smooth | 细分后平滑 |
| test_full_pipeline | 完整流程 |

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试类
pytest tests/test_mesh.py::TestMeshSimplification -v

# 运行并显示覆盖率
pytest tests/ -v --cov=src
```

## 测试结果

所有测试应通过，验证：
1. 数据结构正确维护拓扑关系
2. 简化算法有效减少面数
3. 细分算法正确增加细节
4. 平滑算法改善网格质量
