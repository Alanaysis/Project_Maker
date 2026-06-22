#pragma once

#include "transform.h"
#include "bounds.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <algorithm>
#include <cstdint>

namespace sg {

// 前向声明
class SceneNode;

using SceneNodePtr = std::shared_ptr<SceneNode>;
using SceneNodeConstPtr = std::shared_ptr<const SceneNode>;

/**
 * Renderable - 可渲染对象接口
 *
 * 场景图节点可以关联一个可渲染对象（网格、光源等）
 * 这是一个抽象接口，用户可以扩展实现具体的渲染对象
 */
class Renderable {
public:
    virtual ~Renderable() = default;

    /**
     * 获取本地包围盒（在模型空间中）
     */
    virtual AABB get_local_bounds() const = 0;

    /**
     * 获取可渲染对象的类型名称（用于调试）
     */
    virtual std::string get_type() const = 0;
};

using RenderablePtr = std::shared_ptr<Renderable>;

/**
 * SceneNode - 场景图节点
 *
 * ⭐ 核心概念：
 * - 场景图是一种树形数据结构，用于组织 3D 场景中的物体
 * - 每个节点有一个变换（Transform），相对于其父节点
 * - 变换是层级化的：子节点的世界变换 = 父节点世界变换 × 子节点局部变换
 * - 包围盒也是层级化的：父节点的包围盒包含所有子节点的包围盒
 *
 * 变换传播流程：
 * 1. 更新节点局部变换矩阵
 * 2. 乘以父节点的世界变换矩阵，得到世界变换矩阵
 * 3. 递归更新所有子节点
 *
 * 裁剪流程：
 * 1. 从根节点开始遍历
 * 2. 测试每个节点的 AABB 是否在视锥体内
 * 3. 如果父节点被裁剪，所有子节点也被裁剪（早期剔除）
 */
class SceneNode : public std::enable_shared_from_this<SceneNode> {
public:
    /**
     * 构造函数
     * @param name 节点名称（用于调试和查找）
     */
    explicit SceneNode(const std::string& name = "Node")
        : name_(name)
        , id_(next_id_++)
        , visible_(true)
        , local_transform_dirty_(true)
        , world_transform_dirty_(true) {}

    ~SceneNode() = default;

    // ========== 节点层级管理 ==========

    /**
     * 添加子节点
     * ⭐ 这建立了父子关系，子节点的变换将相对于父节点
     */
    void add_child(const SceneNodePtr& child) {
        if (!child) return;

        // 如果子节点已有父节点，先从旧父节点移除
        if (auto old_parent = child->parent_.lock()) {
            old_parent->remove_child(child);
        }

        child->parent_ = weak_from_this();
        children_.push_back(child);
        child->mark_dirty();
    }

    /**
     * 移除子节点
     */
    bool remove_child(const SceneNodePtr& child) {
        auto it = std::find(children_.begin(), children_.end(), child);
        if (it != children_.end()) {
            (*it)->parent_.reset();
            children_.erase(it);
            return true;
        }
        return false;
    }

    /**
     * 根据名称查找子节点（递归）
     */
    SceneNodePtr find(const std::string& name) {
        if (name_ == name) return shared_from_this();
        for (auto& child : children_) {
            if (auto found = child->find(name)) {
                return found;
            }
        }
        return nullptr;
    }

    /**
     * 根据 ID 查找子节点（递归）
     */
    SceneNodePtr find_by_id(uint64_t id) {
        if (id_ == id) return shared_from_this();
        for (auto& child : children_) {
            if (auto found = child->find_by_id(id)) {
                return found;
            }
        }
        return nullptr;
    }

    /**
     * 获取父节点
     */
    SceneNodePtr get_parent() const {
        return parent_.lock();
    }

    /**
     * 获取所有子节点
     */
    const std::vector<SceneNodePtr>& get_children() const {
        return children_;
    }

    /**
     * 获取子节点数量
     */
    size_t child_count() const {
        return children_.size();
    }

    // ========== 变换管理 ==========

    /**
     * 获取可修改的局部变换
     */
    Transform& get_transform() {
        local_transform_dirty_ = true;
        mark_dirty();
        return transform_;
    }

    /**
     * 获取只读的局部变换
     */
    const Transform& get_transform() const {
        return transform_;
    }

    /**
     * 设置局部变换
     */
    void set_transform(const Transform& t) {
        transform_ = t;
        local_transform_dirty_ = true;
        mark_dirty();
    }

    /**
     * ⭐ 获取世界变换矩阵
     * 这是场景图最核心的操作：
     * world_matrix = parent.world_matrix * local_matrix
     */
    const Mat4& get_world_matrix() const {
        if (world_transform_dirty_) {
            update_world_transform();
        }
        return world_matrix_;
    }

    /**
     * 获取世界空间位置
     */
    Vec3 get_world_position() const {
        return get_world_matrix().get_translation();
    }

    /**
     * ⭐ 更新变换层级
     * 从当前节点开始，递归更新所有子节点的世界变换
     */
    void update_transforms() {
        if (world_transform_dirty_) {
            update_world_transform();
        }
        for (auto& child : children_) {
            child->update_transforms();
        }
    }

    // ========== 包围盒管理 ==========

    /**
     * 设置可渲染对象
     */
    void set_renderable(const RenderablePtr& renderable) {
        renderable_ = renderable;
        mark_bounds_dirty();
    }

    /**
     * 获取可渲染对象
     */
    RenderablePtr get_renderable() const {
        return renderable_;
    }

    /**
     * ⭐ 获取世界空间包围盒
     * 这是裁剪系统的核心数据
     */
    const AABB& get_world_bounds() const {
        if (bounds_dirty_) {
            update_world_bounds();
        }
        return world_bounds_;
    }

    /**
     * 设置自定义的局部包围盒（不使用 Renderable 的包围盒）
     */
    void set_local_bounds(const AABB& bounds) {
        local_bounds_ = bounds;
        has_custom_bounds_ = true;
        mark_bounds_dirty();
    }

    // ========== 可见性与状态 ==========

    /**
     * 设置节点可见性
     */
    void set_visible(bool visible) {
        visible_ = visible;
    }

    /**
     * 获取节点可见性
     */
    bool is_visible() const {
        return visible_;
    }

    /**
     * 获取节点名称
     */
    const std::string& get_name() const {
        return name_;
    }

    /**
     * 设置节点名称
     */
    void set_name(const std::string& name) {
        name_ = name;
    }

    /**
     * 获取节点 ID
     */
    uint64_t get_id() const {
        return id_;
    }

    // ========== 遍历 ==========

    /**
     * 深度优先遍历（前序）
     * ⭐ 这是场景图遍历的基本模式
     */
    void traverse_dfs(const std::function<void(const SceneNodePtr&)>& visitor) {
        visitor(shared_from_this());
        for (auto& child : children_) {
            child->traverse_dfs(visitor);
        }
    }

    /**
     * 深度优先遍历（前序，只读版本）
     */
    void traverse_dfs_const(const std::function<void(SceneNodeConstPtr)>& visitor) const {
        visitor(shared_from_this());
        for (const auto& child : children_) {
            child->traverse_dfs_const(visitor);
        }
    }

    /**
     * 计算以当前节点为根的子树中的节点总数
     */
    size_t total_node_count() const {
        size_t count = 1;
        for (const auto& child : children_) {
            count += child->total_node_count();
        }
        return count;
    }

    /**
     * 获取节点的深度（到根节点的距离）
     */
    int get_depth() const {
        if (auto p = parent_.lock()) {
            return p->get_depth() + 1;
        }
        return 0;
    }

private:
    /**
     * 标记变换为脏（需要重新计算）
     */
    void mark_dirty() {
        world_transform_dirty_ = true;
        bounds_dirty_ = true;
        // 递归标记所有子节点
        for (auto& child : children_) {
            child->mark_dirty();
        }
    }

    /**
     * 标记包围盒为脏
     */
    void mark_bounds_dirty() {
        bounds_dirty_ = true;
        // 向上传播到父节点
        if (auto p = parent_.lock()) {
            p->mark_bounds_dirty();
        }
    }

    /**
     * ⭐ 更新世界变换矩阵
     * 这是变换层级的核心实现
     */
    void update_world_transform() const {
        local_matrix_ = transform_.get_local_matrix();

        if (auto p = parent_.lock()) {
            world_matrix_ = p->get_world_matrix() * local_matrix_;
        } else {
            world_matrix_ = local_matrix_;
        }

        world_transform_dirty_ = false;
    }

    /**
     * ⭐ 更新世界空间包围盒
     * 从局部包围盒变换到世界空间，并合并所有子节点的包围盒
     */
    void update_world_bounds() const {
        // 获取局部包围盒
        AABB local_bounds;
        if (renderable_) {
            local_bounds = renderable_->get_local_bounds();
        } else if (has_custom_bounds_) {
            local_bounds = local_bounds_;
        } else {
            // 没有包围盒时使用零大小包围盒（原点，世界矩阵会定位到正确位置）
            local_bounds = AABB({0, 0, 0}, {0, 0, 0});
        }

        // 变换到世界空间
        world_bounds_ = local_bounds.transform(get_world_matrix());

        // 合并所有子节点的包围盒
        for (const auto& child : children_) {
            world_bounds_.expand(child->get_world_bounds());
        }

        bounds_dirty_ = false;
    }

    // 成员变量
    std::string name_;
    uint64_t id_;
    bool visible_;

    // 变换
    Transform transform_;
    bool local_transform_dirty_;
    mutable bool world_transform_dirty_;
    mutable Mat4 local_matrix_;
    mutable Mat4 world_matrix_;

    // 包围盒
    RenderablePtr renderable_;
    AABB local_bounds_;
    bool has_custom_bounds_ = false;
    mutable bool bounds_dirty_;
    mutable AABB world_bounds_;

    // 层级关系
    std::weak_ptr<SceneNode> parent_;
    std::vector<SceneNodePtr> children_;

    // ID 生成器
    static uint64_t next_id_;
};

} // namespace sg
