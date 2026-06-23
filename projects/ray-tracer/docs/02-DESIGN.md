# 02-DESIGN.md - 光线追踪渲染器设计文档

## 1. 系统架构

### 1.1 核心模块

```
┌─────────────────────────────────────────────────────────┐
│                      主程序 (main.cpp)                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    渲染器 (Renderer)                      │
│  - 渲染配置                                              │
│  - 像素遍历                                              │
│  - 颜色计算                                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    相机 (Camera)                          │
│  - 光线生成                                              │
│  - 视角控制                                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  场景 (HitableList)                       │
│  - 物体集合                                              │
│  - 求交遍历                                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              可命中物体 (Sphere, Plane)                   │
│  - 几何形状                                              │
│  - 求交算法                                              │
│  - 材质引用                                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  材质 (Material)                          │
│  - Lambertian (漫反射)                                   │
│  - Metal (金属)                                          │
│  - Dielectric (电介质)                                   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
相机 (Camera)
    │
    │ 生成光线 Ray
    ▼
渲染器 (Renderer)
    │
    │ 遍历像素 (i, j)
    ▼
场景 (HitableList)
    │
    │ 求交检测
    ▼
物体 (Sphere, Plane)
    │
    │ 返回 HitRecord
    ▼
材质 (Material)
    │
    │ 计算散射
    ▼
颜色 (Color)
    │
    │ 伽马校正
    ▼
输出 (PPM文件)
```

## 2. 类设计

### 2.1 Vec3（三维向量）

```
Vec3
├── 属性: x, y, z
├── 运算符重载: +, -, *, /
├── 方法:
│   ├── dot() - 点积
│   ├── cross() - 叉积
│   ├── length() - 长度
│   ├── normalize() - 单位化
│   ├── reflect() - 反射
│   └── refract() - 折射
└── 工具函数: random_in_unit_sphere(), random_unit_vector()
```

### 2.2 Ray（光线）

```
Ray
├── 属性:
│   ├── origin - 起点
│   └── direction - 方向（单位向量）
└── 方法:
    └── at(t) - 计算光线上某点
```

### 2.3 HitRecord（命中记录）

```
HitRecord
├── 属性:
│   ├── point - 命中点
│   ├── normal - 法线
│   ├── t - 光线参数
│   ├── front_face - 是否正面
│   └── material - 材质
└── 方法:
    └── set_face_normal() - 设置面法线
```

### 2.4 Hitable（可命中物体）

```
Hitable (抽象基类)
├── 方法:
│   └── hit() - 纯虚函数
│
├── Sphere (球体)
│   ├── center - 球心
│   ├── radius - 半径
│   ├── material - 材质
│   └── hit() - 球体求交
│
├── Plane (平面)
│   ├── point - 平面上一点
│   ├── normal - 法线
│   ├── material - 材质
│   └── hit() - 平面求交
│
└── HitableList (物体集合)
    ├── objects - 物体列表
    └── hit() - 遍历求交
```

### 2.5 Material（材质）

```
Material (抽象基类)
├── 方法:
│   └── scatter() - 纯虚函数
│
├── Lambertian (漫反射)
│   ├── albedo - 反照率
│   └── scatter() - 随机散射
│
├── Metal (金属)
│   ├── albedo - 反射率
│   ├── fuzz - 模糊度
│   └── scatter() - 反射
│
└── Dielectric (电介质)
    ├── ir - 折射率
    └── scatter() - 反射/折射
```

### 2.6 Camera（相机）

```
Camera
├── 属性:
│   ├── origin - 相机位置
│   ├── lower_left_corner - 图像左下角
│   ├── horizontal - 水平方向
│   ├── vertical - 垂直方向
│   ├── u, v, w - 相机坐标系
│   └── lens_radius - 镜头半径
└── 方法:
    └── get_ray(s, t) - 生成光线
```

### 2.7 Renderer（渲染器）

```
Renderer
├── 属性:
│   ├── config - 渲染配置
│   ├── camera - 相机
│   └── world - 场景
└── 方法:
    ├── ray_color() - 计算光线颜色
    ├── render() - 渲染到文件
    └── render_to_buffer() - 渲染到缓冲区
```

## 3. 算法设计

### 3.1 光线-球体求交算法

```cpp
bool Sphere::hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) {
    Vec3 oc = ray.origin - center;
    double a = ray.direction.length_squared();
    double half_b = oc.dot(ray.direction);
    double c = oc.length_squared() - radius * radius;
    double discriminant = half_b * half_b - a * c;

    if (discriminant < 0) return false;

    double sqrtd = sqrt(discriminant);
    double root = (-half_b - sqrtd) / a;

    if (root < t_min || t_max < root) {
        root = (-half_b + sqrtd) / a;
        if (root < t_min || t_max < root) return false;
    }

    rec.t = root;
    rec.point = ray.at(rec.t);
    rec.set_face_normal(ray, (rec.point - center) / radius);
    rec.material = material;
    return true;
}
```

### 3.2 颜色计算算法

```cpp
Color Renderer::ray_color(const Ray& ray, int depth) {
    if (depth <= 0) return Color(0, 0, 0);

    HitRecord rec;
    if (world->hit(ray, 0.001, infinity, rec)) {
        Ray scattered;
        Vec3 attenuation;
        if (rec.material->scatter(ray, rec, attenuation, scattered)) {
            return attenuation * ray_color(scattered, depth - 1);
        }
        return Color(0, 0, 0);
    }

    // 背景渐变
    Vec3 unit = ray.direction.normalize();
    double t = 0.5 * (unit.y + 1.0);
    return Color(1, 1, 1) * (1 - t) + Color(0.5, 0.7, 1) * t;
}
```

### 3.3 Schlick 近似算法

```cpp
double reflectance(double cosine, double ref_idx) {
    auto r0 = (1 - ref_idx) / (1 + ref_idx);
    r0 = r0 * r0;
    return r0 + (1 - r0) * pow((1 - cosine), 5);
}
```

## 4. 接口设计

### 4.1 配置接口

```cpp
// 渲染配置
struct RenderConfig {
    int width;
    int height;
    int samples_per_pixel;
    int max_depth;
};

// 相机配置
struct CameraConfig {
    Vec3 lookfrom;
    Vec3 lookat;
    Vec3 vup;
    double vfov;
    double aspect_ratio;
    double aperture;
    double focus_dist;
};
```

### 4.2 场景工厂接口

```cpp
class SceneFactory {
public:
    static std::shared_ptr<HitableList> create_default_scene();
    static std::shared_ptr<HitableList> create_complex_scene();
    static std::shared_ptr<HitableList> create_test_scene();
};
```

## 5. 错误处理

### 5.1 数值稳定性

- 使用 epsilon（1e-10）避免浮点精度问题
- 光线 t_min 设为 0.001 避免自相交
- 处理零向量的单位化

### 5.2 边界情况

- 光线平行于平面
- 光线从物体内部发射
- 光线刚好切过物体
- 递归深度为 0

## 6. 性能考虑

### 6.1 时间复杂度

- 光线-物体求交：O(n)，n 为物体数量
- 总渲染：O(width × height × samples × depth × n)

### 6.2 优化方向

- 空间划分结构（BVH、KD-Tree）
- 并行渲染
- 采样优化（重要性采样）

## 7. 测试策略

### 7.1 单元测试

- Vec3 运算
- Ray 构造和求值
- 光线-球体求交
- 光线-平面求交
- 材质散射
- 颜色计算

### 7.2 集成测试

- 小场景渲染
- 输出文件格式验证

### 7.3 可视化验证

- 渲染测试图像
- 人工检查视觉效果
