#pragma once
// =============================================================================
// fold_expressions.hpp - 折叠表达式 (Fold Expressions, C++17)
// =============================================================================
// 折叠表达式是 C++17 引入的强大特性
// 可以简洁地对参数包中的所有元素应用二元运算
// =============================================================================

#include <iostream>
#include <string>
#include <type_traits>
#include <initializer_list>
#include <array>

namespace tmp {
namespace fold {

// ---------------------------------------------------------------------------
// 四种折叠表达式形式
// ---------------------------------------------------------------------------
// 1. (... op pack)         - 一元左折叠
// 2. (pack op ...)         - 一元右折叠
// 3. (init op ... op pack) - 二元左折叠
// 4. (pack op ... op init) - 二元右折叠

// ---------------------------------------------------------------------------
// 一元折叠
// ---------------------------------------------------------------------------

// 一元左折叠：(... + args) = ((a1 + a2) + a3) + ...
template <typename... Args>
auto sum_left(Args... args) {
    return (... + args);  // 左折叠
}

// 一元右折叠：(args + ...) = a1 + (a2 + (a3 + ...))
template <typename... Args>
auto sum_right(Args... args) {
    return (args + ...);  // 右折叠
}

// 逗号折叠：打印所有参数
template <typename... Args>
void print_all(Args... args) {
    ((std::cout << args << " "), ...);  // 逗号运算符折叠
    std::cout << std::endl;
}

// 逻辑与折叠：检查所有参数是否为真
template <typename... Args>
bool all_true(Args... args) {
    return (... && args);  // 逻辑与折叠
}

// 逻辑或折叠：检查是否有任意参数为真
template <typename... Args>
bool any_true(Args... args) {
    return (... || args);  // 逻辑或折叠
}

// ---------------------------------------------------------------------------
// 二元折叠
// ---------------------------------------------------------------------------

// 带初始值的左折叠：(init + ... + args)
template <typename... Args>
auto sum_with_init(double init, Args... args) {
    return (init + ... + args);
}

// 带初始值的右折叠：(args + ... + init)
template <typename... Args>
auto sum_right_with_init(Args... args, double init) {
    return (args + ... + init);
}

// ---------------------------------------------------------------------------
// 实用折叠表达式
// ---------------------------------------------------------------------------

// 检查所有类型是否相同
template <typename T, typename... Args>
constexpr bool are_all_same() {
    return (std::is_same_v<T, Args> && ...);
}

// 检查所有类型是否满足某个谓词
template <template<typename> class Pred, typename... Args>
constexpr bool all_satisfy() {
    return (Pred<Args>::value && ...);
}

// 统计满足条件的参数个数
template <typename Pred, typename... Args>
std::size_t count_if(Pred pred, Args... args) {
    return (0 + ... + (pred(args) ? 1 : 0));
}

// 查找第一个满足条件的参数
template <typename Pred, typename... Args>
auto find_first(Pred pred, Args... args) -> decltype(auto) {
    // 使用短路求值
    decltype(auto) result = (pred(args) ? args : ...);
    return result;
}

// 对所有参数应用函数
template <typename Func, typename... Args>
void for_each(Func func, Args&... args) {
    (func(args), ...);
}

// 将参数收集到数组
template <typename T, typename... Args>
auto to_array(Args... args) {
    return std::array<T, sizeof...(args)>{static_cast<T>(args)...};
}

// 检查所有参数是否在范围内
template <typename T, typename... Args>
bool all_in_range(T low, T high, Args... args) {
    return (... && (args >= low && args <= high));
}

// 拼接字符串
template <typename... Args>
std::string concat(Args... args) {
    std::string result;
    (result += ... += std::to_string(args));
    return result;
}

// 字符串拼接版本
template <typename... Args>
std::string concat_strings(Args... args) {
    return (std::string{} + ... + args);
}

// ---------------------------------------------------------------------------
// 编译期折叠
// ---------------------------------------------------------------------------

// 编译期求和
template <auto... Values>
constexpr auto constexpr_sum() {
    return (Values + ...);
}

// 编译期求积
template <auto... Values>
constexpr auto constexpr_product() {
    return (Values * ...);
}

// 编译期最大值
template <auto First, auto... Rest>
constexpr auto constexpr_max() {
    if constexpr (sizeof...(Rest) == 0) {
        return First;
    } else {
        auto rest_max = constexpr_max<Rest...>();
        return First > rest_max ? First : rest_max;
    }
}

// 编译期最小值
template <auto First, auto... Rest>
constexpr auto constexpr_min() {
    if constexpr (sizeof...(Rest) == 0) {
        return First;
    } else {
        auto rest_min = constexpr_min<Rest...>();
        return First < rest_min ? First : rest_min;
    }
}

// ---------------------------------------------------------------------------
// 折叠表达式的高级应用
// ---------------------------------------------------------------------------

// 类型列表的编译期操作
template <typename... Ts>
struct TypeList {
    static constexpr std::size_t size = sizeof...(Ts);
};

// 连接多个 TypeList
template <typename... Lists>
struct Concat;

template <typename... Ts, typename... Us, typename... Rest>
struct Concat<TypeList<Ts...>, TypeList<Us...>, Rest...>
    : Concat<TypeList<Ts..., Us...>, Rest...> {};

template <typename... Ts>
struct Concat<TypeList<Ts...>> {
    using type = TypeList<Ts...>;
};

template <typename... Lists>
using Concat_t = typename Concat<Lists...>::type;

// 使用折叠表达式实现多态调用
template <typename Visitor, typename... Visitable>
void visit_all(Visitor& visitor, Visitable&... visitable) {
    (visitable.accept(visitor), ...);
}

// 安全的批量释放资源
template <typename... Ptrs>
void safe_delete_all(Ptrs*... ptrs) {
    ((delete ptrs, ptrs = nullptr), ...);
}

} // namespace fold
} // namespace tmp
