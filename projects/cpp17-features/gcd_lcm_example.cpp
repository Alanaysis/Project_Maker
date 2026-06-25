/**
 * @file gcd_lcm_example.cpp
 * @brief C++17 std::gcd 和 std::lcm 示例
 *
 * C++17 引入了标准的数学函数 std::gcd（最大公约数）和 std::lcm（最小公倍数）。
 * 这些函数在数论、密码学、图形学等领域有广泛应用。
 *
 * 主要优势：
 * 1. 标准化 - 无需自己实现或依赖第三方库
 * 2. 类型安全 - 支持各种整数类型
 * 3. 高效实现 - 编译器优化
 */

#include <iostream>
#include <numeric>
#include <vector>
#include <string>
#include <algorithm>
#include <functional>
#include <cassert>
#include <chrono>

// 1. 基本使用
void basic_example() {
    std::cout << "\n[基本使用]" << std::endl;

    // 计算最大公约数
    int a = 12, b = 18;
    int gcd_result = std::gcd(a, b);
    std::cout << "gcd(" << a << ", " << b << ") = " << gcd_result << std::endl;

    // 计算最小公倍数
    int lcm_result = std::lcm(a, b);
    std::cout << "lcm(" << a << ", " << b << ") = " << lcm_result << std::endl;

    // 验证关系: gcd(a,b) * lcm(a,b) = a * b
    std::cout << "Verification: " << gcd_result << " * " << lcm_result
              << " = " << gcd_result * lcm_result << std::endl;
    std::cout << "Expected: " << a << " * " << b << " = " << a * b << std::endl;
}

// 2. 不同整数类型
void type_example() {
    std::cout << "\n[不同整数类型]" << std::endl;

    // int
    std::cout << "int: gcd(24, 36) = " << std::gcd(24, 36) << std::endl;

    // long
    std::cout << "long: gcd(1000000L, 750000L) = " << std::gcd(1000000L, 750000L) << std::endl;

    // long long
    std::cout << "long long: gcd(123456789LL, 987654321LL) = "
              << std::gcd(123456789LL, 987654321LL) << std::endl;

    // unsigned
    std::cout << "unsigned: gcd(100u, 75u) = " << std::gcd(100u, 75u) << std::endl;

    // 混合类型
    int x = 12;
    long y = 18L;
    auto result = std::gcd(x, y);
    std::cout << "mixed: gcd(int, long) = " << result << std::endl;
}

// 3. 边界情况
void edge_cases_example() {
    std::cout << "\n[边界情况]" << std::endl;

    // 零值处理
    std::cout << "gcd(0, 5) = " << std::gcd(0, 5) << std::endl;
    std::cout << "gcd(5, 0) = " << std::gcd(5, 0) << std::endl;
    std::cout << "gcd(0, 0) = " << std::gcd(0, 0) << std::endl;

    std::cout << "lcm(0, 5) = " << std::lcm(0, 5) << std::endl;
    std::cout << "lcm(5, 0) = " << std::lcm(5, 0) << std::endl;
    std::cout << "lcm(0, 0) = " << std::lcm(0, 0) << std::endl;

    // 相同值
    std::cout << "gcd(7, 7) = " << std::gcd(7, 7) << std::endl;
    std::cout << "lcm(7, 7) = " << std::lcm(7, 7) << std::endl;

    // 互质数
    std::cout << "gcd(7, 13) = " << std::gcd(7, 13) << std::endl;
    std::cout << "lcm(7, 13) = " << std::lcm(7, 13) << std::endl;

    // 负数处理（绝对值）
    std::cout << "gcd(-12, 18) = " << std::gcd(-12, 18) << std::endl;
    std::cout << "gcd(12, -18) = " << std::gcd(12, -18) << std::endl;
    std::cout << "gcd(-12, -18) = " << std::gcd(-12, -18) << std::endl;
}

// 4. 多个数的 GCD 和 LCM
template <typename T>
T gcd_multiple(const std::vector<T>& numbers) {
    if (numbers.empty()) return 0;
    T result = numbers[0];
    for (size_t i = 1; i < numbers.size(); ++i) {
        result = std::gcd(result, numbers[i]);
    }
    return result;
}

template <typename T>
T lcm_multiple(const std::vector<T>& numbers) {
    if (numbers.empty()) return 0;
    T result = numbers[0];
    for (size_t i = 1; i < numbers.size(); ++i) {
        result = std::lcm(result, numbers[i]);
    }
    return result;
}

void multiple_numbers_example() {
    std::cout << "\n[多个数的 GCD 和 LCM]" << std::endl;

    std::vector<int> numbers = {12, 18, 24, 36};

    std::cout << "Numbers: ";
    for (int n : numbers) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    std::cout << "GCD: " << gcd_multiple(numbers) << std::endl;
    std::cout << "LCM: " << lcm_multiple(numbers) << std::endl;

    // 验证
    int gcd = gcd_multiple(numbers);
    int lcm = lcm_multiple(numbers);
    std::cout << "Verification: " << gcd << " divides all numbers: ";
    bool divides_all = true;
    for (int n : numbers) {
        if (n % gcd != 0) {
            divides_all = false;
            break;
        }
    }
    std::cout << (divides_all ? "true" : "false") << std::endl;

    std::cout << "All numbers divide " << lcm << ": ";
    bool all_divide = true;
    for (int n : numbers) {
        if (lcm % n != 0) {
            all_divide = false;
            break;
        }
    }
    std::cout << (all_divide ? "true" : "false") << std::endl;
}

// 5. 分数运算
struct Fraction {
    int numerator;
    int denominator;

    Fraction(int n, int d) : numerator(n), denominator(d) {
        simplify();
    }

    void simplify() {
        int g = std::gcd(std::abs(numerator), std::abs(denominator));
        numerator /= g;
        denominator /= g;
        if (denominator < 0) {
            numerator = -numerator;
            denominator = -denominator;
        }
    }

    Fraction operator+(const Fraction& other) const {
        int lcm_val = std::lcm(denominator, other.denominator);
        int new_num = numerator * (lcm_val / denominator) +
                      other.numerator * (lcm_val / other.denominator);
        return Fraction(new_num, lcm_val);
    }

    Fraction operator*(const Fraction& other) const {
        return Fraction(numerator * other.numerator,
                       denominator * other.denominator);
    }

    friend std::ostream& operator<<(std::ostream& os, const Fraction& f) {
        return os << f.numerator << "/" << f.denominator;
    }
};

void fraction_example() {
    std::cout << "\n[分数运算]" << std::endl;

    Fraction f1(1, 3);
    Fraction f2(1, 6);

    std::cout << f1 << " + " << f2 << " = " << (f1 + f2) << std::endl;

    Fraction f3(2, 5);
    Fraction f4(3, 4);

    std::cout << f3 << " * " << f4 << " = " << (f3 * f4) << std::endl;

    // 化简
    Fraction f5(6, 8);
    std::cout << "6/8 simplified = " << f5 << std::endl;

    Fraction f6(-4, 6);
    std::cout << "-4/6 simplified = " << f6 << std::endl;
}

// 6. 密码学应用：RSA 算法中的互质检查
bool are_coprime(int a, int b) {
    return std::gcd(a, b) == 1;
}

void cryptography_example() {
    std::cout << "\n[密码学应用]" << std::endl;

    // 检查互质
    std::cout << "gcd(7, 13) = " << std::gcd(7, 13) << " (coprime: "
              << (are_coprime(7, 13) ? "true" : "false") << ")" << std::endl;

    std::cout << "gcd(6, 9) = " << std::gcd(6, 9) << " (coprime: "
              << (are_coprime(6, 9) ? "true" : "false") << ")" << std::endl;

    // RSA 中选择公钥指数 e
    // e 必须与 phi(n) = (p-1)(q-1) 互质
    int p = 61, q = 53;
    int n = p * q;
    int phi_n = (p - 1) * (q - 1);

    std::cout << "p = " << p << ", q = " << q << std::endl;
    std::cout << "n = " << n << ", phi(n) = " << phi_n << std::endl;

    // 找到合适的 e
    std::vector<int> candidates = {3, 5, 7, 11, 13, 17, 19, 23};
    for (int e : candidates) {
        if (are_coprime(e, phi_n)) {
            std::cout << "Found e = " << e << " (gcd(e, phi(n)) = "
                      << std::gcd(e, phi_n) << ")" << std::endl;
            break;
        }
    }
}

// 7. 图形学应用：像素网格对齐
void graphics_example() {
    std::cout << "\n[图形学应用]" << std::endl;

    // 计算两个尺寸的最大公约数，用于网格对齐
    int width = 1920;
    int height = 1080;

    int gcd_wh = std::gcd(width, height);
    std::cout << "Resolution: " << width << "x" << height << std::endl;
    std::cout << "GCD: " << gcd_wh << std::endl;
    std::cout << "Aspect ratio: " << width / gcd_wh << ":" << height / gcd_wh << std::endl;

    // 计算最小公倍数，用于纹理平铺
    int tile_width = 64;
    int tile_height = 48;

    int lcm_tile = std::lcm(tile_width, tile_height);
    std::cout << "Tile size: " << tile_width << "x" << tile_height << std::endl;
    std::cout << "LCM: " << lcm_tile << std::endl;
    std::cout << "Square tile size: " << lcm_tile << "x" << lcm_tile << std::endl;
}

// 8. 音乐理论：节拍计算
void music_example() {
    std::cout << "\n[音乐理论]" << std::endl;

    // 计算两个节拍的最小公倍数
    int beat1 = 3;  // 3/4 拍
    int beat2 = 4;  // 4/4 拍

    int lcm_beat = std::lcm(beat1, beat2);
    std::cout << "Beat 1: " << beat1 << "/4" << std::endl;
    std::cout << "Beat 2: " << beat2 << "/4" << std::endl;
    std::cout << "LCM: " << lcm_beat << "/4" << std::endl;
    std::cout << "They align every " << lcm_beat << " beats" << std::endl;

    // 计算音符频率比
    int freq1 = 440;  // A4
    int freq2 = 880;  // A5

    int gcd_freq = std::gcd(freq1, freq2);
    std::cout << "Frequency ratio: " << freq1 / gcd_freq << ":" << freq2 / gcd_freq << std::endl;
}

// 9. 时间计算：周期性事件
void time_example() {
    std::cout << "\n[时间计算]" << std::endl;

    // 两个周期性事件同时发生的周期
    int period1 = 6;   // 每6天
    int period2 = 8;   // 每8天

    int lcm_period = std::lcm(period1, period2);
    std::cout << "Event 1: every " << period1 << " days" << std::endl;
    std::cout << "Event 2: every " << period2 << " days" << std::endl;
    std::cout << "Both events align every " << lcm_period << " days" << std::endl;

    // 齿轮比计算
    int gear1 = 12;
    int gear2 = 18;

    int gcd_gear = std::gcd(gear1, gear2);
    std::cout << "Gear 1: " << gear1 << " teeth" << std::endl;
    std::cout << "Gear 2: " << gear2 << " teeth" << std::endl;
    std::cout << "Gear ratio: " << gear1 / gcd_gear << ":" << gear2 / gcd_gear << std::endl;
}

// 10. 性能测试
void performance_example() {
    std::cout << "\n[性能测试]" << std::endl;

    // 测试性能
    const int iterations = 1000000;
    int sum = 0;

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        sum += std::gcd(i + 1, i + 2);
    }
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "Time for " << iterations << " GCD calculations: "
              << duration.count() << " ms" << std::endl;
    std::cout << "Sum (to prevent optimization): " << sum << std::endl;
}

// 11. 自定义 GCD 实现（对比）
template <typename T>
T custom_gcd(T a, T b) {
    a = std::abs(a);
    b = std::abs(b);
    while (b != 0) {
        T temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

void custom_implementation_example() {
    std::cout << "\n[自定义实现对比]" << std::endl;

    int a = 48, b = 36;

    std::cout << "std::gcd(" << a << ", " << b << ") = " << std::gcd(a, b) << std::endl;
    std::cout << "custom_gcd(" << a << ", " << b << ") = " << custom_gcd(a, b) << std::endl;

    // 验证一致性
    assert(std::gcd(a, b) == custom_gcd(a, b));
    std::cout << "Both implementations produce the same result" << std::endl;
}

// 12. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 使用 std::gcd 和 std::lcm 代替手动实现" << std::endl;
    std::cout << "2. 注意处理零值和负数" << std::endl;
    std::cout << "3. 对于多个数，使用循环或折叠表达式" << std::endl;
    std::cout << "4. 在分数运算中使用 gcd 化简" << std::endl;
    std::cout << "5. 在周期性问题中使用 lcm" << std::endl;
}

// 主示例函数
void gcd_lcm_example() {
    std::cout << "=== std::gcd 和 std::lcm ===" << std::endl;

    basic_example();
    type_example();
    edge_cases_example();
    multiple_numbers_example();
    fraction_example();
    cryptography_example();
    graphics_example();
    music_example();
    time_example();
    performance_example();
    custom_implementation_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    gcd_lcm_example();
    return 0;
}
#endif
