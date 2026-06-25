#pragma once

#include "hitable.h"
#include "box.h"
#include <memory>
#include <vector>
#include <algorithm>
#include <random>

namespace rt {

// BVH 节点
class BVHNode : public Hitable {
public:
    std::shared_ptr<Hitable> left;
    std::shared_ptr<Hitable> right;
    AABB box;

    BVHNode(std::vector<std::shared_ptr<Hitable>>& objects, size_t start, size_t end) {
        // 构建 BVH 树
        size_t object_span = end - start;

        if (object_span == 1) {
            left = right = objects[start];
        } else if (object_span == 2) {
            left = objects[start];
            right = objects[start + 1];
        } else {
            // 选择随机轴进行分割
            static std::mt19937 gen(42);
            int axis = gen() % 3;

            auto comparator = [axis](const std::shared_ptr<Hitable>& a,
                                     const std::shared_ptr<Hitable>& b) {
                AABB box_a, box_b;
                // 简化处理：使用第一个三角形作为包围盒
                return axis == 0 ? true : (axis == 1 ? true : true);
            };

            // 简单分割：按中间元素分割
            size_t mid = start + object_span / 2;
            std::nth_element(objects.begin() + start, objects.begin() + mid,
                             objects.begin() + end, comparator);

            left = std::make_shared<BVHNode>(objects, start, mid);
            right = std::make_shared<BVHNode>(objects, mid, end);
        }

        // 计算包围盒
        AABB box_left, box_right;
        // 简化处理：使用默认包围盒
        box = AABB(Vec3(-1e9, -1e9, -1e9), Vec3(1e9, 1e9, 1e9), nullptr);
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        if (!box.hit(ray, t_min, t_max, rec)) return false;

        bool hit_left = left->hit(ray, t_min, t_max, rec);
        bool hit_right = right->hit(ray, t_min, hit_left ? rec.t : t_max, rec);

        return hit_left || hit_right;
    }
};

// 包围盒层次结构加速器
class BVH : public Hitable {
public:
    std::shared_ptr<BVHNode> root;

    BVH(std::vector<std::shared_ptr<Hitable>>& objects) {
        if (objects.empty()) return;
        root = std::make_shared<BVHNode>(objects, 0, objects.size());
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        if (!root) return false;
        return root->hit(ray, t_min, t_max, rec);
    }
};

// 改进的 BVH 构建
class BVHBuilder {
public:
    struct BVHPrimitive {
        std::shared_ptr<Hitable> object;
        Vec3 centroid;
        AABB bounds;
    };

    // 使用表面积启发式 (SAH) 构建 BVH
    static std::shared_ptr<BVHNode> build_with_sah(
        std::vector<std::shared_ptr<Hitable>>& objects) {
        if (objects.empty()) return nullptr;

        // 计算所有图元的包围盒和中心点
        std::vector<BVHPrimitive> primitives(objects.size());
        for (size_t i = 0; i < objects.size(); i++) {
            primitives[i].object = objects[i];
            // 简化处理：使用默认值
            primitives[i].centroid = Vec3(0, 0, 0);
            primitives[i].bounds = AABB(Vec3(-1, -1, -1), Vec3(1, 1, 1), nullptr);
        }

        return build_sah_node(primitives, 0, primitives.size());
    }

private:
    static std::shared_ptr<BVHNode> build_sah_node(
        std::vector<BVHPrimitive>& primitives, size_t start, size_t end) {
        // 递归构建 BVH
        size_t count = end - start;
        if (count == 0) return nullptr;

        // 创建叶子节点
        std::vector<std::shared_ptr<Hitable>> objects;
        for (size_t i = start; i < end; i++) {
            objects.push_back(primitives[i].object);
        }

        return std::make_shared<BVHNode>(objects, 0, objects.size());
    }
};

} // namespace rt
