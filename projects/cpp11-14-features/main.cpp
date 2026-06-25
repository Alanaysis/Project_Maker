/**
 * C++11/14 新特性实践 - 主程序
 *
 * 本程序演示 C++11/14 的核心新特性
 */

#include <iostream>
#include <string>
#include <vector>
#include <functional>
#include <memory>

// 声明各个示例的主函数
// 注意：这些函数在各自的示例文件中定义
// 为了演示，我们在这里重新组织

void print_header(const std::string& title) {
    std::cout << "\n========================================" << std::endl;
    std::cout << title << std::endl;
    std::cout << "========================================" << std::endl;
}

int main() {
    print_header("C++11/14 新特性实践");

    std::cout << "\n本项目包含以下示例：" << std::endl;
    std::cout << "1. 移动语义和右值引用 (01_move_semantics)" << std::endl;
    std::cout << "2. Lambda 表达式 (02_lambda)" << std::endl;
    std::cout << "3. 智能指针 (03_smart_pointers)" << std::endl;
    std::cout << "4. 并发编程 (04_threads)" << std::endl;
    std::cout << "5. 可变参数模板 (05_variadic_templates)" << std::endl;
    std::cout << "6. constexpr (06_constexpr)" << std::endl;
    std::cout << "7. auto 和 decltype (07_auto_decltype)" << std::endl;
    std::cout << "8. 范围 for 循环 (08_range_for)" << std::endl;
    std::cout << "9. 初始化列表 (09_initializer_list)" << std::endl;

    std::cout << "\n请运行各个示例程序以查看详细内容。" << std::endl;
    std::cout << "例如: ./build/01_move_semantics" << std::endl;

    // 简单演示一些特性
    print_header("快速演示");

    // 移动语义
    std::cout << "\n--- 移动语义 ---" << std::endl;
    std::string s1 = "Hello";
    std::string s2 = std::move(s1);
    std::cout << "s2 = " << s2 << std::endl;
    std::cout << "s1 is " << (s1.empty() ? "empty" : "not empty") << std::endl;

    // Lambda
    std::cout << "\n--- Lambda ---" << std::endl;
    auto add = [](int a, int b) { return a + b; };
    std::cout << "add(3, 4) = " << add(3, 4) << std::endl;

    // 智能指针
    std::cout << "\n--- 智能指针 ---" << std::endl;
    auto ptr = std::make_unique<int>(42);
    std::cout << "*ptr = " << *ptr << std::endl;

    // 初始化列表
    std::cout << "\n--- 初始化列表 ---" << std::endl;
    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::cout << "vec: ";
    for (int val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 范围 for
    std::cout << "\n--- 范围 for ---" << std::endl;
    for (const auto& val : vec) {
        std::cout << val * 2 << " ";
    }
    std::cout << std::endl;

    // auto
    std::cout << "\n--- auto ---" << std::endl;
    auto x = 42;
    auto d = 3.14;
    auto s = std::string("Hello");
    std::cout << "x = " << x << " (int)" << std::endl;
    std::cout << "d = " << d << " (double)" << std::endl;
    std::cout << "s = " << s << " (string)" << std::endl;

    print_header("演示完毕");

    return 0;
}
