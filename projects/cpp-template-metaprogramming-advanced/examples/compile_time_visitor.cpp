/**
 * @file compile_time_visitor.cpp
 * @brief 编译期访问者模式示例
 */

#include <iostream>
#include <string>
#include <variant>
#include <vector>
#include "../include/design_patterns/visitor.hpp"

// 定义形状结构体（在全局作用域）
struct CircleShape { double radius; };
struct RectShape { double w; double h; };
struct TriShape { double base; double h; };

int main() {
    using namespace tmp;

    std::cout << "=== Compile-time Visitor Pattern ===" << std::endl;
    std::cout << std::endl;

    // 1. overloaded 访问者
    std::cout << "--- 1. Overloaded Visitor ---" << std::endl;

    std::variant<int, double, std::string> v1 = 42;
    std::variant<int, double, std::string> v2 = 3.14;
    std::variant<int, double, std::string> v3 = "hello";

    auto visitor = overloaded{
        [](int i) { std::cout << "int: " << i << std::endl; },
        [](double d) { std::cout << "double: " << d << std::endl; },
        [](const std::string& s) { std::cout << "string: " << s << std::endl; }
    };

    std::visit(visitor, v1);
    std::visit(visitor, v2);
    std::visit(visitor, v3);
    std::cout << std::endl;

    // 2. 类型列表访问者
    std::cout << "--- 2. Type List Visitor ---" << std::endl;

    std::cout << "Types in tuple:" << std::endl;
    std::cout << "  - int: " << sizeof(int) << " bytes" << std::endl;
    std::cout << "  - double: " << sizeof(double) << " bytes" << std::endl;
    std::cout << "  - string: " << sizeof(std::string) << " bytes" << std::endl;
    std::cout << "  - bool: " << sizeof(bool) << " bytes" << std::endl;
    std::cout << std::endl;

    // 3. variant 访问模式
    std::cout << "--- 3. Variant Visitor Pattern ---" << std::endl;

    using Shape = std::variant<CircleShape, RectShape, TriShape>;

    std::vector<Shape> shapes = {
        CircleShape{5.0},
        RectShape{4.0, 6.0},
        TriShape{3.0, 8.0}
    };

    auto area_visitor = overloaded{
        [](const CircleShape& c) -> double { return 3.14159 * c.radius * c.radius; },
        [](const RectShape& r) -> double { return r.w * r.h; },
        [](const TriShape& t) -> double { return 0.5 * t.base * t.h; }
    };

    double total_area = 0;
    for (const auto& shape : shapes) {
        total_area += std::visit(area_visitor, shape);
    }
    std::cout << "Total area: " << total_area << std::endl;
    std::cout << std::endl;

    // 4. 编译期属性收集
    std::cout << "--- 4. Property Collection ---" << std::endl;

    PropertyCollector<int> collector;
    collector.add_property("value", 42);
    collector.add_property("name", std::string("test"));
    collector.print();

    return 0;
}
