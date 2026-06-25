#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>

/**
 * @file gcc_demo.cpp
 * @brief GCC 工具链示例
 *
 * 演示 GCC 编译器的各种特性和选项。
 * 本文件故意包含一些可以触发警告的代码，用于演示 GCC 的警告功能。
 */

// 使用 [[nodiscard]] 属性
[[nodiscard]] int compute_value(int x) {
    return x * 2 + 1;
}

// 演示 GCC 特有的 __attribute__ 用法
[[gnu::always_inline]] inline int fast_add(int a, int b) {
    return a + b;
}

// 演示 likely/unlikely 属性 (C++20)
int process_data(int value) {
    if (value > 0) [[likely]] {
        return value * 2;
    } else [[unlikely]] {
        return 0;
    }
}

// 演示 constexpr
constexpr int factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}

// 演示模板元编程
template<int N>
struct Fibonacci {
    static constexpr int value = Fibonacci<N-1>::value + Fibonacci<N-2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr int value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr int value = 1;
};

int main() {
    std::cout << "=== GCC 工具链示例 ===" << std::endl;
    std::cout << std::endl;

    // 编译器信息
    std::cout << "编译器信息:" << std::endl;
#ifdef __GNUC__
    std::cout << "  GCC 版本: " << __GNUC__ << "." << __GNUC_MINOR__ << "." << __GNUC_PATCHLEVEL__ << std::endl;
#endif
    std::cout << "  C++ 标准: " << __cplusplus << std::endl;
    std::cout << std::endl;

    // 使用 nodiscard 函数
    int result = compute_value(5);
    std::cout << "compute_value(5) = " << result << std::endl;

    // 使用 inline 函数
    std::cout << "fast_add(3, 4) = " << fast_add(3, 4) << std::endl;

    // 使用 constexpr
    std::cout << "factorial(10) = " << factorial(10) << std::endl;

    // 使用模板元编程
    std::cout << "Fibonacci(10) = " << Fibonacci<10>::value << std::endl;

    // 使用 STL
    std::vector<int> data(10);
    std::iota(data.begin(), data.end(), 1);

    std::cout << "数据: ";
    for (const auto& val : data) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    auto sum = std::accumulate(data.begin(), data.end(), 0);
    std::cout << "总和: " << sum << std::endl;

    auto max_val = *std::max_element(data.begin(), data.end());
    std::cout << "最大值: " << max_val << std::endl;

    std::cout << std::endl;
    std::cout << "GCC 编译选项说明:" << std::endl;
    std::cout << "  -Wall -Wextra -Wpedantic  : 基本警告" << std::endl;
    std::cout << "  -Wshadow                  : 变量遮蔽警告" << std::endl;
    std::cout << "  -Wconversion              : 类型转换警告" << std::endl;
    std::cout << "  -Wnull-dereference        : 空指针解引用警告" << std::endl;
    std::cout << "  -O2                       : 推荐优化级别" << std::endl;
    std::cout << "  -flto                     : 链接时优化" << std::endl;

    return 0;
}
