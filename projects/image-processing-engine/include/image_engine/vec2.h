#pragma once

#include <cmath>

namespace image_engine {

struct Vec2 {
    float x = 0.0f;
    float y = 0.0f;

    Vec2(float x_ = 0.0f, float y_ = 0.0f) : x(x_), y(y_) {}

    Vec2 operator+(const Vec2& other) const {
        return Vec2(x + other.x, y + other.y);
    }

    Vec2 operator-(const Vec2& other) const {
        return Vec2(x - other.x, y - other.y);
    }

    Vec2 operator*(float s) const {
        return Vec2(x * s, y * s);
    }

    float length() const {
        return sqrtf(x * x + y * y);
    }

    Vec2 normalized() const {
        float len = length();
        if (len > 0.0f) return Vec2(x / len, y / len);
        return Vec2(0.0f, 0.0f);
    }
};

} // namespace image_engine
