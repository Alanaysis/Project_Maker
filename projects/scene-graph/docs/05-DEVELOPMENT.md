# 场景图系统 - 开发指南

## 1. 环境设置

### 1.1 系统要求

- **操作系统**：Linux, macOS, Windows
- **编译器**：GCC 7+, Clang 5+, MSVC 2017+
- **CMake**：3.14+
- **Git**：用于克隆项目

### 1.2 Linux/macOS 设置

```bash
# 安装依赖
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# macOS (使用 Homebrew)
brew install cmake git

# 克隆项目
git clone <repository>
cd projects/scene-graph
```

### 1.3 Windows 设置

```powershell
# 安装 Visual Studio 2017+ 或 MinGW
# 安装 CMake: https://cmake.org/download/
# 安装 Git: https://git-scm.com/download/win

# 克隆项目
git clone <repository>
cd projects\scene-graph
```

---

## 2. 构建项目

### 2.1 基本构建

```bash
mkdir build
cd build
cmake ..
make -j$(nproc)
```

### 2.2 启用测试

```bash
cmake .. -DBUILD_TESTS=ON
make -j$(nproc)
ctest --output-on-failure
```

### 2.3 启用示例

```bash
cmake .. -DBUILD_EXAMPLES=ON
make -j$(nproc)
./scene_graph_demo
```

### 2.4 Debug 构建

```bash
cmake .. -DCMAKE_BUILD_TYPE=Debug
make -j$(nproc)
```

### 2.5 Release 构建

```bash
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

---

## 3. 项目结构详解

```
scene-graph/
├── include/                    # 头文件
│   ├── math_types.h           # 数学类型（Vec3, Mat4, Quaternion）
│   ├── transform.h            # 变换组件
│   ├── bounds.h               # AABB 和 Frustum
│   ├── scene_node.h           # 场景图节点
│   └── scene_graph.h          # 场景图管理器和摄像机
├── src/                        # 源文件
│   └── scene_graph.cpp        # 静态成员变量定义
├── tests/                      # 测试文件
│   ├── test_main.cpp          # 测试入口
│   ├── test_math_types.cpp    # 数学类型测试
│   ├── test_transform.cpp     # 变换测试
│   ├── test_bounds.cpp        # 包围盒测试
│   ├── test_scene_node.cpp    # 场景节点测试
│   └── test_scene_graph.cpp   # 场景图测试
├── examples/                   # 示例程序
│   └── demo.cpp               # 演示程序
├── docs/                       # 文档
│   ├── 01-RESEARCH.md         # 调研报告
│   ├── 02-DESIGN.md           # 设计文档
│   ├── 03-IMPLEMENTATION.md   # 实现细节
│   ├── 04-TESTING.md          # 测试策略
│   └── 05-DEVELOPMENT.md      # 开发指南（本文件）
├── CMakeLists.txt              # CMake 配置
├── README.md                   # 项目说明
└── LEARNING_NOTES.md           # 学习笔记
```

---

## 4. 开发流程

### 4.1 TDD 工作流

```
1. 编写测试
   ↓
2. 运行测试（应该失败）
   ↓
3. 编写最小实现
   ↓
4. 运行测试（应该通过）
   ↓
5. 重构代码
   ↓
6. 运行测试（确保仍然通过）
   ↓
7. 重复
```

### 4.2 开发顺序

建议按以下顺序开发：

1. **数学类型**（1-2天）
   - Vec3
   - Mat4
   - Quaternion
   - 编写并运行 `test_math_types.cpp`

2. **变换**（1天）
   - Transform 类
   - 编写并运行 `test_transform.cpp`

3. **包围盒**（1-2天）
   - AABB
   - Plane
   - Frustum
   - 编写并运行 `test_bounds.cpp`

4. **场景节点**（2-3天）
   - SceneNode 类
   - 层级管理
   - 变换传播
   - 编写并运行 `test_scene_node.cpp`

5. **场景图**（1-2天）
   - Camera 类
   - SceneGraph 类
   - 裁剪算法
   - 编写并运行 `test_scene_graph.cpp`

6. **示例和文档**（1天）
   - demo.cpp
   - 完善文档

---

## 5. 代码规范

### 5.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 命名空间 | 小写 | `sg` |
| 类名 | PascalCase | `SceneNode` |
| 函数名 | snake_case | `get_world_position` |
| 变量名 | snake_case | `world_matrix_` |
| 常量 | kPascalCase | `kMaxNodes` |
| 枚举 | PascalCase | `PlaneIndex` |
| 文件名 | snake_case | `scene_node.h` |

### 5.2 注释规范

```cpp
/**
 * 类/函数的简要描述
 *
 * 详细描述（如果需要）
 *
 * @param param1 参数1的描述
 * @param param2 参数2的描述
 * @return 返回值的描述
 */
```

### 5.3 代码风格

```cpp
// 使用 4 空格缩进
void function() {
    if (condition) {
        // ...
    } else {
        // ...
    }
}

// 类成员变量以下划线结尾
class MyClass {
    int value_;
    std::string name_;
};

// 指针和引用紧贴类型
int* ptr;
int& ref;
```

### 5.4 头文件保护

```cpp
#pragma once

// 或使用 include guards
#ifndef SCENE_GRAPH_MATH_TYPES_H
#define SCENE_GRAPH_MATH_TYPES_H

// ...

#endif // SCENE_GRAPH_MATH_TYPES_H
```

---

## 6. 调试技巧

### 6.1 打印变换矩阵

```cpp
void print_matrix(const Mat4& m, const std::string& name = "") {
    if (!name.empty()) {
        std::cout << name << ":" << std::endl;
    }
    for (int r = 0; r < 4; ++r) {
        std::cout << "  ";
        for (int c = 0; c < 4; ++c) {
            std::cout << std::setw(10) << std::fixed << std::setprecision(3)
                      << m.at(r, c);
        }
        std::cout << std::endl;
    }
}
```

### 6.2 打印场景树

```cpp
void print_scene_tree(const SceneNodePtr& node, int depth = 0) {
    std::string indent(depth * 2, ' ');
    Vec3 pos = node->get_world_position();
    std::cout << indent << node->get_name()
              << " [" << pos.x << ", " << pos.y << ", " << pos.z << "]"
              << (node->is_visible() ? " [V]" : " [H]")
              << std::endl;

    for (const auto& child : node->get_children()) {
        print_scene_tree(child, depth + 1);
    }
}
```

### 6.3 验证裁剪结果

```cpp
void debug_culling(SceneGraph& scene) {
    scene.update();
    auto result = scene.cull();

    std::cout << "=== Culling Debug ===" << std::endl;
    std::cout << "Total nodes: " << result.total_nodes << std::endl;
    std::cout << "Visible: " << result.visible_nodes << std::endl;
    std::cout << "Culled: " << result.culled_nodes << std::endl;
    std::cout << "Early exits: " << result.early_exits << std::endl;

    std::cout << "Visible nodes:" << std::endl;
    for (const auto& node : scene.get_visible_nodes()) {
        Vec3 pos = node->get_world_position();
        std::cout << "  - " << node->get_name()
                  << " [" << pos.x << ", " << pos.y << ", " << pos.z << "]"
                  << std::endl;
    }
}
```

### 6.4 使用 GDB 调试

```bash
# Debug 构建
cmake .. -DCMAKE_BUILD_TYPE=Debug
make -j$(nproc)

# 运行 GDB
gdb ./scene_graph_tests

# 在 GDB 中
(gdb) break test_scene_graph.cpp:42
(gdb) run
(gdb) print node->get_world_position()
(gdb) print node->get_world_matrix()
```

### 6.5 使用 Valgrind 检查内存

```bash
# 检查内存泄漏
valgrind --leak-check=full ./scene_graph_tests

# 检查未初始化内存
valgrind --tool=memcheck ./scene_graph_tests
```

---

## 7. 常见问题

### 7.1 编译错误

**问题**：找不到头文件

**解决**：检查 CMakeLists.txt 中的 include_directories 设置

**问题**：链接错误

**解决**：确保所有源文件都添加到 CMakeLists.txt

### 7.2 运行时错误

**问题**：段错误（Segmentation Fault）

**解决**：
1. 检查空指针
2. 检查数组越界
3. 使用 Valgrind 定位问题

**问题**：变换结果不对

**解决**：
1. 检查变换顺序（应该是 TRS）
2. 检查脏标记是否正确设置
3. 打印中间矩阵值

### 7.3 测试失败

**问题**：浮点数精度问题

**解决**：使用 `EXPECT_NEAR` 而不是 `EXPECT_FLOAT_EQ`

**问题**：测试顺序依赖

**解决**：确保每个测试独立，不依赖其他测试的状态

---

## 8. 性能优化

### 8.1 编译器优化

```bash
# Release 构建
cmake .. -DCMAKE_BUILD_TYPE=Release

# 启用 LTO（Link-Time Optimization）
cmake .. -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON
```

### 8.2 代码优化

1. **避免不必要的拷贝**：使用 `const&` 传递参数
2. **预分配内存**：为 vector 预分配空间
3. **内联小函数**：使用 `inline` 关键字
4. **减少虚函数调用**：在热路径中避免虚函数

### 8.3 数据结构优化

1. **缓存友好**：连续内存布局
2. **减少指针追逐**：使用数组而非链表
3. **空间局部性**：相关数据放在一起

---

## 9. 扩展指南

### 9.1 添加新的渲染对象

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
    std::vector<Particle> particles_;
};

// 使用
auto particles = std::make_shared<SceneNode>("Particles");
particles->set_renderable(std::make_shared<ParticleSystem>());
```

### 9.2 添加空间索引

```cpp
class BVH {
public:
    void build(const std::vector<SceneNodePtr>& nodes);
    std::vector<SceneNodePtr> query(const AABB& region);

private:
    struct BVHNode {
        AABB bounds;
        std::vector<SceneNodePtr> objects;
        std::unique_ptr<BVHNode> left, right;
    };

    std::unique_ptr<BVHNode> root_;
};
```

### 9.3 添加序列化

```cpp
class SceneSerializer {
public:
    void serialize(const SceneNodePtr& root, const std::string& filename);
    SceneNodePtr deserialize(const std::string& filename);

private:
    json node_to_json(const SceneNodePtr& node);
    SceneNodePtr json_to_node(const json& j);
};
```

### 9.4 添加动画支持

```cpp
class Animation {
public:
    void update(float dt);
    void apply_to(Transform& transform);

private:
    struct Keyframe {
        float time;
        Vec3 position;
        Quaternion rotation;
        Vec3 scale;
    };

    std::vector<Keyframe> keyframes_;
    float current_time_ = 0;
};
```

---

## 10. 部署

### 10.1 安装库

```bash
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local
make install
```

### 10.2 在其他项目中使用

```cmake
find_package(scene-graph REQUIRED)
target_link_libraries(my_app scene-graph)
```

### 10.3 打包

```bash
# 创建源码包
cpack --source

# 创建二进制包
cpack
```

---

## 11. 贡献指南

### 11.1 提交代码

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -m "Add my feature"`
4. 推送分支：`git push origin feature/my-feature`
5. 创建 Pull Request

### 11.2 代码审查

- 确保所有测试通过
- 添加新功能的测试
- 更新文档
- 遵循代码规范

### 11.3 问题报告

使用 GitHub Issues 报告问题，包含：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息

---

## 12. 学习资源

### 12.1 推荐书籍

- 《Real-Time Rendering》- Tomas Akenine-Moller
- 《Game Engine Architecture》- Jason Gregory
- 《3D Math Primer for Graphics and Game Development》- Fletcher Dunn

### 12.2 在线资源

- [LearnOpenGL](https://learnopengl.com/)
- [Game Programming Patterns](https://gameprogrammingpatterns.com/)
- [3Blue1Brown - Linear Algebra](https://www.3blue1brown.com/topics/linear-algebra)

### 12.3 相关项目

- [Three.js](https://threejs.org/) - JavaScript 3D 库
- [OpenSceneGraph](http://www.openscenegraph.org/) - C++ 场景图
- [assimp](https://www.assimp.org/) - 3D 模型导入库
