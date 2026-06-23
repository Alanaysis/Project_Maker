#pragma once

#include "hitable.h"
#include <memory>

namespace rt {

// 球体
class Sphere : public Hitable {
public:
    Vec3 center;                         // 球心
    double radius;                       // 半径
    std::shared_ptr<Material> material;  // 材质

    Sphere(Vec3 center, double radius, std::shared_ptr<Material> material)
        : center(center), radius(radius), material(material) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        Vec3 oc = ray.origin - center;
        double a = ray.direction.length_squared();
        double half_b = oc.dot(ray.direction);
        double c = oc.length_squared() - radius * radius;

        double discriminant = half_b * half_b - a * c;
        if (discriminant < 0) return false;

        double sqrtd = std::sqrt(discriminant);

        // 找到最近的在有效范围内的根
        double root = (-half_b - sqrtd) / a;
        if (root < t_min || t_max < root) {
            root = (-half_b + sqrtd) / a;
            if (root < t_min || t_max < root) {
                return false;
            }
        }

        rec.t = root;
        rec.point = ray.at(rec.t);
        Vec3 outward_normal = (rec.point - center) / radius;
        rec.set_face_normal(ray, outward_normal);
        rec.material = material;

        return true;
    }
};

// 平面（用于地面等）
class Plane : public Hitable {
public:
    Vec3 point;                          // 平面上一点
    Vec3 normal;                         // 法线
    std::shared_ptr<Material> material;  // 材质

    Plane(Vec3 point, Vec3 normal, std::shared_ptr<Material> material)
        : point(point), normal(normal.normalize()), material(material) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        double denom = normal.dot(ray.direction);

        // 光线与平面平行
        if (std::fabs(denom) < 1e-10) return false;

        double t = (point - ray.origin).dot(normal) / denom;
        if (t < t_min || t > t_max) return false;

        rec.t = t;
        rec.point = ray.at(t);
        rec.set_face_normal(ray, normal);
        rec.material = material;

        return true;
    }
};

} // namespace rt
