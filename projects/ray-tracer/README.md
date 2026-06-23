# 光线追踪渲染器

一个用 C++ 实现的简易光线追踪渲染器，用于理解光线追踪原理。

## 项目概述

本项目实现了一个基本的光线追踪渲染器，支持：

- 基本的光线追踪算法
- 球体和平面求交
- 多种材质（漫反射、金属、电介质）
- 相机系统（支持景深）
- 多重采样抗锯齿
- PPM 图像输出

## 核心循环

```
相机 → 光线发射 → 场景求交 → 光照计算 → 像素颜色
```

## 技术栈

- **语言**：C++17
- **构建**：CMake 3.10+
- **依赖**：无外部依赖

## 快速开始

### 构建项目

```bash
cd projects/ray-tracer
mkdir build
cd build
cmake ..
make
```

### 运行程序

```bash
# 默认场景
./ray-tracer --scene default --output output.ppm

# 复杂场景
./ray-tracer --scene complex --output complex.ppm

# 测试场景
./ray-tracer --scene test --output test.ppm
```

### 运行测试

```bash
ctest
```

### 运行示例

```bash
./basic_scene
```

## 项目结构

```
projects/ray-tracer/
├── CMakeLists.txt          # 构建配置
├── README.md               # 本文件
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档目录
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
├── include/                # 头文件
│   ├── vec3.h              # 三维向量
│   ├── ray.h               # 光线
│   ├── hitable.h           # 可命中物体
│   ├── sphere.h            # 球体和平面
│   ├── material.h          # 材质
│   ├── camera.h            # 相机
│   ├── renderer.h          # 渲染器
│   └── scene.h             # 场景工厂
├── src/                    # 源代码
│   └── main.cpp            # 主程序
├── tests/                  # 测试文件
│   ├── test_vec3.cpp       # Vec3 测试
│   ├── test_ray.cpp        # Ray 测试
│   ├── test_sphere.cpp     # Sphere 测试
│   └── test_renderer.cpp   # Renderer 测试
└── examples/               # 示例文件
    └── basic_scene.cpp     # 基础场景示例
```

## 核心组件

### Vec3（三维向量）

实现三维向量的基本运算，包括：
- 加法、减法、标量乘法
- 点积、叉积
- 单位化、反射、折射

### Ray（光线）

光线表示为 `P(t) = origin + t * direction`，其中：
- origin：起点
- direction：方向（单位向量）
- t：参数

### Hitable（可命中物体）

抽象基类，支持：
- Sphere（球体）
- Plane（平面）
- HitableList（物体集合）

### Material（材质）

材质基类，支持：
- Lambertian（漫反射）
- Metal（金属）
- Dielectric（电介质）

### Camera（相机）

相机系统，支持：
- 视角（FOV）控制
- 光圈和景深效果
- 相机坐标系

### Renderer（渲染器）

渲染器，支持：
- 递归颜色计算
- 多重采样抗锯齿
- 伽马校正
- PPM 格式输出

## 学习目标

通过本项目，你将学到：

1. **光线追踪算法**
   - 光线-物体求交
   - 递归光线追踪
   - 全局光照

2. **几何数学**
   - 向量运算
   - 点积和叉积
   - 光线-球体求交
   - 光线-平面求交

3. **材质模型**
   - Lambertian 漫反射
   - 金属反射
   - 电介质折射

4. **相机系统**
   - 视角控制
   - 景深效果

5. **图像处理**
   - 多重采样抗锯齿
   - 伽马校正
   - PPM 格式输出

## 示例输出

渲染默认场景：

```bash
./ray-tracer --scene default --output default.ppm
```

生成的图像包含：
- 三个球体（蓝色漫反射、金属、玻璃）
- 灰色地面
- 天空渐变背景
- 金属球有模糊反射
- 玻璃球有折射效果

## 文档

详细文档请参考 `docs/` 目录：

- [01-RESEARCH.md](docs/01-RESEARCH.md) - 技术调研
- [02-DESIGN.md](docs/02-DESIGN.md) - 系统设计
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试文档
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发指南

## 学习笔记

学习过程记录请参考 [LEARNING_NOTES.md](LEARNING_NOTES.md)。

## 扩展方向

1. **添加新材质**
   - 发光材质
   - 各向异性材质
   - 次表面散射

2. **添加新物体**
   - 三角形
   - 网格
   - 曲面

3. **性能优化**
   - BVH 空间划分
   - 并行渲染
   - GPU 加速

4. **高级特性**
   - 纹理映射
   - 环境光遮蔽
   - 焦散

## 参考资源

- [Ray Tracing in One Weekend](https://raytracing.github.io/)
- [Scratchapixel](https://www.scratchapixel.com/)
- [smallpt](http://www.kevinbeason.com/smallpt/)

## 许可证

本项目仅供学习使用。
