#pragma once

#include "hitable.h"
#include <memory>
#include <cmath>

namespace rt {

// 圆柱体（沿 Y 轴）
class Cylinder : public Hitable {
public:
    Vec3 center;                        // 底面中心
    double radius;                      // 半径
    double height;                      // 高度
    std::shared_ptr<Material> material;

    Cylinder(const Vec3& center, double radius, double height,
             std::shared_ptr<Material> material)
        : center(center), radius(radius), height(height), material(material) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        bool hit_any = false;
        double closest_t = t_max;

        // 1. 光线与圆柱侧面相交
        Vec3 oc = ray.origin - center;
        double a = ray.direction.x * ray.direction.x + ray.direction.z * ray.direction.z;
        double b = oc.x * ray.direction.x + oc.z * ray.direction.z;
        double c = oc.x * oc.x + oc.z * oc.z - radius * radius;
        double discriminant = b * b - a * c;

        if (discriminant >= 0) {
            double sqrtd = std::sqrt(discriminant);
            for (int sign = -1; sign <= 1; sign += 2) {
                double t = (-b + sign * sqrtd) / a;
                if (t >= t_min && t <= closest_t) {
                    Vec3 p = ray.at(t);
                    double y_local = p.y - center.y;
                    if (y_local >= 0 && y_local <= height) {
                        closest_t = t;
                        rec.t = t;
                        rec.point = p;
                        Vec3 outward_normal = Vec3(p.x - center.x, 0, p.z - center.z).normalize();
                        rec.set_face_normal(ray, outward_normal);
                        rec.material = material;
                        hit_any = true;
                    }
                }
            }
        }

        // 2. 光线与底面相交
        if (std::fabs(ray.direction.y) > 1e-10) {
            double t = (center.y - ray.origin.y) / ray.direction.y;
            if (t >= t_min && t <= closest_t) {
                Vec3 p = ray.at(t);
                double dx = p.x - center.x;
                double dz = p.z - center.z;
                if (dx * dx + dz * dz <= radius * radius) {
                    closest_t = t;
                    rec.t = t;
                    rec.point = p;
                    rec.set_face_normal(ray, Vec3(0, -1, 0));
                    rec.material = material;
                    hit_any = true;
                }
            }
        }

        // 3. 光线与顶面相交
        if (std::fabs(ray.direction.y) > 1e-10) {
            double top_y = center.y + height;
            double t = (top_y - ray.origin.y) / ray.direction.y;
            if (t >= t_min && t <= closest_t) {
                Vec3 p = ray.at(t);
                double dx = p.x - center.x;
                double dz = p.z - center.z;
                if (dx * dx + dz * dz <= radius * radius) {
                    closest_t = t;
                    rec.t = t;
                    rec.point = p;
                    rec.set_face_normal(ray, Vec3(0, 1, 0));
                    rec.material = material;
                    hit_any = true;
                }
            }
        }

        return hit_any;
    }
};

// 圆锥体（沿 Y 轴）
class Cone : public Hitable {
public:
    Vec3 apex;                          // 锥顶
    double radius;                      // 底面半径
    double height;                      // 高度
    std::shared_ptr<Material> material;

    Cone(const Vec3& apex, double radius, double height,
         std::shared_ptr<Material> material)
        : apex(apex), radius(radius), height(height), material(material) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // 圆锥参数
        double k = radius / height;     // 斜率
        double k2 = k * k;
        Vec3 base_center = apex - Vec3(0, height, 0);

        Vec3 oc = ray.origin - apex;
        double a = ray.direction.x * ray.direction.x + ray.direction.z * ray.direction.z
                  - k2 * ray.direction.y * ray.direction.y;
        double b = oc.x * ray.direction.x + oc.z * ray.direction.z
                  - k2 * oc.y * ray.direction.y;
        double c = oc.x * oc.x + oc.z * oc.z - k2 * oc.y * oc.y;

        double discriminant = b * b - a * c;
        if (discriminant < 0) return false;

        double sqrtd = std::sqrt(discriminant);
        double t = (-b - sqrtd) / a;
        if (t < t_min || t > t_max) {
            t = (-b + sqrtd) / a;
            if (t < t_min || t > t_max) return false;
        }

        Vec3 p = ray.at(t);
        double y_local = p.y - apex.y;

        // 检查是否在圆锥高度范围内
        if (y_local > 0 || y_local < -height) return false;

        rec.t = t;
        rec.point = p;
        Vec3 outward_normal = Vec3(p.x - apex.x, 0, p.z - apex.z).normalize();
        double slope = k;
        outward_normal = Vec3(outward_normal.x, slope, outward_normal.z).normalize();
        rec.set_face_normal(ray, outward_normal);
        rec.material = material;
        return true;
    }
};

} // namespace rt
