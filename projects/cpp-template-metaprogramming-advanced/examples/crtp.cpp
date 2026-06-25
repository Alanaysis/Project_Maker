/**
 * @file crtp.cpp
 * @brief CRTP (奇异递归模板模式) 示例
 *
 * CRTP 实现编译期多态，避免虚函数开销。
 */

#include <iostream>
#include <string>
#include "../include/advanced_templates/crtp.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== CRTP (Curiously Recurring Template Pattern) ===" << std::endl;
    std::cout << std::endl;

    // 1. 静态多态
    std::cout << "--- 1. Static Polymorphism ---" << std::endl;
    Circle circle(5.0);
    Rectangle rect(4.0, 6.0);

    std::cout << circle.name() << ": area = " << circle.area() << std::endl;
    std::cout << rect.name() << ": area = " << rect.area() << std::endl;

    circle.draw();
    rect.draw();
    std::cout << std::endl;

    // 2. CRTP 运算符重载
    std::cout << "--- 2. CRTP Comparable ---" << std::endl;
    // Circle c1(3.0), c2(5.0);
    // c1 < c2 会自动通过 CRTP 生成
    // (需要实现 compare_to_impl)
    std::cout << "(Comparable mixin provides ==, !=, <, >, <=, >=)" << std::endl;
    std::cout << std::endl;

    // 3. CRTP 链式调用
    std::cout << "--- 3. Method Chaining ---" << std::endl;
    QueryBuilder query;
    std::string sql = query
        .from("users")
        .select("name")
        .select("age")
        .where("age > 18")
        .where("active = true")
        .limit(10)
        .build();

    std::cout << "Generated SQL: " << sql << std::endl;
    std::cout << std::endl;

    // 4. CRTP 渲染器
    std::cout << "--- 4. Static Polymorphism Renderer ---" << std::endl;
    OpenGLRenderer gl;
    VulkanRenderer vk;

    render_scene(gl);
    render_scene(vk);
    std::cout << std::endl;

    // 5. 实例计数器
    std::cout << "--- 5. Instance Counter ---" << std::endl;
    // InstanceCounter tracks instances
    std::cout << "(InstanceCounter mixin tracks object lifecycle)" << std::endl;
    std::cout << std::endl;

    // 6. CRTP 检测
    std::cout << "--- 6. CRTP Detection ---" << std::endl;
    std::cout << "Circle uses ShapeBase: "
              << uses_crtp_v<Circle, ShapeBase> << std::endl;
    std::cout << "int uses ShapeBase: "
              << uses_crtp_v<int, ShapeBase> << std::endl;
    std::cout << std::endl;

    std::cout << "Key advantages of CRTP:" << std::endl;
    std::cout << "  - No virtual function overhead" << std::endl;
    std::cout << "  - Compile-time polymorphism" << std::endl;
    std::cout << "  - Can be inlined by compiler" << std::endl;
    std::cout << "  - No vtable pointer in objects" << std::endl;

    return 0;
}
