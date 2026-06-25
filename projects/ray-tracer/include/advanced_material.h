#pragma once

#include "material.h"
#include "texture.h"
#include <memory>

namespace rt {

// 自发光材质
class Emissive : public Material {
public:
    Vec3 emit_color;
    double intensity;

    Emissive(const Vec3& emit_color, double intensity = 1.0)
        : emit_color(emit_color), intensity(intensity) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        return false;  // 自发光材质不散射光线
    }

    Vec3 emitted(double u, double v, const Vec3& p) const {
        return emit_color * intensity;
    }
};

// 纹理材质
class TexturedMaterial : public Material {
public:
    std::shared_ptr<Texture> texture;
    double fuzz;                        // 金属模糊度

    TexturedMaterial(std::shared_ptr<Texture> texture, double fuzz = 0.0)
        : texture(texture), fuzz(fuzz) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 color = texture->value(0, 0, rec.point);

        if (fuzz > 0) {
            // 金属材质
            Vec3 reflected = ray_in.direction.reflect(rec.normal);
            scattered = Ray(rec.point, reflected + random_in_unit_sphere() * fuzz);
            attenuation = color;
            return scattered.direction.dot(rec.normal) > 0;
        } else {
            // 漫反射材质
            Vec3 scatter_direction = rec.normal + random_unit_vector();
            if (scatter_direction.length_squared() < 1e-10) {
                scatter_direction = rec.normal;
            }
            scattered = Ray(rec.point, scatter_direction);
            attenuation = color;
            return true;
        }
    }
};

// 各向异性材质（用于金属效果）
class Anisotropic : public Material {
public:
    Vec3 albedo;
    double roughness_x, roughness_y;    // 各方向的粗糙度

    Anisotropic(const Vec3& albedo, double roughness_x = 0.1, double roughness_y = 0.1)
        : albedo(albedo), roughness_x(roughness_x), roughness_y(roughness_y) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 reflected = ray_in.direction.reflect(rec.normal);

        // 各向异性扰动
        Vec3 tangent = rec.normal.cross(Vec3(0, 1, 0)).normalize();
        Vec3 bitangent = rec.normal.cross(tangent);

        Vec3 perturbation = tangent * random_double(-roughness_x, roughness_x) +
                           bitangent * random_double(-roughness_y, roughness_y);

        scattered = Ray(rec.point, (reflected + perturbation).normalize());
        attenuation = albedo;
        return scattered.direction.dot(rec.normal) > 0;
    }
};

// 多层材质（清漆效果）
class Clearcoat : public Material {
public:
    std::shared_ptr<Material> base;     // 基础材质
    double clearcoat_strength;          // 清漆强度
    double clearcoat_roughness;         // 清漆粗糙度

    Clearcoat(std::shared_ptr<Material> base, double strength = 0.5, double roughness = 0.1)
        : base(base), clearcoat_strength(strength), clearcoat_roughness(roughness) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        // 决定光线是否通过清漆层
        if (random_double() < clearcoat_strength) {
            // 清漆层：镜面反射
            Vec3 reflected = ray_in.direction.reflect(rec.normal);
            Vec3 fuzz = random_in_unit_sphere() * clearcoat_roughness;
            scattered = Ray(rec.point, (reflected + fuzz).normalize());
            attenuation = Vec3(1.0, 1.0, 1.0);  // 清漆不改变颜色
            return scattered.direction.dot(rec.normal) > 0;
        } else {
            // 基础材质
            return base->scatter(ray_in, rec, attenuation, scattered);
        }
    }
};

// 混合材质
class BlendMaterial : public Material {
public:
    std::shared_ptr<Material> material1;
    std::shared_ptr<Material> material2;
    double ratio;                       // 混合比例 (0-1)

    BlendMaterial(std::shared_ptr<Material> m1, std::shared_ptr<Material> m2, double ratio)
        : material1(m1), material2(m2), ratio(ratio) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        if (random_double() < ratio) {
            return material1->scatter(ray_in, rec, attenuation, scattered);
        } else {
            return material2->scatter(ray_in, rec, attenuation, scattered);
        }
    }
};

// 菲涅尔材质
class FresnelBlend : public Material {
public:
    std::shared_ptr<Material> material1; // 入射角接近 0 度时的材质
    std::shared_ptr<Material> material2; // 入射角接近 90 度时的材质

    FresnelBlend(std::shared_ptr<Material> m1, std::shared_ptr<Material> m2)
        : material1(m1), material2(m2) {}

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        // Schlick 近似计算菲涅尔系数
        double cos_theta = std::fmax((-ray_in.direction).dot(rec.normal), 0.0);
        double r0 = 0.04;  // 基础反射率
        double fresnel = r0 + (1.0 - r0) * std::pow(1.0 - cos_theta, 5);

        if (random_double() < fresnel) {
            return material1->scatter(ray_in, rec, attenuation, scattered);
        } else {
            return material2->scatter(ray_in, rec, attenuation, scattered);
        }
    }
};

} // namespace rt
