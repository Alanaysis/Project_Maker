#pragma once

#include <cmath>
#include <algorithm>
#include <array>
#include <cassert>

namespace sg {

// ⭐ 核心数学类型：场景图的基础构建块

/**
 * 三维向量 - 用于表示位置、方向、缩放等
 */
struct Vec3 {
    float x, y, z;

    Vec3() : x(0), y(0), z(0) {}
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}
    Vec3(float v) : x(v), y(v), z(v) {}

    Vec3 operator+(const Vec3& rhs) const { return {x + rhs.x, y + rhs.y, z + rhs.z}; }
    Vec3 operator-(const Vec3& rhs) const { return {x - rhs.x, y - rhs.y, z - rhs.z}; }
    Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
    Vec3 operator/(float s) const { return {x / s, y / s, z / s}; }
    Vec3 operator-() const { return {-x, -y, -z}; }

    Vec3& operator+=(const Vec3& rhs) { x += rhs.x; y += rhs.y; z += rhs.z; return *this; }
    Vec3& operator-=(const Vec3& rhs) { x -= rhs.x; y -= rhs.y; z -= rhs.z; return *this; }
    Vec3& operator*=(float s) { x *= s; y *= s; z *= s; return *this; }

    float dot(const Vec3& rhs) const { return x * rhs.x + y * rhs.y + z * rhs.z; }
    Vec3 cross(const Vec3& rhs) const {
        return {y * rhs.z - z * rhs.y, z * rhs.x - x * rhs.z, x * rhs.y - y * rhs.x};
    }

    float length() const { return std::sqrt(x * x + y * y + z * z); }
    float length_sq() const { return x * x + y * y + z * z; }

    Vec3 normalized() const {
        float len = length();
        if (len < 1e-6f) return {0, 0, 0};
        return *this / len;
    }

    float& operator[](int i) { return (&x)[i]; }
    float operator[](int i) const { return (&x)[i]; }

    bool operator==(const Vec3& rhs) const {
        return std::abs(x - rhs.x) < 1e-6f && std::abs(y - rhs.y) < 1e-6f && std::abs(z - rhs.z) < 1e-6f;
    }
    bool operator!=(const Vec3& rhs) const { return !(*this == rhs); }
};

/**
 * 四维向量 - 用于齐次坐标
 */
struct Vec4 {
    float x, y, z, w;

    Vec4() : x(0), y(0), z(0), w(0) {}
    Vec4(float x, float y, float z, float w) : x(x), y(y), z(z), w(w) {}
    Vec4(const Vec3& v, float w) : x(v.x), y(v.y), z(v.z), w(w) {}

    Vec3 xyz() const { return {x, y, z}; }
    Vec3 to_vec3() const { return (std::abs(w) > 1e-6f) ? Vec3{x/w, y/w, z/w} : Vec3{x, y, z}; }

    float& operator[](int i) { return (&x)[i]; }
    float operator[](int i) const { return (&x)[i]; }
};

/**
 * 四元数 - 用于旋转表示（避免万向锁）
 */
struct Quaternion {
    float x, y, z, w;

    Quaternion() : x(0), y(0), z(0), w(1) {}
    Quaternion(float x, float y, float z, float w) : x(x), y(y), z(z), w(w) {}

    /**
     * 从欧拉角（弧度）创建四元数
     * 旋转顺序：Y -> X -> Z（常见的航空顺序）
     * q = Qy * Qx * Qz
     */
    static Quaternion from_euler(float pitch, float yaw, float roll) {
        float cp = std::cos(pitch * 0.5f), sp = std::sin(pitch * 0.5f);
        float cy = std::cos(yaw * 0.5f),   sy = std::sin(yaw * 0.5f);
        float cr = std::cos(roll * 0.5f),  sr = std::sin(roll * 0.5f);
        return {
            cy * sp * cr + sy * cp * sr,   // x
            sy * cp * cr - cy * sp * sr,   // y
            cy * cp * sr - sy * sp * cr,   // z
            cy * cp * cr + sy * sp * sr    // w
        };
    }

    /**
     * 从轴角表示创建四元数
     */
    static Quaternion from_axis_angle(const Vec3& axis, float angle_rad) {
        Vec3 a = axis.normalized();
        float half = angle_rad * 0.5f;
        float s = std::sin(half);
        return {a.x * s, a.y * s, a.z * s, std::cos(half)};
    }

    Quaternion operator*(const Quaternion& q) const {
        return {
            w * q.x + x * q.w + y * q.z - z * q.y,
            w * q.y - x * q.z + y * q.w + z * q.x,
            w * q.z + x * q.y - y * q.x + z * q.w,
            w * q.w - x * q.x - y * q.y - z * q.z
        };
    }

    Quaternion conjugate() const { return {-x, -y, -z, w}; }

    float length() const { return std::sqrt(x*x + y*y + z*z + w*w); }

    Quaternion normalized() const {
        float len = length();
        if (len < 1e-6f) return {0, 0, 0, 1};
        return {x/len, y/len, z/len, w/len};
    }

    /**
     * 用四元数旋转向量
     * q * v * q^-1
     */
    Vec3 rotate(const Vec3& v) const {
        Quaternion qv(v.x, v.y, v.z, 0);
        Quaternion result = (*this) * qv * conjugate();
        return {result.x, result.y, result.z};
    }

    bool operator==(const Quaternion& rhs) const {
        return std::abs(x - rhs.x) < 1e-6f && std::abs(y - rhs.y) < 1e-6f &&
               std::abs(z - rhs.z) < 1e-6f && std::abs(w - rhs.w) < 1e-6f;
    }
};

/**
 * 4x4 矩阵 - 用于变换计算（列主序存储）
 *
 * 内存布局（列主序）：
 * | m[0] m[4] m[8]  m[12] |
 * | m[1] m[5] m[9]  m[13] |
 * | m[2] m[6] m[10] m[14] |
 * | m[3] m[7] m[11] m[15] |
 */
struct Mat4 {
    std::array<float, 16> m;

    Mat4() : m{} { set_identity(); }

    void set_identity() {
        m.fill(0);
        m[0] = m[5] = m[10] = m[15] = 1.0f;
    }

    float& at(int row, int col) { return m[col * 4 + row]; }
    float at(int row, int col) const { return m[col * 4 + row]; }

    const float* data() const { return m.data(); }

    /**
     * 构建平移矩阵
     */
    static Mat4 translation(const Vec3& t) {
        Mat4 result;
        result.at(0, 3) = t.x;
        result.at(1, 3) = t.y;
        result.at(2, 3) = t.z;
        return result;
    }

    /**
     * 构建缩放矩阵
     */
    static Mat4 scaling(const Vec3& s) {
        Mat4 result;
        result.at(0, 0) = s.x;
        result.at(1, 1) = s.y;
        result.at(2, 2) = s.z;
        return result;
    }

    /**
     * 从四元数构建旋转矩阵
     */
    static Mat4 rotation(const Quaternion& q) {
        Quaternion nq = q.normalized();
        float x = nq.x, y = nq.y, z = nq.z, w = nq.w;
        float x2 = x+x, y2 = y+y, z2 = z+z;
        float xx = x*x2, xy = x*y2, xz = x*z2;
        float yy = y*y2, yz = y*z2, zz = z*z2;
        float wx = w*x2, wy = w*y2, wz = w*z2;

        Mat4 result;
        result.at(0, 0) = 1.0f - (yy + zz);
        result.at(0, 1) = xy - wz;
        result.at(0, 2) = xz + wy;
        result.at(1, 0) = xy + wz;
        result.at(1, 1) = 1.0f - (xx + zz);
        result.at(1, 2) = yz - wx;
        result.at(2, 0) = xz - wy;
        result.at(2, 1) = yz + wx;
        result.at(2, 2) = 1.0f - (xx + yy);
        return result;
    }

    /**
     * 构建 TRS（平移-旋转-缩放）组合矩阵
     * M = T * R * S
     */
    static Mat4 trs(const Vec3& translation, const Quaternion& rotation, const Vec3& scale) {
        return translation_mat(translation) * rotation_mat(rotation) * scaling_mat(scale);
    }

    // 为了兼容性提供的别名
    static Mat4 translation_mat(const Vec3& t) { return translation(t); }
    static Mat4 rotation_mat(const Quaternion& q) { return rotation(q); }
    static Mat4 scaling_mat(const Vec3& s) { return scaling(s); }

    /**
     * 构建透视投影矩阵
     * @param fov_y_rad 垂直视场角（弧度）
     * @param aspect 宽高比
     * @param near 近裁剪面距离
     * @param far 远裁剪面距离
     */
    static Mat4 perspective(float fov_y_rad, float aspect, float near, float far) {
        float tan_half = std::tan(fov_y_rad * 0.5f);
        Mat4 result;
        result.m.fill(0);
        result.at(0, 0) = 1.0f / (aspect * tan_half);
        result.at(1, 1) = 1.0f / tan_half;
        result.at(2, 2) = -(far + near) / (far - near);
        result.at(2, 3) = -(2.0f * far * near) / (far - near);
        result.at(3, 2) = -1.0f;
        result.at(3, 3) = 0.0f;
        return result;
    }

    /**
     * 构建视图矩阵（Look-At）
     */
    static Mat4 look_at(const Vec3& eye, const Vec3& target, const Vec3& up) {
        Vec3 f = (target - eye).normalized();
        Vec3 r = f.cross(up).normalized();
        Vec3 u = r.cross(f);

        Mat4 result;
        result.at(0, 0) = r.x;  result.at(0, 1) = r.y;  result.at(0, 2) = r.z;  result.at(0, 3) = -r.dot(eye);
        result.at(1, 0) = u.x;  result.at(1, 1) = u.y;  result.at(1, 2) = u.z;  result.at(1, 3) = -u.dot(eye);
        result.at(2, 0) = -f.x; result.at(2, 1) = -f.y; result.at(2, 2) = -f.z; result.at(2, 3) = f.dot(eye);
        result.at(3, 0) = 0;    result.at(3, 1) = 0;    result.at(3, 2) = 0;    result.at(3, 3) = 1;
        return result;
    }

    /**
     * 矩阵乘法
     */
    Mat4 operator*(const Mat4& rhs) const {
        Mat4 result;
        result.m.fill(0);
        for (int col = 0; col < 4; ++col) {
            for (int row = 0; row < 4; ++row) {
                float sum = 0;
                for (int k = 0; k < 4; ++k) {
                    sum += at(row, k) * rhs.at(k, col);
                }
                result.at(row, col) = sum;
            }
        }
        return result;
    }

    /**
     * 矩阵乘以向量（齐次坐标）
     */
    Vec4 operator*(const Vec4& v) const {
        Vec4 result;
        result.x = at(0,0)*v.x + at(0,1)*v.y + at(0,2)*v.z + at(0,3)*v.w;
        result.y = at(1,0)*v.x + at(1,1)*v.y + at(1,2)*v.z + at(1,3)*v.w;
        result.z = at(2,0)*v.x + at(2,1)*v.y + at(2,2)*v.z + at(2,3)*v.w;
        result.w = at(3,0)*v.x + at(3,1)*v.y + at(3,2)*v.z + at(3,3)*v.w;
        return result;
    }

    /**
     * 变换点（应用平移）
     */
    Vec3 transform_point(const Vec3& p) const {
        Vec4 result = *this * Vec4(p, 1.0f);
        return result.to_vec3();
    }

    /**
     * 变换方向（不应用平移）
     */
    Vec3 transform_direction(const Vec3& d) const {
        Vec4 result = *this * Vec4(d, 0.0f);
        return {result.x, result.y, result.z};
    }

    /**
     * 提取平移分量
     */
    Vec3 get_translation() const { return {at(0, 3), at(1, 3), at(2, 3)}; }

    /**
     * 提取 3x3 部分（旋转+缩放）
     */
    Mat4 get_rotation_scale() const {
        Mat4 result;
        result.m.fill(0);
        for (int r = 0; r < 3; ++r)
            for (int c = 0; c < 3; ++c)
                result.at(r, c) = at(r, c);
        result.at(3, 3) = 1.0f;
        return result;
    }

    /**
     * 计算行列式（使用 3x3 子矩阵）
     */
    float determinant() const {
        return
            at(0,0) * (at(1,1)*(at(2,2)*at(3,3)-at(2,3)*at(3,2)) - at(1,2)*(at(2,1)*at(3,3)-at(2,3)*at(3,1)) + at(1,3)*(at(2,1)*at(3,2)-at(2,2)*at(3,1))) -
            at(0,1) * (at(1,0)*(at(2,2)*at(3,3)-at(2,3)*at(3,2)) - at(1,2)*(at(2,0)*at(3,3)-at(2,3)*at(3,0)) + at(1,3)*(at(2,0)*at(3,2)-at(2,2)*at(3,0))) +
            at(0,2) * (at(1,0)*(at(2,1)*at(3,3)-at(2,3)*at(3,1)) - at(1,1)*(at(2,0)*at(3,3)-at(2,3)*at(3,0)) + at(1,3)*(at(2,0)*at(3,1)-at(2,1)*at(3,0))) -
            at(0,3) * (at(1,0)*(at(2,1)*at(3,2)-at(2,2)*at(3,1)) - at(1,1)*(at(2,0)*at(3,2)-at(2,2)*at(3,0)) + at(1,2)*(at(2,0)*at(3,1)-at(2,1)*at(3,0)));
    }

    /**
     * 计算逆矩阵
     */
    Mat4 inverse() const {
        Mat4 inv;
        float det = determinant();
        if (std::abs(det) < 1e-10f) return Mat4(); // 返回单位矩阵

        float inv_det = 1.0f / det;

        inv.at(0,0) =  (at(1,1)*(at(2,2)*at(3,3)-at(2,3)*at(3,2)) - at(1,2)*(at(2,1)*at(3,3)-at(2,3)*at(3,1)) + at(1,3)*(at(2,1)*at(3,2)-at(2,2)*at(3,1))) * inv_det;
        inv.at(0,1) = -(at(0,1)*(at(2,2)*at(3,3)-at(2,3)*at(3,2)) - at(0,2)*(at(2,1)*at(3,3)-at(2,3)*at(3,1)) + at(0,3)*(at(2,1)*at(3,2)-at(2,2)*at(3,1))) * inv_det;
        inv.at(0,2) =  (at(0,1)*(at(1,2)*at(3,3)-at(1,3)*at(3,2)) - at(0,2)*(at(1,1)*at(3,3)-at(1,3)*at(3,1)) + at(0,3)*(at(1,1)*at(3,2)-at(1,2)*at(3,1))) * inv_det;
        inv.at(0,3) = -(at(0,1)*(at(1,2)*at(2,3)-at(1,3)*at(2,2)) - at(0,2)*(at(1,1)*at(2,3)-at(1,3)*at(2,1)) + at(0,3)*(at(1,1)*at(2,2)-at(1,2)*at(2,1))) * inv_det;

        inv.at(1,0) = -(at(1,0)*(at(2,2)*at(3,3)-at(2,3)*at(3,2)) - at(1,2)*(at(2,0)*at(3,3)-at(2,3)*at(3,0)) + at(1,3)*(at(2,0)*at(3,2)-at(2,2)*at(3,0))) * inv_det;
        inv.at(1,1) =  (at(0,0)*(at(2,2)*at(3,3)-at(2,3)*at(3,2)) - at(0,2)*(at(2,0)*at(3,3)-at(2,3)*at(3,0)) + at(0,3)*(at(2,0)*at(3,2)-at(2,2)*at(3,0))) * inv_det;
        inv.at(1,2) = -(at(0,0)*(at(1,2)*at(3,3)-at(1,3)*at(3,2)) - at(0,2)*(at(1,0)*at(3,3)-at(1,3)*at(3,0)) + at(0,3)*(at(1,0)*at(3,2)-at(1,2)*at(3,0))) * inv_det;
        inv.at(1,3) =  (at(0,0)*(at(1,2)*at(2,3)-at(1,3)*at(2,2)) - at(0,2)*(at(1,0)*at(2,3)-at(1,3)*at(2,0)) + at(0,3)*(at(1,0)*at(2,2)-at(1,2)*at(2,0))) * inv_det;

        inv.at(2,0) =  (at(1,0)*(at(2,1)*at(3,3)-at(2,3)*at(3,1)) - at(1,1)*(at(2,0)*at(3,3)-at(2,3)*at(3,0)) + at(1,3)*(at(2,0)*at(3,1)-at(2,1)*at(3,0))) * inv_det;
        inv.at(2,1) = -(at(0,0)*(at(2,1)*at(3,3)-at(2,3)*at(3,1)) - at(0,1)*(at(2,0)*at(3,3)-at(2,3)*at(3,0)) + at(0,3)*(at(2,0)*at(3,1)-at(2,1)*at(3,0))) * inv_det;
        inv.at(2,2) =  (at(0,0)*(at(1,1)*at(3,3)-at(1,3)*at(3,1)) - at(0,1)*(at(1,0)*at(3,3)-at(1,3)*at(3,0)) + at(0,3)*(at(1,0)*at(3,1)-at(1,1)*at(3,0))) * inv_det;
        inv.at(2,3) = -(at(0,0)*(at(1,1)*at(2,3)-at(1,3)*at(2,1)) - at(0,1)*(at(1,0)*at(2,3)-at(1,3)*at(2,0)) + at(0,3)*(at(1,0)*at(2,1)-at(1,1)*at(2,0))) * inv_det;

        inv.at(3,0) = -(at(1,0)*(at(2,1)*at(3,2)-at(2,2)*at(3,1)) - at(1,1)*(at(2,0)*at(3,2)-at(2,2)*at(3,0)) + at(1,2)*(at(2,0)*at(3,1)-at(2,1)*at(3,0))) * inv_det;
        inv.at(3,1) =  (at(0,0)*(at(2,1)*at(3,2)-at(2,2)*at(3,1)) - at(0,1)*(at(2,0)*at(3,2)-at(2,2)*at(3,0)) + at(0,2)*(at(2,0)*at(3,1)-at(2,1)*at(3,0))) * inv_det;
        inv.at(3,2) = -(at(0,0)*(at(1,1)*at(3,2)-at(1,2)*at(3,1)) - at(0,1)*(at(1,0)*at(3,2)-at(1,2)*at(3,0)) + at(0,2)*(at(1,0)*at(3,1)-at(1,1)*at(3,0))) * inv_det;
        inv.at(3,3) =  (at(0,0)*(at(1,1)*at(2,2)-at(1,2)*at(2,1)) - at(0,1)*(at(1,0)*at(2,2)-at(1,2)*at(2,0)) + at(0,2)*(at(1,0)*at(2,1)-at(1,1)*at(2,0))) * inv_det;

        return inv;
    }

    /**
     * 矩阵转置
     */
    Mat4 transposed() const {
        Mat4 result;
        for (int r = 0; r < 4; ++r)
            for (int c = 0; c < 4; ++c)
                result.at(r, c) = at(c, r);
        return result;
    }
};

} // namespace sg
