#include "3d_engine/3d_engine.h"
#include <iostream>
#include <cassert>

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Cube creation
    {
        auto cube = engine3d::create_cube(2.0f);
        assert(cube.vertex_count() == 8);
        assert(cube.face_count() == 12);
        passed++;
    }
    total++;
    std::cout << "test_cube: PASS" << std::endl;

    // Test 2: Sphere creation
    {
        auto sphere = engine3d::create_sphere(16, 8);
        assert(sphere.vertex_count() > 0);
        assert(sphere.face_count() > 0);
        passed++;
    }
    total++;
    std::cout << "test_sphere: PASS" << std::endl;

    // Test 3: Cylinder creation
    {
        auto cyl = engine3d::create_cylinder(0.5f, 1.0f, 16);
        assert(cyl.vertex_count() > 0);
        assert(cyl.face_count() > 0);
        passed++;
    }
    total++;
    std::cout << "test_cylinder: PASS" << std::endl;

    // Test 4: Cone creation
    {
        auto cone = engine3d::create_cone(0.5f, 1.0f, 16);
        assert(cone.vertex_count() > 0);
        assert(cone.face_count() > 0);
        passed++;
    }
    total++;
    std::cout << "test_cone: PASS" << std::endl;

    // Test 5: Torus creation
    {
        auto torus = engine3d::create_torus(0.5f, 0.2f, 24, 12);
        assert(torus.vertex_count() > 0);
        assert(torus.face_count() > 0);
        passed++;
    }
    total++;
    std::cout << "test_torus: PASS" << std::endl;

    // Test 6: Mesh name
    {
        auto cube = engine3d::create_cube();
        assert(cube.name == "cube");
        passed++;
    }
    total++;
    std::cout << "test_mesh_name: PASS" << std::endl;

    // Test 7: Face normal computation
    {
        auto cube = engine3d::create_cube(2.0f);
        bool has_valid_normal = false;
        for (const auto& f : cube.faces) {
            float len = f.normal.length();
            if (len > 0.9f && len < 1.1f) {
                has_valid_normal = true;
                break;
            }
        }
        assert(has_valid_normal);
        passed++;
    }
    total++;
    std::cout << "test_face_normal: PASS" << std::endl;

    // Test 8: Vertex count for sphere
    {
        auto sphere = engine3d::create_sphere(8, 4);
        assert(sphere.vertex_count() == (8 + 1) * (4 + 1));
        passed++;
    }
    total++;
    std::cout << "test_sphere_verts: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
