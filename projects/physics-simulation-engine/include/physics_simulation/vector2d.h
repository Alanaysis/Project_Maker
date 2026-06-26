#pragma once

#include <cmath>
#include <cstdint>

namespace physics_simulation {

struct Vec2 {
    double x;
    double y;

    Vec2() : x(0.0), y(0.0) {}
    Vec2(double x, double y) : x(x), y(y) {}

    Vec2 operator+(const Vec2& other) const { return {x + other.x, y + other.y}; }
    Vec2 operator+(double scalar) const { return {x + scalar, y + scalar}; }
    Vec2 operator-(const Vec2& other) const { return {x - other.x, y - other.y}; }
    Vec2 operator-(double scalar) const { return {x - scalar, y - scalar}; }
    Vec2 operator*(double scalar) const { return {x * scalar, y * scalar}; }
    Vec2 operator/(double scalar) const { return {x / scalar, y / scalar}; }
    Vec2 operator-() const { return {-x, -y}; }

    Vec2& operator+=(const Vec2& other) { x += other.x; y += other.y; return *this; }
    Vec2& operator-=(const Vec2& other) { x -= other.x; y -= other.y; return *this; }
    Vec2& operator*=(double scalar) { x *= scalar; y *= scalar; return *this; }
    Vec2& operator/=(double scalar) { x /= scalar; y /= scalar; return *this; }

    double dot(const Vec2& other) const { return x * other.x + y * other.y; }
    double cross(const Vec2& other) const { return x * other.y - y * other.x; }
    double length() const { return std::sqrt(x * x + y * y); }
    double length_squared() const { return x * x + y * y; }

    Vec2 normalized() const {
        double len = length();
        if (len > 1e-10) return *this / len;
        return {1.0, 0.0};
    }

    static Vec2 zero() { return {0.0, 0.0}; }
    static Vec2 unit_x() { return {1.0, 0.0}; }
    static Vec2 unit_y() { return {0.0, 1.0}; }
};

} // namespace physics_simulation
