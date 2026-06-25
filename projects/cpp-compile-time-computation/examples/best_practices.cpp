// best_practices.cpp - 编译期计算最佳实践示例
//
// 本文件展示编译期计算的最佳实践和常见陷阱，包括：
//   1. 何时使用编译期计算
//   2. 常见陷阱和解决方案
//   3. 性能优化技巧
//   4. 代码组织建议
//
// 编译命令：
//   g++ -std=c++20 -I include examples/best_practices.cpp -o best_practices

#include <iostream>
#include <array>
#include <vector>
#include <chrono>

// ============================================================================
// 第一部分：何时使用编译期计算
// ============================================================================

// 好的使用场景 1：常量表达式
constexpr int MAX_SIZE = 100;
constexpr double PI = 3.14159265358979323846;

// 好的使用场景 2：查找表
constexpr auto square_table = []() {
    std::array<int, 100> table{};
    for (int i = 0; i < 100; ++i) {
        table[i] = i * i;
    }
    return table;
}();

// 好的使用场景 3：类型安全的单位转换
constexpr double km_to_m(double km) { return km * 1000.0; }
constexpr double m_to_km(double m) { return m / 1000.0; }

// 好的使用场景 4：编译期验证
constexpr bool is_power_of_two(unsigned int n) {
    return n > 0 && (n & (n - 1)) == 0;
}

// ============================================================================
// 第二部分：常见陷阱和解决方案
// ============================================================================

// 陷阱 1：过度使用 constexpr
// 不好：简单的常量不需要 constexpr
// constexpr int x = 42;  // 没有必要
// 好：直接使用字面量
const int x = 42;

// 陷阱 2：混淆 constexpr 和 const
// constexpr：编译期常量
constexpr int constexpr_val = 42;

// const：运行时常量
const int const_val = []() { return 42; }();

// 陷阱 3：忽略编译时间影响
// 不好：复杂的编译期计算
// constexpr auto huge_table = generate_huge_table<10000>();

// 好：只在必要时使用编译期计算
const auto huge_table = []() {
    std::array<int, 10000> table{};
    for (int i = 0; i < 10000; ++i) {
        table[i] = i * i;
    }
    return table;
}();

// 陷阱 4：C++ 版本差异
// C++11：只允许一条 return 语句
constexpr int factorial_11(int n) {
    return (n <= 1) ? 1 : n * factorial_11(n - 1);
}

// C++14：允许局部变量和循环
constexpr int factorial_14(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// ============================================================================
// 第三部分：性能优化技巧
// ============================================================================

// 技巧 1：使用查找表替代重复计算
constexpr auto sin_table = []() {
    std::array<double, 360> table{};
    for (int i = 0; i < 360; ++i) {
        double x = i * 3.14159265358979323846 / 180.0;
        // 泰勒级数计算 sin
        double result = 0;
        double term = x;
        for (int n = 1; n <= 20; ++n) {
            result += term;
            term *= -x * x / ((2 * n) * (2 * n + 1));
        }
        table[i] = result;
    }
    return table;
}();

// 技巧 2：使用 constexpr 函数而非宏
// 不好：使用宏
#define SQUARE_MACRO(x) ((x) * (x))

// 好：使用 constexpr 函数
constexpr int square(int x) { return x * x; }

// 技巧 3：使用模板参数而非运行时参数
// 不好：运行时参数
int power_runtime(int base, int exp) {
    int result = 1;
    for (int i = 0; i < exp; ++i) {
        result *= base;
    }
    return result;
}

// 好：模板参数（编译期计算）
template<int Exp>
constexpr int power_template(int base) {
    int result = 1;
    for (int i = 0; i < Exp; ++i) {
        result *= base;
    }
    return result;
}

// 技巧 4：使用编译期断言验证
constexpr int safe_divide(int a, int b) {
    // 编译期检查除数不为零
    if (b == 0) {
        throw "Division by zero";
    }
    return a / b;
}

// ============================================================================
// 第四部分：代码组织建议
// ============================================================================

// 建议 1：将编译期计算放在头文件中
// 编译期函数通常放在头文件中，因为它们需要在编译时可用

// 建议 2：使用命名空间组织编译期代码
namespace ct {
    constexpr long long factorial(int n) {
        long long result = 1;
        for (int i = 2; i <= n; ++i) {
            result *= i;
        }
        return result;
    }

    constexpr long long fibonacci(int n) {
        if (n <= 1) return n;
        long long a = 0, b = 1;
        for (int i = 2; i <= n; ++i) {
            long long temp = a + b;
            a = b;
            b = temp;
        }
        return b;
    }
}

// 建议 3：使用 constexpr 变量存储编译期结果
constexpr auto factorial_table = []() {
    std::array<long long, 20> table{};
    for (int i = 0; i < 20; ++i) {
        table[i] = ct::factorial(i);
    }
    return table;
}();

// 建议 4：使用编译期类型检查
template<typename T>
constexpr bool is_valid_type() {
    return std::is_arithmetic_v<T> || std::is_class_v<T>;
}

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 验证常量
static_assert(MAX_SIZE == 100);
static_assert(PI > 3.14 && PI < 3.15);

// 验证查找表
static_assert(square_table[10] == 100);
static_assert(square_table[25] == 625);

// 验证单位转换
static_assert(km_to_m(1.0) == 1000.0);
static_assert(m_to_km(1000.0) == 1.0);

// 验证编译期检查
static_assert(is_power_of_two(8) == true);
static_assert(is_power_of_two(7) == false);

// 验证阶乘
static_assert(factorial_11(5) == 120);
static_assert(factorial_14(5) == 120);

// 验证模板函数
static_assert(power_template<3>(2) == 8);
static_assert(power_template<4>(3) == 81);

// 验证命名空间中的函数
static_assert(ct::factorial(5) == 120);
static_assert(ct::fibonacci(10) == 55);

// 验证编译期表
static_assert(factorial_table[5] == 120);
static_assert(factorial_table[10] == 3628800);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期计算最佳实践 ===" << std::endl;
    std::cout << std::endl;

    // 何时使用编译期计算
    std::cout << "1. 何时使用编译期计算:" << std::endl;
    std::cout << "   - 常量表达式（MAX_SIZE, PI）" << std::endl;
    std::cout << "   - 查找表（sin_table, square_table）" << std::endl;
    std::cout << "   - 类型安全的单位转换" << std::endl;
    std::cout << "   - 编译期验证（is_power_of_two）" << std::endl;
    std::cout << std::endl;

    // 常见陷阱
    std::cout << "2. 常见陷阱:" << std::endl;
    std::cout << "   - 过度使用 constexpr" << std::endl;
    std::cout << "   - 混淆 constexpr 和 const" << std::endl;
    std::cout << "   - 忽略编译时间影响" << std::endl;
    std::cout << "   - C++ 版本差异" << std::endl;
    std::cout << std::endl;

    // 性能优化技巧
    std::cout << "3. 性能优化技巧:" << std::endl;
    std::cout << "   - 使用查找表替代重复计算" << std::endl;
    std::cout << "   - 使用 constexpr 函数而非宏" << std::endl;
    std::cout << "   - 使用模板参数而非运行时参数" << std::endl;
    std::cout << "   - 使用编译期断言验证" << std::endl;
    std::cout << std::endl;

    // 代码组织建议
    std::cout << "4. 代码组织建议:" << std::endl;
    std::cout << "   - 将编译期计算放在头文件中" << std::endl;
    std::cout << "   - 使用命名空间组织编译期代码" << std::endl;
    std::cout << "   - 使用 constexpr 变量存储编译期结果" << std::endl;
    std::cout << "   - 使用编译期类型检查" << std::endl;
    std::cout << std::endl;

    // 示例
    std::cout << "5. 示例:" << std::endl;
    std::cout << "   square(5) = " << square(5) << std::endl;
    std::cout << "   square_table[10] = " << square_table[10] << std::endl;
    std::cout << "   sin_table[90] = " << sin_table[90] << std::endl;
    std::cout << "   power_template<3>(2) = " << power_template<3>(2) << std::endl;
    std::cout << "   ct::factorial(10) = " << ct::factorial(10) << std::endl;
    std::cout << "   ct::fibonacci(20) = " << ct::fibonacci(20) << std::endl;
    std::cout << "   factorial_table[10] = " << factorial_table[10] << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
