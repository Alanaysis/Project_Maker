#pragma once

#include <cmath>
#include <array>
#include <iostream>

namespace sg {

// 3D Vector
struct Vec3 {
    float x = 0.0f, y = 0.0f, z = 0.0f;

    Vec3() = default;
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}

    Vec3 operator+(const Vec3& other) const { return {x + other.x, y + other.y, z + other.z}; }
    Vec3 operator-(const Vec3& other) const { return {x - other.x, y - other.y, z - other.z}; }
    Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
    Vec3 operator/(float s) const { return {x / s, y / s, z / s}; }
    Vec3& operator+=(const Vec3& other) { x += other.x; y += other.y; z += other.z; return *this; }
    Vec3& operator-=(const Vec3& other) { x -= other.x; y -= other.y; z -= other.z; return *this; }
    Vec3& operator*=(float s) { x *= s; y *= s; z *= s; return *this; }

    float dot(const Vec3& other) const { return x * other.x + y * other.y + z * other.z; }
    Vec3 cross(const Vec3& other) const {
        return {y * other.z - z * other.y, z * other.x - x * other.z, x * other.y - y * other.x};
    }
    float length() const { return std::sqrt(x * x + y * y + z * z); }
    float lengthSquared() const { return x * x + y * y + z * z; }
    Vec3 normalized() const {
        float len = length();
        if (len < 1e-6f) return {0, 0, 0};
        return *this / len;
    }

    bool operator==(const Vec3& other) const {
        return std::abs(x - other.x) < 1e-6f && std::abs(y - other.y) < 1e-6f && std::abs(z - other.z) < 1e-6f;
    }
    bool operator!=(const Vec3& other) const { return !(*this == other); }

    static Vec3 up() { return {0, 1, 0}; }
    static Vec3 right() { return {1, 0, 0}; }
    static Vec3 forward() { return {0, 0, -1}; }
    static Vec3 zero() { return {0, 0, 0}; }
    static Vec3 one() { return {1, 1, 1}; }
};

// 4D Vector (for homogeneous coordinates)
struct Vec4 {
    float x = 0.0f, y = 0.0f, z = 0.0f, w = 1.0f;

    Vec4() = default;
    Vec4(float x, float y, float z, float w) : x(x), y(y), z(z), w(w) {}
    Vec4(const Vec3& v, float w) : x(v.x), y(v.y), z(v.z), w(w) {}

    Vec3 xyz() const { return {x, y, z}; }
    Vec3 toVec3() const { return w != 0 ? Vec3{x/w, y/w, z/w} : Vec3{x, y, z}; }

    float dot(const Vec4& other) const { return x * other.x + y * other.y + z * other.z + w * other.w; }
};

// 4x4 Matrix (column-major for OpenGL compatibility)
struct Mat4 {
    std::array<float, 16> m;

    Mat4() : m{} { identity(); }

    void identity() {
        m.fill(0.0f);
        m[0] = m[5] = m[10] = m[15] = 1.0f;
    }

    static Mat4 identityMatrix() {
        Mat4 result;
        result.identity();
        return result;
    }

    // Access element at row r, column c
    float& at(int r, int c) { return m[c * 4 + r]; }
    float at(int r, int c) const { return m[c * 4 + r]; }

    // Matrix multiplication
    Mat4 operator*(const Mat4& other) const {
        Mat4 result;
        result.m.fill(0.0f);
        for (int c = 0; c < 4; ++c) {
            for (int r = 0; r < 4; ++r) {
                for (int k = 0; k < 4; ++k) {
                    result.at(r, c) += at(r, k) * other.at(k, c);
                }
            }
        }
        return result;
    }

    // Transform a point (w=1)
    Vec3 transformPoint(const Vec3& p) const {
        Vec4 result;
        result.x = at(0,0) * p.x + at(0,1) * p.y + at(0,2) * p.z + at(0,3);
        result.y = at(1,0) * p.x + at(1,1) * p.y + at(1,2) * p.z + at(1,3);
        result.z = at(2,0) * p.x + at(2,1) * p.y + at(2,2) * p.z + at(2,3);
        result.w = at(3,0) * p.x + at(3,1) * p.y + at(3,2) * p.z + at(3,3);
        return result.toVec3();
    }

    // Transform a direction (w=0)
    Vec3 transformDirection(const Vec3& d) const {
        return {
            at(0,0) * d.x + at(0,1) * d.y + at(0,2) * d.z,
            at(1,0) * d.x + at(1,1) * d.y + at(1,2) * d.z,
            at(2,0) * d.x + at(2,1) * d.y + at(2,2) * d.z
        };
    }

    // Translation matrix
    static Mat4 translation(const Vec3& t) {
        Mat4 result;
        result.at(0, 3) = t.x;
        result.at(1, 3) = t.y;
        result.at(2, 3) = t.z;
        return result;
    }

    // Scale matrix
    static Mat4 scale(const Vec3& s) {
        Mat4 result;
        result.m.fill(0.0f);
        result.at(0, 0) = s.x;
        result.at(1, 1) = s.y;
        result.at(2, 2) = s.z;
        result.at(3, 3) = 1.0f;
        return result;
    }

    // Rotation around X axis (radians)
    static Mat4 rotationX(float angle) {
        Mat4 result;
        float c = std::cos(angle), s = std::sin(angle);
        result.at(1, 1) = c;  result.at(1, 2) = -s;
        result.at(2, 1) = s;  result.at(2, 2) = c;
        return result;
    }

    // Rotation around Y axis (radians)
    static Mat4 rotationY(float angle) {
        Mat4 result;
        float c = std::cos(angle), s = std::sin(angle);
        result.at(0, 0) = c;  result.at(0, 2) = s;
        result.at(2, 0) = -s; result.at(2, 2) = c;
        return result;
    }

    // Rotation around Z axis (radians)
    static Mat4 rotationZ(float angle) {
        Mat4 result;
        float c = std::cos(angle), s = std::sin(angle);
        result.at(0, 0) = c;  result.at(0, 1) = -s;
        result.at(1, 0) = s;  result.at(1, 1) = c;
        return result;
    }

    // Rotation around arbitrary axis
    static Mat4 rotationAxis(const Vec3& axis, float angle) {
        Vec3 a = axis.normalized();
        float c = std::cos(angle), s = std::sin(angle);
        float t = 1.0f - c;
        Mat4 result;
        result.at(0, 0) = t * a.x * a.x + c;
        result.at(0, 1) = t * a.x * a.y - s * a.z;
        result.at(0, 2) = t * a.x * a.z + s * a.y;
        result.at(1, 0) = t * a.x * a.y + s * a.z;
        result.at(1, 1) = t * a.y * a.y + c;
        result.at(1, 2) = t * a.y * a.z - s * a.x;
        result.at(2, 0) = t * a.x * a.z - s * a.y;
        result.at(2, 1) = t * a.y * a.z + s * a.x;
        result.at(2, 2) = t * a.z * a.z + c;
        return result;
    }

    // Perspective projection matrix
    static Mat4 perspective(float fovY, float aspect, float near, float far) {
        Mat4 result;
        result.m.fill(0.0f);
        float tanHalf = std::tan(fovY * 0.5f);
        result.at(0, 0) = 1.0f / (aspect * tanHalf);
        result.at(1, 1) = 1.0f / tanHalf;
        result.at(2, 2) = -(far + near) / (far - near);
        result.at(2, 3) = -(2.0f * far * near) / (far - near);
        result.at(3, 2) = -1.0f;
        result.at(3, 3) = 0.0f;
        return result;
    }

    // Look-at view matrix
    static Mat4 lookAt(const Vec3& eye, const Vec3& target, const Vec3& worldUp) {
        Vec3 forward = (eye - target).normalized();
        Vec3 right = worldUp.normalized().cross(forward).normalized();
        Vec3 up = forward.cross(right);

        Mat4 result;
        result.at(0, 0) = right.x;   result.at(0, 1) = right.y;   result.at(0, 2) = right.z;   result.at(0, 3) = -right.dot(eye);
        result.at(1, 0) = up.x;      result.at(1, 1) = up.y;      result.at(1, 2) = up.z;      result.at(1, 3) = -up.dot(eye);
        result.at(2, 0) = forward.x; result.at(2, 1) = forward.y; result.at(2, 2) = forward.z; result.at(2, 3) = -forward.dot(eye);
        result.at(3, 0) = 0;         result.at(3, 1) = 0;         result.at(3, 2) = 0;         result.at(3, 3) = 1.0f;
        return result;
    }

    // Transpose
    Mat4 transposed() const {
        Mat4 result;
        for (int r = 0; r < 4; ++r)
            for (int c = 0; c < 4; ++c)
                result.at(r, c) = at(c, r);
        return result;
    }

    // Get translation component
    Vec3 getTranslation() const { return {at(0, 3), at(1, 3), at(2, 3)}; }

    // Inverse (for affine transforms)
    Mat4 inverse() const {
        Mat4 inv;
        auto& o = m;
        auto& i = inv.m;

        i[0] = o[5]*o[10]*o[15] - o[5]*o[11]*o[14] - o[9]*o[6]*o[15] + o[9]*o[7]*o[14] + o[13]*o[6]*o[11] - o[13]*o[7]*o[10];
        i[4] = -o[4]*o[10]*o[15] + o[4]*o[11]*o[14] + o[8]*o[6]*o[15] - o[8]*o[7]*o[14] - o[12]*o[6]*o[11] + o[12]*o[7]*o[10];
        i[8] = o[4]*o[9]*o[15] - o[4]*o[11]*o[13] - o[8]*o[5]*o[15] + o[8]*o[7]*o[13] + o[12]*o[5]*o[11] - o[12]*o[7]*o[9];
        i[12] = -o[4]*o[9]*o[14] + o[4]*o[10]*o[13] + o[8]*o[5]*o[14] - o[8]*o[6]*o[13] - o[12]*o[5]*o[10] + o[12]*o[6]*o[9];

        i[1] = -o[1]*o[10]*o[15] + o[1]*o[11]*o[14] + o[9]*o[2]*o[15] - o[9]*o[3]*o[14] - o[13]*o[2]*o[11] + o[13]*o[3]*o[10];
        i[5] = o[0]*o[10]*o[15] - o[0]*o[11]*o[14] - o[8]*o[2]*o[15] + o[8]*o[3]*o[14] + o[12]*o[2]*o[11] - o[12]*o[3]*o[10];
        i[9] = -o[0]*o[9]*o[15] + o[0]*o[11]*o[13] + o[8]*o[1]*o[15] - o[8]*o[3]*o[13] - o[12]*o[1]*o[11] + o[12]*o[3]*o[9];
        i[13] = o[0]*o[9]*o[14] - o[0]*o[10]*o[13] - o[8]*o[1]*o[14] + o[8]*o[2]*o[13] + o[12]*o[1]*o[10] - o[12]*o[2]*o[9];

        i[2] = o[1]*o[6]*o[15] - o[1]*o[7]*o[14] - o[5]*o[2]*o[15] + o[5]*o[3]*o[14] + o[13]*o[2]*o[7] - o[13]*o[3]*o[6];
        i[6] = -o[0]*o[6]*o[15] + o[0]*o[7]*o[14] + o[4]*o[2]*o[15] - o[4]*o[3]*o[14] - o[12]*o[2]*o[7] + o[12]*o[3]*o[6];
        i[10] = o[0]*o[5]*o[15] - o[0]*o[7]*o[13] - o[4]*o[1]*o[15] + o[4]*o[3]*o[13] + o[12]*o[1]*o[7] - o[12]*o[3]*o[5];
        i[14] = -o[0]*o[5]*o[14] + o[0]*o[6]*o[13] + o[4]*o[1]*o[14] - o[4]*o[2]*o[13] - o[12]*o[1]*o[6] + o[12]*o[2]*o[5];

        i[3] = -o[1]*o[6]*o[11] + o[1]*o[7]*o[10] + o[5]*o[2]*o[11] - o[5]*o[3]*o[10] - o[9]*o[2]*o[7] + o[9]*o[3]*o[6];
        i[7] = o[0]*o[6]*o[11] - o[0]*o[7]*o[10] - o[4]*o[2]*o[11] + o[4]*o[3]*o[10] + o[8]*o[2]*o[7] - o[8]*o[3]*o[6];
        i[11] = -o[0]*o[5]*o[11] + o[0]*o[7]*o[9] + o[4]*o[1]*o[11] - o[4]*o[3]*o[9] - o[8]*o[1]*o[7] + o[8]*o[3]*o[5];
        i[15] = o[0]*o[5]*o[10] - o[0]*o[6]*o[9] - o[4]*o[1]*o[10] + o[4]*o[2]*o[9] + o[8]*o[1]*o[6] - o[8]*o[2]*o[5];

        float det = o[0]*i[0] + o[1]*i[4] + o[2]*i[8] + o[3]*i[12];
        float invDet = 1.0f / det;
        for (int j = 0; j < 16; ++j) i[j] *= invDet;
        return inv;
    }

    // Extract rotation matrix (upper-left 3x3)
    Mat4 getRotationMatrix() const {
        Mat4 result;
        result.m.fill(0.0f);
        result.at(0, 0) = at(0, 0); result.at(0, 1) = at(0, 1); result.at(0, 2) = at(0, 2);
        result.at(1, 0) = at(1, 0); result.at(1, 1) = at(1, 1); result.at(1, 2) = at(1, 2);
        result.at(2, 0) = at(2, 0); result.at(2, 1) = at(2, 1); result.at(2, 2) = at(2, 2);
        result.at(3, 3) = 1.0f;
        return result;
    }

    friend std::ostream& operator<<(std::ostream& os, const Mat4& mat) {
        for (int r = 0; r < 4; ++r) {
            os << "[ ";
            for (int c = 0; c < 4; ++c) {
                os << mat.at(r, c);
                if (c < 3) os << ", ";
            }
            os << " ]\n";
        }
        return os;
    }
};

// Axis-Aligned Bounding Box
struct AABB {
    Vec3 min{1e30f, 1e30f, 1e30f};
    Vec3 max{-1e30f, -1e30f, -1e30f};

    AABB() = default;
    AABB(const Vec3& min, const Vec3& max) : min(min), max(max) {}

    Vec3 center() const { return (min + max) * 0.5f; }
    Vec3 extent() const { return max - min; }
    Vec3 halfExtent() const { return extent() * 0.5f; }

    // Expand to include a point
    void expand(const Vec3& point) {
        min.x = std::min(min.x, point.x);
        min.y = std::min(min.y, point.y);
        min.z = std::min(min.z, point.z);
        max.x = std::max(max.x, point.x);
        max.y = std::max(max.y, point.y);
        max.z = std::max(max.z, point.z);
    }

    // Merge with another AABB
    void merge(const AABB& other) {
        expand(other.min);
        expand(other.max);
    }

    // Transform AABB by matrix
    AABB transformed(const Mat4& mat) const {
        AABB result;
        // Transform all 8 corners
        Vec3 corners[8] = {
            {min.x, min.y, min.z}, {max.x, min.y, min.z},
            {min.x, max.y, min.z}, {max.x, max.y, min.z},
            {min.x, min.y, max.z}, {max.x, min.y, max.z},
            {min.x, max.y, max.z}, {max.x, max.y, max.z}
        };
        for (const auto& corner : corners) {
            result.expand(mat.transformPoint(corner));
        }
        return result;
    }
};

// Color
struct Color {
    float r = 1.0f, g = 1.0f, b = 1.0f, a = 1.0f;

    Color() = default;
    Color(float r, float g, float b, float a = 1.0f) : r(r), g(g), b(b), a(a) {}

    static Color red() { return {1, 0, 0}; }
    static Color green() { return {0, 1, 0}; }
    static Color blue() { return {0, 0, 1}; }
    static Color white() { return {1, 1, 1}; }
    static Color black() { return {0, 0, 0}; }
    static Color yellow() { return {1, 1, 0}; }
    static Color cyan() { return {0, 1, 1}; }
    static Color magenta() { return {1, 0, 1}; }
};

// Constants
constexpr float PI = 3.14159265358979f;
constexpr float DEG_TO_RAD = PI / 180.0f;
constexpr float RAD_TO_DEG = 180.0f / PI;

inline float degToRad(float degrees) { return degrees * DEG_TO_RAD; }
inline float radToDeg(float radians) { return radians * RAD_TO_DEG; }

} // namespace sg
