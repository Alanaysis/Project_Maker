#pragma once

// 物理引擎主头文件
// 包含所有核心组件

#include "vector2d.h"
#include "aabb.h"
#include "rigid_body.h"
#include "collision.h"
#include "constraint.h"
#include "world.h"

namespace physics_engine {

// 版本信息
constexpr int VERSION_MAJOR = 1;
constexpr int VERSION_MINOR = 0;
constexpr int VERSION_PATCH = 0;

// 获取版本字符串
inline const char* get_version() {
    return "1.0.0";
}

} // namespace physics_engine
