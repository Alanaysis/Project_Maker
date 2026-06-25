/**
 * @file if_consteval.cpp
 * @brief C++23 if consteval 示例
 *
 * if consteval 是 C++23 引入的编译期常量求值判断。
 * 它允许在编译时判断当前是否在常量求值上下文中。
 *
 * 主要特点：
 * - 编译时判断是否在常量求值上下文中
 * - 支持不同的编译期和运行时路径
 * - 优化编译期计算
 * - 避免运行时开销
 *
 * 编译命令：
 * g++ -std=c++23 -o if_consteval if_consteval.cpp
 */

#include <iostream>
#include <string>
#include <array>
#include <algorithm>

// ========== 1. 基本用法 ==========

// 使用 if consteval 判断编译期上下文
constexpr int compute(int x) {
    if consteval {
        // 编译期路径：使用更高效的算法
        return x * x;
    } else {
        // 运行时路径：可以使用更复杂的逻辑
        std::cout << "Runtime computation" << std::endl;
        return x * x;
    }
}

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 编译期调用
    constexpr int compile_result = compute(5);
    std::cout << "Compile-time result: " << compile_result << std::endl;

    // 运行时调用
    int runtime_result = compute(10);
    std::cout << "Runtime result: " << runtime_result << std::endl;
}

// ========== 2. 编译期优化 ==========

// 编译期阶乘
constexpr int factorial(int n) {
    if consteval {
        // 编译期：使用递归
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    } else {
        // 运行时：使用循环
        int result = 1;
        for (int i = 2; i <= n; ++i) {
            result *= i;
        }
        return result;
    }
}

void compile_time_optimization() {
    std::cout << "\n=== 编译期优化 ===" << std::endl;

    // 编译期计算
    constexpr int fact5 = factorial(5);
    std::cout << "5! = " << fact5 << std::endl;

    // 运行时计算
    int fact10 = factorial(10);
    std::cout << "10! = " << fact10 << std::endl;
}

// ========== 3. 编译期字符串处理 ==========

// 编译期字符串长度
constexpr size_t string_length(const char* str) {
    if consteval {
        // 编译期：手动计算长度
        size_t len = 0;
        while (str[len] != '\0') {
            ++len;
        }
        return len;
    } else {
        // 运行时：使用标准库
        size_t len = 0;
        while (str[len] != '\0') {
            ++len;
        }
        return len;
    }
}

void string_processing() {
    std::cout << "\n=== 编译期字符串处理 ===" << std::endl;

    // 编译期计算
    constexpr size_t len1 = string_length("Hello");
    std::cout << "Length of 'Hello': " << len1 << std::endl;

    // 运行时计算
    const char* str = "World";
    size_t len2 = string_length(str);
    std::cout << "Length of 'World': " << len2 << std::endl;
}

// ========== 4. 编译期数组处理 ==========

// 编译期数组求和
constexpr int array_sum(const int* arr, size_t size) {
    if consteval {
        // 编译期：手动求和
        int sum = 0;
        for (size_t i = 0; i < size; ++i) {
            sum += arr[i];
        }
        return sum;
    } else {
        // 运行时：可以使用标准库
        int sum = 0;
        for (size_t i = 0; i < size; ++i) {
            sum += arr[i];
        }
        return sum;
    }
}

void array_processing() {
    std::cout << "\n=== 编译期数组处理 ===" << std::endl;

    // 编译期计算
    constexpr int arr[] = {1, 2, 3, 4, 5};
    constexpr int sum1 = array_sum(arr, 5);
    std::cout << "Sum of [1,2,3,4,5]: " << sum1 << std::endl;

    // 运行时计算
    int runtime_arr[] = {10, 20, 30, 40, 50};
    int sum2 = array_sum(runtime_arr, 5);
    std::cout << "Sum of [10,20,30,40,50]: " << sum2 << std::endl;
}

// ========== 5. 编译期查找 ==========

// 编译期线性查找
constexpr int linear_search(const int* arr, size_t size, int target) {
    if consteval {
        // 编译期：手动查找
        for (size_t i = 0; i < size; ++i) {
            if (arr[i] == target) {
                return static_cast<int>(i);
            }
        }
        return -1;
    } else {
        // 运行时：可以使用标准库
        for (size_t i = 0; i < size; ++i) {
            if (arr[i] == target) {
                return static_cast<int>(i);
            }
        }
        return -1;
    }
}

void search_example() {
    std::cout << "\n=== 编译期查找 ===" << std::endl;

    // 编译期查找
    constexpr int arr[] = {10, 20, 30, 40, 50};
    constexpr int index1 = linear_search(arr, 5, 30);
    std::cout << "Index of 30: " << index1 << std::endl;

    // 运行时查找
    int runtime_arr[] = {100, 200, 300, 400, 500};
    int index2 = linear_search(runtime_arr, 5, 300);
    std::cout << "Index of 300: " << index2 << std::endl;
}

// ========== 6. 编译期排序 ==========

// 编译期冒泡排序
constexpr void bubble_sort(int* arr, size_t size) {
    if consteval {
        // 编译期：手动排序
        for (size_t i = 0; i < size - 1; ++i) {
            for (size_t j = 0; j < size - i - 1; ++j) {
                if (arr[j] > arr[j + 1]) {
                    int temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                }
            }
        }
    } else {
        // 运行时：可以使用标准库
        for (size_t i = 0; i < size - 1; ++i) {
            for (size_t j = 0; j < size - i - 1; ++j) {
                if (arr[j] > arr[j + 1]) {
                    int temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                }
            }
        }
    }
}

void sorting_example() {
    std::cout << "\n=== 编译期排序 ===" << std::endl;

    // 编译期排序
    constexpr auto sorted_arr = []() constexpr {
        int arr[] = {5, 2, 8, 1, 9, 3};
        bubble_sort(arr, 6);
        return std::array<int, 6>{arr[0], arr[1], arr[2], arr[3], arr[4], arr[5]};
    }();

    std::cout << "Sorted array: ";
    for (int n : sorted_arr) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 7. 实际应用：配置验证 ==========

// 编译期配置验证
constexpr bool validate_config(int port, int max_connections) {
    if consteval {
        // 编译期：简单验证
        return port > 0 && port < 65536 && max_connections > 0;
    } else {
        // 运行时：可以进行更复杂的验证
        return port > 0 && port < 65536 && max_connections > 0 && max_connections < 10000;
    }
}

void config_validation() {
    std::cout << "\n=== 实际应用：配置验证 ===" << std::endl;

    // 编译期验证
    constexpr bool valid1 = validate_config(8080, 100);
    std::cout << "Config (8080, 100) is " << (valid1 ? "valid" : "invalid") << std::endl;

    // 运行时验证
    bool valid2 = validate_config(8080, 15000);
    std::cout << "Config (8080, 15000) is " << (valid2 ? "valid" : "invalid") << std::endl;
}

// ========== 8. 实际应用：数学计算 ==========

// 编译期平方根 (近似)
constexpr double sqrt_approx(double x, int iterations) {
    if consteval {
        // 编译期：牛顿法
        double guess = x / 2.0;
        for (int i = 0; i < iterations; ++i) {
            guess = (guess + x / guess) / 2.0;
        }
        return guess;
    } else {
        // 运时：可以使用标准库
        double guess = x / 2.0;
        for (int i = 0; i < iterations; ++i) {
            guess = (guess + x / guess) / 2.0;
        }
        return guess;
    }
}

void math_example() {
    std::cout << "\n=== 实际应用：数学计算 ===" << std::endl;

    // 编译期平方根
    constexpr double sqrt2 = sqrt_approx(2.0, 10);
    std::cout << "sqrt(2) ≈ " << sqrt2 << std::endl;

    // 运行时平方根
    double sqrt3 = sqrt_approx(3.0, 10);
    std::cout << "sqrt(3) ≈ " << sqrt3 << std::endl;
}

// ========== 9. 实际应用：编译期表生成 ==========

// 编译期生成查找表
constexpr auto generate_lookup_table() {
    std::array<int, 10> table{};
    if consteval {
        for (int i = 0; i < 10; ++i) {
            table[i] = i * i;
        }
    }
    return table;
}

void lookup_table_example() {
    std::cout << "\n=== 实际应用：编译期表生成 ===" << std::endl;

    // 编译期生成的查找表
    constexpr auto squares = generate_lookup_table();

    std::cout << "Squares lookup table:" << std::endl;
    for (int i = 0; i < 10; ++i) {
        std::cout << "  " << i << "^2 = " << squares[i] << std::endl;
    }
}

// ========== 10. 实际应用：编译期断言 ==========

// 编译期断言
constexpr void compile_time_assert(bool condition, const char* message) {
    if consteval {
        if (!condition) {
            // 编译期：可以触发编译错误
            // 实际上，consteval 函数中不能直接输出错误
            // 但可以通过其他方式触发编译错误
        }
    } else {
        if (!condition) {
            std::cerr << "Assertion failed: " << message << std::endl;
        }
    }
}

void assertion_example() {
    std::cout << "\n=== 实际应用：编译期断言 ===" << std::endl;

    // 编译期断言
    constexpr bool condition = true;
    compile_time_assert(condition, "This should pass");

    // 运行时断言
    bool runtime_condition = false;
    compile_time_assert(runtime_condition, "This will fail at runtime");
}

int main() {
    std::cout << "C++23 if consteval 示例\n" << std::endl;

    basic_usage();
    compile_time_optimization();
    string_processing();
    array_processing();
    search_example();
    sorting_example();
    config_validation();
    math_example();
    lookup_table_example();
    assertion_example();

    return 0;
}
