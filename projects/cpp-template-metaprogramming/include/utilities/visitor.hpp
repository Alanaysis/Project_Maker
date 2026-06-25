#pragma once
// =============================================================================
// visitor.hpp - 访问者模式 (Visitor Pattern)
// =============================================================================
// 使用模板元编程实现的访问者模式
// 支持 std::variant 的多态访问和自定义类型的访问者
// =============================================================================

#include <variant>
#include <tuple>
#include <type_traits>
#include <functional>
#include <iostream>
#include <string>

namespace tmp {

// ---------------------------------------------------------------------------
// 重载模式 (Overloaded Pattern)
// ---------------------------------------------------------------------------
// 将多个 lambda 组合成一个可调用对象，用于 std::variant 的 visit

// 基础版本
template <typename... Ts>
struct Overloaded : Ts... {
    using Ts::operator()...;
};

// C++17 CTAD 推导指引
template <typename... Ts>
Overloaded(Ts...) -> Overloaded<Ts...>;

// ---------------------------------------------------------------------------
// 辅助函数：创建访问者
// ---------------------------------------------------------------------------

template <typename... Visitors>
auto make_visitor(Visitors... visitors) {
    return Overloaded{std::move(visitors)...};
}

// ---------------------------------------------------------------------------
// std::variant 访问辅助
// ---------------------------------------------------------------------------

// 安全的 variant 访问，带默认处理
template <typename Variant, typename... Visitors>
auto visit_with_default(Variant&& variant, Visitors&&... visitors) {
    auto visitor = Overloaded{
        std::forward<Visitors>(visitors)...,
        [](auto&&) { /* 默认处理 */ }
    };
    return std::visit(std::move(visitor), std::forward<Variant>(variant));
}

// ---------------------------------------------------------------------------
// 递归访问者 (Recursive Visitor)
// ---------------------------------------------------------------------------
// 用于处理递归数据结构，如表达式树

// 示例：简单表达式树
struct Expr;

struct Literal {
    double value;
};

struct Addition {
    std::unique_ptr<Expr> left;
    std::unique_ptr<Expr> right;
};

struct Multiplication {
    std::unique_ptr<Expr> left;
    std::unique_ptr<Expr> right;
};

struct Negation {
    std::unique_ptr<Expr> operand;
};

struct Expr {
    std::variant<Literal, Addition, Multiplication, Negation> data;

    template <typename T>
    Expr(T&& t) : data(std::forward<T>(t)) {}
};

// 递归求值
struct Evaluator {
    double operator()(const Literal& lit) const {
        return lit.value;
    }

    double operator()(const Addition& add) const {
        return std::visit(*this, add.left->data) +
               std::visit(*this, add.right->data);
    }

    double operator()(const Multiplication& mul) const {
        return std::visit(*this, mul.left->data) *
               std::visit(*this, mul.right->data);
    }

    double operator()(const Negation& neg) const {
        return -std::visit(*this, neg.operand->data);
    }
};

// 表达式打印
struct Printer {
    std::string operator()(const Literal& lit) const {
        return std::to_string(lit.value);
    }

    std::string operator()(const Addition& add) const {
        return "(" + std::visit(*this, add.left->data) + " + " +
               std::visit(*this, add.right->data) + ")";
    }

    std::string operator()(const Multiplication& mul) const {
        return "(" + std::visit(*this, mul.left->data) + " * " +
               std::visit(*this, mul.right->data) + ")";
    }

    std::string operator()(const Negation& neg) const {
        return "(-" + std::visit(*this, neg.operand->data) + ")";
    }
};

// ---------------------------------------------------------------------------
// 成员函数访问者 (Member Function Visitor)
// ---------------------------------------------------------------------------
// 将成员函数作为访问者

template <typename... Fs>
struct MemberVisitor : Fs... {
    using Fs::operator()...;
};

template <typename... Fs>
MemberVisitor(Fs...) -> MemberVisitor<Fs...>;

// ---------------------------------------------------------------------------
// 编译期访问者分发
// ---------------------------------------------------------------------------

// 使用 if constexpr 实现编译期分发
template <typename Variant, typename Visitor>
auto compile_time_visit(Variant&& variant, Visitor&& visitor) {
    return std::visit([&visitor](auto&& arg) -> decltype(auto) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_invocable_v<Visitor, T>) {
            return std::forward<Visitor>(visitor)(std::forward<decltype(arg)>(arg));
        } else {
            static_assert(std::is_invocable_v<Visitor, T>,
                          "Visitor must handle all variant types");
        }
    }, std::forward<Variant>(variant));
}

// ---------------------------------------------------------------------------
// 类型安全的访问者接口
// ---------------------------------------------------------------------------

// 定义访问者接口
template <typename ReturnType, typename... Types>
struct VisitorInterface {
    virtual ~VisitorInterface() = default;
    virtual ReturnType visit(const Types&...) = 0;
};

// 实现访问者
template <typename Derived, typename ReturnType, typename... Types>
struct VisitorImpl : VisitorInterface<ReturnType, Types...> {
    ReturnType visit(const Types&... args) override {
        return static_cast<Derived*>(this)->do_visit(args...);
    }
};

// ---------------------------------------------------------------------------
// 模式匹配风格的访问者
// ---------------------------------------------------------------------------

// 使用 tuple 实现的模式匹配
template <typename... Patterns>
struct PatternMatcher : Patterns... {
    using Patterns::operator()...;

    template <typename T>
    auto match(T&& value) const -> decltype(auto) {
        return (*this)(std::forward<T>(value));
    }
};

template <typename... Patterns>
PatternMatcher(Patterns...) -> PatternMatcher<Patterns...>;

// ---------------------------------------------------------------------------
// 实用工具：variant 类型检查
// ---------------------------------------------------------------------------

// 检查 variant 是否包含特定类型
template <typename Variant, typename T>
struct variant_contains;

template <typename... Types, typename T>
struct variant_contains<std::variant<Types...>, T>
    : std::disjunction<std::is_same<T, Types>...> {};

template <typename Variant, typename T>
inline constexpr bool variant_contains_v = variant_contains<Variant, T>::value;

// 获取 variant 中类型的索引
template <typename Variant, typename T>
struct variant_index;

template <typename... Types, typename T>
struct variant_index<std::variant<Types...>, T> {
    static constexpr std::size_t value = [] {
        std::size_t index = 0;
        ((std::is_same_v<T, Types> ? 0 : (++index, 0)), ...);
        return index;
    }();
};

template <typename Variant, typename T>
inline constexpr std::size_t variant_index_v = variant_index<Variant, T>::value;

} // namespace tmp
