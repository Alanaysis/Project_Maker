/**
 * 01_concepts.cpp - C++20 概念 (Concepts)
 *
 * 概念是对模板参数的命名约束，让模板编程更加清晰和安全。
 *
 * 核心要点：
 * 1. concept 关键字定义约束
 * 2. requires 表达式定义复杂约束
 * 3. 约束 auto 和约束简写
 * 4. 概念的组合 (合取/析取)
 * 5. 嵌套需求和复合需求
 */

#include <iostream>
#include <string>
#include <vector>
#include <list>
#include <concepts>
#include <type_traits>
#include <numeric>
#include <algorithm>

// ============================================================
// 1. 使用标准库概念约束模板
// ============================================================

// std::integral - 只接受整数类型
template <std::integral T>
T gcd(T a, T b) {
    while (b != 0) {
        T temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

// std::floating_point - 只接受浮点类型
template <std::floating_point T>
T approximate_equal(T a, T b, T epsilon = static_cast<T>(1e-9)) {
    return std::abs(a - b) < epsilon;
}

// ============================================================
// 2. 自定义概念
// ============================================================

// 简单概念：要求类型可默认构造
template <typename T>
concept DefaultConstructible = std::is_default_constructible_v<T>;

// 带表达式的概念：要求类型支持加法
template <typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

// 复合概念：组合多个约束
template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

// 更复杂的概念：容器类型
template <typename T>
concept Container = requires(T t) {
    typename T::value_type;       // 有 value_type 类型
    typename T::iterator;         // 有 iterator 类型
    typename T::size_type;        // 有 size_type 类型
    { t.begin() } -> std::same_as<typename T::iterator>;
    { t.end() } -> std::same_as<typename T::iterator>;
    { t.size() } -> std::convertible_to<typename T::size_type>;
};

// ============================================================
// 3. requires 表达式 (四种形式)
// ============================================================

// 简单需求 - 检查表达式是否有效
template <typename T>
concept Hashable = requires(T a) {
    { std::hash<T>{}(a) } -> std::convertible_to<std::size_t>;
};

// 类型需求 - 检查类型是否存在
template <typename T>
concept HasValueType = requires {
    typename T::value_type;
};

// 复合需求 - 检查表达式及其属性
template <typename T>
concept Sortable = requires(T& t) {
    { t.begin() } -> std::input_or_output_iterator;
    { t.end() } -> std::input_or_output_iterator;
    requires std::totally_ordered<typename T::value_type>;
};

// 嵌套需求 - 使用 requires 嵌套进一步约束
template <typename T>
concept Summable = requires(T a, T b) {
    { a + b } -> std::same_as<T>;
    requires sizeof(T) <= 16;  // 额外约束：类型大小不超过 16 字节
};

// ============================================================
// 4. 约束的使用方式
// ============================================================

// 方式一：模板参数列表中使用
template <Container C>
void print_container(const C& container, const std::string& name) {
    std::cout << name << ": [";
    bool first = true;
    for (const auto& item : container) {
        if (!first) std::cout << ", ";
        std::cout << item;
        first = false;
    }
    std::cout << "]\n";
}

// 方式二：requires 子句
template <typename T>
    requires Numeric<T>
T clamp_value(T value, T low, T high) {
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

// 方式三：约束 auto 参数
auto add_numbers(Numeric auto a, Numeric auto b) {
    return a + b;
}

// 方式四：requires 块（函数体内）
template <typename T>
void process(T& value) {
    // 在函数体内使用 requires 检查
    if constexpr (requires { value.size(); }) {
        std::cout << "  有 size() 方法, 大小 = " << value.size() << "\n";
    }
    if constexpr (requires { value.push_back(std::declval<typename T::value_type>()); }) {
        std::cout << "  有 push_back() 方法, 是动态容器\n";
    }
}

// ============================================================
// 5. 概念重载和特化
// ============================================================

// 通用版本
template <typename T>
std::string describe(const T&) {
    return "通用类型";
}

// Numeric 约束版本
std::string describe(Numeric auto const&) {
    return "数值类型";
}

// std::integral 约束版本
std::string describe(std::integral auto const&) {
    return "整数类型";
}

// ============================================================
// 6. 实际应用示例
// ============================================================

// 安全的除法 - 使用概念确保类型正确
template <Numeric T>
    requires (!std::same_as<T, bool>)  // 排除 bool
std::pair<bool, T> safe_divide(T a, T b) {
    if constexpr (std::floating_point<T>) {
        if (std::abs(b) < std::numeric_limits<T>::epsilon()) {
            return {false, T{}};
        }
        return {true, a / b};
    } else {
        if (b == 0) return {false, T{}};
        return {true, a / b};
    }
}

// 有序容器查找 - 使用概念约束
template <typename C, typename V>
    requires Container<C> && std::equality_comparable_with<typename C::value_type, V>
auto find_in(const C& container, const V& value) {
    return std::find(container.begin(), container.end(), value);
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 概念 (Concepts) 示例 ===\n\n";

    // 1. 标准库概念
    std::cout << "【1. 标准库概念】\n";
    std::cout << "gcd(12, 8) = " << gcd(12, 8) << "\n";
    // gcd(1.5, 2.5);  // 编译错误：浮点类型不满足 std::integral
    std::cout << "approx_equal(1.0, 1.0000000001) = "
              << std::boolalpha << approximate_equal(1.0, 1.0000000001) << "\n\n";

    // 2. 自定义概念
    std::cout << "【2. 自定义概念】\n";
    std::vector<int> vec = {3, 1, 4, 1, 5};
    std::list<double> lst = {2.7, 1.8, 3.14};
    print_container(vec, "vector<int>");
    print_container(lst, "list<double>");

    // 3. 约束 auto
    std::cout << "\n【3. 约束 auto】\n";
    std::cout << "add_numbers(3, 4) = " << add_numbers(3, 4) << "\n";
    std::cout << "add_numbers(1.5, 2.5) = " << add_numbers(1.5, 2.5) << "\n";

    // 4. requires 子句
    std::cout << "\n【4. requires 子句和 clamp】\n";
    std::cout << "clamp_value(15, 0, 10) = " << clamp_value(15, 0, 10) << "\n";
    std::cout << "clamp_value(3.14, 0.0, 5.0) = " << clamp_value(3.14, 0.0, 5.0) << "\n";

    // 5. 函数体内 requires
    std::cout << "\n【5. 函数体内 requires】\n";
    std::vector<int> v = {1, 2, 3};
    int x = 42;
    std::cout << "处理 vector<int>:\n";
    process(v);
    std::cout << "处理 int:\n";
    process(x);

    // 6. 概念重载
    std::cout << "\n【6. 概念重载选择】\n";
    std::string s = "hello";
    std::cout << "describe(42) = " << describe(42) << "\n";      // 整数类型
    std::cout << "describe(3.14) = " << describe(3.14) << "\n";  // 数值类型
    std::cout << "describe(s) = " << describe(s) << "\n";        // 通用类型

    // 7. 安全除法
    std::cout << "\n【7. 安全除法】\n";
    auto [ok1, r1] = safe_divide(10, 3);
    std::cout << "10 / 3 = " << r1 << " (valid: " << ok1 << ")\n";
    auto [ok2, r2] = safe_divide(10, 0);
    std::cout << "10 / 0 = " << r2 << " (valid: " << ok2 << ")\n";
    auto [ok3, r3] = safe_divide(10.0, 3.0);
    std::cout << "10.0 / 3.0 = " << r3 << " (valid: " << ok3 << ")\n";

    // 8. 有序容器查找
    std::cout << "\n【8. 容器查找】\n";
    auto it = find_in(vec, 5);
    if (it != vec.end()) {
        std::cout << "在 vector 中找到 5\n";
    }

    // 9. 概念的静态断言
    std::cout << "\n【9. 概念静态检查】\n";
    static_assert(std::integral<int>);
    static_assert(std::floating_point<double>);
    static_assert(Numeric<float>);
    static_assert(!Numeric<std::string>);
    static_assert(Container<std::vector<int>>);
    static_assert(Container<std::list<double>>);
    static_assert(!Container<int>);
    std::cout << "所有 static_assert 通过!\n";

    std::cout << "\n=== 概念示例完成 ===\n";
    return 0;
}
