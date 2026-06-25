# 光线追踪渲染器

一个完整的光线追踪渲染器项目，涵盖光线追踪的核心技术，包括基础光线追踪、材质系统、光源系统、加速结构、渲染算法和高级特性。

## 项目简介

本项目是一个从零开始实现的光线追踪渲染器，使用 C++17/20 编写。项目旨在帮助学习者深入理解光线追踪的原理和实现，涵盖从基础的光线-物体相交测试到高级的全局光照算法。

## 快速开始

### 环境要求

- C++17/20 兼容的编译器（GCC 9+、Clang 10+、MSVC 2019+）
- CMake 3.10+
- 支持多线程的系统

### 编译运行

```bash
# 克隆项目
cd projects/ray-tracer

# 创建构建目录
mkdir build && cd build

# 编译
cmake ..
make

# 运行基础示例
./basic_scene

# 运行其他示例
./01_basic_sphere
./02_complex_scene
./03_primitives
# ... 更多示例
```

## 技术分类

### 1. 光线追踪基础

| 技术 | 文件 | 描述 |
|------|------|------|
| 光线-球体相交 | `sphere.h` | 使用二次方程求解 |
| 光线-三角形相交 | `triangle.h` | Moller-Trumbore 算法 |
| 光线-平面相交 | `sphere.h` | 平面方程求解 |
| 光线-盒子相交 | `box.h` | Slab 方法 |
| 光线-圆柱相交 | `cylinder.h` | 侧面+端面相交 |

### 2. 材质系统

| 材质类型 | 文件 | 描述 |
|----------|------|------|
| 漫反射 (Lambertian) | `material.h` | 随机散射 |
| 镜面反射 (Metal) | `material.h` | 模糊反射 |
| 折射 (Dielectric) | `material.h` | Snell 定律 + Schlick 近似 |
| 自发光 (Emissive) | `advanced_material.h` | 光源材质 |
| 纹理材质 | `advanced_material.h` | 支持各种纹理 |
| 各向异性 | `advanced_material.h` | 拉丝金属效果 |
| 清漆 | `advanced_material.h` | 多层材质 |
| 混合材质 | `advanced_material.h` | 材质混合 |
| 菲涅尔材质 | `advanced_material.h` | 角度依赖反射 |

### 3. 光源系统

| 光源类型 | 文件 | 描述 |
|----------|------|------|
| 点光源 | `light.h` | 衰减光 |
| 方向光源 | `light.h` | 平行光（太阳光） |
| 面光源 | `light.h` | 软阴影 |
| 环境光 | `light.h` | 全局光照 |
| 环境遮蔽 | `light.h` | 接近遮蔽 |

### 4. 加速结构

| 结构 | 文件 | 描述 |
|------|------|------|
| BVH | `bvh.h` | 包围盒层次结构 |
| KD-Tree | `kdtree.h` | 空间分割 |
| 八叉树 | `octree.h` | 3D 空间分割 |
| 均匀网格 | `octree.h` | 规则网格 |

### 5. 渲染算法

| 算法 | 文件 | 描述 |
|------|------|------|
| 路径追踪 | `advanced_renderer.h` | 物理准确的渲染 |
| 双向路径追踪 | `advanced_renderer.h` | 光源+相机双向 |
| 光子映射 | `advanced_renderer.h` | 焦散效果 |

### 6. 高级特性

| 特性 | 文件 | 描述 |
|------|------|------|
| 抗锯齿 | `renderer.h` | 多重采样 |
| 景深 | `advanced_features.h` | 焦距模糊 |
| 运动模糊 | `advanced_features.h` | 移动物体模糊 |
| 焦散 | `advanced_features.h` | 光线聚焦 |
| 体积渲染 | `advanced_features.h` | 烟雾效果 |
| 采样策略 | `advanced_features.h` | 分层/Halton 采样 |

### 7. 纹理系统

| 纹理类型 | 文件 | 描述 |
|----------|------|------|
| 纯色纹理 | `texture.h` | 单一颜色 |
| 棋盘格纹理 | `texture.h` | 黑白相间 |
| 噪声纹理 | `texture.h` | Perlin 噪声 |
| 图像纹理 | `texture.h` | PPM 图像 |
| 渐变纹理 | `texture.h` | 颜色渐变 |
| 条纹纹理 | `texture.h` | 条纹图案 |

## 学习路径

### 初级：光线追踪基础

1. **Vec3 向量类** - 理解 3D 向量运算
2. **Ray 光线类** - 理解光线表示
3. **Hitable 接口** - 理解物体抽象
4. **Sphere 球体** - 理解光线-球体相交
5. **Material 材质** - 理解材质系统

### 中级：材质与光源

6. **Lambertian 漫反射** - 理解漫反射模型
7. **Metal 金属** - 理解镜面反射
8. **Dielectric 电介质** - 理解折射和反射
9. **Light 光源** - 理解光照模型
10. **Texture 纹理** - 理解纹理映射

### 高级：渲染算法

11. **Path Tracing 路径追踪** - 理解全局光照
12. **BVH 加速** - 理解空间加速结构
13. **Depth of Field 景深** - 理解相机模型
14. **Motion Blur 运动模糊** - 理解时间采样
15. **Volume Rendering 体积渲染** - 理解体积效果

## 文件组织

```
ray-tracer/
├── include/                    # 头文件
│   ├── vec3.h                 # 3D 向量类
│   ├── ray.h                  # 光线类
│   ├── hitable.h              # 可命中物体接口
│   ├── sphere.h               # 球体和平面
│   ├── triangle.h             # 三角形
│   ├── box.h                  # 盒子
│   ├── cylinder.h             # 圆柱和圆锥
│   ├── material.h             # 基础材质
│   ├── advanced_material.h    # 高级材质
│   ├── texture.h              # 纹理系统
│   ├── light.h                # 光源系统
│   ├── camera.h               # 相机
│   ├── renderer.h             # 基础渲染器
│   ├── advanced_renderer.h    # 高级渲染器
│   ├── advanced_features.h    # 高级特性
│   ├── scene.h                # 场景工厂
│   ├── bvh.h                  # BVH 加速
│   ├── kdtree.h               # KD-Tree 加速
│   └── octree.h               # 八叉树和均匀网格
├── src/
│   └── main.cpp               # 主程序
├── examples/                   # 示例程序
│   ├── basic_scene.cpp        # 基础场景
│   ├── 01_basic_sphere.cpp    # 基础球体
│   ├── 02_complex_scene.cpp   # 复杂场景
│   ├── 03_primitives.cpp      # 几何图元
│   ├── 04_path_tracing.cpp    # 路径追踪
│   ├── 05_depth_of_field.cpp  # 景深效果
│   ├── 06_textures.cpp        # 纹理渲染
│   ├── 07_advanced_materials.cpp  # 高级材质
│   ├── 08_motion_blur.cpp     # 运动模糊
│   ├── 09_acceleration.cpp    # 加速结构
│   └── 10_sampling.cpp        # 采样策略
├── tests/                      # 测试程序
├── docs/                       # 文档
└── CMakeLists.txt              # 构建配置
```

## 示例说明

### 示例 1：基础球体渲染
展示如何渲染简单的球体场景，包含漫反射、金属和玻璃材质。

### 示例 2：复杂场景渲染
渲染包含多个随机球体的复杂场景，展示材质多样性。

### 示例 3：几何图元渲染
展示各种几何图元的渲染：球体、平面、三角形、盒子、圆柱体。

### 示例 4：路径追踪渲染
使用路径追踪算法渲染场景，支持全局光照和多线程。

### 示例 5：景深效果
展示景深相机的使用，创建焦点清晰、背景模糊的效果。

### 示例 6：纹理渲染
展示各种纹理的使用：棋盘格、噪声、渐变等。

### 示例 7：高级材质渲染
展示高级材质：自发光、各向异性、清漆、混合材质等。

### 示例 8：运动模糊
展示运动模糊效果，让移动的物体看起来更自然。

### 示例 9：加速结构
展示各种加速结构的使用和性能对比。

### 示例 10：采样策略
展示不同采样策略对抗锯齿效果的影响。

## 性能优化

### 多线程渲染
- 使用 `std::thread` 进行并行渲染
- 支持自定义线程数
- 行级并行处理

### 采样优化
- 分层采样减少噪声
- Halton 低差异序列
- 自适应采样

### 加速结构
- BVH：快速包围盒测试
- KD-Tree：高效空间查询
- 八叉树：3D 空间分割
- 均匀网格：简单快速

## 输出格式

所有示例输出 PPM 格式的图像文件，可以使用以下工具查看：

- **Linux**: `eog`, `feh`, `xdg-open`
- **macOS**: `Preview`, `open`
- **Windows**: `Paint`, `IrfanView`

## 扩展建议

1. **添加更多几何体**：贝塞尔曲面、NURBS、细分曲面
2. **实现更多渲染算法**：Metropolis 光传输、辐射度
3. **添加 GPU 加速**：CUDA、OpenCL
4. **支持更多纹理格式**：PNG、JPEG、HDR
5. **实现实时预览**：OpenGL、Vulkan

## 参考资源

- [Ray Tracing in One Weekend](https://raytracing.github.io/)
- [Physically Based Rendering](http://www.pbr-book.org/)
- [Ray Tracing from the Ground Up](https://www.amazon.com/Ray-Tracing-Ground-Up-Kevin/dp/1568812728)

## 许可证

本项目仅用于学习目的。
