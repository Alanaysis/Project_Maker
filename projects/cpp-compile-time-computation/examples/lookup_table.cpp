// lookup_table.cpp - 编译期查找表示例
//
// 本文件展示编译期查找表的用法，包括：
//   1. 基本查找表
//   2. 数学查找表
//   3. 自定义查找表
//   4. 查找表插值
//
// 编译命令：
//   g++ -std=c++20 -I include examples/lookup_table.cpp -o lookup_table

#include <iostream>
#include <iomanip>
#include "compile_time/lookup.hpp"
#include "compile_time/math.hpp"

using namespace compile_time::lookup;
using namespace compile_time::math;

// ============================================================================
// 第一部分：基本查找表
// ============================================================================

// 平方查找表
constexpr auto square_table = make_square_table<100>();

// 立方查找表
constexpr auto cube_table = make_cube_table<50>();

// 阶乘查找表
constexpr auto factorial_table = make_factorial_table<20>();

// 斐波那契查找表
constexpr auto fibonacci_table = make_fibonacci_table<20>();

// ============================================================================
// 第二部分：数学查找表
// ============================================================================

// 正弦查找表（0-359度）
constexpr auto sine_table = make_sine_table();

// 余弦查找表（0-359度）
constexpr auto cosine_table = make_cosine_table();

// 平方根查找表
constexpr auto sqrt_table = make_sqrt_table();

// 指数查找表
constexpr auto exp_table = make_exp_table();

// 对数查找表
constexpr auto log10_table = make_log10_table();

// ============================================================================
// 第三部分：自定义查找表
// ============================================================================

// 自定义函数查找表
constexpr auto custom_table = make_table<100>([](int i) {
    return i * i + 2 * i + 1;  // (i+1)^2
});

// 带范围的查找表
constexpr auto ranged_table = make_table_with_range<100>([](double x) {
    return x * x;  // x^2
}, 0.0, 10.0);

// ASCII 字符分类表
constexpr auto ascii_class_table = make_ascii_class_table();

// 二进制权重表
constexpr auto binary_weight_table = make_binary_weight_table<32>();

// ============================================================================
// 第四部分：查找表操作
// ============================================================================

// 线性插值
constexpr double sin_30_5 = sine_table.interpolate(30.5);

// 查找最接近的值
constexpr std::size_t nearest = square_table.find_nearest(1000);

// ============================================================================
// 第五部分：实际应用示例
// ============================================================================

// 快速正弦函数（使用查找表）
constexpr double fast_sin(double degrees) {
    int index = static_cast<int>(degrees) % 360;
    if (index < 0) index += 360;
    return sine_table[index];
}

// 快速余弦函数（使用查找表）
constexpr double fast_cos(double degrees) {
    int index = static_cast<int>(degrees) % 360;
    if (index < 0) index += 360;
    return cosine_table[index];
}

// 快速平方函数（使用查找表）
constexpr int fast_square(int n) {
    if (n >= 0 && n < 100) return square_table[n];
    return n * n;  // 超出范围时回退到计算
}

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 基本查找表
static_assert(square_table[10] == 100);
static_assert(square_table[25] == 625);
static_assert(square_table[99] == 9801);

static_assert(cube_table[3] == 27);
static_assert(cube_table[10] == 1000);

static_assert(factorial_table[0] == 1);
static_assert(factorial_table[5] == 120);
static_assert(factorial_table[10] == 3628800);

static_assert(fibonacci_table[0] == 0);
static_assert(fibonacci_table[1] == 1);
static_assert(fibonacci_table[10] == 55);

// 数学查找表
static_assert(compile_time::math::abs(sine_table[0]) < 1e-10);           // sin(0) = 0
static_assert(compile_time::math::abs(sine_table[90] - 1.0) < 1e-10);    // sin(90) = 1
static_assert(compile_time::math::abs(cosine_table[0] - 1.0) < 1e-10);   // cos(0) = 1
static_assert(compile_time::math::abs(cosine_table[90]) < 1e-10);         // cos(90) = 0

// 自定义查找表
static_assert(custom_table[0] == 1);   // (0+1)^2 = 1
static_assert(custom_table[1] == 4);   // (1+1)^2 = 4
static_assert(custom_table[9] == 100); // (9+1)^2 = 100

// ASCII 字符分类表
static_assert(ascii_class_table['0'] == 1);  // 数字
static_assert(ascii_class_table['A'] == 2);  // 大写字母
static_assert(ascii_class_table['a'] == 3);  // 小写字母
static_assert(ascii_class_table['!'] == 4);  // 其他

// 二进制权重表
static_assert(binary_weight_table[0] == 1);
static_assert(binary_weight_table[1] == 2);
static_assert(binary_weight_table[10] == 1024);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "=== 编译期查找示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本查找表
    std::cout << "1. 基本查找表:" << std::endl;
    std::cout << "   square_table[10] = " << square_table[10] << std::endl;
    std::cout << "   square_table[25] = " << square_table[25] << std::endl;
    std::cout << "   cube_table[3] = " << cube_table[3] << std::endl;
    std::cout << "   cube_table[10] = " << cube_table[10] << std::endl;
    std::cout << "   factorial_table[5] = " << factorial_table[5] << std::endl;
    std::cout << "   factorial_table[10] = " << factorial_table[10] << std::endl;
    std::cout << "   fibonacci_table[10] = " << fibonacci_table[10] << std::endl;
    std::cout << "   fibonacci_table[15] = " << fibonacci_table[15] << std::endl;
    std::cout << std::endl;

    // 数学查找表
    std::cout << "2. 数学查找表:" << std::endl;
    std::cout << "   sine_table[0] = " << sine_table[0] << " (sin(0))" << std::endl;
    std::cout << "   sine_table[90] = " << sine_table[90] << " (sin(90))" << std::endl;
    std::cout << "   cosine_table[0] = " << cosine_table[0] << " (cos(0))" << std::endl;
    std::cout << "   cosine_table[90] = " << cosine_table[90] << " (cos(90))" << std::endl;
    std::cout << "   sqrt_table[4] = " << sqrt_table[4] << " (sqrt(4))" << std::endl;
    std::cout << "   sqrt_table[9] = " << sqrt_table[9] << " (sqrt(9))" << std::endl;
    std::cout << std::endl;

    // 自定义查找表
    std::cout << "3. 自定义查找表:" << std::endl;
    std::cout << "   custom_table[0] = " << custom_table[0] << " ((0+1)^2)" << std::endl;
    std::cout << "   custom_table[9] = " << custom_table[9] << " ((9+1)^2)" << std::endl;
    std::cout << "   ranged_table[0] = " << ranged_table[0] << " (0^2)" << std::endl;
    std::cout << "   ranged_table[10] = " << ranged_table[10] << " (1^2)" << std::endl;
    std::cout << std::endl;

    // 插值
    std::cout << "4. 查找表插值:" << std::endl;
    std::cout << "   sin(30.5°) ≈ " << sin_30_5 << std::endl;
    std::cout << "   最接近 1000 的平方数索引: " << nearest << std::endl;
    std::cout << std::endl;

    // 快速函数
    std::cout << "5. 快速函数（使用查找表）:" << std::endl;
    std::cout << "   fast_sin(30) = " << fast_sin(30) << std::endl;
    std::cout << "   fast_cos(60) = " << fast_cos(60) << std::endl;
    std::cout << "   fast_square(15) = " << fast_square(15) << std::endl;
    std::cout << std::endl;

    // ASCII 分类表
    std::cout << "6. ASCII 字符分类表:" << std::endl;
    std::cout << "   '0' -> " << ascii_class_table['0'] << " (数字)" << std::endl;
    std::cout << "   'A' -> " << ascii_class_table['A'] << " (大写字母)" << std::endl;
    std::cout << "   'a' -> " << ascii_class_table['a'] << " (小写字母)" << std::endl;
    std::cout << "   '!' -> " << ascii_class_table['!'] << " (其他)" << std::endl;
    std::cout << std::endl;

    // 二进制权重表
    std::cout << "7. 二进制权重表:" << std::endl;
    for (int i = 0; i < 10; ++i) {
        std::cout << "   2^" << i << " = " << binary_weight_table[i] << std::endl;
    }

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
