#pragma once

#include "hitable.h"
#include "box.h"
#include <memory>
#include <vector>
#include <algorithm>

namespace rt {

// KD-Tree 节点
class KDNode {
public:
    AABB bounds;                        // 节点包围盒
    std::shared_ptr<KDNode> left;       // 左子树
    std::shared_ptr<KDNode> right;      // 右子树
    std::vector<std::shared_ptr<Hitable>> objects;  // 叶子节点的物体
    int split_axis;                     // 分割轴
    double split_position;              // 分割位置
    bool is_leaf;                       // 是否是叶子节点

    KDNode() : split_axis(0), split_position(0), is_leaf(false) {}
};

// KD-Tree 加速结构
class KDTree : public Hitable {
public:
    std::shared_ptr<KDNode> root;
    int max_depth;                      // 最大深度
    int max_objects_per_leaf;           // 每个叶子节点的最大物体数

    KDTree(int max_depth = 20, int max_objects_per_leaf = 4)
        : max_depth(max_depth), max_objects_per_leaf(max_objects_per_leaf) {}

    // 构建 KD-Tree
    void build(std::vector<std::shared_ptr<Hitable>>& objects) {
        if (objects.empty()) return;

        // 计算整体包围盒
        AABB world_bounds(Vec3(1e10, 1e10, 1e10), Vec3(-1e10, -1e10, -1e10), nullptr);
        for (const auto& obj : objects) {
            // 简化处理：使用默认包围盒
            world_bounds = AABB(Vec3(-100, -100, -100), Vec3(100, 100, 100), nullptr);
        }

        root = build_node(objects, world_bounds, 0);
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        if (!root) return false;
        return hit_node(root, ray, t_min, t_max, rec);
    }

private:
    std::shared_ptr<KDNode> build_node(
        std::vector<std::shared_ptr<Hitable>>& objects,
        const AABB& bounds, int depth) {
        auto node = std::make_shared<KDNode>();
        node->bounds = bounds;

        // 终止条件
        if (objects.size() <= static_cast<size_t>(max_objects_per_leaf) || depth >= max_depth) {
            node->objects = objects;
            node->is_leaf = true;
            return node;
        }

        // 选择分割轴（轮换 x, y, z）
        node->split_axis = depth % 3;

        // 计算所有物体的中心点
        std::vector<Vec3> centroids(objects.size());
        for (size_t i = 0; i < objects.size(); i++) {
            centroids[i] = Vec3(0, 0, 0);  // 简化处理
        }

        // 按中心点排序（简化处理：直接按指针排序）
        int axis = node->split_axis;
        std::sort(objects.begin(), objects.end(),
                  [&centroids, axis](const std::shared_ptr<Hitable>& a,
                                     const std::shared_ptr<Hitable>& b) {
                      // 简化处理：使用默认排序
                      return a.get() < b.get();
                  });

        // 分割物体
        size_t mid = objects.size() / 2;
        std::vector<std::shared_ptr<Hitable>> left_objects(objects.begin(), objects.begin() + mid);
        std::vector<std::shared_ptr<Hitable>> right_objects(objects.begin() + mid, objects.end());

        // 创建子包围盒
        AABB left_bounds = bounds;
        AABB right_bounds = bounds;

        // 递归构建子树
        node->left = build_node(left_objects, left_bounds, depth + 1);
        node->right = build_node(right_objects, right_bounds, depth + 1);

        return node;
    }

    bool hit_node(const std::shared_ptr<KDNode>& node,
                  const Ray& ray, double t_min, double t_max, HitRecord& rec) const {
        if (!node) return false;

        // 检查包围盒
        if (!node->bounds.hit(ray, t_min, t_max, rec)) return false;

        if (node->is_leaf) {
            // 叶子节点：测试所有物体
            bool hit_any = false;
            HitRecord temp_rec;
            double closest = t_max;

            for (const auto& obj : node->objects) {
                if (obj->hit(ray, t_min, closest, temp_rec)) {
                    hit_any = true;
                    closest = temp_rec.t;
                    rec = temp_rec;
                }
            }
            return hit_any;
        }

        // 内部节点：递归遍历
        bool hit_left = hit_node(node->left, ray, t_min, t_max, rec);
        bool hit_right = hit_node(node->right, ray, t_min, hit_left ? rec.t : t_max, rec);

        return hit_left || hit_right;
    }
};

} // namespace rt
