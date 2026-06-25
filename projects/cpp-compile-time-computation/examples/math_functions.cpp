// math_functions.cpp - 编译期数学函数示例
//
// 本文件展示编译期数学函数的用法，包括：
//   1. 基本数学函数
//   2. 三角函数
//   3. 指数和对数函数
//   4. 查找表生成
//
// 编译命令：
//   g++ -std=c++20 -I include examples/math_functions.cpp -o math_functions

#include <iostream>
#include <iomanip>
#include "compile_time/math.hpp"
#include "compile_time/lookup.hpp"

// ============================================================================
// 第一部分：基本数学函数
// ============================================================================

// 平方根
constexpr double sqrt_4 = compile_time::math::sqrt(4.0);      // 2.0
constexpr double sqrt_9 = compile_time::math::sqrt(9.0);      // 3.0
constexpr double sqrt_2 = compile_time::math::sqrt(2.0);      // ~1.414

// 立方根
constexpr double cbrt_8 = compile_time::math::cbrt(8.0);      // 2.0
constexpr double cbrt_27 = compile_time::math::cbrt(27.0);    // 3.0

// 幂函数
constexpr double pow_2_10 = compile_time::math::pow(2, 10);   // 1024
constexpr double pow_3_3 = compile_time::math::pow(3, 3);     // 27

// 阶乘
constexpr unsigned long long fact_5 = compile_time::math::factorial(5);    // 120
constexpr unsigned long long fact_10 = compile_time::math::factorial(10);  // 3628800

// 组合数
constexpr unsigned long long comb_5_2 = compile_time::math::combination(5, 2);  // 10
constexpr unsigned long long comb_10_3 = compile_time::math::combination(10, 3); // 120

// ============================================================================
// 第二部分：三角函数
// ============================================================================

// 正弦函数
constexpr double sin_0 = compile_time::math::sin(0.0);        // 0.0
constexpr double sin_pi2 = compile_time::math::sin(compile_time::math::pi / 2);   // ~1.0
constexpr double sin_pi = compile_time::math::sin(compile_time::math::pi);        // ~0.0

// 余弦函数
constexpr double cos_0 = compile_time::math::cos(0.0);        // 1.0
constexpr double cos_pi2 = compile_time::math::cos(compile_time::math::pi / 2);   // ~0.0
constexpr double cos_pi = compile_time::math::cos(compile_time::math::pi);        // ~-1.0

// 正切函数
constexpr double tan_0 = compile_time::math::tan(0.0);        // 0.0
constexpr double tan_pi4 = compile_time::math::tan(compile_time::math::pi / 4);   // ~1.0

// 反三角函数
constexpr double asin_0 = compile_time::math::asin(0.0);      // 0.0
constexpr double asin_1 = compile_time::math::asin(1.0);      // pi/2
constexpr double acos_0 = compile_time::math::acos(0.0);      // pi/2
constexpr double acos_1 = compile_time::math::acos(1.0);      // 0.0
constexpr double atan_0 = compile_time::math::atan(0.0);      // 0.0
constexpr double atan_1 = compile_time::math::atan(1.0);      // pi/4

// ============================================================================
// 第三部分：指数和对数函数
// ============================================================================

// 指数函数
constexpr double exp_0 = compile_time::math::exp(0.0);        // 1.0
constexpr double exp_1 = compile_time::math::exp(1.0);        // ~2.718
constexpr double exp_2 = compile_time::math::exp(2.0);        // ~7.389

// 自然对数
constexpr double ln_1 = compile_time::math::ln(1.0);          // 0.0
constexpr double ln_e = compile_time::math::ln(compile_time::math::e);            // ~1.0

// log2
constexpr double log2_1 = compile_time::math::log2(1.0);      // 0.0
constexpr double log2_2 = compile_time::math::log2(2.0);      // 1.0
constexpr double log2_8 = compile_time::math::log2(8.0);      // 3.0

// log10
constexpr double log10_1 = compile_time::math::log10(1.0);    // 0.0
constexpr double log10_10 = compile_time::math::log10(10.0);  // 1.0
constexpr double log10_100 = compile_time::math::log10(100.0); // 2.0

// ============================================================================
// 第四部分：查找表生成
// ============================================================================

// 正弦查找表（0-359度）
constexpr auto sine_table = compile_time::lookup::make_sine_table();

// 余弦查找表（0-359度）
constexpr auto cosine_table = compile_time::lookup::make_cosine_table();

// 平方查找表
constexpr auto square_table = compile_time::lookup::make_square_table<100>();

// 平方根查找表
constexpr auto sqrt_table = compile_time::lookup::make_sqrt_table();

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 基本数学函数
static_assert(compile_time::math::abs(sqrt_4 - 2.0) < 1e-10);
static_assert(compile_time::math::abs(sqrt_9 - 3.0) < 1e-10);
static_assert(compile_time::math::abs(sqrt_2 - 1.4142135623730951) < 1e-10);

static_assert(compile_time::math::abs(cbrt_8 - 2.0) < 1e-10);
static_assert(compile_time::math::abs(cbrt_27 - 3.0) < 1e-10);

static_assert(pow_2_10 == 1024);
static_assert(pow_3_3 == 27);

static_assert(fact_5 == 120);
static_assert(fact_10 == 3628800);

static_assert(comb_5_2 == 10);
static_assert(comb_10_3 == 120);

// 三角函数
static_assert(compile_time::math::abs(sin_0) < 1e-10);
static_assert(compile_time::math::abs(sin_pi2 - 1.0) < 1e-10);
static_assert(compile_time::math::abs(sin_pi) < 1e-10);

static_assert(compile_time::math::abs(cos_0 - 1.0) < 1e-10);
static_assert(compile_time::math::abs(cos_pi2) < 1e-10);
static_assert(compile_time::math::abs(cos_pi + 1.0) < 1e-10);

// 指数和对数
static_assert(compile_time::math::abs(exp_0 - 1.0) < 1e-10);
static_assert(compile_time::math::abs(ln_1) < 1e-10);

static_assert(compile_time::math::abs(log2_2 - 1.0) < 1e-6);
static_assert(compile_time::math::abs(log2_8 - 3.0) < 1e-6);

// 查找表
static_assert(compile_time::math::abs(sine_table[0]) < 1e-10);           // sin(0) = 0
static_assert(compile_time::math::abs(sine_table[90] - 1.0) < 1e-10);    // sin(90) = 1
static_assert(compile_time::math::abs(cosine_table[0] - 1.0) < 1e-10);   // cos(0) = 1
static_assert(compile_time::math::abs(cosine_table[90]) < 1e-10);         // cos(90) = 0

static_assert(square_table[10] == 100);
static_assert(square_table[25] == 625);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "=== 编译期数学函数示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本数学函数
    std::cout << "1. 基本数学函数:" << std::endl;
    std::cout << "   sqrt(4.0) = " << sqrt_4 << std::endl;
    std::cout << "   sqrt(9.0) = " << sqrt_9 << std::endl;
    std::cout << "   sqrt(2.0) = " << sqrt_2 << std::endl;
    std::cout << "   cbrt(8.0) = " << cbrt_8 << std::endl;
    std::cout << "   cbrt(27.0) = " << cbrt_27 << std::endl;
    std::cout << "   2^10 = " << pow_2_10 << std::endl;
    std::cout << "   3^3 = " << pow_3_3 << std::endl;
    std::cout << "   5! = " << fact_5 << std::endl;
    std::cout << "   10! = " << fact_10 << std::endl;
    std::cout << "   C(5,2) = " << comb_5_2 << std::endl;
    std::cout << "   C(10,3) = " << comb_10_3 << std::endl;
    std::cout << std::endl;

    // 三角函数
    std::cout << "2. 三角函数:" << std::endl;
    std::cout << "   sin(0) = " << sin_0 << std::endl;
    std::cout << "   sin(pi/2) = " << sin_pi2 << std::endl;
    std::cout << "   sin(pi) = " << sin_pi << std::endl;
    std::cout << "   cos(0) = " << cos_0 << std::endl;
    std::cout << "   cos(pi/2) = " << cos_pi2 << std::endl;
    std::cout << "   cos(pi) = " << cos_pi << std::endl;
    std::cout << "   tan(0) = " << tan_0 << std::endl;
    std::cout << "   tan(pi/4) = " << tan_pi4 << std::endl;
    std::cout << std::endl;

    // 反三角函数
    std::cout << "3. 反三角函数:" << std::endl;
    std::cout << "   asin(0) = " << asin_0 << std::endl;
    std::cout << "   asin(1) = " << asin_1 << std::endl;
    std::cout << "   acos(0) = " << acos_0 << std::endl;
    std::cout << "   acos(1) = " << acos_1 << std::endl;
    std::cout << "   atan(0) = " << atan_0 << std::endl;
    std::cout << "   atan(1) = " << atan_1 << std::endl;
    std::cout << std::endl;

    // 指数和对数
    std::cout << "4. 指数和对数:" << std::endl;
    std::cout << "   exp(0) = " << exp_0 << std::endl;
    std::cout << "   exp(1) = " << exp_1 << std::endl;
    std::cout << "   exp(2) = " << exp_2 << std::endl;
    std::cout << "   ln(1) = " << ln_1 << std::endl;
    std::cout << "   ln(e) = " << ln_e << std::endl;
    std::cout << "   log2(2) = " << log2_2 << std::endl;
    std::cout << "   log2(8) = " << log2_8 << std::endl;
    std::cout << "   log10(10) = " << log10_10 << std::endl;
    std::cout << "   log10(100) = " << log10_100 << std::endl;
    std::cout << std::endl;

    // 查找表
    std::cout << "5. 查找表:" << std::endl;
    std::cout << "   sine_table[0] = " << sine_table[0] << " (sin(0))" << std::endl;
    std::cout << "   sine_table[90] = " << sine_table[90] << " (sin(90))" << std::endl;
    std::cout << "   cosine_table[0] = " << cosine_table[0] << " (cos(0))" << std::endl;
    std::cout << "   cosine_table[90] = " << cosine_table[90] << " (cos(90))" << std::endl;
    std::cout << "   square_table[10] = " << square_table[10] << std::endl;
    std::cout << "   square_table[25] = " << square_table[25] << std::endl;
    std::cout << "   sqrt_table[4] = " << sqrt_table[4] << " (sqrt(4))" << std::endl;
    std::cout << "   sqrt_table[9] = " << sqrt_table[9] << " (sqrt(9))" << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
