#pragma once

#include <cmath>
#include <iostream>

namespace physics_engine {

struct Vector2D {
    double x = 0.0;
    double y = 0.0;

    Vector2D() = default;
    Vector2D(double x, double y) : x(x), y(y) {}

    // 向量加法
    Vector2D operator+(const Vector2D& other) const {
        return {x + other.x, y + other.y};
    }

    // 向量减法
    Vector2D operator-(const Vector2D& other) const {
        return {x - other.x, y - other.y};
    }

    // 标量乘法
    Vector2D operator*(double scalar) const {
        return {x * scalar, y * scalar};
    }

    // 标量除法
    Vector2D operator/(double scalar) const {
        return {x / scalar, y / scalar};
    }

    // 复合赋值运算符
    Vector2D& operator+=(const Vector2D& other) {
        x += other.x;
        y += other.y;
        return *this;
    }

    Vector2D& operator-=(const Vector2D& other) {
        x -= other.x;
        y -= other.y;
        return *this;
    }

    Vector2D& operator*=(double scalar) {
        x *= scalar;
        y *= scalar;
        return *this;
    }

    Vector2D& operator/=(double scalar) {
        x /= scalar;
        y /= scalar;
        return *this;
    }

    // 取反
    Vector2D operator-() const {
        return {-x, -y};
    }

    // 相等比较
    bool operator==(const Vector2D& other) const {
        const double epsilon = 1e-10;
        return std::abs(x - other.x) < epsilon && std::abs(y - other.y) < epsilon;
    }

    bool operator!=(const Vector2D& other) const {
        return !(*this == other);
    }

    // 点积
    double dot(const Vector2D& other) const {
        return x * other.x + y * other.y;
    }

    // 叉积（2D 返回标量）
    double cross(const Vector2D& other) const {
        return x * other.y - y * other.x;
    }

    // 向量长度的平方
    double length_squared() const {
        return x * x + y * y;
    }

    // 向量长度
    double length() const {
        return std::sqrt(length_squared());
    }

    // 单位化向量
    Vector2D normalized() const {
        double len = length();
        if (len < 1e-10) {
            return {0.0, 0.0};
        }
        return {x / len, y / len};
    }

    // 就地单位化
    void normalize() {
        double len = length();
        if (len > 1e-10) {
            x /= len;
            y /= len;
        } else {
            x = 0.0;
            y = 0.0;
        }
    }

    // 计算到另一个点的距离
    double distance_to(const Vector2D& other) const {
        return (*this - other).length();
    }

    // 计算到另一个点的距离的平方
    double distance_squared_to(const Vector2D& other) const {
        return (*this - other).length_squared();
    }

    // 旋转向量（弧度）
    Vector2D rotated(double angle) const {
        double cos_a = std::cos(angle);
        double sin_a = std::sin(angle);
        return {
            x * cos_a - y * sin_a,
            x * sin_a + y * cos_a
        };
    }

    // 计算向量的角度（弧度）
    double angle() const {
        return std::atan2(y, x);
    }

    // 两个向量之间的角度
    double angle_to(const Vector2D& other) const {
        return std::atan2(cross(other), dot(other));
    }

    // 投影到另一个向量上
    Vector2D project_onto(const Vector2D& other) const {
        double other_len_sq = other.length_squared();
        if (other_len_sq < 1e-10) {
            return {0.0, 0.0};
        }
        return other * (dot(other) / other_len_sq);
    }

    // 反射向量（关于法线）
    Vector2D reflect(const Vector2D& normal) const {
        return *this - normal * (2.0 * dot(normal));
    }

    // 线性插值
    static Vector2D lerp(const Vector2D& a, const Vector2D& b, double t) {
        return a + (b - a) * t;
    }

    // 输出流运算符
    friend std::ostream& operator<<(std::ostream& os, const Vector2D& v) {
        os << "(" << v.x << ", " << v.y << ")";
        return os;
    }
};

// 标量 * 向量
inline Vector2D operator*(double scalar, const Vector2D& v) {
    return v * scalar;
}

} // namespace physics_engine
