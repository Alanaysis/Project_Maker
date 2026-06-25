#include "3d_engine/3d_engine.h"
#include <iostream>

int main() {
    std::cout << "=== 3D 模型变换演示 ===" << std::endl;

    auto cube = engine3d::create_cube(1.0f);
    std::cout << "原始立方体:\n" << cube.to_string();

    // Scale
    auto scaled = engine3d::Transform::scale(cube, 2.0f, 0.5f, 2.0f);
    std::cout << "\n缩放 (2x, 0.5y, 2z):\n";
    for (int i = 0; i < scaled.vertex_count(); i++) {
        std::cout << "  V" << i << ": " << scaled.vertices[i].position << std::endl;
    }

    // Rotate
    auto rotated = engine3d::Transform::rotate_y(cube, 3.14159f / 4.0f);
    std::cout << "\n旋转 45 度 (Y轴):\n";
    for (int i = 0; i < rotated.vertex_count(); i++) {
        std::cout << "  V" << i << ": " << rotated.vertices[i].position << std::endl;
    }

    // Translate
    auto translated = engine3d::Transform::translate(cube, 5.0f, 3.0f, 1.0f);
    std::cout << "\n平移 (5, 3, 1):\n";
    for (int i = 0; i < translated.vertex_count(); i++) {
        std::cout << "  V" << i << ": " << translated.vertices[i].position << std::endl;
    }

    // Combined
    auto combined = engine3d::Transform::translate(
        engine3d::Transform::rotate_y(cube, 3.14159f / 6.0f),
        0.0f, 0.0f, 3.0f
    );
    std::cout << "\n组合 (旋转30度 + 平移Z=3):\n";
    for (int i = 0; i < combined.vertex_count(); i++) {
        std::cout << "  V" << i << ": " << combined.vertices[i].position << std::endl;
    }

    std::cout << "\n变换演示完成!" << std::endl;
    return 0;
}
