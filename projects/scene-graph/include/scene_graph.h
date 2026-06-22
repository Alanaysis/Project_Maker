#pragma once

#include "scene_node.h"
#include "bounds.h"
#include <vector>
#include <functional>

namespace sg {

/**
 * Camera - 摄像机
 *
 * 定义视图和投影参数，用于计算视锥体
 */
class Camera {
public:
    Camera()
        : position_(0, 0, 5)
        , target_(0, 0, 0)
        , up_(0, 1, 0)
        , fov_y_deg_(60.0f)
        , aspect_ratio_(16.0f / 9.0f)
        , near_plane_(0.1f)
        , far_plane_(1000.0f) {}

    Camera(const Vec3& pos, const Vec3& target, float fov, float aspect, float near, float far)
        : position_(pos), target_(target), up_(0, 1, 0)
        , fov_y_deg_(fov), aspect_ratio_(aspect)
        , near_plane_(near), far_plane_(far) {}

    // 设置方法
    void set_position(const Vec3& pos) { position_ = pos; }
    void set_target(const Vec3& target) { target_ = target; }
    void set_fov(float fov_deg) { fov_y_deg_ = fov_deg; }
    void set_aspect_ratio(float aspect) { aspect_ratio_ = aspect; }
    void set_near_far(float near, float far) { near_plane_ = near; far_plane_ = far; }

    // 获取方法
    const Vec3& get_position() const { return position_; }
    const Vec3& get_target() const { return target_; }
    float get_fov() const { return fov_y_deg_; }
    float get_aspect_ratio() const { return aspect_ratio_; }
    float get_near() const { return near_plane_; }
    float get_far() const { return far_plane_; }

    /**
     * 获取视图矩阵
     */
    Mat4 get_view_matrix() const {
        return Mat4::look_at(position_, target_, up_);
    }

    /**
     * 获取投影矩阵
     */
    Mat4 get_projection_matrix() const {
        const float deg2rad = 3.14159265358979f / 180.0f;
        return Mat4::perspective(fov_y_deg_ * deg2rad, aspect_ratio_, near_plane_, far_plane_);
    }

    /**
     * 获取 View-Projection 组合矩阵
     */
    Mat4 get_view_projection_matrix() const {
        return get_projection_matrix() * get_view_matrix();
    }

    /**
     * 从摄像机参数构建视锥体
     */
    Frustum get_frustum() const {
        return Frustum::from_view_projection(get_view_projection_matrix());
    }

private:
    Vec3 position_;
    Vec3 target_;
    Vec3 up_;
    float fov_y_deg_;
    float aspect_ratio_;
    float near_plane_;
    float far_plane_;
};

/**
 * CullResult - 裁剪结果
 *
 * 记录裁剪过程的统计信息
 */
struct CullResult {
    size_t total_nodes = 0;       // 遍历的总节点数
    size_t visible_nodes = 0;     // 可见节点数
    size_t culled_nodes = 0;      // 被裁剪的节点数
    size_t early_exits = 0;       // 因父节点被裁剪而提前退出的次数

    void reset() {
        total_nodes = visible_nodes = culled_nodes = early_exits = 0;
    }
};

/**
 * SceneGraph - 场景图管理器
 *
 * ⭐ 核心类：管理整个场景图的生命周期和核心操作
 *
 * 核心循环：
 * 场景图 → 遍历 → 变换计算 → 裁剪 → 渲染
 *
 * 1. 遍历：深度优先遍历场景图树
 * 2. 变换计算：自顶向下计算世界变换矩阵
 * 3. 裁剪：使用视锥体测试每个节点的可见性
 * 4. 渲染：收集可见节点列表供渲染器使用
 */
class SceneGraph {
public:
    SceneGraph() : root_(std::make_shared<SceneNode>("Root")) {}

    /**
     * 获取根节点
     */
    SceneNodePtr get_root() const {
        return root_;
    }

    /**
     * 设置摄像机
     */
    void set_camera(const Camera& camera) {
        camera_ = camera;
    }

    /**
     * 获取摄像机
     */
    const Camera& get_camera() const {
        return camera_;
    }

    /**
     * ⭐ 更新场景图
     * 执行变换层级更新（自顶向下）
     */
    void update() {
        if (root_) {
            root_->update_transforms();
        }
    }

    /**
     * ⭐ 视锥裁剪
     * 从根节点开始，递归测试每个节点是否在视锥体内
     *
     * 裁剪策略：
     * 1. 如果节点不可见，跳过该节点及其所有子节点
     * 2. 如果节点的 AABB 在视锥体外，跳过该节点及其所有子节点
     * 3. 如果节点有可渲染对象且在视锥体内，加入可见列表
     *
     * @return 裁剪统计结果
     */
    CullResult cull() {
        CullResult result;
        visible_nodes_.clear();

        if (!root_) return result;

        Frustum frustum = camera_.get_frustum();
        cull_recursive(root_, frustum, result, false);

        return result;
    }

    /**
     * 获取可见节点列表（在 cull() 之后调用）
     */
    const std::vector<SceneNodePtr>& get_visible_nodes() const {
        return visible_nodes_;
    }

    /**
     * 遍历整个场景图（深度优先）
     */
    void traverse(const std::function<void(const SceneNodePtr&)>& visitor) {
        if (root_) {
            root_->traverse_dfs(visitor);
        }
    }

    /**
     * 获取场景图中的总节点数
     */
    size_t total_node_count() const {
        return root_ ? root_->total_node_count() : 0;
    }

    /**
     * 根据名称查找节点
     */
    SceneNodePtr find(const std::string& name) {
        return root_ ? root_->find(name) : nullptr;
    }

private:
    /**
     * ⭐ 递归裁剪实现
     *
     * 这是视锥裁剪的核心算法：
     * - 使用 AABB 与视锥体的 6 个平面进行测试
     * - 如果父节点被裁剪，所有子节点被跳过（early_exit）
     * - 这种层级裁剪是场景图的关键优化
     */
    void cull_recursive(const SceneNodePtr& node, const Frustum& frustum,
                        CullResult& result, bool parent_culled) {
        if (!node) return;

        result.total_nodes++;

        // 如果父节点已被裁剪，当前节点也被裁剪（早期剔除）
        if (parent_culled) {
            result.early_exits++;
            result.culled_nodes++;
            // 递归子节点，但标记为已被裁剪
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, true);
            }
            return;
        }

        // 检查节点可见性标志
        if (!node->is_visible()) {
            result.culled_nodes++;
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, true);
            }
            return;
        }

        // 如果节点没有可渲染对象，跳过裁剪测试，直接处理子节点
        // 这类节点只是分组节点，不需要参与裁剪
        if (!node->get_renderable()) {
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, false);
            }
            return;
        }

        // ⭐ 视锥体与 AABB 相交测试
        const AABB& bounds = node->get_world_bounds();
        bool in_frustum = frustum.test_aabb(bounds);

        if (!in_frustum) {
            result.culled_nodes++;
            // 该节点在视锥体外，裁剪其所有子节点
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, true);
            }
            return;
        }

        // 节点在视锥体内
        result.visible_nodes++;
        visible_nodes_.push_back(node);

        // 递归处理子节点
        for (const auto& child : node->get_children()) {
            cull_recursive(child, frustum, result, false);
        }
    }

    SceneNodePtr root_;
    Camera camera_;
    std::vector<SceneNodePtr> visible_nodes_;
};

} // namespace sg
