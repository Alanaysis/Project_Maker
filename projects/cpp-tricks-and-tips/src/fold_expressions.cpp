/**
 * fold_expressions.cpp - 折叠表达式 (Fold Expressions)
 *
 * 编译命令: g++ -std=c++17 -o fold_expressions fold_expressions.cpp
 *
 * 折叠表达式是 C++17 引入的强大特性，用于对参数包中的所有元素应用二元运算符。
 *
 * 四种折叠形式:
 *   1. 一元右折叠: (pack op ...)      -> (E1 op (E2 op (... op EN)))
 *   2. 一元左折叠: (... op pack)      -> (((E1 op E2) op ...) op EN)
 *   3. 二元右折叠: (pack op ... op init) -> (E1 op (E2 op (... op (EN op init))))
 *   4. 二元左折叠: (init op ... op pack) -> (((init op E1) op E2) op ... op EN)
 *
 * 折叠表达式消除了手动递归展开参数包的需要，代码更简洁、编译更快。
 */

#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <functional>
#include <type_traits>
#include <numeric>
#include <algorithm>

// ============================================================================
// 第一部分: 基础算术折叠
// ============================================================================

/**
 * 求和: 一元左折叠
 * (... + args) 展开为 ((arg1 + arg2) + arg3) + ... + argN
 *
 * 左折叠的结合性是从左到右，与普通加法一致。
 * 对于空参数包，一元折叠会报错，除非使用二元折叠。
 */
template<typename... Args>
auto sum(Args... args) {
    // 一元左折叠: 从左到右累加
    return (... + args);
    // 等价于: return ((arg1 + arg2) + arg3) + ... + argN;
}

/**
 * 求和: 二元左折叠 (带初始值)
 * (init + ... + args) 展开为 (((init + arg1) + arg2) + ... + argN)
 *
 * 二元折叠可以处理空参数包，此时直接返回 init 值。
 * 这使得函数在零参数时也安全可用。
 */
template<typename... Args>
auto sum_with_init(double init, Args... args) {
    // 二元左折叠: 以 init 为初始值
    return (init + ... + args);
}

/**
 * 求积: 一元左折叠
 * 展开为 ((arg1 * arg2) * arg3) * ... * argN
 */
template<typename... Args>
auto product(Args... args) {
    return (... * args);
}

/**
 * 求差: 一元右折叠
 * (args - ...) 展开为 (arg1 - (arg2 - (arg3 - ... - argN)))
 *
 * 注意右折叠的结合性是从右到左，结果与左折叠不同！
 * 例如: (1, 2, 3, 4) 左折叠 = ((1-2)-3)-4 = -8
 *       (1, 2, 3, 4) 右折叠 = 1-(2-(3-4)) = 1-(2-(-1)) = 1-3 = -2
 */
template<typename... Args>
auto subtract_right(Args... args) {
    return (args - ...);
}

/**
 * 求差: 一元左折叠 (对比用)
 * (... - args) 展开为 ((arg1 - arg2) - arg3) - ... - argN
 */
template<typename... Args>
auto subtract_left(Args... args) {
    return (... - args);
}

// ============================================================================
// 第二部分: 比较操作 (all / any / none)
// ============================================================================

/**
 * 检查所有参数是否都满足条件 (全部为真)
 *
 * 使用折叠表达式 + 逻辑与 (&&):
 *   (... && (args > 0)) -> ((arg1 > 0) && (arg2 > 0) && ... && (argN > 0))
 *
 * 逻辑与具有短路特性: 一旦遇到 false，后续不再计算。
 * 这在处理昂贵的谓词时非常有用。
 */
template<typename... Args>
constexpr bool all_positive(Args... args) {
    // 一元左折叠: 所有参数都大于 0 才返回 true
    return (... && (args > 0));
}

/**
 * 检查是否至少有一个参数满足条件 (存在为真)
 *
 * 使用折叠表达式 + 逻辑或 (||):
 *   (... || (args > 0)) -> ((arg1 > 0) || (arg2 > 0) || ... || (argN > 0))
 *
 * 逻辑或也具有短路特性: 一旦遇到 true，后续不再计算。
 */
template<typename... Args>
constexpr bool any_positive(Args... args) {
    // 一元左折叠: 只要有一个参数大于 0 就返回 true
    return (... || (args > 0));
}

/**
 * 检查是否所有参数都不满足条件 (全部为假)
 *
 * 使用逻辑非 + any: none = !any
 * 等价于检查所有参数都不满足谓词。
 */
template<typename... Args>
constexpr bool none_positive(Args... args) {
    // 全部不大于 0，即全部 <= 0
    return (... && !(args > 0));
}

/**
 * 通用版本: 接受自定义谓词的 all/any/none
 */
template<typename Pred, typename... Args>
constexpr bool all_of_fold(Pred pred, Args&&... args) {
    return (... && pred(std::forward<Args>(args)));
}

template<typename Pred, typename... Args>
constexpr bool any_of_fold(Pred pred, Args&&... args) {
    return (... || pred(std::forward<Args>(args)));
}

template<typename Pred, typename... Args>
constexpr bool none_of_fold(Pred pred, Args&&... args) {
    return (... && !pred(std::forward<Args>(args)));
}

// ============================================================================
// 第三部分: 字符串操作
// ============================================================================

/**
 * 字符串连接: 使用逗号运算符折叠
 *
 * 逗号运算符折叠依次执行每个表达式，并返回最后一个表达式的结果。
 * 这里用 lambda 包装，确保每个元素都被追加到结果中。
 */
template<typename... Args>
std::string join_strings(const std::string& separator, Args&&... args) {
    std::string result;
    bool first = true;

    // 逗号运算符折叠: 对每个参数执行 lambda
    // ((lambda1, lambda2), lambda3), ..., lambdaN
    (
        [&]() {
            if (!first) result += separator;
            // 使用 stringstream 将任意类型转为字符串
            std::ostringstream oss;
            oss << args;
            result += oss.str();
            first = false;
        }(), ...
    );

    return result;
}

/**
 * 字符串连接 (优化版): 使用二元折叠
 *
 * 使用重载的 + 运算符直接连接字符串
 */
std::string concat_strings() {
    return "";
}

template<typename... Args>
std::string concat_strings(const std::string& first, Args... rest) {
    return (first + ... + std::string(rest));
    // 二元右折叠: first + (rest1 + (rest2 + ... + restN))
}

/**
 * 检查字符串是否包含所有子串
 */
template<typename... Substrs>
bool contains_all(const std::string& str, Substrs... substrs) {
    return (... && (str.find(substrs) != std::string::npos));
}

// ============================================================================
// 第四部分: 容器操作
// ============================================================================

/**
 * 向容器中插入多个元素
 * 使用逗号运算符折叠，依次调用 push_back
 */
template<typename Container, typename... Args>
void push_multiple(Container& c, Args&&... args) {
    // 逗号运算符折叠: 依次将每个参数插入容器
    (c.push_back(std::forward<Args>(args)), ...);
}

/**
 * 检查容器是否包含所有指定元素
 */
template<typename Container, typename... Args>
bool contains_all_elements(const Container& c, const Args&... args) {
    // 对每个参数检查是否在容器中
    return (... && (std::find(c.begin(), c.end(), args) != c.end()));
}

/**
 * 对多个容器执行相同操作
 * 使用折叠表达式对每个容器调用函数
 */
template<typename Func, typename... Containers>
void for_each_container(Func func, Containers&... containers) {
    // 对每个容器应用函数
    (func(containers), ...);
}

// ============================================================================
// 第五部分: 表达式求值与函数组合
// ============================================================================

/**
 * 编译期表达式求值
 * 使用折叠表达式在编译时计算复杂表达式
 */
template<typename... Args>
constexpr auto sum_squares(Args... args) {
    // 计算所有参数的平方和
    // 展开为: (arg1*arg1 + arg2*arg2 + ... + argN*argN)
    return (... + (args * args));
}

/**
 * 函数组合: compose(f, g, h)(x) = f(g(h(x)))
 *
 * 使用折叠表达式从右到左组合多个函数
 * 这是函数式编程中的经典模式
 *
 * 注意: pack init-capture (... funcs = ...) 需要 C++20，
 * 这里使用 tuple 存储函数来兼容 C++17。
 */
template<typename F, typename... Fs>
auto compose(F&& first, Fs&&... rest) {
    // 将所有函数存储在 tuple 中，用于 lambda 捕获
    auto funcs = std::make_tuple(std::forward<F>(first), std::forward<Fs>(rest)...);

    // 返回一个新函数，该函数依次应用所有组合的函数
    return [funcs = std::move(funcs)](auto&& arg) mutable {
        // 使用 std::apply 展开 tuple，从右到左应用函数
        // 这里简化实现: 使用索引序列从后向前应用
        auto result = std::forward<decltype(arg)>(arg);
        // 从最后一个函数开始，向前依次应用
        // tuple_size - 1, tuple_size - 2, ..., 0
        constexpr size_t N = std::tuple_size_v<decltype(funcs)>;
        // 使用编译期展开从右到左应用
        apply_reverse(funcs, result, std::make_index_sequence<N>{});
        return result;
    };
}

// 辅助函数: 从右到左应用 tuple 中的函数
template<typename Tuple, typename T, size_t... I>
void apply_reverse(Tuple& funcs, T& result, std::index_sequence<I...>) {
    // 使用折叠表达式和逗号运算符，从最后一个索引开始应用
    // 但由于 index_sequence 是升序的，我们需要反转
    // 这里使用一个技巧: 计算 N-1-I 来反转顺序
    constexpr size_t N = sizeof...(I);
    // 折叠表达式: 对每个索引 I，应用第 (N-1-I) 个函数
    ((result = std::get<N - 1 - I>(funcs)(std::move(result))), ...);
}

/**
 * 管道操作: 支持链式调用
 * 使用折叠表达式实现 Elixir 风格的管道操作
 *
 * 用法: pipe(value, func1, func2, func3)
 * 等价于: func3(func2(func1(value)))
 */
template<typename T, typename... Funcs>
auto pipe(T&& value, Funcs&&... funcs) {
    auto result = std::forward<T>(value);
    // 一元左折叠: 依次将结果传递给下一个函数
    // ((result = func1(result)), result = func2(result)), ..., result = funcN(result)
    ((result = std::invoke(std::forward<Funcs>(funcs), std::move(result))), ...);
    return result;
}

// ============================================================================
// 第六部分: 异常处理与日志
// ============================================================================

/**
 * 安全执行多个函数，忽略异常
 * 使用折叠表达式 + try-catch
 */
template<typename... Funcs>
void safe_execute_all(Funcs&&... funcs) {
    // 对每个函数捕获异常并记录
    (
        [&]() {
            try {
                std::forward<Funcs>(funcs)();
            } catch (const std::exception& e) {
                std::cout << "  [捕获异常] " << e.what() << std::endl;
            }
        }(), ...
    );
}

/**
 * 带日志的函数执行
 * 在执行前后打印信息
 */
template<typename... Funcs>
void logged_execute(Funcs&&... funcs) {
    size_t index = 0;
    (
        [&]() {
            std::cout << "  [执行 #" << index << "] ";
            std::forward<Funcs>(funcs)();
            std::cout << " -> 完成" << std::endl;
            ++index;
        }(), ...
    );
}

// ============================================================================
// 第七部分: 折叠表达式的四种形式对比
// ============================================================================

/**
 * 展示四种折叠形式的区别
 */
namespace fold_forms {

    // 一元右折叠: (pack op ...)
    // 展开: E1 op (E2 op (E3 op E4))
    template<typename... Args>
    auto unary_right_fold(Args... args) {
        return (args + ...);  // 1 + (2 + (3 + 4)) = 1 + (2 + 7) = 1 + 9 = 10
    }

    // 一元左折叠: (... op pack)
    // 展开: ((E1 op E2) op E3) op E4
    template<typename... Args>
    auto unary_left_fold(Args... args) {
        return (... + args);  // ((1 + 2) + 3) + 4 = (3 + 3) + 4 = 6 + 4 = 10
    }

    // 二元右折叠: (pack op ... op init)
    // 展开: E1 op (E2 op (E3 op (E4 op init)))
    template<typename... Args>
    auto binary_right_fold(Args... args) {
        return (args + ... + 100);  // 1 + (2 + (3 + (4 + 100))) = 1 + (2 + (3 + 104))
                                     // = 1 + (2 + 107) = 1 + 109 = 110
    }

    // 二元左折叠: (init op ... op pack)
    // 展开: (((init op E1) op E2) op E3) op E4
    template<typename... Args>
    auto binary_left_fold(Args... args) {
        return (100 + ... + args);  // (((100 + 1) + 2) + 3) + 4 = ((101 + 2) + 3) + 4
                                     // = (103 + 3) + 4 = 106 + 4 = 110
    }

} // namespace fold_forms

// ============================================================================
// 主函数: 演示所有功能
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  折叠表达式 (Fold Expressions) 演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // --- 1. 基础算术折叠 ---
    std::cout << "\n--- 1. 基础算术折叠 ---" << std::endl;
    std::cout << "sum(1,2,3,4,5): " << sum(1, 2, 3, 4, 5) << std::endl;
    std::cout << "sum_with_init(100, 1,2,3): " << sum_with_init(100, 1, 2, 3) << std::endl;
    std::cout << "product(2,3,4): " << product(2, 3, 4) << std::endl;
    std::cout << "subtract_left(10,2,3): " << subtract_left(10, 2, 3) << std::endl;
    std::cout << "subtract_right(10,2,3): " << subtract_right(10, 2, 3) << std::endl;
    std::cout << "  左折叠: ((10-2)-3) = 5" << std::endl;
    std::cout << "  右折叠: (10-(2-3)) = 10-(-1) = 11" << std::endl;

    // --- 2. 比较操作 ---
    std::cout << "\n--- 2. all/any/none 检查 ---" << std::endl;
    std::cout << "all_positive(1,2,3): " << std::boolalpha << all_positive(1, 2, 3) << std::endl;
    std::cout << "all_positive(1,-2,3): " << std::boolalpha << all_positive(1, -2, 3) << std::endl;
    std::cout << "any_positive(-1,-2,3): " << std::boolalpha << any_positive(-1, -2, 3) << std::endl;
    std::cout << "any_positive(-1,-2,-3): " << std::boolalpha << any_positive(-1, -2, -3) << std::endl;
    std::cout << "none_positive(-1,-2,-3): " << std::boolalpha << none_positive(-1, -2, -3) << std::endl;

    // 使用自定义谓词
    auto is_even = [](int x) { return x % 2 == 0; };
    std::cout << "all_of(is_even, 2,4,6): " << all_of_fold(is_even, 2, 4, 6) << std::endl;
    std::cout << "any_of(is_even, 1,3,4): " << any_of_fold(is_even, 1, 3, 4) << std::endl;

    // --- 3. 字符串操作 ---
    std::cout << "\n--- 3. 字符串连接 ---" << std::endl;
    std::cout << "join: " << join_strings(", ", "Hello", 42, 3.14, "World") << std::endl;
    std::cout << "concat: " << concat_strings("Hello", " ", "World", "!") << std::endl;
    std::cout << "contains_all: " << std::boolalpha
              << contains_all("Hello World", "Hello", "World") << std::endl;

    // --- 4. 容器操作 ---
    std::cout << "\n--- 4. 容器操作 ---" << std::endl;
    std::vector<int> vec;
    push_multiple(vec, 10, 20, 30, 40, 50);
    std::cout << "vec: ";
    for (const auto& v : vec) std::cout << v << " ";
    std::cout << std::endl;

    std::cout << "contains_all(10,20,30): " << std::boolalpha
              << contains_all_elements(vec, 10, 20, 30) << std::endl;
    std::cout << "contains_all(10,99,30): " << std::boolalpha
              << contains_all_elements(vec, 10, 99, 30) << std::endl;

    // --- 5. 表达式求值 ---
    std::cout << "\n--- 5. 编译期表达式 ---" << std::endl;
    std::cout << "sum_squares(1,2,3): " << sum_squares(1, 2, 3) << std::endl;
    std::cout << "  1² + 2² + 3² = 1 + 4 + 9 = 14" << std::endl;

    // --- 6. 函数组合 ---
    std::cout << "\n--- 6. 函数组合与管道 ---" << std::endl;
    auto double_it = [](int x) { return x * 2; };
    auto add_one = [](int x) { return x + 1; };
    auto square = [](int x) { return x * x; };

    // pipe: square(add_one(double_it(3))) = square(add_one(6)) = square(7) = 49
    int result = pipe(3, double_it, add_one, square);
    std::cout << "pipe(3, double, add_one, square): " << result << std::endl;

    // --- 7. 异常安全执行 ---
    std::cout << "\n--- 7. 安全执行 ---" << std::endl;
    safe_execute_all(
        []() { std::cout << "  [正常] 任务1" << std::endl; },
        []() { throw std::runtime_error("任务2失败"); },
        []() { std::cout << "  [正常] 任务3" << std::endl; }
    );

    // --- 8. 日志执行 ---
    std::cout << "\n--- 8. 带日志执行 ---" << std::endl;
    logged_execute(
        []() { std::cout << "初始化"; },
        []() { std::cout << "处理数据"; },
        []() { std::cout << "清理资源"; }
    );

    // --- 9. 四种折叠形式对比 ---
    std::cout << "\n--- 9. 四种折叠形式对比 ---" << std::endl;
    std::cout << "参数: (1, 2, 3, 4)" << std::endl;
    std::cout << "一元右折叠 (args + ...): "
              << fold_forms::unary_right_fold(1, 2, 3, 4) << std::endl;
    std::cout << "一元左折叠 (... + args): "
              << fold_forms::unary_left_fold(1, 2, 3, 4) << std::endl;
    std::cout << "二元右折叠 (args + ... + 100): "
              << fold_forms::binary_right_fold(1, 2, 3, 4) << std::endl;
    std::cout << "二元左折叠 (100 + ... + args): "
              << fold_forms::binary_left_fold(1, 2, 3, 4) << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "  演示结束" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
