// consteval.cpp - C++20 consteval 立即函数示例
//
// 本文件展示 C++20 consteval 的用法，包括：
//   1. consteval 函数的定义
//   2. consteval vs constexpr 的区别
//   3. consteval 的使用场景
//
// 编译命令：
//   g++ -std=c++20 examples/consteval.cpp -o consteval

#include <iostream>
#include <array>

// ============================================================================
// 第一部分：consteval 函数定义
// ============================================================================

// consteval 函数：必须在编译期求值
consteval int square(int x) {
    return x * x;
}

consteval int cube(int x) {
    return x * x * x;
}

// consteval 函数可以调用其他 consteval 函数
consteval int power_of_4(int x) {
    return square(square(x));
}

// consteval 函数可以有复杂的逻辑
consteval int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// consteval 函数可以有局部变量
consteval int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// ============================================================================
// 第二部分：consteval vs constexpr
// ============================================================================

// constexpr 函数：可以在编译期或运行时求值
constexpr int constexpr_square(int x) {
    return x * x;
}

// consteval 函数：必须在编译期求值
consteval int consteval_square(int x) {
    return x * x;
}

// 示例：consteval 保证编译期求值
consteval int must_be_constexpr(int n) {
    return n * n;
}

// ============================================================================
// 第三部分：consteval 的使用场景
// ============================================================================

// 场景 1：编译期常量验证
consteval int validate_range(int value, int min, int max) {
    if (value < min || value > max) {
        throw "Value out of range";
    }
    return value;
}

// 场景 2：编译期配置
struct Config {
    int port;
    int max_connections;
    int buffer_size;
};

consteval Config make_default_config() {
    return Config{
        .port = 8080,
        .max_connections = 1000,
        .buffer_size = 4096
    };
}

// 场景 3：编译期查找表
consteval auto make_square_table() {
    std::array<int, 100> table{};
    for (int i = 0; i < 100; ++i) {
        table[i] = i * i;
    }
    return table;
}

// 场景 4：编译期字符串处理
consteval std::size_t string_length(const char* str) {
    std::size_t len = 0;
    while (str[len] != '\0') {
        ++len;
    }
    return len;
}

consteval bool string_equal(const char* a, const char* b) {
    while (*a && *b) {
        if (*a != *b) return false;
        ++a;
        ++b;
    }
    return *a == *b;
}

// 场景 5：编译期数学常量
consteval double compute_pi() {
    // 使用莱布尼茨级数计算 pi（减少迭代次数以通过编译）
    double pi = 0.0;
    for (int i = 0; i < 10000; ++i) {
        pi += (i % 2 == 0 ? 1.0 : -1.0) / (2 * i + 1);
    }
    return 4.0 * pi;
}

consteval double compute_e() {
    // 使用泰勒级数计算 e
    double e = 1.0;
    double term = 1.0;
    for (int i = 1; i < 100; ++i) {
        term /= i;
        e += term;
    }
    return e;
}

// 场景 6：编译期位操作
consteval int count_bits(unsigned int n) {
    int count = 0;
    while (n) {
        count += n & 1;
        n >>= 1;
    }
    return count;
}

consteval bool is_power_of_two(unsigned int n) {
    return n > 0 && (n & (n - 1)) == 0;
}

consteval unsigned int next_power_of_two(unsigned int n) {
    unsigned int p = 1;
    while (p < n) p <<= 1;
    return p;
}

// ============================================================================
// 第四部分：consteval 与模板
// ============================================================================

// consteval 模板函数
template<typename T>
consteval T consteval_max(T a, T b) {
    return a > b ? a : b;
}

template<typename T>
consteval T consteval_min(T a, T b) {
    return a < b ? a : b;
}

template<typename T>
consteval T consteval_clamp(T value, T low, T high) {
    return value < low ? low : (value > high ? high : value);
}

// consteval 模板类
template<std::size_t N>
struct consteval_array {
    int data[N]{};

    consteval void fill(int value) {
        for (std::size_t i = 0; i < N; ++i) {
            data[i] = value;
        }
    }

    consteval int& operator[](std::size_t i) {
        return data[i];
    }

    consteval const int& operator[](std::size_t i) const {
        return data[i];
    }

    consteval std::size_t size() const {
        return N;
    }
};

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 验证 consteval 函数
static_assert(square(5) == 25);
static_assert(cube(3) == 27);
static_assert(power_of_4(2) == 16);
static_assert(factorial(5) == 120);
static_assert(fibonacci(10) == 55);

// 验证 consteval vs constexpr
static_assert(consteval_square(5) == constexpr_square(5));

// 验证使用场景
static_assert(validate_range(42, 0, 100) == 42);

constexpr auto default_config = make_default_config();
static_assert(default_config.port == 8080);
static_assert(default_config.max_connections == 1000);

constexpr auto square_table = make_square_table();
static_assert(square_table[10] == 100);
static_assert(square_table[25] == 625);

static_assert(string_length("hello") == 5);
static_assert(string_equal("hello", "hello") == true);
static_assert(string_equal("hello", "world") == false);

static_assert(count_bits(0b10101010) == 4);
static_assert(is_power_of_two(8) == true);
static_assert(is_power_of_two(7) == false);
static_assert(next_power_of_two(5) == 8);

// 验证模板函数
static_assert(consteval_max(5, 10) == 10);
static_assert(consteval_min(5, 10) == 5);
static_assert(consteval_clamp(15, 0, 10) == 10);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== C++20 consteval 立即函数示例 ===" << std::endl;
    std::cout << std::endl;

    // consteval 函数
    std::cout << "1. consteval 函数:" << std::endl;
    std::cout << "   square(5) = " << square(5) << std::endl;
    std::cout << "   cube(3) = " << cube(3) << std::endl;
    std::cout << "   power_of_4(2) = " << power_of_4(2) << std::endl;
    std::cout << "   factorial(10) = " << factorial(10) << std::endl;
    std::cout << "   fibonacci(20) = " << fibonacci(20) << std::endl;
    std::cout << std::endl;

    // 编译期常量验证
    std::cout << "2. 编译期常量验证:" << std::endl;
    std::cout << "   validate_range(42, 0, 100) = " << validate_range(42, 0, 100) << std::endl;
    std::cout << std::endl;

    // 编译期配置
    std::cout << "3. 编译期配置:" << std::endl;
    std::cout << "   port = " << default_config.port << std::endl;
    std::cout << "   max_connections = " << default_config.max_connections << std::endl;
    std::cout << "   buffer_size = " << default_config.buffer_size << std::endl;
    std::cout << std::endl;

    // 编译期查找表
    std::cout << "4. 编译期查找表:" << std::endl;
    std::cout << "   square_table[10] = " << square_table[10] << std::endl;
    std::cout << "   square_table[25] = " << square_table[25] << std::endl;
    std::cout << std::endl;

    // 编译期字符串处理
    std::cout << "5. 编译期字符串处理:" << std::endl;
    std::cout << "   string_length(\"hello\") = " << string_length("hello") << std::endl;
    std::cout << "   string_equal(\"hello\", \"hello\") = " << (string_equal("hello", "hello") ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 编译期位操作
    std::cout << "6. 编译期位操作:" << std::endl;
    std::cout << "   count_bits(0b10101010) = " << count_bits(0b10101010) << std::endl;
    std::cout << "   is_power_of_two(8) = " << (is_power_of_two(8) ? "true" : "false") << std::endl;
    std::cout << "   next_power_of_two(5) = " << next_power_of_two(5) << std::endl;
    std::cout << std::endl;

    // 编译期数学常量
    std::cout << "7. 编译期数学常量:" << std::endl;
    constexpr double pi = compute_pi();
    constexpr double e = compute_e();
    std::cout << "   pi ≈ " << pi << std::endl;
    std::cout << "   e ≈ " << e << std::endl;
    std::cout << std::endl;

    // 注意：以下代码会导致编译错误，因为 consteval 函数不能在运行时调用
    // int runtime_value = 5;
    // int result = must_be_constexpr(runtime_value);  // 编译错误！

    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
