/**
 * compile_time.cpp - 编译期计算优化技巧
 *
 * 核心思想：将计算从运行时转移到编译期，减少程序启动和运行时的开销。
 * 编译器在编译阶段就能求值的表达式，不会生成运行时指令。
 *
 * 编译：g++ -std=c++20 -O2 -o compile_time compile_time.cpp
 */

#include <iostream>
#include <array>
#include <cmath>
#include <chrono>
#include <numeric>
#include <iomanip>

// ============================================================================
// 1. constexpr 函数 —— 编译期可求值的函数
// ============================================================================
// constexpr 函数在参数为编译期常量时，由编译器在编译阶段求值。
// 如果参数是运行时变量，它退化为普通函数，仍然可以正常调用。

// 递归计算斐波那契数列（编译期版本）
constexpr long long fibonacci(int n) {
    if (n <= 1) return n;       // 基础情况
    long long a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        long long temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// constexpr 阶乘（递归写法）
constexpr long long factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}

// constexpr 绝对值
constexpr double constexpr_abs(double x) {
    return (x < 0) ? -x : x;
}

// constexpr 平方根（牛顿迭代法，编译期可用）
constexpr double constexpr_sqrt(double x) {
    if (x < 0) return -1;  // 负数无实数平方根
    if (x == 0) return 0;

    double guess = x / 2.0;  // 初始猜测
    // 牛顿迭代：每次将猜测值向真实值逼近
    for (int i = 0; i < 100; ++i) {
        double next = (guess + x / guess) / 2.0;
        if (constexpr_abs(next - guess) < 1e-15) break;  // 精度足够时停止
        guess = next;
    }
    return guess;
}

// ============================================================================
// 2. constexpr 类 —— 编译期可用的自定义类型
// ============================================================================
// C++20 起，constexpr 支持动态内存分配（new/delete），
// 使得更复杂的编译期数据结构成为可能。

class CompileTimeVector {
private:
    // 使用固定大小数组模拟（传统方式，兼容 C++17）
    static constexpr size_t MAX_SIZE = 32;
    double data_[MAX_SIZE]{};
    size_t size_ = 0;

public:
    constexpr CompileTimeVector() = default;

    // 编译期添加元素
    constexpr void push_back(double val) {
        if (size_ < MAX_SIZE) {
            data_[size_++] = val;
        }
    }

    constexpr size_t size() const { return size_; }
    constexpr double operator[](size_t i) const { return data_[i]; }

    // 编译期内积运算
    constexpr double dot(const CompileTimeVector& other) const {
        double result = 0;
        size_t min_size = (size_ < other.size_) ? size_ : other.size_;
        for (size_t i = 0; i < min_size; ++i) {
            result += data_[i] * other.data_[i];
        }
        return result;
    }

    // 编译期范数计算
    constexpr double norm() const {
        return constexpr_sqrt(dot(*this));
    }
};

// ============================================================================
// 3. 编译期查找表 —— 预计算表避免运行时重复计算
// ============================================================================
// 将常用函数的值预先计算好存入数组，运行时直接查表，用空间换时间。

// 编译期生成正弦查找表（0 到 2*PI，共 N 个点）
template <size_t N>
constexpr std::array<double, N> generate_sin_table() {
    std::array<double, N> table{};
    constexpr double PI = 3.14159265358979323846;
    for (size_t i = 0; i < N; ++i) {
        // 使用泰勒展开在编译期计算 sin 值
        double x = (2.0 * PI * i) / N;
        // 归约到 [-PI, PI] 范围以提高精度
        while (x > PI) x -= 2 * PI;
        while (x < -PI) x += 2 * PI;

        // 泰勒展开：sin(x) = x - x^3/3! + x^5/5! - x^7/7! + ...
        double term = x;
        double result = x;
        for (int k = 1; k < 15; ++k) {
            term *= -x * x / ((2 * k) * (2 * k + 1));
            result += term;
        }
        table[i] = result;
    }
    return table;
}

// 编译期生成平方根查找表
template <size_t N>
constexpr std::array<double, N> generate_sqrt_table() {
    std::array<double, N> table{};
    for (size_t i = 0; i < N; ++i) {
        table[i] = constexpr_sqrt(static_cast<double>(i));
    }
    return table;
}

// 编译期生成阶乘查找表
template <size_t N>
constexpr std::array<long long, N> generate_factorial_table() {
    std::array<long long, N> table{};
    table[0] = 1;
    for (size_t i = 1; i < N; ++i) {
        table[i] = table[i - 1] * i;
    }
    return table;
}

// ============================================================================
// 4. consteval (C++20) —— 强制编译期求值
// ============================================================================
// consteval 函数（也叫"立即函数"）强制要求在编译期求值。
// 如果无法在编译期求值，编译器会报错，而不是静默退化为运行时调用。

#if __cplusplus >= 202002L
consteval int compile_time_only_fib(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// consteval 用于编译期字符串长度计算
consteval size_t consteval_strlen(const char* str) {
    size_t len = 0;
    while (str[len] != '\0') ++len;
    return len;
}

// consteval 用于编译期类型大小验证
consteval bool check_type_sizes() {
    // 编译期断言各类型大小符合预期
    static_assert(sizeof(int) >= 4, "int 至少需要 4 字节");
    static_assert(sizeof(long long) >= 8, "long long 至少需要 8 字节");
    static_assert(sizeof(float) == 4, "float 应为 4 字节");
    static_assert(sizeof(double) == 8, "double 应为 8 字节");
    return true;
}
#endif // C++20 consteval

// ============================================================================
// 5. 编译期条件编译与模板元编程辅助
// ============================================================================

// 编译期最大公约数（辗转相除法）
constexpr long long gcd(long long a, long long b) {
    while (b != 0) {
        long long temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

// 编译期分数类
class ConstexprFraction {
private:
    long long num_;  // 分子
    long long den_;  // 分母

    // 自动约分
    constexpr void simplify() {
        long long g = gcd(
            (num_ < 0) ? -num_ : num_,
            (den_ < 0) ? -den_ : den_
        );
        num_ /= g;
        den_ /= g;
        // 确保分母为正
        if (den_ < 0) { num_ = -num_; den_ = -den_; }
    }

public:
    constexpr ConstexprFraction(long long n = 0, long long d = 1)
        : num_(n), den_(d) {
        simplify();
    }

    constexpr long long numerator() const { return num_; }
    constexpr long long denominator() const { return den_; }

    // 编译期加法
    constexpr ConstexprFraction operator+(const ConstexprFraction& other) const {
        return ConstexprFraction(
            num_ * other.den_ + other.num_ * den_,
            den_ * other.den_
        );
    }

    // 编译期乘法
    constexpr ConstexprFraction operator*(const ConstexprFraction& other) const {
        return ConstexprFraction(num_ * other.num_, den_ * other.den_);
    }

    constexpr double to_double() const {
        return static_cast<double>(num_) / den_;
    }
};

// ============================================================================
// 主函数 —— 展示编译期计算的各种用法与性能优势
// ============================================================================

int main() {
    std::cout << "========================================\n";
    std::cout << "  编译期计算优化技巧演示 (C++17/20)\n";
    std::cout << "========================================\n\n";

    // --- 1. constexpr 函数 ---
    std::cout << "【1. constexpr 函数】\n";

    // 下面这些值在编译期就已经计算好了，运行时只是直接使用常量
    constexpr long long fib_30 = fibonacci(30);     // 编译期计算 fib(30)
    constexpr long long fib_40 = fibonacci(40);     // 编译期计算 fib(40)
    constexpr long long fact_15 = factorial(15);    // 编译期计算 15!
    constexpr double sqrt_2 = constexpr_sqrt(2.0);  // 编译期计算 sqrt(2)

    std::cout << "  fibonacci(30) = " << fib_30 << " [编译期计算]\n";
    std::cout << "  fibonacci(40) = " << fib_40 << " [编译期计算]\n";
    std::cout << "  factorial(15) = " << fact_15 << " [编译期计算]\n";
    std::cout << "  sqrt(2)       = " << std::setprecision(15) << sqrt_2 << " [编译期计算]\n\n";

    // 运行时调用（退化为普通函数）
    int runtime_n = 35;
    auto start = std::chrono::high_resolution_clock::now();
    long long runtime_fib = fibonacci(runtime_n);
    auto end = std::chrono::high_resolution_clock::now();
    auto runtime_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

    std::cout << "  运行时计算 fibonacci(35) = " << runtime_fib
              << " 耗时: " << runtime_ns << " ns\n";
    std::cout << "  （注：constexpr 版本在编译期已完成，运行时零开销）\n\n";

    // --- 2. constexpr 类 ---
    std::cout << "【2. constexpr 类对象】\n";

    // 编译期向量运算
    constexpr CompileTimeVector v1 = []() {
        CompileTimeVector v;
        v.push_back(1.0); v.push_back(2.0); v.push_back(3.0);
        return v;
    }();

    constexpr CompileTimeVector v2 = []() {
        CompileTimeVector v;
        v.push_back(4.0); v.push_back(5.0); v.push_back(6.0);
        return v;
    }();

    constexpr double dot_result = v1.dot(v2);     // 编译期内积
    constexpr double norm_result = v1.norm();      // 编译期范数

    std::cout << "  v1 = (1, 2, 3), v2 = (4, 5, 6)\n";
    std::cout << "  内积 v1·v2 = " << dot_result << " [编译期计算]\n";
    std::cout << "  范数 |v1|  = " << std::setprecision(6) << norm_result << " [编译期计算]\n\n";

    // --- 3. 编译期查找表 ---
    std::cout << "【3. 编译期查找表】\n";

    // 在编译期生成查找表，运行时直接查表，O(1) 时间复杂度
    constexpr auto sin_table = generate_sin_table<360>();    // 每度一个值
    constexpr auto sqrt_table = generate_sqrt_table<100>();  // 0~99 的平方根
    constexpr auto fact_table = generate_factorial_table<21>(); // 0!~20!

    std::cout << "  正弦查找表 (360 个点，前 10 个):\n    ";
    for (int i = 0; i < 10; ++i) {
        std::cout << "sin(" << i << "°)=" << std::setprecision(4) << sin_table[i] << "  ";
    }
    std::cout << "\n";

    std::cout << "  平方根查找表 (前 10 个):\n    ";
    for (int i = 0; i < 10; ++i) {
        std::cout << "sqrt(" << i << ")=" << std::setprecision(4) << sqrt_table[i] << "  ";
    }
    std::cout << "\n";

    std::cout << "  阶乘查找表:\n    ";
    for (int i = 0; i <= 10; ++i) {
        std::cout << i << "!=" << fact_table[i] << "  ";
    }
    std::cout << "\n\n";

    // 性能对比：查表 vs 运行时计算
    {
        constexpr int ITERATIONS = 1000000;
        volatile double sink = 0;  // volatile 防止编译器优化掉循环

        // 测量运行时 std::sin 的性能
        start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < ITERATIONS; ++i) {
            double angle = (2.0 * 3.14159265358979 * (i % 360)) / 360.0;
            sink = std::sin(angle);
        }
        end = std::chrono::high_resolution_clock::now();
        auto sin_runtime_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

        // 测量查表的性能
        start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < ITERATIONS; ++i) {
            sink = sin_table[i % 360];
        }
        end = std::chrono::high_resolution_clock::now();
        auto table_lookup_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

        std::cout << "  性能对比 (" << ITERATIONS << " 次查询):\n";
        std::cout << "    std::sin 运行时计算: " << sin_runtime_ns / 1000.0 << " μs\n";
        std::cout << "    查表法 (编译期生成): " << table_lookup_ns / 1000.0 << " μs\n";
        std::cout << "    加速比: " << std::setprecision(1)
                  << static_cast<double>(sin_runtime_ns) / table_lookup_ns << "x\n\n";
    }

    // --- 4. consteval (C++20) ---
#if __cplusplus >= 202002L
    std::cout << "【4. consteval 强制编译期求值 (C++20)】\n";

    // consteval 保证在编译期完成，否则编译报错
    constexpr int ce_fib = compile_time_only_fib(20);  // OK：编译期常量
    std::cout << "  consteval fibonacci(20) = " << ce_fib << " [必须编译期完成]\n";

    // 编译期字符串长度
    constexpr size_t hello_len = consteval_strlen("Hello, C++20!");
    std::cout << "  consteval strlen(\"Hello, C++20!\") = " << hello_len << "\n";

    // 编译期类型检查
    constexpr bool sizes_ok = check_type_sizes();
    std::cout << "  类型大小检查: " << (sizes_ok ? "通过" : "失败") << "\n";
#else
    std::cout << "【4. consteval (C++20) - 需要 C++20 编译器，当前跳过】\n";
#endif

    // 注意：下面的代码如果取消注释会编译失败，因为 consteval 不接受运行时参数
    // int runtime_val = 10;
    // compile_time_only_fib(runtime_val);  // 编译错误！

    // --- 5. constexpr 分数运算 ---
    std::cout << "\n【5. 编译期分数运算】\n";

    constexpr ConstexprFraction f1(1, 3);   // 1/3
    constexpr ConstexprFraction f2(1, 6);   // 1/6
    constexpr ConstexprFraction sum = f1 + f2;   // 1/3 + 1/6 = 1/2
    constexpr ConstexprFraction product = f1 * f2; // 1/3 * 1/6 = 1/18

    std::cout << "  " << f1.numerator() << "/" << f1.denominator()
              << " + " << f2.numerator() << "/" << f2.denominator()
              << " = " << sum.numerator() << "/" << sum.denominator()
              << " [编译期计算]\n";
    std::cout << "  " << f1.numerator() << "/" << f1.denominator()
              << " * " << f2.numerator() << "/" << f2.denominator()
              << " = " << product.numerator() << "/" << product.denominator()
              << " [编译期计算]\n\n";

    // --- 总结 ---
    std::cout << "========================================\n";
    std::cout << "  总结：编译期计算的优势\n";
    std::cout << "========================================\n";
    std::cout << "  1. constexpr 函数 —— 常量参数时编译期求值，零运行时开销\n";
    std::cout << "  2. constexpr 类   —— 复杂对象可在编译期构造和运算\n";
    std::cout << "  3. 查找表         —— 编译期预计算，运行时 O(1) 查表\n";
    std::cout << "  4. consteval      —— 强制编译期求值，保证零运行时开销\n";
    std::cout << "  5. 分数运算       —— 精确的编译期有理数计算\n";
    std::cout << "\n  适用场景：数学常量、配置计算、查找表生成、类型特征验证\n";

    return 0;
}
