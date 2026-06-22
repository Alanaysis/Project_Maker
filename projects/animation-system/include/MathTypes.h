#pragma once

#include <cmath>
#include <array>

namespace anim {

// 3D Vector
struct Vec3 {
    float x = 0.0f, y = 0.0f, z = 0.0f;

    Vec3() = default;
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}

    Vec3 operator+(const Vec3& v) const { return {x + v.x, y + v.y, z + v.z}; }
    Vec3 operator-(const Vec3& v) const { return {x - v.x, y - v.y, z - v.z}; }
    Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
    Vec3& operator+=(const Vec3& v) { x += v.x; y += v.y; z += v.z; return *this; }

    float length() const { return std::sqrt(x * x + y * y + z * z); }
    Vec3 normalized() const {
        float len = length();
        if (len < 1e-6f) return {0, 0, 0};
        return {x / len, y / len, z / len};
    }
    float dot(const Vec3& v) const { return x * v.x + y * v.y + z * v.z; }
    Vec3 cross(const Vec3& v) const {
        return {y * v.z - z * v.y, z * v.x - x * v.z, x * v.y - y * v.x};
    }
};

// Quaternion for rotation
struct Quat {
    float w = 1.0f, x = 0.0f, y = 0.0f, z = 0.0f;

    Quat() = default;
    Quat(float w, float x, float y, float z) : w(w), x(x), y(y), z(z) {}

    // Create quaternion from axis-angle (radians)
    static Quat fromAxisAngle(const Vec3& axis, float angle) {
        float half = angle * 0.5f;
        float s = std::sin(half);
        Vec3 n = axis.normalized();
        return {std::cos(half), n.x * s, n.y * s, n.z * s};
    }

    // Create quaternion from Euler angles (radians)
    static Quat fromEuler(float pitch, float yaw, float roll) {
        float cp = std::cos(pitch * 0.5f), sp = std::sin(pitch * 0.5f);
        float cy = std::cos(yaw * 0.5f),   sy = std::sin(yaw * 0.5f);
        float cr = std::cos(roll * 0.5f),  sr = std::sin(roll * 0.5f);
        return {
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy
        };
    }

    Quat operator*(const Quat& q) const {
        return {
            w * q.w - x * q.x - y * q.y - z * q.z,
            w * q.x + x * q.w + y * q.z - z * q.y,
            w * q.y - x * q.z + y * q.w + z * q.x,
            w * q.z + x * q.y - y * q.x + z * q.w
        };
    }

    Quat conjugate() const { return {w, -x, -y, -z}; }

    float length() const { return std::sqrt(w * w + x * x + y * y + z * z); }

    Quat normalized() const {
        float len = length();
        if (len < 1e-6f) return {1, 0, 0, 0};
        return {w / len, x / len, y / len, z / len};
    }

    Quat inverse() const {
        float len2 = w * w + x * x + y * y + z * z;
        if (len2 < 1e-6f) return {1, 0, 0, 0};
        return {w / len2, -x / len2, -y / len2, -z / len2};
    }

    // Rotate a vector by this quaternion
    Vec3 rotate(const Vec3& v) const {
        Quat p{0, v.x, v.y, v.z};
        Quat result = (*this) * p * conjugate();
        return {result.x, result.y, result.z};
    }

    // Spherical linear interpolation
    static Quat slerp(const Quat& a, const Quat& b, float t) {
        float dot = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z;
        Quat b2 = b;
        if (dot < 0.0f) {
            dot = -dot;
            b2 = {-b.w, -b.x, -b.y, -b.z};
        }
        if (dot > 0.9995f) {
            // Linear interpolation for very close quaternions
            return Quat{
                a.w + t * (b2.w - a.w),
                a.x + t * (b2.x - a.x),
                a.y + t * (b2.y - a.y),
                a.z + t * (b2.z - a.z)
            }.normalized();
        }
        float theta0 = std::acos(dot);
        float theta = theta0 * t;
        float sinTheta = std::sin(theta);
        float sinTheta0 = std::sin(theta0);
        float wa = std::cos(theta) - dot * sinTheta / sinTheta0;
        float wb = sinTheta / sinTheta0;
        return {
            wa * a.w + wb * b2.w,
            wa * a.x + wb * b2.x,
            wa * a.y + wb * b2.y,
            wa * a.z + wb * b2.z
        };
    }
};

// 4x4 Matrix
struct Mat4 {
    std::array<std::array<float, 4>, 4> m;

    Mat4() {
        for (int i = 0; i < 4; i++)
            for (int j = 0; j < 4; j++)
                m[i][j] = (i == j) ? 1.0f : 0.0f;
    }

    Mat4 operator*(const Mat4& other) const {
        Mat4 result;
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 4; j++) {
                result.m[i][j] = 0;
                for (int k = 0; k < 4; k++) {
                    result.m[i][j] += m[i][k] * other.m[k][j];
                }
            }
        }
        return result;
    }

    Vec3 transformPoint(const Vec3& p) const {
        return {
            m[0][0] * p.x + m[0][1] * p.y + m[0][2] * p.z + m[0][3],
            m[1][0] * p.x + m[1][1] * p.y + m[1][2] * p.z + m[1][3],
            m[2][0] * p.x + m[2][1] * p.y + m[2][2] * p.z + m[2][3]
        };
    }

    // Create translation matrix
    static Mat4 translation(const Vec3& t) {
        Mat4 result;
        result.m[0][3] = t.x;
        result.m[1][3] = t.y;
        result.m[2][3] = t.z;
        return result;
    }

    // Create scale matrix
    static Mat4 scale(const Vec3& s) {
        Mat4 result;
        result.m[0][0] = s.x;
        result.m[1][1] = s.y;
        result.m[2][2] = s.z;
        return result;
    }

    // Create rotation matrix from quaternion
    static Mat4 rotation(const Quat& q) {
        Mat4 result;
        float xx = q.x * q.x, yy = q.y * q.y, zz = q.z * q.z;
        float xy = q.x * q.y, xz = q.x * q.z, yz = q.y * q.z;
        float wx = q.w * q.x, wy = q.w * q.y, wz = q.w * q.z;

        result.m[0][0] = 1 - 2 * (yy + zz);
        result.m[0][1] = 2 * (xy - wz);
        result.m[0][2] = 2 * (xz + wy);
        result.m[1][0] = 2 * (xy + wz);
        result.m[1][1] = 1 - 2 * (xx + zz);
        result.m[1][2] = 2 * (yz - wx);
        result.m[2][0] = 2 * (xz - wy);
        result.m[2][1] = 2 * (yz + wx);
        result.m[2][2] = 1 - 2 * (xx + yy);
        return result;
    }

    // Create TRS matrix (Translation * Rotation * Scale)
    static Mat4 trs(const Vec3& translation, const Quat& rotation, const Vec3& scale) {
        return translation_mat(translation) * rotation_mat(rotation) * scale_mat(scale);
    }

    // Helper aliases for clarity
    static Mat4 translation_mat(const Vec3& t) { return translation(t); }
    static Mat4 rotation_mat(const Quat& q) { return rotation(q); }
    static Mat4 scale_mat(const Vec3& s) { return scale(s); }
};

} // namespace anim
