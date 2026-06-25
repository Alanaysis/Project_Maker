/**
 * @file constexpr_example.cpp
 * @brief C++23 constexpr 扩展示例
 *
 * C++23 扩展了 constexpr 的支持，允许更多的编译期计算。
 *
 * 主要特点：
 * - 更多标准库函数支持 constexpr
 * - 支持更多的编译期操作
 * - 支持字符串字面量
 * - 支持更多的容器操作
 *
 * 编译命令：
 * g++ -std=c++23 -o constexpr_example constexpr_example.cpp
 */

#include <iostream>
#include <array>
#include <string>
#include <algorithm>
#include <numeric>
#include <cmath>

// ========== 1. 基本 constexpr 函数 ==========

constexpr int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

constexpr int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

void basic_constexpr() {
    std::cout << "=== 基本 constexpr 函数 ===" << std::endl;

    // 编译期计算
    constexpr int fact5 = factorial(5);
    constexpr int fib10 = fibonacci(10);

    std::cout << "5! = " << fact5 << std::endl;
    std::cout << "fib(10) = " << fib10 << std::endl;
}

// ========== 2. constexpr 数组操作 ==========

constexpr auto create_array() {
    std::array<int, 10> arr{};
    for (int i = 0; i < 10; ++i) {
        arr[i] = i * i;
    }
    return arr;
}

constexpr int sum_array(const std::array<int, 10>& arr) {
    int sum = 0;
    for (int val : arr) {
        sum += val;
    }
    return sum;
}

void array_operations() {
    std::cout << "\n=== constexpr 数组操作 ===" << std::endl;

    // 编译期创建和操作数组
    constexpr auto squares = create_array();
    constexpr int total = sum_array(squares);

    std::cout << "Squares: ";
    for (int val : squares) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
    std::cout << "Total: " << total << std::endl;
}

// ========== 3. constexpr 字符串操作 ==========

constexpr size_t string_length(const char* str) {
    size_t len = 0;
    while (str[len] != '\0') {
        ++len;
    }
    return len;
}

constexpr bool is_palindrome(const char* str) {
    size_t len = string_length(str);
    for (size_t i = 0; i < len / 2; ++i) {
        if (str[i] != str[len - 1 - i]) {
            return false;
        }
    }
    return true;
}

void string_operations() {
    std::cout << "\n=== constexpr 字符串操作 ===" << std::endl;

    // 编译期字符串操作
    constexpr size_t len = string_length("Hello");
    constexpr bool pal1 = is_palindrome("racecar");
    constexpr bool pal2 = is_palindrome("hello");

    std::cout << "Length of 'Hello': " << len << std::endl;
    std::cout << "'racecar' is palindrome: " << (pal1 ? "yes" : "no") << std::endl;
    std::cout << "'hello' is palindrome: " << (pal2 ? "yes" : "no") << std::endl;
}

// ========== 4. constexpr 数学运算 ==========

constexpr double power(double base, int exp) {
    double result = 1.0;
    for (int i = 0; i < exp; ++i) {
        result *= base;
    }
    return result;
}

constexpr double sqrt_approx(double x, int iterations) {
    double guess = x / 2.0;
    for (int i = 0; i < iterations; ++i) {
        guess = (guess + x / guess) / 2.0;
    }
    return guess;
}

void math_operations() {
    std::cout << "\n=== constexpr 数学运算 ===" << std::endl;

    // 编译期数学运算
    constexpr double pow2_10 = power(2, 10);
    constexpr double sqrt2 = sqrt_approx(2.0, 10);

    std::cout << "2^10 = " << pow2_10 << std::endl;
    std::cout << "sqrt(2) ≈ " << sqrt2 << std::endl;
}

// ========== 5. constexpr 算法 ==========

constexpr auto sort_array(std::array<int, 5> arr) {
    // 简单的冒泡排序
    for (size_t i = 0; i < arr.size() - 1; ++i) {
        for (size_t j = 0; j < arr.size() - i - 1; ++j) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
    return arr;
}

constexpr int find_max(const std::array<int, 5>& arr) {
    int max_val = arr[0];
    for (int val : arr) {
        if (val > max_val) {
            max_val = val;
        }
    }
    return max_val;
}

void algorithm_example() {
    std::cout << "\n=== constexpr 算法 ===" << std::endl;

    // 编译期排序
    constexpr std::array<int, 5> data = {5, 2, 8, 1, 9};
    constexpr auto sorted = sort_array(data);
    constexpr int max_val = find_max(data);

    std::cout << "Original: ";
    for (int val : data) std::cout << val << " ";
    std::cout << std::endl;

    std::cout << "Sorted: ";
    for (int val : sorted) std::cout << val << " ";
    std::cout << std::endl;

    std::cout << "Max: " << max_val << std::endl;
}

// ========== 6. constexpr 查找表 ==========

constexpr auto generate_sin_table() {
    std::array<double, 360> table{};
    for (int i = 0; i < 360; ++i) {
        // 简单的正弦近似
        double x = i * 3.14159265358979 / 180.0;
        table[i] = x - (x * x * x) / 6.0 + (x * x * x * x * x) / 120.0;
    }
    return table;
}

void lookup_table() {
    std::cout << "\n=== constexpr 查找表 ===" << std::endl;

    // 编译期生成查找表
    constexpr auto sin_table = generate_sin_table();

    std::cout << "Sin table (first 10 entries):" << std::endl;
    for (int i = 0; i < 10; ++i) {
        std::cout << "  sin(" << i << "°) ≈ " << sin_table[i] << std::endl;
    }
}

// ========== 7. constexpr 编译期验证 ==========

constexpr bool is_prime(int n) {
    if (n <= 1) return false;
    if (n <= 3) return true;
    if (n % 2 == 0 || n % 3 == 0) return false;
    for (int i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) {
            return false;
        }
    }
    return true;
}

constexpr auto generate_primes(int max_n) {
    std::array<int, 100> primes{};
    int count = 0;
    for (int i = 2; i <= max_n && count < 100; ++i) {
        if (is_prime(i)) {
            primes[count++] = i;
        }
    }
    return primes;
}

void compile_time_validation() {
    std::cout << "\n=== constexpr 编译期验证 ===" << std::endl;

    // 编译期素数检测
    constexpr bool prime7 = is_prime(7);
    constexpr bool prime10 = is_prime(10);

    std::cout << "7 is prime: " << (prime7 ? "yes" : "no") << std::endl;
    std::cout << "10 is prime: " << (prime10 ? "yes" : "no") << std::endl;

    // 编译期生成素数表
    constexpr auto primes = generate_primes(50);
    std::cout << "Primes up to 50: ";
    for (int p : primes) {
        if (p == 0) break;
        std::cout << p << " ";
    }
    std::cout << std::endl;
}

// ========== 8. constexpr 类 ==========

class ConstexprPoint {
private:
    int x_, y_;

public:
    constexpr ConstexprPoint(int x, int y) : x_(x), y_(y) {}

    constexpr int x() const { return x_; }
    constexpr int y() const { return y_; }

    constexpr double distance_to(const ConstexprPoint& other) const {
        double dx = x_ - other.x_;
        double dy = y_ - other.y_;
        return sqrt_approx(dx * dx + dy * dy, 10);
    }

    constexpr ConstexprPoint midpoint(const ConstexprPoint& other) const {
        return ConstexprPoint((x_ + other.x_) / 2, (y_ + other.y_) / 2);
    }
};

void constexpr_class() {
    std::cout << "\n=== constexpr 类 ===" << std::endl;

    // 编译期类操作
    constexpr ConstexprPoint p1(0, 0);
    constexpr ConstexprPoint p2(3, 4);
    constexpr double dist = p1.distance_to(p2);
    constexpr ConstexprPoint mid = p1.midpoint(p2);

    std::cout << "Distance from (0,0) to (3,4): " << dist << std::endl;
    std::cout << "Midpoint: (" << mid.x() << "," << mid.y() << ")" << std::endl;
}

// ========== 9. constexpr 容器操作 ==========

constexpr auto filter_array(const std::array<int, 10>& arr, int threshold) {
    std::array<int, 10> result{};
    int count = 0;
    for (int val : arr) {
        if (val > threshold) {
            result[count++] = val;
        }
    }
    return result;
}

void container_operations() {
    std::cout << "\n=== constexpr 容器操作 ===" << std::endl;

    // 编译期容器操作
    constexpr std::array<int, 10> data = {1, 5, 3, 8, 2, 9, 4, 7, 6, 10};
    constexpr auto filtered = filter_array(data, 5);

    std::cout << "Original: ";
    for (int val : data) std::cout << val << " ";
    std::cout << std::endl;

    std::cout << "Filtered (>5): ";
    for (int val : filtered) {
        if (val == 0) break;
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ========== 10. constexpr 综合示例 ==========

constexpr auto compile_time_computation() {
    // 编译期综合计算
    constexpr int n = 10;
    constexpr auto fib_n = fibonacci(n);
    constexpr auto fact_n = factorial(n);
    constexpr auto prime_n = is_prime(n);

    return std::make_tuple(fib_n, fact_n, prime_n);
}

void comprehensive_example() {
    std::cout << "\n=== constexpr 综合示例 ===" << std::endl;

    // 编译期综合计算
    constexpr auto [fib, fact, prime] = compile_time_computation();

    std::cout << "fibonacci(10) = " << fib << std::endl;
    std::cout << "10! = " << fact << std::endl;
    std::cout << "10 is prime: " << (prime ? "yes" : "no") << std::endl;
}

int main() {
    std::cout << "C++23 constexpr 扩展示例\n" << std::endl;

    basic_constexpr();
    array_operations();
    string_operations();
    math_operations();
    algorithm_example();
    lookup_table();
    compile_time_validation();
    constexpr_class();
    container_operations();
    comprehensive_example();

    return 0;
}
