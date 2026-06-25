#include "3d_engine/vec3.h"
#include <iostream>
#include <cassert>
#include <cmath>

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Vec3 construction
    {
        engine3d::Vec3 v(1.0f, 2.0f, 3.0f);
        assert(v.x == 1.0f);
        assert(v.y == 2.0f);
        assert(v.z == 3.0f);
        passed++;
    }
    total++;
    std::cout << "test_vec3_construct: PASS" << std::endl;

    // Test 2: Vec3 addition
    {
        engine3d::Vec3 a(1.0f, 2.0f, 3.0f);
        engine3d::Vec3 b(4.0f, 5.0f, 6.0f);
        auto c = a + b;
        assert(c.x == 5.0f);
        assert(c.y == 7.0f);
        assert(c.z == 9.0f);
        passed++;
    }
    total++;
    std::cout << "test_vec3_add: PASS" << std::endl;

    // Test 3: Vec3 subtraction
    {
        engine3d::Vec3 a(4.0f, 5.0f, 6.0f);
        engine3d::Vec3 b(1.0f, 2.0f, 3.0f);
        auto c = a - b;
        assert(c.x == 3.0f);
        assert(c.y == 3.0f);
        assert(c.z == 3.0f);
        passed++;
    }
    total++;
    std::cout << "test_vec3_sub: PASS" << std::endl;

    // Test 4: Vec3 scalar multiplication
    {
        engine3d::Vec3 v(1.0f, 2.0f, 3.0f);
        auto c = v * 2.0f;
        assert(c.x == 2.0f);
        assert(c.y == 4.0f);
        assert(c.z == 6.0f);
        passed++;
    }
    total++;
    std::cout << "test_vec3_scale: PASS" << std::endl;

    // Test 5: Dot product
    {
        engine3d::Vec3 a(1.0f, 0.0f, 0.0f);
        engine3d::Vec3 b(0.0f, 1.0f, 0.0f);
        assert(a.dot(b) == 0.0f);
        passed++;
    }
    total++;
    std::cout << "test_dot_product: PASS" << std::endl;

    // Test 6: Cross product
    {
        engine3d::Vec3 a(1.0f, 0.0f, 0.0f);
        engine3d::Vec3 b(0.0f, 1.0f, 0.0f);
        auto c = a.cross(b);
        assert(c.x == 0.0f);
        assert(c.y == 0.0f);
        assert(c.z == 1.0f);
        passed++;
    }
    total++;
    std::cout << "test_cross_product: PASS" << std::endl;

    // Test 7: Normalization
    {
        engine3d::Vec3 v(3.0f, 4.0f, 0.0f);
        auto n = v.normalized();
        assert(std::abs(n.length() - 1.0f) < 0.01f);
        passed++;
    }
    total++;
    std::cout << "test_normalized: PASS" << std::endl;

    // Test 8: Distance
    {
        engine3d::Vec3 a(0.0f, 0.0f, 0.0f);
        engine3d::Vec3 b(3.0f, 4.0f, 0.0f);
        assert(std::abs(a.distance_to(b) - 5.0f) < 0.01f);
        passed++;
    }
    total++;
    std::cout << "test_distance: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
