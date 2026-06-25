# 开发手册

## 1. 环境配置

### 1.1 系统要求

- **操作系统**：Linux、macOS、Windows
- **编译器**：GCC 9+、Clang 10+、MSVC 2019+
- **构建工具**：CMake 3.10+
- **依赖库**：无外部依赖

### 1.2 安装依赖

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install build-essential cmake git
```

#### macOS

```bash
xcode-select --install
brew install cmake
```

#### Windows

1. 安装 Visual Studio 2019+
2. 安装 CMake
3. 安装 Git

### 1.3 验证安装

```bash
# 检查编译器
g++ --version  # 或 clang++ --version

# 检查 CMake
cmake --version

# 检查 Git
git --version
```

## 2. 编译说明

### 2.1 基本编译

```bash
# 进入项目目录
cd projects/ray-tracer

# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译
make

# 或者使用多核编译
make -j$(nproc)
```

### 2.2 编译选项

#### Debug 模式

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

#### Release 模式

```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

#### 指定编译器

```bash
# 使用 Clang
cmake -DCMAKE_CXX_COMPILER=clang++ ..

# 使用 GCC
cmake -DCMAKE_CXX_COMPILER=g++ ..
```

### 2.3 编译输出

编译完成后，将生成以下可执行文件：

```
build/
├── ray-tracer          # 主程序
├── basic_scene         # 基础场景示例
├── 01_basic_sphere     # 示例 1
├── 02_complex_scene    # 示例 2
├── 03_primitives       # 示例 3
├── 04_path_tracing     # 示例 4
├── 05_depth_of_field   # 示例 5
├── 06_textures         # 示例 6
├── 07_advanced_materials  # 示例 7
├── 08_motion_blur      # 示例 8
├── 09_acceleration     # 示例 9
├── 10_sampling         # 示例 10
├── test_vec3           # Vec3 测试
├── test_ray            # Ray 测试
├── test_sphere         # Sphere 测试
└── test_renderer       # Renderer 测试
```

## 3. 运行方式

### 3.1 运行示例

```bash
# 运行基础场景
./basic_scene

# 运行其他示例
./01_basic_sphere
./02_complex_scene
./03_primitives
# ...
```

### 3.2 运行主程序

```bash
# 运行主程序（默认场景）
./ray-tracer

# 指定场景
./ray-tracer --scene default
./ray-tracer --scene complex
./ray-tracer --scene test

# 指定输出文件
./ray-tracer --output output.ppm

# 指定渲染参数
./ray-tracer --width 800 --height 450 --samples 100
```

### 3.3 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
ctest -R test_vec3

# 显示详细输出
ctest -V

# 直接运行测试
./test_vec3
./test_ray
./test_sphere
./test_renderer
```

### 3.4 查看输出

渲染完成后，将生成 PPM 格式的图像文件。

#### Linux

```bash
# 使用 eog 打开
eog output.ppm

# 使用 feh 打开
feh output.ppm

# 使用 xdg-open 打开
xdg-open output.ppm
```

#### macOS

```bash
# 使用 Preview 打开
open output.ppm
```

#### Windows

1. 双击 PPM 文件
2. 或使用 Paint、IrfanView 打开

## 4. 项目结构

### 4.1 目录结构

```
ray-tracer/
├── CMakeLists.txt          # 构建配置
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档目录
│   ├── 01_RESEARCH.md      # 技术调研
│   ├── 02_REQUIREMENTS.md  # 需求分析
│   ├── 03_DESIGN.md        # 技术设计
│   ├── 04_PRODUCT.md       # 产品思考
│   └── 05_DEVELOPMENT.md   # 开发手册
├── include/                # 头文件
│   ├── vec3.h              # 3D 向量类
│   ├── ray.h               # 光线类
│   ├── hitable.h           # 可命中物体接口
│   ├── sphere.h            # 球体和平面
│   ├── triangle.h          # 三角形
│   ├── box.h               # 盒子
│   ├── cylinder.h          # 圆柱和圆锥
│   ├── material.h          # 基础材质
│   ├── advanced_material.h # 高级材质
│   ├── texture.h           # 纹理系统
│   ├── light.h             # 光源系统
│   ├── camera.h            # 相机
│   ├── renderer.h          # 基础渲染器
│   ├── advanced_renderer.h # 高级渲染器
│   ├── advanced_features.h # 高级特性
│   ├── scene.h             # 场景工厂
│   ├── bvh.h               # BVH 加速
│   ├── kdtree.h            # KD-Tree 加速
│   └── octree.h            # 八叉树和均匀网格
├── src/                    # 源代码
│   └── main.cpp            # 主程序
├── tests/                  # 测试文件
│   ├── test_vec3.cpp       # Vec3 测试
│   ├── test_ray.cpp        # Ray 测试
│   ├── test_sphere.cpp     # Sphere 测试
│   └── test_renderer.cpp   # Renderer 测试
├── examples/               # 示例文件
│   ├── basic_scene.cpp     # 基础场景
│   ├── 01_basic_sphere.cpp # 示例 1
│   ├── 02_complex_scene.cpp # 示例 2
│   ├── 03_primitives.cpp   # 示例 3
│   ├── 04_path_tracing.cpp # 示例 4
│   ├── 05_depth_of_field.cpp # 示例 5
│   ├── 06_textures.cpp     # 示例 6
│   ├── 07_advanced_materials.cpp # 示例 7
│   ├── 08_motion_blur.cpp  # 示例 8
│   ├── 09_acceleration.cpp # 示例 9
│   └── 10_sampling.cpp     # 示例 10
└── build/                  # 构建目录
```

### 4.2 文件说明

#### 头文件

| 文件 | 说明 |
|------|------|
| `vec3.h` | 3D 向量类，支持基本运算、点积、叉积、反射、折射 |
| `ray.h` | 光线类，表示为 P(t) = origin + t * direction |
| `hitable.h` | 可命中物体接口，定义 hit() 方法 |
| `sphere.h` | 球体和平面，实现光线相交 |
| `triangle.h` | 三角形，使用 Moller-Trumbore 算法 |
| `box.h` | 盒子（AABB），使用 Slab 方法 |
| `cylinder.h` | 圆柱和圆锥，实现侧面和端面相交 |
| `material.h` | 基础材质：Lambertian、Metal、Dielectric |
| `advanced_material.h` | 高级材质：Emissive、Anisotropic、Clearcoat 等 |
| `texture.h` | 纹理系统：SolidColor、Checker、Noise 等 |
| `light.h` | 光源系统：PointLight、DirectionalLight、AreaLight |
| `camera.h` | 相机系统，支持视角和景深 |
| `renderer.h` | 基础渲染器，支持抗锯齿 |
| `advanced_renderer.h` | 高级渲染器：路径追踪、光子映射 |
| `advanced_features.h` | 高级特性：运动模糊、体积渲染、采样策略 |
| `scene.h` | 场景工厂，创建测试场景 |
| `bvh.h` | BVH 加速结构 |
| `kdtree.h` | KD-Tree 加速结构 |
| `octree.h` | 八叉树和均匀网格 |

#### 示例文件

| 文件 | 说明 |
|------|------|
| `basic_scene.cpp` | 基础场景渲染 |
| `01_basic_sphere.cpp` | 基础球体渲染 |
| `02_complex_scene.cpp` | 复杂场景渲染 |
| `03_primitives.cpp` | 几何图元渲染 |
| `04_path_tracing.cpp` | 路径追踪渲染 |
| `05_depth_of_field.cpp` | 景深效果 |
| `06_textures.cpp` | 纹理渲染 |
| `07_advanced_materials.cpp` | 高级材质渲染 |
| `08_motion_blur.cpp` | 运动模糊效果 |
| `09_acceleration.cpp` | 加速结构测试 |
| `10_sampling.cpp` | 采样策略测试 |

## 5. 开发指南

### 5.1 添加新几何体

1. 在 `include/` 目录创建新头文件
2. 继承 `Hitable` 接口
3. 实现 `hit()` 方法
4. 在 `CMakeLists.txt` 中添加测试
5. 创建示例文件

示例：

```cpp
// include/new_shape.h
#pragma once

#include "hitable.h"

namespace rt {

class NewShape : public Hitable {
public:
    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override {
        // 实现相交测试
    }
};

} // namespace rt
```

### 5.2 添加新材质

1. 在 `include/material.h` 或新文件中添加
2. 继承 `Material` 接口
3. 实现 `scatter()` 方法
4. 创建示例测试

示例：

```cpp
class NewMaterial : public Material {
public:
    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        // 实现散射逻辑
    }
};
```

### 5.3 添加新光源

1. 在 `include/light.h` 或新文件中添加
2. 继承 `Light` 接口
3. 实现光照计算方法
4. 在渲染器中集成

示例：

```cpp
class NewLight : public Light {
public:
    Vec3 direction_to(const Vec3& point) const override {
        // 计算方向
    }

    double intensity_at(const Vec3& point) const override {
        // 计算强度
    }
};
```

### 5.4 添加新纹理

1. 在 `include/texture.h` 或新文件中添加
2. 继承 `Texture` 接口
3. 实现 `value()` 方法
4. 在材质中使用

示例：

```cpp
class NewTexture : public Texture {
public:
    Vec3 value(double u, double v, const Vec3& p) const override {
        // 计算纹理颜色
    }
};
```

### 5.5 添加新加速结构

1. 在 `include/` 目录创建新头文件
2. 继承 `Hitable` 接口
3. 实现构建和查询算法
4. 创建性能测试

示例：

```cpp
class NewAcceleration : public Hitable {
public:
    void build(std::vector<std::shared_ptr<Hitable>>& objects);

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override {
        // 实现查询算法
    }
};
```

## 6. 调试技巧

### 6.1 使用调试模式编译

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

### 6.2 使用 GDB 调试

```bash
# 编译调试版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行 GDB
gdb ./ray-tracer

# 在 GDB 中
(gdb) break main
(gdb) run
(gdb) next
(gdb) print variable
(gdb) backtrace
```

### 6.3 使用 Valgrind 检测内存泄漏

```bash
# 安装 Valgrind
sudo apt install valgrind  # Linux
brew install valgrind      # macOS

# 运行 Valgrind
valgrind --leak-check=full ./ray-tracer
```

### 6.4 使用 AddressSanitizer

```bash
# 编译时启用 AddressSanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make

# 运行程序
./ray-tracer
```

### 6.5 添加调试输出

```cpp
#include <iostream>

// 在关键位置添加调试输出
std::cout << "Debug: " << variable << std::endl;
std::cerr << "Error: " << message << std::endl;
```

## 7. 性能分析

### 7.1 使用 gprof

```bash
# 编译时启用性能分析
cmake -DCMAKE_CXX_FLAGS="-pg" ..
make

# 运行程序
./ray-tracer

# 分析结果
gprof ./ray-tracer gmon.out > analysis.txt
```

### 7.2 使用 perf

```bash
# 运行 perf
perf record ./ray-tracer

# 分析结果
perf report
```

### 7.3 使用 time 命令

```bash
# 测量运行时间
time ./ray-tracer
```

### 7.4 添加计时器

```cpp
#include <chrono>

auto start = std::chrono::high_resolution_clock::now();
// 执行代码
auto end = std::chrono::high_resolution_clock::now();
auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
std::cout << "Time: " << duration.count() << " ms" << std::endl;
```

## 8. 测试指南

### 8.1 编写单元测试

```cpp
#include <cassert>
#include <iostream>

void test_vec3_addition() {
    rt::Vec3 a(1, 2, 3);
    rt::Vec3 b(4, 5, 6);
    rt::Vec3 c = a + b;

    assert(c.x == 5);
    assert(c.y == 7);
    assert(c.z == 9);

    std::cout << "test_vec3_addition passed" << std::endl;
}

int main() {
    test_vec3_addition();
    return 0;
}
```

### 8.2 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
ctest -R test_vec3

# 显示详细输出
ctest -V
```

### 8.3 测试覆盖率

```bash
# 编译时启用覆盖率
cmake -DCMAKE_CXX_FLAGS="--coverage" ..
make

# 运行测试
ctest

# 生成覆盖率报告
gcov src/*.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage
```

## 9. 常见问题

### 9.1 编译错误

**问题**：找不到头文件

**解决**：检查 `#include` 路径，确保使用正确的相对路径

**问题**：链接错误

**解决**：检查 `CMakeLists.txt`，确保所有源文件都添加到目标

### 9.2 运行时错误

**问题**：段错误

**解决**：使用 GDB 或 Valgrind 调试，检查空指针和越界访问

**问题**：内存泄漏

**解决**：使用 Valgrind 或 AddressSanitizer 检测

### 9.3 渲染问题

**问题**：渲染结果全黑

**解决**：检查光源、材质和相机设置

**问题**：渲染结果有噪点

**解决**：增加采样数或使用更好的采样策略

**问题**：渲染速度慢

**解决**：使用加速结构或多线程渲染

## 10. 最佳实践

### 10.1 代码风格

- 使用一致的命名约定
- 添加详细注释
- 保持函数简短
- 避免魔法数字

### 10.2 内存管理

- 使用智能指针
- 避免裸指针
- 及时释放资源
- 避免循环引用

### 10.3 性能优化

- 使用 const 引用传递
- 避免不必要的拷贝
- 使用移动语义
- 预分配内存

### 10.4 错误处理

- 检查输入参数
- 使用异常处理
- 提供有意义的错误信息
- 记录错误日志

## 11. 版本控制

### 11.1 Git 工作流

```bash
# 克隆项目
git clone <repository-url>

# 创建新分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "Add new feature"

# 推送分支
git push origin feature/new-feature

# 合并到主分支
git checkout master
git merge feature/new-feature
```

### 11.2 提交规范

- 使用清晰的提交信息
- 每个提交只做一件事
- 提交前运行测试
- 保持提交历史清晰

## 12. 部署

### 12.1 打包发布

```bash
# 编译 Release 版本
cmake -DCMAKE_BUILD_TYPE=Release ..
make

# 打包
tar -czf ray-tracer.tar.gz build/
```

### 12.2 文档生成

```bash
# 使用 Doxygen 生成文档
doxygen Doxyfile
```

## 13. 总结

本开发手册提供了光线追踪渲染器项目的完整开发指南，包括环境配置、编译说明、运行方式、项目结构、开发指南、调试技巧、性能分析、测试指南、常见问题、最佳实践、版本控制和部署等内容。

通过遵循本手册，开发者可以：
- 快速搭建开发环境
- 编译和运行项目
- 理解项目结构
- 添加新功能
- 调试和优化代码
- 测试和部署项目
