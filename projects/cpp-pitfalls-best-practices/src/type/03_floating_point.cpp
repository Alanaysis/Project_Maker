/**
 * @file 03_floating_point.cpp
 * @brief 浮点精度问题示例
 *
 * 浮点精度问题：浮点数无法精确表示某些小数
 * 危害：计算误差累积、比较失败、逻辑错误
 */

#include <iostream>
#include <iomanip>
#include <cmath>
#include <limits>
#include <cfenv>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：直接比较浮点数
 *
 * 问题：浮点数计算有精度误差，直接比较可能失败
 */
void bad_float_comparison() {
    double a = 0.1 + 0.2;
    double b = 0.3;

    std::cout << std::setprecision(20);
    std::cout << "a = " << a << std::endl;
    std::cout << "b = " << b << std::endl;
    std::cout << "a == b ? " << (a == b ? "true" : "false") << std::endl;
    // 实际上 a != b，因为 0.1 + 0.2 != 0.3 精确
}

/**
 * 错误示例 2：累积误差
 *
 * 问题：多次运算导致误差累积
 */
void bad_accumulation() {
    float sum = 0.0f;
    for (int i = 0; i < 1000000; i++) {
        sum += 0.000001f;
    }
    std::cout << "期望: 1.0, 实际: " << sum << std::endl;
    // 实际值与 1.0 有显著差异
}

/**
 * 错误示例 3：大数吃小数
 *
 * 问题：大数与小数相加时，小数可能被忽略
 */
void bad_large_small() {
    double large = 1e16;
    double small = 1.0;
    double result = large + small - large;
    std::cout << "期望: 1.0, 实际: " << result << std::endl;
    // 结果可能是 0.0
}

/**
 * 错误示例 4：除以接近零的数
 *
 * 问题：可能导致无穷大或 NaN
 */
void bad_divide_near_zero() {
    double a = 1.0;
    double b = 1e-300;
    double result = a / b;
    std::cout << "result = " << result << std::endl;
    // 可能溢出到 inf
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 epsilon 比较
 *
 * 解决方案：使用误差范围比较浮点数
 */
bool almost_equal(double a, double b, double epsilon = 1e-9) {
    return std::abs(a - b) < epsilon;
}

void good_epsilon_comparison() {
    double a = 0.1 + 0.2;
    double b = 0.3;

    if (almost_equal(a, b)) {
        std::cout << "a 约等于 b" << std::endl;
    } else {
        std::cout << "a 不等于 b" << std::endl;
    }
}

/**
 * 正确示例 2：使用相对误差比较
 *
 * 解决方案：对于大数使用相对误差
 */
bool almost_equal_relative(double a, double b, double rel_epsilon = 1e-9) {
    double diff = std::abs(a - b);
    double largest = std::max(std::abs(a), std::abs(b));
    return diff <= largest * rel_epsilon;
}

void good_relative_comparison() {
    double a = 1e10 + 1.0;
    double b = 1e10;

    if (almost_equal_relative(a, b)) {
        std::cout << "a 约等于 b（相对误差）" << std::endl;
    } else {
        std::cout << "a 不等于 b" << std::endl;
    }
}

/**
 * 正确示例 3：使用 Kahan 求和算法
 *
 * 解决方案：减少累积误差
 */
double kahan_sum(const double* data, size_t count) {
    double sum = 0.0;
    double c = 0.0;  // 补偿变量

    for (size_t i = 0; i < count; i++) {
        double y = data[i] - c;
        double t = sum + y;
        c = (t - sum) - y;
        sum = t;
    }
    return sum;
}

void good_kahan_sum() {
    double values[3] = {1.0, 1e-16, -1e-16};
    double result = kahan_sum(values, 3);
    std::cout << "Kahan 求和结果: " << result << std::endl;
}

/**
 * 正确示例 4：使用整数运算
 *
 * 解决方案：对于货币等场景使用整数
 */
void good_integer_currency() {
    // 使用分而非元
    int price_cents = 199;  // 1.99 元
    int quantity = 3;
    int total_cents = price_cents * quantity;
    std::cout << "总价: " << total_cents / 100 << "."
              << std::setfill('0') << std::setw(2)
              << total_cents % 100 << " 元" << std::endl;
}

/**
 * 正确示例 5：检查浮点异常
 *
 * 解决方案：启用浮点异常检查
 */
void good_check_exceptions() {
    // 清除浮点异常标志
    std::feclearexcept(FE_ALL_EXCEPT);

    double a = 1.0;
    double b = 0.0;
    double result = a / b;

    // 检查异常
    if (std::fetestexcept(FE_DIVBYZERO)) {
        std::cout << "检测到除零异常" << std::endl;
    }
    if (std::fetestexcept(FE_OVERFLOW)) {
        std::cout << "检测到溢出异常" << std::endl;
    }
    if (std::fetestexcept(FE_INVALID)) {
        std::cout << "检测到无效操作异常" << std::endl;
    }

    std::cout << "result = " << result << std::endl;
}

/**
 * 正确示例 6：使用 std::numeric_limits
 *
 * 解决方案：使用类型特性获取精度信息
 */
void good_numeric_limits() {
    std::cout << "float 精度: " << std::numeric_limits<float>::digits10
              << " 位十进制数字" << std::endl;
    std::cout << "double 精度: " << std::numeric_limits<double>::digits10
              << " 位十进制数字" << std::endl;
    std::cout << "float epsilon: " << std::numeric_limits<float>::epsilon()
              << std::endl;
    std::cout << "double epsilon: " << std::numeric_limits<double>::epsilon()
              << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 浮点精度问题示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 直接比较浮点数" << std::endl;
    bad_float_comparison();
    std::cout << "问题：浮点数计算有精度误差" << std::endl;
    std::cout << std::endl;

    std::cout << "[错误示例 2] 累积误差" << std::endl;
    bad_accumulation();
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 epsilon 比较" << std::endl;
    good_epsilon_comparison();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用相对误差比较" << std::endl;
    good_relative_comparison();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 Kahan 求和" << std::endl;
    good_kahan_sum();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用整数运算" << std::endl;
    good_integer_currency();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 检查浮点异常" << std::endl;
    good_check_exceptions();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 std::numeric_limits" << std::endl;
    good_numeric_limits();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
