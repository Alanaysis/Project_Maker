/**
 * constexpr 测试
 */

#include <gtest/gtest.h>
#include <array>

// 测试 constexpr 函数
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

TEST(Constexpr, Factorial) {
    constexpr int fact5 = factorial(5);
    EXPECT_EQ(fact5, 120);

    constexpr int fact10 = factorial(10);
    EXPECT_EQ(fact10, 3628800);
}

// 测试 constexpr 变量
TEST(Constexpr, Variables) {
    constexpr int x = 42;
    constexpr double pi = 3.14159265358979;
    constexpr bool flag = true;

    EXPECT_EQ(x, 42);
    EXPECT_DOUBLE_EQ(pi, 3.14159265358979);
    EXPECT_TRUE(flag);
}

// 测试 constexpr 函数（C++14 风格）
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

TEST(Constexpr, Fibonacci) {
    constexpr int fib10 = fibonacci(10);
    EXPECT_EQ(fib10, 55);

    constexpr int fib20 = fibonacci(20);
    EXPECT_EQ(fib20, 6765);
}

// 测试 constexpr 类
class Point {
    int x_, y_;

public:
    constexpr Point(int x, int y) : x_(x), y_(y) {}
    constexpr int x() const { return x_; }
    constexpr int y() const { return y_; }

    constexpr Point add(const Point& other) const {
        return Point(x_ + other.x_, y_ + other.y_);
    }
};

TEST(Constexpr, Class) {
    constexpr Point p1(1, 2);
    constexpr Point p2(3, 4);
    constexpr Point p3 = p1.add(p2);

    EXPECT_EQ(p1.x(), 1);
    EXPECT_EQ(p1.y(), 2);
    EXPECT_EQ(p3.x(), 4);
    EXPECT_EQ(p3.y(), 6);
}

// 测试 constexpr 与数组（C++14 中 std::array::operator[] 不是 constexpr）
TEST(Constexpr, Array) {
    // 使用普通数组测试
    constexpr int arr[] = {0, 1, 4, 9, 16, 25, 36, 49, 64, 81};
    EXPECT_EQ(arr[0], 0);
    EXPECT_EQ(arr[1], 1);
    EXPECT_EQ(arr[5], 25);
    EXPECT_EQ(arr[9], 81);
}

// 测试 constexpr 条件判断
constexpr int abs_val(int n) {
    if (n < 0) return -n;
    return n;
}

TEST(Constexpr, Conditional) {
    constexpr int abs_neg = abs_val(-42);
    constexpr int abs_pos = abs_val(42);

    EXPECT_EQ(abs_neg, 42);
    EXPECT_EQ(abs_pos, 42);
}

// 测试 constexpr 循环
constexpr int sum_range(int n) {
    int sum = 0;
    for (int i = 1; i <= n; ++i) {
        sum += i;
    }
    return sum;
}

TEST(Constexpr, Loop) {
    constexpr int sum10 = sum_range(10);
    EXPECT_EQ(sum10, 55);

    constexpr int sum100 = sum_range(100);
    EXPECT_EQ(sum100, 5050);
}

// 测试 constexpr 与模板
template<typename T>
constexpr T square(T x) {
    return x * x;
}

TEST(Constexpr, Template) {
    constexpr int sq_int = square(5);
    constexpr double sq_double = square(3.14);

    EXPECT_EQ(sq_int, 25);
    EXPECT_DOUBLE_EQ(sq_double, 9.8596);
}

// 测试 constexpr 与 static_assert
TEST(Constexpr, StaticAssert) {
    static_assert(factorial(5) == 120, "5! should be 120");
    static_assert(fibonacci(10) == 55, "fib(10) should be 55");
    static_assert(abs_val(-42) == 42, "abs(-42) should be 42");
}

// 测试 constexpr 字符串长度
constexpr size_t strlen_constexpr(const char* str) {
    size_t len = 0;
    while (str[len] != '\0') {
        ++len;
    }
    return len;
}

TEST(Constexpr, StringLength) {
    constexpr size_t len = strlen_constexpr("Hello");
    EXPECT_EQ(len, 5);

    constexpr size_t len_empty = strlen_constexpr("");
    EXPECT_EQ(len_empty, 0);
}

// 测试 constexpr 最大公约数
constexpr int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

TEST(Constexpr, GCD) {
    constexpr int g = gcd(12, 18);
    EXPECT_EQ(g, 6);

    constexpr int g2 = gcd(100, 75);
    EXPECT_EQ(g2, 25);
}

// 测试 constexpr 最小公倍数
constexpr int lcm(int a, int b) {
    return (a / gcd(a, b)) * b;
}

TEST(Constexpr, LCM) {
    constexpr int l = lcm(12, 18);
    EXPECT_EQ(l, 36);

    constexpr int l2 = lcm(100, 75);
    EXPECT_EQ(l2, 300);
}

// 测试 constexpr 与运行时混合
TEST(Constexpr, RuntimeMix) {
    // 编译期计算
    constexpr int compile_time = factorial(5);
    EXPECT_EQ(compile_time, 120);

    // 运行时计算
    int runtime_n = 10;
    int runtime_result = factorial(runtime_n);
    EXPECT_EQ(runtime_result, 3628800);
}

// 测试 constexpr 递归深度
constexpr int power(int base, int exp) {
    return exp == 0 ? 1 : base * power(base, exp - 1);
}

TEST(Constexpr, Recursion) {
    constexpr int p = power(2, 10);
    EXPECT_EQ(p, 1024);

    constexpr int p3 = power(3, 5);
    EXPECT_EQ(p3, 243);
}
