#pragma once

#include "hitable.h"
#include <memory>

namespace rt {

// 三角形（Moller-Trumbore 算法）
class Triangle : public Hitable {
public:
    Vec3 v0, v1, v2;                    // 三个顶点
    Vec3 normal;                         // 预计算法线
    std::shared_ptr<Material> material;

    Triangle(const Vec3& v0, const Vec3& v1, const Vec3& v2,
             std::shared_ptr<Material> material)
        : v0(v0), v1(v1), v2(v2), material(material) {
        // 预计算法线
        normal = (v1 - v0).cross(v2 - v0).normalize();
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // Moller-Trumbore 光线-三角形相交算法
        const double EPSILON = 1e-10;
        Vec3 edge1 = v1 - v0;
        Vec3 edge2 = v2 - v0;
        Vec3 h = ray.direction.cross(edge2);
        double a = edge1.dot(h);

        // 光线与三角形平行
        if (a > -EPSILON && a < EPSILON) return false;

        double f = 1.0 / a;
        Vec3 s = ray.origin - v0;
        double u = f * s.dot(h);

        if (u < 0.0 || u > 1.0) return false;

        Vec3 q = s.cross(edge1);
        double v = f * ray.direction.dot(q);

        if (v < 0.0 || u + v > 1.0) return false;

        double t = f * edge2.dot(q);

        if (t > EPSILON && t >= t_min && t <= t_max) {
            rec.t = t;
            rec.point = ray.at(t);
            rec.set_face_normal(ray, normal);
            rec.material = material;
            return true;
        }

        return false;
    }
};

// 带纹理坐标的三角形
class TexturedTriangle : public Hitable {
public:
    Vec3 v0, v1, v2;
    Vec2 uv0, uv1, uv2;                // 纹理坐标
    Vec3 normal;
    std::shared_ptr<Material> material;

    TexturedTriangle(const Vec3& v0, const Vec3& v1, const Vec3& v2,
                     const Vec2& uv0, const Vec2& uv1, const Vec2& uv2,
                     std::shared_ptr<Material> material)
        : v0(v0), v1(v1), v2(v2), uv0(uv0), uv1(uv1), uv2(uv2), material(material) {
        normal = (v1 - v0).cross(v2 - v0).normalize();
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        const double EPSILON = 1e-10;
        Vec3 edge1 = v1 - v0;
        Vec3 edge2 = v2 - v0;
        Vec3 h = ray.direction.cross(edge2);
        double a = edge1.dot(h);

        if (a > -EPSILON && a < EPSILON) return false;

        double f = 1.0 / a;
        Vec3 s = ray.origin - v0;
        double u = f * s.dot(h);

        if (u < 0.0 || u > 1.0) return false;

        Vec3 q = s.cross(edge1);
        double v = f * ray.direction.dot(q);

        if (v < 0.0 || u + v > 1.0) return false;

        double t = f * edge2.dot(q);

        if (t > EPSILON && t >= t_min && t <= t_max) {
            rec.t = t;
            rec.point = ray.at(t);
            rec.set_face_normal(ray, normal);
            rec.material = material;
            // 计算插值纹理坐标
            double w = 1.0 - u - v;
            // rec.u = w * uv0.x + u * uv1.x + v * uv2.x;
            // rec.v = w * uv0.y + u * uv1.y + v * uv2.y;
            return true;
        }

        return false;
    }
};

} // namespace rt
