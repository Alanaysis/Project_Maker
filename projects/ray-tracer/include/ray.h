#pragma once

#include "vec3.h"

namespace rt {

// 光线表示：P(t) = origin + t * direction
class Ray {
public:
    Vec3 origin;    // 光线起点
    Vec3 direction; // 光线方向（单位向量）

    Ray() {}
    Ray(const Vec3& origin, const Vec3& direction)
        : origin(origin), direction(direction.normalize()) {}

    // 计算光线上某点
    Vec3 at(double t) const {
        return origin + direction * t;
    }
};

} // namespace rt
