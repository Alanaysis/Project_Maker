#pragma once

#include "vector2d.h"
#include <algorithm>
#include <limits>

namespace physics_engine {

struct AABB {
    Vector2D min;  // 左下角
    Vector2D max;  // 右上角

    AABB() = default;
    AABB(const Vector2D& min, const Vector2D& max) : min(min), max(max) {}
    AABB(double min_x, double min_y, double max_x, double max_y)
        : min(min_x, min_y), max(max_x, max_y) {}

    // 获取中心点
    Vector2D center() const {
        return (min + max) * 0.5;
    }

    // 获取尺寸（宽和高）
    Vector2D size() const {
        return max - min;
    }

    // 获取半尺寸（半宽和半高）
    Vector2D half_size() const {
        return size() * 0.5;
    }

    // 获取面积
    double area() const {
        Vector2D s = size();
        return s.x * s.y;
    }

    // 获取周长
    double perimeter() const {
        Vector2D s = size();
        return 2.0 * (s.x + s.y);
    }

    // 检测点是否在 AABB 内
    bool contains(const Vector2D& point) const {
        return point.x >= min.x && point.x <= max.x &&
               point.y >= min.y && point.y <= max.y;
    }

    // 检测另一个 AABB 是否完全包含在本 AABB 内
    bool contains(const AABB& other) const {
        return other.min.x >= min.x && other.max.x <= max.x &&
               other.min.y >= min.y && other.max.y <= max.y;
    }

    // 检测与另一个 AABB 是否重叠
    bool intersects(const AABB& other) const {
        return min.x <= other.max.x && max.x >= other.min.x &&
               min.y <= other.max.y && max.y >= other.min.y;
    }

    // 计算与另一个 AABB 的重叠区域
    AABB intersection(const AABB& other) const {
        return {
            std::max(min.x, other.min.x),
            std::max(min.y, other.min.y),
            std::min(max.x, other.max.x),
            std::min(max.y, other.max.y)
        };
    }

    // 合并另一个 AABB
    AABB merge(const AABB& other) const {
        return {
            std::min(min.x, other.min.x),
            std::min(min.y, other.min.y),
            std::max(max.x, other.max.x),
            std::max(max.y, other.max.y)
        };
    }

    // 就地合并
    void merge_inplace(const AABB& other) {
        min.x = std::min(min.x, other.min.x);
        min.y = std::min(min.y, other.min.y);
        max.x = std::max(max.x, other.max.x);
        max.y = std::max(max.y, other.max.y);
    }

    // 扩展 AABB（各方向扩展指定距离）
    AABB expanded(double amount) const {
        return {
            min.x - amount,
            min.y - amount,
            max.x + amount,
            max.y + amount
        };
    }

    // 计算到另一个 AABB 的最近距离
    double distance_to(const AABB& other) const {
        double dx = std::max({0.0, min.x - other.max.x, other.min.x - max.x});
        double dy = std::max({0.0, min.y - other.max.y, other.min.y - max.y});
        return std::sqrt(dx * dx + dy * dy);
    }

    // 获取指定角点（0=左下, 1=右下, 2=右上, 3=左上）
    Vector2D corner(int index) const {
        switch (index) {
            case 0: return min;
            case 1: return {max.x, min.y};
            case 2: return max;
            case 3: return {min.x, max.y};
            default: return min;
        }
    }

    // 检测是否有效（min <= max）
    bool is_valid() const {
        return min.x <= max.x && min.y <= max.y;
    }

    // 输出流运算符
    friend std::ostream& operator<<(std::ostream& os, const AABB& aabb) {
        os << "AABB[" << aabb.min << " -> " << aabb.max << "]";
        return os;
    }
};

} // namespace physics_engine
