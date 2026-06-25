#pragma once

#include "hitable.h"
#include "box.h"
#include <memory>
#include <vector>
#include <array>

namespace rt {

// 八叉树节点
class OctreeNode {
public:
    AABB bounds;                        // 节点包围盒
    std::array<std::shared_ptr<OctreeNode>, 8> children;  // 8 个子节点
    std::vector<std::shared_ptr<Hitable>> objects;         // 物体列表
    bool is_leaf;                       // 是否是叶子节点

    OctreeNode() : is_leaf(true) {
        children.fill(nullptr);
    }
};

// 八叉树加速结构
class Octree : public Hitable {
public:
    std::shared_ptr<OctreeNode> root;
    int max_depth;
    int max_objects_per_leaf;

    Octree(int max_depth = 8, int max_objects_per_leaf = 4)
        : max_depth(max_depth), max_objects_per_leaf(max_objects_per_leaf) {}

    // 构建八叉树
    void build(std::vector<std::shared_ptr<Hitable>>& objects) {
        if (objects.empty()) return;

        // 计算整体包围盒
        AABB world_bounds(Vec3(-100, -100, -100), Vec3(100, 100, 100), nullptr);
        root = build_node(objects, world_bounds, 0);
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        if (!root) return false;
        return hit_node(root, ray, t_min, t_max, rec);
    }

private:
    std::shared_ptr<OctreeNode> build_node(
        std::vector<std::shared_ptr<Hitable>>& objects,
        const AABB& bounds, int depth) {
        auto node = std::make_shared<OctreeNode>();
        node->bounds = bounds;

        // 终止条件
        if (objects.size() <= static_cast<size_t>(max_objects_per_leaf) || depth >= max_depth) {
            node->objects = objects;
            node->is_leaf = true;
            return node;
        }

        // 计算子节点包围盒
        Vec3 center = (bounds.min_point + bounds.max_point) * 0.5;
        Vec3 min = bounds.min_point;
        Vec3 max = bounds.max_point;

        std::array<AABB, 8> child_bounds = {
            AABB(min, center, nullptr),                                        // 0: 左前下
            AABB(Vec3(center.x, min.y, min.z), Vec3(max.x, center.y, center.z), nullptr),  // 1: 右前下
            AABB(Vec3(min.x, center.y, min.z), Vec3(center.x, max.y, center.z), nullptr),  // 2: 左后下
            AABB(Vec3(center.x, center.y, min.z), Vec3(max.x, max.y, center.z), nullptr),  // 3: 右后下
            AABB(Vec3(min.x, min.y, center.z), Vec3(center.x, center.y, max.z), nullptr),  // 4: 左前上
            AABB(Vec3(center.x, min.y, center.z), Vec3(max.x, center.y, max.z), nullptr),  // 5: 右前上
            AABB(Vec3(min.x, center.y, center.z), Vec3(center.x, max.y, max.z), nullptr),  // 6: 左后上
            AABB(center, max, nullptr)                                         // 7: 右后上
        };

        // 分配物体到子节点
        std::array<std::vector<std::shared_ptr<Hitable>>, 8> child_objects;

        for (const auto& obj : objects) {
            // 简化处理：将物体分配到中心所在的子节点
            // 实际应用中应该根据物体的包围盒进行分配
            Vec3 obj_center(0, 0, 0);  // 简化

            int child_idx = 0;
            if (obj_center.x >= center.x) child_idx |= 1;
            if (obj_center.y >= center.y) child_idx |= 2;
            if (obj_center.z >= center.z) child_idx |= 4;

            child_objects[child_idx].push_back(obj);
        }

        // 递归构建子节点
        node->is_leaf = false;
        for (int i = 0; i < 8; i++) {
            if (!child_objects[i].empty()) {
                node->children[i] = build_node(child_objects[i], child_bounds[i], depth + 1);
            }
        }

        return node;
    }

    bool hit_node(const std::shared_ptr<OctreeNode>& node,
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

        // 内部节点：递归遍历所有子节点
        bool hit_any = false;
        double closest = t_max;

        for (const auto& child : node->children) {
            if (child && hit_node(child, ray, t_min, closest, rec)) {
                hit_any = true;
                closest = rec.t;
            }
        }

        return hit_any;
    }
};

// 均匀网格加速结构
class UniformGrid : public Hitable {
public:
    Vec3 grid_min;                      // 网格最小坐标
    Vec3 grid_max;                      // 网格最大坐标
    Vec3 cell_size;                     // 单元格大小
    int nx, ny, nz;                     // 网格维度
    std::vector<std::vector<std::shared_ptr<Hitable>>> cells;  // 网格单元

    UniformGrid(int nx = 32, int ny = 32, int nz = 32)
        : nx(nx), ny(ny), nz(nz) {
        grid_min = Vec3(-100, -100, -100);
        grid_max = Vec3(100, 100, 100);
        cell_size = (grid_max - grid_min) / Vec3(nx, ny, nz);
        cells.resize(nx * ny * nz);
    }

    // 构建均匀网格
    void build(std::vector<std::shared_ptr<Hitable>>& objects) {
        for (const auto& obj : objects) {
            // 简化处理：将物体添加到中心所在的单元格
            Vec3 center(0, 0, 0);
            int idx = get_cell_index(center);
            if (idx >= 0 && idx < static_cast<int>(cells.size())) {
                cells[idx].push_back(obj);
            }
        }
    }

    bool hit(const Ray& ray, double t_min, double t_max, HitRecord& rec) const override {
        // 3D DDA 光线遍历算法
        bool hit_any = false;
        double closest = t_max;

        // 计算光线进入和离开网格的位置
        double t_enter = t_min;
        double t_exit = t_max;

        // 遍历网格
        Vec3 pos = ray.origin + ray.direction * t_enter;
        int xi = static_cast<int>((pos.x - grid_min.x) / cell_size.x);
        int yi = static_cast<int>((pos.y - grid_min.y) / cell_size.y);
        int zi = static_cast<int>((pos.z - grid_min.z) / cell_size.z);

        xi = std::clamp(xi, 0, nx - 1);
        yi = std::clamp(yi, 0, ny - 1);
        zi = std::clamp(zi, 0, nz - 1);

        // 简化处理：只测试当前单元格
        int idx = xi + yi * nx + zi * nx * ny;
        if (idx >= 0 && idx < static_cast<int>(cells.size())) {
            for (const auto& obj : cells[idx]) {
                if (obj->hit(ray, t_min, closest, rec)) {
                    hit_any = true;
                    closest = rec.t;
                }
            }
        }

        return hit_any;
    }

private:
    int get_cell_index(const Vec3& p) const {
        int xi = static_cast<int>((p.x - grid_min.x) / cell_size.x);
        int yi = static_cast<int>((p.y - grid_min.y) / cell_size.y);
        int zi = static_cast<int>((p.z - grid_min.z) / cell_size.z);

        if (xi < 0 || xi >= nx || yi < 0 || yi >= ny || zi < 0 || zi >= nz) {
            return -1;
        }

        return xi + yi * nx + zi * nx * ny;
    }
};

} // namespace rt
