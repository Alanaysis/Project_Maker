#include "3d_engine/3d_engine.h"
#include <iostream>

int main() {
    std::cout << "=== 3D 建模引擎演示 ===" << std::endl;

    // Create primitives
    auto cube = engine3d::create_cube(2.0f);
    std::cout << cube.to_string();

    auto sphere = engine3d::create_sphere(12, 8);
    std::cout << sphere.to_string();

    auto cylinder = engine3d::create_cylinder(0.5f, 2.0f, 16);
    std::cout << cylinder.to_string();

    auto cone = engine3d::create_cone(0.5f, 2.0f, 16);
    std::cout << cone.to_string();

    auto torus = engine3d::create_torus(0.8f, 0.3f, 24, 12);
    std::cout << torus.to_string();

    // Transform cube
    auto rotated = engine3d::Transform::rotate_y(cube, 0.785f); // 45 degrees
    auto translated = engine3d::Transform::translate(rotated, 0.0f, 0.0f, 0.0f);

    std::cout << "\n旋转后的立方体顶点 (前 3 个):\n";
    for (int i = 0; i < 3 && i < static_cast<int>(translated.vertices.size()); i++) {
        std::cout << "  V" << i << ": " << translated.vertices[i].position << std::endl;
    }

    std::cout << "\n所有模型创建完成!" << std::endl;
    return 0;
}
