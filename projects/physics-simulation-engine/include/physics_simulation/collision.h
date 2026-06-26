#pragma once

#include "vector2d.h"
#include "aabb.h"
#include "rigid_body.h"
#include <vector>

namespace physics_simulation {

struct ContactPoint {
    Vec2 position;
    Vec2 normal;
    double penetration;
    Vec2 r_a;
    Vec2 r_b;
};

struct CollisionManifold {
    RigidBody* body_a;
    RigidBody* body_b;
    std::vector<ContactPoint> contacts;
    Vec2 normal;

    bool has_collision() const {
        return !contacts.empty();
    }
};

struct CollisionResult {
    bool collided = false;
    Vec2 normal;
    double penetration = 0.0;
    Vec2 contact_point;
};

inline CollisionResult aabb_vs_aabb(const AABB& a, const AABB& b) {
    CollisionResult result;

    double overlap_x = std::min(a.max.x, b.max.x) - std::max(a.min.x, b.min.x);
    double overlap_y = std::min(a.max.y, b.max.y) - std::max(a.min.y, b.min.y);

    if (overlap_x <= 0.0 || overlap_y <= 0.0) {
        return result;
    }

    result.collided = true;

    if (overlap_x < overlap_y) {
        double sign = (a.center().x < b.center().x) ? 1.0 : -1.0;
        result.normal = {sign, 0.0};
        result.penetration = overlap_x;
    } else {
        double sign = (a.center().y < b.center().y) ? 1.0 : -1.0;
        result.normal = {0.0, sign};
        result.penetration = overlap_y;
    }

    result.contact_point = (a.center() + b.center()) * 0.5;

    return result;
}

inline CollisionResult circle_vs_circle(
    const Vec2& center_a, double radius_a,
    const Vec2& center_b, double radius_b)
{
    CollisionResult result;

    Vec2 diff = center_b - center_a;
    double dist_sq = diff.length_squared();
    double radius_sum = radius_a + radius_b;

    if (dist_sq > radius_sum * radius_sum) {
        return result;
    }

    double dist = std::sqrt(dist_sq);
    result.collided = true;

    if (dist > 1e-10) {
        result.normal = diff / dist;
    } else {
        result.normal = {1.0, 0.0};
        dist = 0.0;
    }

    result.penetration = radius_sum - dist;
    result.contact_point = center_a + result.normal * radius_a;

    return result;
}

inline CollisionResult aabb_vs_circle(
    const AABB& aabb,
    const Vec2& circle_center,
    double circle_radius)
{
    CollisionResult result;

    double closest_x = std::max(aabb.min.x, std::min(circle_center.x, aabb.max.x));
    double closest_y = std::max(aabb.min.y, std::min(circle_center.y, aabb.max.y));
    Vec2 closest = {closest_x, closest_y};

    Vec2 diff = circle_center - closest;
    double dist_sq = diff.length_squared();
    double radius_sq = circle_radius * circle_radius;

    if (dist_sq > radius_sq) {
        return result;
    }

    double dist = std::sqrt(dist_sq);
    result.collided = true;

    if (dist > 1e-10) {
        result.normal = diff / dist;
    } else {
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

inline CollisionResult detect_collision(const RigidBody& a, const RigidBody& b) {
    AABB aabb_a = a.compute_aabb();
    AABB aabb_b = b.compute_aabb();

    return aabb_vs_aabb(aabb_a, aabb_b);
}

} // namespace physics_simulation
