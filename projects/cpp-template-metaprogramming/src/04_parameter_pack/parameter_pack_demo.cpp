// =============================================================================
// parameter_pack_demo.cpp - 可变参数模板演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o parameter_pack_demo parameter_pack_demo.cpp
// 运行: ./parameter_pack_demo
// =============================================================================

#include <iostream>
#include <string>
#include <tuple>
#include "variadic/parameter_pack.hpp"

int main() {
    using namespace tmp::variadic;

    std::cout << "=== 可变参数模板演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本递归展开
    std::cout << "1. 基本递归展开:" << std::endl;
    print(1, 2.0, 'c', "hello", std::string("world"));
    std::cout << std::endl;

    // 2. sizeof... 运算符
    std::cout << "2. sizeof... 运算符:" << std::endl;
    std::cout << "  count_args<int, double, char>() = "
              << count_args<int, double, char>() << std::endl;
    std::cout << "  count_args_values(1, 2, 3, 4, 5) = "
              << count_args_values(1, 2, 3, 4, 5) << std::endl;
    std::cout << std::endl;

    // 3. 带索引的打印
    std::cout << "3. 带索引的打印:" << std::endl;
    print_with_index("hello", 42, 3.14, 'x');
    std::cout << std::endl;

    // 4. 折叠表达式求和
    std::cout << "4. 折叠表达式:" << std::endl;
    std::cout << "  sum(1, 2, 3, 4, 5) = " << sum(1, 2, 3, 4, 5) << std::endl;
    std::cout << "  product(2, 3, 4) = " << product(2, 3, 4) << std::endl;
    std::cout << std::endl;

    // 5. 打印 tuple
    std::cout << "5. 打印 tuple:" << std::endl;
    auto t = std::make_tuple(1, 3.14, "hello", 'x');
    print_tuple(t);
    std::cout << std::endl;

    // 6. 条件过滤
    std::cout << "6. 条件过滤 (偶数):" << std::endl;
    for_each_if([](int x) { return x % 2 == 0; }, 1, 2, 3, 4, 5, 6);
    std::cout << std::endl;

    // 7. 参数转换
    std::cout << "7. 参数转换:" << std::endl;
    auto result = transform([](int x) { return x * x; }, 1, 2, 3, 4, 5);
    std::cout << "  Squares: ";
    std::apply([](auto... args) { ((std::cout << args << " "), ...); }, result);
    std::cout << std::endl;
    std::cout << std::endl;

    // 8. 不同的递归策略
    std::cout << "8. 不同的递归策略:" << std::endl;
    std::cout << "  Strategy 1: ";
    strategy1_print(1, 2, 3, 4, 5);
    std::cout << "  Strategy 2: ";
    strategy2_print(1, 2, 3, 4, 5);
    std::cout << "  Strategy 3: ";
    strategy3_print(1, 2, 3, 4, 5);
    std::cout << std::endl;

    // 9. 类型安全的 printf
    std::cout << "9. 类型安全的 printf:" << std::endl;
    safe_printf("Hello {}, you are {} years old!\n", "Alice", 25);
    safe_printf("{} + {} = {}\n", 3, 4, 7);
    std::cout << std::endl;

    std::cout << "=== 可变参数模板演示完成 ===" << std::endl;
    return 0;
}
