#pragma once

#include <cmath>
#include <iostream>

namespace rt {

class Vec3 {
public:
    double x, y, z;

    Vec3() : x(0), y(0), z(0) {}
    Vec3(double x, double y, double z) : x(x), y(y), z(z) {}

    // 向量加法
    Vec3 operator+(const Vec3& v) const {
        return Vec3(x + v.x, y + v.y, z + v.z);
    }

    // 向量减法
    Vec3 operator-(const Vec3& v) const {
        return Vec3(x - v.x, y - v.y, z - v.z);
    }

    // 标量乘法
    Vec3 operator*(double t) const {
        return Vec3(x * t, y * t, z * t);
    }

    // 向量分量乘法
    Vec3 operator*(const Vec3& v) const {
        return Vec3(x * v.x, y * v.y, z * v.z);
    }

    // 标量除法
    Vec3 operator/(double t) const {
        return Vec3(x / t, y / t, z / t);
    }

    // 取负
    Vec3 operator-() const {
        return Vec3(-x, -y, -z);
    }

    // 复合赋值
    Vec3& operator+=(const Vec3& v) {
        x += v.x; y += v.y; z += v.z;
        return *this;
    }

    Vec3& operator*=(double t) {
        x *= t; y *= t; z *= t;
        return *this;
    }

    Vec3& operator/=(double t) {
        x /= t; y /= t; z /= t;
        return *this;
    }

    // 点积
    double dot(const Vec3& v) const {
        return x * v.x + y * v.y + z * v.z;
    }

    // 叉积
    Vec3 cross(const Vec3& v) const {
        return Vec3(
            y * v.z - z * v.y,
            z * v.x - x * v.z,
            x * v.y - y * v.x
        );
    }

    // 向量长度
    double length() const {
        return std::sqrt(x * x + y * y + z * z);
    }

    // 向量长度平方
    double length_squared() const {
        return x * x + y * y + z * z;
    }

    // 单位化
    Vec3 normalize() const {
        double len = length();
        if (len < 1e-10) return Vec3(0, 0, 0);
        return Vec3(x / len, y / len, z / len);
    }

    // 反射
    Vec3 reflect(const Vec3& normal) const {
        return *this - normal * 2.0 * this->dot(normal);
    }

    // 折射 (Snell's law)
    Vec3 refract(const Vec3& normal, double eta_ratio) const {
        double cos_theta = std::fmin((-(*this)).dot(normal), 1.0);
        Vec3 r_out_perp = (*this + normal * cos_theta) * eta_ratio;
        Vec3 r_out_parallel = normal * (-std::sqrt(std::fabs(1.0 - r_out_perp.length_squared())));
        return r_out_perp + r_out_parallel;
    }

    // 输出
    friend std::ostream& operator<<(std::ostream& os, const Vec3& v) {
        os << "(" << v.x << ", " << v.y << ", " << v.z << ")";
        return os;
    }
};

// 标量 * 向量
inline Vec3 operator*(double t, const Vec3& v) {
    return Vec3(t * v.x, t * v.y, t * v.z);
}

// 工具函数
inline double dot(const Vec3& u, const Vec3& v) {
    return u.dot(v);
}

inline Vec3 cross(const Vec3& u, const Vec3& v) {
    return u.cross(v);
}

inline Vec3 normalize(const Vec3& v) {
    return v.normalize();
}

} // namespace rt
