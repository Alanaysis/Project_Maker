#pragma once
// =============================================================================
// integer_sequence.hpp - 编译期整数序列 (Compile-Time Integer Sequence)
// =============================================================================
// integer_sequence 是 C++14 引入的编译期数据结构
// 用于存储编译期整数序列，常用于参数包展开和索引操作
// =============================================================================

#include <cstddef>
#include <type_traits>
#include <array>
#include <tuple>

namespace tmp {

// ---------------------------------------------------------------------------
// integer_sequence 基础定义
// ---------------------------------------------------------------------------
template <typename T, T... Ints>
struct integer_sequence {
    using value_type = T;
    static constexpr std::size_t size() noexcept { return sizeof...(Ints); }
};

// index_sequence: integer_sequence 的特化，类型为 size_t
template <std::size_t... Is>
using index_sequence = integer_sequence<std::size_t, Is...>;

// ---------------------------------------------------------------------------
// make_integer_sequence - 生成 [0, N) 的整数序列
// ---------------------------------------------------------------------------

// 递归实现
namespace detail {
    template <typename T, typename Seq, T N>
    struct make_integer_sequence_impl;

    template <typename T, T... Ints, T N>
    struct make_integer_sequence_impl<T, integer_sequence<T, Ints...>, N>
        : make_integer_sequence_impl<T, integer_sequence<T, Ints..., sizeof...(Ints)>, N - 1> {};

    template <typename T, T... Ints>
    struct make_integer_sequence_impl<T, integer_sequence<T, Ints...>, 0> {
        using type = integer_sequence<T, Ints...>;
    };
}

template <typename T, T N>
using make_integer_sequence = typename detail::make_integer_sequence_impl<
    T, integer_sequence<T>, N>::type;

// make_index_sequence: 生成 [0, N) 的 size_t 序列
template <std::size_t N>
using make_index_sequence = make_integer_sequence<std::size_t, N>;

// ---------------------------------------------------------------------------
// index_sequence_for - 为参数包生成索引序列
// ---------------------------------------------------------------------------
template <typename... Ts>
using index_sequence_for = make_index_sequence<sizeof...(Ts)>;

// ---------------------------------------------------------------------------
// integer_sequence 的基本操作
// ---------------------------------------------------------------------------

// 获取序列中指定位置的值
namespace detail {
    template <std::size_t I, typename Seq>
    struct sequence_element;

    template <std::size_t I, typename T, T First, T... Rest>
    struct sequence_element<I, integer_sequence<T, First, Rest...>>
        : sequence_element<I - 1, integer_sequence<T, Rest...>> {};

    template <typename T, T First, T... Rest>
    struct sequence_element<0, integer_sequence<T, First, Rest...>> {
        static constexpr T value = First;
    };
}

template <std::size_t I, typename Seq>
inline constexpr auto sequence_element_v = detail::sequence_element<I, Seq>::value;

// 获取序列的第一个元素
template <typename Seq>
struct sequence_front;

template <typename T, T First, T... Rest>
struct sequence_front<integer_sequence<T, First, Rest...>> {
    static constexpr T value = First;
};

template <typename Seq>
inline constexpr auto sequence_front_v = sequence_front<Seq>::value;

// 获取序列的最后一个元素
template <typename Seq>
struct sequence_back;

template <typename T, T... Ints>
struct sequence_back<integer_sequence<T, Ints...>> {
    // 使用逗号运算符获取最后一个值
    static constexpr T value = (Ints, ...);
};

template <typename Seq>
inline constexpr auto sequence_back_v = sequence_back<Seq>::value;

// ---------------------------------------------------------------------------
// integer_sequence 的变换操作
// ---------------------------------------------------------------------------

// 反转序列
namespace detail {
    template <typename T, typename Seq, typename Result = integer_sequence<T>>
    struct reverse_sequence_impl;

    template <typename T, T First, T... Rest, T... Result>
    struct reverse_sequence_impl<T, integer_sequence<T, First, Rest...>,
                                  integer_sequence<T, Result...>>
        : reverse_sequence_impl<T, integer_sequence<T, Rest...>,
                                integer_sequence<T, First, Result...>> {};

    template <typename T, T... Result>
    struct reverse_sequence_impl<T, integer_sequence<T>, integer_sequence<T, Result...>> {
        using type = integer_sequence<T, Result...>;
    };
}

template <typename Seq>
struct reverse_sequence : detail::reverse_sequence_impl<typename Seq::value_type, Seq> {};

template <typename Seq>
using reverse_sequence_t = typename reverse_sequence<Seq>::type;

// 连接两个序列
template <typename Seq1, typename Seq2>
struct concat_sequence;

template <typename T, T... Ints1, T... Ints2>
struct concat_sequence<integer_sequence<T, Ints1...>, integer_sequence<T, Ints2...>> {
    using type = integer_sequence<T, Ints1..., Ints2...>;
};

template <typename Seq1, typename Seq2>
using concat_sequence_t = typename concat_sequence<Seq1, Seq2>::type;

// 对序列中的每个元素应用变换
template <template<auto> class Func, typename Seq>
struct transform_sequence;

template <template<auto> class Func, typename T, T... Ints>
struct transform_sequence<Func, integer_sequence<T, Ints...>> {
    using type = integer_sequence<decltype(Func<Ints>::value), Func<Ints>::value...>;
};

template <template<auto> class Func, typename Seq>
using transform_sequence_t = typename transform_sequence<Func, Seq>::type;

// ---------------------------------------------------------------------------
// integer_sequence 的归约操作
// ---------------------------------------------------------------------------

// 求和
template <typename Seq>
struct sequence_sum;

template <typename T, T... Ints>
struct sequence_sum<integer_sequence<T, Ints...>> {
    static constexpr T value = (Ints + ...);
};

template <typename Seq>
inline constexpr auto sequence_sum_v = sequence_sum<Seq>::value;

// 求积
template <typename Seq>
struct sequence_product;

template <typename T, T... Ints>
struct sequence_product<integer_sequence<T, Ints...>> {
    static constexpr T value = (Ints * ...);
};

template <typename Seq>
inline constexpr auto sequence_product_v = sequence_product<Seq>::value;

// 最大值
template <typename Seq>
struct sequence_max;

template <typename T, T First, T... Rest>
struct sequence_max<integer_sequence<T, First, Rest...>> {
    static constexpr T value = [] {
        T max_val = First;
        for (T val : {Rest...}) {
            if (val > max_val) max_val = val;
        }
        return max_val;
    }();
};

// ---------------------------------------------------------------------------
// 实用工具：索引序列遍历 tuple
// ---------------------------------------------------------------------------

// 使用 index_sequence 遍历 tuple
template <typename Tuple, typename F, std::size_t... Is>
void for_each_impl(Tuple&& t, F&& f, index_sequence<Is...>) {
    (f(std::get<Is>(std::forward<Tuple>(t))), ...);
}

template <typename Tuple, typename F>
void for_each(Tuple&& t, F&& f) {
    constexpr std::size_t size = std::tuple_size_v<std::remove_reference_t<Tuple>>;
    for_each_impl(std::forward<Tuple>(t), std::forward<F>(f),
                  make_index_sequence<size>{});
}

// 使用 index_sequence 将 tuple 转为数组
template <typename Tuple, std::size_t... Is>
auto tuple_to_array_impl(Tuple&& t, index_sequence<Is...>) {
    return std::array{std::get<Is>(std::forward<Tuple>(t))...};
}

template <typename Tuple>
auto tuple_to_array(Tuple&& t) {
    constexpr std::size_t size = std::tuple_size_v<std::remove_reference_t<Tuple>>;
    return tuple_to_array_impl(std::forward<Tuple>(t), make_index_sequence<size>{});
}

// ---------------------------------------------------------------------------
// 实用工具：生成编译期查找表
// ---------------------------------------------------------------------------

// 生成平方数序列
template <std::size_t... Is>
constexpr auto make_square_sequence(index_sequence<Is...>) {
    return integer_sequence<std::size_t, (Is * Is)...>{};
}

// 生成斐波那契数列序列
namespace detail {
    template <std::size_t A, std::size_t B, std::size_t N, std::size_t... Fibs>
    struct fib_sequence_impl
        : fib_sequence_impl<B, A + B, N - 1, Fibs..., A> {};

    template <std::size_t A, std::size_t B, std::size_t... Fibs>
    struct fib_sequence_impl<A, B, 0, Fibs...> {
        using type = integer_sequence<std::size_t, Fibs...>;
    };
}

template <std::size_t N>
struct fib_sequence : detail::fib_sequence_impl<0, 1, N> {};

template <std::size_t N>
using fib_sequence_t = typename fib_sequence<N>::type;

// ---------------------------------------------------------------------------
// 实用工具：编译期数组初始化
// ---------------------------------------------------------------------------

// 使用索引序列初始化数组
template <typename T, std::size_t N, typename Func, std::size_t... Is>
constexpr std::array<T, N> make_array_impl(Func func, index_sequence<Is...>) {
    return {{func(Is)...}};
}

template <typename T, std::size_t N, typename Func>
constexpr std::array<T, N> make_array(Func func) {
    return make_array_impl<T, N>(func, make_index_sequence<N>{});
}

// 使用索引序列进行批量赋值
template <typename Tuple, typename Values, std::size_t... Is>
void assign_from_tuple_impl(Tuple& dest, const Values& src, index_sequence<Is...>) {
    ((std::get<Is>(dest) = std::get<Is>(src)), ...);
}

template <typename Tuple, typename Values>
void assign_from_tuple(Tuple& dest, const Values& src) {
    constexpr std::size_t size = std::tuple_size_v<Tuple>;
    assign_from_tuple_impl(dest, src, make_index_sequence<size>{});
}

} // namespace tmp
