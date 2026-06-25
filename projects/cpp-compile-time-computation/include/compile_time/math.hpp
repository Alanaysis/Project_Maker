#pragma once
// math.hpp - 编译期数学函数
//
// 实现常用的数学函数，所有函数都是 constexpr，可以在编译期执行。
//
// 实现方法：
//   - 平方根：牛顿迭代法
//   - 幂函数：快速幂算法
//   - 三角函数：泰勒级数展开
//   - 对数函数：泰勒级数展开
//
// 使用示例：
//   constexpr double sqrt_val = ct_math::sqrt(4.0);  // 2.0
//   constexpr double sin_val = ct_math::sin(3.14159 / 2);  // ~1.0

#include <cstddef>
#include <limits>
#include <cmath>

namespace compile_time {
namespace math {

// 常量
constexpr double pi = 3.14159265358979323846;
constexpr double e = 2.71828182845904523536;

// 编译期绝对值
template<typename T>
constexpr T abs(T x) {
    return x < 0 ? -x : x;
}

// 编译期最大值
template<typename T>
constexpr T max(T a, T b) {
    return a > b ? a : b;
}

// 编译期最小值
template<typename T>
constexpr T min(T a, T b) {
    return a < b ? a : b;
}

// 编译期限制范围
template<typename T>
constexpr T clamp(T value, T low, T high) {
    return value < low ? low : (value > high ? high : value);
}

// 编译期平方根（牛顿迭代法）
constexpr double sqrt(double x) {
    if (x < 0) return 0;  // 负数返回 0
    if (x == 0) return 0;

    double guess = x / 2.0;
    for (int i = 0; i < 100; ++i) {
        double new_guess = (guess + x / guess) / 2.0;
        if (abs(new_guess - guess) < 1e-15) break;
        guess = new_guess;
    }
    return guess;
}

// 编译期立方根
constexpr double cbrt(double x) {
    if (x == 0) return 0;
    double guess = x / 3.0;
    for (int i = 0; i < 100; ++i) {
        double new_guess = (2.0 * guess + x / (guess * guess)) / 3.0;
        if (abs(new_guess - guess) < 1e-15) break;
        guess = new_guess;
    }
    return guess;
}

// 编译期幂函数（整数指数）
constexpr double pow(double base, int exp) {
    if (exp < 0) return 1.0 / pow(base, -exp);
    if (exp == 0) return 1.0;

    double result = 1.0;
    double current = base;
    int n = exp;

    while (n > 0) {
        if (n % 2 == 1) {
            result *= current;
        }
        current *= current;
        n /= 2;
    }
    return result;
}

// 编译期幂函数（浮点指数，使用近似方法）
constexpr double pow(double base, double exp) {
    if (exp == 0) return 1.0;
    if (base == 0) return 0.0;

    // 使用 e^(exp * ln(base))
    // 先计算 ln(base)，然后计算 e^(exp * ln(base))
    // 这里使用简化实现
    double result = 1.0;
    int int_exp = static_cast<int>(exp);
    double frac_exp = exp - int_exp;

    // 整数部分
    result = pow(base, int_exp);

    // 小数部分（使用泰勒级数近似）
    if (frac_exp > 0) {
        // ln(base) 的近似
        double ln_base = 0;
        double x = (base - 1.0) / (base + 1.0);
        double x2 = x * x;
        double term = x;
        for (int n = 0; n < 20; ++n) {
            ln_base += term / (2 * n + 1);
            term *= x2;
        }
        ln_base *= 2.0;

        // e^(frac_exp * ln_base) 的近似
        double exp_val = frac_exp * ln_base;
        double e_result = 1.0;
        double e_term = 1.0;
        for (int n = 1; n < 30; ++n) {
            e_term *= exp_val / n;
            e_result += e_term;
        }
        result *= e_result;
    }

    return result;
}

// 编译期阶乘
constexpr unsigned long long factorial(int n) {
    unsigned long long result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// 编译期组合数 C(n, k)
constexpr unsigned long long combination(int n, int k) {
    if (k > n) return 0;
    if (k == 0 || k == n) return 1;

    // 优化：C(n, k) = C(n, n-k)
    if (k > n - k) k = n - k;

    unsigned long long result = 1;
    for (int i = 0; i < k; ++i) {
        result *= (n - i);
        result /= (i + 1);
    }
    return result;
}

// 编译期正弦函数（泰勒级数）
constexpr double sin(double x) {
    // 归一化到 [-pi, pi]
    while (x > pi) x -= 2 * pi;
    while (x < -pi) x += 2 * pi;

    double result = 0;
    double term = x;
    for (int n = 1; n <= 20; ++n) {
        result += term;
        term *= -x * x / ((2 * n) * (2 * n + 1));
    }
    return result;
}

// 编译期余弦函数（泰勒级数）
constexpr double cos(double x) {
    // 归一化到 [-pi, pi]
    while (x > pi) x -= 2 * pi;
    while (x < -pi) x += 2 * pi;

    double result = 0;
    double term = 1.0;
    for (int n = 1; n <= 20; ++n) {
        result += term;
        term *= -x * x / ((2 * n - 1) * (2 * n));
    }
    return result;
}

// 编译期正切函数
constexpr double tan(double x) {
    return sin(x) / cos(x);
}

// 编译期自然对数（泰勒级数）
constexpr double ln(double x) {
    if (x <= 0) return 0;  // 错误处理
    if (x == 1) return 0;

    // 使用 ln(x) = 2 * [(x-1)/(x+1) + (1/3)*((x-1)/(x+1))^3 + ...]
    double y = (x - 1.0) / (x + 1.0);
    double y2 = y * y;
    double result = 0;
    double term = y;

    for (int n = 0; n < 30; ++n) {
        result += term / (2 * n + 1);
        term *= y2;
    }
    return 2.0 * result;
}

// 编译期 log2
constexpr double log2(double x) {
    return ln(x) / ln(2.0);
}

// 编译期 log10
constexpr double log10(double x) {
    return ln(x) / ln(10.0);
}

// 编译期指数函数（泰勒级数）
constexpr double exp(double x) {
    double result = 1.0;
    double term = 1.0;
    for (int n = 1; n < 30; ++n) {
        term *= x / n;
        result += term;
    }
    return result;
}

// 编译期双曲正弦
constexpr double sinh(double x) {
    return (exp(x) - exp(-x)) / 2.0;
}

// 编译期双曲余弦
constexpr double cosh(double x) {
    return (exp(x) + exp(-x)) / 2.0;
}

// 编译期双曲正切
constexpr double tanh(double x) {
    return sinh(x) / cosh(x);
}

// 编译期反正弦（近似）
constexpr double asin(double x) {
    if (x < -1 || x > 1) return 0;  // 错误处理
    if (x == 1) return pi / 2;
    if (x == -1) return -pi / 2;

    double result = x;
    double term = x;
    double x2 = x * x;
    for (int n = 1; n < 20; ++n) {
        term *= x2 * (2 * n - 1) * (2 * n - 1) / (2 * n * (2 * n + 1));
        result += term;
    }
    return result;
}

// 编译期反余弦
constexpr double acos(double x) {
    return pi / 2 - asin(x);
}

// 编译期反正切
constexpr double atan(double x) {
    if (x > 1) return pi / 2 - atan(1.0 / x);
    if (x < -1) return -pi / 2 - atan(1.0 / x);

    double result = x;
    double term = x;
    double x2 = x * x;
    for (int n = 1; n < 20; ++n) {
        term *= -x2;
        result += term / (2 * n + 1);
    }
    return result;
}

// 编译期 atan2
constexpr double atan2(double y, double x) {
    if (x > 0) return atan(y / x);
    if (x < 0 && y >= 0) return atan(y / x) + pi;
    if (x < 0 && y < 0) return atan(y / x) - pi;
    if (x == 0 && y > 0) return pi / 2;
    if (x == 0 && y < 0) return -pi / 2;
    return 0;  // x == 0 && y == 0
}

// 编译期取模
constexpr double fmod(double x, double y) {
    if (y == 0) return 0;
    return x - static_cast<int>(x / y) * y;
}

// 编译期向上取整
constexpr double ceil(double x) {
    int i = static_cast<int>(x);
    return (x > i) ? i + 1 : i;
}

// 编译期向下取整
constexpr double floor(double x) {
    int i = static_cast<int>(x);
    return (x < i) ? i - 1 : i;
}

// 编译期四舍五入
constexpr double round(double x) {
    return floor(x + 0.5);
}

// 编译期判断是否为 NaN
constexpr bool isnan(double x) {
    return x != x;
}

// 编译期判断是否为无穷大
constexpr bool isinf(double x) {
    return x == x && x - x != 0;
}

} // namespace math
} // namespace compile_time
