#pragma once

#include "Vec3.h"
#include <algorithm>
#include <limits>

namespace spatial {

/**
 * Axis-Aligned Bounding Box (AABB)
 * Fundamental data structure for spatial partitioning
 */
struct AABB {
    Vec3 min;
    Vec3 max;

    AABB() : min(Vec3::zero()), max(Vec3::zero()) {}
    AABB(const Vec3& min, const Vec3& max) : min(min), max(max) {}

    /**
     * Create AABB from a single point
     */
    static AABB fromPoint(const Vec3& point) {
        return AABB(point, point);
    }

    /**
     * Create AABB from center and half-extents
     */
    static AABB fromCenterHalfExtents(const Vec3& center, const Vec3& halfExtents) {
        return AABB(center - halfExtents, center + halfExtents);
    }

    /**
     * Get the center of the AABB
     */
    Vec3 center() const {
        return (min + max) * 0.5f;
    }

    /**
     * Get the half-extents of the AABB
     */
    Vec3 halfExtents() const {
        return (max - min) * 0.5f;
    }

    /**
     * Get the size (width, height, depth) of the AABB
     */
    Vec3 size() const {
        return max - min;
    }

    /**
     * Get the surface area of the AABB
     * Used for Surface Area Heuristic (SAH) in BVH construction
     */
    float surfaceArea() const {
        Vec3 s = size();
        return 2.0f * (s.x * s.y + s.y * s.z + s.z * s.x);
    }

    /**
     * Get the volume of the AABB
     */
    float volume() const {
        Vec3 s = size();
        return s.x * s.y * s.z;
    }

    /**
     * Get the longest axis (0=x, 1=y, 2=z)
     */
    int longestAxis() const {
        Vec3 s = size();
        if (s.x > s.y && s.x > s.z) return 0;
        if (s.y > s.z) return 1;
        return 2;
    }

    /**
     * Expand the AABB to include a point
     */
    void expand(const Vec3& point) {
        min.x = std::min(min.x, point.x);
        min.y = std::min(min.y, point.y);
        min.z = std::min(min.z, point.z);
        max.x = std::max(max.x, point.x);
        max.y = std::max(max.y, point.y);
        max.z = std::max(max.z, point.z);
    }

    /**
     * Expand the AABB to include another AABB
     */
    void expand(const AABB& other) {
        expand(other.min);
        expand(other.max);
    }

    /**
     * Merge two AABBs
     */
    static AABB merge(const AABB& a, const AABB& b) {
        AABB result = a;
        result.expand(b);
        return result;
    }

    /**
     * Check if this AABB contains a point
     */
    bool contains(const Vec3& point) const {
        return point.x >= min.x && point.x <= max.x &&
               point.y >= min.y && point.y <= max.y &&
               point.z >= min.z && point.z <= max.z;
    }

    /**
     * Check if this AABB contains another AABB
     */
    bool contains(const AABB& other) const {
        return contains(other.min) && contains(other.max);
    }

    /**
     * Check if this AABB intersects with another AABB
     */
    bool intersects(const AABB& other) const {
        return min.x <= other.max.x && max.x >= other.min.x &&
               min.y <= other.max.y && max.y >= other.min.y &&
               min.z <= other.max.z && max.z >= other.min.z;
    }

    /**
     * Check if this AABB is valid (min <= max)
     */
    bool isValid() const {
        return min.x <= max.x && min.y <= max.y && min.z <= max.z;
    }

    /**
     * Get the corner points of the AABB
     */
    void getCorners(Vec3 corners[8]) const {
        corners[0] = Vec3(min.x, min.y, min.z);
        corners[1] = Vec3(max.x, min.y, min.z);
        corners[2] = Vec3(min.x, max.y, min.z);
        corners[3] = Vec3(max.x, max.y, min.z);
        corners[4] = Vec3(min.x, min.y, max.z);
        corners[5] = Vec3(max.x, min.y, max.z);
        corners[6] = Vec3(min.x, max.y, max.z);
        corners[7] = Vec3(max.x, max.y, max.z);
    }
};

} // namespace spatial
