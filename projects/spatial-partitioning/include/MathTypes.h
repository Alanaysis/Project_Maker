#pragma once

#include <cmath>
#include <algorithm>
#include <limits>

namespace spatial {

// 向量
struct Vec3 {
    float x, y, z;

    Vec3() : x(0), y(0), z(0) {}
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}
    explicit Vec3(float v) : x(v), y(v), z(v) {}

    Vec3 operator+(const Vec3& v) const { return {x + v.x, y + v.y, z + v.z}; }
    Vec3 operator-(const Vec3& v) const { return {x - v.x, y - v.y, z - v.z}; }
    Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
    Vec3 operator/(float s) const { return {x / s, y / s, z / s}; }

    Vec3& operator+=(const Vec3& v) { x += v.x; y += v.y; z += v.z; return *this; }
    Vec3& operator-=(const Vec3& v) { x -= v.x; y -= v.y; z -= v.z; return *this; }
    Vec3& operator*=(float s) { x *= s; y *= s; z *= s; return *this; }

    float operator[](int i) const { return (&x)[i]; }
    float& operator[](int i) { return (&x)[i]; }

    float length() const { return std::sqrt(x * x + y * y + z * z); }
    float lengthSquared() const { return x * x + y * y + z * z; }
    Vec3 normalized() const { float l = length(); return *this / l; }

    float dot(const Vec3& v) const { return x * v.x + y * v.y + z * v.z; }
    Vec3 cross(const Vec3& v) const {
        return {y * v.z - z * v.y, z * v.x - x * v.z, x * v.y - y * v.x};
    }

    Vec3 min(const Vec3& v) const {
        return {std::min(x, v.x), std::min(y, v.y), std::min(z, v.z)};
    }
    Vec3 max(const Vec3& v) const {
        return {std::max(x, v.x), std::max(y, v.y), std::max(z, v.z)};
    }

    bool operator==(const Vec3& v) const { return x == v.x && y == v.y && z == v.z; }
    bool operator!=(const Vec3& v) const { return !(*this == v); }
};

// 射线
struct Ray {
    Vec3 origin;
    Vec3 direction;

    Ray() {}
    Ray(const Vec3& origin, const Vec3& direction) : origin(origin), direction(direction.normalized()) {}

    Vec3 pointAt(float t) const { return origin + direction * t; }
};

// 平面
struct Plane {
    Vec3 normal;
    float distance;

    Plane() : normal(0, 1, 0), distance(0) {}
    Plane(const Vec3& normal, float distance) : normal(normal.normalized()), distance(distance) {}
    Plane(const Vec3& a, const Vec3& b, const Vec3& c) {
        normal = (b - a).cross(c - a).normalized();
        distance = normal.dot(a);
    }

    float distanceToPoint(const Vec3& p) const { return normal.dot(p) - distance; }

    Vec3 project(const Vec3& p) const { return p - normal * distanceToPoint(p); }
};

// 三角形
struct Triangle {
    Vec3 v0, v1, v2;

    Triangle() {}
    Triangle(const Vec3& v0, const Vec3& v1, const Vec3& v2) : v0(v0), v1(v1), v2(v2) {}

    Vec3 centroid() const { return (v0 + v1 + v2) / 3.0f; }
    Vec3 normal() const { return (v1 - v0).cross(v2 - v0).normalized(); }
    float area() const { return (v1 - v0).cross(v2 - v0).length() * 0.5f; }
};

} // namespace spatial
