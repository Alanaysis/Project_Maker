# 05-DEVELOPMENT.md - 光线追踪渲染器开发文档

## 1. 开发环境

### 1.1 系统要求

- **操作系统**：Linux、macOS、Windows
- **编译器**：支持 C++17 的编译器（GCC 7+、Clang 5+、MSVC 2017+）
- **构建工具**：CMake 3.10+
- **内存**：至少 512MB RAM

### 1.2 依赖项

- **无外部依赖**：纯 C++ 实现
- **标准库**：cmath、iostream、fstream、vector、memory、random、algorithm

## 2. 快速开始

### 2.1 获取代码

```bash
cd projects/ray-tracer
```

### 2.2 构建项目

```bash
mkdir build
cd build
cmake ..
make
```

### 2.3 运行程序

```bash
# 默认场景
./ray-tracer --scene default --output output.ppm

# 复杂场景
./ray-tracer --scene complex --output complex.ppm

# 测试场景
./ray-tracer --scene test --output test.ppm
```

### 2.4 运行测试

```bash
# 运行所有测试
ctest

# 或单独运行
./test_vec3
./test_ray
./test_sphere
./test_renderer
```

### 2.5 运行示例

```bash
./basic_scene
```

## 3. 项目结构

```
projects/ray-tracer/
├── CMakeLists.txt          # 构建配置
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档目录
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
└── examples/               # 示例文件
```

## 4. 开发流程

### 4.1 开发步骤

1. **环境搭建**：安装 C++ 编译器和 CMake
2. **项目初始化**：创建目录结构和 CMakeLists.txt
3. **核心组件**：实现 Vec3、Ray、Hitable
4. **几何体**：实现 Sphere、Plane
5. **材质系统**：实现 Lambertian、Metal、Dielectric
6. **相机系统**：实现 Camera
7. **渲染器**：实现 Renderer
8. **场景工厂**：实现 SceneFactory
9. **主程序**：实现 main.cpp
10. **测试**：编写和运行测试
11. **文档**：编写文档

### 4.2 开发原则

- **模块化**：每个组件独立，便于测试和复用
- **抽象化**：使用抽象基类和接口
- **可扩展**：易于添加新材质和物体
- **可测试**：组件可独立测试

## 5. 核心组件开发

### 5.1 Vec3 开发

**目标**：实现三维向量的基本运算

**实现步骤**：
1. 定义类结构
2. 实现构造函数
3. 实现运算符重载
4. 实现点积、叉积
5. 实现单位化、反射、折射
6. 编写测试

**关键代码**：
```cpp
Vec3 reflect(const Vec3& normal) const {
    return *this - normal * 2.0 * this->dot(normal);
}

Vec3 refract(const Vec3& normal, double eta_ratio) const {
    double cos_theta = std::fmin((-(*this)).dot(normal), 1.0);
    Vec3 r_out_perp = (*this + normal * cos_theta) * eta_ratio;
    Vec3 r_out_parallel = normal * (-std::sqrt(std::fabs(1.0 - r_out_perp.length_squared())));
    return r_out_perp + r_out_parallel;
}
```

### 5.2 Ray 开发

**目标**：实现光线表示

**实现步骤**：
1. 定义类结构
2. 实现构造函数（自动单位化方向）
3. 实现 at() 方法

**关键代码**：
```cpp
Ray(const Vec3& origin, const Vec3& direction)
    : origin(origin), direction(direction.normalize()) {}

Vec3 at(double t) const {
    return origin + direction * t;
}
```

### 5.3 Hitable 开发

**目标**：实现可命中物体的抽象接口

**实现步骤**：
1. 定义 HitRecord 结构
2. 定义 Hitable 抽象基类
3. 实现 HitableList
4. 实现 Sphere
5. 实现 Plane

**关键代码**：
```cpp
bool Sphere::hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) {
    Vec3 oc = ray.origin - center;
    double a = ray.direction.length_squared();
    double half_b = oc.dot(ray.direction);
    double c = oc.length_squared() - radius * radius;
    double discriminant = half_b * half_b - a * c;

    if (discriminant < 0) return false;

    double sqrtd = std::sqrt(discriminant);
    double root = (-half_b - sqrtd) / a;

    if (root < t_min || t_max < root) {
        root = (-half_b + sqrtd) / a;
        if (root < t_min || t_max < root) return false;
    }

    rec.t = root;
    rec.point = ray.at(rec.t);
    Vec3 outward_normal = (rec.point - center) / radius;
    rec.set_face_normal(ray, outward_normal);
    rec.material = material;
    return true;
}
```

### 5.4 Material 开发

**目标**：实现材质系统

**实现步骤**：
1. 定义 Material 抽象基类
2. 实现 Lambertian
3. 实现 Metal
4. 实现 Dielectric
5. 实现 Schlick 近似

**关键代码**：
```cpp
// Lambertian
bool scatter(...) {
    Vec3 scatter_direction = rec.normal + random_unit_vector();
    scattered = Ray(rec.point, scatter_direction);
    attenuation = albedo;
    return true;
}

// Metal
bool scatter(...) {
    Vec3 reflected = ray_in.direction.reflect(rec.normal);
    scattered = Ray(rec.point, reflected + random_in_unit_sphere() * fuzz);
    attenuation = albedo;
    return scattered.direction.dot(rec.normal) > 0;
}

// Dielectric
bool scatter(...) {
    double refraction_ratio = rec.front_face ? (1.0 / ir) : ir;
    Vec3 unit_direction = ray_in.direction.normalize();
    double cos_theta = std::fmin((-unit_direction).dot(rec.normal), 1.0);
    double sin_theta = std::sqrt(1.0 - cos_theta * cos_theta);

    bool cannot_refract = refraction_ratio * sin_theta > 1.0;
    Vec3 direction;

    if (cannot_refract || reflectance(cos_theta, refraction_ratio) > random_double()) {
        direction = unit_direction.reflect(rec.normal);
    } else {
        direction = unit_direction.refract(rec.normal, refraction_ratio);
    }

    scattered = Ray(rec.point, direction);
    return true;
}
```

### 5.5 Camera 开发

**目标**：实现相机系统

**实现步骤**：
1. 定义 CameraConfig
2. 实现 Camera 类
3. 计算相机坐标系
4. 实现 get_ray() 方法

**关键代码**：
```cpp
Camera(const CameraConfig& config) {
    double theta = config.vfov * M_PI / 180.0;
    double h = std::tan(theta / 2.0);
    double viewport_height = 2.0 * h;
    double viewport_width = config.aspect_ratio * viewport_height;

    w = (config.lookfrom - config.lookat).normalize();
    u = config.vup.cross(w).normalize();
    v = w.cross(u);

    origin = config.lookfrom;
    horizontal = u * viewport_width * config.focus_dist;
    vertical = v * viewport_height * config.focus_dist;
    lower_left_corner = origin - horizontal / 2.0 - vertical / 2.0 - w * config.focus_dist;

    lens_radius = config.aperture / 2.0;
}
```

### 5.6 Renderer 开发

**目标**：实现渲染器

**实现步骤**：
1. 定义 RenderConfig
2. 实现 ray_color() 方法
3. 实现 render() 方法
4. 实现 render_to_buffer() 方法

**关键代码**：
```cpp
Color ray_color(const Ray& ray, int depth) const {
    HitRecord rec;

    if (depth <= 0) return Color(0, 0, 0);

    if (world->hit(ray, 0.001, std::numeric_limits<double>::infinity(), rec)) {
        Ray scattered;
        Vec3 attenuation;
        if (rec.material->scatter(ray, rec, attenuation, scattered)) {
            return attenuation * ray_color(scattered, depth - 1);
        }
        return Color(0, 0, 0);
    }

    Vec3 unit_direction = ray.direction.normalize();
    double t = 0.5 * (unit_direction.y + 1.0);
    return Color(1.0, 1.0, 1.0) * (1.0 - t) + Color(0.5, 0.7, 1.0) * t;
}
```

## 6. 调试技巧

### 6.1 常见问题

1. **自相交**
   - 问题：光线命中自身
   - 解决：使用 t_min = 0.001

2. **数值溢出**
   - 问题：除以零或极小值
   - 解决：检查分母，使用 epsilon

3. **递归过深**
   - 问题：栈溢出
   - 解决：设置最大递归深度

4. **颜色溢出**
   - 问题：颜色值超出范围
   - 解决：使用 std::clamp

### 6.2 调试方法

1. **打印中间值**
   ```cpp
   std::cout << "t = " << rec.t << std::endl;
   std::cout << "point = " << rec.point << std::endl;
   std::cout << "normal = " << rec.normal << std::endl;
   ```

2. **渲染小图像**
   - 快速验证算法
   - 减少调试时间

3. **使用测试场景**
   - 隔离问题
   - 简化调试

## 7. 性能优化

### 7.1 当前性能

- 分辨率：400x225
- 采样数：50
- 渲染时间：约 10-30 秒（取决于场景复杂度）

### 7.2 优化方向

1. **空间划分**
   - BVH（Bounding Volume Hierarchy）
   - KD-Tree
   - 减少求交计算

2. **并行渲染**
   - 多线程
   - GPU 加速
   - 分布式渲染

3. **采样优化**
   - 重要性采样
   - 分层采样
   - 减少采样数

4. **内存优化**
   - 对象池
   - 缓存友好的数据结构
   - 减少内存分配

## 8. 扩展开发

### 8.1 添加新材质

1. 继承 Material 类
2. 实现 scatter() 方法
3. 在 SceneFactory 中使用

**示例**：
```cpp
class Emissive : public Material {
public:
    Vec3 emit_color;

    Emissive(const Vec3& color) : emit_color(color) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        return false; // 不散射，只发光
    }

    Vec3 emit() const {
        return emit_color;
    }
};
```

### 8.2 添加新物体

1. 继承 Hitable 类
2. 实现 hit() 方法
3. 在 SceneFactory 中使用

**示例**：
```cpp
class Triangle : public Hitable {
public:
    Vec3 v0, v1, v2;
    std::shared_ptr<Material> material;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override {
        // Möller–Trumbore intersection algorithm
        // ...
    }
};
```

### 8.3 添加新相机模型

1. 修改 Camera 类
2. 实现新的 get_ray() 方法

**示例**：
```cpp
// 正交相机
Ray get_ray(double s, double t) const {
    Vec3 rd = random_in_unit_disk() * lens_radius;
    Vec3 offset = u * rd.x + v * rd.y;
    return Ray(
        lower_left_corner + horizontal * s + vertical * t,
        -w  // 固定方向
    );
}
```

## 9. 文档维护

### 9.1 文档更新

- 代码变更时更新文档
- 添加新功能时更新文档
- 修复 bug 时更新文档

### 9.2 文档格式

- 使用 Markdown 格式
- 保持文档结构清晰
- 使用代码示例

## 10. 版本控制

### 10.1 Git 工作流

1. **主分支**：master
2. **开发分支**：dev
3. **功能分支**：feature/xxx
4. **修复分支**：fix/xxx

### 10.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

## 11. 学习资源

### 11.1 推荐书籍

- "Ray Tracing in One Weekend" - Peter Shirley
- "Fundamentals of Computer Graphics" - Marschner & Shirley
- "Physically Based Rendering" - Pharr & Humphreys

### 11.2 在线资源

- raytracing.github.io
- Scratchapixel
- Computer Graphics from Scratch

### 11.3 开源项目

- smallpt
- pbrt
- Mitsuba
