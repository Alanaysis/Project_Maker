// =============================================================================
// compile_time_string_demo.cpp - 编译期字符串演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o compile_time_string_demo compile_time_string_demo.cpp
// 运行: ./compile_time_string_demo
// =============================================================================

#include <iostream>
#include <string>
#include "compile_time/compile_time_string.hpp"

int main() {
    std::cout << "=== 编译期字符串演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本定义
    std::cout << "1. 基本定义:" << std::endl;
    constexpr tmp::FixedString hello{"Hello"};
    constexpr tmp::FixedString world{"World"};
    std::cout << "  hello: " << hello.view() << " (size=" << hello.size << ")" << std::endl;
    std::cout << "  world: " << world.view() << " (size=" << world.size << ")" << std::endl;
    std::cout << std::endl;

    // 2. 访问字符
    std::cout << "2. 访问字符:" << std::endl;
    std::cout << "  hello[0] = " << hello[0] << std::endl;
    std::cout << "  hello[4] = " << hello[4] << std::endl;
    std::cout << std::endl;

    // 3. 比较操作
    std::cout << "3. 比较操作:" << std::endl;
    constexpr tmp::FixedString hello2{"Hello"};
    constexpr tmp::FixedString other{"Other"};
    std::cout << "  hello == hello2: " << (hello == hello2) << std::endl;
    std::cout << "  hello == other: " << (hello == other) << std::endl;
    std::cout << std::endl;

    // 4. 字符串长度
    std::cout << "4. 字符串长度:" << std::endl;
    std::cout << "  length(hello) = " << tmp::string_length<hello>() << std::endl;
    std::cout << std::endl;

    // 5. 字符串连接 (编译期)
    std::cout << "5. 字符串连接:" << std::endl;
    constexpr auto greeting = tmp::concat_strings<"Hello, ", "World!">();
    std::cout << "  concat: " << greeting.view() << std::endl;
    std::cout << std::endl;

    // 6. 字符串反转
    std::cout << "6. 字符串反转:" << std::endl;
    constexpr auto reversed = tmp::reverse_string<"Hello">();
    std::cout << "  reverse(Hello) = " << reversed.view() << std::endl;
    std::cout << std::endl;

    // 7. 大小写转换
    std::cout << "7. 大小写转换:" << std::endl;
    constexpr auto upper = tmp::to_upper<"hello world">();
    constexpr auto lower = tmp::to_lower<"HELLO WORLD">();
    std::cout << "  to_upper(hello world) = " << upper.view() << std::endl;
    std::cout << "  to_lower(HELLO WORLD) = " << lower.view() << std::endl;
    std::cout << std::endl;

    // 8. 前缀/后缀检查
    std::cout << "8. 前缀/后缀检查:" << std::endl;
    constexpr bool starts = tmp::starts_with<"Hello World", "Hello">();
    constexpr bool ends = tmp::ends_with<"Hello World", "World">();
    std::cout << "  starts_with(Hello World, Hello) = " << starts << std::endl;
    std::cout << "  ends_with(Hello World, World) = " << ends << std::endl;
    std::cout << std::endl;

    // 9. 字符串哈希
    std::cout << "9. 字符串哈希:" << std::endl;
    constexpr auto hash1 = tmp::fixed_string_hash<"Hello">();
    constexpr auto hash2 = tmp::fixed_string_hash<"World">();
    std::cout << "  hash(Hello) = " << hash1 << std::endl;
    std::cout << "  hash(World) = " << hash2 << std::endl;
    std::cout << std::endl;

    // 10. 类型萃取
    std::cout << "10. 类型萃取:" << std::endl;
    std::cout << "  FixedString is fixed string: "
              << tmp::is_fixed_string_v<tmp::FixedString<5>> << std::endl;
    std::cout << "  int is fixed string: "
              << tmp::is_fixed_string_v<int> << std::endl;
    std::cout << std::endl;

    // 11. 配置示例
    std::cout << "11. 编译期配置:" << std::endl;
    std::cout << "  HostConfig name: " << tmp::HostConfig::name.view() << std::endl;
    std::cout << "  HostConfig value: " << tmp::HostConfig::value.view() << std::endl;
    std::cout << "  PortConfig name: " << tmp::PortConfig::name.view() << std::endl;
    std::cout << "  PortConfig value: " << tmp::PortConfig::value.view() << std::endl;
    std::cout << std::endl;

    // 12. 编译期断言
    std::cout << "12. 编译期断言:" << std::endl;
    static_assert(hello.size == 5, "Hello should have 5 characters");
    static_assert(hello == hello2, "Hello should equal Hello");
    static_assert(starts == true, "Hello World starts with Hello");
    static_assert(ends == true, "Hello World ends with World");
    std::cout << "  All compile-time assertions passed!" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 编译期字符串演示完成 ===" << std::endl;
    return 0;
}
