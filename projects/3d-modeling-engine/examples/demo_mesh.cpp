#include "3d_engine/3d_engine.h"
#include <iostream>

int main() {
    std::cout << "=== 3D 基本模型演示 ===" << std::endl;

    // Create all primitives
    auto cube = engine3d::create_cube(2.0f);
    auto sphere = engine3d::create_sphere(12, 8);
    auto cylinder = engine3d::create_cylinder(0.5f, 2.0f, 16);
    auto cone = engine3d::create_cone(0.5f, 2.0f, 16);
    auto torus = engine3d::create_torus(0.8f, 0.3f, 24, 12);

    std::cout << "\n--- 立方体 ---\n" << cube.to_string();
    std::cout << "  顶点 (前 3 个):\n";
    for (int i = 0; i < 3 && i < cube.vertex_count(); i++) {
        std::cout << "    " << cube.vertices[i].position << std::endl;
    }

    std::cout << "\n--- 球体 ---\n" << sphere.to_string();
    std::cout << "  顶点 (前 3 个):\n";
    for (int i = 0; i < 3 && i < sphere.vertex_count(); i++) {
        std::cout << "    " << sphere.vertices[i].position << std::endl;
    }

    std::cout << "\n--- 圆柱 ---\n" << cylinder.to_string();
    std::cout << "  顶点 (前 3 个):\n";
    for (int i = 0; i < 3 && i < cylinder.vertex_count(); i++) {
        std::cout << "    " << cylinder.vertices[i].position << std::endl;
    }

    std::cout << "\n--- 圆锥 ---\n" << cone.to_string();
    std::cout << "  顶点 (前 3 个):\n";
    for (int i = 0; i < 3 && i < cone.vertex_count(); i++) {
        std::cout << "    " << cone.vertices[i].position << std::endl;
    }

    std::cout << "\n--- 环面 ---\n" << torus.to_string();
    std::cout << "  顶点 (前 3 个):\n";
    for (int i = 0; i < 3 && i < torus.vertex_count(); i++) {
        std::cout << "    " << torus.vertices[i].position << std::endl;
    }

    std::cout << "\n所有模型创建完成!" << std::endl;
    return 0;
}
