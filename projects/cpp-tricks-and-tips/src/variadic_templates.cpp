/**
 * variadic_templates.cpp - 可变参数模板 (Variadic Templates)
 *
 * 编译命令: g++ -std=c++17 -o variadic_templates variadic_templates.cpp
 *
 * 本文件演示 C++11 引入、C++17 增强的可变参数模板技术，包括:
 *   1. 可变参数打印函数
 *   2. 类 Tuple 容器实现
 *   3. 递归展开参数包
 *   4. 折叠表达式整合
 *
 * 可变参数模板允许模板接受任意数量、任意类型的参数，
 * 是现代 C++ 泛型编程的基石之一。
 */

#include <iostream>
#include <string>
#include <tuple>
#include <utility>
#include <typeinfo>
#include <array>

// ============================================================================
// 第一部分: 基础可变参数打印函数
// ============================================================================

/**
 * 基础版本 - 使用递归展开参数包
 *
 * 可变参数模板的三要素:
 *   1. 模板参数包 (Parameter Pack): typename... Args
 *   2. 函数参数包 (Function Parameter Pack): Args&&... args
 *   3. 包展开 (Pack Expansion): args... 或表达式(args)...
 *
 * 递归展开需要一个"终止函数"来处理参数包为空的情况。
 */

// 终止函数: 当参数包为空时调用此版本
// 没有参数时打印换行，结束递归
inline void print_basic() {
    std::cout << std::endl;
}

// 递归展开: 每次取出第一个参数，剩余参数继续递归
// 第一个参数 first 通过完美转发取出
// 剩余参数 rest... 继续传递给下一次调用
template<typename T, typename... Args>
void print_basic(T&& first, Args&&... rest) {
    std::cout << std::forward<T>(first);

    // 如果还有剩余参数，打印分隔符
    if constexpr (sizeof...(rest) > 0) {
        std::cout << ", ";
    }

    // 递归调用，展开剩余参数
    print_basic(std::forward<Args>(rest)...);
}

/**
 * C++17 折叠表达式版本 - 无需终止函数
 *
 * 使用一元左折叠 (unary left fold):
 *   (args << ... << expr) 展开为 arg1 << arg2 << ... << argN
 *
 * 优势: 代码简洁，无需递归，编译效率更高
 */
template<typename... Args>
void print_fold(Args&&... args) {
    // 一元左折叠: 对参数包中每个元素应用 << 运算符
    // 展开形式: (std::cout << arg1 << ", " << arg2 << ", " << ... << argN)
    // 注意: 最后一个参数后面也会有多余的 ", "，这里用 lambda 优化
    ((std::cout << std::forward<Args>(args)), ...);
    std::cout << std::endl;
}

/**
 * 优化版: 带自定义分隔符的打印函数
 * 使用折叠表达式配合逗号运算符
 */
template<typename... Args>
void print_with_sep(const std::string& sep, Args&&... args) {
    bool first = true;
    // 逗号运算符折叠: 对每个参数执行 lambda 表达式
    // ((lambda(arg1), lambda(arg2), ..., lambda(argN)))
    (
        [&]() {
            if (!first) std::cout << sep;
            std::cout << std::forward<Args>(args);
            first = false;
        }(), ...
    );
    std::cout << std::endl;
}

// ============================================================================
// 第二部分: 类 Tuple 容器实现
// ============================================================================

/**
 * 简易 Tuple 实现 - 展示可变参数模板的递归继承技巧
 *
 * 核心思想: 使用递归继承来存储不同类型的元素
 *   Tuple<int, double, string>
 *     -> 继承自 Tuple<double, string>  (存储 int)
 *       -> 继承自 Tuple<string>        (存储 double)
 *         -> 继承自 Tuple<>            (存储 string)
 *           -> 空基类 (递归终止)
 *
 * 这种设计称为"递归继承"或"mixin继承"，是 STL 内部实现 tuple 的常见方式。
 */

// 基础模板: 存储第一个元素，继承自剩余元素的 Tuple
template<typename... Elements>
class SimpleTuple;

// 空特化: 递归终止条件，空 Tuple 作为基类
template<>
class SimpleTuple<> {
public:
    // 空 tuple 没有数据成员
};

// 递归特化: 存储 Head，继承自 Tail... 的 SimpleTuple
template<typename Head, typename... Tail>
class SimpleTuple<Head, Tail...> : private SimpleTuple<Tail...> {
private:
    Head value_;  // 存储当前元素

public:
    // 构造函数: 接受第一个参数存储，其余参数转发给基类
    SimpleTuple(Head&& head, Tail&&... tail)
        : SimpleTuple<Tail...>(std::forward<Tail>(tail)...)
        , value_(std::forward<Head>(head)) {}

    // 获取当前元素的值
    Head& head() { return value_; }
    const Head& head() const { return value_; }

    // 获取剩余元素组成的 Tuple (即基类部分)
    SimpleTuple<Tail...>& tail() {
        return static_cast<SimpleTuple<Tail...>&>(*this);
    }
    const SimpleTuple<Tail...>& tail() const {
        return static_cast<const SimpleTuple<Tail...>&>(*this);
    }
};

/**
 * 辅助函数: 获取 Tuple 中第 N 个元素
 * 使用递归模板函数实现编译期索引访问
 *
 * 使用 constexpr if 替代 SFINAE 来处理递归终止条件，
 * 代码更简洁，编译错误信息也更友好。
 */
template<size_t N, typename Head, typename... Tail>
auto& get_tuple_element(SimpleTuple<Head, Tail...>& t) {
    if constexpr (N == 0) {
        // 当 N == 0 时，返回当前头部元素
        return t.head();
    } else {
        // 当 N > 0 时，递归到尾部 tuple，N 减 1
        return get_tuple_element<N - 1>(t.tail());
    }
}

/**
 * make_simple_tuple 辅助函数: 利用模板参数推导简化创建
 * 类似于 std::make_tuple 的实现原理
 */
template<typename... Args>
SimpleTuple<typename std::decay<Args>::type...> make_simple_tuple(Args&&... args) {
    // std::decay 移除引用和 cv 限定符，确保存储的是值类型
    return SimpleTuple<typename std::decay<Args>::type...>(
        std::forward<Args>(args)...
    );
}

// ============================================================================
// 第三部分: 参数包的各种操作技巧
// ============================================================================

/**
 * 编译期计算参数包大小
 * sizeof... 运算符是 C++11 引入的，用于获取参数包中的元素数量
 */
template<typename... Args>
constexpr size_t count_args(Args&&...) {
    return sizeof...(Args);  // 返回类型参数包的大小
}

/**
 * 编译期判断参数包是否包含某个类型
 * 使用递归模板 + constexpr if 实现
 */
template<typename Target, typename... Types>
constexpr bool contains_type() {
    // 折叠表达式: 检查是否存在类型与 Target 相同
    return (std::is_same_v<Target, Types> || ...);
}

/**
 * 所有参数都满足某个条件
 * 使用折叠表达式检查所有参数是否都为正数
 */
template<typename... Args>
constexpr bool all_positive(Args... args) {
    // 一元右折叠: (args > 0 && ...)
    return ((args > 0) && ...);
}

/**
 * 对所有参数应用函数
 * 使用折叠表达式对参数包中的每个元素执行操作
 */
template<typename Func, typename... Args>
void for_each_arg(Func func, Args&&... args) {
    // 逗号运算符折叠: 对每个参数调用 func
    // (func(arg1), func(arg2), ..., func(argN))
    (func(std::forward<Args>(args)), ...);
}

/**
 * 使用索引序列 (index_sequence) 展开元组参数
 * 这是调用 tuple 元素展开的关键技术
 */
template<typename Tuple, typename Func, size_t... I>
auto apply_impl(Tuple&& t, Func&& func, std::index_sequence<I...>) {
    // 使用 get<I> 展开 tuple 中的每个元素作为函数参数
    return func(std::get<I>(std::forward<Tuple>(t))...);
}

template<typename Tuple, typename Func>
auto apply_from_tuple(Tuple&& t, Func&& func) {
    // 获取 tuple 大小，生成索引序列 0, 1, 2, ..., N-1
    constexpr size_t size = std::tuple_size_v<std::decay_t<Tuple>>;
    return apply_impl(
        std::forward<Tuple>(t),
        std::forward<Func>(func),
        std::make_index_sequence<size>{}
    );
}

// ============================================================================
// 第四部分: 高级用法 - 类型萃取与参数包操作
// ============================================================================

/**
 * 编译期查找最大类型大小
 * 使用折叠表达式比较所有类型 sizeof 的最大值
 */
template<typename... Types>
constexpr size_t max_type_size() {
    // 折叠表达式取最大值: (max(sizeof(T1), sizeof(T2), ..., sizeof(TN)))
    size_t max_size = 0;
    ((max_size = (sizeof(Types) > max_size ? sizeof(Types) : max_size)), ...);
    return max_size;
}

/**
 * 编译期计算所有类型大小之和
 */
template<typename... Types>
constexpr size_t total_type_size() {
    // 一元右折叠求和: (sizeof(T1) + sizeof(T2) + ... + sizeof(TN))
    return (sizeof(Types) + ...);
}

/**
 * 创建类型数组的辅助模板
 * 使用折叠表达式初始化数组
 */
template<typename T, typename... Args>
auto make_array(Args&&... args) {
    // 直接使用初始化列表展开参数包
    // 注意: std::array 是聚合类型，需要双花括号初始化
    return std::array<T, sizeof...(Args)>{{std::forward<Args>(args)...}};
}

// ============================================================================
// 主函数: 演示所有功能
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  可变参数模板 (Variadic Templates) 演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // --- 1. 基础递归打印 ---
    std::cout << "\n--- 1. 递归展开打印 ---" << std::endl;
    print_basic(1, 3.14, "hello", 'c', true);

    // --- 2. 折叠表达式打印 ---
    std::cout << "\n--- 2. 折叠表达式打印 ---" << std::endl;
    print_fold("apple", 42, 2.718, "world");

    // --- 3. 带分隔符打印 ---
    std::cout << "\n--- 3. 自定义分隔符打印 ---" << std::endl;
    print_with_sep(" | ", "C++", 17, 3.14, "templates");

    // --- 4. 参数包大小 ---
    std::cout << "\n--- 4. 参数包大小 ---" << std::endl;
    std::cout << "count_args(1,2,3): " << count_args(1, 2, 3) << std::endl;
    std::cout << "count_args('a','b'): " << count_args('a', 'b') << std::endl;

    // --- 5. 类型检查 ---
    std::cout << "\n--- 5. 类型包含检查 ---" << std::endl;
    std::cout << "int in (int, double, char): "
              << std::boolalpha << contains_type<int, int, double, char>() << std::endl;
    std::cout << "float in (int, double, char): "
              << std::boolalpha << contains_type<float, int, double, char>() << std::endl;

    // --- 6. 条件检查 ---
    std::cout << "\n--- 6. 折叠表达式条件检查 ---" << std::endl;
    std::cout << "all_positive(1,2,3): " << std::boolalpha << all_positive(1, 2, 3) << std::endl;
    std::cout << "all_positive(1,-2,3): " << std::boolalpha << all_positive(1, -2, 3) << std::endl;

    // --- 7. for_each 操作 ---
    std::cout << "\n--- 7. for_each 应用 ---" << std::endl;
    for_each_arg(
        [](const auto& x) { std::cout << "[" << x << "] "; },
        10, 20.5, "hello", 'Z'
    );
    std::cout << std::endl;

    // --- 8. SimpleTuple 操作 ---
    std::cout << "\n--- 8. 简易 Tuple 实现 ---" << std::endl;
    auto my_tuple = make_simple_tuple(42, 3.14, std::string("Hello"));
    std::cout << "head: " << my_tuple.head() << std::endl;
    std::cout << "tail().head(): " << my_tuple.tail().head() << std::endl;
    std::cout << "tail().tail().head(): " << my_tuple.tail().tail().head() << std::endl;

    // 使用编译期索引访问
    std::cout << "get<0>: " << get_tuple_element<0>(my_tuple) << std::endl;
    std::cout << "get<1>: " << get_tuple_element<1>(my_tuple) << std::endl;
    std::cout << "get<2>: " << get_tuple_element<2>(my_tuple) << std::endl;

    // --- 9. apply_from_tuple ---
    std::cout << "\n--- 9. 从 Tuple 展开参数调用函数 ---" << std::endl;
    auto std_tuple = std::make_tuple(10, 20);
    auto sum = apply_from_tuple(std_tuple, [](int a, int b) { return a + b; });
    std::cout << "apply_from_tuple(add, (10, 20)): " << sum << std::endl;

    // --- 10. 编译期类型大小计算 ---
    std::cout << "\n--- 10. 编译期类型大小计算 ---" << std::endl;
    std::cout << "max_type_size<int, double, char>(): "
              << max_type_size<int, double, char>() << " bytes" << std::endl;
    std::cout << "total_type_size<int, double, char>(): "
              << total_type_size<int, double, char>() << " bytes" << std::endl;

    // --- 11. 参数包展开创建数组 ---
    std::cout << "\n--- 11. 参数包创建数组 ---" << std::endl;
    auto arr = make_array<int>(1, 2, 3, 4, 5);
    for (const auto& val : arr) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "  演示结束" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
