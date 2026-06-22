#pragma once

#include "math_types.h"

namespace sg {

/**
 * Transform - 变换组件
 *
 * 管理物体的局部变换（位置、旋转、缩放），
 * 并计算局部到世界空间的变换矩阵。
 *
 * ⭐ 核心概念：
 * - 局部变换（Local Transform）：相对于父节点的变换
 * - 世界变换（World Transform）：在世界空间中的最终变换
 * - TRS 组合：先缩放 -> 再旋转 -> 最后平移
 */
class Transform {
public:
    Vec3 position;
    Quaternion rotation;
    Vec3 scale;

    Transform()
        : position(0, 0, 0)
        , rotation()
        , scale(1, 1, 1) {}

    Transform(const Vec3& pos, const Quaternion& rot, const Vec3& scl)
        : position(pos), rotation(rot), scale(scl) {}

    /**
     * ⭐ 计算局部变换矩阵
     * M = T * R * S
     * 这是场景图变换层级的基础
     */
    Mat4 get_local_matrix() const {
        return Mat4::trs(position, rotation, scale);
    }

    /**
     * 设置欧拉角旋转（度数 -> 四元数）
     */
    void set_rotation_euler(float pitch_deg, float yaw_deg, float roll_deg) {
        const float deg2rad = 3.14159265358979f / 180.0f;
        rotation = Quaternion::from_euler(
            pitch_deg * deg2rad,
            yaw_deg * deg2rad,
            roll_deg * deg2rad
        );
    }

    /**
     * 绕轴旋转
     */
    void rotate_axis(const Vec3& axis, float angle_deg) {
        const float deg2rad = 3.14159265358979f / 180.0f;
        Quaternion delta = Quaternion::from_axis_angle(axis, angle_deg * deg2rad);
        rotation = (rotation * delta).normalized();
    }

    /**
     * 平移
     */
    void translate(const Vec3& delta) {
        position += delta;
    }

    /**
     * 缩放
     */
    void scale_by(const Vec3& factors) {
        scale.x *= factors.x;
        scale.y *= factors.y;
        scale.z *= factors.z;
    }

    /**
     * 获取变换的前方向（-Z 方向）
     */
    Vec3 forward() const {
        return rotation.rotate({0, 0, -1});
    }

    /**
     * 获取变换的右方向（+X 方向）
     */
    Vec3 right() const {
        return rotation.rotate({1, 0, 0});
    }

    /**
     * 获取变换的上方向（+Y 方向）
     */
    Vec3 up() const {
        return rotation.rotate({0, 1, 0});
    }

    bool operator==(const Transform& rhs) const {
        return position == rhs.position && rotation == rhs.rotation && scale == rhs.scale;
    }
    bool operator!=(const Transform& rhs) const { return !(*this == rhs); }
};

} // namespace sg
