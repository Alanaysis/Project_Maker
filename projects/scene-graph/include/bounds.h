#pragma once

#include "math_types.h"
#include <limits>
#include <algorithm>

namespace sg {

/**
 * AABB - 轴对齐包围盒 (Axis-Aligned Bounding Box)
 *
 * ⭐ 核心概念：
 * - AABB 是最简单的包围体，用于快速的粗粒度相交测试
 * - 与 OBB（有向包围盒）相比，AABB 计算更快但不够紧密
 * - 在场景图中，每个节点可以关联一个 AABB 用于裁剪
 */
struct AABB {
    Vec3 min;
    Vec3 max;

    AABB() : min(std::numeric_limits<float>::max()),
             max(std::numeric_limits<float>::lowest()) {}

    AABB(const Vec3& min, const Vec3& max) : min(min), max(max) {}

    /**
     * 从中心点和半尺寸创建
     */
    static AABB from_center_size(const Vec3& center, const Vec3& half_size) {
        return {center - half_size, center + half_size};
    }

    /**
     * 创建一个包围所有给定点的 AABB
     */
    static AABB from_points(const Vec3* points, size_t count) {
        AABB result;
        for (size_t i = 0; i < count; ++i) {
            result.expand(points[i]);
        }
        return result;
    }

    /**
     * 扩展 AABB 以包含给定点
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
     * 扩展 AABB 以包含另一个 AABB
     */
    void expand(const AABB& other) {
        expand(other.min);
        expand(other.max);
    }

    /**
     * 合并两个 AABB
     */
    static AABB merge(const AABB& a, const AABB& b) {
        AABB result = a;
        result.expand(b);
        return result;
    }

    /**
     * 获取中心点
     */
    Vec3 center() const {
        return (min + max) * 0.5f;
    }

    /**
     * 获取半尺寸（extents）
     */
    Vec3 extents() const {
        return (max - min) * 0.5f;
    }

    /**
     * 获取尺寸
     */
    Vec3 size() const {
        return max - min;
    }

    /**
     * 获取体积
     */
    float volume() const {
        Vec3 s = size();
        return s.x * s.y * s.z;
    }

    /**
     * 获取表面积（用于 SAH 等高级算法）
     */
    float surface_area() const {
        Vec3 s = size();
        return 2.0f * (s.x * s.y + s.y * s.z + s.z * s.x);
    }

    /**
     * 测试一个点是否在 AABB 内
     */
    bool contains(const Vec3& point) const {
        return point.x >= min.x && point.x <= max.x &&
               point.y >= min.y && point.y <= max.y &&
               point.z >= min.z && point.z <= max.z;
    }

    /**
     * 测试两个 AABB 是否相交
     */
    bool intersects(const AABB& other) const {
        return min.x <= other.max.x && max.x >= other.min.x &&
               min.y <= other.max.y && max.y >= other.min.y &&
               min.z <= other.max.z && max.z >= other.min.z;
    }

    /**
     * 用变换矩阵变换 AABB
     * ⭐ 这是变换层级中 AABB 变换的关键算法
     * 通过计算变换后 8 个顶点的新 AABB
     */
    AABB transform(const Mat4& matrix) const {
        // 初始化为变换后的第一个角点
        Vec3 corners[8] = {
            {min.x, min.y, min.z},
            {max.x, min.y, min.z},
            {min.x, max.y, min.z},
            {max.x, max.y, min.z},
            {min.x, min.y, max.z},
            {max.x, min.y, max.z},
            {min.x, max.y, max.z},
            {max.x, max.y, max.z}
        };

        AABB result;
        for (int i = 0; i < 8; ++i) {
            result.expand(matrix.transform_point(corners[i]));
        }
        return result;
    }

    bool operator==(const AABB& rhs) const {
        return min == rhs.min && max == rhs.max;
    }
    bool operator!=(const AABB& rhs) const { return !(*this == rhs); }
};

/**
 * Plane - 平面（用于视锥体定义）
 *
 * 平面方程: ax + by + cz + d = 0
 * 法向量 (a, b, c) 指向平面的"正面"（可见侧）
 */
struct Plane {
    Vec3 normal;
    float distance;

    Plane() : normal(0, 1, 0), distance(0) {}
    Plane(const Vec3& n, float d) : normal(n.normalized()), distance(d) {}

    /**
     * 从三个点构造平面
     * 按逆时针顺序，法向量朝上
     */
    static Plane from_points(const Vec3& a, const Vec3& b, const Vec3& c) {
        Vec3 n = (c - a).cross(b - a).normalized();
        return {n, -n.dot(a)};
    }

    /**
     * 计算点到平面的有符号距离
     * 正值 = 在正面（可见侧）
     * 负值 = 在背面（不可见侧）
     * 零   = 在平面上
     */
    float distance_to(const Vec3& point) const {
        return normal.dot(point) + distance;
    }

    /**
     * 平面归一化
     */
    Plane normalized() const {
        float len = normal.length();
        if (len < 1e-6f) return *this;
        return {normal / len, distance / len};
    }
};

/**
 * Frustum - 视锥体
 *
 * ⭐ 核心概念：
 * - 视锥体是摄像机可见的空间区域，由 6 个平面定义
 * - 近/远裁剪面 + 左/右/上/下 四个侧面
 * - 裁剪（Culling）就是测试物体是否在视锥体内
 *
 * 平面法向量都朝内（指向可见区域）
 */
class Frustum {
public:
    enum PlaneIndex {
        LEFT = 0,
        RIGHT,
        BOTTOM,
        TOP,
        NEAR,
        FAR,
        PLANE_COUNT
    };

    Frustum() = default;

    /**
     * 从 View-Projection 矩阵提取视锥体
     *
     * ⭐ 这是 Gribb/Hartmann 方法，从组合矩阵直接提取 6 个平面
     * 参考：http://www.cs.otago.ac.nz/postgrads/alexis/planeExtraction.pdf
     */
    static Frustum from_view_projection(const Mat4& vp) {
        Frustum frustum;

        // 左平面：行3 + 行0
        frustum.planes_[LEFT] = Plane(
            Vec3(vp.at(3,0) + vp.at(0,0), vp.at(3,1) + vp.at(0,1), vp.at(3,2) + vp.at(0,2)),
            vp.at(3,3) + vp.at(0,3)
        ).normalized();

        // 右平面：行3 - 行0
        frustum.planes_[RIGHT] = Plane(
            Vec3(vp.at(3,0) - vp.at(0,0), vp.at(3,1) - vp.at(0,1), vp.at(3,2) - vp.at(0,2)),
            vp.at(3,3) - vp.at(0,3)
        ).normalized();

        // 下平面：行3 + 行1
        frustum.planes_[BOTTOM] = Plane(
            Vec3(vp.at(3,0) + vp.at(1,0), vp.at(3,1) + vp.at(1,1), vp.at(3,2) + vp.at(1,2)),
            vp.at(3,3) + vp.at(1,3)
        ).normalized();

        // 上平面：行3 - 行1
        frustum.planes_[TOP] = Plane(
            Vec3(vp.at(3,0) - vp.at(1,0), vp.at(3,1) - vp.at(1,1), vp.at(3,2) - vp.at(1,2)),
            vp.at(3,3) - vp.at(1,3)
        ).normalized();

        // 近平面：行3 + 行2
        frustum.planes_[NEAR] = Plane(
            Vec3(vp.at(3,0) + vp.at(2,0), vp.at(3,1) + vp.at(2,1), vp.at(3,2) + vp.at(2,2)),
            vp.at(3,3) + vp.at(2,3)
        ).normalized();

        // 远平面：行3 - 行2
        frustum.planes_[FAR] = Plane(
            Vec3(vp.at(3,0) - vp.at(2,0), vp.at(3,1) - vp.at(2,1), vp.at(3,2) - vp.at(2,2)),
            vp.at(3,3) - vp.at(2,3)
        ).normalized();

        return frustum;
    }

    /**
     * ⭐ 测试 AABB 是否在视锥体内
     *
     * 使用"p-vertex"（正顶点）优化：
     * - 对于每个平面，找到 AABB 在平面法向量方向上最远的顶点
     * - 如果这个顶点在平面背面，则整个 AABB 在视锥体外
     *
     * @return true 如果 AABB 与视锥体相交或完全在内部
     */
    bool test_aabb(const AABB& aabb) const {
        for (int i = 0; i < PLANE_COUNT; ++i) {
            // 找到在平面法向量方向上最远的顶点（p-vertex）
            Vec3 p_vertex;
            p_vertex.x = (planes_[i].normal.x >= 0) ? aabb.max.x : aabb.min.x;
            p_vertex.y = (planes_[i].normal.y >= 0) ? aabb.max.y : aabb.min.y;
            p_vertex.z = (planes_[i].normal.z >= 0) ? aabb.max.z : aabb.min.z;

            // 如果 p-vertex 在平面背面，AABB 完全在视锥体外
            if (planes_[i].distance_to(p_vertex) < 0) {
                return false;
            }
        }
        return true;
    }

    /**
     * 测试点是否在视锥体内
     */
    bool test_point(const Vec3& point) const {
        for (int i = 0; i < PLANE_COUNT; ++i) {
            if (planes_[i].distance_to(point) < 0) {
                return false;
            }
        }
        return true;
    }

    /**
     * 测试球体是否与视锥体相交
     */
    bool test_sphere(const Vec3& center, float radius) const {
        for (int i = 0; i < PLANE_COUNT; ++i) {
            if (planes_[i].distance_to(center) < -radius) {
                return false;
            }
        }
        return true;
    }

    /**
     * 获取指定平面（用于调试）
     */
    const Plane& get_plane(PlaneIndex index) const {
        return planes_[index];
    }

private:
    Plane planes_[PLANE_COUNT];
};

} // namespace sg
