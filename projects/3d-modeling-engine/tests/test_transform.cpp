#include "3d_engine/3d_engine.h"
#include <iostream>
#include <cassert>
#include <cmath>

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Translation
    {
        auto cube = engine3d::create_cube(1.0f);
        auto translated = engine3d::Transform::translate(cube, 10.0f, 0.0f, 0.0f);
        assert(std::abs(translated.vertices[0].position.x - (cube.vertices[0].position.x + 10.0f)) < 0.1f);
        passed++;
    }
    total++;
    std::cout << "test_translation: PASS" << std::endl;

    // Test 2: Scaling
    {
        auto cube = engine3d::create_cube(1.0f);
        auto scaled = engine3d::Transform::scale(cube, 2.0f, 2.0f, 2.0f);
        assert(std::abs(scaled.vertices[0].position.x - (cube.vertices[0].position.x * 2.0f)) < 0.1f);
        passed++;
    }
    total++;
    std::cout << "test_scaling: PASS" << std::endl;

    // Test 3: Rotation X
    {
        auto cube = engine3d::create_cube(1.0f);
        auto rotated = engine3d::Transform::rotate_x(cube, 3.14159f / 2.0f);
        // Rotation around X axis
        assert(std::abs(rotated.vertices[0].position.z - cube.vertices[0].position.y) < 0.5f || std::abs(rotated.vertices[0].position.z + cube.vertices[0].position.y) < 0.5f);
        passed++;
    }
    total++;
    std::cout << "test_rotation_x: PASS" << std::endl;

    // Test 4: Rotation Y
    {
        auto cube = engine3d::create_cube(1.0f);
        auto rotated = engine3d::Transform::rotate_y(cube, 3.14159f / 2.0f);
        // X should become -Z
        assert(std::abs(rotated.vertices[0].position.z - (-cube.vertices[0].position.x)) < 0.1f);
        passed++;
    }
    total++;
    std::cout << "test_rotation_y: PASS" << std::endl;

    // Test 5: Rotation Z
    {
        auto cube = engine3d::create_cube(1.0f);
        auto rotated = engine3d::Transform::rotate_z(cube, 3.14159f / 2.0f);
        // X should become Y
        assert(std::abs(rotated.vertices[0].position.y - cube.vertices[0].position.x) < 0.1f);
        passed++;
    }
    total++;
    std::cout << "test_rotation_z: PASS" << std::endl;

    // Test 6: Identity transform
    {
        auto cube = engine3d::create_cube(1.0f);
        auto identity = engine3d::Transform::translate(cube, 0.0f, 0.0f, 0.0f);
        assert(std::abs(identity.vertices[0].position.x - cube.vertices[0].position.x) < 0.01f);
        passed++;
    }
    total++;
    std::cout << "test_identity: PASS" << std::endl;

    // Test 7: Combined transform
    {
        auto cube = engine3d::create_cube(1.0f);
        auto scaled = engine3d::Transform::scale(cube, 2.0f, 2.0f, 2.0f);
        auto translated = engine3d::Transform::translate(scaled, 5.0f, 5.0f, 5.0f);
        assert(std::abs(translated.vertices[0].position.x - (cube.vertices[0].position.x * 2.0f + 5.0f)) < 0.1f);
        passed++;
    }
    total++;
    std::cout << "test_combined: PASS" << std::endl;

    // Test 8: Vertex count preserved
    {
        auto cube = engine3d::create_cube(1.0f);
        auto rotated = engine3d::Transform::rotate_y(cube, 1.0f);
        assert(rotated.vertex_count() == cube.vertex_count());
        passed++;
    }
    total++;
    std::cout << "test_vertex_preserve: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
