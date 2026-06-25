/**
 * @file fold_expressions.cpp
 * @brief C++17 折叠表达式示例
 *
 * 折叠表达式用于简化变参模板的参数包展开。
 * 它提供了四种折叠形式，使得对参数包的操作更加简洁。
 *
 * 主要优势：
 * 1. 简化代码 - 替代递归模板
 * 2. 可读性强 - 直观的表达式
 * 3. 性能好 - 编译期展开
 */

#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <functional>
#include <numeric>

// 1. 四种折叠形式
// 一元右折叠: (pack op ...)
// 一元左折叠: (... op pack)
// 二元右折叠: (pack op ... op init)
// 二元左折叠: (init op ... op pack)

// 一元右折叠示例
template <typename... Args>
auto sum_right_fold(Args... args) {
    return (args + ...);  // (a + (b + (c + d)))
}

// 一元左折叠示例
template <typename... Args>
auto sum_left_fold(Args... args) {
    return (... + args);  // (((a + b) + c) + d)
}

// 二元右折叠示例
template <typename... Args>
auto sum_right_fold_with_init(Args... args) {
    return (args + ... + 0);  // (a + (b + (c + (d + 0))))
}

// 二元左折叠示例
template <typename... Args>
auto sum_left_fold_with_init(Args... args) {
    return (0 + ... + args);  // ((((0 + a) + b) + c) + d)
}

void basic_fold_example() {
    std::cout << "\n[基本折叠表达式]" << std::endl;

    std::cout << "sum_right_fold(1, 2, 3, 4, 5): " << sum_right_fold(1, 2, 3, 4, 5) << std::endl;
    std::cout << "sum_left_fold(1, 2, 3, 4, 5): " << sum_left_fold(1, 2, 3, 4, 5) << std::endl;
    std::cout << "sum_right_fold_with_init(1, 2, 3): " << sum_right_fold_with_init(1, 2, 3) << std::endl;
    std::cout << "sum_left_fold_with_init(1, 2, 3): " << sum_left_fold_with_init(1, 2, 3) << std::endl;

    // 空参数包
    std::cout << "sum_right_fold_with_init(): " << sum_right_fold_with_init() << std::endl;
    std::cout << "sum_left_fold_with_init(): " << sum_left_fold_with_init() << std::endl;
}

// 2. 各种运算符的折叠
// 加法
template <typename... Args>
auto add(Args... args) {
    return (args + ...);
}

// 乘法
template <typename... Args>
auto multiply(Args... args) {
    return (args * ...);
}

// 逻辑与
template <typename... Args>
bool logical_and(Args... args) {
    return (args && ...);
}

// 逻辑或
template <typename... Args>
bool logical_or(Args... args) {
    return (args || ...);
}

// 位运算
template <typename... Args>
auto bitwise_or(Args... args) {
    return (args | ...);
}

void operator_fold_example() {
    std::cout << "\n[各种运算符的折叠]" << std::endl;

    std::cout << "add(1, 2, 3, 4, 5): " << add(1, 2, 3, 4, 5) << std::endl;
    std::cout << "multiply(1, 2, 3, 4, 5): " << multiply(1, 2, 3, 4, 5) << std::endl;
    std::cout << "logical_and(true, true, false): " << logical_and(true, true, false) << std::endl;
    std::cout << "logical_or(false, false, true): " << logical_or(false, false, true) << std::endl;
    std::cout << "bitwise_or(1, 2, 4, 8): " << bitwise_or(1, 2, 4, 8) << std::endl;
}

// 3. 字符串连接
template <typename... Args>
std::string concat(Args... args) {
    std::ostringstream oss;
    (oss << ... << args);
    return oss.str();
}

template <typename... Args>
std::string concat_with_separator(const std::string& sep, Args... args) {
    std::ostringstream oss;
    bool first = true;
    auto print = [&](const auto& arg) {
        if (!first) oss << sep;
        oss << arg;
        first = false;
    };
    (print(args), ...);
    return oss.str();
}

void string_fold_example() {
    std::cout << "\n[字符串连接]" << std::endl;

    std::cout << "concat(\"Hello\", \" \", \"World\"): " << concat("Hello", " ", "World") << std::endl;
    std::cout << "concat(1, \", \", 2, \", \", 3): " << concat(1, ", ", 2, ", ", 3) << std::endl;
    std::cout << "concat_with_separator(\", \", 1, 2, 3, 4, 5): "
              << concat_with_separator(", ", 1, 2, 3, 4, 5) << std::endl;
}

// 4. 条件检查
template <typename... Args>
bool all_positive(Args... args) {
    return ((args > 0) && ...);
}

template <typename... Args>
bool any_negative(Args... args) {
    return ((args < 0) || ...);
}

template <typename... Args>
bool all_same_type() {
    return (std::is_same_v<Args, typename std::tuple_element<0, std::tuple<Args...>>::type> && ...);
}

void conditional_fold_example() {
    std::cout << "\n[条件检查]" << std::endl;

    std::cout << "all_positive(1, 2, 3, 4, 5): " << all_positive(1, 2, 3, 4, 5) << std::endl;
    std::cout << "all_positive(1, -2, 3, 4, 5): " << all_positive(1, -2, 3, 4, 5) << std::endl;
    std::cout << "any_negative(1, 2, -3, 4, 5): " << any_negative(1, 2, -3, 4, 5) << std::endl;
    std::cout << "any_negative(1, 2, 3, 4, 5): " << any_negative(1, 2, 3, 4, 5) << std::endl;
}

// 5. 变参函数调用
template <typename Func, typename... Args>
void for_each(Func func, Args... args) {
    (func(args), ...);
}

template <typename Func, typename... Args>
auto transform(Func func, Args... args) {
    return std::make_tuple(func(args)...);
}

void function_fold_example() {
    std::cout << "\n[变参函数调用]" << std::endl;

    // 打印所有参数
    std::cout << "for_each: ";
    for_each([](auto x) { std::cout << x << " "; }, 1, 2.5, "Hello", 'c');
    std::cout << std::endl;

    // 转换所有参数
    auto result = transform([](auto x) { return x * 2; }, 1, 2, 3, 4, 5);
    std::cout << "transform: ";
    std::apply([](auto... args) { ((std::cout << args << " "), ...); }, result);
    std::cout << std::endl;
}

// 6. 容器操作
template <typename Container, typename... Args>
void push_back_all(Container& c, Args... args) {
    (c.push_back(args), ...);
}

template <typename Container>
auto sum_container(const Container& c) {
    return std::accumulate(c.begin(), c.end(),
        typename Container::value_type{});
}

void container_fold_example() {
    std::cout << "\n[容器操作]" << std::endl;

    std::vector<int> vec;
    push_back_all(vec, 1, 2, 3, 4, 5);

    std::cout << "Vector: ";
    for (int v : vec) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    std::cout << "Sum: " << sum_container(vec) << std::endl;
}

// 7. 表达式求值
template <typename T>
T evaluate(T value) {
    return value;
}

template <typename T, typename... Args>
T evaluate(T first, Args... rest) {
    return first + evaluate(rest...);
}

// 使用折叠表达式简化
template <typename... Args>
auto evaluate_fold(Args... args) {
    return (args + ...);
}

void evaluation_example() {
    std::cout << "\n[表达式求值]" << std::endl;

    std::cout << "evaluate(1, 2, 3, 4, 5): " << evaluate(1, 2, 3, 4, 5) << std::endl;
    std::cout << "evaluate_fold(1, 2, 3, 4, 5): " << evaluate_fold(1, 2, 3, 4, 5) << std::endl;
}

// 8. 编译期计算
template <typename... Args>
constexpr auto constexpr_sum(Args... args) {
    return (args + ...);
}

template <typename... Args>
constexpr auto constexpr_product(Args... args) {
    return (args * ...);
}

void constexpr_fold_example() {
    std::cout << "\n[编译期计算]" << std::endl;

    constexpr auto sum = constexpr_sum(1, 2, 3, 4, 5);
    constexpr auto product = constexpr_product(1, 2, 3, 4, 5);

    std::cout << "constexpr_sum(1, 2, 3, 4, 5): " << sum << std::endl;
    std::cout << "constexpr_product(1, 2, 3, 4, 5): " << product << std::endl;

    static_assert(constexpr_sum(1, 2, 3) == 6, "Sum should be 6");
    static_assert(constexpr_product(1, 2, 3) == 6, "Product should be 6");
}

// 9. 错误处理
template <typename... Args>
bool validate_all(Args... args) {
    return ((args != 0) && ...);
}

template <typename... Args>
void print_errors(Args... args) {
    auto print_if_error = [](auto arg) {
        if (arg == 0) {
            std::cout << "Error: zero value" << std::endl;
        }
    };
    (print_if_error(args), ...);
}

void error_handling_example() {
    std::cout << "\n[错误处理]" << std::endl;

    std::cout << "validate_all(1, 2, 3, 4, 5): " << validate_all(1, 2, 3, 4, 5) << std::endl;
    std::cout << "validate_all(1, 0, 3, 4, 5): " << validate_all(1, 0, 3, 4, 5) << std::endl;

    std::cout << "print_errors(1, 0, 3, 0, 5):" << std::endl;
    print_errors(1, 0, 3, 0, 5);
}

// 10. 实际应用：日志系统
template <typename... Args>
void log(const std::string& level, Args... args) {
    std::cout << "[" << level << "] ";
    ((std::cout << args << " "), ...);
    std::cout << std::endl;
}

template <typename... Args>
void log_info(Args... args) {
    log("INFO", args...);
}

template <typename... Args>
void log_error(Args... args) {
    log("ERROR", args...);
}

void logging_example() {
    std::cout << "\n[日志系统]" << std::endl;

    log_info("User", "logged in", "from", "192.168.1.1");
    log_error("Failed to", "connect to", "database");
}

// 主示例函数
void fold_expressions_example() {
    std::cout << "=== 折叠表达式 ===" << std::endl;

    basic_fold_example();
    operator_fold_example();
    string_fold_example();
    conditional_fold_example();
    function_fold_example();
    container_fold_example();
    evaluation_example();
    constexpr_fold_example();
    error_handling_example();
    logging_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    fold_expressions_example();
    return 0;
}
#endif
