#pragma once

#include "types.h"

namespace sg {

// A plane in 3D space (ax + by + cz + d = 0)
struct Plane {
    Vec3 normal{0, 1, 0};
    float distance = 0.0f;

    Plane() = default;
    Plane(const Vec3& normal, float distance) : normal(normal), distance(distance) {}
    Plane(const Vec3& normal, const Vec3& point)
        : normal(normal), distance(-normal.dot(point)) {}

    // Normalize the plane
    void normalize() {
        float len = normal.length();
        if (len > 0) {
            normal = normal / len;
            distance /= len;
        }
    }

    // Signed distance from point to plane
    float distanceTo(const Vec3& point) const {
        return normal.dot(point) + distance;
    }

    // Check if point is on positive side (inside)
    bool isOnPositiveSide(const Vec3& point) const {
        return distanceTo(point) >= 0.0f;
    }
};

// Bounding sphere for culling
struct BoundingSphere {
    Vec3 center;
    float radius = 0.0f;

    BoundingSphere() = default;
    BoundingSphere(const Vec3& center, float radius) : center(center), radius(radius) {}

    // Transform by matrix
    BoundingSphere transformed(const Mat4& mat) const {
        BoundingSphere result;
        result.center = mat.transformPoint(center);
        Vec3 scale = {
            Vec3{mat.at(0,0), mat.at(1,0), mat.at(2,0)}.length(),
            Vec3{mat.at(0,1), mat.at(1,1), mat.at(2,1)}.length(),
            Vec3{mat.at(0,2), mat.at(1,2), mat.at(2,2)}.length()
        };
        float maxScale = std::max({scale.x, scale.y, scale.z});
        result.radius = radius * maxScale;
        return result;
    }
};

// View frustum (6 planes)
class Frustum {
public:
    enum PlaneID {
        Left = 0,
        Right,
        Bottom,
        Top,
        Near,
        Far,
        Count
    };

    Frustum() = default;

    // Extract frustum planes from view-projection matrix
    void extractFromMatrix(const Mat4& vp);

    // Set frustum parameters and compute planes
    void setPerspective(float fovY, float aspect, float nearDist, float farDist,
                        const Vec3& eye, const Vec3& forward, const Vec3& right, const Vec3& up);

    // Culling tests
    Visibility testAABB(const AABB& aabb) const;
    Visibility testSphere(const BoundingSphere& sphere) const;
    Visibility testSphere(const Vec3& center, float radius) const;

    // Simple boolean tests
    bool containsAABB(const AABB& aabb) const;
    bool containsSphere(const Vec3& center, float radius) const;
    bool containsPoint(const Vec3& point) const;

    // Get specific plane
    const Plane& getPlane(PlaneID id) const { return planes_[id]; }

    // Debug
    void print() const;

private:
    std::array<Plane, Count> planes_;

    // For sphere testing
    Vec3 getPosition() const { return position_; }
    float getNear() const { return nearDist_; }
    float getFar() const { return farDist_; }

    Vec3 position_;
    float nearDist_ = 0.1f;
    float farDist_ = 1000.0f;
};

// Camera class
class Camera {
public:
    Camera() = default;

    // Setup
    void setPerspective(float fovY, float aspect, float near, float far);
    void setPosition(const Vec3& pos) { position_ = pos; }
    void setTarget(const Vec3& target) { target_ = target; }
    void setUp(const Vec3& up) { up_ = up; }

    // Getters
    const Vec3& getPosition() const { return position_; }
    const Vec3& getTarget() const { return target_; }
    const Vec3& getUp() const { return up_; }
    float getFOV() const { return fovY_; }
    float getAspect() const { return aspect_; }
    float getNear() const { return near_; }
    float getFar() const { return far_; }

    // Matrices
    const Mat4& getViewMatrix() { updateViewMatrix(); return viewMatrix_; }
    const Mat4& getProjectionMatrix() const { return projMatrix_; }
    Mat4 getViewProjectionMatrix() { return getProjectionMatrix() * getViewMatrix(); }

    // Frustum
    Frustum& getFrustum() { updateFrustum(); return frustum_; }

    // Update frustum from current camera state
    void updateFrustum();

    // Transform
    Vec3 getForward() const { return (target_ - position_).normalized(); }
    Vec3 getRight() const { return getForward().cross(up_).normalized(); }

private:
    Vec3 position_{0, 5, 10};
    Vec3 target_{0, 0, 0};
    Vec3 up_{0, 1, 0};
    float fovY_ = 60.0f * DEG_TO_RAD;
    float aspect_ = 16.0f / 9.0f;
    float near_ = 0.1f;
    float far_ = 1000.0f;

    Mat4 viewMatrix_;
    Mat4 projMatrix_;
    Frustum frustum_;
    bool viewDirty_ = true;

    void updateViewMatrix();
};

} // namespace sg
