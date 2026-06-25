// =============================================================================
// factorial_fibonacci.cpp - 编译期 factorial/fibonacci
// =============================================================================
// 编译: g++ -std=c++17 -o factorial_fibonacci factorial_fibonacci.cpp
// 运行: ./factorial_fibonacci
// =============================================================================

#include <iostream>
#include <array>
#include <type_traits>

// ---------------------------------------------------------------------------
// 1. 编译期阶乘 - 递归模板
// ---------------------------------------------------------------------------
template <std::size_t N>
struct Factorial {
    static constexpr std::size_t value = N * Factorial<N - 1>::value;
};

template <>
struct Factorial<0> {
    static constexpr std::size_t value = 1;
};

// C++14 constexpr 函数版本
constexpr std::size_t factorial(std::size_t n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}

// ---------------------------------------------------------------------------
// 2. 编译期斐波那契 - 递归模板
// ---------------------------------------------------------------------------
template <std::size_t N>
struct Fibonacci {
    static constexpr std::size_t value = Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template <>
struct Fibonacci<0> {
    static constexpr std::size_t value = 0;
};

template <>
struct Fibonacci<1> {
    static constexpr std::size_t value = 1;
};

// constexpr 函数版本
constexpr std::size_t fibonacci(std::size_t n) {
    if (n <= 1) return n;
    std::size_t a = 0, b = 1;
    for (std::size_t i = 2; i <= n; ++i) {
        std::size_t c = a + b;
        a = b;
        b = c;
    }
    return b;
}

// ---------------------------------------------------------------------------
// 3. 编译期 GCD (最大公约数)
// ---------------------------------------------------------------------------
constexpr std::size_t gcd(std::size_t a, std::size_t b) {
    return (b == 0) ? a : gcd(b, a % b);
}

// ---------------------------------------------------------------------------
// 4. 编译期幂运算
// ---------------------------------------------------------------------------
constexpr std::size_t power(std::size_t base, std::size_t exp) {
    if (exp == 0) return 1;
    if (exp % 2 == 0) {
        std::size_t half = power(base, exp / 2);
        return half * half;
    }
    return base * power(base, exp - 1);
}

// ---------------------------------------------------------------------------
// 5. 编译期组合数 C(n, k)
// ---------------------------------------------------------------------------
constexpr std::size_t binomial(std::size_t n, std::size_t k) {
    if (k > n) return 0;
    if (k == 0 || k == n) return 1;
    return factorial(n) / (factorial(k) * factorial(n - k));
}

// ---------------------------------------------------------------------------
// 6. 编译期素数检测
// ---------------------------------------------------------------------------
constexpr bool is_prime(std::size_t n) {
    if (n < 2) return false;
    if (n == 2 || n == 3) return true;
    if (n % 2 == 0 || n % 3 == 0) return false;
    for (std::size_t i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) return false;
    }
    return true;
}

// 编译期第 N 个素数
constexpr std::size_t nth_prime(std::size_t n) {
    std::size_t count = 0;
    std::size_t num = 2;
    while (true) {
        if (is_prime(num)) {
            if (count == n) return num;
            ++count;
        }
        ++num;
    }
}

// ---------------------------------------------------------------------------
// 7. 编译期查找表生成
// ---------------------------------------------------------------------------
// 生成阶乘查找表
template <std::size_t... Is>
constexpr auto make_factorial_table(std::index_sequence<Is...>) {
    return std::array<std::size_t, sizeof...(Is)>{factorial(Is)...};
}

// 生成斐波那契查找表
template <std::size_t... Is>
constexpr auto make_fibonacci_table(std::index_sequence<Is...>) {
    return std::array<std::size_t, sizeof...(Is)>{fibonacci(Is)...};
}

// 生成素数查找表
template <std::size_t... Is>
constexpr auto make_prime_table(std::index_sequence<Is...>) {
    return std::array<std::size_t, sizeof...(Is)>{nth_prime(Is)...};
}

// ---------------------------------------------------------------------------
// 8. 编译期矩阵运算
// ---------------------------------------------------------------------------
template <std::size_t N>
struct Matrix {
    std::array<std::array<int, N>, N> data{};

    constexpr int determinant() const {
        if constexpr (N == 1) {
            return data[0][0];
        } else if constexpr (N == 2) {
            return data[0][0] * data[1][1] - data[0][1] * data[1][0];
        } else {
            // 简化：只处理 1x1 和 2x2
            return 0;
        }
    }
};

// ---------------------------------------------------------------------------
// 主函数
// ---------------------------------------------------------------------------
int main() {
    std::cout << "=== 编译期数学计算 ===" << std::endl;
    std::cout << std::endl;

    // 1. 阶乘
    std::cout << "1. 阶乘:" << std::endl;
    std::cout << "  0! = " << Factorial<0>::value << std::endl;
    std::cout << "  5! = " << Factorial<5>::value << std::endl;
    std::cout << "  10! = " << Factorial<10>::value << std::endl;
    std::cout << "  15! = " << Factorial<15>::value << std::endl;
    std::cout << "  20! = " << Factorial<20>::value << std::endl;

    // constexpr 函数
    static_assert(factorial(0) == 1);
    static_assert(factorial(5) == 120);
    static_assert(factorial(10) == 3628800);
    std::cout << "  constexpr factorial(10) = " << factorial(10) << std::endl;
    std::cout << std::endl;

    // 2. 斐波那契
    std::cout << "2. 斐波那契:" << std::endl;
    std::cout << "  F(0) = " << Fibonacci<0>::value << std::endl;
    std::cout << "  F(1) = " << Fibonacci<1>::value << std::endl;
    std::cout << "  F(10) = " << Fibonacci<10>::value << std::endl;
    std::cout << "  F(20) = " << Fibonacci<20>::value << std::endl;
    std::cout << "  F(30) = " << Fibonacci<30>::value << std::endl;

    static_assert(fibonacci(0) == 0);
    static_assert(fibonacci(1) == 1);
    static_assert(fibonacci(10) == 55);
    std::cout << "  constexpr fibonacci(30) = " << fibonacci(30) << std::endl;
    std::cout << std::endl;

    // 3. GCD
    std::cout << "3. 最大公约数:" << std::endl;
    static_assert(gcd(12, 8) == 4);
    static_assert(gcd(100, 75) == 25);
    std::cout << "  gcd(12, 8) = " << gcd(12, 8) << std::endl;
    std::cout << "  gcd(100, 75) = " << gcd(100, 75) << std::endl;
    std::cout << std::endl;

    // 4. 幂运算
    std::cout << "4. 幂运算:" << std::endl;
    static_assert(power(2, 10) == 1024);
    static_assert(power(3, 5) == 243);
    std::cout << "  2^10 = " << power(2, 10) << std::endl;
    std::cout << "  3^5 = " << power(3, 5) << std::endl;
    std::cout << std::endl;

    // 5. 组合数
    std::cout << "5. 组合数 C(n,k):" << std::endl;
    static_assert(binomial(5, 2) == 10);
    static_assert(binomial(10, 3) == 120);
    std::cout << "  C(5,2) = " << binomial(5, 2) << std::endl;
    std::cout << "  C(10,3) = " << binomial(10, 3) << std::endl;
    std::cout << std::endl;

    // 6. 素数
    std::cout << "6. 素数:" << std::endl;
    std::cout << "  First 15 primes: ";
    for (std::size_t i = 0; i < 15; ++i) {
        std::cout << nth_prime(i) << " ";
    }
    std::cout << std::endl;

    static_assert(is_prime(2));
    static_assert(is_prime(7));
    static_assert(!is_prime(9));
    static_assert(is_prime(97));
    std::cout << "  97 is prime: " << is_prime(97) << std::endl;
    std::cout << std::endl;

    // 7. 查找表
    std::cout << "7. 编译期查找表:" << std::endl;
    constexpr auto fact_table = make_factorial_table(std::make_index_sequence<10>{});
    std::cout << "  Factorials: ";
    for (auto v : fact_table) std::cout << v << " ";
    std::cout << std::endl;

    constexpr auto fib_table = make_fibonacci_table(std::make_index_sequence<15>{});
    std::cout << "  Fibonacci: ";
    for (auto v : fib_table) std::cout << v << " ";
    std::cout << std::endl;

    constexpr auto prime_table = make_prime_table(std::make_index_sequence<10>{});
    std::cout << "  Primes: ";
    for (auto v : prime_table) std::cout << v << " ";
    std::cout << std::endl;
    std::cout << std::endl;

    // 8. 矩阵行列式
    std::cout << "8. 编译期矩阵:" << std::endl;
    constexpr Matrix<2> mat{{{{1, 2}, {3, 4}}}};
    static_assert(mat.determinant() == -2);
    std::cout << "  det([[1,2],[3,4]]) = " << mat.determinant() << std::endl;
    std::cout << std::endl;

    std::cout << "=== 编译期数学计算演示完成 ===" << std::endl;
    return 0;
}
