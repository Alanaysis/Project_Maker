# 03-IMPLEMENTATION.md - 光线追踪渲染器实现文档

## 1. 项目结构

```
projects/ray-tracer/
├── CMakeLists.txt          # 构建配置
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 本文档
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
├── tests/                  # 测试
│   ├── test_vec3.cpp       # Vec3 测试
│   ├── test_ray.cpp        # Ray 测试
│   ├── test_sphere.cpp     # Sphere 测试
│   └── test_renderer.cpp   # Renderer 测试
└── examples/               # 示例
    └── basic_scene.cpp     # 基础场景示例
```

## 2. 核心实现

### 2.1 Vec3（三维向量）

**文件**：`include/vec3.h`

**关键实现**：

```cpp
class Vec3 {
public:
    double x, y, z;

    // 向量运算
    Vec3 operator+(const Vec3& v) const;
    Vec3 operator-(const Vec3& v) const;
    Vec3 operator*(double t) const;

    // 点积和叉积
    double dot(const Vec3& v) const;
    Vec3 cross(const Vec3& v) const;

    // 单位化
    Vec3 normalize() const;

    // 反射
    Vec3 reflect(const Vec3& normal) const;

    // 折射
    Vec3 refract(const Vec3& normal, double eta_ratio) const;
};
```

**实现要点**：
- 使用 `double` 类型保证精度
- 运算符重载提高代码可读性
- 处理零向量的特殊情况

### 2.2 Ray（光线）

**文件**：`include/ray.h`

**关键实现**：

```cpp
class Ray {
public:
    Vec3 origin;    // 起点
    Vec3 direction; // 方向（单位向量）

    Ray(const Vec3& origin, const Vec3& direction)
        : origin(origin), direction(direction.normalize()) {}

    Vec3 at(double t) const {
        return origin + direction * t;
    }
};
```

**实现要点**：
- 构造时自动单位化方向向量
- `at()` 方法用于计算光线上任意点

### 2.3 Hitable（可命中物体）

**文件**：`include/hitable.h`

**关键实现**：

```cpp
struct HitRecord {
    Vec3 point;
    Vec3 normal;
    double t;
    bool front_face;
    std::shared_ptr<Material> material;

    void set_face_normal(const Ray& ray, const Vec3& outward_normal) {
        front_face = ray.direction.dot(outward_normal) < 0;
        normal = front_face ? outward_normal : -outward_normal;
    }
};

class Hitable {
public:
    virtual bool hit(const Ray& ray, double t_min, double t_max,
                     HitRecord& rec) const = 0;
};

class HitableList : public Hitable {
public:
    std::vector<std::shared_ptr<Hitable>> objects;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override {
        HitRecord temp_rec;
        bool hit_anything = false;
        double closest_so_far = t_max;

        for (const auto& object : objects) {
            if (object->hit(ray, t_min, closest_so_far, temp_rec)) {
                hit_anything = true;
                closest_so_far = temp_rec.t;
                rec = temp_rec;
            }
        }
        return hit_anything;
    }
};
```

**实现要点**：
- 使用虚函数实现多态
- HitRecord 记录命中信息
- HitableList 维护最近命中

### 2.4 Sphere（球体）

**文件**：`include/sphere.h`

**关键实现**：

```cpp
class Sphere : public Hitable {
public:
    Vec3 center;
    double radius;
    std::shared_ptr<Material> material;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override {
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
};
```

**实现要点**：
- 使用二次方程求解
- 处理两个根，选择最近的有效根
- 设置面法线方向

### 2.5 Material（材质）

**文件**：`include/material.h`

**关键实现**：

```cpp
class Material {
public:
    virtual bool scatter(const Ray& ray_in, const HitRecord& rec,
                         Vec3& attenuation, Ray& scattered) const = 0;
};

class Lambertian : public Material {
public:
    Vec3 albedo;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 scatter_direction = rec.normal + random_unit_vector();
        if (scatter_direction.length_squared() < 1e-10) {
            scatter_direction = rec.normal;
        }
        scattered = Ray(rec.point, scatter_direction);
        attenuation = albedo;
        return true;
    }
};

class Metal : public Material {
public:
    Vec3 albedo;
    double fuzz;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 reflected = ray_in.direction.reflect(rec.normal);
        scattered = Ray(rec.point, reflected + random_in_unit_sphere() * fuzz);
        attenuation = albedo;
        return scattered.direction.dot(rec.normal) > 0;
    }
};

class Dielectric : public Material {
public:
    double ir;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        attenuation = Vec3(1.0, 1.0, 1.0);
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
};
```

**实现要点**：
- Lambertian：随机散射方向
- Metal：镜面反射 + 模糊
- Dielectric：折射 + 全内反射

### 2.6 Camera（相机）

**文件**：`include/camera.h`

**关键实现**：

```cpp
class Camera {
public:
    Vec3 origin;
    Vec3 lower_left_corner;
    Vec3 horizontal;
    Vec3 vertical;
    Vec3 u, v, w;
    double lens_radius;

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

    Ray get_ray(double s, double t) const {
        Vec3 rd = random_in_unit_disk() * lens_radius;
        Vec3 offset = u * rd.x + v * rd.y;
        return Ray(
            origin + offset,
            lower_left_corner + horizontal * s + vertical * t - origin - offset
        );
    }
};
```

**实现要点**：
- 支持视角（FOV）控制
- 支持光圈和景深效果
- 使用相机坐标系

### 2.7 Renderer（渲染器）

**文件**：`include/renderer.h`

**关键实现**：

```cpp
class Renderer {
public:
    RenderConfig config;
    Camera camera;
    std::shared_ptr<Hitable> world;

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

    void render(const std::string& filename) const {
        std::ofstream file(filename);
        file << "P3\n" << config.width << " " << config.height << "\n255\n";

        for (int j = config.height - 1; j >= 0; --j) {
            for (int i = 0; i < config.width; ++i) {
                Color pixel_color(0, 0, 0);
                for (int s = 0; s < config.samples_per_pixel; ++s) {
                    double u = (i + random_double()) / config.width;
                    double v = (j + random_double()) / config.height;
                    Ray ray = camera.get_ray(u, v);
                    pixel_color += ray_color(ray, config.max_depth);
                }
                int r = color_to_int(pixel_color.x, config.samples_per_pixel);
                int g = color_to_int(pixel_color.y, config.samples_per_pixel);
                int b = color_to_int(pixel_color.z, config.samples_per_pixel);
                file << r << " " << g << " " << b << "\n";
            }
        }
    }
};
```

**实现要点**：
- 递归颜色计算
- 多重采样抗锯齿
- 伽马校正
- PPM 格式输出

## 3. 场景工厂

**文件**：`include/scene.h`

提供三种预设场景：
- `create_default_scene()`：三个球体 + 地面
- `create_complex_scene()`：多个随机球体
- `create_test_scene()`：简单测试场景

## 4. 构建系统

**文件**：`CMakeLists.txt`

使用 CMake 构建：
```bash
mkdir build && cd build
cmake ..
make
```

运行程序：
```bash
./ray-tracer --scene default --output output.ppm
```

## 5. 关键技术点

### 5.1 数值稳定性

- 使用 epsilon（1e-10）避免浮点精度问题
- 光线 t_min 设为 0.001 避免自相交
- 处理零向量的单位化

### 5.2 递归深度限制

- 设置最大递归深度（默认 50）
- 深度为 0 时返回黑色

### 5.3 抗锯齿

- 对每个像素多次采样
- 取平均值作为最终颜色

### 5.4 伽马校正

- 线性空间渲染
- 输出前进行伽马校正：c' = sqrt(c)

## 6. 扩展点

### 6.1 添加新材质

继承 `Material` 类，实现 `scatter()` 方法。

### 6.2 添加新物体

继承 `Hitable` 类，实现 `hit()` 方法。

### 6.3 添加新场景

在 `SceneFactory` 中添加新的静态方法。

### 6.4 添加新相机模型

修改 `Camera` 类的 `get_ray()` 方法。

## 7. 性能优化方向

1. **空间划分**：BVH、KD-Tree
2. **并行渲染**：多线程、GPU 加速
3. **采样优化**：重要性采样、分层采样
4. **内存优化**：对象池、缓存友好的数据结构
