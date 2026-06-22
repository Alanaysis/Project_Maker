#include <iostream>
#include <cassert>
#include <cmath>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtx/quaternion.hpp>

// 测试宏
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            std::cerr << "FAILED: " << message << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
            return false; \
        } \
    } while(0)

#define TEST_ASSERT_APPROX(a, b, epsilon) \
    TEST_ASSERT(std::abs((a) - (b)) < (epsilon), \
                "Expected " << (a) << " ≈ " << (b) << " (epsilon=" << (epsilon) << ")")

#define RUN_TEST(test_func) \
    do { \
        std::cout << "Running " << #test_func << "... "; \
        if (test_func()) { \
            std::cout << "PASSED" << std::endl; \
            passed++; \
        } else { \
            std::cout << "FAILED" << std::endl; \
            failed++; \
        } \
        total++; \
    } while(0)

using Vec2 = glm::vec2;
using Vec3 = glm::vec3;
using Vec4 = glm::vec4;
using Mat3 = glm::mat3;
using Mat4 = glm::mat4;
using Quat = glm::quat;

// 向量测试
bool TestVectorOperations() {
    Vec3 a(1.0f, 2.0f, 3.0f);
    Vec3 b(4.0f, 5.0f, 6.0f);

    // 加法
    Vec3 c = a + b;
    TEST_ASSERT_APPROX(c.x, 5.0f, 0.001f);
    TEST_ASSERT_APPROX(c.y, 7.0f, 0.001f);
    TEST_ASSERT_APPROX(c.z, 9.0f, 0.001f);

    // 减法
    Vec3 d = b - a;
    TEST_ASSERT_APPROX(d.x, 3.0f, 0.001f);
    TEST_ASSERT_APPROX(d.y, 3.0f, 0.001f);
    TEST_ASSERT_APPROX(d.z, 3.0f, 0.001f);

    // 标量乘法
    Vec3 e = a * 2.0f;
    TEST_ASSERT_APPROX(e.x, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(e.y, 4.0f, 0.001f);
    TEST_ASSERT_APPROX(e.z, 6.0f, 0.001f);

    // 点积
    float dot = glm::dot(a, b);
    TEST_ASSERT_APPROX(dot, 32.0f, 0.001f);  // 1*4 + 2*5 + 3*6 = 32

    // 叉积
    Vec3 cross = glm::cross(a, b);
    TEST_ASSERT_APPROX(cross.x, -3.0f, 0.001f);  // 2*6 - 3*5 = -3
    TEST_ASSERT_APPROX(cross.y, 6.0f, 0.001f);   // 3*4 - 1*6 = 6
    TEST_ASSERT_APPROX(cross.z, -3.0f, 0.001f);  // 1*5 - 2*4 = -3

    // 长度
    float length = glm::length(a);
    TEST_ASSERT_APPROX(length, std::sqrt(14.0f), 0.001f);  // sqrt(1+4+9) = sqrt(14)

    // 归一化
    Vec3 normalized = glm::normalize(a);
    float normLength = glm::length(normalized);
    TEST_ASSERT_APPROX(normLength, 1.0f, 0.001f);

    return true;
}

// 矩阵测试
bool TestMatrixOperations() {
    // 单位矩阵
    Mat4 identity = Mat4(1.0f);
    Vec4 v(1.0f, 2.0f, 3.0f, 1.0f);
    Vec4 result = identity * v;
    TEST_ASSERT_APPROX(result.x, 1.0f, 0.001f);
    TEST_ASSERT_APPROX(result.y, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(result.z, 3.0f, 0.001f);
    TEST_ASSERT_APPROX(result.w, 1.0f, 0.001f);

    // 平移矩阵
    Mat4 translation = glm::translate(Mat4(1.0f), Vec3(1.0f, 2.0f, 3.0f));
    Vec4 translated = translation * Vec4(0.0f, 0.0f, 0.0f, 1.0f);
    TEST_ASSERT_APPROX(translated.x, 1.0f, 0.001f);
    TEST_ASSERT_APPROX(translated.y, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(translated.z, 3.0f, 0.001f);

    // 缩放矩阵
    Mat4 scale = glm::scale(Mat4(1.0f), Vec3(2.0f, 3.0f, 4.0f));
    Vec4 scaled = scale * Vec4(1.0f, 1.0f, 1.0f, 1.0f);
    TEST_ASSERT_APPROX(scaled.x, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(scaled.y, 3.0f, 0.001f);
    TEST_ASSERT_APPROX(scaled.z, 4.0f, 0.001f);

    // 旋转矩阵（绕 Y 轴旋转 90 度）
    Mat4 rotation = glm::rotate(Mat4(1.0f), glm::radians(90.0f), Vec3(0.0f, 1.0f, 0.0f));
    Vec4 rotated = rotation * Vec4(1.0f, 0.0f, 0.0f, 1.0f);
    TEST_ASSERT_APPROX(rotated.x, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(rotated.z, -1.0f, 0.01f);

    // 矩阵乘法
    Mat4 combined = translation * rotation;
    Vec4 combinedResult = combined * Vec4(1.0f, 0.0f, 0.0f, 1.0f);
    TEST_ASSERT_APPROX(combinedResult.x, 1.0f, 0.01f);   // 平移 x
    TEST_ASSERT_APPROX(combinedResult.z, 2.0f, 0.01f);   // 旋转后 + 平移 z

    return true;
}

// 四元数测试
bool TestQuaternionOperations() {
    // 创建四元数
    Quat q = glm::angleAxis(glm::radians(90.0f), Vec3(0.0f, 1.0f, 0.0f));

    // 旋转向量
    Vec3 v(1.0f, 0.0f, 0.0f);
    Vec3 rotated = glm::rotate(q, v);
    TEST_ASSERT_APPROX(rotated.x, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(rotated.z, -1.0f, 0.01f);

    // 四元数乘法
    Quat q1 = glm::angleAxis(glm::radians(45.0f), Vec3(0.0f, 1.0f, 0.0f));
    Quat q2 = glm::angleAxis(glm::radians(45.0f), Vec3(0.0f, 1.0f, 0.0f));
    Quat q3 = q2 * q1;

    Vec3 rotated2 = glm::rotate(q3, Vec3(1.0f, 0.0f, 0.0f));
    TEST_ASSERT_APPROX(rotated2.x, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(rotated2.z, -1.0f, 0.01f);

    // 四元数归一化
    Quat qNorm = glm::normalize(q);
    float length = glm::length(qNorm);
    TEST_ASSERT_APPROX(length, 1.0f, 0.001f);

    // 球面插值
    Quat qStart = glm::angleAxis(0.0f, Vec3(0.0f, 1.0f, 0.0f));
    Quat qEnd = glm::angleAxis(glm::radians(90.0f), Vec3(0.0f, 1.0f, 0.0f));
    Quat qMid = glm::slerp(qStart, qEnd, 0.5f);

    Vec3 rotatedMid = glm::rotate(qMid, Vec3(1.0f, 0.0f, 0.0f));
    TEST_ASSERT_APPROX(rotatedMid.x, std::cos(glm::radians(45.0f)), 0.01f);
    TEST_ASSERT_APPROX(rotatedMid.z, -std::sin(glm::radians(45.0f)), 0.01f);

    return true;
}

// 变换组合测试
bool TestTransformComposition() {
    // 创建变换：先缩放，再旋转，最后平移
    Mat4 scale = glm::scale(Mat4(1.0f), Vec3(2.0f));
    Mat4 rotation = glm::rotate(Mat4(1.0f), glm::radians(45.0f), Vec3(0.0f, 1.0f, 0.0f));
    Mat4 translation = glm::translate(Mat4(1.0f), Vec3(1.0f, 0.0f, 0.0f));

    // 组合变换（注意顺序：T * R * S）
    Mat4 transform = translation * rotation * scale;

    // 测试原点
    Vec4 origin(0.0f, 0.0f, 0.0f, 1.0f);
    Vec4 transformedOrigin = transform * origin;
    TEST_ASSERT_APPROX(transformedOrigin.x, 1.0f, 0.001f);  // 只有平移
    TEST_ASSERT_APPROX(transformedOrigin.y, 0.0f, 0.001f);

    // 测试单位向量
    Vec4 unitX(1.0f, 0.0f, 0.0f, 1.0f);
    Vec4 transformedUnitX = transform * unitX;

    // 预期：缩放 2 倍，旋转 45 度，平移 1
    float expectedX = 1.0f + 2.0f * std::cos(glm::radians(45.0f));
    float expectedZ = -2.0f * std::sin(glm::radians(45.0f));
    TEST_ASSERT_APPROX(transformedUnitX.x, expectedX, 0.01f);
    TEST_ASSERT_APPROX(transformedUnitX.z, expectedZ, 0.01f);

    return true;
}

// 投影矩阵测试
bool TestProjectionMatrix() {
    // 透视投影
    float fov = 45.0f;
    float aspect = 16.0f / 9.0f;
    float near = 0.1f;
    float far = 100.0f;

    Mat4 perspective = glm::perspective(glm::radians(fov), aspect, near, far);

    // 测试近平面上的点
    Vec4 nearPoint(0.0f, 0.0f, -near, 1.0f);
    Vec4 projectedNear = perspective * nearPoint;
    float ndcZ = projectedNear.z / projectedNear.w;
    TEST_ASSERT_APPROX(ndcZ, -1.0f, 0.01f);  // OpenGL 近平面映射到 -1

    // 测试远平面上的点
    Vec4 farPoint(0.0f, 0.0f, -far, 1.0f);
    Vec4 projectedFar = perspective * farPoint;
    float ndcZFar = projectedFar.z / projectedFar.w;
    TEST_ASSERT_APPROX(ndcZFar, 1.0f, 0.01f);  // 远平面映射到 1

    // 正交投影
    Mat4 ortho = glm::ortho(-1.0f, 1.0f, -1.0f, 1.0f, near, far);

    Vec4 orthoPoint(0.5f, 0.5f, -50.0f, 1.0f);
    Vec4 projectedOrtho = ortho * orthoPoint;
    TEST_ASSERT_APPROX(projectedOrtho.x / projectedOrtho.w, 0.5f, 0.01f);
    TEST_ASSERT_APPROX(projectedOrtho.y / projectedOrtho.w, 0.5f, 0.01f);

    return true;
}

// 视图矩阵测试
bool TestViewMatrix() {
    Vec3 eye(0.0f, 0.0f, 5.0f);
    Vec3 center(0.0f, 0.0f, 0.0f);
    Vec3 up(0.0f, 1.0f, 0.0f);

    Mat4 view = glm::lookAt(eye, center, up);

    // 测试原点在视图空间中的位置
    Vec4 worldOrigin(0.0f, 0.0f, 0.0f, 1.0f);
    Vec4 viewOrigin = view * worldOrigin;
    TEST_ASSERT_APPROX(viewOrigin.z, -5.0f, 0.01f);  // 原点在相机前方 5 个单位

    // 测试相机位置
    Vec4 viewEye = view * Vec4(eye, 1.0f);
    TEST_ASSERT_APPROX(viewEye.x, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(viewEye.y, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(viewEye.z, 0.0f, 0.01f);

    return true;
}

// 插值测试
bool TestInterpolation() {
    // 线性插值
    Vec3 a(0.0f, 0.0f, 0.0f);
    Vec3 b(10.0f, 10.0f, 10.0f);
    Vec3 mid = glm::mix(a, b, 0.5f);
    TEST_ASSERT_APPROX(mid.x, 5.0f, 0.001f);
    TEST_ASSERT_APPROX(mid.y, 5.0f, 0.001f);
    TEST_ASSERT_APPROX(mid.z, 5.0f, 0.001f);

    // 球面插值
    Quat q1 = glm::angleAxis(0.0f, Vec3(0.0f, 1.0f, 0.0f));
    Quat q2 = glm::angleAxis(glm::radians(90.0f), Vec3(0.0f, 1.0f, 0.0f));
    Quat qMid = glm::slerp(q1, q2, 0.5f);

    Vec3 v(1.0f, 0.0f, 0.0f);
    Vec3 rotated = glm::rotate(qMid, v);
    float angle = std::acos(glm::dot(glm::normalize(rotated), Vec3(1.0f, 0.0f, 0.0f)));
    TEST_ASSERT_APPROX(angle, glm::radians(45.0f), 0.01f);

    return true;
}

int main() {
    std::cout << "=== VR Application Math Tests ===" << std::endl;
    std::cout << std::endl;

    int passed = 0;
    int failed = 0;
    int total = 0;

    RUN_TEST(TestVectorOperations);
    RUN_TEST(TestMatrixOperations);
    RUN_TEST(TestQuaternionOperations);
    RUN_TEST(TestTransformComposition);
    RUN_TEST(TestProjectionMatrix);
    RUN_TEST(TestViewMatrix);
    RUN_TEST(TestInterpolation);

    std::cout << std::endl;
    std::cout << "=== Results ===" << std::endl;
    std::cout << "Passed: " << passed << "/" << total << std::endl;

    if (failed > 0) {
        std::cout << "Failed: " << failed << "/" << total << std::endl;
        return 1;
    }

    std::cout << "All tests passed!" << std::endl;
    return 0;
}