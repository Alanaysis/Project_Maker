#pragma once

#include "hitable.h"
#include <memory>
#include <array>

namespace rt {

// 轴对齐包围盒 (AABB)
class AABB : public Hitable {
public:
    Vec3 min_point;
    Vec3 max_point;
    std::shared_ptr<Material> material;

    AABB() : min_point(Vec3(0, 0, 0)), max_point(Vec3(0, 0, 0)), material(nullptr) {}

    AABB(const Vec3& min_point, const Vec3& max_point,
         std::shared_ptr<Material> material)
        : min_point(min_point), max_point(max_point), material(material) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // 使用 slab 方法进行光线-盒子相交
        double tmin = t_min;
        double tmax = t_max;
        Vec3 hit_normal;

        for (int i = 0; i < 3; i++) {
            double origin_val, dir_val, min_val, max_val;
            Vec3 axis_normal;

            if (i == 0) {
                origin_val = ray.origin.x;
                dir_val = ray.direction.x;
                min_val = min_point.x;
                max_val = max_point.x;
                axis_normal = Vec3(-1, 0, 0);
            } else if (i == 1) {
                origin_val = ray.origin.y;
                dir_val = ray.direction.y;
                min_val = min_point.y;
                max_val = max_point.y;
                axis_normal = Vec3(0, -1, 0);
            } else {
                origin_val = ray.origin.z;
                dir_val = ray.direction.z;
                min_val = min_point.z;
                max_val = max_point.z;
                axis_normal = Vec3(0, 0, -1);
            }

            double inv_dir = 1.0 / dir_val;
            double t0 = (min_val - origin_val) * inv_dir;
            double t1 = (max_val - origin_val) * inv_dir;

            if (inv_dir < 0.0) std::swap(t0, t1);

            // 更新 tmin 和 tmax
            Vec3 normal_candidate = (t0 > tmin) ? axis_normal : hit_normal;
            if (t0 > tmin) {
                tmin = t0;
                hit_normal = axis_normal;
                // 调整法线方向
                if (i == 0 && ray.direction.x > 0) hit_normal = Vec3(1, 0, 0);
                else if (i == 1 && ray.direction.y > 0) hit_normal = Vec3(0, 1, 0);
                else if (i == 2 && ray.direction.z > 0) hit_normal = Vec3(0, 0, 1);
            }
            tmax = std::fmin(tmax, t1);

            if (tmin > tmax) return false;
        }

        rec.t = tmin;
        rec.point = ray.at(tmin);
        rec.set_face_normal(ray, hit_normal);
        rec.material = material;
        return true;
    }

    // 获取包围盒的中心点
    Vec3 center() const {
        return (min_point + max_point) * 0.5;
    }

    // 获取包围盒的尺寸
    Vec3 size() const {
        return max_point - min_point;
    }
};

// 旋转体：绕 Y 轴旋转的盒子
class Box : public Hitable {
public:
    Vec3 center;
    Vec3 half_size;                     // 半尺寸
    double angle;                       // 旋转角度（弧度）
    std::shared_ptr<Material> material;

    Box(const Vec3& center, const Vec3& half_size, double angle,
        std::shared_ptr<Material> material)
        : center(center), half_size(half_size), angle(angle), material(material) {}

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // 将光线变换到盒子的局部坐标系
        double cos_a = std::cos(-angle);
        double sin_a = std::sin(-angle);

        Vec3 local_origin = ray.origin - center;
        Vec3 rotated_origin(
            local_origin.x * cos_a - local_origin.z * sin_a,
            local_origin.y,
            local_origin.x * sin_a + local_origin.z * cos_a
        );

        Vec3 rotated_dir(
            ray.direction.x * cos_a - ray.direction.z * sin_a,
            ray.direction.y,
            ray.direction.x * sin_a + ray.direction.z * cos_a
        );

        Ray local_ray(rotated_origin + center, rotated_dir);

        // 使用 AABB 相交测试
        AABB box(center - half_size, center + half_size, material);
        if (box.hit(local_ray, t_min, t_max, rec)) {
            // 将法线旋转回世界坐标系
            Vec3 local_normal = rec.normal;
            rec.normal = Vec3(
                local_normal.x * cos_a + local_normal.z * sin_a,
                local_normal.y,
                -local_normal.x * sin_a + local_normal.z * cos_a
            );
            return true;
        }
        return false;
    }
};

} // namespace rt
