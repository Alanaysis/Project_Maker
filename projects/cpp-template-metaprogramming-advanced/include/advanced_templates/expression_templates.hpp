#pragma once
/**
 * @file expression_templates.hpp
 * @brief 表达式模板 (Expression Templates)
 *
 * 表达式模板是一种延迟求值技术，可以避免创建临时对象，
 * 并将多个操作融合为一次遍历。
 *
 * 核心思想：
 *   - 向量运算 a + b + c 不立即计算，而是构建一个表达式树
 *   - 只在赋值时才遍历计算，减少临时对象和内存拷贝
 *   - 编译器可以更好地优化循环
 *
 * 应用场景：
 *   - 数值计算库（如 Blitz++, Eigen）
 *   - 科学计算
 *   - 任何需要高效数组操作的场景
 */

#include <cstddef>
#include <array>
#include <iostream>
#include <cmath>
#include <initializer_list>
#include <cassert>

namespace tmp {

// ============================================================================
// 前置声明
// ============================================================================

template <typename T, std::size_t N>
class Vector;

template <typename LHS, typename RHS, typename Op>
class BinaryExpr;

template <typename Operand, typename Op>
class UnaryExpr;

// ============================================================================
// 运算符标签
// ============================================================================

struct AddOp {
    template <typename T>
    static constexpr T apply(const T& a, const T& b) { return a + b; }
};

struct SubOp {
    template <typename T>
    static constexpr T apply(const T& a, const T& b) { return a - b; }
};

struct MulOp {
    template <typename T>
    static constexpr T apply(const T& a, const T& b) { return a * b; }
};

struct DivOp {
    template <typename T>
    static constexpr T apply(const T& a, const T& b) { return a / b; }
};

struct NegateOp {
    template <typename T>
    static constexpr T apply(const T& a) { return -a; }
};

// ============================================================================
// 表达式基类 (CRTP)
// ============================================================================

/**
 * @brief 表达式基类 - 使用 CRTP 避免虚函数开销
 * @tparam Derived 派生类型
 * @tparam T 元素类型
 */
template <typename Derived, typename T>
class Expression {
public:
    /// @brief 获取指定索引的元素
    constexpr T operator[](std::size_t i) const {
        return derived()[i];
    }

    /// @brief 获取表达式大小
    constexpr std::size_t size() const {
        return derived().size();
    }

    /// @brief 转换为派生类型
    const Derived& derived() const {
        return static_cast<const Derived&>(*this);
    }
};

// ============================================================================
// 二元表达式
// ============================================================================

/**
 * @brief 二元表达式 - 表示两个操作数的运算
 * @tparam LHS 左操作数类型
 * @tparam RHS 右操作数类型
 * @tparam Op 运算符类型
 */
template <typename LHS, typename RHS, typename Op>
class BinaryExpr : public Expression<BinaryExpr<LHS, RHS, Op>,
                                      typename LHS::value_type> {
    const LHS& lhs_;
    const RHS& rhs_;

public:
    using value_type = typename LHS::value_type;

    constexpr BinaryExpr(const LHS& lhs, const RHS& rhs)
        : lhs_(lhs), rhs_(rhs) {}

    constexpr value_type operator[](std::size_t i) const {
        return Op::apply(lhs_[i], rhs_[i]);
    }

    constexpr std::size_t size() const {
        return lhs_.size();
    }
};

// ============================================================================
// 一元表达式
// ============================================================================

/**
 * @brief 一元表达式 - 表示单个操作数的运算
 */
template <typename Operand, typename Op>
class UnaryExpr : public Expression<UnaryExpr<Operand, Op>,
                                     typename Operand::value_type> {
    const Operand& operand_;

public:
    using value_type = typename Operand::value_type;

    constexpr explicit UnaryExpr(const Operand& operand)
        : operand_(operand) {}

    constexpr value_type operator[](std::size_t i) const {
        return Op::apply(operand_[i]);
    }

    constexpr std::size_t size() const {
        return operand_.size();
    }
};

// ============================================================================
// 标量表达式
// ============================================================================

/**
 * @brief 标量表达式 - 广播标量到向量
 */
template <typename T>
class ScalarExpr : public Expression<ScalarExpr<T>, T> {
    T value_;

public:
    using value_type = T;

    constexpr explicit ScalarExpr(T value) : value_(value) {}

    constexpr T operator[](std::size_t) const {
        return value_;
    }

    constexpr std::size_t size() const {
        return 0;  // 标量没有固定大小
    }
};

// ============================================================================
// Vector 类 - 使用表达式模板的向量
// ============================================================================

/**
 * @brief 向量类 - 支持表达式模板的高效向量运算
 * @tparam T 元素类型
 * @tparam N 向量大小
 */
template <typename T, std::size_t N>
class Vector : public Expression<Vector<T, N>, T> {
    std::array<T, N> data_;

public:
    using value_type = T;

    /// @brief 默认构造
    constexpr Vector() : data_{} {}

    /// @brief 从初始化列表构造
    constexpr Vector(std::initializer_list<T> init) : data_{} {
        std::size_t i = 0;
        for (auto it = init.begin(); it != init.end() && i < N; ++it, ++i) {
            data_[i] = *it;
        }
    }

    /// @brief 从表达式构造 - 这是延迟求值的关键！
    template <typename Expr>
    constexpr Vector(const Expression<Expr, T>& expr) : data_{} {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = expr[i];
        }
    }

    /// @brief 赋值运算符 - 从表达式赋值
    template <typename Expr>
    constexpr Vector& operator=(const Expression<Expr, T>& expr) {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = expr[i];
        }
        return *this;
    }

    /// @brief 访问元素
    constexpr T operator[](std::size_t i) const { return data_[i]; }
    constexpr T& operator[](std::size_t i) { return data_[i]; }

    /// @brief 获取大小
    constexpr std::size_t size() const { return N; }

    /// @brief 内部数据访问
    constexpr const T* data() const { return data_.data(); }
    constexpr T* data() { return data_.data(); }

    /// @brief 初始化所有元素为同一值
    constexpr static Vector fill(T value) {
        Vector v;
        for (std::size_t i = 0; i < N; ++i) {
            v.data_[i] = value;
        }
        return v;
    }

    /// @brief 点积
    template <typename RHS>
    constexpr T dot(const Expression<RHS, T>& rhs) const {
        T result = T{0};
        for (std::size_t i = 0; i < N; ++i) {
            result += data_[i] * rhs[i];
        }
        return result;
    }

    /// @brief 向量的模
    constexpr T norm() const {
        return std::sqrt(dot(*this));
    }

    /// @brief 输出
    friend std::ostream& operator<<(std::ostream& os, const Vector& v) {
        os << "[";
        for (std::size_t i = 0; i < N; ++i) {
            if (i > 0) os << ", ";
            os << v.data_[i];
        }
        os << "]";
        return os;
    }
};

// ============================================================================
// 运算符重载 - 返回表达式对象（不立即计算）
// ============================================================================

/// @brief 向量 + 向量
template <typename L, typename R, typename T>
constexpr auto operator+(const Expression<L, T>& lhs,
                          const Expression<R, T>& rhs) {
    return BinaryExpr<L, R, AddOp>(lhs.derived(), rhs.derived());
}

/// @brief 向量 - 向量
template <typename L, typename R, typename T>
constexpr auto operator-(const Expression<L, T>& lhs,
                          const Expression<R, T>& rhs) {
    return BinaryExpr<L, R, SubOp>(lhs.derived(), rhs.derived());
}

/// @brief 向量 * 向量 (逐元素)
template <typename L, typename R, typename T>
constexpr auto operator*(const Expression<L, T>& lhs,
                          const Expression<R, T>& rhs) {
    return BinaryExpr<L, R, MulOp>(lhs.derived(), rhs.derived());
}

/// @brief 向量 / 向量 (逐元素)
template <typename L, typename R, typename T>
constexpr auto operator/(const Expression<L, T>& lhs,
                          const Expression<R, T>& rhs) {
    return BinaryExpr<L, R, DivOp>(lhs.derived(), rhs.derived());
}

/// @brief 标量 * 向量
template <typename T, std::size_t N>
constexpr auto operator*(T scalar, const Vector<T, N>& vec) {
    ScalarExpr<T> s(scalar);
    return BinaryExpr<ScalarExpr<T>, Vector<T, N>, MulOp>(s, vec);
}

/// @brief 向量 * 标量
template <typename T, std::size_t N>
constexpr auto operator*(const Vector<T, N>& vec, T scalar) {
    ScalarExpr<T> s(scalar);
    return BinaryExpr<Vector<T, N>, ScalarExpr<T>, MulOp>(vec, s);
}

/// @brief 向量取负
template <typename Derived, typename T>
constexpr auto operator-(const Expression<Derived, T>& expr) {
    return UnaryExpr<Derived, NegateOp>(expr.derived());
}

// ============================================================================
// 便利函数
// ============================================================================

/// @brief 逐元素取绝对值
template <typename T, std::size_t N>
constexpr Vector<T, N> abs(const Vector<T, N>& v) {
    Vector<T, N> result;
    for (std::size_t i = 0; i < N; ++i) {
        result[i] = std::abs(v[i]);
    }
    return result;
}

/// @brief 归一化向量
template <typename T, std::size_t N>
constexpr Vector<T, N> normalize(const Vector<T, N>& v) {
    T n = v.norm();
    return (T{1} / n) * v;
}

}  // namespace tmp
