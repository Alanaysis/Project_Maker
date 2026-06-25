#pragma once

#include "vec3.h"
#include "ray.h"
#include "hitable.h"
#include <memory>
#include <vector>
#include <random>

namespace rt {

// 运动模糊
class MovingSphere : public Hitable {
public:
    Vec3 center0, center1;              // 起始和结束位置
    double time0, time1;                // 时间范围
    double radius;
    std::shared_ptr<Material> material;

    MovingSphere(const Vec3& center0, const Vec3& center1,
                 double time0, double time1, double radius,
                 std::shared_ptr<Material> material)
        : center0(center0), center1(center1), time0(time0), time1(time1),
          radius(radius), material(material) {}

    Vec3 center(double time) const {
        return center0 + (center1 - center0) * ((time - time0) / (time1 - time0));
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // 使用运动中心进行相交测试
        Vec3 center_t = center(0.5);  // 使用中间时间
        Vec3 oc = ray.origin - center_t;
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
        Vec3 outward_normal = (rec.point - center_t) / radius;
        rec.set_face_normal(ray, outward_normal);
        rec.material = material;

        return true;
    }
};

// 景深相机
class DepthOfFieldCamera {
public:
    Vec3 origin;
    Vec3 lower_left_corner;
    Vec3 horizontal, vertical;
    Vec3 u, v, w;
    double lens_radius;
    double focus_distance;

    DepthOfFieldCamera(const Vec3& lookfrom, const Vec3& lookat, const Vec3& vup,
                       double vfov, double aspect_ratio, double aperture,
                       double focus_distance)
        : origin(lookfrom), focus_distance(focus_distance) {
        double theta = vfov * M_PI / 180.0;
        double h = std::tan(theta / 2.0);
        double viewport_height = 2.0 * h;
        double viewport_width = aspect_ratio * viewport_height;

        w = (lookfrom - lookat).normalize();
        u = vup.cross(w).normalize();
        v = w.cross(u);

        horizontal = u * viewport_width * focus_distance;
        vertical = v * viewport_height * focus_distance;
        lower_left_corner = origin - horizontal / 2.0 - vertical / 2.0 - w * focus_distance;

        lens_radius = aperture / 2.0;
    }

    Ray get_ray(double s, double t) const {
        Vec3 rd = random_in_unit_disk() * lens_radius;
        Vec3 offset = u * rd.x + v * rd.y;

        return Ray(
            origin + offset,
            lower_left_corner + horizontal * s + vertical * t - origin - offset
        );
    }

private:
    static Vec3 random_in_unit_disk() {
        static std::mt19937 gen(42);
        static std::uniform_real_distribution<double> dist(-1.0, 1.0);
        while (true) {
            Vec3 p(dist(gen), dist(gen), 0);
            if (p.length_squared() < 1) return p;
        }
    }
};

// 体积渲染
class Volume : public Hitable {
public:
    std::shared_ptr<Hitable> boundary;  // 边界形状
    double density;                     // 密度
    Vec3 color;                         // 颜色

    Volume(std::shared_ptr<Hitable> boundary, double density, const Vec3& color)
        : boundary(boundary), density(density), color(color) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // 使用烟雾渲染技术
        HitRecord rec1, rec2;

        if (!boundary->hit(ray, -std::numeric_limits<double>::infinity(),
                          std::numeric_limits<double>::infinity(), rec1)) {
            return false;
        }

        if (!boundary->hit(ray, rec1.t + 0.0001,
                          std::numeric_limits<double>::infinity(), rec2)) {
            return false;
        }

        // 限制到有效范围
        rec1.t = std::fmax(rec1.t, t_min);
        rec2.t = std::fmin(rec2.t, t_max);

        if (rec1.t >= rec2.t) return false;

        // 随机选择散射点
        double ray_length = ray.direction.length();
        double distance_inside = (rec2.t - rec1.t) * ray_length;
        double hit_distance = -(1.0 / density) * std::log(random_double());

        if (hit_distance > distance_inside) return false;

        rec.t = rec1.t + hit_distance / ray_length;
        rec.point = ray.at(rec.t);
        rec.normal = Vec3(1, 0, 0);  // 任意方向
        rec.material = std::make_shared<Lambertian>(color);

        return true;
    }

private:
    static double random_double() {
        static std::mt19937 gen(42);
        static std::uniform_real_distribution<double> dist(0.0, 1.0);
        return dist(gen);
    }
};

// 抗锯齿采样器
class Sampler {
public:
    // 多重采样抗锯齿 (MSAA)
    static std::vector<Vec2> msaa_samples(int samples_per_pixel) {
        std::vector<Vec2> samples;
        int sqrt_samples = static_cast<int>(std::sqrt(samples_per_pixel));

        for (int i = 0; i < sqrt_samples; i++) {
            for (int j = 0; j < sqrt_samples; j++) {
                double u = (i + 0.5) / sqrt_samples;
                double v = (j + 0.5) / sqrt_samples;
                samples.push_back(Vec2(u, v));
            }
        }

        return samples;
    }

    // Stratified sampling
    static std::vector<Vec2> stratified_samples(int samples_per_pixel) {
        std::vector<Vec2> samples;
        int sqrt_samples = static_cast<int>(std::sqrt(samples_per_pixel));
        std::mt19937 gen(42);
        std::uniform_real_distribution<double> dist(0.0, 1.0);

        for (int i = 0; i < sqrt_samples; i++) {
            for (int j = 0; j < sqrt_samples; j++) {
                double u = (i + dist(gen)) / sqrt_samples;
                double v = (j + dist(gen)) / sqrt_samples;
                samples.push_back(Vec2(u, v));
            }
        }

        return samples;
    }

    // Halton 序列低差异采样
    static std::vector<Vec2> halton_samples(int count) {
        std::vector<Vec2> samples;
        for (int i = 0; i < count; i++) {
            double u = halton(i, 2);
            double v = halton(i, 3);
            samples.push_back(Vec2(u, v));
        }
        return samples;
    }

private:
    static double halton(int index, int base) {
        double f = 1.0;
        double r = 0.0;
        int i = index;

        while (i > 0) {
            f /= base;
            r += f * (i % base);
            i /= base;
        }

        return r;
    }
};

// 焦散效果
class Caustics {
public:
    // 计算焦散效果
    static Vec3 compute_caustics(const Vec3& point, const Vec3& normal,
                                 const std::shared_ptr<Hitable>& world) {
        // 简化实现：使用反射光线模拟焦散
        Vec3 caustic_color(0, 0, 0);

        // 从反射点发射光线
        for (int i = 0; i < 16; i++) {
            Vec3 reflected = normal + random_unit_vector();
            Ray caustic_ray(point, reflected);

            HitRecord rec;
            if (world->hit(caustic_ray, 0.001, 1000, rec)) {
                caustic_color += Vec3(0.1, 0.1, 0.05);  // 简化焦散颜色
            }
        }

        return caustic_color / 16.0;
    }

private:
    static Vec3 random_unit_vector() {
        static std::mt19937 gen(42);
        static std::uniform_real_distribution<double> dist(-1.0, 1.0);
        Vec3 p;
        do {
            p = Vec3(dist(gen), dist(gen), dist(gen));
        } while (p.length_squared() > 1.0);
        return p.normalize();
    }
};

} // namespace rt
