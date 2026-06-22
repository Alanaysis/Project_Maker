#pragma once

#include "types.h"

namespace sg {

// Local transform component - stores position, rotation, scale
struct Transform {
    Vec3 position{0, 0, 0};
    Vec3 rotation{0, 0, 0};  // Euler angles in radians (pitch, yaw, roll)
    Vec3 scale{1, 1, 1};

    // Get local transform matrix (TRS order)
    Mat4 getLocalMatrix() const {
        // Translation * RotationY * RotationX * RotationZ * Scale
        Mat4 T = Mat4::translation(position);
        Mat4 Ry = Mat4::rotationY(rotation.y);
        Mat4 Rx = Mat4::rotationX(rotation.x);
        Mat4 Rz = Mat4::rotationZ(rotation.z);
        Mat4 S = Mat4::scale(scale);
        return T * Ry * Rx * Rz * S;
    }

    // Get rotation matrix only
    Mat4 getRotationMatrix() const {
        Mat4 Ry = Mat4::rotationY(rotation.y);
        Mat4 Rx = Mat4::rotationX(rotation.x);
        Mat4 Rz = Mat4::rotationZ(rotation.z);
        return Ry * Rx * Rz;
    }

    // Get forward vector (negative Z in local space)
    Vec3 getForward() const {
        return getRotationMatrix().transformDirection(Vec3::forward());
    }

    // Get right vector (positive X in local space)
    Vec3 getRight() const {
        return getRotationMatrix().transformDirection(Vec3::right());
    }

    // Get up vector (positive Y in local space)
    Vec3 getUp() const {
        return getRotationMatrix().transformDirection(Vec3::up());
    }

    // Translate in local space
    void translate(const Vec3& offset) {
        position += offset;
    }

    // Rotate by Euler angles (in radians)
    void rotate(const Vec3& euler) {
        rotation += euler;
    }

    // Look at target point (sets rotation)
    void lookAt(const Vec3& target) {
        Vec3 dir = (target - position).normalized();
        rotation.y = std::atan2(dir.x, dir.z);
        rotation.x = -std::asin(dir.y);
    }
};

} // namespace sg
