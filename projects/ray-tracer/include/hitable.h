#pragma once

#include "ray.h"
#include <memory>
#include <vector>

namespace rt {

class Material;

// 命中记录
struct HitRecord {
    Vec3 point;        // 命中点
    Vec3 normal;       // 法线
    double t;          // 光线参数
    bool front_face;   // 是否正面命中
    std::shared_ptr<Material> material; // 材质

    void set_face_normal(const Ray& ray, const Vec3& outward_normal) {
        front_face = ray.direction.dot(outward_normal) < 0;
        normal = front_face ? outward_normal : -outward_normal;
    }
};

// 可命中物体的抽象基类
class Hitable {
public:
    virtual ~Hitable() = default;
    virtual bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const = 0;
};

// 场景（可命中物体集合）
class HitableList : public Hitable {
public:
    std::vector<std::shared_ptr<Hitable>> objects;

    HitableList() {}
    HitableList(std::shared_ptr<Hitable> object) { add(object); }

    void add(std::shared_ptr<Hitable> object) {
        objects.push_back(object);
    }

    void clear() {
        objects.clear();
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
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

} // namespace rt
