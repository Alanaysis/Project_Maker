#pragma once

#include "vector2d.h"
#include <algorithm>

namespace physics_simulation {

struct AABB {
    Vec2 min;
    Vec2 max;

    AABB() : min{0.0, 0.0}, max{0.0, 0.0} {}
    AABB(const Vec2& min, const Vec2& max) : min(min), max(max) {}
    AABB(double min_x, double min_y, double max_x, double max_y)
        : min(min_x, min_y), max(max_x, max_y) {}

    Vec2 center() const { return (min + max) * 0.5; }
    Vec2 size() const { return max - min; }
    Vec2 half_size() const { return size() * 0.5; }
    double area() const {
        Vec2 s = size();
        return s.x * s.y;
    }
    bool contains(const Vec2& point) const {
        return point.x >= min.x && point.x <= max.x &&
               point.y >= min.y && point.y <= max.y;
    }
    bool intersects(const AABB& other) const {
        return min.x <= other.max.x && max.x >= other.min.x &&
               min.y <= other.max.y && max.y >= other.min.y;
    }
    AABB merge(const AABB& other) const {
        return {
            std::min(min.x, other.min.x),
            std::min(min.y, other.min.y),
            std::max(max.x, other.max.x),
            std::max(max.y, other.max.y)
        };
    }
    AABB expanded(double amount) const {
        return {
            min.x - amount,
            min.y - amount,
            max.x + amount,
            max.y + amount
        };
    }
    bool is_valid() const {
        return min.x <= max.x && min.y <= max.y;
    }
};

} // namespace physics_simulation
