#pragma once

#include "vector2d.h"
#include "aabb.h"
#include "rigid_body.h"
#include <vector>

namespace physics_engine {

// 碰撞接触点
struct ContactPoint {
    Vector2D position;      // 接触点位置
    Vector2D normal;        // 从 body_a 指向 body_b 的法线
    double penetration;     // 穿透深度（正值表示重叠）
    Vector2D r_a;           // 从 body_a 质心到接触点的向量
    Vector2D r_b;           // 从 body_b 质心到接触点的向量
};

// 碰撞信息
struct CollisionManifold {
    RigidBody* body_a;
    RigidBody* body_b;
    std::vector<ContactPoint> contacts;
    Vector2D normal;  // 从 body_a 指向 body_b 的法线

    bool has_collision() const {
        return !contacts.empty();
    }
};

// 碰撞检测结果
struct CollisionResult {
    bool collided = false;
    Vector2D normal;
    double penetration = 0.0;
    Vector2D contact_point;
};

// AABB 与 AABB 碰撞检测
inline CollisionResult aabb_vs_aabb(const AABB& a, const AABB& b) {
    CollisionResult result;

    // 计算重叠
    double overlap_x = std::min(a.max.x, b.max.x) - std::max(a.min.x, b.min.x);
    double overlap_y = std::min(a.max.y, b.max.y) - std::max(a.min.y, b.min.y);

    if (overlap_x <= 0.0 || overlap_y <= 0.0) {
        return result;  // 没有碰撞
    }

    result.collided = true;

    // 选择最小穿透方向
    if (overlap_x < overlap_y) {
        // X 方向穿透较小
        double sign = (a.center().x < b.center().x) ? 1.0 : -1.0;
        result.normal = {sign, 0.0};
        result.penetration = overlap_x;
    } else {
        // Y 方向穿透较小
        double sign = (a.center().y < b.center().y) ? 1.0 : -1.0;
        result.normal = {0.0, sign};
        result.penetration = overlap_y;
    }

    // 计算接触点（使用两个 AABB 的中心）
    result.contact_point = (a.center() + b.center()) * 0.5;

    return result;
}

// 圆形与圆形碰撞检测
inline CollisionResult circle_vs_circle(
    const Vector2D& center_a, double radius_a,
    const Vector2D& center_b, double radius_b)
{
    CollisionResult result;

    Vector2D diff = center_b - center_a;
    double dist_sq = diff.length_squared();
    double radius_sum = radius_a + radius_b;

    if (dist_sq > radius_sum * radius_sum) {
        return result;  // 没有碰撞
    }

    double dist = std::sqrt(dist_sq);
    result.collided = true;

    if (dist > 1e-10) {
        result.normal = diff / dist;
    } else {
        // 圆心重合，选择任意方向
        result.normal = {1.0, 0.0};
        dist = 0.0;
    }

    result.penetration = radius_sum - dist;
    result.contact_point = center_a + result.normal * radius_a;

    return result;
}

// AABB 与圆形碰撞检测
inline CollisionResult aabb_vs_circle(
    const AABB& aabb,
    const Vector2D& circle_center,
    double circle_radius)
{
    CollisionResult result;

    // 找到 AABB 上最近的点
    double closest_x = std::max(aabb.min.x, std::min(circle_center.x, aabb.max.x));
    double closest_y = std::max(aabb.min.y, std::min(circle_center.y, aabb.max.y));
    Vector2D closest = {closest_x, closest_y};

    Vector2D diff = circle_center - closest;
    double dist_sq = diff.length_squared();
    double radius_sq = circle_radius * circle_radius;

    if (dist_sq > radius_sq) {
        return result;  // 没有碰撞
    }

    double dist = std::sqrt(dist_sq);
    result.collided = true;

    if (dist > 1e-10) {
        result.normal = diff / dist;
    } else {
        // 圆心在 AABB 内部，计算到各边的最近距离
        double dx_left = circle_center.x - aabb.min.x;
        double dx_right = aabb.max.x - circle_center.x;
        double dy_bottom = circle_center.y - aabb.min.y;
        double dy_top = aabb.max.y - circle_center.y;

        double min_dist = std::min({dx_left, dx_right, dy_bottom, dy_top});

        if (min_dist == dx_left) result.normal = {-1.0, 0.0};
        else if (min_dist == dx_right) result.normal = {1.0, 0.0};
        else if (min_dist == dy_bottom) result.normal = {0.0, -1.0};
        else result.normal = {0.0, 1.0};

        dist = 0.0;
    }

    result.penetration = circle_radius - dist;
    result.contact_point = closest;

    return result;
}

// 通用碰撞检测（基于刚体）
inline CollisionResult detect_collision(const RigidBody& a, const RigidBody& b) {
    // 简化实现：使用 AABB 进行碰撞检测
    AABB aabb_a = a.compute_aabb();
    AABB aabb_b = b.compute_aabb();

    return aabb_vs_aabb(aabb_a, aabb_b);
}

} // namespace physics_engine
