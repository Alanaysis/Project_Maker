#pragma once

// 标准库
#include <iostream>
#include <string>
#include <vector>
#include <array>
#include <memory>
#include <functional>
#include <algorithm>
#include <cmath>
#include <cassert>
#include <chrono>
#include <fstream>
#include <sstream>
#include <map>
#include <unordered_map>
#include <set>
#include <optional>
#include <variant>
#include <stdexcept>

// OpenGL
#define GLEW_STATIC
#include <GL/glew.h>
#include <GLFW/glfw3.h>

// GLM 数学库
#define GLM_FORCE_RADIANS
#define GLM_FORCE_DEPTH_ZERO_TO_ONE
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtx/quaternion.hpp>
#include <glm/gtx/string_cast.hpp>

// OpenXR（可选）
#ifdef USE_OPENXR
#include <openxr/openxr.h>
#include <openxr/openxr_platform.h>
#endif

// 命名空间别名
namespace vr {

// 数学类型
using Vec2 = glm::vec2;
using Vec3 = glm::vec3;
using Vec4 = glm::vec4;
using Mat3 = glm::mat3;
using Mat4 = glm::mat4;
using Quat = glm::quat;

// 常量
constexpr float PI = glm::pi<float>();
constexpr float TWO_PI = glm::two_pi<float>();
constexpr float HALF_PI = glm::half_pi<float>();
constexpr float DEG_TO_RAD = PI / 180.0f;
constexpr float RAD_TO_DEG = 180.0f / PI;

// VR 常量
constexpr int TARGET_FPS = 90;
constexpr float TARGET_FRAME_TIME = 1000.0f / TARGET_FPS;  // 毫秒
constexpr float NEAR_CLIP = 0.1f;
constexpr float FAR_CLIP = 1000.0f;
constexpr float DEFAULT_IPD = 0.064f;  // 64mm

// 颜色常量
namespace Colors {
    constexpr Vec4 White = {1.0f, 1.0f, 1.0f, 1.0f};
    constexpr Vec4 Black = {0.0f, 0.0f, 0.0f, 1.0f};
    constexpr Vec4 Red = {1.0f, 0.0f, 0.0f, 1.0f};
    constexpr Vec4 Green = {0.0f, 1.0f, 0.0f, 1.0f};
    constexpr Vec4 Blue = {0.0f, 0.0f, 1.0f, 1.0f};
    constexpr Vec4 Yellow = {1.0f, 1.0f, 0.0f, 1.0f};
    constexpr Vec4 Cyan = {0.0f, 1.0f, 1.0f, 1.0f};
    constexpr Vec4 Magenta = {1.0f, 0.0f, 1.0f, 1.0f};
    constexpr Vec4 Gray = {0.5f, 0.5f, 0.5f, 1.0f};
    constexpr Vec4 DarkGray = {0.25f, 0.25f, 0.25f, 1.0f};
    constexpr Vec4 LightGray = {0.75f, 0.75f, 0.75f, 1.0f};
}  // namespace Colors

// 错误码
enum class ErrorCode {
    Success = 0,
    VRInitFailed,
    OpenGLInitFailed,
    WindowInitFailed,
    ShaderCompileError,
    ShaderLinkError,
    TextureLoadError,
    ModelLoadError,
    SessionLost,
    TrackingLost,
    ControllerDisconnected,
    FileNotFound,
    InvalidParameter,
    OutOfMemory,
    UnknownError
};

// 日志级别
enum class LogLevel {
    Debug,
    Info,
    Warning,
    Error,
    Fatal
};

// VR 设备类型
enum class VRDeviceType {
    None,
    Desktop,        // 桌面模拟模式
    Oculus,
    SteamVR,
    WMR,            // Windows Mixed Reality
    Other
};

// 眼睛类型
enum class Eye {
    Left = 0,
    Right = 1,
    Count = 2
};

// 交互动作
enum class Action {
    Grab,
    Release,
    Trigger,
    ButtonA,
    ButtonB,
    Thumbstick,
    Menu
};

// 日志宏
#define VR_LOG(level, msg) \
    vr::Logger::GetInstance().Log(level, __FILE__, __LINE__, msg)

#define VR_DEBUG(msg) VR_LOG(vr::LogLevel::Debug, msg)
#define VR_INFO(msg) VR_LOG(vr::LogLevel::Info, msg)
#define VR_WARNING(msg) VR_LOG(vr::LogLevel::Warning, msg)
#define VR_ERROR(msg) VR_LOG(vr::LogLevel::Error, msg)
#define VR_FATAL(msg) VR_LOG(vr::LogLevel::Fatal, msg)

// 断言宏
#ifdef DEBUG
#define VR_ASSERT(x) assert(x)
#else
#define VR_ASSERT(x) ((void)(x))
#endif

// 工具函数
namespace Utils {

// 角度转换
inline float DegreesToRadians(float degrees) {
    return degrees * DEG_TO_RAD;
}

inline float RadiansToDegrees(float radians) {
    return radians * RAD_TO_DEG;
}

// 限制范围
template<typename T>
T Clamp(T value, T min, T max) {
    return (value < min) ? min : (value > max) ? max : value;
}

// 线性插值
template<typename T>
T Lerp(const T& a, const T& b, float t) {
    return a + t * (b - a);
}

// 平滑插值
template<typename T>
T SmoothStep(const T& edge0, const T& edge1, float x) {
    float t = Clamp((x - edge0) / (edge1 - edge0), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}

// 检查浮点数是否近似相等
inline bool Approximately(float a, float b, float epsilon = 1e-6f) {
    return std::abs(a - b) < epsilon;
}

// 安全除法
inline float SafeDivide(float a, float b, float defaultValue = 0.0f) {
    return (std::abs(b) > 1e-6f) ? (a / b) : defaultValue;
}

}  // namespace Utils

// 前向声明
class Application;
class Engine;
class Renderer;
class VRSystem;
class InputManager;
class SceneManager;
class Camera;
class Shader;
class Texture;
class Mesh;
class Material;
class Transform;
class Scene;
class SceneObject;
class Logger;

// 智能指针别名
template<typename T>
using UniquePtr = std::unique_ptr<T>;

template<typename T>
using SharedPtr = std::shared_ptr<T>;

template<typename T>
using WeakPtr = std::weak_ptr<T>;

}  // namespace vr