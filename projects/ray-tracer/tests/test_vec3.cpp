#include "../include/vec3.h"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace rt;

void test_constructor() {
    Vec3 v1;
    assert(v1.x == 0 && v1.y == 0 && v1.z == 0);

    Vec3 v2(1.0, 2.0, 3.0);
    assert(v2.x == 1.0 && v2.y == 2.0 && v2.z == 3.0);

    std::cout << "  [PASS] Constructor" << std::endl;
}

void test_addition() {
    Vec3 v1(1.0, 2.0, 3.0);
    Vec3 v2(4.0, 5.0, 6.0);
    Vec3 v3 = v1 + v2;

    assert(std::abs(v3.x - 5.0) < 1e-10);
    assert(std::abs(v3.y - 7.0) < 1e-10);
    assert(std::abs(v3.z - 9.0) < 1e-10);

    std::cout << "  [PASS] Addition" << std::endl;
}

void test_subtraction() {
    Vec3 v1(4.0, 5.0, 6.0);
    Vec3 v2(1.0, 2.0, 3.0);
    Vec3 v3 = v1 - v2;

    assert(std::abs(v3.x - 3.0) < 1e-10);
    assert(std::abs(v3.y - 3.0) < 1e-10);
    assert(std::abs(v3.z - 3.0) < 1e-10);

    std::cout << "  [PASS] Subtraction" << std::endl;
}

void test_scalar_multiplication() {
    Vec3 v1(1.0, 2.0, 3.0);
    Vec3 v2 = v1 * 2.0;

    assert(std::abs(v2.x - 2.0) < 1e-10);
    assert(std::abs(v2.y - 4.0) < 1e-10);
    assert(std::abs(v2.z - 6.0) < 1e-10);

    // 标量 * 向量
    Vec3 v3 = 3.0 * v1;
    assert(std::abs(v3.x - 3.0) < 1e-10);
    assert(std::abs(v3.y - 6.0) < 1e-10);
    assert(std::abs(v3.z - 9.0) < 1e-10);

    std::cout << "  [PASS] Scalar Multiplication" << std::endl;
}

void test_dot_product() {
    Vec3 v1(1.0, 2.0, 3.0);
    Vec3 v2(4.0, 5.0, 6.0);

    double result = v1.dot(v2);
    assert(std::abs(result - 32.0) < 1e-10);

    // 函数形式
    double result2 = dot(v1, v2);
    assert(std::abs(result2 - 32.0) < 1e-10);

    std::cout << "  [PASS] Dot Product" << std::endl;
}

void test_cross_product() {
    Vec3 v1(1.0, 0.0, 0.0);
    Vec3 v2(0.0, 1.0, 0.0);
    Vec3 v3 = v1.cross(v2);

    assert(std::abs(v3.x - 0.0) < 1e-10);
    assert(std::abs(v3.y - 0.0) < 1e-10);
    assert(std::abs(v3.z - 1.0) < 1e-10);

    std::cout << "  [PASS] Cross Product" << std::endl;
}

void test_length() {
    Vec3 v1(3.0, 4.0, 0.0);

    assert(std::abs(v1.length() - 5.0) < 1e-10);
    assert(std::abs(v1.length_squared() - 25.0) < 1e-10);

    std::cout << "  [PASS] Length" << std::endl;
}

void test_normalize() {
    Vec3 v1(3.0, 4.0, 0.0);
    Vec3 v2 = v1.normalize();

    assert(std::abs(v2.length() - 1.0) < 1e-10);
    assert(std::abs(v2.x - 0.6) < 1e-10);
    assert(std::abs(v2.y - 0.8) < 1e-10);

    // 零向量
    Vec3 v3(0, 0, 0);
    Vec3 v4 = v3.normalize();
    assert(v4.x == 0 && v4.y == 0 && v4.z == 0);

    std::cout << "  [PASS] Normalize" << std::endl;
}

void test_reflect() {
    Vec3 v(1.0, -1.0, 0.0);
    Vec3 normal(0.0, 1.0, 0.0);
    Vec3 reflected = v.reflect(normal);

    assert(std::abs(reflected.x - 1.0) < 1e-10);
    assert(std::abs(reflected.y - 1.0) < 1e-10);
    assert(std::abs(reflected.z - 0.0) < 1e-10);

    std::cout << "  [PASS] Reflect" << std::endl;
}

int main() {
    std::cout << "Running Vec3 tests..." << std::endl;

    test_constructor();
    test_addition();
    test_subtraction();
    test_scalar_multiplication();
    test_dot_product();
    test_cross_product();
    test_length();
    test_normalize();
    test_reflect();

    std::cout << "All Vec3 tests passed!" << std::endl;
    return 0;
}
