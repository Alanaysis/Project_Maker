#include "scene_graph/frustum.h"
#include <cmath>
#include <iostream>
#include <algorithm>

namespace sg {

void Frustum::extractFromMatrix(const Mat4& vp) {
    // Extract frustum planes from view-projection matrix
    // Using the Gribb-Hartmann method

    // Left plane
    planes_[Left].normal = Vec3{vp.at(3,0) + vp.at(0,0), vp.at(3,1) + vp.at(0,1), vp.at(3,2) + vp.at(0,2)};
    planes_[Left].distance = vp.at(3,3) + vp.at(0,3);

    // Right plane
    planes_[Right].normal = Vec3{vp.at(3,0) - vp.at(0,0), vp.at(3,1) - vp.at(0,1), vp.at(3,2) - vp.at(0,2)};
    planes_[Right].distance = vp.at(3,3) - vp.at(0,3);

    // Bottom plane
    planes_[Bottom].normal = Vec3{vp.at(3,0) + vp.at(1,0), vp.at(3,1) + vp.at(1,1), vp.at(3,2) + vp.at(1,2)};
    planes_[Bottom].distance = vp.at(3,3) + vp.at(1,3);

    // Top plane
    planes_[Top].normal = Vec3{vp.at(3,0) - vp.at(1,0), vp.at(3,1) - vp.at(1,1), vp.at(3,2) - vp.at(1,2)};
    planes_[Top].distance = vp.at(3,3) - vp.at(1,3);

    // Near plane
    planes_[Near].normal = Vec3{vp.at(3,0) + vp.at(2,0), vp.at(3,1) + vp.at(2,1), vp.at(3,2) + vp.at(2,2)};
    planes_[Near].distance = vp.at(3,3) + vp.at(2,3);

    // Far plane
    planes_[Far].normal = Vec3{vp.at(3,0) - vp.at(2,0), vp.at(3,1) - vp.at(2,1), vp.at(3,2) - vp.at(2,2)};
    planes_[Far].distance = vp.at(3,3) - vp.at(2,3);

    // Normalize all planes
    for (auto& plane : planes_) {
        plane.normalize();
    }
}

void Frustum::setPerspective(float fovY, float aspect, float nearDist, float farDist,
                              const Vec3& eye, const Vec3& forward, const Vec3& right, const Vec3& up) {
    position_ = eye;
    nearDist_ = nearDist;
    farDist_ = farDist;

    float halfV = std::tan(fovY * 0.5f);
    float halfH = halfV * aspect;

    Vec3 nearCenter = eye + forward * nearDist;
    Vec3 farCenter = eye + forward * farDist;

    // Near plane
    planes_[Near] = Plane(forward, nearCenter);

    // Far plane
    planes_[Far] = Plane(forward * -1.0f, farCenter);

    // Left plane
    Vec3 leftNormal = (forward - right * halfH).normalized().cross(up);
    planes_[Left] = Plane(leftNormal, eye);

    // Right plane
    Vec3 rightNormal = up.cross((forward + right * halfH).normalized());
    planes_[Right] = Plane(rightNormal, eye);

    // Top plane
    Vec3 topNormal = right.cross((forward - up * halfV).normalized());
    planes_[Top] = Plane(topNormal, eye);

    // Bottom plane
    Vec3 bottomNormal = (forward + up * halfV).normalized().cross(right);
    planes_[Bottom] = Plane(bottomNormal, eye);

    // Normalize all planes
    for (auto& plane : planes_) {
        plane.normalize();
    }
}

Visibility Frustum::testAABB(const AABB& aabb) const {
    Visibility result = Visibility::Full;
    Vec3 center = aabb.center();
    Vec3 halfExt = aabb.halfExtent();

    for (int i = 0; i < PlaneID::Count; ++i) {
        const Plane& plane = planes_[i];

        // Compute the positive vertex (farthest along plane normal)
        Vec3 positiveVertex = center;
        if (plane.normal.x >= 0) positiveVertex.x += halfExt.x; else positiveVertex.x -= halfExt.x;
        if (plane.normal.y >= 0) positiveVertex.y += halfExt.y; else positiveVertex.y -= halfExt.y;
        if (plane.normal.z >= 0) positiveVertex.z += halfExt.z; else positiveVertex.z -= halfExt.z;

        // If positive vertex is outside, the AABB is completely outside
        if (plane.distanceTo(positiveVertex) < 0) {
            return Visibility::None;
        }

        // Compute the negative vertex (closest along plane normal)
        Vec3 negativeVertex = center;
        if (plane.normal.x >= 0) negativeVertex.x -= halfExt.x; else negativeVertex.x += halfExt.x;
        if (plane.normal.y >= 0) negativeVertex.y -= halfExt.y; else negativeVertex.y += halfExt.y;
        if (plane.normal.z >= 0) negativeVertex.z -= halfExt.z; else negativeVertex.z += halfExt.z;

        // If negative vertex is outside, AABB intersects the plane
        if (plane.distanceTo(negativeVertex) < 0) {
            result = Visibility::Partial;
        }
    }
    return result;
}

Visibility Frustum::testSphere(const BoundingSphere& sphere) const {
    return testSphere(sphere.center, sphere.radius);
}

Visibility Frustum::testSphere(const Vec3& center, float radius) const {
    Visibility result = Visibility::Full;

    for (int i = 0; i < PlaneID::Count; ++i) {
        const Plane& plane = planes_[i];
        float distance = plane.distanceTo(center);

        if (distance < -radius) {
            return Visibility::None;  // Completely outside
        }
        if (distance < radius) {
            result = Visibility::Partial;  // Intersects
        }
    }
    return result;
}

bool Frustum::containsAABB(const AABB& aabb) const {
    return testAABB(aabb) != Visibility::None;
}

bool Frustum::containsSphere(const Vec3& center, float radius) const {
    return testSphere(center, radius) != Visibility::None;
}

bool Frustum::containsPoint(const Vec3& point) const {
    for (int i = 0; i < PlaneID::Count; ++i) {
        if (planes_[i].distanceTo(point) < 0) {
            return false;
        }
    }
    return true;
}

void Frustum::print() const {
    const char* names[] = {"Left", "Right", "Bottom", "Top", "Near", "Far"};
    std::cout << "Frustum planes:\n";
    for (int i = 0; i < PlaneID::Count; ++i) {
        std::cout << "  " << names[i] << ": n=("
                  << planes_[i].normal.x << ", " << planes_[i].normal.y << ", " << planes_[i].normal.z
                  << ") d=" << planes_[i].distance << "\n";
    }
}

// Camera implementation

void Camera::setPerspective(float fovY, float aspect, float near, float far) {
    fovY_ = fovY;
    aspect_ = aspect;
    near_ = near;
    far_ = far;
    projMatrix_ = Mat4::perspective(fovY, aspect, near, far);
    viewDirty_ = true;
}

void Camera::updateViewMatrix() {
    if (viewDirty_) {
        viewMatrix_ = Mat4::lookAt(position_, target_, up_);
        viewDirty_ = false;
    }
}

void Camera::updateFrustum() {
    // Update view matrix first
    updateViewMatrix();

    // Compute view-projection matrix
    Mat4 vp = projMatrix_ * viewMatrix_;

    // Extract frustum from VP matrix
    frustum_.extractFromMatrix(vp);
}

} // namespace sg
