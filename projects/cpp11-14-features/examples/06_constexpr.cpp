/**
 * C++11/14 constexpr 示例
 *
 * 学习目标：
 * 1. 理解 constexpr 的含义
 * 2. 掌握 constexpr 函数的编写
 * 3. 理解 C++14 对 constexpr 的放宽
 * 4. 学会在编译期进行计算
 */

#include <iostream>
#include <array>
#include <type_traits>

// ==========================================
// 1. constexpr 基础
// ==========================================

// C++11 constexpr 函数：只能包含一个 return 语句
constexpr int factorial_cxx11(int n) {
    return n <= 1 ? 1 : n * factorial_cxx11(n - 1);
}

// C++14 constexpr 函数：可以包含多条语句
constexpr int factorial_cxx14(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

void demonstrate_basic_constexpr() {
    std::cout << "\n=== 1. constexpr 基础 ===" << std::endl;

    // constexpr 变量
    constexpr int x = 42;
    constexpr double pi = 3.14159265358979;
    constexpr const char* str = "Hello";

    std::cout << "x = " << x << std::endl;
    std::cout << "pi = " << pi << std::endl;
    std::cout << "str = " << str << std::endl;

    // 编译期计算
    constexpr int fact5 = factorial_cxx11(5);
    std::cout << "5! = " << fact5 << std::endl;

    // 运行时计算也可以使用 constexpr 函数
    int runtime_n = 10;
    int runtime_result = factorial_cxx14(runtime_n);
    std::cout << runtime_n << "! = " << runtime_result << std::endl;
}

// ==========================================
// 2. C++11 vs C++14 constexpr
// ==========================================

// C++11 限制：只能有一个 return 语句
constexpr int fib_cxx11(int n) {
    return n <= 1 ? n : fib_cxx11(n - 1) + fib_cxx11(n - 2);
}

// C++14 放宽：可以使用循环、局部变量等
constexpr int fib_cxx14(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// C++14 放宽：可以使用 if-else
constexpr int abs_val(int n) {
    if (n < 0) {
        return -n;
    }
    return n;
}

void demonstrate_cxx14_constexpr() {
    std::cout << "\n=== 2. C++11 vs C++14 constexpr ===" << std::endl;

    // C++11 风格
    constexpr int fib10_cxx11 = fib_cxx11(10);
    std::cout << "fib(10) C++11 风格: " << fib10_cxx11 << std::endl;

    // C++14 风格
    constexpr int fib10_cxx14 = fib_cxx14(10);
    std::cout << "fib(10) C++14 风格: " << fib10_cxx14 << std::endl;

    // C++14 if-else
    constexpr int abs_neg = abs_val(-42);
    constexpr int abs_pos = abs_val(42);
    std::cout << "abs(-42) = " << abs_neg << std::endl;
    std::cout << "abs(42) = " << abs_pos << std::endl;
}

// ==========================================
// 3. constexpr 与模板
// ==========================================

template<typename T>
constexpr T square(T x) {
    return x * x;
}

template<typename T>
constexpr T cube(T x) {
    return x * x * x;
}

template<typename T>
constexpr T power(T base, int exp) {
    T result = 1;
    for (int i = 0; i < exp; ++i) {
        result *= base;
    }
    return result;
}

void demonstrate_constexpr_templates() {
    std::cout << "\n=== 3. constexpr 与模板 ===" << std::endl;

    // 编译期计算
    constexpr int sq = square(5);
    constexpr int cu = cube(3);
    constexpr int pow = power(2, 10);

    std::cout << "5² = " << sq << std::endl;
    std::cout << "3³ = " << cu << std::endl;
    std::cout << "2¹⁰ = " << pow << std::endl;

    // 运行时计算
    double runtime_val = 3.14;
    std::cout << "3.14² = " << square(runtime_val) << std::endl;
}

// ==========================================
// 4. constexpr 类
// ==========================================

class Point {
    int x_, y_;

public:
    constexpr Point(int x, int y) : x_(x), y_(y) {}

    constexpr int x() const { return x_; }
    constexpr int y() const { return y_; }

    constexpr Point add(const Point& other) const {
        return Point(x_ + other.x_, y_ + other.y_);
    }

    constexpr Point multiply(int factor) const {
        return Point(x_ * factor, y_ * factor);
    }
};

// constexpr 函数使用 constexpr 类
constexpr Point midpoint(const Point& a, const Point& b) {
    return Point((a.x() + b.x()) / 2, (a.y() + b.y()) / 2);
}

void demonstrate_constexpr_class() {
    std::cout << "\n=== 4. constexpr 类 ===" << std::endl;

    // 编译期创建和计算
    constexpr Point p1(1, 2);
    constexpr Point p2(3, 4);
    constexpr Point p3 = p1.add(p2);
    constexpr Point p4 = p1.multiply(3);

    std::cout << "p1: (" << p1.x() << ", " << p1.y() << ")" << std::endl;
    std::cout << "p2: (" << p2.x() << ", " << p2.y() << ")" << std::endl;
    std::cout << "p1 + p2: (" << p3.x() << ", " << p3.y() << ")" << std::endl;
    std::cout << "p1 * 3: (" << p4.x() << ", " << p4.y() << ")" << std::endl;

    // 编译期计算中点
    constexpr Point mid = midpoint(p1, p2);
    std::cout << "中点: (" << mid.x() << ", " << mid.y() << ")" << std::endl;
}

// ==========================================
// 5. constexpr 与数组
// ==========================================

// 编译期计算平方
constexpr int square_val(int i) {
    return i * i;
}

// 编译期查找
constexpr int find_square(int value) {
    for (int i = 0; i < 10; ++i) {
        if (square_val(i) == value) {
            return i;
        }
    }
    return -1;
}

void demonstrate_constexpr_array() {
    std::cout << "\n=== 5. constexpr 与数组 ===" << std::endl;

    // 编译期生成平方数数组
    std::cout << "平方数数组: ";
    for (int i = 0; i < 10; ++i) {
        std::cout << square_val(i) << " ";
    }
    std::cout << std::endl;

    // 编译期查找
    constexpr int idx = find_square(25);
    std::cout << "25 在索引 " << idx << std::endl;

    // 编译期查找不存在的值
    constexpr int not_found = find_square(100);
    std::cout << "100 在索引 " << not_found << " (未找到)" << std::endl;
}

// ==========================================
// 6. constexpr 与类型特征
// ==========================================

// 编译期判断是否为偶数
constexpr bool is_even(int n) {
    return n % 2 == 0;
}

// 编译期最大公约数
constexpr int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

// 编译期最小公倍数
constexpr int lcm(int a, int b) {
    return (a / gcd(a, b)) * b;
}

void demonstrate_constexpr_type_traits() {
    std::cout << "\n=== 6. constexpr 与类型特征 ===" << std::endl;

    // 编译期判断
    static_assert(is_even(42), "42 should be even");
    static_assert(!is_even(43), "43 should not be even");
    std::cout << "编译期判断通过" << std::endl;

    // 编译期计算 GCD 和 LCM
    constexpr int g = gcd(12, 18);
    constexpr int l = lcm(12, 18);
    std::cout << "gcd(12, 18) = " << g << std::endl;
    std::cout << "lcm(12, 18) = " << l << std::endl;
}

// ==========================================
// 7. constexpr 的实际应用
// ==========================================

// 编译期字符串长度
constexpr size_t strlen_constexpr(const char* str) {
    size_t len = 0;
    while (str[len] != '\0') {
        ++len;
    }
    return len;
}

// 编译期字符串比较
constexpr bool strcmp_constexpr(const char* a, const char* b) {
    while (*a && *b) {
        if (*a != *b) return false;
        ++a;
        ++b;
    }
    return *a == *b;
}

// 编译期哈希
constexpr size_t hash_string(const char* str) {
    size_t hash = 5381;
    while (*str) {
        hash = ((hash << 5) + hash) + *str;
        ++str;
    }
    return hash;
}

void demonstrate_constexpr_practical() {
    std::cout << "\n=== 7. constexpr 的实际应用 ===" << std::endl;

    // 编译期字符串长度
    constexpr size_t len = strlen_constexpr("Hello, World!");
    std::cout << "字符串长度: " << len << std::endl;

    // 编译期字符串比较
    constexpr bool equal = strcmp_constexpr("Hello", "Hello");
    constexpr bool not_equal = strcmp_constexpr("Hello", "World");
    std::cout << "\"Hello\" == \"Hello\": " << equal << std::endl;
    std::cout << "\"Hello\" == \"World\": " << not_equal << std::endl;

    // 编译期哈希
    constexpr size_t hash1 = hash_string("Hello");
    constexpr size_t hash2 = hash_string("World");
    std::cout << "hash(\"Hello\") = " << hash1 << std::endl;
    std::cout << "hash(\"World\") = " << hash2 << std::endl;
}

// ==========================================
// 8. constexpr 与模板元编程
// ==========================================

// 编译期阶乘（模板元编程风格）
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

// 编译期斐波那契（模板元编程风格）
template<int N>
struct Fibonacci {
    static constexpr int value = Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr int value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr int value = 1;
};

void demonstrate_constexpr_metaprogramming() {
    std::cout << "\n=== 8. constexpr 与模板元编程 ===" << std::endl;

    // 模板元编程风格
    std::cout << "Factorial<10>::value = " << Factorial<10>::value << std::endl;
    std::cout << "Fibonacci<10>::value = " << Fibonacci<10>::value << std::endl;

    // 与 constexpr 函数对比
    std::cout << "factorial(10) = " << factorial_cxx14(10) << std::endl;
    std::cout << "fib(10) = " << fib_cxx14(10) << std::endl;

    // 编译期验证
    static_assert(Factorial<10>::value == 3628800, "10! should be 3628800");
    static_assert(Fibonacci<10>::value == 55, "fib(10) should be 55");
    std::cout << "编译期验证通过" << std::endl;
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11/14 constexpr 示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 基础
    demonstrate_basic_constexpr();

    // 2. C++11 vs C++14
    demonstrate_cxx14_constexpr();

    // 3. 模板
    demonstrate_constexpr_templates();

    // 4. 类
    demonstrate_constexpr_class();

    // 5. 数组
    demonstrate_constexpr_array();

    // 6. 类型特征
    demonstrate_constexpr_type_traits();

    // 7. 实际应用
    demonstrate_constexpr_practical();

    // 8. 模板元编程
    demonstrate_constexpr_metaprogramming();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
