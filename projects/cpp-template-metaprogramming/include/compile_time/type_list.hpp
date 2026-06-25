#pragma once
// =============================================================================
// type_list.hpp - 编译期类型列表 (Compile-Time Type List)
// =============================================================================
// TypeList 是模板元编程中最重要的数据结构
// 类似于函数式编程中的 List，但操作都在编译期完成
// =============================================================================

#include <cstddef>
#include <type_traits>

namespace tmp {

// ---------------------------------------------------------------------------
// TypeList 基础定义
// ---------------------------------------------------------------------------
template <typename... Ts>
struct TypeList {
    static constexpr std::size_t size = sizeof...(Ts);
};

// 空列表
using EmptyList = TypeList<>;

// ---------------------------------------------------------------------------
// 基本操作
// ---------------------------------------------------------------------------

// 获取第一个类型 (head)
template <typename List>
struct Front;

template <typename Head, typename... Tail>
struct Front<TypeList<Head, Tail...>> {
    using type = Head;
};

template <typename List>
using Front_t = typename Front<List>::type;

// 获取除第一个外的所有类型 (tail)
template <typename List>
struct PopFront;

template <typename Head, typename... Tail>
struct PopFront<TypeList<Head, Tail...>> {
    using type = TypeList<Tail...>;
};

template <typename List>
using PopFront_t = typename PopFront<List>::type;

// 在头部插入类型 (push_front)
template <typename List, typename T>
struct PushFront;

template <typename... Ts, typename T>
struct PushFront<TypeList<Ts...>, T> {
    using type = TypeList<T, Ts...>;
};

template <typename List, typename T>
using PushFront_t = typename PushFront<List, T>::type;

// 在尾部插入类型 (push_back)
template <typename List, typename T>
struct PushBack;

template <typename... Ts, typename T>
struct PushBack<TypeList<Ts...>, T> {
    using type = TypeList<Ts..., T>;
};

template <typename List, typename T>
using PushBack_t = typename PushBack<List, T>::type;

// ---------------------------------------------------------------------------
// 索引访问
// ---------------------------------------------------------------------------

// 获取第 N 个类型
namespace detail {
    template <std::size_t N, typename List>
    struct GetImpl;

    template <std::size_t N, typename Head, typename... Tail>
    struct GetImpl<N, TypeList<Head, Tail...>>
        : GetImpl<N - 1, TypeList<Tail...>> {};

    template <typename Head, typename... Tail>
    struct GetImpl<0, TypeList<Head, Tail...>> {
        using type = Head;
    };
}

template <std::size_t N, typename List>
struct Get : detail::GetImpl<N, List> {};

template <std::size_t N, typename List>
using Get_t = typename Get<N, List>::type;

// ---------------------------------------------------------------------------
// 查找操作
// ---------------------------------------------------------------------------

// 查找类型在列表中的索引
namespace detail {
    template <typename T, typename List, std::size_t Index = 0>
    struct IndexOfImpl;

    template <typename T, typename Head, typename... Tail, std::size_t Index>
    struct IndexOfImpl<T, TypeList<Head, Tail...>, Index>
        : IndexOfImpl<T, TypeList<Tail...>, Index + 1> {};

    template <typename T, typename... Tail, std::size_t Index>
    struct IndexOfImpl<T, TypeList<T, Tail...>, Index> {
        static constexpr std::size_t value = Index;
    };
}

template <typename T, typename List>
struct IndexOf : detail::IndexOfImpl<T, List> {};

template <typename T, typename List>
inline constexpr std::size_t IndexOf_v = IndexOf<T, List>::value;

// 检查类型是否在列表中
template <typename T, typename List>
struct Contains;

template <typename T, typename List>
struct Contains : std::false_type {};

// 需要一个辅助来展开
namespace detail {
    template <typename T, typename... Ts>
    struct ContainsImpl : std::false_type {};

    template <typename T, typename First, typename... Rest>
    struct ContainsImpl<T, First, Rest...>
        : std::conditional_t<std::is_same_v<T, First>,
                             std::true_type,
                             ContainsImpl<T, Rest...>> {};
}

template <typename T, typename... Ts>
struct Contains<T, TypeList<Ts...>> : detail::ContainsImpl<T, Ts...> {};

template <typename T, typename List>
inline constexpr bool Contains_v = Contains<T, List>::value;

// ---------------------------------------------------------------------------
// 转换操作
// ---------------------------------------------------------------------------

// 对每个类型应用变换
template <template<typename> class Func, typename List>
struct Transform;

template <template<typename> class Func, typename... Ts>
struct Transform<Func, TypeList<Ts...>> {
    using type = TypeList<typename Func<Ts>::type...>;
};

template <template<typename> class Func, typename List>
using Transform_t = typename Transform<Func, List>::type;

// ---------------------------------------------------------------------------
// 过滤操作
// ---------------------------------------------------------------------------

// 过滤满足条件的类型
namespace detail {
    template <template<typename> class Pred, typename List, typename Result = TypeList<>>
    struct FilterImpl;

    template <template<typename> class Pred, typename Result>
    struct FilterImpl<Pred, TypeList<>, Result> {
        using type = Result;
    };

    template <template<typename> class Pred, typename Head, typename... Tail, typename... Result>
    struct FilterImpl<Pred, TypeList<Head, Tail...>, TypeList<Result...>>
        : FilterImpl<Pred, TypeList<Tail...>,
              std::conditional_t<Pred<Head>::value,
                                 TypeList<Result..., Head>,
                                 TypeList<Result...>>> {};
}

template <template<typename> class Pred, typename List>
struct Filter : detail::FilterImpl<Pred, List> {};

template <template<typename> class Pred, typename List>
using Filter_t = typename Filter<Pred, List>::type;

// ---------------------------------------------------------------------------
// 折叠操作
// ---------------------------------------------------------------------------

// 左折叠
namespace detail {
    template <template<typename, typename> class Func, typename Init, typename List>
    struct FoldLeftImpl;

    template <template<typename, typename> class Func, typename Init>
    struct FoldLeftImpl<Func, Init, TypeList<>> {
        using type = Init;
    };

    template <template<typename, typename> class Func, typename Init,
              typename Head, typename... Tail>
    struct FoldLeftImpl<Func, Init, TypeList<Head, Tail...>>
        : FoldLeftImpl<Func, typename Func<Init, Head>::type, TypeList<Tail...>> {};
}

template <template<typename, typename> class Func, typename Init, typename List>
struct FoldLeft : detail::FoldLeftImpl<Func, Init, List> {};

template <template<typename, typename> class Func, typename Init, typename List>
using FoldLeft_t = typename FoldLeft<Func, Init, List>::type;

// ---------------------------------------------------------------------------
// 连接操作
// ---------------------------------------------------------------------------

template <typename List1, typename List2>
struct Concat;

template <typename... Ts, typename... Us>
struct Concat<TypeList<Ts...>, TypeList<Us...>> {
    using type = TypeList<Ts..., Us...>;
};

template <typename List1, typename List2>
using Concat_t = typename Concat<List1, List2>::type;

// ---------------------------------------------------------------------------
// 反转操作
// ---------------------------------------------------------------------------

namespace detail {
    template <typename List, typename Result = TypeList<>>
    struct ReverseImpl;

    template <typename Result>
    struct ReverseImpl<TypeList<>, Result> {
        using type = Result;
    };

    template <typename Head, typename... Tail, typename... Result>
    struct ReverseImpl<TypeList<Head, Tail...>, TypeList<Result...>>
        : ReverseImpl<TypeList<Tail...>, TypeList<Head, Result...>> {};
}

template <typename List>
struct Reverse : detail::ReverseImpl<List> {};

template <typename List>
using Reverse_t = typename Reverse<List>::type;

// ---------------------------------------------------------------------------
// 去重操作
// ---------------------------------------------------------------------------

namespace detail {
    template <typename List, typename Seen = TypeList<>>
    struct UniqueImpl;

    template <typename... Seen>
    struct UniqueImpl<TypeList<>, TypeList<Seen...>> {
        using type = TypeList<Seen...>;
    };

    template <typename Head, typename... Tail, typename... Seen>
    struct UniqueImpl<TypeList<Head, Tail...>, TypeList<Seen...>>
        : std::conditional_t<
            Contains<Head, TypeList<Seen...>>::value,
            UniqueImpl<TypeList<Tail...>, TypeList<Seen...>>,
            UniqueImpl<TypeList<Tail...>, TypeList<Seen..., Head>>
        > {};
}

template <typename List>
struct Unique : detail::UniqueImpl<List> {};

template <typename List>
using Unique_t = typename Unique<List>::type;

// ---------------------------------------------------------------------------
// 辅助工具
// ---------------------------------------------------------------------------

// 获取列表大小
template <typename List>
struct Size;

template <typename... Ts>
struct Size<TypeList<Ts...>> {
    static constexpr std::size_t value = sizeof...(Ts);
};

template <typename List>
inline constexpr std::size_t Size_v = Size<List>::value;

// 检查列表是否为空
template <typename List>
struct IsEmpty : std::false_type {};

template <>
struct IsEmpty<TypeList<>> : std::true_type {};

template <typename List>
inline constexpr bool IsEmpty_v = IsEmpty<List>::value;

} // namespace tmp
