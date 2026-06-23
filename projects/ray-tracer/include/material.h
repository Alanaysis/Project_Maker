#pragma once

#include "ray.h"
#include "hitable.h"
#include <random>

namespace rt {

// 工具函数：生成随机数
inline double random_double() {
    static std::mt19937 gen(42); // 固定种子以保证可重复性
    static std::uniform_real_distribution<double> dist(0.0, 1.0);
    return dist(gen);
}

inline double random_double(double min, double max) {
    return min + (max - min) * random_double();
}

// 生成单位球内的随机向量
inline Vec3 random_in_unit_sphere() {
    while (true) {
        Vec3 p(random_double(-1, 1), random_double(-1, 1), random_double(-1, 1));
        if (p.length_squared() < 1) return p;
    }
}

// 生成单位向量
inline Vec3 random_unit_vector() {
    return random_in_unit_sphere().normalize();
}

// 材质基类
class Material {
public:
    virtual ~Material() = default;

    // 散射函数：计算光线如何被材质散射
    // 返回 true 表示光线被散射，false 表示光线被吸收
    virtual bool scatter(const Ray& ray_in, const HitRecord& rec,
                         Vec3& attenuation, Ray& scattered) const = 0;
};

// 漫反射材质（Lambertian）
class Lambertian : public Material {
public:
    Vec3 albedo; // 反照率（颜色）

    Lambertian(const Vec3& albedo) : albedo(albedo) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 scatter_direction = rec.normal + random_unit_vector();

        // 处理退化情况
        if (scatter_direction.length_squared() < 1e-10) {
            scatter_direction = rec.normal;
        }

        scattered = Ray(rec.point, scatter_direction);
        attenuation = albedo;
        return true;
    }
};

// 金属材质
class Metal : public Material {
public:
    Vec3 albedo;  // 反射率
    double fuzz;  // 模糊度（0-1）

    Metal(const Vec3& albedo, double fuzz = 0.0)
        : albedo(albedo), fuzz(fuzz < 1 ? fuzz : 1) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 reflected = ray_in.direction.reflect(rec.normal);
        scattered = Ray(rec.point, reflected + random_in_unit_sphere() * fuzz);
        attenuation = albedo;
        return scattered.direction.dot(rec.normal) > 0;
    }
};

// 电介质材质（玻璃、水等）
class Dielectric : public Material {
public:
    double ir; // 折射率

    Dielectric(double ir) : ir(ir) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        attenuation = Vec3(1.0, 1.0, 1.0); // 透明材质不吸收光线
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

private:
    // Schlick's approximation for reflectance
    static double reflectance(double cosine, double ref_idx) {
        auto r0 = (1 - ref_idx) / (1 + ref_idx);
        r0 = r0 * r0;
        return r0 + (1 - r0) * std::pow((1 - cosine), 5);
    }
};

} // namespace rt
