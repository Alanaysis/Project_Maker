// =============================================================================
// function_templates.cpp - 函数模板基础
// =============================================================================
// 编译: g++ -std=c++17 -o function_templates function_templates.cpp
// 运行: ./function_templates
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

// ---------------------------------------------------------------------------
// 1. 基本函数模板
// ---------------------------------------------------------------------------

// 简单的函数模板：求最大值
template <typename T>
T max_value(T a, T b) {
    return (a > b) ? a : b;
}

// 自动推导返回类型 (C++14)
template <typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}

// C++17: auto 返回类型自动推导
template <typename T, typename U>
auto multiply(T a, U b) {
    return a * b;
}

// ---------------------------------------------------------------------------
// 2. 多模板参数
// ---------------------------------------------------------------------------

// 两个模板参数
template <typename T, typename U>
void print_pair(const T& a, const U& b) {
    std::cout << "(" << a << ", " << b << ")" << std::endl;
}

// 三个模板参数
template <typename T, typename U, typename V>
auto sum_three(T a, U b, V c) {
    return a + b + c;
}

// ---------------------------------------------------------------------------
// 3. 带默认模板参数
// ---------------------------------------------------------------------------

template <typename T, typename Compare = std::less<T>>
T max_with_compare(T a, T b, Compare comp = Compare{}) {
    return comp(a, b) ? b : a;
}

// ---------------------------------------------------------------------------
// 4. 函数模板重载
// ---------------------------------------------------------------------------

// 通用版本
template <typename T>
void process(const T& value) {
    std::cout << "Generic: " << value << std::endl;
}

// 指针特化
template <typename T>
void process(T* ptr) {
    if (ptr) {
        std::cout << "Pointer: " << *ptr << std::endl;
    } else {
        std::cout << "Null pointer" << std::endl;
    }
}

// 多参数版本
template <typename T, typename... Args>
void process(const T& first, const Args&... rest) {
    std::cout << first << " ";
    process(rest...);
}

// ---------------------------------------------------------------------------
// 5. 尾置返回类型
// ---------------------------------------------------------------------------

// 当返回类型依赖于参数时使用尾置返回类型
template <typename Container>
auto get_first(const Container& c) -> decltype(c.front()) {
    return c.front();
}

template <typename Container>
auto get_size(const Container& c) -> decltype(c.size()) {
    return c.size();
}

// ---------------------------------------------------------------------------
// 6. 模板参数推导
// ---------------------------------------------------------------------------

// 引用折叠规则
template <typename T>
void ref_info(T&& arg) {
    if constexpr (std::is_lvalue_reference_v<T>) {
        std::cout << "Lvalue reference" << std::endl;
    } else if constexpr (std::is_rvalue_reference_v<T>) {
        std::cout << "Rvalue reference" << std::endl;
    } else {
        std::cout << "Value" << std::endl;
    }
}

// 完美转发
template <typename T>
void wrapper(T&& arg) {
    // 转发给另一个函数
    process(std::forward<T>(arg));
}

// ---------------------------------------------------------------------------
// 7. 递归函数模板
// ---------------------------------------------------------------------------

// 编译期阶乘
template <std::size_t N>
constexpr std::size_t factorial() {
    return N * factorial<N - 1>();
}

template <>
constexpr std::size_t factorial<0>() {
    return 1;
}

// 运行时递归版本
template <typename T>
T factorial_rt(T n) {
    if (n <= 1) return 1;
    return n * factorial_rt(n - 1);
}

// ---------------------------------------------------------------------------
// 8. 变参函数模板
// ---------------------------------------------------------------------------

// 计算参数个数
template <typename... Args>
constexpr std::size_t count_args(Args&&...) {
    return sizeof...(Args);
}

// 打印所有参数
template <typename... Args>
void print_all(Args&&... args) {
    ((std::cout << args << " "), ...);  // C++17 折叠表达式
    std::cout << std::endl;
}

// 求和
template <typename... Args>
auto sum_all(Args... args) {
    return (args + ...);  // C++17 折叠表达式
}

// ---------------------------------------------------------------------------
// 9. SFINAE 与函数模板
// ---------------------------------------------------------------------------

// 只接受算术类型
template <typename T>
std::enable_if_t<std::is_arithmetic_v<T>, T>
safe_divide(T a, T b) {
    if (b == 0) {
        std::cerr << "Division by zero!" << std::endl;
        return T{};
    }
    return a / b;
}

// ---------------------------------------------------------------------------
// 主函数
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== C++ 函数模板基础 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本函数模板
    std::cout << "1. 基本函数模板:" << std::endl;
    std::cout << "max(3, 5) = " << max_value(3, 5) << std::endl;
    std::cout << "max(3.14, 2.71) = " << max_value(3.14, 2.71) << std::endl;
    std::cout << "max('a', 'z') = " << max_value('a', 'z') << std::endl;
    std::cout << "add(3, 4.5) = " << add(3, 4.5) << std::endl;
    std::cout << "multiply(3, 4.5) = " << multiply(3, 4.5) << std::endl;
    std::cout << std::endl;

    // 2. 多模板参数
    std::cout << "2. 多模板参数:" << std::endl;
    print_pair(42, "hello");
    print_pair(3.14, 'A');
    std::cout << "sum_three(1, 2.5, 3) = " << sum_three(1, 2.5, 3L) << std::endl;
    std::cout << std::endl;

    // 3. 带默认模板参数
    std::cout << "3. 带默认模板参数:" << std::endl;
    std::cout << "max_with_compare(3, 5) = " << max_with_compare(3, 5) << std::endl;
    std::cout << "max_with_compare(3, 5, std::greater<>{}) = "
              << max_with_compare(3, 5, std::greater<>{}) << std::endl;
    std::cout << std::endl;

    // 4. 函数模板重载
    std::cout << "4. 函数模板重载:" << std::endl;
    process(42);
    int x = 100;
    process(&x);
    process(nullptr);
    std::cout << std::endl;

    // 5. 尾置返回类型
    std::cout << "5. 尾置返回类型:" << std::endl;
    std::vector<int> v = {1, 2, 3, 4, 5};
    std::cout << "First element: " << get_first(v) << std::endl;
    std::cout << "Size: " << get_size(v) << std::endl;
    std::cout << std::endl;

    // 6. 模板参数推导
    std::cout << "6. 模板参数推导:" << std::endl;
    int val = 42;
    ref_info(val);              // 左值
    ref_info(42);               // 右值
    ref_info(std::move(val));   // 右值
    std::cout << std::endl;

    // 7. 递归函数模板
    std::cout << "7. 递归函数模板:" << std::endl;
    std::cout << "factorial<5>() = " << factorial<5>() << std::endl;
    std::cout << "factorial<10>() = " << factorial<10>() << std::endl;
    std::cout << "factorial_rt(5) = " << factorial_rt(5) << std::endl;
    std::cout << std::endl;

    // 8. 变参函数模板
    std::cout << "8. 变参函数模板:" << std::endl;
    std::cout << "count_args(1, 2.0, 'c', \"hello\") = "
              << count_args(1, 2.0, 'c', "hello") << std::endl;
    print_all(1, 2.0, 'c', "hello");
    std::cout << "sum_all(1, 2, 3, 4, 5) = " << sum_all(1, 2, 3, 4, 5) << std::endl;
    std::cout << std::endl;

    // 9. SFINAE
    std::cout << "9. SFINAE 与函数模板:" << std::endl;
    std::cout << "safe_divide(10.0, 3.0) = " << safe_divide(10.0, 3.0) << std::endl;
    std::cout << "safe_divide(10.0, 0.0) = " << safe_divide(10.0, 0.0) << std::endl;
    // safe_divide("hello", "world");  // 编译错误：不是算术类型
    std::cout << std::endl;

    std::cout << "=== 函数模板基础演示完成 ===" << std::endl;
    return 0;
}
